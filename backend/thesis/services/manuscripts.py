"""Borradores DOCX: original, texto convertido y campos de cita declarados."""

import hashlib
import uuid
from pathlib import Path

from django.conf import settings
from django.db import transaction

from thesis.integrations.docx import MAX_DOCX_BYTES, convert_docx, inspect_docx
from thesis.models import ManuscriptCitation, ManuscriptDocument
from thesis.services.access import require_project
from thesis.services.errors import DomainError


def _present(manuscript: ManuscriptDocument, *, include_text: bool = False) -> dict:
    result = {
        "manuscript_id": str(manuscript.id), "project_id": str(manuscript.project_id),
        "label": manuscript.label, "sha256": manuscript.sha256,
        "format": "DOCX", "citation_count": manuscript.citations.count(),
        "processing_status": manuscript.processing_status,
        "citation_verification": "FIELDS_ONLY_UNVERIFIED", "created_at": manuscript.created_at.isoformat(),
    }
    if include_text:
        result["markdown"] = manuscript.markdown
        result["citations"] = [
            {"kind": citation.kind, "part_name": citation.part_name,
             "paragraph_index": citation.paragraph_index, "display_text": citation.display_text,
             "field_code": citation.field_code, "citation_items": citation.citation_items,
             "verified_against_source": False}
            for citation in manuscript.citations.order_by("id")
        ]
    return result


def upload_docx_pending(actor, project_id, label: str, uploaded_file) -> dict:
    """Guarda bytes y encola la conversión sin cargar Docling en la petición."""
    project = require_project(actor, project_id, owner_only=True)
    label = label.strip()
    if not label or len(label) > 300:
        raise DomainError("VALIDATION_ERROR", "La etiqueta del borrador debe tener entre 1 y 300 caracteres")
    root = Path(settings.MEDIA_ROOT)
    folder = root / "manuscripts" / str(project.id)
    folder.mkdir(parents=True, exist_ok=True)
    temp = folder / f"upload-{uuid.uuid4().hex}.part"
    digest = hashlib.sha256()
    size = 0
    try:
        with temp.open("wb") as output:
            for chunk in uploaded_file.chunks():
                size += len(chunk)
                if size > MAX_DOCX_BYTES:
                    raise DomainError("VALIDATION_ERROR", "El DOCX supera el límite local de carga")
                output.write(chunk)
                digest.update(chunk)
        with temp.open("rb") as saved:
            header = saved.read(4)
        if not size or header != b"PK\x03\x04":
            raise DomainError("DOCX_UNREADABLE", "El archivo no tiene cabecera DOCX válida")
        duplicate = ManuscriptDocument.objects.filter(project=project, sha256=digest.hexdigest()).first()
        if duplicate:
            if duplicate.processing_status == ManuscriptDocument.ProcessingStatus.READY:
                return {**_present(duplicate), "upload_status": "DUPLICATE_DOCX"}
            from thesis.services.document_jobs import enqueue_manuscript_job
            return {**_present(duplicate), "upload_status": "DOCX_QUEUED",
                    "job": enqueue_manuscript_job(actor, project.id, duplicate.id)}
        manuscript = ManuscriptDocument(project=project, label=label, sha256=digest.hexdigest(), markdown="",
                                        processing_status=ManuscriptDocument.ProcessingStatus.QUEUED)
        destination = folder / f"{manuscript.id}.docx"
        manuscript.storage_key = str(destination.relative_to(root))
        temp.replace(destination)
        try:
            with transaction.atomic():
                manuscript.save()
                from thesis.services.document_jobs import enqueue_manuscript_job
                job = enqueue_manuscript_job(actor, project.id, manuscript.id)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return {**_present(manuscript), "upload_status": "DOCX_QUEUED", "job": job}
    finally:
        temp.unlink(missing_ok=True)


def process_pending_docx(actor, project_id, manuscript_id) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    manuscript = ManuscriptDocument.objects.filter(project=project, pk=manuscript_id).first()
    if manuscript is None:
        raise DomainError("NOT_FOUND", "Borrador no encontrado")
    if manuscript.processing_status != ManuscriptDocument.ProcessingStatus.QUEUED:
        raise DomainError("VERSION_CONFLICT", "El borrador no está pendiente de conversión")
    root = Path(settings.MEDIA_ROOT).resolve()
    path = (root / manuscript.storage_key).resolve()
    if not path.is_relative_to(root) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != manuscript.sha256:
        raise DomainError("DOCX_UNREADABLE", "El borrador no está disponible o cambió")
    citations = inspect_docx(path)
    markdown = convert_docx(path)
    with transaction.atomic():
        manuscript = ManuscriptDocument.objects.select_for_update().get(pk=manuscript.pk)
        if manuscript.processing_status != ManuscriptDocument.ProcessingStatus.QUEUED:
            raise DomainError("VERSION_CONFLICT", "El borrador ya fue convertido")
        manuscript.markdown = markdown
        manuscript.processing_status = ManuscriptDocument.ProcessingStatus.READY
        manuscript.save(update_fields=["markdown", "processing_status"])
        ManuscriptCitation.objects.bulk_create([ManuscriptCitation(manuscript=manuscript, **item) for item in citations])
    return {**_present(manuscript), "processing_status": "READY"}


def list_manuscripts(actor, project_id) -> list[dict]:
    project = require_project(actor, project_id)
    return [_present(item) for item in ManuscriptDocument.objects.filter(project=project).order_by("-created_at")]


def get_manuscript(actor, project_id, manuscript_id) -> dict:
    project = require_project(actor, project_id)
    manuscript = ManuscriptDocument.objects.filter(project=project, pk=manuscript_id).first()
    if manuscript is None:
        raise DomainError("NOT_FOUND", "Borrador no encontrado")
    return _present(manuscript, include_text=True)


def read_manuscript_section(actor, project_id, manuscript_id, *, offset: int = 0, limit: int = 5000) -> dict:
    if offset < 0 or not 1 <= limit <= 20000:
        raise DomainError("VALIDATION_ERROR", "Offset o límite inválido")
    project = require_project(actor, project_id)
    manuscript = ManuscriptDocument.objects.filter(project=project, pk=manuscript_id).first()
    if manuscript is None:
        raise DomainError("NOT_FOUND", "Borrador no encontrado")
    return {
        **_present(manuscript), "markdown": manuscript.markdown[offset:offset + limit],
        "offset": offset, "next_offset": min(offset + limit, len(manuscript.markdown)),
        "total_characters": len(manuscript.markdown),
    }


def list_manuscript_citations(actor, project_id, manuscript_id, *, offset: int = 0, limit: int = 20) -> dict:
    if offset < 0 or not 1 <= limit <= 50:
        raise DomainError("VALIDATION_ERROR", "Offset o límite inválido")
    project = require_project(actor, project_id)
    manuscript = ManuscriptDocument.objects.filter(project=project, pk=manuscript_id).first()
    if manuscript is None:
        raise DomainError("NOT_FOUND", "Borrador no encontrado")
    query = manuscript.citations.order_by("id")
    return {
        "manuscript_id": str(manuscript.id), "total_citations": query.count(),
        "offset": offset,
        "citations": [{
            "kind": citation.kind, "part_name": citation.part_name,
            "paragraph_index": citation.paragraph_index, "display_text": citation.display_text,
            "field_code": citation.field_code, "citation_items": citation.citation_items,
            "verified_against_source": False,
        } for citation in query[offset:offset + limit]],
    }
