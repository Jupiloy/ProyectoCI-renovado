"""Consulta de catálogos académicos con control de acceso por proyecto."""

from thesis.integrations.semantic_scholar import search_papers
from thesis.services.access import require_project
from thesis.services.errors import DomainError


def search_semantic_scholar(actor, project_id, query: str, limit: int = 5) -> dict:
    require_project(actor, project_id)
    query = query.strip()
    if not 3 <= len(query) <= 300:
        raise DomainError("VALIDATION_ERROR", "La consulta debe tener entre 3 y 300 caracteres")
    return {
        "provider": "SEMANTIC_SCHOLAR",
        "query": query,
        "results": search_papers(query, limit),
        "verification_level": "METADATA_ONLY",
        "full_text_inspected": False,
    }
