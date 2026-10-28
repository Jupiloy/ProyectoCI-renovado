import uuid
from django.conf import settings
from django.db import models


class AIGenerationJob(models.Model):
    """Trabajo persistente y observable de generación con IA iniciado por el backend."""

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "En cola"
        RUNNING = "RUNNING", "En ejecución"
        SUCCEEDED = "SUCCEEDED", "Generación completada"
        FAILED = "FAILED", "Generación fallida"
        CANCELLED = "CANCELLED", "Generación cancelada"

    class AcceptanceStatus(models.TextChoices):
        PENDING_ACCEPTANCE = "PENDING_ACCEPTANCE", "Pendiente de aceptación humana"
        ACCEPTED = "ACCEPTED", "Aceptada e incorporada como revisión canónica"
        REJECTED = "REJECTED", "Rechazada explícitamente por el tesista"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "thesis.Project",
        on_delete=models.PROTECT,
        related_name="ai_generation_jobs",
        verbose_name="Proyecto",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_ai_jobs",
        verbose_name="Solicitado por",
    )
    workflow = models.ForeignKey(
        "thesis.ProjectWorkflow",
        on_delete=models.PROTECT,
        related_name="ai_jobs",
        verbose_name="Recorrido activo asociado",
    )
    workflow_version_no = models.PositiveIntegerField(
        verbose_name="Versión del recorrido al encolar",
    )
    state_version_at_request = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Versión del estado del proyecto al solicitar generación",
    )
    task = models.ForeignKey(
        "thesis.WorkflowTask",
        on_delete=models.PROTECT,
        related_name="ai_jobs",
        verbose_name="Tarea del recorrido asociada",
    )
    workflow_task_id = models.CharField(
        max_length=50,
        verbose_name="Identificador de la tarea (ej. P01 o USR_...)",
    )
    prompt = models.ForeignKey(
        "thesis.WorkflowPrompt",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_jobs",
        verbose_name="Prompt utilizado",
    )
    prompt_text_used = models.TextField(
        blank=True,
        default="",
        verbose_name="Texto exacto del prompt inyectado",
    )
    prompt_version_used = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Versión del prompt utilizada",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
        verbose_name="Estado de ejecución del job",
    )
    acceptance_status = models.CharField(
        max_length=30,
        choices=AcceptanceStatus.choices,
        default=AcceptanceStatus.PENDING_ACCEPTANCE,
        verbose_name="Estado de aceptación de la propuesta",
    )
    idempotency_key = models.UUIDField(
        verbose_name="Clave de idempotencia de la solicitud",
    )
    input_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Entrada específica suministrada por el usuario",
    )
    context_snapshot = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Instantánea de variables/perfil/dependencias autorizadas",
    )
    context_sha256 = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Hash SHA-256 del contexto inyectado",
    )
    output_schema_used = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Esquema de salida requerido",
    )
    output_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Propuesta generada estructurada y validada localmente",
    )
    output_sha256 = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Hash SHA-256 de la salida generada",
    )
    provider = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Proveedor de IA efectivamente utilizado",
    )
    model = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Modelo de IA efectivamente utilizado",
    )
    usage_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métricas reales de uso devueltas por el proveedor (tokens, etc.)",
    )
    error_code = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Código de error normalizado seguro",
    )
    error_message = models.TextField(
        blank=True,
        default="",
        verbose_name="Mensaje seguro de error para el usuario",
    )
    decision_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decided_ai_jobs",
        verbose_name="Usuario que tomó la decisión de aceptar/rechazar",
    )
    decision_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de la decisión humana",
    )
    decision_key = models.UUIDField(
        null=True,
        blank=True,
        verbose_name="Clave idempotente de la decisión humana",
    )
    decision_reason = models.TextField(
        blank=True,
        default="",
        verbose_name="Motivo opcional del rechazo o aceptación",
    )
    result_revision_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="ID de ChapterRevision generada al aceptar (para P01-P32)",
    )
    result_execution_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="ID de WorkflowTaskExecution generada al aceptar (para USR_...)",
    )
    result_document_revision = models.ForeignKey(
        "thesis.ChapterDocumentRevision",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="accepted_ai_jobs",
        verbose_name="Revisión canónica creada al aceptar texto P05/P29",
    )
    attempts = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Número de intentos de ejecución",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de encolado",
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de inicio de ejecución",
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de finalización",
    )

    class Meta:
        db_table = "thesis_ai_generation_job"
        verbose_name = "Trabajo de generación con IA"
        verbose_name_plural = "Trabajos de generación con IA"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "idempotency_key"],
                name="unique_ai_job_project_idempotency",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "created_at"], name="ai_job_queue_idx"),
            models.Index(fields=["project", "workflow_task_id"], name="ai_job_proj_task_idx"),
        ]

    def __str__(self):
        return f"AIJob {self.id} [{self.workflow_task_id}] ({self.status} / {self.acceptance_status})"
