import { apiRequest } from "./client"
import type {
  AcceptProposalPayload,
  AIBatch,
  AIGenerationJob,
  BatchSynthesis,
  DocumentDiff,
  RejectProposalPayload,
} from "./types"

export async function generateProposal(
  projectId: string,
  taskId: string,
  payload: {
    input_data?: Record<string, unknown>
    context_refs?: Record<string, unknown>[]
    expected_state_version?: number
    workflow_version_no?: number
    idempotency_key: string
  },
  csrfToken?: string,
): Promise<AIGenerationJob> {
  return apiRequest<AIGenerationJob>(
    `/projects/${projectId}/workflow/tasks/${taskId}/generate`,
    {
      method: "POST",
      body: JSON.stringify(payload),
      csrfToken,
    },
  )
}

export async function getGenerationJob(
  projectId: string,
  jobId: string,
): Promise<AIGenerationJob> {
  return apiRequest<AIGenerationJob>(`/projects/${projectId}/ai-jobs/${jobId}`)
}

export async function getGenerationDocumentDiff(
  projectId: string,
  jobId: string,
): Promise<DocumentDiff> {
  return apiRequest<DocumentDiff>(
    `/projects/${projectId}/ai-jobs/${jobId}/document-diff`,
  )
}

export async function cancelGenerationJob(
  projectId: string,
  jobId: string,
  csrfToken?: string,
): Promise<AIGenerationJob> {
  return apiRequest<AIGenerationJob>(
    `/projects/${projectId}/ai-jobs/${jobId}/cancel`,
    {
      method: "POST",
      csrfToken,
    },
  )
}

export async function acceptProposal(
  projectId: string,
  jobId: string,
  payload: AcceptProposalPayload,
  csrfToken?: string,
): Promise<{
  job_id: string
  acceptance_status: string
  result_revision_id: number | null
  result_execution_id: number | null
  result_document_revision_id: string | null
  workflow_version_no: number
  state_version?: number
  idempotent: boolean
}> {
  return apiRequest(`/projects/${projectId}/ai-jobs/${jobId}/accept`, {
    method: "POST",
    body: JSON.stringify(payload),
    csrfToken,
  })
}

export async function rejectProposal(
  projectId: string,
  jobId: string,
  payload: RejectProposalPayload,
  csrfToken?: string,
): Promise<{
  job_id: string
  acceptance_status: string
  decision_reason: string | null
  idempotent: boolean
}> {
  return apiRequest(`/projects/${projectId}/ai-jobs/${jobId}/reject`, {
    method: "POST",
    body: JSON.stringify(payload),
    csrfToken,
  })
}

export async function createGenerationBatch(
  projectId: string,
  payload: {
    tasks: Array<{
      task_id: string
      input_data?: Record<string, unknown>
      context_refs?: Record<string, unknown>[]
    }>
    expected_state_version: number
    workflow_version_no: number
    idempotency_key: string
  },
  csrfToken?: string,
): Promise<AIBatch> {
  return apiRequest<AIBatch>(`/projects/${projectId}/ai-batches`, {
    method: "POST",
    body: JSON.stringify(payload),
    csrfToken,
  })
}

export async function listGenerationBatches(
  projectId: string,
): Promise<AIBatch[]> {
  const res = await apiRequest<{ items: AIBatch[] }>(
    `/projects/${projectId}/ai-batches`,
  )
  return res.items
}

export async function getGenerationBatch(
  projectId: string,
  batchId: string,
): Promise<AIBatch> {
  return apiRequest<AIBatch>(`/projects/${projectId}/ai-batches/${batchId}`)
}

export async function cancelGenerationBatch(
  projectId: string,
  batchId: string,
  csrfToken?: string,
): Promise<AIBatch> {
  return apiRequest<AIBatch>(
    `/projects/${projectId}/ai-batches/${batchId}/cancel`,
    {
      method: "POST",
      csrfToken,
    },
  )
}

export async function createBatchSynthesis(
  projectId: string,
  batchId: string,
  payload: {
    job_ids: string[]
    idempotency_key: string
  },
  csrfToken?: string,
): Promise<BatchSynthesis> {
  return apiRequest<BatchSynthesis>(
    `/projects/${projectId}/ai-batches/${batchId}/syntheses`,
    {
      method: "POST",
      body: JSON.stringify(payload),
      csrfToken,
    },
  )
}

export async function listBatchSyntheses(
  projectId: string,
  batchId: string,
): Promise<BatchSynthesis[]> {
  const res = await apiRequest<{ items: BatchSynthesis[] }>(
    `/projects/${projectId}/ai-batches/${batchId}/syntheses`,
  )
  return res.items
}

export async function getBatchSynthesis(
  projectId: string,
  batchId: string,
  synthesisId: string,
): Promise<BatchSynthesis> {
  return apiRequest<BatchSynthesis>(
    `/projects/${projectId}/ai-batches/${batchId}/syntheses/${synthesisId}`,
  )
}

export async function cancelBatchSynthesis(
  projectId: string,
  batchId: string,
  synthesisId: string,
  csrfToken?: string,
): Promise<BatchSynthesis> {
  return apiRequest<BatchSynthesis>(
    `/projects/${projectId}/ai-batches/${batchId}/syntheses/${synthesisId}/cancel`,
    {
      method: "POST",
      csrfToken,
    },
  )
}

export async function decideBatchSynthesis(
  projectId: string,
  batchId: string,
  synthesisId: string,
  payload: {
    decision: "ACCEPTED" | "REJECTED"
    decision_key: string
    reason?: string
  },
  csrfToken?: string,
): Promise<BatchSynthesis> {
  return apiRequest<BatchSynthesis>(
    `/projects/${projectId}/ai-batches/${batchId}/syntheses/${synthesisId}/decision`,
    {
      method: "POST",
      body: JSON.stringify(payload),
      csrfToken,
    },
  )
}
