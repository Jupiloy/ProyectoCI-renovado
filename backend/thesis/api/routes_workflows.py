"""Rutas de workflows; registradas en el router compartido."""

from uuid import UUID
from thesis.services.workflows import create_or_update_draft, execute_custom_workflow_task, get_custom_workflow_task_executions, get_effective_prompt, get_workflow_state, publish_workflow_draft, restore_workflow_version, validate_workflow_draft
from .schemas import PublishWorkflowIn, RestoreWorkflowIn, WorkflowDraftIn, WorkflowTaskExecuteIn
from .routers import router


@router.get("/{project_id}/workflow", operation_id="thesis_api_projects_workflow_state")
def workflow_state(request, project_id: UUID):
    return get_workflow_state(request.user, project_id)


@router.put("/{project_id}/workflow/draft", operation_id="thesis_api_projects_update_workflow_draft")
def update_workflow_draft(request, project_id: UUID, payload: WorkflowDraftIn):
    payload_data = payload.dict(exclude_unset=True) if hasattr(payload, "dict") else payload.model_dump(exclude_unset=True)
    return create_or_update_draft(request.user, project_id, payload_data, payload.expected_version)


@router.post("/{project_id}/workflow/validate", operation_id="thesis_api_projects_validate_draft")
def validate_draft(request, project_id: UUID):
    return validate_workflow_draft(request.user, project_id)


@router.post("/{project_id}/workflow/publish", operation_id="thesis_api_projects_publish_draft")
def publish_draft(request, project_id: UUID, payload: PublishWorkflowIn):
    return publish_workflow_draft(request.user, project_id, payload.change_summary, payload.expected_version)


@router.post("/{project_id}/workflow/restore", operation_id="thesis_api_projects_restore_workflow")
def restore_workflow(request, project_id: UUID, payload: RestoreWorkflowIn):
    return restore_workflow_version(request.user, project_id, payload.target_version_no, payload.change_summary)


@router.get("/{project_id}/workflow/tasks/{task_id}/prompt", operation_id="thesis_api_projects_effective_prompt")
def effective_prompt(request, project_id: UUID, task_id: str):
    return get_effective_prompt(request.user, project_id, task_id)


@router.post("/{project_id}/workflow/tasks/{task_id}/execute", operation_id="thesis_api_projects_execute_workflow_task")
def execute_workflow_task(request, project_id: UUID, task_id: str, payload: WorkflowTaskExecuteIn):
    return execute_custom_workflow_task(
        request.user, project_id, task_id, payload.input_data,
        payload.output_data, payload.idempotency_key,
    )


@router.get("/{project_id}/workflow/tasks/{task_id}/executions", operation_id="thesis_api_projects_workflow_task_executions")
def workflow_task_executions(request, project_id: UUID, task_id: str, workflow_version_no: int | None = None):
    return get_custom_workflow_task_executions(
        request.user, project_id, task_id, workflow_version_no,
    )
