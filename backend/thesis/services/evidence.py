"""Cotejos documentales conservadores, sin dictámenes científicos automáticos."""

import re

from rapidfuzz import fuzz

from thesis.integrations.crossref import get_doi_record
from thesis.models import SourceDocument, SourceExcerpt, SourceMetadataCheck
from thesis.services.access import require_project
from thesis.services.errors import DomainError


def _source(actor, project_id, source_id, *, owner_only=False):
    project = require_project(actor, project_id, owner_only=owner_only)
    source = SourceDocument.objects.filter(project=project, pk=source_id).first()
    if source is None:
        raise DomainError("NOT_FOUND", "Fuente no encontrada")
    return source


def check_source_doi(actor, project_id, source_id) -> dict:
    source = _source(actor, project_id, source_id, owner_only=True)
    if not source.doi:
        raise DomainError("VALIDATION_ERROR", "La fuente no tiene DOI declarado")
    record = get_doi_record(source.doi)
    title = (record.get("title") or [""])[0]
    authors = [" ".join(part for part in [item.get("given", ""), item.get("family", "")] if part)
               for item in record.get("author", []) if isinstance(item, dict)]
    title_similarity = None if source.kind == SourceDocument.Kind.UPLOAD else fuzz.ratio(
        source.title.casefold(), title.casefold())
    entry, _ = SourceMetadataCheck.objects.update_or_create(source=source, defaults={
        "doi": record["DOI"], "registered_title": title,
        "registered_authors_json": authors, "title_similarity": title_similarity,
        "registry_record_json": {"DOI": record["DOI"], "title": record.get("title", []),
                                 "author": record.get("author", []), "published": record.get("published"),
                                 "container-title": record.get("container-title", [])},
    })
    return present_metadata_check(entry)


def present_metadata_check(entry: SourceMetadataCheck) -> dict:
    return {"source_id": str(entry.source_id), "doi": entry.doi, "registry": entry.registry,
            "registered_title": entry.registered_title, "registered_authors": entry.registered_authors_json,
            "title_similarity_candidate": entry.title_similarity,
            "registry_record": entry.registry_record_json,
            "checked_at": entry.checked_at.isoformat(), "registry_record_found": True,
            "cover_metadata_verified": False, "scientific_claims_verified": False}


def get_source_metadata_check(actor, project_id, source_id) -> dict:
    source = _source(actor, project_id, source_id)
    entry = SourceMetadataCheck.objects.filter(source=source).first()
    if entry is None:
        raise DomainError("NOT_FOUND", "Aún no se ha cotejado el DOI")
    return present_metadata_check(entry)


def locate_quote(actor, project_id, source_id, quote: str, *, limit: int = 5) -> dict:
    source = _source(actor, project_id, source_id)
    quote = quote.strip()
    if source.verification_status != SourceDocument.Status.TEXT_CHECKED:
        raise DomainError("VALIDATION_ERROR", "La fuente no tiene texto extraído")
    if not 10 <= len(quote) <= 500 or not 1 <= limit <= 10:
        raise DomainError("VALIDATION_ERROR", "La cita debe tener entre 10 y 500 caracteres")
    matches = []
    for excerpt in SourceExcerpt.objects.filter(source=source).order_by("page_no", "chunk_no"):
        exact = re.search(re.escape(quote), excerpt.text, flags=re.IGNORECASE)
        if exact is not None:
            matches.append({"physical_page": excerpt.page_no, "excerpt_id": excerpt.pk,
                            "start_char": exact.start(), "end_char": exact.end(),
                            "matched_text": excerpt.text[exact.start():exact.end()],
                            "excerpt_sha256": excerpt.text_sha256, "match_type": "EXACT", "similarity": 100.0})
            continue
        # Solo propone frases realmente presentes en el texto extraído.
        spans = [(match.start(), match.end()) for match in re.finditer(r"[^.!?\n]+[.!?]?", excerpt.text)
                 if match.group().strip()]
        for start, end in spans:
            candidate = excerpt.text[start:end].strip()
            score = fuzz.ratio(quote.casefold(), candidate.casefold())
            if score >= 70:
                actual_start = excerpt.text.find(candidate, start, end)
                matches.append({"physical_page": excerpt.page_no, "excerpt_id": excerpt.pk,
                                "start_char": actual_start, "end_char": actual_start + len(candidate),
                                "matched_text": candidate, "excerpt_sha256": excerpt.text_sha256,
                                "match_type": "FUZZY_CANDIDATE", "similarity": round(score, 2)})
    matches.sort(key=lambda item: (item["match_type"] != "EXACT", -item["similarity"], item["physical_page"]))
    return {"source_id": str(source.id), "query": quote, "matches": matches[:limit],
            "full_text_inspected": True, "scientific_claims_verified": False,
            "note": "La coincidencia localiza texto extraído; requiere cotejo con el PDF físico"}
