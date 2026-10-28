"""Trabajos documentales y manuscritos del tesista."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from .projects import Project
from .sources import SourceDocument


class DocumentJob(models.Model):
    """Trabajo documental persistente; un trabajador lo ejecuta fuera de la petición."""

    class Kind(models.TextChoices):
        GROBID = "GROBID", "Analizar PDF con GROBID"
        INDEX = "INDEX", "Indexar pasajes"
        OCR = "OCR", "Reconocer texto del PDF"
        DOI_CHECK = "DOI_CHECK", "Cotejar registro DOI"
        DOCX = "DOCX", "Convertir borrador Word"
        PDF_EXTRACT = "PDF_EXTRACT", "Extraer páginas PDF"
        OPENALEX_PDF = "OPENALEX_PDF", "Descargar y extraer PDF OpenAlex"
        FORMAT_EXTRACT = "FORMAT_EXTRACT", "Extraer estructura de documento multiformato"

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "En cola"
        RUNNING = "RUNNING", "En proceso"
        SUCCEEDED = "SUCCEEDED", "Completado"
        FAILED = "FAILED", "Fallido"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="document_jobs")
    source = models.ForeignKey(SourceDocument, on_delete=models.PROTECT, null=True, blank=True, related_name="document_jobs")
    manuscript = models.ForeignKey("ManuscriptDocument", on_delete=models.PROTECT, null=True, blank=True, related_name="document_jobs")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    attempts = models.PositiveSmallIntegerField(default=0)
    result_json = models.JSONField(null=True, blank=True)
    error_code = models.CharField(max_length=40, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "document_job"
        constraints = [models.UniqueConstraint(
            fields=["source", "kind"],
            condition=Q(source__isnull=False, status__in=["QUEUED", "RUNNING"]),
            name="document_job_one_active_source_kind",
        ), models.UniqueConstraint(
            fields=["manuscript", "kind"],
            condition=Q(manuscript__isnull=False, status__in=["QUEUED", "RUNNING"]),
            name="document_job_one_active_manuscript",
        ), models.CheckConstraint(
            condition=Q(source__isnull=False, manuscript__isnull=True) | Q(source__isnull=True, manuscript__isnull=False),
            name="document_job_single_target",
        )]
        indexes = [models.Index(fields=["status", "created_at"], name="document_job_queue_idx")]


class ManuscriptDocument(models.Model):
    """Borrador aportado por el usuario; no equivale a una fuente comprobada."""

    class ProcessingStatus(models.TextChoices):
        QUEUED = "QUEUED", "En cola"
        READY = "READY", "Convertido"
        FAILED = "FAILED", "Fallido"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="manuscripts")
    label = models.CharField(max_length=300)
    storage_key = models.CharField(max_length=500)
    sha256 = models.CharField(max_length=64)
    markdown = models.TextField()
    processing_status = models.CharField(max_length=10, choices=ProcessingStatus.choices, default=ProcessingStatus.READY)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "manuscript_document"
        constraints = [models.UniqueConstraint(fields=["project", "sha256"], name="manuscript_project_sha_unique")]


class ManuscriptCitation(models.Model):
    class Kind(models.TextChoices):
        WORD = "WORD", "Campo CITATION de Word"
        ZOTERO = "ZOTERO", "Campo CSL_CITATION de Zotero"

    manuscript = models.ForeignKey(ManuscriptDocument, on_delete=models.CASCADE, related_name="citations")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    part_name = models.CharField(max_length=100)
    paragraph_index = models.PositiveIntegerField()
    display_text = models.TextField()
    field_code = models.TextField()
    citation_items = models.JSONField(default=list)

    class Meta:
        db_table = "manuscript_citation"
        indexes = [models.Index(fields=["manuscript", "part_name", "paragraph_index"], name="citation_manuscript_loc_idx")]
