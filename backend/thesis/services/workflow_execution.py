"""Servicios de recorridos configurables."""

import hashlib
import json
from typing import Any
from uuid import UUID

from django.db import transaction

from thesis.models import ProjectWorkflow, ResearchProfile, StepProgress, WorkflowDependency, WorkflowTask, WorkflowTaskExecution
from thesis.services.access import require_project
from thesis.services.errors import DomainError


def get_custom_workflow_task_executions(
    actor: Any, project_id: UUID, task_id: str, workflow_version_no: int | None = None,
) -> dict[str, Any]:
    project = require_project(actor, project_id)
    workflow = ProjectWorkflow.objects.filter(
        project=project,
        version_no=workflow_version_no if workflow_version_no is not None else None,
    ).first() if workflow_version_no is not None else ProjectWorkflow.objects.filter(
        project=project, status=ProjectWorkflow.Status.PUBLISHED,
    ).order_by("-version_no").first()
    if workflow is None:
        raise DomainError("NOT_FOUND", "Versión de recorrido no encontrada")
    task = WorkflowTask.objects.filter(workflow=workflow, task_id=task_id, legacy_step_code="").first()
    if task is None:
        raise DomainError("NOT_FOUND", f"Tarea personalizada '{task_id}' no encontrada")
    executions = task.executions.filter(workflow=workflow).order_by("-revision_no")[:100]
    return {
        "task_id": task_id,
        "workflow_version_no": workflow.version_no,
        "executions": [{
            "execution_id": item.pk, "revision_no": item.revision_no,
            "input_data": item.input_json, "output_data": item.output_json,
            "prompt_text_used": item.prompt_text_used,
            "prompt_version_used": item.prompt_version_used,
            "output_sha256": item.output_sha256,
            "created_at": item.created_at.isoformat(),
        } for item in executions],
    }


def execute_custom_workflow_task(
    actor: Any, project_id: UUID, task_id: str, input_data: dict,
    output_data: dict, idempotency_key: UUID,
) -> dict[str, Any]:
    """Persiste una ejecución de tarea USR_ con contrato JSON abierto y versión exacta."""
    project = require_project(actor, project_id, owner_only=True)
    profile = ResearchProfile.objects.select_related("active_workflow").get(project=project)
    workflow = profile.active_workflow
    if profile.workflow_mode != ResearchProfile.WorkflowMode.CONFIGURABLE_GRAPH or workflow is None:
        raise DomainError("CONFIG_ERROR", "El proyecto no tiene un recorrido configurable publicado")
    if not task_id.startswith("USR_"):
        raise DomainError("VALIDATION_ERROR", "Este endpoint solo ejecuta tareas personalizadas USR_")
    task = WorkflowTask.objects.select_related("prompt").filter(
        workflow=workflow, task_id=task_id, is_active=True
    ).first()
    if task is None:
        raise DomainError("NOT_FOUND", f"Tarea personalizada activa '{task_id}' no encontrada")
    if not isinstance(input_data, dict) or not isinstance(output_data, dict):
        raise DomainError("VALIDATION_ERROR", "input_data y output_data deben ser objetos JSON")
    try:
        canonical_input = json.dumps(input_data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        canonical_output = json.dumps(output_data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise DomainError("VALIDATION_ERROR", "La entrada y salida deben ser JSON serializable") from exc
    if len(canonical_input.encode("utf-8")) > 200_000 or len(canonical_output.encode("utf-8")) > 500_000:
        raise DomainError("VALIDATION_ERROR", "La entrada o salida excede el límite de tamaño")

    for dep in task.prerequisite_dependencies.filter(is_blocking=True).select_related("target_task"):
        target = dep.target_task
        if not target.is_active:
            raise DomainError("PREREQUISITE_LOCKED", f"La dependencia {target.task_id} está inactiva")
        if dep.dependency_type != WorkflowDependency.Type.DATA_REQUIRED:
            raise DomainError(
                "CONFIG_ERROR",
                f"La dependencia {dep.dependency_type} requiere un flujo de aprobación aún no configurado",
            )
        if target.legacy_step_code:
            progress = StepProgress.objects.filter(
                project=project, step_code=target.legacy_step_code,
                workflow=workflow, workflow_version_no=workflow.version_no,
                status=StepProgress.Status.COMPLETED,
            ).first()
            target_output = progress.output_json if progress else None
        else:
            prior = target.executions.filter(workflow=workflow).order_by("-revision_no").first()
            target_output = prior.output_json if prior else None
        if target_output is None:
            raise DomainError("PREREQUISITE_LOCKED", f"Completa {target.task_id} antes de {task_id}")
        if dep.required_field:
            value: Any = target_output
            for part in dep.required_field.split("."):
                if not isinstance(value, dict) or part not in value:
                    value = None
                    break
                value = value[part]
            if value in (None, "", [], {}):
                raise DomainError(
                    "PREREQUISITE_LOCKED",
                    f"La salida de {target.task_id} no contiene el dato requerido '{dep.required_field}'",
                )

    with transaction.atomic():
        locked_profile = ResearchProfile.objects.select_for_update().get(project=project)
        if locked_profile.active_workflow_id != workflow.pk:
            raise DomainError("VERSION_CONFLICT", "El recorrido cambió durante la ejecución; vuelve a cargarlo")
        task = WorkflowTask.objects.select_for_update().get(pk=task.pk)
        existing = WorkflowTaskExecution.objects.filter(task=task, idempotency_key=idempotency_key).first()
        if existing:
            if existing.input_json != input_data or existing.output_json != output_data:
                raise DomainError("VERSION_CONFLICT", "La clave de idempotencia ya se usó con otros datos")
            return {
                "execution_id": existing.pk, "task_id": task.task_id,
                "workflow_version_no": workflow.version_no,
                "revision_no": existing.revision_no, "idempotent": True,
            }
        latest = task.executions.filter(workflow=workflow).order_by("-revision_no").first()
        prompt = getattr(task, "prompt", None)
        digest = hashlib.sha256(canonical_output.encode("utf-8")).hexdigest()
        execution = WorkflowTaskExecution.objects.create(
            task=task, workflow=workflow, revision_no=(latest.revision_no + 1 if latest else 1),
            idempotency_key=idempotency_key, input_json=input_data, output_json=output_data,
            prompt_text_used=prompt.prompt_text if prompt else "",
            prompt_version_used=prompt.prompt_version if prompt else None,
            output_sha256=digest, created_by=actor,
        )
    return {
        "execution_id": execution.pk, "task_id": task.task_id,
        "workflow_version_no": workflow.version_no,
        "prompt_version": execution.prompt_version_used,
        "revision_no": execution.revision_no, "output_sha256": execution.output_sha256,
        "idempotent": False,
    }
