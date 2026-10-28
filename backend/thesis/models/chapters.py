"""Avance, revisiones y decisiones del asesor."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django_fsm import FSMField, FSMModelMixin, transition

from .projects import Project


class StepProgress(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "En curso"
        COMPLETED = "COMPLETED", "Completado"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="steps")
    step_code = models.CharField(max_length=3)
    task_id = models.CharField(max_length=50, blank=True, default="", verbose_name="ID de tarea en workflow")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IN_PROGRESS)
    output_json = models.JSONField(default=dict)
    workflow = models.ForeignKey(
        "thesis.ProjectWorkflow",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="step_progress_records",
        verbose_name="Recorrido asociado",
    )
    workflow_version_no = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Versión del recorrido al completar",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "step_progress"
        constraints = [models.UniqueConstraint(fields=["project", "step_code"], name="step_project_code_unique")]


class Chapter(FSMModelMixin, models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        READY = "READY", "En revisión"
        CHANGES_REQUESTED = "CHANGES_REQUESTED", "Con observaciones"
        APPROVED = "APPROVED", "Aprobado"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="chapters")
    number = models.PositiveSmallIntegerField()
    status = FSMField(default=Status.DRAFT, protected=True, choices=Status.choices)
    approved_revision = models.ForeignKey("ChapterRevision", on_delete=models.PROTECT, null=True, blank=True, related_name="approving_chapters")
    approved_snapshot = models.ForeignKey(
        "ChapterSnapshot",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approving_chapters",
        verbose_name="Instantánea aprobada",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    submitted_snapshot = models.ForeignKey(
        "ChapterSnapshot",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="submitted_for_chapters",
        verbose_name="Instantánea vigente de envío",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @transition(field=status, source=[Status.DRAFT, Status.CHANGES_REQUESTED], target=Status.READY)
    def submit(self):
        pass

    @transition(field=status, source=Status.READY, target=Status.CHANGES_REQUESTED)
    def request_changes(self):
        pass

    @transition(field=status, source=Status.READY, target=Status.APPROVED)
    def approve(self):
        pass

    @transition(field=status, source=Status.APPROVED, target=Status.DRAFT)
    def reopen(self):
        pass

    @transition(field=status, source=Status.CHANGES_REQUESTED, target=Status.DRAFT)
    def resume_editing(self):
        pass

    class Meta:
        db_table = "chapter"
        constraints = [
            models.UniqueConstraint(fields=["project", "number"], name="chapter_project_number_unique"),
            models.CheckConstraint(condition=Q(number__gte=1, number__lte=7), name="chapter_number_range"),
        ]


class ChapterRevision(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.PROTECT, related_name="revisions")
    revision_no = models.PositiveIntegerField()
    step_code = models.CharField(max_length=3)
    idempotency_key = models.UUIDField()
    content_md = models.TextField()
    content_sha256 = models.CharField(max_length=64)
    workflow = models.ForeignKey(
        "thesis.ProjectWorkflow",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revisions",
        verbose_name="Recorrido asociado",
    )
    workflow_version_no = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Versión del recorrido al crear la revisión",
    )
    prompt_text_used = models.TextField(
        blank=True,
        default="",
        verbose_name="Texto exacto del prompt utilizado",
    )
    prompt_version_used = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Versión del prompt utilizada",
    )
    context_snapshot = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Instantánea de variables/contexto al generar",
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chapter_revision"
        constraints = [
            models.UniqueConstraint(fields=["chapter", "revision_no"], name="revision_chapter_number_unique"),
            models.UniqueConstraint(fields=["chapter", "idempotency_key"], name="revision_chapter_key_unique"),
            models.CheckConstraint(condition=Q(revision_no__gt=0), name="revision_positive_number"),
            models.CheckConstraint(condition=~Q(content_md=""), name="revision_nonempty_content"),
        ]


class ChapterDocument(models.Model):
    """Documento canónico editable de un capítulo y puntero a su versión vigente."""

    chapter = models.OneToOneField(Chapter, on_delete=models.PROTECT, related_name="canonical_document")
    current_revision = models.ForeignKey(
        "ChapterDocumentRevision",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="current_for_documents",
    )
    lock_version = models.PositiveIntegerField(default=0)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chapter_document"


class ChapterDocumentRevision(models.Model):
    """Versión append-only del árbol editable y de su proyección Markdown."""

    class Source(models.TextChoices):
        USER_EDIT = "USER_EDIT", "Edición del tesista"
        AI_PROPOSAL = "AI_PROPOSAL", "Propuesta IA aceptada por el tesista"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(ChapterDocument, on_delete=models.PROTECT, related_name="revisions")
    revision_no = models.PositiveIntegerField()
    schema_version = models.PositiveSmallIntegerField(default=1)
    content_tree = models.JSONField(default=dict)
    content_md = models.TextField(blank=True, default="")
    content_sha256 = models.CharField(max_length=64)
    citation_manifest_sha256 = models.CharField(max_length=64, blank=True, default="")
    state_version = models.PositiveIntegerField()
    idempotency_key = models.UUIDField()
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.USER_EDIT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chapter_document_revision"
        constraints = [
            models.UniqueConstraint(fields=["document", "revision_no"], name="chapter_doc_revision_number_unique"),
            models.UniqueConstraint(fields=["document", "idempotency_key"], name="chapter_doc_revision_key_unique"),
            models.CheckConstraint(condition=Q(revision_no__gt=0), name="chapter_doc_revision_positive_number"),
            models.CheckConstraint(condition=Q(schema_version__in=[1, 2]), name="chapter_doc_revision_schema_supported_ck"),
        ]
        indexes = [models.Index(fields=["document", "-revision_no"], name="chapter_doc_revision_order_idx")]


class ReviewComment(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Abierta"
        RESOLVED = "RESOLVED", "Resuelta"

    revision = models.ForeignKey(
        ChapterRevision,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="comments",
    )
    snapshot = models.ForeignKey(
        "ChapterSnapshot",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="comments",
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="authored_comments")
    start_cp = models.PositiveIntegerField()
    end_cp = models.PositiveIntegerField()
    selected_text = models.TextField()
    body = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="resolved_comments")
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "review_comment"
        constraints = [
            models.CheckConstraint(condition=Q(end_cp__gt=models.F("start_cp")), name="comment_positive_range"),
            models.CheckConstraint(
                condition=(
                    Q(revision__isnull=False, snapshot__isnull=True)
                    | Q(revision__isnull=True, snapshot__isnull=False)
                ),
                name="review_comment_exactly_one_anchor",
            ),
        ]
        indexes = [
            models.Index(fields=["revision", "status", "created_at"], name="review_comment_status_idx"),
            models.Index(fields=["snapshot", "status", "created_at"], name="review_comment_snap_status_idx"),
        ]


class ReviewEvent(models.Model):
    class Action(models.TextChoices):
        SUBMIT = "SUBMIT", "Enviado"
        REQUEST_CHANGES = "REQUEST_CHANGES", "Observado"
        APPROVE = "APPROVE", "Aprobado"
        REOPEN = "REOPEN", "Reabierto"

    chapter = models.ForeignKey(Chapter, on_delete=models.PROTECT, related_name="review_events")
    revision = models.ForeignKey(ChapterRevision, on_delete=models.PROTECT, null=True, blank=True)
    snapshot = models.ForeignKey("ChapterSnapshot", on_delete=models.PROTECT, null=True, blank=True, related_name="review_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=20, choices=Action.choices)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "review_event"
        indexes = [models.Index(fields=["chapter", "created_at"], name="review_event_chapter_idx")]


class ChapterSnapshot(models.Model):
    """Instantánea integral e inmutable de un capítulo al ser enviado para revisión."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chapter = models.ForeignKey(Chapter, on_delete=models.PROTECT, related_name="snapshots")
    document_revision = models.ForeignKey(
        ChapterDocumentRevision,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="chapter_snapshots",
    )
    snapshot_no = models.PositiveIntegerField()
    format_version = models.PositiveSmallIntegerField(default=1)
    project_title = models.CharField(max_length=300, blank=True, default="")
    state_version = models.PositiveIntegerField(null=True, blank=True)
    workflow = models.ForeignKey(
        "thesis.ProjectWorkflow",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="chapter_snapshots",
        verbose_name="Recorrido asociado",
    )
    workflow_version_no = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Versión del recorrido al congelar",
    )
    content_md = models.TextField(blank=True, default="")
    sections_manifest = models.JSONField(default=list)
    document_artifacts_manifest = models.JSONField(default=list)
    payload_sha256 = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chapter_snapshot"
        constraints = [
            models.UniqueConstraint(fields=["chapter", "snapshot_no"], name="chapter_snapshot_chapter_number_unique"),
            models.CheckConstraint(condition=Q(snapshot_no__gt=0), name="chapter_snapshot_positive_number"),
        ]
        indexes = [
            models.Index(fields=["chapter", "-snapshot_no"], name="chapter_snapshot_ordering_idx"),
        ]
