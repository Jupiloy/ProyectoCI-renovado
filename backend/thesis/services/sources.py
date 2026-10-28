"""Incorporación de registros OpenAlex y evidencia textual localizada."""

import hashlib
import uuid
from pathlib import Path

from django.conf import settings
from django.db import transaction

from thesis.integrations.openalex import get_work
from thesis.integrations.ocr import create_searchable_pdf
from thesis.integrations.pdf import MAX_PDF_BYTES, download_pdf, extract_pages
from thesis.models import DocumentJob, SourceDocument, SourceExcerpt, SourceSegment
from thesis.services.access import require_project
from thesis.services.source_serialization import _present
from thesis.services.errors import DomainError




def _excerpt_rows(source: SourceDocument, pages: list[tuple[int, str]]) -> list[SourceExcerpt]:
    chunks = []
    for page_no, page_text in pages:
        for offset in range(0, len(page_text), 4000):
            content = page_text[offset:offset + 4000].strip()
            if content:
                chunks.append(SourceExcerpt(
                    source=source, chunk_no=len(chunks) + 1, page_no=page_no,
                    text=content, text_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                ))
    return chunks


def _register_openalex_work(project, work: dict) -> SourceDocument:
    source, created = SourceDocument.objects.get_or_create(
        project=project, openalex_id=work["openalex_id"],
        defaults={
            "record_provider": SourceDocument.RecordProvider.OPENALEX,
            "metadata_origin": SourceDocument.MetadataOrigin.PROVIDER_API,
            "provider_record_id": work["openalex_id"].rsplit("/", 1)[-1],
            "title": work["title"], "authors_json": work["authors"],
            "publication_year": work["publication_year"], "doi": work["doi"],
            "url": work["landing_page_url"], "pdf_url": work["pdf_url"],
            "openalex_retracted": work.get("openalex_retracted"),
            "verification_status": SourceDocument.Status.REJECTED if work.get("openalex_retracted") is True else SourceDocument.Status.METADATA_CHECKED,
        },
    )
    if not created and source.openalex_retracted != work.get("openalex_retracted"):
        source.openalex_retracted = work.get("openalex_retracted")
        if source.openalex_retracted is True:
            source.verification_status = SourceDocument.Status.REJECTED
        source.save(update_fields=["openalex_retracted", "verification_status"])
    return source


def enqueue_openalex_source(actor, project_id, openalex_id: str) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    work = get_work(openalex_id)
    source = _register_openalex_work(project, work)
    if source.openalex_retracted is True:
        return _present(source, download_status="RETRACTED_IN_OPENALEX")
    if source.verification_status == SourceDocument.Status.TEXT_CHECKED:
        return _present(source, download_status="ALREADY_EXTRACTED")
    if source.verification_status == SourceDocument.Status.OCR_REQUIRED:
        return _present(source, download_status="OCR_REQUIRED")
    if not source.pdf_url:
        return _present(source, download_status="NO_PDF_LINK")
    from thesis.services.document_jobs import enqueue_document_job
    job = enqueue_document_job(actor, project.id, source.id, "OPENALEX_PDF")
    return {**_present(source, download_status="PDF_QUEUED"), "job": job}


def import_openalex_source(actor, project_id, openalex_id: str) -> dict:
    project = require_project(actor, project_id)
    work = get_work(openalex_id)
    source = _register_openalex_work(project, work)
    if source.openalex_retracted is True:
        return _present(source, download_status="RETRACTED_IN_OPENALEX")
    if source.verification_status == SourceDocument.Status.TEXT_CHECKED:
        return _present(source, download_status="ALREADY_EXTRACTED")
    if source.verification_status == SourceDocument.Status.OCR_REQUIRED:
        return _present(source, download_status="OCR_REQUIRED")
    if not source.pdf_url:
        return _present(source, download_status="NO_PDF_LINK")

    root = Path(settings.MEDIA_ROOT)
    destination = root / "sources" / str(project.id) / f"{source.id}.pdf"
    temp = destination.with_name(f"{source.id}.{uuid.uuid4().hex}.part")
    temp.parent.mkdir(parents=True, exist_ok=True)
    try:
        digest = download_pdf(source.pdf_url, temp)
        count, pages = extract_pages(temp)
        if not pages:
            return _present(source, download_status="PDF_WITHOUT_EXTRACTABLE_TEXT")
        duplicate = SourceDocument.objects.filter(project=project, sha256=digest).exclude(pk=source.pk).first()
        if duplicate:
            return _present(source, download_status=f"DUPLICATE_PDF:{duplicate.id}")
        chunks = _excerpt_rows(source, pages)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp.replace(destination)
        with transaction.atomic():
            source.storage_key = str(destination.relative_to(root))
            source.sha256 = digest
            source.mime_type = "application/pdf"
            source.page_count = count
            source.verification_status = SourceDocument.Status.TEXT_CHECKED
            source.extraction_state = SourceDocument.ExtractionState.EXTRACTED
            source.extraction_method = SourceDocument.ExtractionMethod.POPPLER
            source.extraction_details_json = {
                "parser": "Poppler", "pages_with_digital_text": [page for page, _ in pages],
                "physical_page_count": count, "ocr_required_pages": count - len(pages),
                "selective_ocr": len(pages) < count, "original_preserved": True,
            }
            if len(pages) < count:
                source.verification_status = SourceDocument.Status.OCR_REQUIRED
                source.extraction_state = SourceDocument.ExtractionState.OCR_REQUIRED
            source.save(update_fields=["storage_key", "sha256", "mime_type", "page_count", "verification_status",
                                       "extraction_method", "extraction_state", "extraction_details_json"])
            source.excerpts.all().delete()
            SourceExcerpt.objects.bulk_create(chunks)
        return _present(source, download_status="OCR_REQUIRED" if source.verification_status == SourceDocument.Status.OCR_REQUIRED else "PDF_EXTRACTED")
    except DomainError as exc:
        return _present(source, download_status=f"{exc.code}: {exc.message}")
    finally:
        temp.unlink(missing_ok=True)


def upload_source_pending(actor, project_id, label: str, uploaded_file) -> dict:
    """Conserva un PDF/DOCX/PPTX/XLSX original; extracción estructural va al worker."""
    project = require_project(actor, project_id, owner_only=True)
    label = label.strip()
    if not label or len(label) > 300:
        raise DomainError("VALIDATION_ERROR", "La etiqueta debe tener entre 1 y 300 caracteres")
    filename = Path(getattr(uploaded_file, "name", "")).name
    extension = Path(filename).suffix.lower()
    mime_by_extension = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    if extension not in mime_by_extension:
        raise DomainError("UNSUPPORTED_FORMAT", "Solo se admiten archivos PDF, DOCX, PPTX y XLSX")
    job_kind = DocumentJob.Kind.PDF_EXTRACT if extension == ".pdf" else DocumentJob.Kind.FORMAT_EXTRACT
    root = Path(settings.MEDIA_ROOT)
    folder = root / "sources" / str(project.id)
    folder.mkdir(parents=True, exist_ok=True)
    temp = folder / f"upload-{uuid.uuid4().hex}.part"
    digest = hashlib.sha256()
    size = 0
    try:
        with temp.open("wb") as output:
            for chunk in uploaded_file.chunks():
                size += len(chunk)
                if size > MAX_PDF_BYTES:
                    raise DomainError("VALIDATION_ERROR", "El archivo supera el límite local de carga de 30 MB")
                output.write(chunk)
                digest.update(chunk)
        with temp.open("rb") as saved:
            header = saved.read(5)
        if extension == ".pdf" and header != b"%PDF-":
            raise DomainError("VALIDATION_ERROR", "El archivo no tiene cabecera PDF")
        if extension != ".pdf" and header[:2] != b"PK":
            raise DomainError("INVALID_DOCUMENT", "El archivo Office debe ser un paquete OOXML ZIP")
        duplicate = SourceDocument.objects.filter(project=project, sha256=digest.hexdigest()).first()
        if duplicate:
            result = _present(duplicate)
            if duplicate.verification_status == SourceDocument.Status.PENDING_EXTRACTION:
                from thesis.services.document_jobs import enqueue_document_job
                result["job"] = enqueue_document_job(actor, project.id, duplicate.id, job_kind)
                result["upload_status"] = "PDF_QUEUED" if extension == ".pdf" else "EXTRACTION_QUEUED"
            else:
                result["upload_status"] = "DUPLICATE_FILE"
            return result
        source = SourceDocument(project=project, kind=SourceDocument.Kind.UPLOAD, record_provider="",
                                metadata_origin=SourceDocument.MetadataOrigin.USER_UPLOADED_FILE, title=label,
                                authors_json=[], storage_key="", sha256=digest.hexdigest(),
                                original_filename=filename,
                                mime_type=mime_by_extension[extension], verification_status=SourceDocument.Status.PENDING_EXTRACTION,
                                extraction_state="QUEUED")
        destination = folder / f"{source.id}{extension}"
        source.storage_key = str(destination.relative_to(root))
        temp.replace(destination)
        try:
            with transaction.atomic():
                source.save()
                from thesis.services.document_jobs import enqueue_document_job
                job = enqueue_document_job(actor, project.id, source.id, job_kind)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return {**_present(source),
                "upload_status": "PDF_QUEUED" if extension == ".pdf" else "EXTRACTION_QUEUED",
                "job": job}
    finally:
        temp.unlink(missing_ok=True)


def upload_pdf_pending(actor, project_id, label: str, uploaded_file) -> dict:
    """Compatibilidad del nombre histórico; ahora el endpoint admite los cuatro formatos."""
    return upload_source_pending(actor, project_id, label, uploaded_file)


def extract_pending_pdf(actor, project_id, source_id) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    source = SourceDocument.objects.filter(project=project, pk=source_id).first()
    if source is None:
        raise DomainError("NOT_FOUND", "Fuente no encontrada")
    if source.verification_status != SourceDocument.Status.PENDING_EXTRACTION:
        raise DomainError("VERSION_CONFLICT", "El PDF ya fue procesado")
    root = Path(settings.MEDIA_ROOT).resolve()
    path = (root / source.storage_key).resolve()
    if not path.is_relative_to(root) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != source.sha256:
        raise DomainError("PDF_UNREADABLE", "El PDF original no está disponible o cambió")
    count, pages = extract_pages(path)
    chunks = _excerpt_rows(source, pages)
    with transaction.atomic():
        source = SourceDocument.objects.select_for_update().get(pk=source.pk)
        if source.verification_status != SourceDocument.Status.PENDING_EXTRACTION:
            raise DomainError("VERSION_CONFLICT", "El PDF ya fue procesado")
        source.page_count = count
        needs_ocr = len(pages) < count
        source.verification_status = (SourceDocument.Status.OCR_REQUIRED if needs_ocr
                                      else SourceDocument.Status.TEXT_CHECKED)
        source.extraction_state = (SourceDocument.ExtractionState.OCR_REQUIRED if needs_ocr
                                   else SourceDocument.ExtractionState.EXTRACTED)
        source.extraction_method = SourceDocument.ExtractionMethod.POPPLER if pages else None
        source.extraction_details_json = {
            "parser": "Poppler", "pages_with_digital_text": [page for page, _ in pages],
            "physical_page_count": count, "ocr_required_pages": count - len(pages),
            "selective_ocr": needs_ocr, "original_preserved": True,
        }
        source.save(update_fields=["page_count", "verification_status", "extraction_method", "extraction_state",
                                   "extraction_details_json"])
        SourceExcerpt.objects.bulk_create(chunks)
    return {**_present(source), "upload_status": "OCR_REQUIRED" if needs_ocr else "PDF_EXTRACTED"}


def process_source_ocr(actor, project_id, source_id) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    source = SourceDocument.objects.filter(project=project, pk=source_id).first()
    if source is None:
        raise DomainError("NOT_FOUND", "Fuente no encontrada")
    if source.verification_status != SourceDocument.Status.OCR_REQUIRED or not source.storage_key:
        raise DomainError("VALIDATION_ERROR", "La fuente no está pendiente de OCR")

    root = Path(settings.MEDIA_ROOT).resolve()
    original = (root / source.storage_key).resolve()
    if not original.is_relative_to(root) or not original.is_file():
        raise DomainError("PDF_UNREADABLE", "El PDF original no está disponible")
    if hashlib.sha256(original.read_bytes()).hexdigest() != source.sha256:
        raise DomainError("PDF_UNREADABLE", "El PDF original no coincide con su hash registrado")

    destination = original.with_suffix(".ocr.pdf")
    temp = destination.with_name(f"{source.id}.{uuid.uuid4().hex}.ocr.part.pdf")
    placed = False
    try:
        create_searchable_pdf(original, temp)
        count, pages = extract_pages(temp)
        if count != source.page_count:
            raise DomainError("OCR_FAILED", "El OCR no conservó el número de páginas del original")
        digest = hashlib.sha256(temp.read_bytes()).hexdigest()
        with transaction.atomic():
            source = SourceDocument.objects.select_for_update().get(pk=source.pk)
            if source.verification_status != SourceDocument.Status.OCR_REQUIRED:
                raise DomainError("VERSION_CONFLICT", "La fuente ya fue procesada por otro trabajo")
            temp.replace(destination)
            placed = True
            source.derived_storage_key = str(destination.relative_to(root))
            source.derived_sha256 = digest
            source.extraction_method = SourceDocument.ExtractionMethod.OCR
            source.verification_status = (SourceDocument.Status.TEXT_CHECKED if len(pages) == count
                                          else SourceDocument.Status.OCR_REQUIRED)
            source.extraction_state = (SourceDocument.ExtractionState.EXTRACTED if len(pages) == count
                                       else SourceDocument.ExtractionState.PARTIAL)
            source.extraction_details_json = {
                **source.extraction_details_json,
                "pages_with_text_after_ocr": [page for page, _ in pages],
                "pages_with_text_after_ocr_count": len(pages), "ocr_complete_by_page": len(pages) == count,
                "selective_ocr": True,
            }
            source.save(update_fields=["derived_storage_key", "derived_sha256", "extraction_method",
                                       "verification_status", "extraction_state", "extraction_details_json"])
            source.excerpts.all().delete()
            SourceExcerpt.objects.bulk_create(_excerpt_rows(source, pages))
        source.refresh_from_db()
        return _present(source, download_status="OCR_EXTRACTED" if source.verification_status == SourceDocument.Status.TEXT_CHECKED else "OCR_PARTIAL")
    except Exception:
        if placed:
            destination.unlink(missing_ok=True)
        raise
    finally:
        temp.unlink(missing_ok=True)


def list_sources(actor, project_id) -> list[dict]:
    project = require_project(actor, project_id)
    return [_present(source) for source in SourceDocument.objects.filter(project=project).order_by("-created_at")]


def list_excerpts(actor, project_id, source_id, *, page_no: int | None = None, limit: int = 20) -> dict:
    project = require_project(actor, project_id)
    source = SourceDocument.objects.filter(project=project, pk=source_id).first()
    if source is None:
        raise DomainError("NOT_FOUND", "Fuente no encontrada")
    if source.verification_status == SourceDocument.Status.REJECTED:
        return {"source": _present(source), "excerpts": []}
    if not 1 <= limit <= 50 or (page_no is not None and page_no < 1):
        raise DomainError("VALIDATION_ERROR", "Página o límite inválido")
    query = source.excerpts.order_by("chunk_no")
    if page_no is not None:
        query = query.filter(page_no=page_no)
    return {
        "source": _present(source),
        "excerpts": [{
            "excerpt_id": excerpt.id, "physical_page": excerpt.page_no,
            "text": excerpt.text, "text_sha256": excerpt.text_sha256,
        } for excerpt in query[:limit]],
    }


def extract_pending_multiformat(actor, project_id, source_id) -> dict:
    """Extrae estructuras Office conservando original/hash y localizadores nativos."""
    project = require_project(actor, project_id, owner_only=True)
    source = SourceDocument.objects.filter(project=project, pk=source_id).first()
    if source is None:
        raise DomainError("NOT_FOUND", "Fuente no encontrada")
    if source.kind != SourceDocument.Kind.UPLOAD or source.verification_status != SourceDocument.Status.PENDING_EXTRACTION:
        raise DomainError("VERSION_CONFLICT", "La fuente no está pendiente de extracción")
    root = Path(settings.MEDIA_ROOT).resolve()
    original = (root / source.storage_key).resolve()
    if not original.is_relative_to(root) or not original.is_file():
        raise DomainError("DOCUMENT_UNREADABLE", "El archivo original no está disponible")
    if hashlib.sha256(original.read_bytes()).hexdigest() != source.sha256:
        raise DomainError("DOCUMENT_UNREADABLE", "El archivo original no coincide con su hash registrado")
    from thesis.integrations.multiformat import extract_office
    extension = original.suffix.lower()
    segments, details = extract_office(original, extension)
    method_by_extension = {
        ".docx": SourceDocument.ExtractionMethod.PYTHON_DOCX,
        ".pptx": SourceDocument.ExtractionMethod.PYTHON_PPTX,
        ".xlsx": SourceDocument.ExtractionMethod.OPENPYXL,
    }
    digest = source.sha256
    rows = [SourceSegment(source=source, **segment) for segment in segments]
    with transaction.atomic():
        source = SourceDocument.objects.select_for_update().get(pk=source.pk)
        if source.verification_status != SourceDocument.Status.PENDING_EXTRACTION:
            raise DomainError("VERSION_CONFLICT", "La fuente ya fue procesada por otro trabajo")
        source.verification_status = SourceDocument.Status.TEXT_CHECKED
        source.extraction_state = details["extraction_state"]
        source.extraction_method = method_by_extension[extension]
        source.extraction_details_json = {**details, "input_sha256": digest,
                                          "original_preserved": True,
                                          "claims_verified": False}
        source.save(update_fields=["verification_status", "extraction_state", "extraction_method",
                                   "extraction_details_json"])
        source.segments.all().delete()
        SourceSegment.objects.bulk_create(rows, batch_size=500)
    return {**_present(source), "upload_status": details["extraction_state"],
            "segment_count": len(rows), "extraction_details": source.extraction_details_json}


def list_source_segments(actor, project_id, source_id, *, offset: int = 0, limit: int = 50) -> dict:
    project = require_project(actor, project_id)
    source = SourceDocument.objects.filter(project=project, pk=source_id).first()
    if source is None:
        raise DomainError("NOT_FOUND", "Fuente no encontrada")
    if not 0 <= offset <= 100_000 or not 1 <= limit <= 100:
        raise DomainError("VALIDATION_ERROR", "Offset o límite inválido")
    query = source.segments.order_by("sequence_no")
    total = query.count()
    return {"source": _present(source), "offset": offset, "limit": limit,
            "total": total, "segments": [{
                "segment_id": item.id, "sequence_no": item.sequence_no,
                "kind": item.kind, "locator": item.locator_json,
                "text": item.text, "text_sha256": item.text_sha256,
                "extraction_method": item.extraction_method,
                "extraction_version": item.extraction_version,
                "metadata": item.metadata_json,
            } for item in query[offset:offset + limit]]}
