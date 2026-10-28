"""Síntesis IA trazable de outputs exitosos de un lote B6.1."""

import hashlib
import json
import logging
from typing import Any
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from thesis.integrations.llm import (
    LLMError, LLMMessage, LLMOutputInvalidError, get_llm_adapter,
)
from thesis.models import (
    AIGenerationBatch, AIGenerationBatchItem, AIGenerationBatchSynthesis,
    AIGenerationJob,
)
from thesis.services.access import require_project
from thesis.services.errors import DomainError

logger = logging.getLogger(__name__)
SYNTHESIS_PROMPT_VERSION = 1
SYNTHESIS_PROMPT = (
    "Sintetiza comparativamente las salidas JSON que se te proporcionan. No escribas capítulos ni "
    "conviertas propuestas en hechos. Cada acuerdo, diferencia y recomendación debe citar los task_id "
    "de las salidas que lo sustentan. No inventes tareas, fuentes, datos o consenso. Si la evidencia "
    "no permite concluir algo, decláralo en gaps. Devuelve solo el objeto JSON del esquema."
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SynthesisAgreement(_StrictModel):
    claim: str = Field(min_length=1, max_length=1200)
    source_task_ids: list[str] = Field(min_length=1, max_length=8)


class SynthesisObservation(_StrictModel):
    task_id: str = Field(min_length=1, max_length=50)
    observation: str = Field(min_length=1, max_length=1200)


class SynthesisDifference(_StrictModel):
    topic: str = Field(min_length=1, max_length=300)
    observations: list[SynthesisObservation] = Field(min_length=1, max_length=8)


class SynthesisGap(_StrictModel):
    description: str = Field(min_length=1, max_length=1200)
    related_task_ids: list[str] = Field(default_factory=list, max_length=8)


class SynthesisRecommendation(_StrictModel):
    recommendation: str = Field(min_length=1, max_length=1200)
    rationale: str = Field(min_length=1, max_length=1200)
    source_task_ids: list[str] = Field(min_length=1, max_length=8)


class BatchSynthesisOutput(_StrictModel):
    summary: str = Field(min_length=1, max_length=3000)
    summary_source_task_ids: list[str] = Field(min_length=1, max_length=8)
    agreements: list[SynthesisAgreement] = Field(default_factory=list, max_length=12)
    differences: list[SynthesisDifference] = Field(default_factory=list, max_length=12)
    gaps: list[SynthesisGap] = Field(default_factory=list, max_length=12)
    recommendations: list[SynthesisRecommendation] = Field(default_factory=list, max_length=12)


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _source_output_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _present_synthesis(item: AIGenerationBatchSynthesis) -> dict:
    if _hash(item.source_snapshot) != item.source_snapshot_sha256:
        raise DomainError("OUTPUT_INVALID", "El snapshot de fuentes de la síntesis no coincide con su hash")
    if item.status == AIGenerationBatchSynthesis.Status.SUCCEEDED and (
        not item.output_sha256 or _hash(item.output_data) != item.output_sha256
    ):
        raise DomainError("OUTPUT_INVALID", "El output de síntesis no coincide con su hash")
    sources = [
        {
            "job_id": source.get("job_id"),
            "task_id": source.get("task_id"),
            "output_sha256": source.get("output_sha256"),
            "acceptance_status_at_snapshot": source.get("acceptance_status"),
        }
        for source in item.source_snapshot
    ]
    return {
        "synthesis_id": str(item.id),
        "batch_id": str(item.batch_id),
        "project_id": str(item.batch.project_id),
        "status": item.status,
        "decision_status": item.decision_status,
        "request_sha256": item.request_sha256,
        "source_snapshot_sha256": item.source_snapshot_sha256,
        "sources": sources,
        "output_data": item.output_data if item.status == AIGenerationBatchSynthesis.Status.SUCCEEDED else None,
        "output_sha256": item.output_sha256 if item.status == AIGenerationBatchSynthesis.Status.SUCCEEDED else "",
        "provider": item.provider or None,
        "model": item.model or None,
        "usage": item.usage_data,
        "error_code": item.error_code or None,
        "error_message": item.error_message or None,
        "decision_reason": item.decision_reason or None,
        "attempts": item.attempts,
        "created_at": item.created_at.isoformat(),
        "started_at": item.started_at.isoformat() if item.started_at else None,
        "finished_at": item.finished_at.isoformat() if item.finished_at else None,
        "decision_at": item.decision_at.isoformat() if item.decision_at else None,
    }


def _make_source_snapshot(batch: AIGenerationBatch, requested_ids: list[UUID]) -> tuple[list[dict], list[str]]:
    items = list(
        AIGenerationBatchItem.objects.filter(batch=batch, job_id__in=requested_ids)
        .select_related("job").order_by("item_order")
    )
    if len(items) != len(requested_ids):
        raise DomainError("NOT_FOUND", "Uno o más jobs no pertenecen a este lote")
    sources = []
    task_ids = []
    for item in items:
        job = item.job
        if job.status != AIGenerationJob.Status.SUCCEEDED or not isinstance(job.output_data, dict):
            raise DomainError("BATCH_SYNTHESIS_NOT_READY", "Todos los outputs seleccionados deben estar SUCCEEDED")
        if not job.output_sha256 or _source_output_hash(job.output_data) != job.output_sha256:
            raise DomainError("OUTPUT_INVALID", f"El output persistido de '{job.workflow_task_id}' no coincide con su hash")
        sources.append({
            "job_id": str(job.id),
            "task_id": item.task_id,
            "output_sha256": job.output_sha256,
            "acceptance_status": job.acceptance_status,
            "output_data": job.output_data,
        })
        task_ids.append(item.task_id)
    return sources, task_ids


def create_batch_synthesis(
    actor: Any, project_id: UUID, batch_id: UUID, job_ids: list[UUID], idempotency_key: UUID,
) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    if not isinstance(job_ids, list) or not 2 <= len(job_ids) <= 8 or len(set(job_ids)) != len(job_ids):
        raise DomainError("VALIDATION_ERROR", "job_ids debe contener de 2 a 8 IDs distintos")
    request_data = {"batch_id": str(batch_id), "job_ids": sorted(str(value) for value in job_ids)}
    request_hash = _hash(request_data)
    with transaction.atomic():
        batch = AIGenerationBatch.objects.select_for_update().filter(project=project, pk=batch_id).first()
        if batch is None:
            raise DomainError("NOT_FOUND", "Lote de generación no encontrado")
        existing = AIGenerationBatchSynthesis.objects.filter(batch=batch, idempotency_key=idempotency_key).first()
        if existing:
            if existing.request_sha256 != request_hash:
                raise DomainError("IDEMPOTENCY_CONFLICT", "La clave ya fue usada para otra selección de síntesis")
            return _present_synthesis(existing)
        sources, task_ids = _make_source_snapshot(batch, job_ids)
        if len(set(task_ids)) != len(task_ids):
            raise DomainError("VALIDATION_ERROR", "La síntesis requiere tareas distintas")
        source_hash = _hash(sources)
        request = AIGenerationBatchSynthesis.objects.create(
            batch=batch,
            requested_by=actor,
            idempotency_key=idempotency_key,
            request_data=request_data,
            request_sha256=request_hash,
            source_snapshot=sources,
            source_snapshot_sha256=source_hash,
            prompt_text_used=SYNTHESIS_PROMPT,
            prompt_version_used=SYNTHESIS_PROMPT_VERSION,
            output_schema_used=BatchSynthesisOutput.model_json_schema(),
            status=AIGenerationBatchSynthesis.Status.QUEUED,
        )
        return _present_synthesis(request)


def get_batch_synthesis(actor: Any, project_id: UUID, batch_id: UUID, synthesis_id: UUID) -> dict:
    project = require_project(actor, project_id)
    item = AIGenerationBatchSynthesis.objects.select_related("batch").filter(
        batch__project=project, batch_id=batch_id, pk=synthesis_id,
    ).first()
    if item is None:
        raise DomainError("NOT_FOUND", "Síntesis de lote no encontrada")
    return _present_synthesis(item)


def list_batch_syntheses(actor: Any, project_id: UUID, batch_id: UUID) -> list[dict]:
    project = require_project(actor, project_id)
    batch = AIGenerationBatch.objects.filter(project=project, pk=batch_id).first()
    if batch is None:
        raise DomainError("NOT_FOUND", "Lote de generación no encontrado")
    return [
        _present_synthesis(item)
        for item in AIGenerationBatchSynthesis.objects.filter(batch=batch).select_related("batch")[:50]
    ]


def cancel_batch_synthesis(actor: Any, project_id: UUID, batch_id: UUID, synthesis_id: UUID) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    with transaction.atomic():
        item = AIGenerationBatchSynthesis.objects.select_for_update().select_related("batch").filter(
            batch__project=project, batch_id=batch_id, pk=synthesis_id,
        ).first()
        if item is None:
            raise DomainError("NOT_FOUND", "Síntesis de lote no encontrada")
        if item.status != AIGenerationBatchSynthesis.Status.QUEUED:
            raise DomainError("JOB_NOT_CANCELLABLE", "Solo se puede cancelar una síntesis que sigue QUEUED")
        item.status = AIGenerationBatchSynthesis.Status.CANCELLED
        item.finished_at = timezone.now()
        item.save(update_fields=["status", "finished_at"])
    return _present_synthesis(item)


def decide_batch_synthesis(
    actor: Any, project_id: UUID, batch_id: UUID, synthesis_id: UUID,
    decision: str, decision_key: UUID, reason: str = "",
) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    if decision not in {"ACCEPTED", "REJECTED"}:
        raise DomainError("VALIDATION_ERROR", "decision debe ser ACCEPTED o REJECTED")
    reason = reason.strip()
    if len(reason) > 1000:
        raise DomainError("VALIDATION_ERROR", "reason no puede superar 1000 caracteres")
    with transaction.atomic():
        item = AIGenerationBatchSynthesis.objects.select_for_update().select_related("batch").filter(
            batch__project=project, batch_id=batch_id, pk=synthesis_id,
        ).first()
        if item is None:
            raise DomainError("NOT_FOUND", "Síntesis de lote no encontrada")
        if item.status != AIGenerationBatchSynthesis.Status.SUCCEEDED:
            raise DomainError("VERSION_CONFLICT", "Solo se puede revisar una síntesis SUCCEEDED")
        if item.decision_status != AIGenerationBatchSynthesis.DecisionStatus.PENDING_REVIEW:
            if item.decision_key == decision_key and item.decision_status == decision and item.decision_reason == reason:
                return _present_synthesis(item)
            raise DomainError("VERSION_CONFLICT", "La síntesis ya recibió una decisión final")
        item.decision_status = decision
        item.decision_by = actor
        item.decision_key = decision_key
        item.decision_reason = reason
        item.decision_at = timezone.now()
        item.save(update_fields=["decision_status", "decision_by", "decision_key", "decision_reason", "decision_at"])
    return _present_synthesis(item)


def _fail_synthesis(item: AIGenerationBatchSynthesis, error_code: str, error_message: str) -> None:
    item.status = AIGenerationBatchSynthesis.Status.FAILED
    item.error_code = error_code[:50]
    item.error_message = error_message[:2000]
    item.finished_at = timezone.now()
    item.save(update_fields=["status", "error_code", "error_message", "finished_at"])


def process_batch_synthesis_job(synthesis_id: UUID, *, already_claimed: bool = False) -> AIGenerationBatchSynthesis | None:
    with transaction.atomic():
        item = AIGenerationBatchSynthesis.objects.select_for_update().select_related("batch").filter(pk=synthesis_id).first()
        expected = AIGenerationBatchSynthesis.Status.RUNNING if already_claimed else AIGenerationBatchSynthesis.Status.QUEUED
        if item is None or item.status != expected:
            return item
        if not already_claimed:
            item.status = AIGenerationBatchSynthesis.Status.RUNNING
            item.started_at = timezone.now()
            item.attempts += 1
            item.save(update_fields=["status", "started_at", "attempts"])
        if _hash(item.source_snapshot) != item.source_snapshot_sha256:
            _fail_synthesis(item, "OUTPUT_INVALID", "El snapshot de entradas de síntesis no coincide con su hash")
            return item
        sources = item.source_snapshot

    try:
        adapter = get_llm_adapter()
        result = adapter.generate_structured(
            messages=[
                LLMMessage(role="system", content=item.prompt_text_used),
                LLMMessage(
                    role="user",
                    content=(
                        "Integra solo estas propuestas de tareas independientes. Conserva las referencias "
                        "a task_id y distingue acuerdos, diferencias, vacíos y recomendaciones.\n\n"
                        + json.dumps(sources, ensure_ascii=False)
                    ),
                ),
            ],
            output_schema=item.output_schema_used,
            timeout=30.0,
        )
        output = BatchSynthesisOutput.model_validate(result.content_json).model_dump()
        allowed_task_ids = {source["task_id"] for source in sources}
        referenced = set(output["summary_source_task_ids"])
        for group in (output["agreements"], output["recommendations"]):
            for entry in group:
                referenced.update(entry["source_task_ids"])
        for difference in output["differences"]:
            referenced.update(observation["task_id"] for observation in difference["observations"])
        for gap in output["gaps"]:
            referenced.update(gap["related_task_ids"])
        if not referenced.issubset(allowed_task_ids):
            raise LLMOutputInvalidError("La síntesis refiere task_id que no forma parte del snapshot")
        if not referenced:
            raise LLMOutputInvalidError("La síntesis no conserva referencias a los outputs seleccionados")
    except LLMError as exc:
        with transaction.atomic():
            current = AIGenerationBatchSynthesis.objects.select_for_update().get(pk=synthesis_id)
            if current.status == AIGenerationBatchSynthesis.Status.RUNNING:
                _fail_synthesis(current, exc.code, str(exc))
            return current
    except (ValidationError, ValueError, TypeError) as exc:
        with transaction.atomic():
            current = AIGenerationBatchSynthesis.objects.select_for_update().get(pk=synthesis_id)
            if current.status == AIGenerationBatchSynthesis.Status.RUNNING:
                _fail_synthesis(current, "OUTPUT_INVALID", str(exc))
            return current
    except Exception:
        logger.exception("Falla inesperada al sintetizar lote %s", synthesis_id)
        with transaction.atomic():
            current = AIGenerationBatchSynthesis.objects.select_for_update().get(pk=synthesis_id)
            if current.status == AIGenerationBatchSynthesis.Status.RUNNING:
                _fail_synthesis(current, "PROVIDER_UNAVAILABLE", "Falla inesperada en el proveedor de IA")
            return current

    output_hash = _hash(output)
    with transaction.atomic():
        current = AIGenerationBatchSynthesis.objects.select_for_update().get(pk=synthesis_id)
        if current.status != AIGenerationBatchSynthesis.Status.RUNNING:
            return current
        current.output_data = output
        current.output_sha256 = output_hash
        current.provider = result.provider
        current.model = result.model
        current.usage_data = result.usage or {}
        current.status = AIGenerationBatchSynthesis.Status.SUCCEEDED
        current.finished_at = timezone.now()
        current.save(update_fields=["output_data", "output_sha256", "provider", "model", "usage_data", "status", "finished_at"])
    return current
