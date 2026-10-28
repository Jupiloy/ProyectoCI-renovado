"""Registro trazable de resultados que el usuario selecciona en una búsqueda abierta."""

import re
from urllib.parse import urlsplit
from uuid import UUID

from django.db import IntegrityError, transaction

from thesis.models import SearchExecution, SearchExecutionSource, SourceDocument
from thesis.services.access import require_project
from thesis.services.errors import DomainError
from thesis.services.source_duplicates import candidate_duplicates
from thesis.services.sources import _present


DISCOVERY_PROVIDERS = {
    "OPENALEX": SourceDocument.RecordProvider.OPENALEX,
    "SEMANTIC_SCHOLAR": SourceDocument.RecordProvider.SEMANTIC_SCHOLAR,
    "ALICIA": SourceDocument.RecordProvider.ALICIA,
}


def _https_url(value: str | None, field: str) -> str | None:
    value = str(value or "").strip()
    if not value:
        return None
    if len(value) > 2048:
        raise DomainError("VALIDATION_ERROR", f"{field} supera 2048 caracteres")
    parsed = urlsplit(value)
    try:
        parsed.port
    except ValueError as exc:
        raise DomainError("VALIDATION_ERROR", f"{field} contiene un puerto no válido") from exc
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or any(c.isspace() for c in value):
        raise DomainError("VALIDATION_ERROR", f"{field} debe ser un enlace HTTPS válido")
    return value


def _candidate_payload(payload: dict) -> dict:
    provider_key = str(payload.get("provider", "")).strip().upper()
    provider = DISCOVERY_PROVIDERS.get(provider_key)
    if provider is None:
        raise DomainError("VALIDATION_ERROR", "provider debe ser OPENALEX, SEMANTIC_SCHOLAR o ALICIA")
    record_id = str(payload.get("provider_record_id", "")).strip()
    if not record_id or len(record_id) > 512 or any(ord(char) < 32 for char in record_id):
        raise DomainError("VALIDATION_ERROR", "provider_record_id está vacío o excede 512 caracteres")
    if provider == SourceDocument.RecordProvider.OPENALEX:
        match = re.fullmatch(r"(?:https://openalex\.org/)?(W[1-9][0-9]*)", record_id)
        if not match:
            raise DomainError("VALIDATION_ERROR", "provider_record_id no es un identificador OpenAlex válido")
        record_id = match.group(1)
        openalex_id = f"https://openalex.org/{record_id}"
    elif provider == SourceDocument.RecordProvider.SEMANTIC_SCHOLAR:
        if not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", record_id):
            raise DomainError("VALIDATION_ERROR", "provider_record_id no es un identificador Semantic Scholar válido")
        openalex_id = None
    else:
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,512}", record_id):
            raise DomainError("VALIDATION_ERROR", "provider_record_id de ALICIA contiene caracteres no válidos")
        openalex_id = None

    title = str(payload.get("title", "")).strip()
    if not title or len(title) > 2000:
        raise DomainError("VALIDATION_ERROR", "title debe tener entre 1 y 2000 caracteres")
    authors = payload.get("authors", [])
    if not isinstance(authors, list) or len(authors) > 100 or any(
        not isinstance(author, str) or not author.strip() or len(author.strip()) > 300 for author in authors
    ):
        raise DomainError("VALIDATION_ERROR", "authors debe ser una lista de hasta 100 nombres válidos")
    year = payload.get("publication_year")
    if year is not None and (isinstance(year, bool) or not isinstance(year, int) or not 1000 <= year <= 9999):
        raise DomainError("VALIDATION_ERROR", "publication_year debe ser un año de cuatro cifras")
    doi = str(payload.get("doi") or "").strip() or None
    abstract = str(payload.get("abstract") or "").strip()
    venue = str(payload.get("publication_venue") or "").strip()
    if doi and len(doi) > 255:
        raise DomainError("VALIDATION_ERROR", "doi supera 255 caracteres")
    if len(abstract) > 50_000 or len(venue) > 2_000:
        raise DomainError("VALIDATION_ERROR", "abstract o publication_venue exceden el límite permitido")

    return {
        "provider": provider,
        "provider_record_id": record_id,
        "openalex_id": openalex_id,
        "title": title,
        "authors_json": [author.strip() for author in authors],
        "publication_year": year,
        "doi": doi,
        "abstract": abstract,
        "publication_venue": venue,
        "url": _https_url(payload.get("record_url"), "record_url"),
        "pdf_url": _https_url(payload.get("pdf_url"), "pdf_url"),
    }


def _execution_for_project(project, execution_id):
    if not execution_id:
        return None
    try:
        execution_uuid = UUID(str(execution_id))
    except (TypeError, ValueError) as exc:
        raise DomainError("VALIDATION_ERROR", "search_execution_id debe ser UUID") from exc
    execution = SearchExecution.objects.filter(pk=execution_uuid, strategy__project=project).first()
    if execution is None:
        raise DomainError("NOT_FOUND", "Ejecución manual no encontrada en este proyecto")
    return execution


def select_discovery_candidate(actor, project_id, payload: dict) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    normalized = _candidate_payload(payload)
    execution = _execution_for_project(project, payload.get("search_execution_id"))
    with transaction.atomic():
        query = SourceDocument.objects.select_for_update().filter(
            project=project, record_provider=normalized["provider"],
            provider_record_id=normalized["provider_record_id"], kind=SourceDocument.Kind.EXTERNAL,
        )
        source = query.first()
        created = False
        if source is None:
            try:
                source = SourceDocument.objects.create(
                    project=project, kind=SourceDocument.Kind.EXTERNAL,
                    metadata_origin=SourceDocument.MetadataOrigin.USER_SELECTED_CANDIDATE,
                    record_provider=normalized["provider"], provider_record_id=normalized["provider_record_id"],
                    openalex_id=normalized["openalex_id"], title=normalized["title"],
                    authors_json=normalized["authors_json"], publication_year=normalized["publication_year"],
                    doi=normalized["doi"], abstract=normalized["abstract"],
                    publication_venue=normalized["publication_venue"], url=normalized["url"],
                    pdf_url=normalized["pdf_url"],
                    verification_status=SourceDocument.Status.UNVERIFIED_METADATA,
                )
                created = True
            except IntegrityError as exc:
                raise DomainError("IDEMPOTENCY_CONFLICT", "El registro ya se añadió concurrentemente al proyecto") from exc
        link_created = False
        if execution:
            _, link_created = SearchExecutionSource.objects.get_or_create(
                execution=execution, source=source,
                link_kind=SearchExecutionSource.LinkKind.DISCOVERY_SELECTION,
                imported_file_sha256="", defaults={"created_by": actor},
            )

    metadata_conflict = not created and any((
        source.title != normalized["title"],
        source.authors_json != normalized["authors_json"],
        source.publication_year != normalized["publication_year"],
        source.doi != normalized["doi"],
        source.abstract != normalized["abstract"],
        source.publication_venue != normalized["publication_venue"],
        source.url != normalized["url"],
        source.pdf_url != normalized["pdf_url"],
    ))

    possible_duplicates = candidate_duplicates(
        project, title=source.title, doi=source.doi,
        record_provider=source.record_provider, provider_record_id=source.provider_record_id,
    )
    return {
        **_present(source),
        "created": created,
        "metadata_origin": source.metadata_origin,
        "verification_level": "USER_SUPPLIED_METADATA_UNVERIFIED"
        if source.metadata_origin == SourceDocument.MetadataOrigin.USER_SELECTED_CANDIDATE
        else "METADATA_ONLY",
        "full_text_inspected": source.verification_status == SourceDocument.Status.TEXT_CHECKED,
        "metadata_conflict": metadata_conflict,
        "possible_duplicates": possible_duplicates,
        "search_execution_id": str(execution.id) if execution else None,
        "linked_to_execution": link_created,
        "notice": "El tesista seleccionó el registro y envió estos metadatos. No se cotejaron nuevamente con el proveedor ni se inspeccionó el texto completo.",
    }


def list_search_execution_sources(actor, project_id, strategy_id, execution_id) -> dict:
    project = require_project(actor, project_id)
    execution = SearchExecution.objects.filter(
        pk=execution_id, strategy_id=strategy_id, strategy__project=project,
    ).first()
    if execution is None:
        raise DomainError("NOT_FOUND", "Ejecución manual no encontrada en este proyecto")
    rows = SearchExecutionSource.objects.filter(execution=execution).select_related("source", "created_by") \
        .order_by("created_at", "id")
    return {
        "search_execution_id": str(execution.id),
        "strategy_id": str(execution.strategy_id),
        "sources": [
            {
                "link_id": str(link.id),
                "link_kind": link.link_kind,
                "imported_file_sha256": link.imported_file_sha256 or None,
                "created_by_id": link.created_by_id,
                "created_at": link.created_at.isoformat(),
                "source": _present(link.source),
            }
            for link in rows
        ],
    }
