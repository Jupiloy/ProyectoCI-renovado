"""Rutas de support; registradas en el router compartido."""

from uuid import UUID
from django.http import FileResponse
from thesis.services.support_invitations import accept_support_invitation, create_support_invitation, get_support_invitation_context, get_support_source_file, list_support_contributions, list_support_invitations, revoke_support_invitation, submit_support_contribution
from .schemas import AcceptSupportInvitationIn, CreateSupportInvitationIn, SupportContributionIn
from .routers import router


@router.post("/{project_id}/support-invitations", operation_id="thesis_api_projects_create_project_support_invitation")
def create_project_support_invitation(request, project_id: UUID, payload: CreateSupportInvitationIn):
    return create_support_invitation(
        request.user, project_id, payload.invited_email, payload.task_id,
        payload.task_instructions, payload.source_ids, payload.ttl_hours,
    )


@router.get("/{project_id}/support-invitations", operation_id="thesis_api_projects_get_project_support_invitations")
def get_project_support_invitations(request, project_id: UUID):
    return {"items": list_support_invitations(request.user, project_id)}


@router.post("/{project_id}/support-invitations/{invitation_id}/revoke", operation_id="thesis_api_projects_revoke_project_support_invitation")
def revoke_project_support_invitation(request, project_id: UUID, invitation_id: UUID):
    return revoke_support_invitation(request.user, project_id, invitation_id)


@router.get("/{project_id}/support-invitations/{invitation_id}/contributions", operation_id="thesis_api_projects_get_project_support_contributions")
def get_project_support_contributions(request, project_id: UUID, invitation_id: UUID):
    return {"items": list_support_contributions(request.user, project_id, invitation_id)}


@router.post("/support-invitations/{invitation_id}/accept", operation_id="thesis_api_projects_accept_project_support_invitation")
def accept_project_support_invitation(request, invitation_id: UUID, payload: AcceptSupportInvitationIn):
    return accept_support_invitation(request.user, invitation_id, payload.invite_token)


@router.get("/support-invitations/{invitation_id}/workspace", operation_id="thesis_api_projects_get_support_workspace")
def get_support_workspace(request, invitation_id: UUID):
    return get_support_invitation_context(request.user, invitation_id)


@router.get("/support-invitations/{invitation_id}/sources/{source_id}/file", operation_id="thesis_api_projects_download_support_source")
def download_support_source(request, invitation_id: UUID, source_id: UUID):
    path, filename = get_support_source_file(request.user, invitation_id, source_id)
    return FileResponse(path.open("rb"), as_attachment=True, filename=filename, content_type="application/pdf")


@router.post("/support-invitations/{invitation_id}/contributions", operation_id="thesis_api_projects_submit_project_support_contribution")
def submit_project_support_contribution(request, invitation_id: UUID, payload: SupportContributionIn):
    return submit_support_contribution(
        request.user, invitation_id, payload.response_text,
        payload.source_excerpt_ids, payload.idempotency_key,
    )
