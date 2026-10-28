"""Casos de uso para decisiones humanas, versionadas, sobre duplicados candidatos."""

from uuid import UUID

from django.db import transaction
from django.db.models import Max

from thesis.models import Project, SourceDocument, SourceDuplicateDecision
from thesis.services.access import require_project
from thesis.services.errors import DomainError
from thesis.services.source_duplicates import duplicate_match


def _uuid(value, field: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise DomainError("VALIDATION_ERROR", f"{field} debe ser UUID") from exc


def _present(row: SourceDuplicateDecision, *, is_current: bool) -> dict:
    return {
        "decision_id": str(row.id), "project_id": str(row.project_id),
        "source_a_id": str(row.source_a_id), "source_b_id": str(row.source_b_id),
        "decision_no": row.decision_no, "match_basis": row.match_basis, "decision": row.decision,
        "primary_source_id": str(row.primary_source_id) if row.primary_source_id else None, "note": row.note,
        "created_by_id": row.created_by_id, "idempotency_key": str(row.idempotency_key),
        "created_at": row.created_at.isoformat(), "is_current": is_current,
    }


def decide_source_duplicate(actor, project_id, source_id, other_source_id, decision: str,
                            note: str = "", idempotency_key=None, primary_source_id=None) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    source_uuid = _uuid(source_id, "source_id")
    other_uuid = _uuid(other_source_id, "other_source_id")
    key = _uuid(idempotency_key, "idempotency_key")
    primary_uuid = _uuid(primary_source_id, "primary_source_id") if primary_source_id else None
    if source_uuid == other_uuid:
        raise DomainError("VALIDATION_ERROR", "Se requieren dos fuentes diferentes")
    try:
        decision_value = SourceDuplicateDecision.Decision(decision)
    except ValueError as exc:
        raise DomainError("VALIDATION_ERROR", "decision no es una opción admitida") from exc
    if (decision_value == SourceDuplicateDecision.Decision.SET_PRIMARY) != (primary_uuid is not None):
        raise DomainError("VALIDATION_ERROR", "SET_PRIMARY requiere primary_source_id; las otras decisiones no lo admiten")
    if primary_uuid and primary_uuid not in {source_uuid, other_uuid}:
        raise DomainError("VALIDATION_ERROR", "primary_source_id debe ser una de las dos fuentes")
    note = str(note or "").strip()
    if len(note) > 2000:
        raise DomainError("VALIDATION_ERROR", "note supera 2000 caracteres")

    with transaction.atomic():
        # El bloqueo por proyecto serializa el número de versión y la idempotencia.
        Project.objects.select_for_update().get(pk=project.pk)
        existing_key = SourceDuplicateDecision.objects.filter(project=project, idempotency_key=key).first()
        if existing_key:
            same_pair = {existing_key.source_a_id, existing_key.source_b_id} == {source_uuid, other_uuid}
            if (not same_pair or existing_key.decision != decision_value or existing_key.note != note
                    or existing_key.primary_source_id != primary_uuid):
                raise DomainError("IDEMPOTENCY_CONFLICT", "idempotency_key ya se usó para otra decisión")
            latest_no = SourceDuplicateDecision.objects.filter(
                project=project, source_a_id=existing_key.source_a_id, source_b_id=existing_key.source_b_id,
            ).aggregate(value=Max("decision_no"))["value"]
            return {**_present(existing_key, is_current=existing_key.decision_no == latest_no),
                    "created": False, "match": existing_key.match_basis}

        sources = {
            source.id: source for source in SourceDocument.objects.select_for_update().filter(
                project=project, pk__in=[source_uuid, other_uuid], kind=SourceDocument.Kind.EXTERNAL,
            )
        }
        if len(sources) != 2:
            raise DomainError("NOT_FOUND", "Fuentes externas no encontradas en este proyecto")
        source_a, source_b = sorted(sources.values(), key=lambda item: str(item.id))
        match = duplicate_match(source_a, source_b)
        if match is None:
            raise DomainError("VALIDATION_ERROR", "Las fuentes no coinciden por DOI ni por título normalizado")

        decision_no = (SourceDuplicateDecision.objects.filter(
            project=project, source_a=source_a, source_b=source_b,
        ).aggregate(value=Max("decision_no"))["value"] or 0) + 1
        row = SourceDuplicateDecision.objects.create(
            project=project, source_a=source_a, source_b=source_b, decision_no=decision_no, match_basis=match,
            decision=decision_value, primary_source_id=primary_uuid, note=note,
            created_by=actor, idempotency_key=key,
        )
        return {**_present(row, is_current=True), "created": True, "match": match}


def list_source_duplicate_decisions(actor, project_id) -> dict:
    project = require_project(actor, project_id)
    rows = list(SourceDuplicateDecision.objects.filter(project=project).select_related(
        "source_a", "source_b",
    ).order_by("source_a_id", "source_b_id", "decision_no"))
    current = {(row.source_a_id, row.source_b_id): row.decision_no for row in rows}
    return {
        "project_id": str(project.id),
        "decisions": [
            {**_present(row, is_current=row.decision_no == current[(row.source_a_id, row.source_b_id)]),
             "source_a_title": row.source_a.title, "source_b_title": row.source_b.title}
            for row in rows
        ],
    }
