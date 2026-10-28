"""Instrumentos, reactivos y trazabilidad a indicadores."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from .projects import Project
from .research import Indicator, VariableDimension


class Instrument(models.Model):
    class Kind(models.TextChoices):
        QUESTIONNAIRE = "QUESTIONNAIRE", "Cuestionario"
        INTERVIEW = "INTERVIEW", "Guía de Entrevista"
        FOCUS_GROUP = "FOCUS_GROUP", "Grupo Focal"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        APPROVED = "APPROVED", "Aprobado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="instruments")
    lineage_key = models.UUIDField(default=uuid.uuid4)
    version_no = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    target_population = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_instruments",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "instrument"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "lineage_key", "version_no"],
                name="instrument_proj_lineage_ver_uk",
            ),
            models.CheckConstraint(condition=Q(version_no__gt=0), name="instrument_version_positive"),
            models.CheckConstraint(
                condition=Q(kind__in=["QUESTIONNAIRE", "INTERVIEW", "FOCUS_GROUP"]),
                name="instrument_valid_kind",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="DRAFT", approved_by__isnull=True, approved_at__isnull=True)
                    | Q(status="APPROVED", approved_by__isnull=False, approved_at__isnull=False)
                ),
                name="instrument_approval_fields",
            ),
        ]


class InstrumentItem(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT, related_name="items")
    dimension = models.ForeignKey(
        VariableDimension,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="instrument_items",
    )
    ordinal = models.PositiveSmallIntegerField()
    prompt_text = models.TextField()
    response_scale = models.CharField(max_length=120, null=True, blank=True)
    probe_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "instrument_item"
        ordering = ["ordinal"]
        constraints = [
            models.UniqueConstraint(fields=["instrument", "ordinal"], name="instrument_item_inst_ord_uk"),
            models.CheckConstraint(
                condition=Q(ordinal__gte=1) & ~Q(prompt_text=""),
                name="instrument_item_valid",
            ),
        ]


class InstrumentItemIndicator(models.Model):
    instrument_item = models.ForeignKey(InstrumentItem, on_delete=models.PROTECT, related_name="item_indicators")
    indicator = models.ForeignKey(Indicator, on_delete=models.PROTECT, related_name="item_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "instrument_item_indicator"
        constraints = [
            models.UniqueConstraint(
                fields=["instrument_item", "indicator"],
                name="inst_item_indicator_unique",
            ),
        ]
