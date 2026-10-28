"""Rutas de generation; registradas en el router compartido."""

from uuid import UUID
from ninja import Status
from thesis.services.ai_jobs import get_ai_job, request_task_generation
from thesis.services.ai_batches import create_ai_batch, get_ai_batch, list_ai_batches, cancel_ai_batch
from thesis.services.batch_synthesis import cancel_batch_synthesis, create_batch_synthesis, decide_batch_synthesis, get_batch_synthesis, list_batch_syntheses
from .schemas import CreateAIBatchIn, CreateBatchSynthesisIn, DecideBatchSynthesisIn, GenerateTaskProposalIn
from .routers import router


@router.post("/{project_id}/workflow/tasks/{task_id}/generate", response={200: dict, 202: dict}, operation_id="thesis_api_projects_generate_proposal")
def generate_proposal(request, project_id: UUID, task_id: str, payload: GenerateTaskProposalIn):
    job = request_task_generation(
        actor=request.user,
        project_id=project_id,
        task_id=task_id,
        input_data=payload.input_data,
        context_refs=payload.context_refs,
        idempotency_key=payload.idempotency_key,
        expected_state_version=payload.expected_state_version,
        workflow_version_no=payload.workflow_version_no,
    )
    status_code = 200 if job.get("status") == "SUCCEEDED" else 202
    return Status(status_code, job)


@router.get("/{project_id}/ai-jobs/{job_id}", operation_id="thesis_api_projects_get_generation_job")
def get_generation_job(request, project_id: UUID, job_id: UUID):
    return get_ai_job(request.user, project_id, job_id)


@router.post("/{project_id}/ai-batches", response={202: dict}, operation_id="thesis_api_projects_create_generation_batch")
def create_generation_batch(request, project_id: UUID, payload: CreateAIBatchIn):
    batch = create_ai_batch(
        actor=request.user,
        project_id=project_id,
        tasks=[item.dict() for item in payload.tasks],
        expected_state_version=payload.expected_state_version,
        workflow_version_no=payload.workflow_version_no,
        idempotency_key=payload.idempotency_key,
    )
    return Status(202, batch)


@router.get("/{project_id}/ai-batches", operation_id="thesis_api_projects_get_generation_batches")
def get_generation_batches(request, project_id: UUID):
    return {"items": list_ai_batches(request.user, project_id)}


@router.get("/{project_id}/ai-batches/{batch_id}", operation_id="thesis_api_projects_get_generation_batch")
def get_generation_batch(request, project_id: UUID, batch_id: UUID):
    return get_ai_batch(request.user, project_id, batch_id)


@router.post("/{project_id}/ai-batches/{batch_id}/cancel", operation_id="thesis_api_projects_cancel_generation_batch")
def cancel_generation_batch(request, project_id: UUID, batch_id: UUID):
    return cancel_ai_batch(request.user, project_id, batch_id)


@router.post("/{project_id}/ai-batches/{batch_id}/syntheses", response={202: dict}, operation_id="thesis_api_projects_create_generation_batch_synthesis")
def create_generation_batch_synthesis(request, project_id: UUID, batch_id: UUID, payload: CreateBatchSynthesisIn):
    result = create_batch_synthesis(
        request.user, project_id, batch_id, payload.job_ids, payload.idempotency_key,
    )
    return Status(202, result)


@router.get("/{project_id}/ai-batches/{batch_id}/syntheses", operation_id="thesis_api_projects_get_generation_batch_syntheses")
def get_generation_batch_syntheses(request, project_id: UUID, batch_id: UUID):
    return {"items": list_batch_syntheses(request.user, project_id, batch_id)}


@router.get("/{project_id}/ai-batches/{batch_id}/syntheses/{synthesis_id}", operation_id="thesis_api_projects_get_generation_batch_synthesis")
def get_generation_batch_synthesis(request, project_id: UUID, batch_id: UUID, synthesis_id: UUID):
    return get_batch_synthesis(request.user, project_id, batch_id, synthesis_id)


@router.post("/{project_id}/ai-batches/{batch_id}/syntheses/{synthesis_id}/cancel", operation_id="thesis_api_projects_cancel_generation_batch_synthesis")
def cancel_generation_batch_synthesis(request, project_id: UUID, batch_id: UUID, synthesis_id: UUID):
    return cancel_batch_synthesis(request.user, project_id, batch_id, synthesis_id)


@router.post("/{project_id}/ai-batches/{batch_id}/syntheses/{synthesis_id}/decision", operation_id="thesis_api_projects_decide_generation_batch_synthesis")
def decide_generation_batch_synthesis(
    request, project_id: UUID, batch_id: UUID, synthesis_id: UUID, payload: DecideBatchSynthesisIn,
):
    return decide_batch_synthesis(
        request.user, project_id, batch_id, synthesis_id,
        payload.decision, payload.decision_key, payload.reason,
    )
