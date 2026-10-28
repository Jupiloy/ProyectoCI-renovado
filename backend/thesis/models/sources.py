"""Fuentes científicas, extractos y vínculos de evidencia."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from pgvector.django import VectorField

from .chapters import ChapterRevision
from .projects import Project


class SourceDocument(models.Model):
    class Kind(models.TextChoices):
        EXTERNAL = "EXTERNAL", "Fuente externa"
        UPLOAD = "UPLOAD", "Archivo aportado"

    class Status(models.TextChoices):
        PENDING_EXTRACTION = "PENDING_EXTRACTION", "Archivo pendiente de extracción"
        METADATA_CHECKED = "METADATA_CHECKED", "Registro consultado"
        UNVERIFIED_METADATA = "UNVERIFIED_METADATA", "Metadatos no cotejados"
        TEXT_CHECKED = "TEXT_CHECKED", "Texto extraído; no implica verificación científica"
        OCR_REQUIRED = "OCR_REQUIRED", "PDF sin texto extraíble"
        REJECTED = "REJECTED", "Excluido por filtro documental"

    class ExtractionMethod(models.TextChoices):
        POPPLER = "POPPLER", "Texto del PDF original"
        OCR = "OCR", "Texto de copia procesada por OCR"
        PYTHON_DOCX = "PYTHON_DOCX", "Extracción estructural DOCX"
        PYTHON_PPTX = "PYTHON_PPTX", "Extracción estructural PPTX"
        OPENPYXL = "OPENPYXL", "Extracción estructural XLSX"

    class ExtractionState(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", "Sin iniciar"
        QUEUED = "QUEUED", "En cola"
        EXTRACTED = "EXTRACTED", "Extracción con texto disponible"
        OCR_REQUIRED = "OCR_REQUIRED", "OCR pendiente para páginas sin texto"
        PARTIAL = "PARTIAL", "Extracción parcial"
        NO_TEXT = "NO_TEXT", "Sin texto extraíble"
        FAILED = "FAILED", "Extracción fallida"

    class RecordProvider(models.TextChoices):
        OPENALEX = "OPENALEX", "OpenAlex"
        SEMANTIC_SCHOLAR = "SEMANTIC_SCHOLAR", "Semantic Scholar"
        ALICIA = "ALICIA", "ALICIA / CONCYTEC"
        CROSSREF = "CROSSREF", "Crossref"
        SCOPUS = "SCOPUS", "Scopus (archivo importado por el usuario)"
        WEB_OF_SCIENCE = "WEB_OF_SCIENCE", "Web of Science (archivo importado por el usuario)"
        ZOTERO = "ZOTERO", "Zotero (biblioteca vinculada por el usuario)"
        OTHER = "OTHER", "Otro registro bibliográfico"

    class MetadataOrigin(models.TextChoices):
        PROVIDER_API = "PROVIDER_API", "Consulta de API del proveedor"
        USER_FILE_IMPORT = "USER_FILE_IMPORT", "Archivo bibliográfico del usuario"
        USER_SELECTED_CANDIDATE = "USER_SELECTED_CANDIDATE", "Resultado seleccionado por el usuario"
        USER_UPLOADED_FILE = "USER_UPLOADED_FILE", "Archivo cargado por el usuario"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="sources")
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.EXTERNAL)
    openalex_id = models.URLField(max_length=255, null=True, blank=True)
    record_provider = models.CharField(max_length=24, choices=RecordProvider.choices, blank=True, default=RecordProvider.OPENALEX)
    metadata_origin = models.CharField(max_length=32, choices=MetadataOrigin.choices, default=MetadataOrigin.PROVIDER_API)
    provider_record_id = models.CharField(max_length=512, null=True, blank=True)
    imported_file_sha256 = models.CharField(max_length=64, null=True, blank=True)
    imported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name="imported_bibliographic_sources")
    title = models.TextField()
    authors_json = models.JSONField(default=list)
    publication_year = models.PositiveSmallIntegerField(null=True, blank=True)
    doi = models.CharField(max_length=255, null=True, blank=True)
    abstract = models.TextField(blank=True)
    publication_venue = models.TextField(blank=True)
    url = models.URLField(max_length=2048, null=True, blank=True)
    pdf_url = models.URLField(max_length=2048, null=True, blank=True)
    openalex_retracted = models.BooleanField(null=True, blank=True)
    storage_key = models.CharField(max_length=500, null=True, blank=True)
    original_filename = models.CharField(max_length=255, blank=True, default="")
    sha256 = models.CharField(max_length=64, null=True, blank=True)
    derived_storage_key = models.CharField(max_length=500, null=True, blank=True)
    derived_sha256 = models.CharField(max_length=64, null=True, blank=True)
    extraction_method = models.CharField(max_length=16, choices=ExtractionMethod.choices, null=True, blank=True)
    extraction_state = models.CharField(max_length=20, choices=ExtractionState.choices,
                                        default=ExtractionState.NOT_STARTED)
    extraction_details_json = models.JSONField(default=dict)
    mime_type = models.CharField(max_length=100, null=True, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=Status.choices, default=Status.METADATA_CHECKED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "source_document"
        constraints = [
            models.UniqueConstraint(fields=["project", "openalex_id"], condition=Q(openalex_id__isnull=False), name="source_project_openalex_unique"),
            models.UniqueConstraint(fields=["project", "record_provider", "provider_record_id"],
                                    condition=Q(provider_record_id__isnull=False), name="source_project_provider_record_unique"),
            models.UniqueConstraint(fields=["project", "sha256"], condition=Q(sha256__isnull=False), name="source_project_sha_unique"),
            models.CheckConstraint(condition=Q(page_count__isnull=True) | Q(page_count__gt=0), name="source_positive_pages"),
            models.CheckConstraint(
                condition=Q(kind="EXTERNAL", record_provider__gt="")
                | Q(kind="UPLOAD", storage_key__isnull=False, sha256__isnull=False),
                name="source_kind_payload",
            ),
        ]
        indexes = [models.Index(fields=["project", "verification_status"], name="source_project_status_idx")]


class SourceExcerpt(models.Model):
    source = models.ForeignKey(SourceDocument, on_delete=models.CASCADE, related_name="excerpts")
    chunk_no = models.PositiveIntegerField()
    page_no = models.PositiveIntegerField()
    text = models.TextField()
    text_sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "source_excerpt"
        constraints = [
            models.UniqueConstraint(fields=["source", "chunk_no"], name="excerpt_source_chunk_unique"),
            models.CheckConstraint(condition=Q(chunk_no__gt=0, page_no__gt=0), name="excerpt_positive_location"),
            models.CheckConstraint(condition=~Q(text=""), name="excerpt_nonempty_text"),
        ]
        indexes = [models.Index(fields=["source", "page_no", "chunk_no"], name="excerpt_source_page_idx")]


class SourceSegment(models.Model):
    """Unidad de texto extraído con localizador propio del formato original."""

    class Kind(models.TextChoices):
        PARAGRAPH = "PARAGRAPH", "Párrafo"
        TABLE = "TABLE", "Tabla"
        SLIDE_TEXT = "SLIDE_TEXT", "Texto de diapositiva"
        SPREADSHEET_ROW = "SPREADSHEET_ROW", "Fila de hoja"
        IMAGE_REFERENCE = "IMAGE_REFERENCE", "Referencia a imagen no OCR"

    source = models.ForeignKey(SourceDocument, on_delete=models.CASCADE, related_name="segments")
    sequence_no = models.PositiveIntegerField()
    kind = models.CharField(max_length=24, choices=Kind.choices)
    locator_json = models.JSONField(default=dict)
    text = models.TextField(blank=True)
    text_sha256 = models.CharField(max_length=64)
    extraction_method = models.CharField(max_length=24)
    extraction_version = models.CharField(max_length=80)
    metadata_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "source_segment"
        constraints = [
            models.UniqueConstraint(fields=["source", "sequence_no"], name="segment_source_seq_unique"),
            models.CheckConstraint(condition=Q(sequence_no__gt=0), name="segment_positive_sequence"),
            models.CheckConstraint(condition=~Q(text="") | Q(kind="IMAGE_REFERENCE"), name="segment_text_or_image_ref"),
        ]
        indexes = [models.Index(fields=["source", "kind", "sequence_no"], name="segment_source_kind_seq_idx")]


class SourcePassage(models.Model):
    """Pasaje indexado que conserva su excerpt PDF o segmento multiformato."""

    excerpt = models.ForeignKey(SourceExcerpt, on_delete=models.CASCADE, null=True, blank=True, related_name="passages")
    segment = models.ForeignKey(SourceSegment, on_delete=models.CASCADE, null=True, blank=True, related_name="passages")
    start_char = models.PositiveIntegerField()
    text = models.TextField()
    text_sha256 = models.CharField(max_length=64)
    embedding = VectorField(dimensions=384)
    embedding_model = models.CharField(max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "source_passage"
        constraints = [
            models.UniqueConstraint(fields=["excerpt", "start_char"], name="passage_excerpt_start_unique"),
            models.UniqueConstraint(fields=["segment", "start_char"], name="passage_segment_start_unique"),
            models.CheckConstraint(
                condition=(Q(excerpt__isnull=False, segment__isnull=True) | Q(excerpt__isnull=True, segment__isnull=False)),
                name="passage_exactly_one_locator",
            ),
        ]


class SourceGrobidAnalysis(models.Model):
    """Extracción automática GROBID, separada de la verificación de portada."""

    source = models.OneToOneField(SourceDocument, on_delete=models.CASCADE, related_name="grobid_analysis")
    input_sha256 = models.CharField(max_length=64)
    tei_sha256 = models.CharField(max_length=64)
    tei_xml = models.TextField()
    extracted_title = models.TextField(blank=True)
    extracted_authors_json = models.JSONField(default=list)
    references_json = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "source_grobid_analysis"


class SourceMetadataCheck(models.Model):
    """Respuesta conservada de Crossref; acredita un registro, no el contenido del PDF."""

    source = models.OneToOneField(SourceDocument, on_delete=models.PROTECT, related_name="metadata_check")
    doi = models.CharField(max_length=255)
    registry = models.CharField(max_length=20, default="CROSSREF")
    registered_title = models.TextField()
    registered_authors_json = models.JSONField(default=list)
    title_similarity = models.FloatField(null=True, blank=True)
    registry_record_json = models.JSONField(default=dict)
    checked_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "source_metadata_check"


class EvidenceLink(models.Model):
    """Vínculo candidato entre una afirmación y texto físicamente localizado."""

    class Status(models.TextChoices):
        CANDIDATE = "CANDIDATE", "Pendiente de revisión"
        CONFIRMED = "CONFIRMED", "Confirmado por asesor"
        REJECTED = "REJECTED", "Rechazado por asesor"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="evidence_links")
    revision = models.ForeignKey(ChapterRevision, on_delete=models.PROTECT, null=True, blank=True, related_name="evidence_links")
    excerpt = models.ForeignKey(SourceExcerpt, on_delete=models.PROTECT, related_name="evidence_links")
    claim_text = models.TextField()
    start_char = models.PositiveIntegerField()
    end_char = models.PositiveIntegerField()
    matched_text = models.TextField()
    excerpt_sha256 = models.CharField(max_length=64)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CANDIDATE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_evidence_links")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="reviewed_evidence_links")
    review_note = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "evidence_link"
        constraints = [models.CheckConstraint(condition=Q(end_char__gt=models.F("start_char")), name="evidence_positive_range")]
        indexes = [models.Index(fields=["project", "status"], name="evidence_project_status_idx")]
