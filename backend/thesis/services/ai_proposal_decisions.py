"""Revisión y decisión explícita de propuestas generadas con IA."""
import hashlib
import json
from typing import Any
from uuid import UUID
from django.db import transaction
from django.utils import timezone
from pydantic import ValidationError
from thesis.models import AIGenerationJob, Chapter, ChapterDocumentRevision, ResearchProfile
from thesis.services.access import require_project
from thesis.services.ai_job_context import _job_context_is_current
from thesis.services.chapter_documents import get_chapter_document, markdown_to_content_tree, save_chapter_document
from thesis.services.errors import DomainError
from thesis.services.step_contracts import CONTRACTS
from thesis.services.steps import save_step
from thesis.services.workflows import execute_custom_workflow_task

TEXTUAL_CONTENT_TASKS = frozenset({"P05", "P29"})


def _accepted_proposal_content_md(task_id: str, output_data: dict[str, Any]) -> str:
    """Proyecta solo campos declarados como texto de capítulo; nunca infiere prosa desde JSON."""
    if task_id in TEXTUAL_CONTENT_TASKS:
        content = output_data.get("contenido_markdown")
        if not isinstance(content, str) or not content.strip():
            raise DomainError(
                "OUTPUT_INVALID",
                f"La propuesta {task_id} requiere contenido_markdown no vacío para crear su revisión",
            )
        return content
    return "```json\n" + json.dumps(output_data, ensure_ascii=False, indent=2) + "\n```"

def _validated_job_output(job: AIGenerationJob) -> dict[str, Any]:
    """Verifica hash y contrato local antes de usar una salida persistida en un diff."""
    output_data = job.output_data
    if not isinstance(output_data, dict):
        raise DomainError("OUTPUT_INVALID", "El trabajo no conserva una salida estructurada válida")
    calculated_hash = hashlib.sha256(
        json.dumps(output_data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    if not job.output_sha256 or calculated_hash != job.output_sha256:
        raise DomainError("OUTPUT_INVALID", "El hash de la salida persistida no coincide")
    contract = CONTRACTS.get(job.workflow_task_id)
    if contract is None:
        raise DomainError("VALIDATION_ERROR", "La tarea no tiene un contrato de contenido de capítulo")
    try:
        return contract.model_validate(output_data).model_dump()
    except ValidationError as exc:
        raise DomainError("OUTPUT_INVALID", "La salida persistida ya no cumple su contrato") from exc

def get_ai_document_diff(actor: Any, project_id: UUID, job_id: UUID) -> dict[str, Any]:
    """Prepara el diff reemplazable P05/P29 sin persistir ni modificar el documento."""
    project = require_project(actor, project_id, owner_only=True)
    job = AIGenerationJob.objects.select_related("task", "workflow").filter(project=project, pk=job_id).first()
    if not job:
        raise DomainError("NOT_FOUND", "Trabajo de generación no encontrado en el proyecto")
    if job.workflow_task_id not in TEXTUAL_CONTENT_TASKS:
        raise DomainError("VALIDATION_ERROR", "Solo P05 y P29 tienen salida contractual de texto de capítulo")
    if job.status != AIGenerationJob.Status.SUCCEEDED or job.acceptance_status != AIGenerationJob.AcceptanceStatus.PENDING_ACCEPTANCE:
        raise DomainError("VERSION_CONFLICT", "La propuesta debe estar completada y pendiente de aceptación")

    profile = ResearchProfile.objects.get(project=project)
    if not _job_context_is_current(job, profile):
        raise DomainError("CONTEXT_STALE", "El contexto cambió desde la generación; vuelve a generar la propuesta")
    chapter_no = int(job.task.chapter_no)
    chapter = Chapter.objects.filter(project=project, number=chapter_no).first()
    if chapter and chapter.status in (Chapter.Status.READY, Chapter.Status.APPROVED):
        raise DomainError("VERSION_CONFLICT", "Reabre el capítulo antes de preparar una propuesta de reemplazo")

    output_data = _validated_job_output(job)
    proposed_markdown = _accepted_proposal_content_md(job.workflow_task_id, output_data)
    proposed_tree, normalized_markdown = markdown_to_content_tree(
        proposed_markdown, f"ai-proposal:{job.id}",
    )
    current = get_chapter_document(actor, project.id, chapter_no)
    operations = [{
        "op": "replace_document",
        "before_block_ids": [block["id"] for block in current["content_tree"]["blocks"]],
        "after_blocks": proposed_tree["blocks"],
    }]
    diff_payload = {
        "job_id": str(job.id),
        "task_id": job.workflow_task_id,
        "chapter_no": chapter_no,
        "operation": "REPLACE_DOCUMENT",
        "expected_state_version": job.state_version_at_request,
        "expected_document_version": current["document_version"],
        "before_content_sha256": current["content_sha256"],
        "before_tree": current["content_tree"],
        "before_content_md": current["content_md"],
        "after_tree": proposed_tree,
        "after_content_md": normalized_markdown,
        "operations": operations,
        "source_output_sha256": job.output_sha256,
    }
    diff_payload["proposal_sha256"] = hashlib.sha256(
        json.dumps(diff_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return diff_payload

def accept_ai_proposal(
    actor: Any,
    project_id: UUID,
    job_id: UUID,
    expected_state_version: int,
    decision_key: str | UUID,
    expected_document_version: int | None = None,
    proposal_sha256: str | None = None,
) -> dict[str, Any]:
    """Acepta explícitamente una propuesta y la incorpora mediante el caso de uso canónico."""
    project = require_project(actor, project_id, owner_only=True)
    try:
        dec_key = UUID(str(decision_key))
    except (ValueError, TypeError) as exc:
        raise DomainError("VALIDATION_ERROR", "decision_key debe ser un UUID válido") from exc

    with transaction.atomic():
        job = AIGenerationJob.objects.select_for_update().filter(project=project, pk=job_id).first()
        if not job:
            raise DomainError("NOT_FOUND", "Trabajo de generación no encontrado en el proyecto")

        # Idempotencia de aceptación
        if job.acceptance_status == AIGenerationJob.AcceptanceStatus.ACCEPTED:
            if job.decision_key != dec_key:
                raise DomainError("IDEMPOTENCY_CONFLICT", "La propuesta ya fue aceptada con otra decision_key")
            return {
                "job_id": str(job.id),
                "acceptance_status": job.acceptance_status,
                "result_revision_id": job.result_revision_id,
                "result_execution_id": job.result_execution_id,
                "result_document_revision_id": str(job.result_document_revision_id) if job.result_document_revision_id else None,
                "workflow_version_no": job.workflow_version_no,
                "idempotent": True,
            }
        if job.acceptance_status == AIGenerationJob.AcceptanceStatus.REJECTED:
            raise DomainError(
                "VERSION_CONFLICT",
                "Esta propuesta ya fue rechazada explícitamente y no puede ser aceptada posteriormente",
            )

        if job.status != AIGenerationJob.Status.SUCCEEDED:
            raise DomainError(
                "VALIDATION_ERROR",
                f"Solo se pueden aceptar propuestas de trabajos completados con éxito (estado actual: {job.status})",
            )

        # Revalidar frescura del contexto
        profile = ResearchProfile.objects.select_for_update().get(project=project)
        if (
            profile.lock_version != expected_state_version
            or job.state_version_at_request != expected_state_version
            or not _job_context_is_current(job, profile)
        ):
            raise DomainError(
                "CONTEXT_STALE",
                "El estado o contexto cambió desde que se generó la propuesta; vuelve a generarla antes de aceptarla",
            )

        document_diff = None
        if job.workflow_task_id in TEXTUAL_CONTENT_TASKS:
            if expected_document_version is None or not proposal_sha256:
                raise DomainError(
                    "VALIDATION_ERROR",
                    "P05/P29 requieren expected_document_version y proposal_sha256 del diff que el tesista revisó",
                )
            document_diff = get_ai_document_diff(actor, project.id, job.id)
            if document_diff["expected_document_version"] != expected_document_version:
                raise DomainError("VERSION_CONFLICT", "El documento cambió desde que se preparó el diff")
            if document_diff["proposal_sha256"] != proposal_sha256:
                raise DomainError("VERSION_CONFLICT", "El diff ya no coincide con la propuesta que se revisó")

        # Incorporación canónica
        if job.workflow_task_id in CONTRACTS:
            content_md = _accepted_proposal_content_md(job.workflow_task_id, job.output_data or {})
            save_res = save_step(
                actor=actor,
                project_id=project.id,
                step_code=job.workflow_task_id,
                content_md=content_md,
                output_data=job.output_data,
                expected_version=expected_state_version,
                idempotency_key=str(dec_key),
            )
            job.result_revision_id = save_res["revision_id"]
            new_state_version = save_res["state_version"]
            if document_diff:
                document_res = save_chapter_document(
                    actor=actor,
                    project_id=project.id,
                    chapter_no=document_diff["chapter_no"],
                    content_tree=document_diff["after_tree"],
                    expected_version=expected_document_version,
                    idempotency_key=str(dec_key),
                    source=ChapterDocumentRevision.Source.AI_PROPOSAL,
                )
                job.result_document_revision_id = document_res["revision_id"]
                new_state_version = document_res["state_version"]
        else:
            custom_res = execute_custom_workflow_task(
                actor=actor,
                project_id=project.id,
                task_id=job.workflow_task_id,
                input_data=job.input_data,
                output_data=job.output_data,
                idempotency_key=dec_key,
            )
            job.result_execution_id = custom_res["execution_id"]
            profile.lock_version += 1
            profile.save(update_fields=["lock_version", "updated_at"])
            new_state_version = profile.lock_version

        job.acceptance_status = AIGenerationJob.AcceptanceStatus.ACCEPTED
        job.decision_by = actor
        job.decision_at = timezone.now()
        job.decision_key = dec_key
        job.save(
            update_fields=[
                "acceptance_status",
                "decision_by",
                "decision_at",
                "decision_key",
                "result_revision_id",
                "result_execution_id",
                "result_document_revision",
            ]
        )

    return {
        "job_id": str(job.id),
        "acceptance_status": job.acceptance_status,
        "result_revision_id": job.result_revision_id,
        "result_execution_id": job.result_execution_id,
        "result_document_revision_id": str(job.result_document_revision_id) if job.result_document_revision_id else None,
        "workflow_version_no": job.workflow_version_no,
        "state_version": new_state_version,
        "idempotent": False,
    }

def reject_ai_proposal(
    actor: Any,
    project_id: UUID,
    job_id: UUID,
    decision_key: str | UUID,
    reason: str = "",
) -> dict[str, Any]:
    """Rechaza explícitamente una propuesta sin alterar el manuscrito canónico ni el perfil."""
    project = require_project(actor, project_id, owner_only=True)
    try:
        dec_key = UUID(str(decision_key))
    except (ValueError, TypeError) as exc:
        raise DomainError("VALIDATION_ERROR", "decision_key debe ser un UUID válido") from exc
    with transaction.atomic():
        job = AIGenerationJob.objects.select_for_update().filter(project=project, pk=job_id).first()
        if not job:
            raise DomainError("NOT_FOUND", "Trabajo de generación no encontrado en el proyecto")

        if job.acceptance_status == AIGenerationJob.AcceptanceStatus.REJECTED:
            if job.decision_key != dec_key or job.decision_reason != reason.strip()[:500]:
                raise DomainError("IDEMPOTENCY_CONFLICT", "La propuesta ya fue rechazada con otros datos de decisión")
            return {
                "job_id": str(job.id),
                "acceptance_status": job.acceptance_status,
                "decision_reason": job.decision_reason,
                "idempotent": True,
            }
        if job.acceptance_status == AIGenerationJob.AcceptanceStatus.ACCEPTED:
            raise DomainError(
                "VERSION_CONFLICT",
                "Esta propuesta ya fue aceptada e incorporada; no puede rechazarse posteriormente",
            )

        if job.status != AIGenerationJob.Status.SUCCEEDED:
            raise DomainError(
                "VALIDATION_ERROR",
                f"Solo se pueden rechazar propuestas de trabajos completados con éxito (estado actual: {job.status})",
            )

        job.acceptance_status = AIGenerationJob.AcceptanceStatus.REJECTED
        job.decision_by = actor
        job.decision_at = timezone.now()
        job.decision_key = dec_key
        job.decision_reason = reason.strip()[:500]
        job.save(update_fields=["acceptance_status", "decision_by", "decision_at", "decision_key", "decision_reason"])

    return {
        "job_id": str(job.id),
        "acceptance_status": job.acceptance_status,
        "decision_reason": job.decision_reason,
        "idempotent": False,
    }
