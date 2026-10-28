"""Claim, heartbeat y cierre seguro de jobs ejecutados por conectores BYOA."""

import hashlib
import json
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from django.db import transaction
from django.utils import timezone
from pydantic import ValidationError

from thesis.models import AIGenerationJob, AgentConnection, ResearchProfile
from thesis.services.ai_job_context import _job_context_is_current
from thesis.services.ai_job_serialization import present_ai_job
from thesis.services.errors import DomainError
from thesis.services.output_schemas import validate_output_data
from thesis.services.step_contracts import CONTRACTS

LEASE_SECONDS = 300
MAX_AGENT_EVENTS = 100
MAX_EVENT_BYTES = 4096
MAX_PROVENANCE_BYTES = 16_000
SAFE_FAILURE_CODES = {
    "RUNTIME_UNAVAILABLE", "RUNTIME_TIMEOUT", "RUNTIME_FAILED", "OUTPUT_INVALID",
    "CONNECTION_REVOKED", "LEASE_EXPIRED", "TOOL_PERMISSION_DENIED",
}


def _owned_job(connection: AgentConnection, job_id: UUID, *, lock=False) -> AIGenerationJob:
    qs = AIGenerationJob.objects.select_related("project", "workflow", "task").filter(
        pk=job_id,
        project_id=connection.project_id,
        agent_connection=connection,
        execution_mode=AIGenerationJob.ExecutionMode.BYOA,
    )
    if lock:
        qs = qs.select_for_update()
    job = qs.first()
    if job is None:
        raise DomainError("NOT_FOUND", "Trabajo BYOA no encontrado")
    return job


def claim_next_byoa_job(connection: AgentConnection) -> dict | None:
    now = timezone.now()
    with transaction.atomic():
        expired = list(
            AIGenerationJob.objects.select_for_update(skip_locked=True).filter(
                agent_connection=connection,
                execution_mode=AIGenerationJob.ExecutionMode.BYOA,
                status=AIGenerationJob.Status.RUNNING,
                lease_expires_at__lte=now,
            )
        )
        for job in expired:
            job.status = AIGenerationJob.Status.FAILED
            job.error_code = "LEASE_EXPIRED"
            job.error_message = "El conector dejó de renovar la tarea; vuelve a solicitarla si aún la necesitas"
            job.finished_at = now
            job.lease_expires_at = None
            job.save(update_fields=["status", "error_code", "error_message", "finished_at", "lease_expires_at"])

        job = (
            AIGenerationJob.objects.select_for_update(skip_locked=True)
            .select_related("project", "workflow", "task")
            .filter(
                agent_connection=connection,
                execution_mode=AIGenerationJob.ExecutionMode.BYOA,
                status=AIGenerationJob.Status.QUEUED,
                project__status="ACTIVE",
            )
            .order_by("created_at")
            .first()
        )
        if job is None:
            return None
        job.status = AIGenerationJob.Status.RUNNING
        job.started_at = now
        job.attempts += 1
        job.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        job.save(update_fields=["status", "started_at", "attempts", "lease_expires_at"])
        return {
            "protocol_version": "1",
            "runtime": connection.runtime,
            "job_id": str(job.pk),
            "correlation_id": str(job.pk),
            "lease_expires_at": job.lease_expires_at.isoformat(),
            "task": {
                "project_id": str(job.project_id),
                "task_id": job.workflow_task_id,
                "prompt_text": job.prompt_text_used,
                "prompt_version": job.prompt_version_used,
                "input_data": job.input_data,
                "context_snapshot": job.context_snapshot,
                "context_sha256": job.context_sha256,
                "output_schema": job.output_schema_used,
            },
        }


def heartbeat_byoa_job(connection: AgentConnection, job_id: UUID) -> dict:
    now = timezone.now()
    with transaction.atomic():
        job = _owned_job(connection, job_id, lock=True)
        if job.status == AIGenerationJob.Status.CANCELLED:
            return {"job_id": str(job.pk), "status": job.status, "cancelled": True}
        if job.status != AIGenerationJob.Status.RUNNING:
            raise DomainError("JOB_NOT_CANCELLABLE", "El trabajo ya no está en ejecución")
        if job.lease_expires_at is None or job.lease_expires_at <= now:
            job.status = AIGenerationJob.Status.FAILED
            job.error_code = "LEASE_EXPIRED"
            job.error_message = "El lease de ejecución venció"
            job.finished_at = now
            job.lease_expires_at = None
            job.save(update_fields=["status", "error_code", "error_message", "finished_at", "lease_expires_at"])
            return {"job_id": str(job.pk), "status": job.status, "cancelled": False, "error_code": job.error_code}
        job.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        job.save(update_fields=["lease_expires_at"])
        return {"job_id": str(job.pk), "status": job.status, "cancelled": False, "lease_expires_at": job.lease_expires_at.isoformat()}


def append_byoa_event(connection: AgentConnection, job_id: UUID, *, event_type: str, payload: dict) -> dict:
    if event_type not in {"progress", "tool_activity"} or not isinstance(payload, dict):
        raise DomainError("INVALID_EVENT", "Evento de progreso no válido")
    if event_type == "progress":
        message = payload.get("message")
        if not isinstance(message, str) or len(message) > 300:
            raise DomainError("INVALID_EVENT", "El mensaje de progreso debe tener hasta 300 caracteres")
        safe_payload = {"message": message}
    else:
        tool_name = payload.get("tool_name")
        if not isinstance(tool_name, str) or len(tool_name) > 80:
            raise DomainError("INVALID_EVENT", "tool_name debe ser texto de hasta 80 caracteres")
        safe_payload = {"tool_name": tool_name}
    if len(json.dumps(safe_payload, ensure_ascii=False).encode("utf-8")) > MAX_EVENT_BYTES:
        raise DomainError("INVALID_EVENT", "El evento excede el tamaño permitido")
    with transaction.atomic():
        job = _owned_job(connection, job_id, lock=True)
        if job.status != AIGenerationJob.Status.RUNNING or not job.lease_expires_at or job.lease_expires_at <= timezone.now():
            raise DomainError("LEASE_EXPIRED", "El trabajo no tiene un lease de ejecución vigente")
        events = list(job.agent_events or [])
        event = {
            "event_id": str(uuid4()),
            "sequence": max((int(item.get("sequence", 0)) for item in events), default=0) + 1,
            "type": event_type,
            "created_at": timezone.now().isoformat(),
            "payload": safe_payload,
        }
        events.append(event)
        job.agent_events = events[-MAX_AGENT_EVENTS:]
        job.save(update_fields=["agent_events"])
        return event


def complete_byoa_job(
    connection: AgentConnection,
    job_id: UUID,
    *,
    output_data: Any,
    provenance: dict | None = None,
    usage_data: dict | None = None,
) -> dict:
    if not isinstance(provenance or {}, dict) or not isinstance(usage_data or {}, dict):
        raise DomainError("VALIDATION_ERROR", "provenance y usage deben ser objetos")
    provenance = provenance or {}
    usage_data = usage_data or {}
    for name, value in (("provenance", provenance), ("usage_data", usage_data)):
        try:
            encoded = json.dumps(value, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise DomainError("VALIDATION_ERROR", f"{name} debe ser JSON") from exc
        if len(encoded) > MAX_PROVENANCE_BYTES:
            raise DomainError("OUTPUT_TOO_LARGE", f"{name} excede el tamaño permitido")
    job = _owned_job(connection, job_id)
    try:
        if job.workflow_task_id in CONTRACTS:
            validated_output = CONTRACTS[job.workflow_task_id].model_validate(output_data).model_dump()
        else:
            validated_output = validate_output_data(output_data, job.output_schema_used)
    except ValidationError as exc:
        raise DomainError("OUTPUT_INVALID", f"La propuesta no cumple el contrato {job.workflow_task_id}: {str(exc)[:400]}") from exc
    except DomainError:
        raise
    output_hash = hashlib.sha256(
        json.dumps(validated_output, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    now = timezone.now()
    with transaction.atomic():
        job = _owned_job(connection, job_id, lock=True)
        if job.status == AIGenerationJob.Status.SUCCEEDED and job.output_sha256 == output_hash:
            return present_ai_job(job)
        if job.status != AIGenerationJob.Status.RUNNING or not job.lease_expires_at or job.lease_expires_at <= now:
            raise DomainError("LEASE_EXPIRED", "El trabajo no está en ejecución con un lease vigente")
        profile = ResearchProfile.objects.select_for_update().get(project=job.project)
        if not _job_context_is_current(job, profile):
            job.status = AIGenerationJob.Status.FAILED
            job.error_code = "CONTEXT_STALE"
            job.error_message = "El contexto cambió mientras se generaba la propuesta; vuelve a solicitarla"
            job.finished_at = now
            job.lease_expires_at = None
            job.save(update_fields=["status", "error_code", "error_message", "finished_at", "lease_expires_at"])
            return present_ai_job(job)
        job.output_data = validated_output
        job.output_sha256 = output_hash
        job.provider = connection.runtime
        job.model = str(provenance.get("model") or "")[:100]
        job.usage_data = usage_data
        job.agent_provenance = {
            "runtime": connection.runtime,
            "model": job.model or None,
            "conversation_id": str(provenance.get("conversation_id") or "")[:200] or None,
        }
        job.status = AIGenerationJob.Status.SUCCEEDED
        job.acceptance_status = AIGenerationJob.AcceptanceStatus.PENDING_ACCEPTANCE
        job.finished_at = now
        job.lease_expires_at = None
        job.save(update_fields=[
            "output_data", "output_sha256", "provider", "model", "usage_data", "agent_provenance",
            "status", "acceptance_status", "finished_at", "lease_expires_at",
        ])
    return present_ai_job(job)


def fail_byoa_job(connection: AgentConnection, job_id: UUID, *, error_code: str, message: str) -> dict:
    if error_code not in SAFE_FAILURE_CODES:
        error_code = "RUNTIME_FAILED"
    safe_message = message.strip()[:500] if isinstance(message, str) else "La ejecución del agente falló"
    with transaction.atomic():
        job = _owned_job(connection, job_id, lock=True)
        if job.status != AIGenerationJob.Status.RUNNING:
            raise DomainError("JOB_NOT_CANCELLABLE", "El trabajo ya no está en ejecución")
        if not job.lease_expires_at or job.lease_expires_at <= timezone.now():
            raise DomainError("LEASE_EXPIRED", "El lease de ejecución venció")
        job.status = AIGenerationJob.Status.FAILED
        job.error_code = error_code
        job.error_message = safe_message or "La ejecución del agente falló"
        job.finished_at = timezone.now()
        job.lease_expires_at = None
        job.save(update_fields=["status", "error_code", "error_message", "finished_at", "lease_expires_at"])
    return present_ai_job(job)
