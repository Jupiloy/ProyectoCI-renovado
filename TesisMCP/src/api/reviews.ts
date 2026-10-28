import { apiRequest } from "./client"
import type {
  AdvisorDashboardProject,
  ChapterSnapshotDetail,
  ChapterSnapshotSummary,
  ChapterState,
  ReviewComment,
  SupportContribution,
  SupportInvitation,
} from "./types"

export function getAdvisorDashboard(): Promise<AdvisorDashboardProject[]> {
  return apiRequest<AdvisorDashboardProject[]>("/projects/advisor/dashboard")
}

export function submitChapter(
  projectId: string,
  chapterNo: number,
  csrfToken: string,
): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/submit`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify({}),
    },
  )
}

export function listChapterSnapshots(
  projectId: string,
  chapterNo: number,
): Promise<ChapterSnapshotSummary[]> {
  return apiRequest<ChapterSnapshotSummary[]>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/snapshots`,
  )
}

export function getChapterSnapshot(
  projectId: string,
  chapterNo: number,
  snapshotId: string,
): Promise<ChapterSnapshotDetail> {
  return apiRequest<ChapterSnapshotDetail>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/snapshots/${encodeURIComponent(snapshotId)}`,
  )
}

export function listComments(
  projectId: string,
  chapterNo: number,
  snapshotId?: string,
): Promise<ReviewComment[]> {
  const query = snapshotId ? `?snapshot_id=${encodeURIComponent(snapshotId)}` : ""
  return apiRequest<ReviewComment[]>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/comments${query}`,
  )
}

export function addComment(
  projectId: string,
  chapterNo: number,
  payload: {
    start_cp: number
    end_cp: number
    selected_text: string
    body: string
    snapshot_id?: string
  },
  csrfToken: string,
): Promise<ReviewComment> {
  return apiRequest<ReviewComment>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/comments`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify(payload),
    },
  )
}

export function resolveComment(
  projectId: string,
  commentId: number,
  csrfToken: string,
): Promise<ReviewComment> {
  return apiRequest<ReviewComment>(
    `/projects/${encodeURIComponent(projectId)}/comments/${commentId}/resolve`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify({}),
    },
  )
}

export function decideChapter(
  projectId: string,
  chapterNo: number,
  action: "REQUEST_CHANGES" | "APPROVE" | "REOPEN",
  reason: string,
  csrfToken: string,
): Promise<ChapterState> {
  return apiRequest<ChapterState>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/decision`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify({ action, reason }),
    },
  )
}

export function listSupportInvitations(
  projectId: string,
): Promise<{ items: SupportInvitation[] }> {
  return apiRequest<{ items: SupportInvitation[] }>(
    `/projects/${encodeURIComponent(projectId)}/support-invitations`,
  )
}

export function createSupportInvitation(
  projectId: string,
  payload: {
    invited_email: string
    task_id: string
    task_instructions: string
    source_ids?: string[]
    ttl_hours?: number
  },
  csrfToken: string,
): Promise<SupportInvitation> {
  return apiRequest<SupportInvitation>(
    `/projects/${encodeURIComponent(projectId)}/support-invitations`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify(payload),
    },
  )
}

export function revokeSupportInvitation(
  projectId: string,
  invitationId: string,
  csrfToken: string,
): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(
    `/projects/${encodeURIComponent(projectId)}/support-invitations/${encodeURIComponent(invitationId)}/revoke`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify({}),
    },
  )
}

export function listSupportContributions(
  projectId: string,
  invitationId: string,
): Promise<{ items: SupportContribution[] }> {
  return apiRequest<{ items: SupportContribution[] }>(
    `/projects/${encodeURIComponent(projectId)}/support-invitations/${encodeURIComponent(invitationId)}/contributions`,
  )
}
