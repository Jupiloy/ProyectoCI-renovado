"""Servicio de dominio para generación de tareas con IA y ciclo de aceptación."""

import hashlib
import json
import logging
from typing import Any
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from pydantic import ValidationError

from thesis.integrations.llm import (
    LLMError,
    LLMMessage,
    LLMOutputInvalidError,
    LLMProviderRateLimitError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
    get_llm_adapter,
)
from thesis.models import (
    AIGenerationBatchSynthesis,
    AIGenerationJob,
    AgentConnection,
    ProjectWorkflow,
    ResearchProfile,
    StepProgress,
    WorkflowTask,
    WorkflowTaskExecution,
)
from thesis.services.access import require_project
from thesis.services.ai_job_serialization import present_ai_job
from thesis.services.errors import DomainError
from thesis.services.output_schemas import validate_output_data, validate_output_schema_definition
from thesis.services.step_contracts import CONTRACTS

logger = logging.getLogger(__name__)


from thesis.services.ai_job_context import _build_context_snapshot, _job_context_is_current
from thesis.services.ai_proposal_decisions import (
    TEXTUAL_CONTENT_TASKS, _accepted_proposal_content_md, _validated_job_output,
    get_ai_document_diff, accept_ai_proposal, reject_ai_proposal,
)












def request_task_generation(
    actor: Any,
    project_id: UUID,
    task_id: str,
    input_data: dict[str, Any] | None = None,
    context_refs: list[dict[str, Any]] | None = None,
    idempotency_key: str | UUID | None = None,
    expected_state_version: int | None = None,
    workflow_version_no: int | None = None,
    execution_mode: str = AIGenerationJob.ExecutionMode.SERVER,
    agent_connection_id: UUID | None = None,
) -> dict[str, Any]:
    """Solicita la generación asistida con IA de una propuesta estructurada."""
    project = require_project(actor, project_id, owner_only=True)
    if not idempotency_key:
        raise DomainError("VALIDATION_ERROR", "idempotency_key es obligatorio")
    try:
        key = UUID(str(idempotency_key))
    except (ValueError, TypeError) as exc:
        raise DomainError("VALIDATION_ERROR", "idempotency_key debe ser un UUID válido") from exc

    input_data = input_data or {}
    if execution_mode not in AIGenerationJob.ExecutionMode.values:
        raise DomainError("VALIDATION_ERROR", "execution_mode debe ser SERVER o BYOA")
    agent_connection = None
    if execution_mode == AIGenerationJob.ExecutionMode.BYOA:
        if not agent_connection_id:
            raise DomainError("VALIDATION_ERROR", "agent_connection_id es obligatorio para BYOA")
        agent_connection = AgentConnection.objects.filter(
            pk=agent_connection_id, user=actor, project=project, revoked_at__isnull=True,
            expires_at__gt=timezone.now(), project__status="ACTIVE",
        ).first()
        if agent_connection is None:
            raise DomainError("NOT_FOUND", "Conexión BYOA no encontrada para este proyecto")
    elif agent_connection_id is not None:
        raise DomainError("VALIDATION_ERROR", "agent_connection_id solo se permite con execution_mode=BYOA")

    with transaction.atomic():
        profile = ResearchProfile.objects.select_for_update().get(project=project)
        if expected_state_version is not None and profile.lock_version != expected_state_version:
            raise DomainError(
                "VERSION_CONFLICT",
                f"El estado del proyecto cambió (versión esperada: {expected_state_version}, actual: {profile.lock_version})",
            )

        active_wf = profile.active_workflow
        if not active_wf:
            active_wf = (
                ProjectWorkflow.objects.filter(project=project, status=ProjectWorkflow.Status.PUBLISHED)
                .order_by("-version_no")
                .first()
            )
        if not active_wf:
            raise DomainError("NOT_FOUND", "No existe un recorrido publicado para este proyecto")

        if workflow_version_no is not None and active_wf.version_no != workflow_version_no:
            raise DomainError(
                "VERSION_CONFLICT",
                f"La versión del recorrido cambió (esperada: {workflow_version_no}, actual: {active_wf.version_no})",
            )

        task = (
            WorkflowTask.objects.select_related("prompt")
            .filter(workflow=active_wf, task_id=task_id)
            .first()
        )
        if not task:
            raise DomainError("NOT_FOUND", f"La tarea '{task_id}' no existe en el recorrido publicado activo")
        if not task.is_active:
            raise DomainError("PREREQUISITE_LOCKED", f"La tarea '{task_id}' está desactivada en el recorrido")

        # Verificar dependencias bloqueantes
        unmet = []
        for dep in task.prerequisite_dependencies.filter(is_blocking=True).select_related("target_task"):
            target_id = dep.target_task.task_id
            if dep.target_task.is_active:
                if target_id.startswith("USR_"):
                    done = WorkflowTaskExecution.objects.filter(
                        task=dep.target_task, workflow=active_wf
                    ).exists()
                else:
                    done = StepProgress.objects.filter(
                        project=project, step_code=target_id, status=StepProgress.Status.COMPLETED
                    ).exists()
                if not done:
                    reason = f" ({dep.reason})" if dep.reason else ""
                    unmet.append(f"{target_id}{reason}")
        if unmet:
            raise DomainError(
                "PREREQUISITE_LOCKED",
                f"Dependencias bloqueantes pendientes para '{task_id}': completa {', '.join(unmet)} antes de generar",
            )

        # Idempotencia de solicitud
        existing = AIGenerationJob.objects.filter(project=project, idempotency_key=key).first()
        if existing:
            if (existing.workflow_task_id != task_id or existing.input_data != input_data
                    or existing.execution_mode != execution_mode
                    or existing.agent_connection_id != getattr(agent_connection, "pk", None)):
                raise DomainError(
                    "VERSION_CONFLICT",
                    "La clave de idempotencia ya fue utilizada con otra tarea o datos de entrada diferentes",
                )
            return present_ai_job(existing)

        # Rechazar la solicitud con error de dominio estable si el proveedor
        # está deshabilitado o falta su configuración; no dejar un job ficticio.
        if execution_mode == AIGenerationJob.ExecutionMode.SERVER:
            try:
                get_llm_adapter()
            except LLMProviderUnavailableError as exc:
                raise DomainError("PROVIDER_UNAVAILABLE", str(exc)) from exc

        context_snapshot = _build_context_snapshot(project, profile, active_wf, task, context_refs)

        context_sha256 = hashlib.sha256(
            json.dumps(context_snapshot, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

        prompt_obj = getattr(task, "prompt", None)
        prompt_text_used = prompt_obj.prompt_text if prompt_obj else ""
        prompt_version_used = prompt_obj.prompt_version if prompt_obj else 1

        # Determinar output_schema
        if task_id in CONTRACTS:
            output_schema_used = CONTRACTS[task_id].model_json_schema()
        else:
            output_schema_used = validate_output_schema_definition(task.output_schema)

        job = AIGenerationJob.objects.create(
            project=project,
            requested_by=actor,
            workflow=active_wf,
            workflow_version_no=active_wf.version_no,
            state_version_at_request=profile.lock_version,
            task=task,
            workflow_task_id=task_id,
            prompt=prompt_obj,
            prompt_text_used=prompt_text_used,
            prompt_version_used=prompt_version_used,
            status=AIGenerationJob.Status.QUEUED,
            execution_mode=execution_mode,
            agent_connection=agent_connection,
            acceptance_status=AIGenerationJob.AcceptanceStatus.PENDING_ACCEPTANCE,
            idempotency_key=key,
            input_data=input_data,
            context_snapshot=context_snapshot,
            context_sha256=context_sha256,
            output_schema_used=output_schema_used,
        )

    # La API encola siempre. El worker procesa el job fuera de la petición HTTP.
    if (execution_mode == AIGenerationJob.ExecutionMode.SERVER
            and getattr(settings, "TESISMCP_SYNC_AI_GENERATION", False)):
        process_ai_generation_job(job.id)
        job.refresh_from_db()

    return present_ai_job(job)


def _fail_job(job: AIGenerationJob, error_code: str, error_message: str) -> None:
    job.status = AIGenerationJob.Status.FAILED
    job.error_code = error_code
    job.error_message = error_message
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "error_code", "error_message", "finished_at", "attempts"])


def process_ai_generation_job(job_id: UUID, *, already_claimed: bool = False) -> AIGenerationJob:
    """Procesa un trabajo de generación en cola invocando el adaptador LLM y validando localmente."""
    with transaction.atomic():
        job = AIGenerationJob.objects.select_for_update().filter(pk=job_id).first()
        expected_status = AIGenerationJob.Status.RUNNING if already_claimed else AIGenerationJob.Status.QUEUED
        if not job or job.status != expected_status:
            return job
        if job.execution_mode != AIGenerationJob.ExecutionMode.SERVER:
            return job

        if not already_claimed:
            job.status = AIGenerationJob.Status.RUNNING
            job.started_at = timezone.now()
            job.attempts += 1
            job.save(update_fields=["status", "started_at", "attempts"])

        # Comprobar la versión fijada antes de hacer una llamada potencialmente costosa.
        profile = ResearchProfile.objects.select_for_update().get(project=job.project)
        if not _job_context_is_current(job, profile):
            _fail_job(
                job,
                "CONTEXT_STALE",
                "El proyecto, el recorrido, el prompt o las fuentes cambiaron tras encolar el trabajo",
            )
            return job

    # Llamar al adaptador LLM
    try:
        adapter = get_llm_adapter()
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "Eres el asistente metodológico de TesisMCP. Tu tarea es generar únicamente "
                    "una propuesta estructurada en formato JSON estricto que cumpla con el esquema requerido."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"PROMPT METODOLÓGICO:\n{job.prompt_text_used}\n\n"
                    f"DATOS DE ENTRADA:\n{json.dumps(job.input_data, ensure_ascii=False)}\n\n"
                    f"CONTEXTO VERIFICADO:\n{json.dumps(job.context_snapshot, ensure_ascii=False)}"
                ),
            ),
        ]
        llm_result = adapter.generate_structured(
            messages=messages,
            output_schema=job.output_schema_used,
            timeout=30.0,
        )
    except LLMProviderTimeoutError as e:
        _fail_job(job, "PROVIDER_TIMEOUT", str(e))
        return job
    except LLMProviderRateLimitError as e:
        _fail_job(job, "PROVIDER_RATE_LIMITED", str(e))
        return job
    except LLMProviderUnavailableError as e:
        _fail_job(job, "PROVIDER_UNAVAILABLE", str(e))
        return job
    except LLMOutputInvalidError as e:
        _fail_job(job, "OUTPUT_INVALID", str(e))
        return job
    except Exception as e:
        logger.exception("Error inesperado en adaptador LLM para job %s", job.id)
        _fail_job(job, "PROVIDER_UNAVAILABLE", "Falla inesperada en el proveedor de IA")
        return job

    # Validación estricta local de la salida estructurada
    try:
        if job.workflow_task_id in CONTRACTS:
            contract_cls = CONTRACTS[job.workflow_task_id]
            validated_output = contract_cls.model_validate(llm_result.content_json).model_dump()
        else:
            validated_output = validate_output_data(llm_result.content_json, job.output_schema_used)
    except ValidationError as exc:
        _fail_job(
            job,
            "OUTPUT_INVALID",
            f"La salida estructurada no cumple el contrato {job.workflow_task_id}: {str(exc)[:500]}",
        )
        return job
    except DomainError as exc:
        _fail_job(job, exc.code, exc.message)
        return job

    output_sha256 = hashlib.sha256(
        json.dumps(validated_output, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    with transaction.atomic():
        current_job = AIGenerationJob.objects.select_for_update().get(pk=job_id)
        profile = ResearchProfile.objects.select_for_update().get(project=current_job.project)
        if current_job.status != AIGenerationJob.Status.RUNNING:
            return current_job
        if not _job_context_is_current(current_job, profile):
            _fail_job(
                current_job,
                "CONTEXT_STALE",
                "El contexto cambió mientras se generaba la propuesta; vuelve a solicitarla",
            )
            return current_job
        current_job.output_data = validated_output
        current_job.output_sha256 = output_sha256
        current_job.provider = llm_result.provider
        current_job.model = llm_result.model
        current_job.usage_data = llm_result.usage or {}
        current_job.status = AIGenerationJob.Status.SUCCEEDED
        current_job.acceptance_status = AIGenerationJob.AcceptanceStatus.PENDING_ACCEPTANCE
        current_job.finished_at = timezone.now()
        current_job.save(
            update_fields=[
                "output_data", "output_sha256", "provider", "model", "usage_data",
                "status", "acceptance_status", "finished_at",
            ]
        )
    return current_job


def get_ai_job(actor: Any, project_id: UUID, job_id: UUID) -> dict[str, Any]:
    """Consulta el estado autorizado de un trabajo de generación."""
    project = require_project(actor, project_id)
    job = AIGenerationJob.objects.filter(project=project, pk=job_id).first()
    if not job:
        raise DomainError("NOT_FOUND", "Trabajo de generación no encontrado en el proyecto")
    if (job.execution_mode == AIGenerationJob.ExecutionMode.BYOA
            and job.status == AIGenerationJob.Status.RUNNING
            and (job.lease_expires_at is None or job.lease_expires_at <= timezone.now())):
        job.status = AIGenerationJob.Status.FAILED
        job.error_code = "LEASE_EXPIRED"
        job.error_message = "El conector dejó de renovar la tarea; vuelve a solicitarla si aún la necesitas"
        job.finished_at = timezone.now()
        job.lease_expires_at = None
        job.save(update_fields=["status", "error_code", "error_message", "finished_at", "lease_expires_at"])
    return present_ai_job(job)




def run_next_ai_job() -> bool:
    """Reclama el siguiente job IA o síntesis de lote mediante una transacción breve."""
    with transaction.atomic():
        job = (
            AIGenerationJob.objects.select_for_update(skip_locked=True)
            .filter(status=AIGenerationJob.Status.QUEUED, execution_mode=AIGenerationJob.ExecutionMode.SERVER)
            .order_by("created_at")
            .first()
        )
        synthesis = (
            AIGenerationBatchSynthesis.objects.select_for_update(skip_locked=True)
            .filter(status=AIGenerationBatchSynthesis.Status.QUEUED)
            .order_by("created_at")
            .first()
        )
        if not job and not synthesis:
            return False
        process_synthesis = synthesis is not None and (
            job is None or synthesis.created_at < job.created_at
        )
        if process_synthesis:
            synthesis.status = AIGenerationBatchSynthesis.Status.RUNNING
            synthesis.started_at = timezone.now()
            synthesis.attempts += 1
            synthesis.save(update_fields=["status", "started_at", "attempts"])
            synthesis_id = synthesis.id
        else:
            job.status = AIGenerationJob.Status.RUNNING
            job.started_at = timezone.now()
            job.attempts += 1
            job.save(update_fields=["status", "started_at", "attempts"])
            job_id = job.id
    if process_synthesis:
        from thesis.services.batch_synthesis import process_batch_synthesis_job
        process_batch_synthesis_job(synthesis_id, already_claimed=True)
    else:
        process_ai_generation_job(job_id, already_claimed=True)
    return True


def fail_interrupted_ai_jobs() -> int:
    """Falla jobs RUNNING abandonados durante el arranque exclusivo del worker.

    No los reencola: una caída tras completar la llamada externa pero antes de
    guardar su respuesta podría causar una segunda llamada facturable.
    El caller debe adquirir antes el advisory lock global del worker.
    """
    failed_count = 0
    with transaction.atomic():
        interrupted = list(
            AIGenerationJob.objects.select_for_update()
            .filter(status=AIGenerationJob.Status.RUNNING, execution_mode=AIGenerationJob.ExecutionMode.SERVER)
            .order_by("started_at", "created_at")
        )
        for job in interrupted:
            _fail_job(
                job,
                "WORKER_INTERRUPTED",
                "El trabajador se interrumpió antes de guardar el resultado; solicita una nueva generación si aún la necesitas",
            )
            failed_count += 1
        interrupted_syntheses = list(
            AIGenerationBatchSynthesis.objects.select_for_update()
            .filter(status=AIGenerationBatchSynthesis.Status.RUNNING)
            .order_by("started_at", "created_at")
        )
        for item in interrupted_syntheses:
            item.status = AIGenerationBatchSynthesis.Status.FAILED
            item.error_code = "WORKER_INTERRUPTED"
            item.error_message = "El trabajador se interrumpió antes de guardar la síntesis; solicita una nueva síntesis si aún la necesitas"
            item.finished_at = timezone.now()
            item.save(update_fields=["status", "error_code", "error_message", "finished_at"])
            failed_count += 1
    return failed_count


def cancel_ai_job(actor: Any, project_id: UUID, job_id: UUID) -> dict[str, Any]:
    """Cancela un trabajo en cola antes de su ejecución."""
    project = require_project(actor, project_id, owner_only=True)
    with transaction.atomic():
        job = AIGenerationJob.objects.select_for_update().filter(project=project, pk=job_id).first()
        if not job:
            raise DomainError("NOT_FOUND", "Trabajo de generación no encontrado en el proyecto")
        can_cancel_running_by_agent = (
            job.execution_mode == AIGenerationJob.ExecutionMode.BYOA
            and job.status == AIGenerationJob.Status.RUNNING
        )
        if job.status != AIGenerationJob.Status.QUEUED and not can_cancel_running_by_agent:
            raise DomainError(
                "JOB_NOT_CANCELLABLE",
                f"No se puede cancelar un trabajo en estado '{job.status}'",
            )
        job.status = AIGenerationJob.Status.CANCELLED
        job.finished_at = timezone.now()
        job.lease_expires_at = None
        job.save(update_fields=["status", "finished_at", "lease_expires_at"])
    return present_ai_job(job)




