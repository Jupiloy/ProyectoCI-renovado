"""Presentación de datos de dominio; sin cambios de persistencia."""

from typing import Any
from thesis.models import AIGenerationJob


def present_ai_job(job: AIGenerationJob) -> dict[str, Any]:
    """Serializa la entidad AIGenerationJob de forma segura sin exponer secretos."""
    return {
        "job_id": str(job.id),
        "project_id": str(job.project_id),
        "task_id": job.workflow_task_id,
        "workflow_version_no": job.workflow_version_no,
        "prompt_version_used": job.prompt_version_used,
        "status": job.status,
        "acceptance_status": job.acceptance_status,
        "idempotency_key": str(job.idempotency_key),
        "input_data": job.input_data,
        "output_data": job.output_data if job.status == AIGenerationJob.Status.SUCCEEDED else None,
        "output_sha256": job.output_sha256 if job.status == AIGenerationJob.Status.SUCCEEDED else "",
        "provider": job.provider,
        "model": job.model,
        "usage": job.usage_data,
        "error_code": job.error_code or None,
        "error_message": job.error_message or None,
        "decision_reason": job.decision_reason or None,
        "result_revision_id": job.result_revision_id,
        "result_execution_id": job.result_execution_id,
        "result_document_revision_id": str(job.result_document_revision_id) if job.result_document_revision_id else None,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }
