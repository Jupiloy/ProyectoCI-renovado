"""Rutas de generation_decisions; registradas en el router compartido."""

from uuid import UUID
from thesis.services.ai_jobs import accept_ai_proposal, cancel_ai_job, get_ai_document_diff, reject_ai_proposal
from .schemas import AcceptAIProposalIn, RejectAIProposalIn
from .routers import router


@router.get("/{project_id}/ai-jobs/{job_id}/document-diff", operation_id="thesis_api_projects_get_generation_document_diff")
def get_generation_document_diff(request, project_id: UUID, job_id: UUID):
    return get_ai_document_diff(request.user, project_id, job_id)


@router.post("/{project_id}/ai-jobs/{job_id}/cancel", operation_id="thesis_api_projects_cancel_generation_job")
def cancel_generation_job(request, project_id: UUID, job_id: UUID):
    return cancel_ai_job(request.user, project_id, job_id)


@router.post("/{project_id}/ai-jobs/{job_id}/accept", operation_id="thesis_api_projects_accept_proposal")
def accept_proposal(request, project_id: UUID, job_id: UUID, payload: AcceptAIProposalIn):
    return accept_ai_proposal(
        actor=request.user,
        project_id=project_id,
        job_id=job_id,
        expected_state_version=payload.expected_state_version,
        decision_key=payload.decision_key,
        expected_document_version=payload.expected_document_version,
        proposal_sha256=payload.proposal_sha256,
    )


@router.post("/{project_id}/ai-jobs/{job_id}/reject", operation_id="thesis_api_projects_reject_proposal")
def reject_proposal(request, project_id: UUID, job_id: UUID, payload: RejectAIProposalIn):
    return reject_ai_proposal(
        actor=request.user,
        project_id=project_id,
        job_id=job_id,
        decision_key=payload.decision_key,
        reason=payload.reason,
    )
