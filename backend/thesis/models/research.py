"""Perfil y entidades metodológicas de la investigación."""

from django.db import models
from django.db.models import Q

from .projects import Project


class ResearchProfile(models.Model):
    class Approach(models.TextChoices):
        QUANTITATIVE = "QUANTITATIVE", "Cuantitativo"
        QUALITATIVE = "QUALITATIVE", "Cualitativo"
        MIXED = "MIXED", "Mixto"

    class WorkflowMode(models.TextChoices):
        LEGACY_SEQUENTIAL = "LEGACY_SEQUENTIAL", "Secuencial heredado P01-P32"
        CONFIGURABLE_GRAPH = "CONFIGURABLE_GRAPH", "Grafo configurable por proyecto"

    project = models.OneToOneField(Project, on_delete=models.PROTECT, primary_key=True, related_name="profile")
    approach = models.CharField(max_length=16, choices=Approach.choices, null=True, blank=True)
    topic = models.TextField(null=True, blank=True, help_text="Idea provisional descrita por el tesista")
    ods_code = models.CharField(max_length=20, null=True, blank=True)
    unit_of_analysis = models.TextField(null=True, blank=True)
    place = models.TextField(null=True, blank=True)
    period_text = models.CharField(max_length=120, null=True, blank=True)
    problem_statement = models.TextField(null=True, blank=True)
    schema_version = models.PositiveSmallIntegerField(default=1)
    lock_version = models.PositiveIntegerField(default=0)
    workflow_mode = models.CharField(
        max_length=30,
        choices=WorkflowMode.choices,
        default=WorkflowMode.LEGACY_SEQUENTIAL,
        verbose_name="Modo de ejecución del recorrido",
    )
    active_workflow = models.ForeignKey(
        "thesis.ProjectWorkflow",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_profiles",
        verbose_name="Recorrido activo publicado",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "research_profile"
        constraints = [
            models.CheckConstraint(condition=Q(schema_version__gte=1), name="research_profile_schema_version_positive"),
            models.CheckConstraint(
                condition=Q(approach__isnull=True) | Q(approach__in=["QUANTITATIVE", "QUALITATIVE", "MIXED"]),
                name="research_profile_valid_approach",
            ),
        ]


class ConsistencyRow(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="consistency_rows")
    ordinal = models.PositiveSmallIntegerField(help_text="0 para general, 1..n para específicas")
    question_text = models.TextField(null=True, blank=True)
    objective_text = models.TextField(null=True, blank=True)
    hypothesis_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "consistency_row"
        ordering = ["ordinal"]
        constraints = [
            models.UniqueConstraint(fields=["project", "ordinal"], name="consistency_row_project_ordinal_unique"),
        ]


class ResearchVariable(models.Model):
    class Role(models.TextChoices):
        INDEPENDENT = "INDEPENDENT", "Variable Independiente"
        DEPENDENT = "DEPENDENT", "Variable Dependiente"
        OTHER = "OTHER", "Otra / Constructo"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="variables")
    role = models.CharField(max_length=16, choices=Role.choices)
    name = models.CharField(max_length=200)
    conceptual_definition = models.TextField(null=True, blank=True)
    operational_definition = models.TextField(null=True, blank=True)
    ordinal = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "research_variable"
        ordering = ["ordinal"]
        constraints = [
            models.UniqueConstraint(fields=["project", "ordinal"], name="research_variable_project_ordinal_unique"),
            models.CheckConstraint(condition=Q(ordinal__gte=1), name="research_variable_ordinal_positive"),
            models.CheckConstraint(
                condition=Q(role__in=["INDEPENDENT", "DEPENDENT", "OTHER"]),
                name="research_variable_valid_role",
            ),
        ]
        indexes = [models.Index(fields=["project", "role"], name="research_var_project_role_idx")]


class ConsistencyRowVariable(models.Model):
    consistency_row = models.ForeignKey(ConsistencyRow, on_delete=models.PROTECT, related_name="row_variables")
    variable = models.ForeignKey(ResearchVariable, on_delete=models.PROTECT, related_name="row_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "consistency_row_variable"
        constraints = [
            models.UniqueConstraint(
                fields=["consistency_row", "variable"],
                name="consistency_row_variable_unique",
            ),
        ]


class VariableDimension(models.Model):
    variable = models.ForeignKey(ResearchVariable, on_delete=models.PROTECT, related_name="dimensions")
    ordinal = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=200)
    definition = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "variable_dimension"
        ordering = ["ordinal"]
        constraints = [
            models.UniqueConstraint(fields=["variable", "ordinal"], name="variable_dimension_var_ordinal_unique"),
            models.CheckConstraint(condition=Q(ordinal__gte=1), name="variable_dimension_ordinal_positive"),
        ]


class Indicator(models.Model):
    dimension = models.ForeignKey(VariableDimension, on_delete=models.PROTECT, related_name="indicators")
    ordinal = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=200)
    measurement_scale = models.CharField(max_length=30, null=True, blank=True)
    technique = models.CharField(max_length=120, null=True, blank=True)
    operational_rule = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "indicator"
        ordering = ["ordinal"]
        constraints = [
            models.UniqueConstraint(fields=["dimension", "ordinal"], name="indicator_dim_ordinal_unique"),
            models.CheckConstraint(condition=Q(ordinal__gte=1), name="indicator_ordinal_positive"),
        ]
