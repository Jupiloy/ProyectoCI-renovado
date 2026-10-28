"""Rutas de integrations; registradas en el router compartido."""

from thesis.services.zotero import complete_zotero_oauth, disconnect_zotero, get_zotero_connection_status, start_zotero_oauth
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
