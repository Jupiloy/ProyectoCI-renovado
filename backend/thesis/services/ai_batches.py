"""Orquestación atómica de lotes sobre los jobs de generación existentes."""

import hashlib
import json
from typing import Any
from uuid import UUID, NAMESPACE_URL, uuid5

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from thesis.models import (
    AIGenerationBatch, AIGenerationBatchItem, AIGenerationJob,
    ProjectWorkflow, ResearchProfile, WorkflowDependency, WorkflowTask,
)
from thesis.services.access import require_project
from thesis.services.ai_jobs import present_ai_job, request_task_generation
from thesis.services.errors import DomainError


MAX_BATCH_TASKS = 8
_TERMINAL = {
    AIGenerationJob.Status.SUCCEEDED,
    AIGenerationJob.Status.FAILED,
    AIGenerationJob.Status.CANCELLED,
}


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _validate_tasks(tasks: Any) -> list[dict[str, Any]]:
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= MAX_BATCH_TASKS:
        raise DomainError("VALIDATION_ERROR", f"tasks debe contener entre 1 y {MAX_BATCH_TASKS} elementos")
    normalized = []
    seen = set()
    for item in tasks:
        if not isinstance(item, dict) or set(item) - {"task_id", "input_data", "context_refs"}:
            raise DomainError("VALIDATION_ERROR", "Cada tarea solo admite task_id, input_data y context_refs")
        task_id = item.get("task_id")
        input_data = item.get("input_data", {})
        context_refs = item.get("context_refs", [])
        if not isinstance(task_id, str) or not task_id.strip() or len(task_id) > 50:
            raise DomainError("VALIDATION_ERROR", "task_id debe ser texto no vacío de hasta 50 caracteres")
        if task_id in seen:
            raise DomainError("VALIDATION_ERROR", f"La tarea '{task_id}' está repetida en el lote")
        if not isinstance(input_data, dict) or not isinstance(context_refs, list):
            raise DomainError("VALIDATION_ERROR", "input_data debe ser objeto y context_refs debe ser lista")
        seen.add(task_id)
        normalized.append({"task_id": task_id, "input_data": input_data, "context_refs": context_refs})
    return normalized


def _batch_status(jobs: list[AIGenerationJob]) -> str:
    statuses = [job.status for job in jobs]
    if not statuses:
        return "FAILED"
    if all(status == AIGenerationJob.Status.QUEUED for status in statuses):
        return "QUEUED"
    if any(status == AIGenerationJob.Status.RUNNING for status in statuses):
        return "RUNNING"
    if any(status == AIGenerationJob.Status.QUEUED for status in statuses):
        return "QUEUED"
    if all(status == AIGenerationJob.Status.SUCCEEDED for status in statuses):
        return "SUCCEEDED"
    if all(status == AIGenerationJob.Status.FAILED for status in statuses):
        return "FAILED"
    if all(status == AIGenerationJob.Status.CANCELLED for status in statuses):
        return "CANCELLED"
    if all(status in _TERMINAL for status in statuses):
        return "PARTIAL"
    return "RUNNING"


def _present_batch(batch: AIGenerationBatch) -> dict[str, Any]:
    items = list(
        AIGenerationBatchItem.objects.filter(batch=batch).select_related("job").order_by("item_order")
    )
    jobs = [item.job for item in items]
    counts = {
        status.lower(): sum(job.status == status for job in jobs)
        for status in (
            AIGenerationJob.Status.QUEUED,
            AIGenerationJob.Status.RUNNING,
            AIGenerationJob.Status.SUCCEEDED,
            AIGenerationJob.Status.FAILED,
            AIGenerationJob.Status.CANCELLED,
        )
    }
    return {
        "batch_id": str(batch.id),
        "project_id": str(batch.project_id),
        "status": _batch_status(jobs),
        "item_count": len(items),
        "status_counts": counts,
        "completed_count": sum(job.status in _TERMINAL for job in jobs),
        "request_sha256": batch.request_sha256,
        "workflow_version_no": batch.workflow_version_no,
        "state_version_at_request": batch.state_version_at_request,
        "created_at": batch.created_at.isoformat(),
        "items": [
            {
                "item_order": item.item_order,
                "input_sha256": item.input_sha256,
                **present_ai_job(item.job),
            }
            for item in items
        ],
    }


def create_ai_batch(
    actor: Any, project_id: UUID, tasks: list[dict[str, Any]],
    expected_state_version: int, workflow_version_no: int, idempotency_key: str | UUID,
) -> dict[str, Any]:
    project = require_project(actor, project_id, owner_only=True)
    normalized_tasks = _validate_tasks(tasks)
    try:
        key = UUID(str(idempotency_key))
    except (ValueError, TypeError) as exc:
        raise DomainError("VALIDATION_ERROR", "idempotency_key debe ser un UUID válido") from exc
    if expected_state_version < 0 or workflow_version_no < 1:
        raise DomainError("VALIDATION_ERROR", "Las versiones solicitadas deben ser enteros válidos")
    request_data = {
        "tasks": normalized_tasks,
        "expected_state_version": expected_state_version,
        "workflow_version_no": workflow_version_no,
    }
    request_sha256 = _canonical_hash(request_data)

    with transaction.atomic():
        profile = ResearchProfile.objects.select_for_update().get(project=project)
        existing = AIGenerationBatch.objects.filter(project=project, idempotency_key=key).first()
        if existing:
            if existing.request_sha256 != request_sha256:
                raise DomainError("IDEMPOTENCY_CONFLICT", "La clave ya fue usada con otra solicitud de lote")
            return _present_batch(existing)
        if getattr(settings, "TESISMCP_SYNC_AI_GENERATION", False):
            raise DomainError(
                "ASYNC_GENERATION_REQUIRED",
                "Los lotes requieren generación asíncrona; desactiva TESISMCP_SYNC_AI_GENERATION.",
            )
        if profile.lock_version != expected_state_version:
            raise DomainError("VERSION_CONFLICT", "El estado del proyecto cambió desde que se preparó el lote")

        workflow = profile.active_workflow
        if workflow is None:
            workflow = (
                ProjectWorkflow.objects.filter(project=project, status=ProjectWorkflow.Status.PUBLISHED)
                .order_by("-version_no").first()
            )
        if workflow is None:
            raise DomainError("NOT_FOUND", "No existe un recorrido publicado para este proyecto")
        if workflow.version_no != workflow_version_no:
            raise DomainError("VERSION_CONFLICT", "La versión del recorrido cambió desde que se preparó el lote")

        task_ids = [item["task_id"] for item in normalized_tasks]
        workflow_tasks = {
            task.task_id: task
            for task in WorkflowTask.objects.filter(workflow=workflow, task_id__in=task_ids, is_active=True)
        }
        missing = [task_id for task_id in task_ids if task_id not in workflow_tasks]
        if missing:
            raise DomainError("NOT_FOUND", f"Tareas inexistentes o inactivas: {', '.join(missing)}")
        internal_dependency = WorkflowDependency.objects.filter(
            workflow=workflow,
            is_blocking=True,
            source_task__task_id__in=task_ids,
            target_task__task_id__in=task_ids,
        ).exists()
        if internal_dependency:
            raise DomainError(
                "BATCH_DEPENDENCY_CONFLICT",
                "El lote contiene tareas unidas por una dependencia bloqueante del recorrido",
            )

        batch = AIGenerationBatch.objects.create(
            project=project,
            requested_by=actor,
            workflow=workflow,
            workflow_version_no=workflow.version_no,
            state_version_at_request=profile.lock_version,
            idempotency_key=key,
            request_data=request_data,
            request_sha256=request_sha256,
        )
        for item_order, item in enumerate(normalized_tasks, start=1):
            child_key = uuid5(NAMESPACE_URL, f"tesismcp:ai-batch:{batch.id}:task:{item['task_id']}")
            job_data = request_task_generation(
                actor=actor,
                project_id=project.id,
                task_id=item["task_id"],
                input_data=item["input_data"],
                context_refs=item["context_refs"],
                idempotency_key=child_key,
                expected_state_version=profile.lock_version,
                workflow_version_no=workflow.version_no,
            )
            job = AIGenerationJob.objects.get(pk=job_data["job_id"], project=project)
            AIGenerationBatchItem.objects.create(
                batch=batch,
                job=job,
                task_id=item["task_id"],
                item_order=item_order,
                input_sha256=_canonical_hash({
                    "input_data": item["input_data"], "context_refs": item["context_refs"],
                }),
            )
        return _present_batch(batch)


def get_ai_batch(actor: Any, project_id: UUID, batch_id: UUID) -> dict[str, Any]:
    project = require_project(actor, project_id)
    batch = AIGenerationBatch.objects.filter(project=project, pk=batch_id).first()
    if not batch:
        raise DomainError("NOT_FOUND", "Lote de generación no encontrado en el proyecto")
    return _present_batch(batch)


def list_ai_batches(actor: Any, project_id: UUID) -> list[dict[str, Any]]:
    project = require_project(actor, project_id)
    return [_present_batch(batch) for batch in AIGenerationBatch.objects.filter(project=project)[:50]]


def cancel_ai_batch(actor: Any, project_id: UUID, batch_id: UUID) -> dict[str, Any]:
    project = require_project(actor, project_id, owner_only=True)
    with transaction.atomic():
        batch = AIGenerationBatch.objects.select_for_update().filter(project=project, pk=batch_id).first()
        if not batch:
            raise DomainError("NOT_FOUND", "Lote de generación no encontrado en el proyecto")
        jobs = list(
            AIGenerationJob.objects.select_for_update()
            .filter(batch_item__batch=batch).order_by("created_at")
        )
        cancelled = 0
        still_running = 0
        already_terminal = 0
        now = timezone.now()
        for job in jobs:
            if job.status == AIGenerationJob.Status.QUEUED:
                job.status = AIGenerationJob.Status.CANCELLED
                job.finished_at = now
                job.save(update_fields=["status", "finished_at"])
                cancelled += 1
            elif job.status == AIGenerationJob.Status.RUNNING:
                still_running += 1
            else:
                already_terminal += 1
        result = _present_batch(batch)
        result["cancellation"] = {
            "cancelled": cancelled,
            "already_terminal": already_terminal,
            "still_running": still_running,
        }
        return result
