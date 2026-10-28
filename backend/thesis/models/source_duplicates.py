"""Historial auditable de decisiones humanas sobre posibles duplicados."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from .projects import Project
from .sources import SourceDocument


class SourceDuplicateDecision(models.Model):
    class Decision(models.TextChoices):
        MARK_DUPLICATE = "MARK_DUPLICATE", "Confirmar que son duplicados"
        KEEP_SEPARATE = "KEEP_SEPARATE", "Mantener como registros distintos"
        SET_PRIMARY = "SET_PRIMARY", "Elegir un registro preferido"

    class MatchBasis(models.TextChoices):
        DOI_AND_TITLE = "DOI_AND_TITLE", "Coinciden DOI y título"
        DOI = "DOI", "Coincide DOI"
        TITLE = "TITLE", "Coincide título normalizado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="source_duplicate_decisions")
    source_a = models.ForeignKey(SourceDocument, on_delete=models.PROTECT, related_name="duplicate_decisions_as_a")
    source_b = models.ForeignKey(SourceDocument, on_delete=models.PROTECT, related_name="duplicate_decisions_as_b")
    decision_no = models.PositiveIntegerField()
    match_basis = models.CharField(max_length=14, choices=MatchBasis.choices)
    decision = models.CharField(max_length=24, choices=Decision.choices)
    primary_source = models.ForeignKey(SourceDocument, on_delete=models.PROTECT, null=True, blank=True,
                                       related_name="duplicate_decisions_as_primary")
    note = models.CharField(max_length=2000, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name="source_duplicate_decisions")
    idempotency_key = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "source_duplicate_decision"
        constraints = [
            models.UniqueConstraint(fields=["project", "source_a", "source_b", "decision_no"],
                                    name="src_dup_project_pair_version_uq"),
            models.UniqueConstraint(fields=["project", "idempotency_key"],
                                    name="src_dup_project_idempotency_uq"),
            models.CheckConstraint(condition=Q(source_a__lt=F("source_b")),
                                   name="src_dup_pair_ordered_ck"),
            models.CheckConstraint(condition=Q(decision_no__gt=0), name="src_dup_version_positive_ck"),
            models.CheckConstraint(condition=Q(match_basis__in=["DOI_AND_TITLE", "DOI", "TITLE"]),
                                   name="src_dup_match_basis_known_ck"),
            models.CheckConstraint(condition=Q(decision__in=["MARK_DUPLICATE", "KEEP_SEPARATE", "SET_PRIMARY"]),
                                   name="src_dup_decision_known_ck"),
            models.CheckConstraint(
                condition=(Q(decision="SET_PRIMARY", primary_source=F("source_a"))
                           | Q(decision="SET_PRIMARY", primary_source=F("source_b"))
                           | Q(decision__in=["MARK_DUPLICATE", "KEEP_SEPARATE"], primary_source__isnull=True)),
                name="src_dup_primary_action_ck",
            ),
        ]
        indexes = [models.Index(fields=["project", "source_a", "source_b", "-decision_no"],
                                name="src_dup_project_pair_idx")]
