"""Enlace trazable entre una cita, la afirmación y un pasaje; sin evaluación semántica automática."""

import hashlib
from uuid import UUID

from django.db import transaction

from thesis.models import (
    ChapterCitationOccurrence, CitationEvidenceReview, ProjectParticipant,
    SourceExcerpt, SourceMetadataCheck,
)
from thesis.services.access import require_project
from thesis.services.errors import DomainError


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _present(review: CitationEvidenceReview) -> dict:
    source = review.occurrence.source
    return {
        "review_id": str(review.id),
        "occurrence_id": str(review.occurrence_id),
        "source_id": str(source.id),
        "source_identity": "CROSSREF_CHECKED" if SourceMetadataCheck.objects.filter(source=source).exists()
        else "NOT_CHECKED",
        "source_text_status": source.verification_status,
        "automated_semantic_assessment": "NOT_PERFORMED",
        "chapter_document_revision_id": str(review.occurrence.document_revision_id),
        "claim_text": review.claim_text,
        "claim_sha256": review.claim_sha256,
        "claim_range": {"start": review.claim_start, "end": review.claim_end},
        "excerpt_id": review.excerpt_id,
        "physical_page": review.excerpt.page_no,
        "matched_text": review.matched_text,
        "excerpt_range": {"start": review.excerpt_start, "end": review.excerpt_end},
        "excerpt_sha256": review.excerpt_sha256,
        "status": review.status,
        "review_version": review.review_version,
        "previous_review_id": str(review.previous_review_id) if review.previous_review_id else None,
        "review_note": review.review_note,
        "created_by_id": review.created_by_id,
        "created_at": review.created_at.isoformat(),
    }


def _get_occurrence(project, chapter_no: int, occurrence_id) -> ChapterCitationOccurrence:
    try:
        normalized_id = UUID(str(occurrence_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise DomainError("VALIDATION_ERROR", "occurrence_id debe ser UUID") from exc
    occurrence = ChapterCitationOccurrence.objects.select_related(
        "source", "document_revision__document__chapter",
    ).filter(
        pk=normalized_id,
        document_revision__document__chapter__project=project,
        document_revision__document__chapter__number=chapter_no,
    ).first()
    if occurrence is None:
        raise DomainError("NOT_FOUND", "Ocurrencia de cita no encontrada")
    return occurrence


def create_citation_evidence_candidate(
    actor, project_id, chapter_no: int, occurrence_id, excerpt_id: int,
    claim_start: int, claim_end: int, excerpt_start: int, excerpt_end: int,
    idempotency_key,
) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    occurrence = _get_occurrence(project, chapter_no, occurrence_id)
    try:
        key = UUID(str(idempotency_key))
    except (ValueError, TypeError, AttributeError) as exc:
        raise DomainError("VALIDATION_ERROR", "idempotency_key debe ser UUID") from exc
    block = next((item for item in occurrence.document_revision.content_tree.get("blocks", [])
                  if item.get("id") == str(occurrence.block_id)), None)
    if not block or block.get("type") != "paragraph":
        raise DomainError("VERSION_CONFLICT", "El bloque citado ya no se puede localizar en su revisión")
    text = block["text"]
    if (type(claim_start) is not int or type(claim_end) is not int or claim_start < 0
            or claim_end > len(text) or claim_end <= claim_start
            or not claim_start <= occurrence.char_offset <= claim_end):
        raise DomainError("VALIDATION_ERROR", "El rango de afirmación debe incluir el ancla de la cita")
    claim_text = text[claim_start:claim_end]
    if not 10 <= len(claim_text.strip()) <= 1000:
        raise DomainError("VALIDATION_ERROR", "La afirmación seleccionada debe tener entre 10 y 1000 caracteres")

    excerpt = SourceExcerpt.objects.select_related("source").filter(
        source__project=project, pk=excerpt_id,
    ).first()
    if excerpt is None or excerpt.source_id != occurrence.source_id:
        raise DomainError("NOT_FOUND", "El pasaje no pertenece a la fuente citada")
    if excerpt.source.verification_status != excerpt.source.Status.TEXT_CHECKED:
        raise DomainError("INSUFFICIENT_ACCESS", "La fuente aún no tiene texto extraído y verificable")
    if _digest(excerpt.text) != excerpt.text_sha256:
        raise DomainError("VERSION_CONFLICT", "El hash del pasaje no coincide con el texto almacenado")
    if (type(excerpt_start) is not int or type(excerpt_end) is not int or excerpt_start < 0
            or excerpt_end > len(excerpt.text) or excerpt_end <= excerpt_start):
        raise DomainError("VALIDATION_ERROR", "Rango del pasaje inválido")

    with transaction.atomic():
        prior = CitationEvidenceReview.objects.filter(occurrence=occurrence).order_by("-review_version").first()
        version = prior.review_version + 1 if prior else 1
        existing = CitationEvidenceReview.objects.filter(occurrence=occurrence, idempotency_key=key).first()
        if existing:
            if (existing.excerpt_id != excerpt.id or existing.claim_start != claim_start
                    or existing.claim_end != claim_end or existing.excerpt_start != excerpt_start
                    or existing.excerpt_end != excerpt_end):
                raise DomainError("IDEMPOTENCY_CONFLICT", "idempotency_key ya se usó con otro pasaje")
            return _present(existing) | {"idempotent": True}
        matched_text = excerpt.text[excerpt_start:excerpt_end]
        if not matched_text.strip():
            raise DomainError("VALIDATION_ERROR", "El rango del pasaje no puede estar vacío")
        review = CitationEvidenceReview.objects.create(
            occurrence=occurrence, excerpt=excerpt, claim_text=claim_text,
            claim_start=claim_start, claim_end=claim_end, claim_sha256=_digest(claim_text),
            excerpt_start=excerpt_start, excerpt_end=excerpt_end, matched_text=matched_text,
            excerpt_sha256=excerpt.text_sha256, status=CitationEvidenceReview.Status.CANDIDATE,
            review_version=version, previous_review=prior, idempotency_key=key, created_by=actor,
        )
    return _present(review) | {"idempotent": False}


def review_citation_evidence(actor, project_id, chapter_no: int, review_id, status: str,
                             expected_version: int, idempotency_key, note: str = "") -> dict:
    project = require_project(actor, project_id)
    if not ProjectParticipant.objects.filter(
        project=project, user=actor, active=True, role=ProjectParticipant.Role.ADVISOR,
    ).exists():
        raise DomainError("NOT_FOUND", "Proyecto no encontrado")
    if status not in {
        CitationEvidenceReview.Status.SUPPORTS, CitationEvidenceReview.Status.CONTRADICTS,
        CitationEvidenceReview.Status.UNRELATED, CitationEvidenceReview.Status.INSUFFICIENT,
    }:
        raise DomainError("VALIDATION_ERROR", "La decisión del asesor no está admitida")
    try:
        normalized_id = UUID(str(review_id))
        key = UUID(str(idempotency_key))
    except (ValueError, TypeError, AttributeError) as exc:
        raise DomainError("VALIDATION_ERROR", "review_id e idempotency_key deben ser UUID") from exc

    with transaction.atomic():
        prior = CitationEvidenceReview.objects.select_for_update().filter(
            occurrence__document_revision__document__chapter__project=project,
            occurrence__document_revision__document__chapter__number=chapter_no,
            pk=normalized_id,
        ).select_related("occurrence__source", "excerpt", "occurrence").first()
        if prior is None:
            raise DomainError("NOT_FOUND", "Revisión de evidencia no encontrada")
        latest = CitationEvidenceReview.objects.select_for_update().filter(
            occurrence=prior.occurrence,
        ).order_by("-review_version").first()
        existing = CitationEvidenceReview.objects.filter(occurrence=prior.occurrence, idempotency_key=key).first()
        if existing:
            if (existing.status != status or existing.previous_review_id != prior.id
                    or existing.review_note != note.strip()[:2000]):
                raise DomainError("IDEMPOTENCY_CONFLICT", "idempotency_key ya se usó con otra decisión")
            return _present(existing) | {"idempotent": True}
        if latest.pk != prior.pk or prior.review_version != expected_version:
            raise DomainError("VERSION_CONFLICT", "La evaluación cambió; carga el historial vigente")
        if hashlib.sha256(prior.excerpt.text.encode("utf-8")).hexdigest() != prior.excerpt_sha256:
            raise DomainError("VERSION_CONFLICT", "El pasaje cambió después de crear la evaluación")
        review = CitationEvidenceReview.objects.create(
            occurrence=prior.occurrence, excerpt=prior.excerpt, claim_text=prior.claim_text,
            claim_start=prior.claim_start, claim_end=prior.claim_end, claim_sha256=prior.claim_sha256,
            excerpt_start=prior.excerpt_start, excerpt_end=prior.excerpt_end,
            matched_text=prior.matched_text, excerpt_sha256=prior.excerpt_sha256,
            status=status, review_version=prior.review_version + 1, previous_review=prior,
            idempotency_key=key, review_note=note.strip()[:2000], created_by=actor,
        )
    return _present(review) | {"idempotent": False}


def list_citation_evidence(actor, project_id, chapter_no: int, occurrence_id) -> list[dict]:
    project = require_project(actor, project_id)
    occurrence = _get_occurrence(project, chapter_no, occurrence_id)
    return [_present(row) for row in CitationEvidenceReview.objects.filter(
        occurrence=occurrence,
    ).select_related("occurrence__source", "excerpt", "previous_review", "created_by").order_by("review_version")]
