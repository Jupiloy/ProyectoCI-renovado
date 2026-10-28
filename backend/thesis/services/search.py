"""Indexación y recuperación semántica de pasajes con página física."""

import hashlib

from django.db import transaction
from django.db.models import Q
from pgvector.django import CosineDistance

from thesis.integrations.embeddings import MODEL_NAME, embed_texts
from thesis.models import SourceDocument, SourcePassage
from thesis.services.access import require_project
from thesis.services.errors import DomainError


PASSAGE_CHARS = 500
MAX_PASSAGES_PER_SOURCE = 20000


def index_source_passages(actor, project_id, source_id) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    source = SourceDocument.objects.filter(project=project, pk=source_id).first()
    if source is None:
        raise DomainError("NOT_FOUND", "Fuente no encontrada")
    if source.verification_status != SourceDocument.Status.TEXT_CHECKED:
        raise DomainError("VALIDATION_ERROR", "La fuente aún no tiene texto extraído")
    pieces = []
    for excerpt in source.excerpts.order_by("chunk_no"):
        for start in range(0, len(excerpt.text), PASSAGE_CHARS):
            value = excerpt.text[start:start + PASSAGE_CHARS].strip()
            if value:
                pieces.append((excerpt, None, start, value))
                if len(pieces) > MAX_PASSAGES_PER_SOURCE:
                    raise DomainError("VALIDATION_ERROR", "La fuente supera el límite de pasajes para indexación")
    for segment in source.segments.exclude(text="").order_by("sequence_no"):
        for start in range(0, len(segment.text), PASSAGE_CHARS):
            value = segment.text[start:start + PASSAGE_CHARS].strip()
            if value:
                pieces.append((None, segment, start, value))
                if len(pieces) > MAX_PASSAGES_PER_SOURCE:
                    raise DomainError("VALIDATION_ERROR", "La fuente supera el límite de pasajes para indexación")
    if not pieces:
        raise DomainError("VALIDATION_ERROR", "La fuente no tiene pasajes para indexar")
    vectors = embed_texts([piece[3] for piece in pieces])
    rows = [SourcePassage(
        excerpt=excerpt, segment=segment, start_char=start, text=value,
        text_sha256=hashlib.sha256(value.encode("utf-8")).hexdigest(),
        embedding=vector, embedding_model=MODEL_NAME,
    ) for (excerpt, segment, start, value), vector in zip(pieces, vectors, strict=True)]
    with transaction.atomic():
        SourceDocument.objects.select_for_update().get(pk=source.pk)
        SourcePassage.objects.filter(Q(excerpt__source=source) | Q(segment__source=source)).delete()
        SourcePassage.objects.bulk_create(rows, batch_size=200)
    return {"source_id": str(source.id), "indexed_passages": len(rows),
            "embedding_model": MODEL_NAME, "index_status": "INDEXED",
            "scientific_claims_verified": False}


def search_passages(actor, project_id, query: str, *, limit: int = 5, source_ids=None) -> dict:
    project = require_project(actor, project_id)
    query = query.strip()
    if not query or len(query) > 500 or not 1 <= limit <= 20:
        raise DomainError("VALIDATION_ERROR", "Consulta o límite inválido")
    project_passages = SourcePassage.objects.filter(embedding_model=MODEL_NAME).filter(
        Q(excerpt__source__project=project) | Q(segment__source__project=project))
    if source_ids is not None:
        project_passages = project_passages.filter(
            Q(excerpt__source_id__in=source_ids) | Q(segment__source_id__in=source_ids))
    if not project_passages.exists():
        return {"query": query, "results": [], "search_status": "NO_INDEXED_PASSAGES"}
    vector = embed_texts([query])[0]
    matches = (project_passages.select_related("excerpt__source", "segment__source")
               .annotate(distance=CosineDistance("embedding", vector))
               .order_by("distance", "pk")[:limit])
    return {"query": query, "search_status": "CANDIDATES_ONLY", "results": [{
        "source_id": str(item.excerpt.source_id if item.excerpt_id else item.segment.source_id), "passage_id": item.id,
        "excerpt_id": item.excerpt_id, "segment_id": item.segment_id,
        "physical_page": item.excerpt.page_no if item.excerpt_id else None,
        "locator": ({"physical_page": item.excerpt.page_no} if item.excerpt_id
                    else item.segment.locator_json),
        "locator_kind": "PDF_PAGE" if item.excerpt_id else item.segment.kind,
        "start_char": item.start_char, "text": item.text, "text_sha256": item.text_sha256,
        "cosine_distance": item.distance, "embedding_model": item.embedding_model,
        "supports_claim_verified": False,
    } for item in matches]}
