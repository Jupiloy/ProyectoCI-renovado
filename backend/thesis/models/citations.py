"""Ocurrencias de citas fijadas a una revisión canónica de capítulo."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from .chapters import ChapterDocumentRevision
from .sources import SourceDocument
from .sources import SourceExcerpt


class ChapterCitationOccurrence(models.Model):
    """Un registro bibliográfico citado en una posición de un bloque de una revisión."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_revision = models.ForeignKey(
        ChapterDocumentRevision, on_delete=models.PROTECT, related_name="citation_occurrences",
    )
    group_id = models.UUIDField()
    group_order = models.PositiveSmallIntegerField()
    block_id = models.UUIDField()
    char_offset = models.PositiveIntegerField()
    source = models.ForeignKey(SourceDocument, on_delete=models.PROTECT, related_name="citation_occurrences")
    source_order = models.PositiveSmallIntegerField()
    locator = models.CharField(max_length=200, blank=True, default="")
    reference_snapshot = models.JSONField(default=dict)
    reference_sha256 = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name="chapter_citation_occurrences")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chapter_citation_occurrence"
        constraints = [
            models.UniqueConstraint(fields=["document_revision", "group_id", "source_order"],
                                    name="chapter_cit_group_order_uq"),
            models.UniqueConstraint(fields=["document_revision", "group_order", "source_order"],
                                    name="chapter_cit_revision_order_uq"),
            models.UniqueConstraint(fields=["document_revision", "group_id", "source"],
                                    name="chapter_cit_group_source_uq"),
            models.CheckConstraint(condition=Q(source_order__gt=0), name="chapter_cit_source_order_ck"),
            models.CheckConstraint(condition=Q(group_order__gt=0), name="chapter_cit_group_order_ck"),
        ]
        indexes = [
            models.Index(fields=["document_revision", "block_id", "char_offset"],
                         name="chapter_cit_revision_pos_idx"),
        ]


class CitationEvidenceReview(models.Model):
    """Historial append-only de un pasaje ligado a una cita y su revisión humana."""

    class Status(models.TextChoices):
        CANDIDATE = "CANDIDATE", "Pasaje candidato; falta revisar"
        SUPPORTS = "SUPPORTS", "Asesor considera que respalda la afirmación"
        CONTRADICTS = "CONTRADICTS", "Asesor considera que contradice la afirmación"
        UNRELATED = "UNRELATED", "Asesor considera que no trata la afirmación"
        INSUFFICIENT = "INSUFFICIENT", "Evidencia insuficiente"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    occurrence = models.ForeignKey(
        ChapterCitationOccurrence, on_delete=models.PROTECT, related_name="evidence_reviews",
    )
    excerpt = models.ForeignKey(SourceExcerpt, on_delete=models.PROTECT, related_name="citation_reviews")
    claim_text = models.TextField()
    claim_start = models.PositiveIntegerField()
    claim_end = models.PositiveIntegerField()
    claim_sha256 = models.CharField(max_length=64)
    excerpt_start = models.PositiveIntegerField()
    excerpt_end = models.PositiveIntegerField()
    matched_text = models.TextField()
    excerpt_sha256 = models.CharField(max_length=64)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CANDIDATE)
    review_version = models.PositiveIntegerField()
    previous_review = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="superseding_reviews",
    )
    idempotency_key = models.UUIDField()
    review_note = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="citation_evidence_reviews",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "citation_evidence_review"
        constraints = [
            models.UniqueConstraint(fields=["occurrence", "review_version"], name="cit_evidence_version_uq"),
            models.UniqueConstraint(fields=["occurrence", "idempotency_key"], name="cit_evidence_idempotency_uq"),
            models.CheckConstraint(condition=Q(review_version__gt=0), name="cit_evidence_version_ck"),
            models.CheckConstraint(condition=Q(claim_end__gt=models.F("claim_start")), name="cit_evidence_claim_range_ck"),
            models.CheckConstraint(condition=Q(excerpt_end__gt=models.F("excerpt_start")), name="cit_evidence_excerpt_range_ck"),
        ]
        indexes = [models.Index(fields=["occurrence", "-review_version"], name="cit_evidence_history_idx")]


class CitationReplacementProposal(models.Model):
    """Propuesta inmutable para sustituir una fuente citada sin alterar la revisión vigente."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    occurrence = models.ForeignKey(
        ChapterCitationOccurrence, on_delete=models.PROTECT, related_name="replacement_proposals",
    )
    document_revision = models.ForeignKey(
        ChapterDocumentRevision, on_delete=models.PROTECT, related_name="citation_replacement_proposals",
    )
    expected_document_version = models.PositiveIntegerField()
    replacement_source = models.ForeignKey(
        SourceDocument, on_delete=models.PROTECT, related_name="citation_replacement_proposals",
    )
    previous_reference_snapshot = models.JSONField(default=dict)
    replacement_reference_snapshot = models.JSONField(default=dict)
    previous_reference_sha256 = models.CharField(max_length=64)
    replacement_reference_sha256 = models.CharField(max_length=64)
    rationale = models.TextField()
    idempotency_key = models.UUIDField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="citation_replacement_proposals",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "citation_replacement_proposal"
        constraints = [
            models.UniqueConstraint(fields=["occurrence", "idempotency_key"], name="cit_replace_idempotency_uq"),
            models.CheckConstraint(condition=Q(expected_document_version__gte=0), name="cit_replace_doc_version_ck"),
        ]
        indexes = [models.Index(fields=["document_revision", "created_at"], name="cit_replace_revision_idx")]


class CitationReplacementDecision(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Aceptada"
        REJECTED = "REJECTED", "Rechazada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proposal = models.ForeignKey(
        CitationReplacementProposal, on_delete=models.PROTECT, related_name="decisions",
    )
    status = models.CharField(max_length=8, choices=Status.choices)
    expected_document_version = models.PositiveIntegerField()
    resulting_document_revision = models.ForeignKey(
        ChapterDocumentRevision, on_delete=models.PROTECT, null=True, blank=True,
        related_name="citation_replacement_decisions",
    )
    reason = models.TextField(blank=True, default="")
    idempotency_key = models.UUIDField()
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="citation_replacement_decisions",
    )
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "citation_replacement_decision"
        constraints = [
            models.UniqueConstraint(fields=["proposal"], name="cit_replace_one_decision_uq"),
            models.UniqueConstraint(fields=["proposal", "idempotency_key"], name="cit_replace_decision_key_uq"),
            models.CheckConstraint(
                condition=(Q(status="ACCEPTED", resulting_document_revision__isnull=False)
                           | Q(status="REJECTED", resulting_document_revision__isnull=True)),
                name="cit_replace_decision_revision_ck",
            ),
        ]
