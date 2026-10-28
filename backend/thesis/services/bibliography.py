"""Importación trazable de registros bibliográficos exportados por el usuario."""

import hashlib
from pathlib import Path
from uuid import UUID

from django.db import transaction

from thesis.integrations.bibliography_import import MAX_IMPORT_BYTES, parse_bibliography
from thesis.models import SearchExecution, SearchExecutionSource, SourceDocument
from thesis.services.access import require_project
from thesis.services.errors import DomainError
from thesis.services.source_duplicates import candidate_duplicates


PROVIDER_MAP = {
    "SCOPUS": SourceDocument.RecordProvider.SCOPUS,
    "WOS": SourceDocument.RecordProvider.WEB_OF_SCIENCE,
    "WEB_OF_SCIENCE": SourceDocument.RecordProvider.WEB_OF_SCIENCE,
    "OTHER": SourceDocument.RecordProvider.OTHER,
}


def import_bibliography(actor, project_id, uploaded_file, provider: str, execution_id=None) -> dict:
    """Importa metadatos sin descargar PDFs ni afirmar validación bibliográfica."""
    project = require_project(actor, project_id, owner_only=True)
    execution = None
    if execution_id:
        try:
            execution_uuid = UUID(str(execution_id))
        except (TypeError, ValueError) as exc:
            raise DomainError("VALIDATION_ERROR", "execution_id debe ser UUID") from exc
        execution = SearchExecution.objects.filter(
            pk=execution_uuid, strategy__project=project,
        ).select_related("strategy").first()
        if execution is None:
            raise DomainError("NOT_FOUND", "Ejecución manual no encontrada en este proyecto")
    provider_key = provider.strip().upper().replace(" ", "_")
    record_provider = PROVIDER_MAP.get(provider_key)
    if record_provider is None:
        raise DomainError("VALIDATION_ERROR", "provider debe ser SCOPUS, WOS o OTHER")
    filename = Path(getattr(uploaded_file, "name", "")).name
    extension = Path(filename).suffix.lower().lstrip(".")
    if not extension:
        raise DomainError("VALIDATION_ERROR", "El archivo necesita extensión .ris, .bib, .bibtex o .csv")
    content = uploaded_file.read(MAX_IMPORT_BYTES + 1)
    if len(content) > MAX_IMPORT_BYTES:
        raise DomainError("VALIDATION_ERROR", "El archivo excede el límite de 5 MiB")
    rows = parse_bibliography(content, extension)
    if not rows:
        raise DomainError("VALIDATION_ERROR", "No se encontraron registros bibliográficos con título")
    file_sha256 = hashlib.sha256(content).hexdigest()
    imported = []
    already_present = 0
    duplicate_candidates = 0
    linked_sources = 0
    with transaction.atomic():
        for row_no, row in enumerate(rows, start=1):
            record_id = row["record_id"] or f"{file_sha256}:{row_no}"
            duplicate_rows = candidate_duplicates(
                project, title=row["title"], doi=row.get("doi"),
                record_provider=record_provider, provider_record_id=record_id,
            )
            duplicate_candidates += bool(duplicate_rows)
            source, created = SourceDocument.objects.get_or_create(
                project=project,
                record_provider=record_provider,
                provider_record_id=record_id,
                defaults={
                    "kind": SourceDocument.Kind.EXTERNAL,
                    "imported_file_sha256": file_sha256,
                    "imported_by": actor,
                    "metadata_origin": SourceDocument.MetadataOrigin.USER_FILE_IMPORT,
                    "title": row["title"],
                    "authors_json": row["authors"],
                    "publication_year": row["year"],
                    "doi": row["doi"],
                    "url": row["url"],
                    "abstract": row["abstract"],
                    "publication_venue": row["venue"],
                    "verification_status": SourceDocument.Status.UNVERIFIED_METADATA,
                },
            )
            if not created:
                already_present += 1
            if execution:
                _, link_created = SearchExecutionSource.objects.get_or_create(
                    execution=execution, source=source,
                    link_kind=SearchExecutionSource.LinkKind.BIBLIOGRAPHY_IMPORT,
                    imported_file_sha256=file_sha256,
                    defaults={"created_by": actor},
                )
                linked_sources += int(link_created)
            imported.append({
                "source_id": str(source.id),
                "created": created,
                "title": source.title,
                "provider_record_id": source.provider_record_id,
                "possible_duplicates": duplicate_rows,
                "verification_level": "IMPORTED_METADATA_UNVERIFIED",
                "full_text_inspected": False,
            })
    return {
        "project_id": str(project.id),
        "provider": record_provider,
        "filename": filename,
        "file_sha256": file_sha256,
        "records_seen": len(rows),
        "records_created": len(rows) - already_present,
        "records_already_imported": already_present,
        "records_with_possible_duplicates": duplicate_candidates,
        "search_execution_id": str(execution.id) if execution else None,
        "sources_linked_to_execution": linked_sources,
        "results": imported,
        "notice": "El usuario exportó/importó estos metadatos. TesisMCP no ejecutó la búsqueda en la base ni inspeccionó los textos completos.",
    }
