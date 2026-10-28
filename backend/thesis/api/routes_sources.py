"""Rutas de sources; registradas en el router compartido."""

from uuid import UUID
from ninja import File, Form, Status, UploadedFile
from thesis.services.sources import enqueue_openalex_source, list_excerpts, list_source_segments, list_sources, upload_source_pending
from thesis.services.bibliography import import_bibliography
from thesis.services.discovery_sources import select_discovery_candidate
from thesis.services.source_duplicate_decisions import decide_source_duplicate, list_source_duplicate_decisions
from thesis.services.zotero import import_zotero_item, list_zotero_items
from .schemas import ImportSourceIn, SelectDiscoveryCandidateIn, SourceDuplicateDecisionIn, ZoteroImportIn
from .routers import router


@router.post("/{project_id}/sources", response={200: dict, 202: dict}, operation_id="thesis_api_projects_import_source")
def import_source(request, project_id: UUID, payload: ImportSourceIn):
    result = enqueue_openalex_source(request.user, project_id, payload.openalex_id)
    return Status(202, result) if "job" in result else result


@router.post("/{project_id}/sources/upload", response={200: dict, 202: dict}, operation_id="thesis_api_projects_upload_source")
def upload_source(request, project_id: UUID, label: Form[str], file: File[UploadedFile]):
    result = upload_source_pending(request.user, project_id, label, file)
    return Status(202, result) if result["verification_status"] == "PENDING_EXTRACTION" else result


@router.post("/{project_id}/sources/import-bibliography", operation_id="thesis_api_projects_import_bibliographic_file")
def import_bibliographic_file(request, project_id: UUID, provider: Form[str], file: File[UploadedFile],
                              execution_id: Form[str] = ""):
    return import_bibliography(request.user, project_id, file, provider, execution_id or None)


@router.get("/{project_id}/sources/zotero", operation_id="thesis_api_projects_zotero_library_items")
def zotero_library_items(request, project_id: UUID, query: str = "", start: int = 0, limit: int = 25):
    return list_zotero_items(request.user, project_id, query=query, start=start, limit=limit)


@router.post("/{project_id}/sources/import-zotero", operation_id="thesis_api_projects_import_zotero_bibliographic_item")
def import_zotero_bibliographic_item(request, project_id: UUID, payload: ZoteroImportIn):
    result = import_zotero_item(request.user, project_id, payload.item_key)
    return Status(201, result) if result["created"] else result


@router.post("/{project_id}/sources/select-discovery", response={201: dict, 200: dict}, operation_id="thesis_api_projects_select_discovered_source")
def select_discovered_source(request, project_id: UUID, payload: SelectDiscoveryCandidateIn):
    result = select_discovery_candidate(request.user, project_id, payload.dict())
    return Status(201, result) if result["created"] else result


@router.post("/{project_id}/sources/duplicate-decisions", response={201: dict, 200: dict}, operation_id="thesis_api_projects_source_duplicate_decision")
def source_duplicate_decision(request, project_id: UUID, payload: SourceDuplicateDecisionIn):
    result = decide_source_duplicate(
        request.user, project_id, payload.source_id, payload.other_source_id,
        payload.decision, payload.note, payload.idempotency_key, payload.primary_source_id,
    )
    return Status(201, result) if result["created"] else result


@router.get("/{project_id}/sources/duplicate-decisions", operation_id="thesis_api_projects_source_duplicate_decisions")
def source_duplicate_decisions(request, project_id: UUID):
    return list_source_duplicate_decisions(request.user, project_id)


@router.get("/{project_id}/sources", operation_id="thesis_api_projects_sources")
def sources(request, project_id: UUID):
    return list_sources(request.user, project_id)


@router.get("/{project_id}/sources/{source_id}/excerpts", operation_id="thesis_api_projects_excerpts")
def excerpts(request, project_id: UUID, source_id: UUID, page_no: int | None = None, limit: int = 20):
    return list_excerpts(request.user, project_id, source_id, page_no=page_no, limit=limit)


@router.get("/{project_id}/sources/{source_id}/segments", operation_id="thesis_api_projects_source_segments")
def source_segments(request, project_id: UUID, source_id: UUID, offset: int = 0, limit: int = 50):
    return list_source_segments(request.user, project_id, source_id, offset=offset, limit=limit)
