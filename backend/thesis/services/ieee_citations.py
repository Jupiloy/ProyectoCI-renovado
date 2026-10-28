"""Renderización preliminar IEEE desde metadatos congelados en una revisión."""

from collections import OrderedDict

from thesis.models import ChapterCitationOccurrence, ChapterDocument
from thesis.services.access import require_project
from thesis.services.errors import DomainError


def _reference_text(number: int, reference: dict) -> tuple[str, list[str]]:
    authors = reference.get("authors")
    if not isinstance(authors, list):
        authors = []
    authors_text = ", ".join(str(author).strip() for author in authors if str(author).strip())
    title = str(reference.get("title") or "").strip()
    venue = str(reference.get("publication_venue") or "").strip()
    year = reference.get("publication_year")
    doi = str(reference.get("doi") or "").strip()
    url = str(reference.get("url") or "").strip()

    missing = []
    if not authors_text:
        missing.append("authors")
    if not title:
        missing.append("title")
    if not venue:
        missing.append("publication_venue")
    if not year:
        missing.append("publication_year")

    parts = [f"[{number}]"]
    if authors_text:
        parts.append(authors_text)
    if title:
        parts.append(f'"{title}"')
    if venue:
        parts.append(venue)
    if year:
        parts.append(str(year))
    if doi:
        parts.append(f"doi: {doi}")
    elif url:
        parts.append(url)
    return ", ".join(parts), missing


def build_ieee_citation_view(revision) -> dict:
    """Devuelve numeración por primera aparición y referencias con brechas de metadatos visibles."""
    rows = list(ChapterCitationOccurrence.objects.filter(document_revision=revision).order_by(
        "group_order", "source_order", "id",
    ))
    block_order = {
        block["id"]: index for index, block in enumerate(revision.content_tree.get("blocks", []))
    }
    grouped = OrderedDict()
    source_numbers = OrderedDict()
    frozen_references = {}
    for row in rows:
        group_key = (str(row.group_id), str(row.block_id), row.char_offset)
        group = grouped.setdefault(group_key, {
            "group_id": str(row.group_id), "block_id": str(row.block_id),
            "position": row.char_offset, "source_ids": [], "occurrence_ids": [], "numbers": [],
        })
        source_id = str(row.source_id)
        if source_id not in source_numbers:
            source_numbers[source_id] = len(source_numbers) + 1
            frozen_references[source_id] = row.reference_snapshot
        group["source_ids"].append(source_id)
        group["occurrence_ids"].append(str(row.id))
        group["numbers"].append(source_numbers[source_id])

    marks = list(grouped.values())
    marks.sort(key=lambda mark: (block_order.get(mark["block_id"], 1_000_000), mark["position"]))
    for mark in marks:
        mark["citation_text"] = ", ".join(f"[{number}]" for number in mark["numbers"])

    references = []
    for source_id, number in source_numbers.items():
        reference_text, missing = _reference_text(number, frozen_references[source_id])
        references.append({
            "number": number,
            "source_id": source_id,
            "reference": frozen_references[source_id],
            "reference_sha256": next(row.reference_sha256 for row in rows if str(row.source_id) == source_id),
            "ieee_text": reference_text,
            "status": "INCOMPLETE_METADATA" if missing else "METADATA_COMPLETE",
            "missing_fields": missing,
        })
    return {
        "style": "IEEE",
        "rendering_status": "PRELIMINARY_METADATA_FORMAT",
        "document_revision_id": str(revision.id),
        "document_revision_sha256": revision.content_sha256,
        "citation_manifest_sha256": revision.citation_manifest_sha256,
        "marks": marks,
        "references": references,
        "notice": "La numeración y el formato se generan desde metadatos congelados; revise el tipo documental y la referencia antes de entregar.",
    }


def get_current_ieee_citation_view(actor, project_id, chapter_no: int) -> dict:
    project = require_project(actor, project_id)
    document = ChapterDocument.objects.select_related("current_revision").filter(
        chapter__project=project, chapter__number=chapter_no,
    ).first()
    if not document or not document.current_revision:
        raise DomainError("NOT_FOUND", "No hay revisión canónica para este capítulo")
    return build_ieee_citation_view(document.current_revision)
