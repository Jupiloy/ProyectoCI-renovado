"""Análisis bibliográfico opcional de PDFs ya incorporados."""

import hashlib
from pathlib import Path

from django.conf import settings
from django.db import transaction

from thesis.integrations.grobid import parse_tei, process_fulltext
from thesis.models import SourceDocument, SourceGrobidAnalysis
from thesis.services.access import require_project
from thesis.services.errors import DomainError


def _source(actor, project_id, source_id, *, owner_only=False):
    project = require_project(actor, project_id, owner_only=owner_only)
    source = SourceDocument.objects.filter(project=project, pk=source_id).first()
    if source is None:
        raise DomainError("NOT_FOUND", "Fuente no encontrada")
    return source


def _present(analysis: SourceGrobidAnalysis, *, offset=0, limit=20) -> dict:
    references = analysis.references_json
    return {
        "source_id": str(analysis.source_id), "input_sha256": analysis.input_sha256,
        "tei_sha256": analysis.tei_sha256,
        "extracted_title": analysis.extracted_title,
        "extracted_authors": analysis.extracted_authors_json,
        "reference_count": len(references), "reference_offset": offset,
        "references": references[offset:offset + limit],
        "verification_level": "MACHINE_EXTRACTED_UNVERIFIED",
        "cover_metadata_verified": False, "references_verified": False,
    }


def analyze_source_grobid(actor, project_id, source_id) -> dict:
    source = _source(actor, project_id, source_id, owner_only=True)
    if source.verification_status != SourceDocument.Status.TEXT_CHECKED or not source.storage_key:
        raise DomainError("VALIDATION_ERROR", "La fuente requiere un PDF con texto antes del análisis GROBID")
    root = Path(settings.MEDIA_ROOT).resolve()
    storage_key = source.derived_storage_key or source.storage_key
    expected_sha = source.derived_sha256 or source.sha256
    path = (root / storage_key).resolve()
    if not path.is_relative_to(root) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
        raise DomainError("PDF_UNREADABLE", "El PDF no está disponible o no coincide con su hash")
    existing = SourceGrobidAnalysis.objects.filter(source=source, input_sha256=expected_sha).first()
    if existing:
        return {**_present(existing), "analysis_status": "ALREADY_ANALYZED"}
    tei = process_fulltext(path)
    parsed = parse_tei(tei)
    try:
        xml = tei.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DomainError("GROBID_FAILED", "GROBID devolvió TEI con codificación inválida") from exc
    with transaction.atomic():
        analysis, _ = SourceGrobidAnalysis.objects.update_or_create(
            source=source,
            defaults={"input_sha256": expected_sha, "tei_sha256": hashlib.sha256(tei).hexdigest(),
                      "tei_xml": xml, "extracted_title": parsed["title"],
                      "extracted_authors_json": parsed["authors"], "references_json": parsed["references"]},
        )
    return {**_present(analysis), "analysis_status": "ANALYZED"}


def get_source_grobid(actor, project_id, source_id, *, offset=0, limit=20) -> dict:
    if offset < 0 or not 1 <= limit <= 50:
        raise DomainError("VALIDATION_ERROR", "Offset o límite inválido")
    source = _source(actor, project_id, source_id)
    analysis = SourceGrobidAnalysis.objects.filter(source=source).first()
    if analysis is None:
        raise DomainError("NOT_FOUND", "Esta fuente aún no tiene análisis GROBID")
    return _present(analysis, offset=offset, limit=limit)
