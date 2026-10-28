"""Rutas de integrations; registradas en el router compartido."""

from uuid import UUID

from django.http import JsonResponse

from thesis.services.agent_connections import (
    agent_connection_bearer, create_agent_connection, list_agent_connections, revoke_agent_connection,
)
from thesis.services.byoa_jobs import (
    append_byoa_event, claim_next_byoa_job, complete_byoa_job, fail_byoa_job, heartbeat_byoa_job,
)
from thesis.services.zotero import complete_zotero_oauth, disconnect_zotero, get_zotero_connection_status, start_zotero_oauth
from .schemas import AgentCompleteIn, AgentConnectionCreateIn, AgentEventIn, AgentFailIn
from .routers import integrations_router


@integrations_router.get("/zotero", operation_id="thesis_api_projects_zotero_status")
def zotero_status(request):
    return get_zotero_connection_status(request.user)


@integrations_router.get("/zotero/connect", operation_id="thesis_api_projects_zotero_connect")
def zotero_connect(request):
    return start_zotero_oauth(request.user, request)


@integrations_router.get("/zotero/callback", operation_id="thesis_api_projects_zotero_oauth_callback")
def zotero_oauth_callback(request):
    return complete_zotero_oauth(request.user, request)


@integrations_router.delete("/zotero", operation_id="thesis_api_projects_zotero_disconnect")
def zotero_disconnect(request):
    return disconnect_zotero(request.user)


@integrations_router.post("/agents", operation_id="thesis_api_create_agent_connection")
def create_agent_connection_route(request, payload: AgentConnectionCreateIn):
    result = create_agent_connection(
        request.user, payload.project_id, name=payload.name, runtime=payload.runtime,
    )
    return JsonResponse(result, status=201, headers={"Cache-Control": "no-store", "Pragma": "no-cache"})


@integrations_router.get("/agents", operation_id="thesis_api_list_agent_connections")
def list_agent_connections_route(request, project_id: UUID):
    return {"items": list_agent_connections(request.user, project_id)}


@integrations_router.delete("/agents/{connection_id}", operation_id="thesis_api_revoke_agent_connection")
def revoke_agent_connection_route(request, connection_id: UUID):
    return revoke_agent_connection(request.user, connection_id)


@integrations_router.post("/agents/connector/claim", auth=agent_connection_bearer,
                          operation_id="thesis_api_agent_connector_claim")
def agent_connector_claim(request):
    return {"job": claim_next_byoa_job(request.auth)}


@integrations_router.post("/agents/connector/jobs/{job_id}/heartbeat", auth=agent_connection_bearer,
                          operation_id="thesis_api_agent_connector_heartbeat")
def agent_connector_heartbeat(request, job_id: UUID):
    return heartbeat_byoa_job(request.auth, job_id)


@integrations_router.post("/agents/connector/jobs/{job_id}/events", auth=agent_connection_bearer,
                          operation_id="thesis_api_agent_connector_events")
def agent_connector_event(request, job_id: UUID, payload: AgentEventIn):
    return append_byoa_event(request.auth, job_id, event_type=payload.type, payload=payload.payload)


@integrations_router.post("/agents/connector/jobs/{job_id}/complete", auth=agent_connection_bearer,
                          operation_id="thesis_api_agent_connector_complete")
def agent_connector_complete(request, job_id: UUID, payload: AgentCompleteIn):
    return complete_byoa_job(
        request.auth, job_id, output_data=payload.output_data,
        provenance=payload.provenance, usage_data=payload.usage_data,
    )


@integrations_router.post("/agents/connector/jobs/{job_id}/fail", auth=agent_connection_bearer,
                          operation_id="thesis_api_agent_connector_fail")
def agent_connector_fail(request, job_id: UUID, payload: AgentFailIn):
    return fail_byoa_job(
        request.auth, job_id, error_code=payload.error_code, message=payload.message,
    )
