"""Casos de uso versionados para estrategias y ejecuciones manuales de búsqueda."""

import hashlib
import json
from datetime import date
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from django.db import IntegrityError, transaction
from django.db.models import F, OuterRef, Subquery
from django.utils import timezone

from thesis.models import Project, SearchExecution, SearchStrategy
from thesis.services.access import require_project
from thesis.services.errors import DomainError


STRATEGY_FIELDS = ("provider", "title", "topic", "query_text", "search_equation", "concepts", "filters", "search_url")


def _payload_hash(payload: dict) -> str:
    canonical = {key: payload.get(key) for key in STRATEGY_FIELDS}
    blob = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalize_strategy(payload: dict) -> dict:
    provider = str(payload.get("provider", "")).strip().upper()
    if provider not in SearchStrategy.Provider.values:
        raise DomainError("VALIDATION_ERROR", "Proveedor no admitido para una estrategia de búsqueda")
    title = str(payload.get("title", "")).strip()
    topic = str(payload.get("topic", "")).strip()
    query_text = str(payload.get("query_text", "")).strip()
    equation = str(payload.get("search_equation", "")).strip()
    if not 2 <= len(title) <= 160 or not 3 <= len(topic) <= 1000 or not 3 <= len(query_text) <= 2000:
        raise DomainError("VALIDATION_ERROR", "Título, tema o consulta están vacíos o exceden sus límites")
    if len(equation) > 5000:
        raise DomainError("VALIDATION_ERROR", "La ecuación supera 5000 caracteres")

    concepts = payload.get("concepts", [])
    if not isinstance(concepts, list) or len(concepts) > 30:
        raise DomainError("VALIDATION_ERROR", "concepts debe ser una lista de hasta 30 términos")
    normalized_concepts = []
    for concept in concepts:
        if not isinstance(concept, str) or not 1 <= len(concept.strip()) <= 160:
            raise DomainError("VALIDATION_ERROR", "Cada concepto debe tener entre 1 y 160 caracteres")
        value = concept.strip()
        if value not in normalized_concepts:
            normalized_concepts.append(value)

    filters = payload.get("filters", {})
    if not isinstance(filters, dict):
        raise DomainError("VALIDATION_ERROR", "filters debe ser un objeto JSON")
    try:
        filters_blob = json.dumps(filters, ensure_ascii=False, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise DomainError("VALIDATION_ERROR", "filters contiene valores no válidos para JSON") from exc
    if len(filters_blob.encode("utf-8")) > 20_000:
        raise DomainError("VALIDATION_ERROR", "filters supera 20 KiB")

    search_url = str(payload.get("search_url", "")).strip()
    if search_url:
        parsed = urlsplit(search_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise DomainError("VALIDATION_ERROR", "search_url debe usar HTTPS")
        host = parsed.hostname.lower().rstrip(".")
        allowed_suffix = {
            SearchStrategy.Provider.SCOPUS: "scopus.com",
            SearchStrategy.Provider.WEB_OF_SCIENCE: "webofscience.com",
        }.get(provider)
        if allowed_suffix and host != allowed_suffix and not host.endswith(f".{allowed_suffix}"):
            raise DomainError("VALIDATION_ERROR", "La URL no pertenece al sitio oficial de la base seleccionada")
        if len(search_url) > 2048:
            raise DomainError("VALIDATION_ERROR", "search_url supera 2048 caracteres")

    return {
        "provider": provider,
        "title": title,
        "topic": topic,
        "query_text": query_text,
        "search_equation": equation,
        "concepts_json": normalized_concepts,
        "filters_json": filters,
        "search_url": search_url,
    }


def _serialize_strategy(strategy: SearchStrategy) -> dict:
    return {
        "strategy_id": str(strategy.id),
        "series_id": str(strategy.series_id),
        "version_no": strategy.version_no,
        "supersedes_strategy_id": str(strategy.supersedes_id) if strategy.supersedes_id else None,
        "provider": strategy.provider,
        "title": strategy.title,
        "topic": strategy.topic,
        "query_text": strategy.query_text,
        "search_equation": strategy.search_equation,
        "concepts": strategy.concepts_json,
        "filters": strategy.filters_json,
        "search_url": strategy.search_url,
        "content_sha256": strategy.content_sha256,
        "created_by_id": strategy.created_by_id,
        "created_at": strategy.created_at.isoformat(),
    }


def _strategy_by_id(actor, project_id, strategy_id, *, lock=False) -> SearchStrategy:
    require_project(actor, project_id)
    query = SearchStrategy.objects.filter(project_id=project_id, pk=strategy_id)
    if lock:
        query = query.select_for_update()
    strategy = query.first()
    if strategy is None:
        raise DomainError("NOT_FOUND", "Estrategia de búsqueda no encontrada")
    return strategy


def create_search_strategy(actor, project_id, payload: dict) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    data = _normalize_strategy(payload)
    digest = _payload_hash({
        "provider": data["provider"], "title": data["title"], "topic": data["topic"],
        "query_text": data["query_text"], "search_equation": data["search_equation"],
        "concepts": data["concepts_json"], "filters": data["filters_json"], "search_url": data["search_url"],
    })
    key = payload.get("idempotency_key")
    if not key:
        raise DomainError("VALIDATION_ERROR", "idempotency_key es obligatorio")
    try:
        key = UUID(str(key))
    except (TypeError, ValueError) as exc:
        raise DomainError("VALIDATION_ERROR", "idempotency_key debe ser UUID") from exc

    with transaction.atomic():
        prior = SearchStrategy.objects.filter(project=project, idempotency_key=key).first()
        if prior:
            if prior.created_by_id != actor.pk or prior.content_sha256 != digest:
                raise DomainError("IDEMPOTENCY_CONFLICT", "idempotency_key ya se usó con otra estrategia")
            return _serialize_strategy(prior)
        try:
            strategy = SearchStrategy.objects.create(
                project=project, series_id=uuid4(), version_no=1, content_sha256=digest,
                idempotency_key=key, created_by=actor, **data,
            )
        except IntegrityError as exc:
            raise DomainError("IDEMPOTENCY_CONFLICT", "La estrategia colisionó con una escritura concurrente") from exc
    return _serialize_strategy(strategy)


def revise_search_strategy(actor, project_id, strategy_id, expected_version: int, payload: dict) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    data = _normalize_strategy(payload)
    digest = _payload_hash({
        "provider": data["provider"], "title": data["title"], "topic": data["topic"],
        "query_text": data["query_text"], "search_equation": data["search_equation"],
        "concepts": data["concepts_json"], "filters": data["filters_json"], "search_url": data["search_url"],
    })
    key = payload.get("idempotency_key")
    if not key:
        raise DomainError("VALIDATION_ERROR", "idempotency_key es obligatorio")
    try:
        key = UUID(str(key))
    except (TypeError, ValueError) as exc:
        raise DomainError("VALIDATION_ERROR", "idempotency_key debe ser UUID") from exc

    with transaction.atomic():
        prior = SearchStrategy.objects.filter(project=project, idempotency_key=key).first()
        if prior:
            if prior.created_by_id != actor.pk or prior.content_sha256 != digest:
                raise DomainError("IDEMPOTENCY_CONFLICT", "idempotency_key ya se usó con otra revisión")
            return _serialize_strategy(prior)
        Project.objects.select_for_update().get(pk=project.pk)
        base = SearchStrategy.objects.select_for_update().filter(project=project, pk=strategy_id).first()
        if base is None:
            raise DomainError("NOT_FOUND", "Estrategia de búsqueda no encontrada")
        latest_no = SearchStrategy.objects.filter(project=project, series_id=base.series_id).order_by("-version_no").values_list("version_no", flat=True).first()
        if expected_version != base.version_no or latest_no != base.version_no:
            raise DomainError("VERSION_CONFLICT", "La estrategia cambió; carga la última versión antes de revisarla")
        try:
            revised = SearchStrategy.objects.create(
                project=project, series_id=base.series_id, version_no=base.version_no + 1,
                supersedes=base, content_sha256=digest, idempotency_key=key,
                created_by=actor, **data,
            )
        except IntegrityError as exc:
            raise DomainError("IDEMPOTENCY_CONFLICT", "La revisión colisionó con una escritura concurrente") from exc
    return _serialize_strategy(revised)


def list_search_strategies(actor, project_id) -> list[dict]:
    project = require_project(actor, project_id)
    latest = SearchStrategy.objects.filter(project_id=OuterRef("project_id"), series_id=OuterRef("series_id")) \
        .order_by("-version_no").values("version_no")[:1]
    rows = SearchStrategy.objects.filter(project=project).annotate(latest_version=Subquery(latest)) \
        .filter(version_no=F("latest_version")).order_by("-created_at")
    return [_serialize_strategy(row) for row in rows]


def get_search_strategy_history(actor, project_id, strategy_id) -> list[dict]:
    selected = _strategy_by_id(actor, project_id, strategy_id)
    rows = SearchStrategy.objects.filter(project_id=project_id, series_id=selected.series_id).order_by("version_no")
    return [_serialize_strategy(row) for row in rows]


def record_manual_search_execution(actor, project_id, strategy_id, execution_date: date,
                                   reported_result_count: int | None, notes: str, idempotency_key) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    try:
        key = UUID(str(idempotency_key))
    except (TypeError, ValueError) as exc:
        raise DomainError("VALIDATION_ERROR", "idempotency_key debe ser UUID") from exc
    if not isinstance(execution_date, date):
        raise DomainError("VALIDATION_ERROR", "execution_date debe ser una fecha")
    if execution_date > timezone.localdate():
        raise DomainError("VALIDATION_ERROR", "execution_date no puede ser futura")
    if reported_result_count is not None and not 0 <= reported_result_count <= 1_000_000:
        raise DomainError("VALIDATION_ERROR", "reported_result_count debe estar entre 0 y 1000000")
    notes = str(notes or "").strip()
    if len(notes) > 2000:
        raise DomainError("VALIDATION_ERROR", "notes supera 2000 caracteres")
    with transaction.atomic():
        strategy = _strategy_by_id(actor, project.id, strategy_id, lock=True)
        prior = SearchExecution.objects.filter(strategy=strategy, idempotency_key=key).first()
        if prior:
            same = (prior.executed_by_id == actor.pk and prior.execution_date == execution_date
                    and prior.reported_result_count == reported_result_count and prior.notes == notes)
            if not same:
                raise DomainError("IDEMPOTENCY_CONFLICT", "idempotency_key ya se usó con otra ejecución")
            return _serialize_execution(prior)
        try:
            execution = SearchExecution.objects.create(
                strategy=strategy, executed_by=actor, execution_date=execution_date,
                reported_result_count=reported_result_count, notes=notes, idempotency_key=key,
            )
        except IntegrityError as exc:
            raise DomainError("IDEMPOTENCY_CONFLICT", "La ejecución colisionó con una escritura concurrente") from exc
    return _serialize_execution(execution)


def _serialize_execution(execution: SearchExecution) -> dict:
    return {
        "execution_id": str(execution.id),
        "strategy_id": str(execution.strategy_id),
        "strategy_version_no": execution.strategy.version_no,
        "execution_mode": "MANUAL_USER_DECLARED",
        "execution_date": execution.execution_date.isoformat(),
        "recorded_at": execution.recorded_at.isoformat(),
        "executed_by_id": execution.executed_by_id,
        "reported_result_count": execution.reported_result_count,
        "notes": execution.notes,
    }


def list_manual_search_executions(actor, project_id, strategy_id) -> list[dict]:
    strategy = _strategy_by_id(actor, project_id, strategy_id)
    return [_serialize_execution(row) for row in strategy.manual_executions.select_related("strategy").order_by("-recorded_at")]
