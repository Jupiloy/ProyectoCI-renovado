"""Vincula afirmaciones y pasajes; solo el asesor puede confirmar respaldo."""

import hashlib

from django.db import transaction
from django.utils import timezone

from thesis.models import ChapterRevision, EvidenceLink, ProjectParticipant, SourceExcerpt
from thesis.services.access import require_project
from thesis.services.errors import DomainError


def _present(link: EvidenceLink) -> dict:
    return {"evidence_link_id": link.pk, "project_id": str(link.project_id),
            "revision_id": link.revision_id, "source_id": str(link.excerpt.source_id),
            "physical_page": link.excerpt.page_no, "excerpt_id": link.excerpt_id,
            "claim_text": link.claim_text, "matched_text": link.matched_text,
            "start_char": link.start_char, "end_char": link.end_char,
            "excerpt_sha256": link.excerpt_sha256, "status": link.status,
            "reviewed_by_id": link.reviewed_by_id, "review_note": link.review_note,
            "automatically_verified": False}


def create_evidence_link(actor, project_id, excerpt_id: int, claim_text: str,
                         start_char: int, end_char: int, matched_text: str,
                         revision_id: int | None = None) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    claim_text = claim_text.strip()
    if not 10 <= len(claim_text) <= 1000:
        raise DomainError("VALIDATION_ERROR", "La afirmación debe tener entre 10 y 1000 caracteres")
    excerpt = SourceExcerpt.objects.select_related("source").filter(source__project=project, pk=excerpt_id).first()
    if excerpt is None or excerpt.source.verification_status != excerpt.source.Status.TEXT_CHECKED:
        raise DomainError("NOT_FOUND", "Extracto no disponible")
    digest = hashlib.sha256(excerpt.text.encode("utf-8")).hexdigest()
    if digest != excerpt.text_sha256 or start_char < 0 or end_char <= start_char or excerpt.text[start_char:end_char] != matched_text:
        raise DomainError("VALIDATION_ERROR", "El pasaje no coincide con el extracto y su hash")
    revision = None
    if revision_id is not None:
        revision = ChapterRevision.objects.filter(chapter__project=project, pk=revision_id).first()
        if revision is None or claim_text not in revision.content_md:
            raise DomainError("VALIDATION_ERROR", "La afirmación no figura en la revisión indicada")
    link = EvidenceLink.objects.create(project=project, revision=revision, excerpt=excerpt,
                                       claim_text=claim_text, start_char=start_char, end_char=end_char,
                                       matched_text=matched_text, excerpt_sha256=digest, created_by=actor)
    return _present(link)


def list_evidence_links(actor, project_id, *, limit: int = 50) -> list[dict]:
    project = require_project(actor, project_id)
    if not 1 <= limit <= 100:
        raise DomainError("VALIDATION_ERROR", "Límite inválido")
    return [_present(link) for link in EvidenceLink.objects.filter(project=project)
            .select_related("excerpt__source").order_by("-created_at", "-id")[:limit]]


def review_evidence_link(actor, project_id, link_id: int, decision: str, note: str = "") -> dict:
    project = require_project(actor, project_id)
    if not ProjectParticipant.objects.filter(project=project, user=actor, active=True,
                                             role=ProjectParticipant.Role.ADVISOR).exists():
        raise DomainError("NOT_FOUND", "Proyecto no encontrado")
    if decision not in (EvidenceLink.Status.CONFIRMED, EvidenceLink.Status.REJECTED):
        raise DomainError("VALIDATION_ERROR", "Decisión inválida")
    with transaction.atomic():
        link = EvidenceLink.objects.select_for_update().select_related("excerpt__source").filter(project=project, pk=link_id).first()
        if link is None:
            raise DomainError("NOT_FOUND", "Vínculo de evidencia no encontrado")
        if link.status != EvidenceLink.Status.CANDIDATE:
            raise DomainError("VERSION_CONFLICT", "El vínculo ya fue revisado")
        if hashlib.sha256(link.excerpt.text.encode("utf-8")).hexdigest() != link.excerpt_sha256:
            raise DomainError("VERSION_CONFLICT", "El texto extraído cambió después de crear el vínculo")
        link.status = decision
        link.reviewed_by = actor
        link.reviewed_at = timezone.now()
        link.review_note = note.strip()[:2000]
        link.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note"])
    return _present(link)
