import { apiRequest } from "./client"
import type {
  CustomWorkflowTaskExecutions,
  EffectivePrompt,
  PublishWorkflowInput,
  RestoreWorkflowInput,
  SaveStepPayload,
  WorkflowDraftInput,
  WorkflowState,
  WorkflowTaskExecuteInput,
  WorkflowValidationResult,
} from "./types"

export function getWorkflowState(projectId: string): Promise<WorkflowState> {
  return apiRequest<WorkflowState>(`/projects/${encodeURIComponent(projectId)}/workflow`)
}

export function updateWorkflowDraft(
  projectId: string,
  payload: WorkflowDraftInput,
  csrfToken: string,
): Promise<WorkflowState> {
  return apiRequest<WorkflowState>(
    `/projects/${encodeURIComponent(projectId)}/workflow/draft`,
    {
      method: "PUT",
      csrfToken,
      body: JSON.stringify(payload),
    },
  )
}

export function validateWorkflowDraft(
  projectId: string,
  csrfToken: string,
): Promise<WorkflowValidationResult> {
  return apiRequest<WorkflowValidationResult>(
    `/projects/${encodeURIComponent(projectId)}/workflow/validate`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify({}),
    },
  )
}

export function publishWorkflowDraft(
  projectId: string,
  payload: PublishWorkflowInput,
  csrfToken: string,
): Promise<WorkflowState> {
  return apiRequest<WorkflowState>(
    `/projects/${encodeURIComponent(projectId)}/workflow/publish`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify(payload),
    },
  )
}

export function restoreWorkflowVersion(
  projectId: string,
  payload: RestoreWorkflowInput,
  csrfToken: string,
): Promise<WorkflowState> {
  return apiRequest<WorkflowState>(
    `/projects/${encodeURIComponent(projectId)}/workflow/restore`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify(payload),
    },
  )
}

export function getEffectivePrompt(projectId: string, taskId: string): Promise<EffectivePrompt> {
  return apiRequest<EffectivePrompt>(
    `/projects/${encodeURIComponent(projectId)}/workflow/tasks/${encodeURIComponent(taskId)}/prompt`,
  )
}

export function executeCustomWorkflowTask(
  projectId: string,
  taskId: string,
  payload: WorkflowTaskExecuteInput,
  csrfToken: string,
): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(
    `/projects/${encodeURIComponent(projectId)}/workflow/tasks/${encodeURIComponent(taskId)}/execute`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify(payload),
    },
  )
}

export function getCustomWorkflowTaskExecutions(
  projectId: string,
  taskId: string,
  workflowVersionNo?: number,
): Promise<CustomWorkflowTaskExecutions> {
  const query = workflowVersionNo !== undefined ? `?workflow_version_no=${workflowVersionNo}` : ""
  return apiRequest<CustomWorkflowTaskExecutions>(
    `/projects/${encodeURIComponent(projectId)}/workflow/tasks/${encodeURIComponent(taskId)}/executions${query}`,
  )
}

export function saveStep(
  projectId: string,
  stepCode: string,
  payload: SaveStepPayload,
  csrfToken: string,
): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(
    `/projects/${encodeURIComponent(projectId)}/steps/${encodeURIComponent(stepCode)}`,
    {
      method: "PUT",
      csrfToken,
      body: JSON.stringify(payload),
    },
  )
}
