"""Rutas de evidence; registradas en el router compartido."""

from uuid import UUID
from ninja import File, Form, Status, UploadedFile
from thesis.models import DocumentJob
from thesis.services.document_jobs import enqueue_document_job, get_document_job
from thesis.services.evidence import get_source_metadata_check, locate_quote
from thesis.services.evidence_links import create_evidence_link, list_evidence_links, review_evidence_link
from thesis.services.grobid import get_source_grobid
from thesis.services.manuscripts import get_manuscript, list_manuscripts, upload_docx_pending
from thesis.services.search import search_passages
from .schemas import EvidenceDecisionIn, EvidenceLinkIn, QuoteIn, SearchPassagesIn
from .routers import router


@router.post("/{project_id}/sources/{source_id}/doi-check", response={202: dict}, operation_id="thesis_api_projects_check_doi")
def check_doi(request, project_id: UUID, source_id: UUID):
    return Status(202, enqueue_document_job(request.user, project_id, source_id, DocumentJob.Kind.DOI_CHECK))


@router.get("/{project_id}/sources/{source_id}/doi-check", operation_id="thesis_api_projects_doi_check")
def doi_check(request, project_id: UUID, source_id: UUID):
    return get_source_metadata_check(request.user, project_id, source_id)


@router.post("/{project_id}/sources/{source_id}/locate", operation_id="thesis_api_projects_locate_source_quote")
def locate_source_quote(request, project_id: UUID, source_id: UUID, payload: QuoteIn):
    return locate_quote(request.user, project_id, source_id, payload.quote, limit=payload.limit)


@router.post("/{project_id}/evidence-links", operation_id="thesis_api_projects_add_evidence")
def add_evidence(request, project_id: UUID, payload: EvidenceLinkIn):
    return create_evidence_link(request.user, project_id, payload.excerpt_id, payload.claim_text,
                                payload.start_char, payload.end_char, payload.matched_text, payload.revision_id)


@router.get("/{project_id}/evidence-links", operation_id="thesis_api_projects_evidence_links")
def evidence_links(request, project_id: UUID, limit: int = 50):
    return list_evidence_links(request.user, project_id, limit=limit)


@router.post("/{project_id}/evidence-links/{link_id}/review", operation_id="thesis_api_projects_review_evidence")
def review_evidence(request, project_id: UUID, link_id: int, payload: EvidenceDecisionIn):
    return review_evidence_link(request.user, project_id, link_id, payload.decision, payload.note)


@router.post("/{project_id}/sources/{source_id}/ocr", response={202: dict}, operation_id="thesis_api_projects_ocr_source")
def ocr_source(request, project_id: UUID, source_id: UUID):
    return Status(202, enqueue_document_job(request.user, project_id, source_id, DocumentJob.Kind.OCR))


@router.post("/{project_id}/sources/{source_id}/grobid", response={202: dict}, operation_id="thesis_api_projects_grobid_source")
def grobid_source(request, project_id: UUID, source_id: UUID):
    return Status(202, enqueue_document_job(request.user, project_id, source_id, DocumentJob.Kind.GROBID))


@router.get("/{project_id}/sources/{source_id}/grobid", operation_id="thesis_api_projects_grobid_analysis")
def grobid_analysis(request, project_id: UUID, source_id: UUID, offset: int = 0, limit: int = 20):
    return get_source_grobid(request.user, project_id, source_id, offset=offset, limit=limit)


@router.post("/{project_id}/sources/{source_id}/index", response={202: dict}, operation_id="thesis_api_projects_index_source")
def index_source(request, project_id: UUID, source_id: UUID):
    return Status(202, enqueue_document_job(request.user, project_id, source_id, DocumentJob.Kind.INDEX))


@router.get("/{project_id}/jobs/{job_id}", operation_id="thesis_api_projects_document_job")
def document_job(request, project_id: UUID, job_id: UUID):
    return get_document_job(request.user, project_id, job_id)


@router.post("/{project_id}/passages/search", operation_id="thesis_api_projects_search_source_passages")
def search_source_passages(request, project_id: UUID, payload: SearchPassagesIn):
    return search_passages(request.user, project_id, payload.query,
                           limit=payload.limit, source_ids=payload.source_ids)


@router.post("/{project_id}/manuscripts/upload", response={200: dict, 202: dict}, operation_id="thesis_api_projects_upload_manuscript")
def upload_manuscript(request, project_id: UUID, label: Form[str], file: File[UploadedFile]):
    result = upload_docx_pending(request.user, project_id, label, file)
    return Status(202, result) if result["processing_status"] == "QUEUED" else result


@router.get("/{project_id}/manuscripts", operation_id="thesis_api_projects_manuscripts")
def manuscripts(request, project_id: UUID):
    return list_manuscripts(request.user, project_id)


@router.get("/{project_id}/manuscripts/{manuscript_id}", operation_id="thesis_api_projects_manuscript")
def manuscript(request, project_id: UUID, manuscript_id: UUID):
    return get_manuscript(request.user, project_id, manuscript_id)
