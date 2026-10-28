"""Validación, persistencia y lectura de marcas de cita para revisiones canónicas."""

import hashlib
import json
from collections import OrderedDict
from uuid import UUID

from thesis.models import ChapterCitationOccurrence, SourceDocument
from thesis.services.errors import DomainError


MAX_CITATION_GROUPS = 500
MAX_SOURCES_PER_GROUP = 20
MAX_CITATION_OCCURRENCES = 1000


def _uuid(value, field: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise DomainError("VALIDATION_ERROR", f"{field} debe ser UUID") from exc


def _hash(value: dict | list) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def frozen_reference(source: SourceDocument) -> dict:
    return {
        "source_id": str(source.id), "kind": source.kind, "title": source.title,
        "authors": source.authors_json, "publication_year": source.publication_year,
        "doi": source.doi, "publication_venue": source.publication_venue,
        "record_provider": source.record_provider, "provider_record_id": source.provider_record_id,
        "metadata_origin": source.metadata_origin, "verification_status": source.verification_status,
        "url": source.url, "sha256": source.sha256,
    }


def normalize_citation_marks(project, content_tree: dict, marks) -> tuple[list[dict], str]:
    if not isinstance(marks, list) or len(marks) > MAX_CITATION_GROUPS:
        raise DomainError("VALIDATION_ERROR", f"citations debe ser una lista de hasta {MAX_CITATION_GROUPS} grupos")
    paragraph_order = {UUID(block["id"]): index for index, block in enumerate(content_tree["blocks"])
                       if block["type"] == "paragraph"}
    paragraphs = {UUID(block["id"]): block["text"] for block in content_tree["blocks"]
                  if block["type"] == "paragraph"}
    normalized = []
    seen_groups = set()
    requested_source_ids = set()
    occurrence_count = 0
    for mark_index, mark in enumerate(marks):
        if not isinstance(mark, dict) or set(mark) != {"group_id", "block_id", "position", "sources"}:
            raise DomainError("VALIDATION_ERROR", "Cada cita requiere group_id, block_id, position y sources")
        group_id = _uuid(mark["group_id"], "group_id")
        block_id = _uuid(mark["block_id"], "block_id")
        position = mark["position"]
        sources = mark["sources"]
        if str(group_id) in seen_groups:
            raise DomainError("VALIDATION_ERROR", "group_id debe ser único dentro de la revisión")
        seen_groups.add(str(group_id))
        if block_id not in paragraphs:
            raise DomainError("VALIDATION_ERROR", "La cita debe anclarse a un bloque paragraph de la revisión")
        if type(position) is not int or position < 0 or position > len(paragraphs[block_id]):
            raise DomainError("VALIDATION_ERROR", "position debe ser un offset Unicode dentro del párrafo")
        if not isinstance(sources, list) or not 1 <= len(sources) <= MAX_SOURCES_PER_GROUP:
            raise DomainError("VALIDATION_ERROR", f"Cada cita debe tener entre 1 y {MAX_SOURCES_PER_GROUP} fuentes")
        rows = []
        seen_sources = set()
        for item in sources:
            if not isinstance(item, dict) or set(item) != {"source_id", "locator"}:
                raise DomainError("VALIDATION_ERROR", "Cada fuente citada requiere source_id y locator")
            source_id = _uuid(item["source_id"], "source_id")
            locator = item["locator"]
            if not isinstance(locator, str) or len(locator.strip()) > 200:
                raise DomainError("VALIDATION_ERROR", "locator debe ser texto de hasta 200 caracteres")
            if source_id in seen_sources:
                raise DomainError("VALIDATION_ERROR", "Una fuente no puede repetirse dentro del mismo grupo de cita")
            seen_sources.add(source_id)
            requested_source_ids.add(source_id)
            rows.append({"source_id": source_id, "locator": locator.strip()})
        occurrence_count += len(rows)
        normalized.append({"group_id": group_id, "block_id": block_id, "position": position,
                           "sources": rows, "input_order": mark_index})
    if occurrence_count > MAX_CITATION_OCCURRENCES:
        raise DomainError("VALIDATION_ERROR", f"Una revisión admite hasta {MAX_CITATION_OCCURRENCES} ocurrencias de fuente")

    sources = {source.id: source for source in SourceDocument.objects.filter(
        project=project, pk__in=requested_source_ids,
    )}
    if len(sources) != len(requested_source_ids):
        raise DomainError("NOT_FOUND", "Una o más fuentes citadas no pertenecen a este proyecto")

    normalized.sort(key=lambda mark: (paragraph_order[mark["block_id"]], mark["position"], mark["input_order"]))

    manifest = []
    for group_order, mark in enumerate(normalized, start=1):
        mark["group_order"] = group_order
        items = []
        for source_row in mark["sources"]:
            source = sources[source_row["source_id"]]
            reference_snapshot = frozen_reference(source)
            source_row["reference_snapshot"] = reference_snapshot
            source_row["reference_sha256"] = _hash(reference_snapshot)
            items.append({"source_id": str(source.id), "locator": source_row["locator"],
                          "reference_sha256": source_row["reference_sha256"]})
        manifest.append({"group_id": str(mark["group_id"]), "block_id": str(mark["block_id"]),
                         "position": mark["position"], "sources": items})
    return normalized, _hash(manifest)


def persist_citation_marks(revision, actor, marks: list[dict]) -> None:
    ChapterCitationOccurrence.objects.bulk_create([
        ChapterCitationOccurrence(
            document_revision=revision, group_id=mark["group_id"], group_order=mark["group_order"],
            block_id=mark["block_id"],
            char_offset=mark["position"], source_id=source_row["source_id"], source_order=index,
            locator=source_row["locator"], reference_snapshot=source_row["reference_snapshot"],
            reference_sha256=source_row["reference_sha256"], created_by=actor,
        )
        for mark in marks for index, source_row in enumerate(mark["sources"], start=1)
    ])


def list_citation_marks(revision) -> list[dict]:
    grouped = OrderedDict()
    rows = ChapterCitationOccurrence.objects.filter(document_revision=revision).order_by(
        "group_order", "source_order", "id",
    )
    for row in rows:
        group_key = (row.group_id, row.block_id, row.char_offset)
        mark = grouped.setdefault(group_key, {
            "group_id": str(row.group_id), "block_id": str(row.block_id), "position": row.char_offset,
            "sources": [],
        })
        mark["sources"].append({
            "source_id": str(row.source_id), "source_order": row.source_order,
            "locator": row.locator, "reference": row.reference_snapshot,
            "reference_sha256": row.reference_sha256,
        })
    return list(grouped.values())
