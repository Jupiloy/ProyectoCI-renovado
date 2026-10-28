import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class AIGenerationBatch(models.Model):
    """Solicitud idempotente que agrupa trabajos B5.1 relacionados por contexto."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "thesis.Project", on_delete=models.PROTECT, related_name="ai_generation_batches",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_ai_batches",
    )
    workflow = models.ForeignKey(
        "thesis.ProjectWorkflow", on_delete=models.PROTECT, related_name="ai_batches",
    )
    workflow_version_no = models.PositiveIntegerField()
    state_version_at_request = models.PositiveIntegerField()
    idempotency_key = models.UUIDField()
    request_data = models.JSONField()
    request_sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "thesis_ai_generation_batch"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "idempotency_key"], name="unique_ai_batch_project_idempotency",
            ),
        ]
        indexes = [models.Index(fields=["project", "created_at"], name="ai_batch_proj_created_idx")]


class AIGenerationBatchItem(models.Model):
    """Asociación inmutable y ordenada entre una tarea del lote y su job B5.1."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        AIGenerationBatch, on_delete=models.PROTECT, related_name="items",
    )
    job = models.OneToOneField(
        "thesis.AIGenerationJob", on_delete=models.PROTECT, related_name="batch_item",
    )
    task_id = models.CharField(max_length=50)
    item_order = models.PositiveSmallIntegerField()
    input_sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "thesis_ai_generation_batch_item"
        ordering = ["item_order"]
        constraints = [
            models.UniqueConstraint(fields=["batch", "task_id"], name="unique_ai_batch_task"),
            models.UniqueConstraint(fields=["batch", "item_order"], name="unique_ai_batch_order"),
            models.CheckConstraint(
                condition=Q(item_order__gte=1, item_order__lte=8), name="ai_batch_order_range_ck",
            ),
        ]


class AIGenerationBatchSynthesis(models.Model):
    """Informe agregado independiente, encolado y revisable sobre outputs de un lote."""

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "En cola"
        RUNNING = "RUNNING", "En ejecución"
        SUCCEEDED = "SUCCEEDED", "Síntesis generada"
        FAILED = "FAILED", "Síntesis fallida"
        CANCELLED = "CANCELLED", "Cancelada antes de iniciar"

    class DecisionStatus(models.TextChoices):
        PENDING_REVIEW = "PENDING_REVIEW", "Pendiente de revisión del tesista"
        ACCEPTED = "ACCEPTED", "Revisada y aceptada como informe auxiliar"
        REJECTED = "REJECTED", "Rechazada por el tesista"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(AIGenerationBatch, on_delete=models.PROTECT, related_name="syntheses")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_batch_syntheses")
    idempotency_key = models.UUIDField()
    request_data = models.JSONField()
    request_sha256 = models.CharField(max_length=64)
    source_snapshot = models.JSONField()
    source_snapshot_sha256 = models.CharField(max_length=64)
    prompt_text_used = models.TextField()
    prompt_version_used = models.PositiveIntegerField(default=1)
    output_schema_used = models.JSONField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    decision_status = models.CharField(max_length=20, choices=DecisionStatus.choices, default=DecisionStatus.PENDING_REVIEW)
    output_data = models.JSONField(null=True, blank=True)
    output_sha256 = models.CharField(max_length=64, blank=True, default="")
    provider = models.CharField(max_length=50, blank=True, default="")
    model = models.CharField(max_length=100, blank=True, default="")
    usage_data = models.JSONField(default=dict, blank=True)
    error_code = models.CharField(max_length=50, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    decision_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="decided_batch_syntheses")
    decision_key = models.UUIDField(null=True, blank=True)
    decision_at = models.DateTimeField(null=True, blank=True)
    decision_reason = models.TextField(blank=True, default="")
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "thesis_ai_generation_batch_synthesis"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["batch", "idempotency_key"], name="unique_ai_batch_synthesis_key"),
        ]
        indexes = [models.Index(fields=["status", "created_at"], name="ai_batch_synth_queue_idx")]
