"""Datos de investigación originales y versiones inmutables."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from .projects import Project


class ResearchDataset(models.Model):
    """Contenedor mutable de identidad; los archivos y metadatos viven en versiones."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="research_datasets")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name="created_research_datasets")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "research_dataset"
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "name"], name="research_dataset_project_name_uq"),
            models.CheckConstraint(condition=~Q(name=""), name="research_dataset_name_nonempty_ck"),
        ]


class ResearchDatasetVersion(models.Model):
    """Archivo original inmutable con hash y descripción estructural de importación."""

    class Format(models.TextChoices):
        CSV = "CSV", "CSV"
        XLSX = "XLSX", "Excel XLSX"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset = models.ForeignKey(ResearchDataset, on_delete=models.PROTECT, related_name="versions")
    version_no = models.PositiveIntegerField()
    idempotency_key = models.UUIDField()
    original_filename = models.CharField(max_length=255)
    file_format = models.CharField(max_length=8, choices=Format.choices)
    storage_key = models.CharField(max_length=500)
    sha256 = models.CharField(max_length=64)
    size_bytes = models.PositiveBigIntegerField()
    row_count = models.PositiveIntegerField()
    column_count = models.PositiveSmallIntegerField()
    columns_json = models.JSONField(default=list)
    import_metadata_json = models.JSONField(default=dict)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name="uploaded_research_dataset_versions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "research_dataset_version"
        ordering = ["dataset_id", "version_no"]
        constraints = [
            models.UniqueConstraint(fields=["dataset", "version_no"], name="research_dataset_version_no_uq"),
            models.UniqueConstraint(fields=["dataset", "idempotency_key"], name="research_dataset_version_key_uq"),
            models.CheckConstraint(condition=Q(version_no__gt=0), name="research_dataset_version_positive_ck"),
            models.CheckConstraint(condition=Q(row_count__gt=0), name="research_dataset_rows_positive_ck"),
            models.CheckConstraint(condition=Q(column_count__gt=0), name="research_dataset_cols_positive_ck"),
            models.CheckConstraint(condition=Q(size_bytes__gt=0), name="research_dataset_bytes_positive_ck"),
            models.CheckConstraint(condition=Q(sha256__regex=r"^[0-9a-f]{64}$"), name="research_dataset_sha256_ck"),
        ]
        indexes = [models.Index(fields=["dataset", "-version_no"], name="research_dataset_version_idx")]


class ResearchTableRecipe(models.Model):
    """Identidad de una receta declarativa dentro de una versión de dataset."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset_version = models.ForeignKey(
        ResearchDatasetVersion, on_delete=models.PROTECT, related_name="table_recipes",
    )
    name = models.CharField(max_length=160)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_table_recipes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "research_table_recipe"
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["dataset_version", "name"], name="research_table_recipe_input_name_uq",
            ),
            models.CheckConstraint(condition=~Q(name=""), name="research_table_recipe_name_nonempty_ck"),
        ]


class ResearchTableRecipeVersion(models.Model):
    """Snapshot append-only de especificación y tabla resultante."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipe = models.ForeignKey(ResearchTableRecipe, on_delete=models.PROTECT, related_name="versions")
    version_no = models.PositiveIntegerField()
    idempotency_key = models.UUIDField()
    expected_input_sha256 = models.CharField(max_length=64)
    spec_json = models.JSONField(default=dict)
    spec_sha256 = models.CharField(max_length=64)
    result_json = models.JSONField(default=dict)
    result_sha256 = models.CharField(max_length=64)
    engine_version = models.CharField(max_length=32)
    row_count = models.PositiveIntegerField()
    column_count = models.PositiveSmallIntegerField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_table_recipe_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "research_table_recipe_version"
        ordering = ["recipe_id", "version_no"]
        constraints = [
            models.UniqueConstraint(fields=["recipe", "version_no"], name="research_table_recipe_version_no_uq"),
            models.UniqueConstraint(fields=["recipe", "idempotency_key"], name="research_table_recipe_version_key_uq"),
            models.CheckConstraint(condition=Q(version_no__gt=0), name="research_table_recipe_version_positive_ck"),
            models.CheckConstraint(condition=Q(row_count__gt=0), name="research_table_recipe_rows_positive_ck"),
            models.CheckConstraint(condition=Q(column_count__gt=0), name="research_table_recipe_cols_positive_ck"),
            models.CheckConstraint(condition=Q(expected_input_sha256__regex=r"^[0-9a-f]{64}$"),
                                   name="research_table_input_sha256_ck"),
            models.CheckConstraint(condition=Q(spec_sha256__regex=r"^[0-9a-f]{64}$"),
                                   name="research_table_spec_sha256_ck"),
            models.CheckConstraint(condition=Q(result_sha256__regex=r"^[0-9a-f]{64}$"),
                                   name="research_table_result_sha256_ck"),
        ]
        indexes = [models.Index(fields=["recipe", "-version_no"], name="research_table_recipe_ver_idx")]


class ResearchFigure(models.Model):
    """Identidad de figura derivada de una versión de tabla reproducible."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    table_version = models.ForeignKey(
        ResearchTableRecipeVersion, on_delete=models.PROTECT, related_name="figures",
    )
    name = models.CharField(max_length=160)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_research_figures",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "research_figure"
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["table_version", "name"], name="research_figure_input_name_uq"),
            models.CheckConstraint(condition=~Q(name=""), name="research_figure_name_nonempty_ck"),
        ]


class ResearchFigureVersion(models.Model):
    """PNG generado y metadatos inmutables de accesibilidad/procedencia."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    figure = models.ForeignKey(ResearchFigure, on_delete=models.PROTECT, related_name="versions")
    version_no = models.PositiveIntegerField()
    idempotency_key = models.UUIDField()
    source_result_sha256 = models.CharField(max_length=64)
    spec_json = models.JSONField(default=dict)
    spec_sha256 = models.CharField(max_length=64)
    storage_key = models.CharField(max_length=500)
    output_sha256 = models.CharField(max_length=64)
    size_bytes = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=32, default="image/png")
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    renderer_version = models.CharField(max_length=64)
    accessibility_json = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_research_figure_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "research_figure_version"
        ordering = ["figure_id", "version_no"]
        constraints = [
            models.UniqueConstraint(fields=["figure", "version_no"], name="research_figure_version_no_uq"),
            models.UniqueConstraint(fields=["figure", "idempotency_key"], name="research_figure_version_key_uq"),
            models.CheckConstraint(condition=Q(version_no__gt=0), name="research_figure_version_positive_ck"),
            models.CheckConstraint(condition=Q(size_bytes__gt=0), name="research_figure_bytes_positive_ck"),
            models.CheckConstraint(condition=Q(width__gt=0, height__gt=0), name="research_figure_dimensions_positive_ck"),
            models.CheckConstraint(condition=Q(source_result_sha256__regex=r"^[0-9a-f]{64}$"),
                                   name="research_figure_source_sha256_ck"),
            models.CheckConstraint(condition=Q(spec_sha256__regex=r"^[0-9a-f]{64}$"),
                                   name="research_figure_spec_sha256_ck"),
            models.CheckConstraint(condition=Q(output_sha256__regex=r"^[0-9a-f]{64}$"),
                                   name="research_figure_output_sha256_ck"),
            models.CheckConstraint(condition=Q(mime_type="image/png"), name="research_figure_png_mime_ck"),
        ]
        indexes = [models.Index(fields=["figure", "-version_no"], name="research_figure_ver_idx")]
