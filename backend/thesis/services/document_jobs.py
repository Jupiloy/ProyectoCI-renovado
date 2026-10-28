"""Cola PostgreSQL para el análisis y la indexación de fuentes."""

import logging

from django.db import transaction
from django.utils import timezone

from thesis.models import DocumentJob, ManuscriptDocument, SourceDocument
from thesis.services.access import require_project
from thesis.services.errors import DomainError


logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 3


def present_job(job: DocumentJob) -> dict:
    return {
        "job_id": str(job.id), "project_id": str(job.project_id),
        "source_id": str(job.source_id) if job.source_id else None,
        "manuscript_id": str(job.manuscript_id) if job.manuscript_id else None,
        "kind": job.kind, "status": job.status,
        "attempts": job.attempts, "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "result": job.result_json, "error_code": job.error_code or None,
        "error_message": job.error_message or None,
    }


def enqueue_document_job(actor, project_id, source_id, kind: str) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    if kind not in (DocumentJob.Kind.GROBID, DocumentJob.Kind.INDEX,
                    DocumentJob.Kind.OCR, DocumentJob.Kind.DOI_CHECK, DocumentJob.Kind.PDF_EXTRACT,
                    DocumentJob.Kind.OPENALEX_PDF, DocumentJob.Kind.FORMAT_EXTRACT):
        raise DomainError("VALIDATION_ERROR", "Tipo de trabajo inválido")
    with transaction.atomic():
        source = SourceDocument.objects.select_for_update().filter(project=project, pk=source_id).first()
        if source is None:
            raise DomainError("NOT_FOUND", "Fuente no encontrada")
        if kind == DocumentJob.Kind.OCR and source.verification_status != SourceDocument.Status.OCR_REQUIRED:
            raise DomainError("VALIDATION_ERROR", "La fuente no requiere OCR")
        if kind in (DocumentJob.Kind.PDF_EXTRACT, DocumentJob.Kind.FORMAT_EXTRACT) and source.verification_status != SourceDocument.Status.PENDING_EXTRACTION:
            raise DomainError("VALIDATION_ERROR", "La fuente no está pendiente de extracción")
        if kind == DocumentJob.Kind.PDF_EXTRACT and source.mime_type != "application/pdf":
            raise DomainError("VALIDATION_ERROR", "La extracción PDF requiere un archivo PDF")
        if kind == DocumentJob.Kind.FORMAT_EXTRACT and source.mime_type == "application/pdf":
            raise DomainError("VALIDATION_ERROR", "La extracción Office no admite PDF")
        if kind == DocumentJob.Kind.OPENALEX_PDF and (source.kind != SourceDocument.Kind.EXTERNAL or not source.pdf_url or source.openalex_retracted is True):
            raise DomainError("VALIDATION_ERROR", "La fuente OpenAlex no tiene un PDF permitido")
        if kind in (DocumentJob.Kind.GROBID, DocumentJob.Kind.INDEX) and source.verification_status != SourceDocument.Status.TEXT_CHECKED:
            raise DomainError("VALIDATION_ERROR", "La fuente requiere texto extraído")
        if kind == DocumentJob.Kind.DOI_CHECK and not source.doi:
            raise DomainError("VALIDATION_ERROR", "La fuente no tiene DOI declarado")
        if kind == DocumentJob.Kind.GROBID and not source.storage_key:
            raise DomainError("VALIDATION_ERROR", "El análisis GROBID requiere un PDF disponible")
        existing = DocumentJob.objects.filter(
            source=source, kind=kind, status__in=[DocumentJob.Status.QUEUED, DocumentJob.Status.RUNNING],
        ).first()
        if existing:
            return present_job(existing)
        job = DocumentJob.objects.create(project=project, source=source, requested_by=actor, kind=kind)
        return present_job(job)


def get_document_job(actor, project_id, job_id) -> dict:
    project = require_project(actor, project_id)
    job = DocumentJob.objects.filter(project=project, pk=job_id).first()
    if job is None:
        raise DomainError("NOT_FOUND", "Trabajo no encontrado")
    return present_job(job)


def enqueue_manuscript_job(actor, project_id, manuscript_id) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    with transaction.atomic():
        manuscript = ManuscriptDocument.objects.select_for_update().filter(project=project, pk=manuscript_id).first()
        if manuscript is None:
            raise DomainError("NOT_FOUND", "Borrador no encontrado")
        existing = DocumentJob.objects.filter(manuscript=manuscript, kind=DocumentJob.Kind.DOCX,
                                              status__in=[DocumentJob.Status.QUEUED, DocumentJob.Status.RUNNING]).first()
        if existing:
            return present_job(existing)
        if manuscript.processing_status == ManuscriptDocument.ProcessingStatus.READY:
            raise DomainError("VALIDATION_ERROR", "El borrador ya fue convertido")
        manuscript.processing_status = ManuscriptDocument.ProcessingStatus.QUEUED
        manuscript.save(update_fields=["processing_status"])
        job = DocumentJob.objects.create(project=project, manuscript=manuscript,
                                         requested_by=actor, kind=DocumentJob.Kind.DOCX)
        return present_job(job)


def recover_interrupted_jobs() -> None:
    """Solo se llama tras adquirir el bloqueo global del trabajador."""
    DocumentJob.objects.filter(status=DocumentJob.Status.RUNNING, attempts__gte=MAX_ATTEMPTS).update(
        status=DocumentJob.Status.FAILED, error_code="WORKER_INTERRUPTED",
        error_message="El trabajador se interrumpió repetidamente", finished_at=timezone.now(),
    )
    DocumentJob.objects.filter(status=DocumentJob.Status.RUNNING, attempts__lt=MAX_ATTEMPTS).update(
        status=DocumentJob.Status.QUEUED, started_at=None,
    )


def run_next_document_job() -> bool:
    """Reclama un trabajo y ejecuta su operación fuera de la transacción de reclamo."""
    with transaction.atomic():
        job = DocumentJob.objects.select_for_update(skip_locked=True).filter(
            status=DocumentJob.Status.QUEUED,
        ).order_by("created_at", "id").first()
        if job is None:
            return False
        job.status = DocumentJob.Status.RUNNING
        job.attempts += 1
        job.started_at = timezone.now()
        job.save(update_fields=["status", "attempts", "started_at"])

    try:
        if job.kind == DocumentJob.Kind.GROBID:
            from thesis.services.grobid import analyze_source_grobid
            result = analyze_source_grobid(job.requested_by, job.project_id, job.source_id)
        elif job.kind == DocumentJob.Kind.INDEX:
            from thesis.services.search import index_source_passages
            result = index_source_passages(job.requested_by, job.project_id, job.source_id)
        elif job.kind == DocumentJob.Kind.OCR:
            from thesis.services.sources import process_source_ocr
            result = process_source_ocr(job.requested_by, job.project_id, job.source_id)
        elif job.kind == DocumentJob.Kind.DOI_CHECK:
            from thesis.services.evidence import check_source_doi
            result = check_source_doi(job.requested_by, job.project_id, job.source_id)
        elif job.kind == DocumentJob.Kind.DOCX:
            from thesis.services.manuscripts import process_pending_docx
            result = process_pending_docx(job.requested_by, job.project_id, job.manuscript_id)
        elif job.kind == DocumentJob.Kind.PDF_EXTRACT:
            from thesis.services.sources import extract_pending_pdf
            result = extract_pending_pdf(job.requested_by, job.project_id, job.source_id)
        elif job.kind == DocumentJob.Kind.FORMAT_EXTRACT:
            from thesis.services.sources import extract_pending_multiformat
            result = extract_pending_multiformat(job.requested_by, job.project_id, job.source_id)
        elif job.kind == DocumentJob.Kind.OPENALEX_PDF:
            from thesis.services.sources import import_openalex_source
            source = SourceDocument.objects.get(pk=job.source_id)
            result = import_openalex_source(job.requested_by, job.project_id, source.openalex_id)
        else:
            raise DomainError("VALIDATION_ERROR", "Tipo de trabajo desconocido")
    except DomainError as exc:
        if job.manuscript_id:
            ManuscriptDocument.objects.filter(pk=job.manuscript_id).update(processing_status=ManuscriptDocument.ProcessingStatus.FAILED)
        DocumentJob.objects.filter(pk=job.pk).update(
            status=DocumentJob.Status.FAILED, result_json=None,
            error_code=exc.code, error_message=exc.message[:1000], finished_at=timezone.now(),
        )
        if job.source_id and job.kind in (DocumentJob.Kind.PDF_EXTRACT, DocumentJob.Kind.FORMAT_EXTRACT):
            SourceDocument.objects.filter(pk=job.source_id).update(
                extraction_state=SourceDocument.ExtractionState.FAILED,
                extraction_details_json={"error_code": exc.code, "extraction_succeeded": False},
            )
    except Exception:
        logger.exception("Falló el trabajo documental %s", job.pk)
        if job.manuscript_id:
            ManuscriptDocument.objects.filter(pk=job.manuscript_id).update(processing_status=ManuscriptDocument.ProcessingStatus.FAILED)
        DocumentJob.objects.filter(pk=job.pk).update(
            status=DocumentJob.Status.FAILED, result_json=None,
            error_code="INTERNAL_ERROR", error_message="Error interno del procesamiento",
            finished_at=timezone.now(),
        )
        if job.source_id and job.kind in (DocumentJob.Kind.PDF_EXTRACT, DocumentJob.Kind.FORMAT_EXTRACT):
            SourceDocument.objects.filter(pk=job.source_id).update(
                extraction_state=SourceDocument.ExtractionState.FAILED,
                extraction_details_json={"error_code": "INTERNAL_ERROR", "extraction_succeeded": False},
            )
    else:
        DocumentJob.objects.filter(pk=job.pk).update(
            status=DocumentJob.Status.SUCCEEDED, result_json=result,
            error_code="", error_message="", finished_at=timezone.now(),
        )
    return True
