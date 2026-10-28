"""Rutas de overview; registradas en el router compartido."""

from uuid import UUID
from django.http import FileResponse
from ninja import Status
from thesis.services.discovery import search_semantic_scholar
from thesis.services.discovery_peru import search_peru_antecedents
from thesis.services.exploration import explore_idea
from thesis.services.exports import export_approved_snapshot_docx, export_draft_docx
from thesis.services.projects import create_project, get_project_state, list_user_projects, register_idea
from thesis.services.discovery_sources import list_search_execution_sources
from thesis.services.search_strategies import create_search_strategy, get_search_strategy_history, list_manual_search_executions, list_search_strategies, record_manual_search_execution, revise_search_strategy
from .schemas import CreateProjectIn, ManualSearchExecutionIn, ProjectListOut, RegisterIdeaIn, SearchStrategyIn, SearchStrategyRevisionIn
from .routers import router


@router.get("", response=ProjectListOut, operation_id="thesis_api_projects_list")
def list_projects(request, offset: int = 0, limit: int = 50):
    return list_user_projects(request.user, offset=offset, limit=limit)


@router.post("", operation_id="thesis_api_projects_create")
def create(request, payload: CreateProjectIn):
    project = create_project(request.user, payload.name, payload.title)
    return get_project_state(request.user, project.id)


@router.get("/{project_id}", operation_id="thesis_api_projects_state")
def state(request, project_id: UUID):
    return get_project_state(request.user, project_id)


@router.get("/{project_id}/export/draft.docx", operation_id="thesis_api_projects_export_draft")
def export_draft(request, project_id: UUID):
    stream = export_draft_docx(request.user, project_id)
    return FileResponse(
        stream,
        as_attachment=True,
        filename="tesis-borrador.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/{project_id}/chapters/{chapter_no}/export/approved.docx", operation_id="thesis_api_projects_export_approved_chapter")
def export_approved_chapter(request, project_id: UUID, chapter_no: int):
    stream = export_approved_snapshot_docx(request.user, project_id, chapter_no)
    return FileResponse(
        stream,
        as_attachment=True,
        filename=f"capitulo-{chapter_no}-aprobado.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.put("/{project_id}/idea", operation_id="thesis_api_projects_idea")
def idea(request, project_id: UUID, payload: RegisterIdeaIn):
    return register_idea(request.user, project_id, payload.description, payload.expected_version)


@router.get("/{project_id}/idea/explore", operation_id="thesis_api_projects_explore")
def explore(request, project_id: UUID):
    return explore_idea(request.user, project_id)


@router.get("/{project_id}/discovery/semantic-scholar", operation_id="thesis_api_projects_semantic_scholar")
def semantic_scholar(request, project_id: UUID, query: str, limit: int = 5):
    return search_semantic_scholar(request.user, project_id, query, limit)


@router.get("/{project_id}/discovery/peru", operation_id="thesis_api_projects_peru_discovery")
def peru_discovery(request, project_id: UUID, query: str, scope_filter: str = "todos",
                   include_articles: bool = True, limit: int = 5):
    return search_peru_antecedents(request.user, project_id, query, scope_filter, include_articles, limit)


@router.post("/{project_id}/search-strategies", response={201: dict}, operation_id="thesis_api_projects_create_project_search_strategy")
def create_project_search_strategy(request, project_id: UUID, payload: SearchStrategyIn):
    result = create_search_strategy(request.user, project_id, payload.dict())
    return Status(201, result)


@router.get("/{project_id}/search-strategies", operation_id="thesis_api_projects_search_strategies")
def search_strategies(request, project_id: UUID):
    return {"strategies": list_search_strategies(request.user, project_id)}


@router.get("/{project_id}/search-strategies/{strategy_id}", operation_id="thesis_api_projects_search_strategy_history")
def search_strategy_history(request, project_id: UUID, strategy_id: UUID):
    return {"versions": get_search_strategy_history(request.user, project_id, strategy_id)}


@router.post("/{project_id}/search-strategies/{strategy_id}/revisions", response={201: dict}, operation_id="thesis_api_projects_create_search_strategy_revision")
def create_search_strategy_revision(request, project_id: UUID, strategy_id: UUID, payload: SearchStrategyRevisionIn):
    result = revise_search_strategy(request.user, project_id, strategy_id, payload.expected_version, payload.dict())
    return Status(201, result)


@router.post("/{project_id}/search-strategies/{strategy_id}/executions/manual", response={201: dict}, operation_id="thesis_api_projects_register_manual_search_execution")
def register_manual_search_execution(request, project_id: UUID, strategy_id: UUID, payload: ManualSearchExecutionIn):
    result = record_manual_search_execution(
        request.user, project_id, strategy_id, payload.execution_date,
        payload.reported_result_count, payload.notes, payload.idempotency_key,
    )
    return Status(201, result)


@router.get("/{project_id}/search-strategies/{strategy_id}/executions", operation_id="thesis_api_projects_manual_search_executions")
def manual_search_executions(request, project_id: UUID, strategy_id: UUID):
    return {"executions": list_manual_search_executions(request.user, project_id, strategy_id)}


@router.get("/{project_id}/search-strategies/{strategy_id}/executions/{execution_id}/sources", operation_id="thesis_api_projects_manual_search_execution_sources")
def manual_search_execution_sources(request, project_id: UUID, strategy_id: UUID, execution_id: UUID):
    return list_search_execution_sources(request.user, project_id, strategy_id, execution_id)
