"""Estrategias versionadas y registro de búsquedas bibliográficas manuales."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from .projects import Project
from .sources import SourceDocument


class SearchStrategy(models.Model):
    class Provider(models.TextChoices):
        OPEN_WEB = "OPEN_WEB", "Web abierta"
        OPENALEX = "OPENALEX", "OpenAlex"
        SEMANTIC_SCHOLAR = "SEMANTIC_SCHOLAR", "Semantic Scholar"
        ALICIA = "ALICIA", "ALICIA / CONCYTEC"
        SCOPUS = "SCOPUS", "Scopus"
        WEB_OF_SCIENCE = "WEB_OF_SCIENCE", "Web of Science"
        OTHER = "OTHER", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="search_strategies")
    series_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    version_no = models.PositiveIntegerField()
    supersedes = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True,
                                   related_name="superseded_by")
    provider = models.CharField(max_length=24, choices=Provider.choices)
    title = models.CharField(max_length=160)
    topic = models.TextField()
    query_text = models.TextField()
    search_equation = models.TextField(blank=True)
    concepts_json = models.JSONField(default=list)
    filters_json = models.JSONField(default=dict)
    search_url = models.URLField(max_length=2048, blank=True)
    content_sha256 = models.CharField(max_length=64)
    idempotency_key = models.UUIDField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name="created_search_strategies")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "search_strategy"
        constraints = [
            models.UniqueConstraint(fields=["project", "series_id", "version_no"], name="search_strat_series_ver_uq"),
            models.UniqueConstraint(fields=["project", "idempotency_key"], name="search_strat_idempotency_uq"),
            models.CheckConstraint(condition=Q(version_no__gt=0), name="search_strat_version_positive"),
            models.CheckConstraint(condition=Q(version_no=1, supersedes__isnull=True) | Q(version_no__gt=1, supersedes__isnull=False),
                                   name="search_strat_chain_valid"),
        ]
        indexes = [models.Index(fields=["project", "series_id", "-version_no"], name="search_strat_project_ord_idx")]


class SearchExecution(models.Model):
    """Declaración del usuario de que ejecutó manualmente una estrategia concreta."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    strategy = models.ForeignKey(SearchStrategy, on_delete=models.PROTECT, related_name="manual_executions")
    executed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                    related_name="recorded_search_executions")
    execution_date = models.DateField()
    reported_result_count = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    idempotency_key = models.UUIDField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "search_execution"
        constraints = [
            models.UniqueConstraint(fields=["strategy", "idempotency_key"], name="search_exec_idempotency_uq"),
            models.CheckConstraint(condition=Q(reported_result_count__isnull=True) | Q(reported_result_count__lte=1000000),
                                   name="search_exec_count_bound"),
        ]
        indexes = [models.Index(fields=["strategy", "-execution_date"], name="search_exec_strat_date_idx")]


class SearchExecutionSource(models.Model):
    """Relación inmutable entre una ejecución y fuentes seleccionadas/importadas."""

    class LinkKind(models.TextChoices):
        DISCOVERY_SELECTION = "DISCOVERY_SELECTION", "Resultado de descubrimiento seleccionado"
        BIBLIOGRAPHY_IMPORT = "BIBLIOGRAPHY_IMPORT", "Registro de archivo bibliográfico importado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(SearchExecution, on_delete=models.PROTECT, related_name="source_links")
    source = models.ForeignKey(SourceDocument, on_delete=models.PROTECT, related_name="search_execution_links")
    link_kind = models.CharField(max_length=24, choices=LinkKind.choices)
    imported_file_sha256 = models.CharField(max_length=64, blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name="created_search_execution_source_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "search_execution_source"
        constraints = [
            models.UniqueConstraint(fields=["execution", "source", "link_kind", "imported_file_sha256"],
                                    name="search_exec_source_link_uq"),
            models.CheckConstraint(
                condition=Q(link_kind="BIBLIOGRAPHY_IMPORT", imported_file_sha256__regex=r"^[0-9a-f]{64}$")
                | Q(link_kind="DISCOVERY_SELECTION", imported_file_sha256=""),
                name="search_exec_source_provenance_valid",
            ),
        ]
        indexes = [models.Index(fields=["execution", "link_kind"], name="search_exec_source_kind_idx")]
