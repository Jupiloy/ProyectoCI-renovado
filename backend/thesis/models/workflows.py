from django.conf import settings
from django.db import models


class ProjectWorkflow(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador en edición"
        PUBLISHED = "PUBLISHED", "Publicado y activo"
        RETIRED = "RETIRED", "Versión histórica retirada"

    project = models.ForeignKey(
        "thesis.Project",
        on_delete=models.CASCADE,
        related_name="workflows",
        verbose_name="Proyecto",
    )
    version_no = models.PositiveIntegerField(
        default=1,
        verbose_name="Número de versión del recorrido",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Estado de la versión",
    )
    base_template_version = models.CharField(
        max_length=50,
        default="catalogo_p01_p32_v1",
        verbose_name="Versión de plantilla base",
    )
    change_summary = models.TextField(
        blank=True,
        default="",
        verbose_name="Resumen o justificación del cambio",
    )
    content_sha256 = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Hash SHA-256 de integridad del grafo",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_workflows",
        verbose_name="Creado por",
    )
    parent_workflow = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="derived_workflows",
        verbose_name="Versión padre de origen",
    )
    lock_version = models.PositiveIntegerField(
        default=0,
        verbose_name="Versión de bloqueo concurrente (optimista)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de última actualización",
    )

    class Meta:
        db_table = "thesis_project_workflow"
        verbose_name = "Recorrido de proyecto"
        verbose_name_plural = "Recorridos de proyecto"
        ordering = ["project", "version_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "version_no"],
                name="unique_project_workflow_version",
            ),
        ]

    def __str__(self):
        return f"Workflow {self.project_id} v{self.version_no} ({self.status})"


class WorkflowTask(models.Model):
    workflow = models.ForeignKey(
        ProjectWorkflow,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Recorrido asociado",
    )
    task_id = models.CharField(
        max_length=50,
        verbose_name="Identificador único de la tarea",
    )
    legacy_step_code = models.CharField(
        max_length=10,
        blank=True,
        default="",
        verbose_name="Código de paso legado (ej. P01)",
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Título visible de la tarea",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Descripción u objetivo de la tarea",
    )
    chapter_no = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Capítulo académico asignado",
    )
    order_index = models.PositiveIntegerField(
        default=1,
        verbose_name="Índice de orden visible",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="¿Tarea activa?",
    )
    is_optional = models.BooleanField(
        default=False,
        verbose_name="¿Tarea opcional?",
    )
    is_protected = models.BooleanField(
        default=False,
        verbose_name="¿Control núcleo protegido? (Inalterable)",
    )
    contract_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Nombre de contrato Pydantic asociado",
    )
    output_schema = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Esquema JSON de salida esperado (JSON Schema seguro)",
    )
    branch_condition = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Condición de rama o enfoque",
    )

    class Meta:
        db_table = "thesis_workflow_task"
        verbose_name = "Tarea de recorrido"
        verbose_name_plural = "Tareas de recorrido"
        ordering = ["workflow", "order_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "task_id"],
                name="unique_workflow_task_id",
            ),
        ]

    def __str__(self):
        return f"{self.task_id}: {self.title} (Workflow v{self.workflow.version_no})"


class WorkflowDependency(models.Model):
    class Type(models.TextChoices):
        DATA_REQUIRED = "DATA_REQUIRED", "Dato de salida requerido de la tarea previa"
        HUMAN_REVIEW = "HUMAN_REVIEW", "Revisión humana requerida"
        POLICY_GATE = "POLICY_GATE", "Compuerta normativa institucional"

    workflow = models.ForeignKey(
        ProjectWorkflow,
        on_delete=models.CASCADE,
        related_name="dependencies",
        verbose_name="Recorrido asociado",
    )
    source_task = models.ForeignKey(
        WorkflowTask,
        on_delete=models.CASCADE,
        related_name="prerequisite_dependencies",
        verbose_name="Tarea dependiente (origen de la necesidad)",
    )
    target_task = models.ForeignKey(
        WorkflowTask,
        on_delete=models.CASCADE,
        related_name="dependent_tasks",
        verbose_name="Tarea prerrequisito (destino necesario)",
    )
    dependency_type = models.CharField(
        max_length=30,
        choices=Type.choices,
        default=Type.DATA_REQUIRED,
        verbose_name="Tipo de dependencia",
    )
    required_field = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Campo específico requerido en output_json",
    )
    is_blocking = models.BooleanField(
        default=True,
        verbose_name="¿Bloquea ejecución de la tarea dependiente?",
    )
    reason = models.TextField(
        blank=True,
        default="",
        verbose_name="Justificación metodológica de la dependencia",
    )

    class Meta:
        db_table = "thesis_workflow_dependency"
        verbose_name = "Dependencia de recorrido"
        verbose_name_plural = "Dependencias de recorrido"
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "source_task", "target_task"],
                name="unique_workflow_dependency",
            ),
        ]

    def __str__(self):
        return f"{self.source_task.task_id} requiere {self.target_task.task_id} ({self.dependency_type})"


class WorkflowPrompt(models.Model):
    class Provenance(models.TextChoices):
        BASE_CATALOG = "BASE_CATALOG", "Plantilla base del catálogo"
        USER_EDITED = "USER_EDITED", "Editado por el usuario"
        AI_SUGGESTED = "AI_SUGGESTED", "Sugerido por IA y aceptado"

    task = models.OneToOneField(
        WorkflowTask,
        on_delete=models.CASCADE,
        related_name="prompt",
        verbose_name="Tarea asociada",
    )
    prompt_text = models.TextField(
        verbose_name="Texto exacto de la plantilla del prompt",
    )
    prompt_version = models.PositiveIntegerField(
        default=1,
        verbose_name="Versión del prompt",
    )
    provenance = models.CharField(
        max_length=30,
        choices=Provenance.choices,
        default=Provenance.BASE_CATALOG,
        verbose_name="Procedencia del prompt",
    )
    parameters_schema = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Esquema de variables y parámetros permitidos",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Autor de la versión del prompt",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )

    class Meta:
        db_table = "thesis_workflow_prompt"
        verbose_name = "Prompt de recorrido"
        verbose_name_plural = "Prompts de recorrido"

    def __str__(self):
        return f"Prompt para {self.task.task_id} (v{self.prompt_version})"


class WorkflowTaskExecution(models.Model):
    """Ejecución versionada de una tarea personalizada fuera de P01-P32."""

    task = models.ForeignKey(WorkflowTask, on_delete=models.PROTECT, related_name="executions")
    workflow = models.ForeignKey(ProjectWorkflow, on_delete=models.PROTECT, related_name="task_executions")
    revision_no = models.PositiveIntegerField()
    idempotency_key = models.UUIDField()
    input_json = models.JSONField(default=dict)
    output_json = models.JSONField(default=dict)
    prompt_text_used = models.TextField(blank=True, default="")
    prompt_version_used = models.PositiveIntegerField(null=True, blank=True)
    output_sha256 = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "thesis_workflow_task_execution"
        ordering = ["task", "revision_no"]
        constraints = [
            models.UniqueConstraint(fields=["task", "revision_no"], name="unique_workflow_task_revision"),
            models.UniqueConstraint(fields=["task", "idempotency_key"], name="unique_workflow_task_idempotency"),
            models.CheckConstraint(condition=models.Q(revision_no__gt=0), name="workflow_task_revision_positive"),
        ]
