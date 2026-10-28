"""Propuestas trazables de sustitución de fuente con aceptación explícita y revisión nueva."""

import hashlib
import json
from uuid import UUID, uuid5

from django.db import transaction

from thesis.models import (
    ChapterCitationOccurrence, ChapterDocument, CitationReplacementDecision,
    CitationReplacementProposal, ProjectParticipant, SourceDocument,
)
from thesis.services.access import require_project
from thesis.services.chapter_documents import save_chapter_document
from thesis.services.citation_occurrences import frozen_reference, list_citation_marks
from thesis.services.errors import DomainError
from thesis.services.ieee_citations import build_ieee_citation_view


def _hash(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _present(proposal: CitationReplacementProposal, decision=None, *, idempotent=False) -> dict:
    return {
        "proposal_id": str(proposal.id),
        "occurrence_id": str(proposal.occurrence_id),
        "document_revision_id": str(proposal.document_revision_id),
        "expected_document_version": proposal.expected_document_version,
        "replacement_source_id": str(proposal.replacement_source_id),
        "previous_reference": proposal.previous_reference_snapshot,
        "replacement_reference": proposal.replacement_reference_snapshot,
        "previous_reference_sha256": proposal.previous_reference_sha256,
        "replacement_reference_sha256": proposal.replacement_reference_sha256,
        "rationale": proposal.rationale,
        "decision": ({
            "status": decision.status,
            "resulting_document_revision_id": str(decision.resulting_document_revision_id)
            if decision.resulting_document_revision_id else None,
            "decided_by_id": decision.decided_by_id,
            "decided_at": decision.decided_at.isoformat(),
            "reason": decision.reason,
        } if decision else None),
        "idempotent": idempotent,
    }


def _require_project_participant(actor, project, *, owner_only=False):
    roles = [ProjectParticipant.Role.OWNER] if owner_only else [
        ProjectParticipant.Role.OWNER, ProjectParticipant.Role.ADVISOR,
    ]
    if not ProjectParticipant.objects.filter(project=project, user=actor, active=True, role__in=roles).exists():
        raise DomainError("NOT_FOUND", "Proyecto no encontrado")


def create_citation_replacement_proposal(
    actor, project_id, chapter_no: int, occurrence_id, replacement_source_id,
    rationale: str, idempotency_key,
) -> dict:
    project = require_project(actor, project_id)
    _require_project_participant(actor, project)
    try:
        occurrence_uuid, source_uuid, key = map(UUID, map(str, (occurrence_id, replacement_source_id, idempotency_key)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise DomainError("VALIDATION_ERROR", "Los IDs deben ser UUID") from exc
    rationale = rationale.strip()
    if not 10 <= len(rationale) <= 2000:
        raise DomainError("VALIDATION_ERROR", "La justificación debe tener entre 10 y 2000 caracteres")

    with transaction.atomic():
        document = ChapterDocument.objects.select_for_update().filter(
            chapter__project=project, chapter__number=chapter_no,
        ).first()
        occurrence = ChapterCitationOccurrence.objects.select_related(
            "document_revision", "source",
        ).filter(
            pk=occurrence_uuid,
            document_revision__document__chapter__project=project,
            document_revision__document__chapter__number=chapter_no,
        ).first()
        if document is None or document.current_revision is None or occurrence is None:
            raise DomainError("NOT_FOUND", "Documento u ocurrencia de cita no encontrados")
        if occurrence.document_revision_id != document.current_revision_id:
            raise DomainError("VERSION_CONFLICT", "La cita pertenece a una revisión anterior; actualiza el documento")
        replacement = SourceDocument.objects.filter(project=project, pk=source_uuid).first()
        if replacement is None:
            raise DomainError("NOT_FOUND", "Fuente de reemplazo no encontrada en este proyecto")
        if replacement.id == occurrence.source_id:
            raise DomainError("VALIDATION_ERROR", "La fuente de reemplazo debe ser diferente")
        prior = CitationReplacementProposal.objects.filter(occurrence=occurrence, idempotency_key=key).first()
        if prior:
            if prior.replacement_source_id != replacement.id or prior.rationale != rationale:
                raise DomainError("IDEMPOTENCY_CONFLICT", "idempotency_key ya se usó con otra propuesta")
            return _present(prior, prior.decisions.first(), idempotent=True)

        previous_reference = occurrence.reference_snapshot
        replacement_reference = frozen_reference(replacement)
        proposal = CitationReplacementProposal.objects.create(
            occurrence=occurrence, document_revision=document.current_revision,
            expected_document_version=document.lock_version, replacement_source=replacement,
            previous_reference_snapshot=previous_reference,
            replacement_reference_snapshot=replacement_reference,
            previous_reference_sha256=occurrence.reference_sha256,
            replacement_reference_sha256=_hash(replacement_reference),
            rationale=rationale, idempotency_key=key, created_by=actor,
        )
    return _present(proposal)


def decide_citation_replacement(actor, project_id, chapter_no: int, proposal_id, action: str,
                                expected_document_version: int, idempotency_key, reason: str = "") -> dict:
    project = require_project(actor, project_id, owner_only=True)
    try:
        proposal_uuid, key = UUID(str(proposal_id)), UUID(str(idempotency_key))
    except (ValueError, TypeError, AttributeError) as exc:
        raise DomainError("VALIDATION_ERROR", "proposal_id e idempotency_key deben ser UUID") from exc
    if action not in (CitationReplacementDecision.Status.ACCEPTED, CitationReplacementDecision.Status.REJECTED):
        raise DomainError("VALIDATION_ERROR", "La decisión debe ser ACCEPTED o REJECTED")

    with transaction.atomic():
        proposal = CitationReplacementProposal.objects.select_for_update().select_related(
            "occurrence", "document_revision", "replacement_source",
        ).filter(
            pk=proposal_uuid,
            occurrence__document_revision__document__chapter__project=project,
            occurrence__document_revision__document__chapter__number=chapter_no,
        ).first()
        if proposal is None:
            raise DomainError("NOT_FOUND", "Propuesta de sustitución no encontrada")
        prior_decision = proposal.decisions.select_related("resulting_document_revision").first()
        if prior_decision:
            if (prior_decision.idempotency_key == key and prior_decision.status == action
                    and prior_decision.reason == reason.strip()[:2000]):
                return _present(proposal, prior_decision, idempotent=True)
            raise DomainError("VERSION_CONFLICT", "La propuesta ya tiene una decisión registrada")

        document = ChapterDocument.objects.select_for_update().get(
            chapter=proposal.occurrence.document_revision.document.chapter,
        )
        if (document.current_revision_id != proposal.document_revision_id
                or document.lock_version != proposal.expected_document_version
                or expected_document_version != proposal.expected_document_version):
            raise DomainError("VERSION_CONFLICT", "El documento cambió; vuelve a comparar la propuesta")
        if action == CitationReplacementDecision.Status.REJECTED:
            decision = CitationReplacementDecision.objects.create(
                proposal=proposal, status=action, expected_document_version=expected_document_version,
                resulting_document_revision=None, reason=reason.strip()[:2000], idempotency_key=key,
                decided_by=actor,
            )
            return _present(proposal, decision)

        if _hash(frozen_reference(proposal.replacement_source)) != proposal.replacement_reference_sha256:
            raise DomainError("VERSION_CONFLICT", "Los metadatos de reemplazo cambiaron; genera una propuesta nueva")
        marks = list_citation_marks(document.current_revision)
        target_seen = False
        citation_input = []
        for mark in marks:
            source_items = []
            for source_item in mark["sources"]:
                source_id = source_item["source_id"]
                if mark["group_id"] == str(proposal.occurrence.group_id) and source_id == str(proposal.occurrence.source_id):
                    source_id = str(proposal.replacement_source_id)
                    target_seen = True
                source_items.append({"source_id": source_id, "locator": source_item["locator"]})
            if len({item["source_id"] for item in source_items}) != len(source_items):
                raise DomainError("VALIDATION_ERROR", "La fuente de reemplazo ya aparece en este grupo de cita")
            citation_input.append({
                "group_id": mark["group_id"], "block_id": mark["block_id"],
                "position": mark["position"], "sources": source_items,
            })
        if not target_seen:
            raise DomainError("VERSION_CONFLICT", "La cita propuesta no figura en la revisión vigente")
        replacement_revision = save_chapter_document(
            actor, project.id, chapter_no, document.current_revision.content_tree,
            document.lock_version, str(uuid5(proposal.id, "accept-citation-replacement")),
            citations=citation_input,
        )
        from thesis.models import ChapterDocumentRevision

        resulting_revision = ChapterDocumentRevision.objects.get(pk=replacement_revision["revision_id"])
        decision = CitationReplacementDecision.objects.create(
            proposal=proposal, status=action, expected_document_version=expected_document_version,
            resulting_document_revision=resulting_revision, reason=reason.strip()[:2000],
            idempotency_key=key, decided_by=actor,
        )
    return _present(proposal, decision)


def preview_citation_replacement(actor, project_id, chapter_no: int, proposal_id) -> dict:
    project = require_project(actor, project_id)
    try:
        proposal_uuid = UUID(str(proposal_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise DomainError("VALIDATION_ERROR", "proposal_id debe ser UUID") from exc
    proposal = CitationReplacementProposal.objects.select_related("document_revision").filter(
        pk=proposal_uuid,
        occurrence__document_revision__document__chapter__project=project,
        occurrence__document_revision__document__chapter__number=chapter_no,
    ).first()
    if proposal is None:
        raise DomainError("NOT_FOUND", "Propuesta de sustitución no encontrada")
    return _present(proposal, proposal.decisions.first()) | {
        "preview": {
            "from": proposal.previous_reference_snapshot,
            "to": proposal.replacement_reference_snapshot,
            "current_ieee_view": build_ieee_citation_view(proposal.document_revision),
            "requires_explicit_acceptance": True,
        },
    }
