"""Presentación de datos de dominio; sin cambios de persistencia."""

from thesis.models import SourceDocument


def _present(source: SourceDocument, *, download_status: str | None = None) -> dict:
    result = {
        "source_id": str(source.id), "project_id": str(source.project_id),
        "kind": source.kind,
        "openalex_id": source.openalex_id,
        "record_provider": source.record_provider,
        "provider_record_id": source.provider_record_id,
        "imported_file_sha256": source.imported_file_sha256,
        "title": source.title if source.kind == SourceDocument.Kind.EXTERNAL else None,
        "abstract": source.abstract or None,
        "publication_venue": source.publication_venue or None,
        "display_label": source.title,
        "original_filename": source.original_filename or None,
        "metadata_origin": source.metadata_origin if source.kind == SourceDocument.Kind.EXTERNAL else source.metadata_origin,
        "title_verified_against_cover": False,
        "authors": source.authors_json if source.kind == SourceDocument.Kind.EXTERNAL else None,
        "publication_year": source.publication_year,
        "doi": source.doi,
        "authors_from_openalex": source.authors_json if source.record_provider == SourceDocument.RecordProvider.OPENALEX else None,
        "publication_year_from_openalex": source.publication_year if source.record_provider == SourceDocument.RecordProvider.OPENALEX else None,
        "doi_from_openalex": source.doi if source.record_provider == SourceDocument.RecordProvider.OPENALEX else None,
        "record_url": source.openalex_id or source.url,
        "landing_page_url": source.url, "pdf_url": source.pdf_url,
        "openalex_retracted": source.openalex_retracted,
        "verification_status": source.verification_status,
        "physical_page_count": source.page_count,
        "text_extraction_method": source.extraction_method,
        "extraction_state": source.extraction_state,
        "extraction_details": source.extraction_details_json,
        "ocr_derived_sha256": source.derived_sha256,
        "full_text_extracted": (source.verification_status == SourceDocument.Status.TEXT_CHECKED
                                and source.extraction_state not in {"NO_TEXT", "PARTIAL"}),
        "verification_level": (
            "USER_UPLOADED_DOCUMENT" if source.kind == SourceDocument.Kind.UPLOAD else
            "METADATA_ONLY" if source.metadata_origin == SourceDocument.MetadataOrigin.PROVIDER_API else
            "USER_SUPPLIED_METADATA_UNVERIFIED"
        ),
        "cover_metadata_verified": False,
        "scientific_claims_verified": False,
        "excerpt_count": source.excerpts.count(),
        "segment_count": source.segments.count(),
    }
    if download_status:
        result["download_status"] = download_status
    return result
