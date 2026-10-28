"""Servicio de búsqueda y clasificación de antecedentes científicos nacionales y locales (Perú)."""

from typing import Any

from thesis.integrations.alicia import search_alicia_theses
from thesis.integrations.peru_articles import search_peru_affiliated_articles
from thesis.models import ResearchProfile
from thesis.services.access import require_project
from thesis.services.errors import DomainError
from thesis.services.geography import GeographicScope, _contains_term, _strip_accents, resolve_geographic_scope


def _classify_locality(item: dict, scope: GeographicScope) -> tuple[bool, str]:
    """Evalúa de forma determinista si un registro califica como local y explica la razón."""
    title_clean = _strip_accents(item.get("title") or "")
    abstract_clean = _strip_accents(item.get("abstract") or "")
    combined_text = f"{title_clean} {abstract_clean}"

    # 1. Comprobar si la institución es una universidad local de la zona (por acrónimo o nombre de región)
    inst_clean = _strip_accents(item.get("institution") or "")
    region_clean = _strip_accents(scope.region)
    if scope.match_keywords and _contains_term(inst_clean, region_clean):
        return True, f"LOCAL_POR_INSTITUCION: {item.get('institution')}"

    for local_inst in scope.local_institutions:
        if _contains_term(inst_clean, local_inst):
            return True, f"LOCAL_POR_INSTITUCION: {item.get('institution')}"

    # 2. Comprobar si el objeto de estudio, población o empresa está en la localidad
    for kw in scope.match_keywords:
        if _contains_term(combined_text, kw) or _contains_term(inst_clean, kw):
            return True, f"LOCAL_POR_OBJETO_ESTUDIO: Coincidencia geográfica con '{kw}'"

    return False, "NACIONAL: Ámbito general Perú"


def search_peru_antecedents(
    actor,
    project_id,
    query: str,
    scope_filter: str = "todos",
    include_articles: bool = True,
    limit: int = 5,
) -> dict[str, Any]:
    """Busca tesis en ALICIA y artículos con filiación peruana, sin certificar arbitraje."""
    project = require_project(actor, project_id)
    query = query.strip()
    if not query:
        raise DomainError("VALIDATION_ERROR", "La consulta de búsqueda no puede estar vacía")
    if scope_filter not in ("todos", "locales", "nacionales"):
        raise DomainError("VALIDATION_ERROR", "scope_filter debe ser 'todos', 'locales' o 'nacionales'")
    if not 1 <= limit <= 20:
        raise DomainError("VALIDATION_ERROR", "limit debe estar entre 1 y 20")

    profile = ResearchProfile.objects.filter(project=project).first()
    place = profile.place if profile else None
    scope = resolve_geographic_scope(place)
    if scope_filter == "locales" and not scope.match_keywords:
        raise DomainError("VALIDATION_ERROR", "Configura el lugar del proyecto antes de buscar antecedentes locales")

    raw_candidates: list[dict] = []
    provider_errors: list[str] = []
    provider_successes = 0

    # 1. Búsqueda local orientada a la región
    if scope_filter in ("todos", "locales") and scope.match_keywords:
        try:
            local_query = f"{query} {scope.region}"
            theses_local = search_alicia_theses(local_query, limit=limit)
            raw_candidates.extend(theses_local)
            provider_successes += 1
        except DomainError:
            provider_errors.append("ALICIA_LOCAL")

    # 2. Búsqueda nacional en ALICIA
    if scope_filter in ("todos", "nacionales") or len(raw_candidates) < limit:
        try:
            theses_national = search_alicia_theses(query, limit=limit)
            raw_candidates.extend(theses_national)
            provider_successes += 1
        except DomainError:
            provider_errors.append("ALICIA_NACIONAL")

    # 3. Artículos con filiación peruana; la revisión por pares queda sin acreditar.
    if include_articles:
        try:
            articles = search_peru_affiliated_articles(query, limit=min(limit, 5))
            raw_candidates.extend(articles)
            provider_successes += 1
        except DomainError:
            provider_errors.append("OPENALEX_PERU")
    if not provider_successes:
        raise DomainError("SEARCH_UNAVAILABLE", "No se pudo consultar ningún proveedor de antecedentes peruanos")

    # Clasificación y deduplicación por título normalizado
    seen_titles = set()
    classified_results = []
    for item in raw_candidates:
        title_key = (item.get("title") or "").strip().lower()
        if not title_key or title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        is_local, justification = _classify_locality(item, scope)
        item["es_local"] = is_local
        item["justificacion_local"] = justification
        item["region_evaluada"] = scope.region

        # Filtrar según la opción seleccionada
        if scope_filter == "locales" and not is_local:
            continue
        if scope_filter == "nacionales" and is_local:
            continue

        classified_results.append(item)

    # Ordenar: si es "todos", priorizar los locales primero, luego por año descendente
    def _sort_key(doc: dict):
        local_weight = 0 if doc.get("es_local") else 1
        year_weight = -(doc.get("publication_year") or 0)
        return (local_weight, year_weight)

    classified_results.sort(key=_sort_key)
    final_list = classified_results[:limit]

    return {
        "project_id": str(project.id),
        "query": query,
        "region_detectada": scope.region,
        "scope_filter": scope_filter,
        "total_encontrados": len(final_list),
        "resultados": final_list,
        "fuentes_no_disponibles": provider_errors,
        "verification_level": "METADATA_ONLY",
        "full_text_inspected": False,
    }
