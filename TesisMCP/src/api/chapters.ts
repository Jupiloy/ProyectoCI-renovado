import { apiRequest } from "./client"
import type {
  ChapterContentTree,
  ChapterDocument,
  ChapterState,
  CitationEvidenceReview,
  CitationReplacementProposal,
  IeeeCitationView,
} from "./types"

export function getChapterState(projectId: string, chapterNo: number): Promise<ChapterState> {
  return apiRequest<ChapterState>(`/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}`)
}

export function getChapterDocument(projectId: string, chapterNo: number): Promise<ChapterDocument> {
  return apiRequest<ChapterDocument>(`/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/document`)
}

export type SaveChapterInput = {
  content_tree: ChapterContentTree
  citations: Array<{
    group_id: string
    block_id: string
    position: number
    sources: Array<{ source_id: string; locator: string }>
  }>
  expected_version: number
  idempotency_key: string
}

export function saveChapterDocument(
  projectId: string,
  chapterNo: number,
  payload: SaveChapterInput,
  csrfToken: string,
): Promise<ChapterDocument> {
  return apiRequest<ChapterDocument>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/document`,
    { method: "PUT", csrfToken, body: JSON.stringify(payload) },
  )
}

export function getChapterIeeeCitations(
  projectId: string,
  chapterNo: number,
): Promise<IeeeCitationView> {
  return apiRequest<IeeeCitationView>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/citations/ieee`,
  )
}

export async function listCitationEvidence(
  projectId: string,
  chapterNo: number,
  occurrenceId: string,
): Promise<CitationEvidenceReview[]> {
  const res = await apiRequest<{ reviews: CitationEvidenceReview[] }>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/citations/${occurrenceId}/evidence`,
  )
  return res.reviews
}

export function addCitationEvidence(
  projectId: string,
  chapterNo: number,
  occurrenceId: string,
  payload: {
    excerpt_id: number
    claim_start: number
    claim_end: number
    excerpt_start: number
    excerpt_end: number
    idempotency_key: string
  },
  csrfToken?: string,
): Promise<{ idempotent: boolean; review_id: string }> {
  return apiRequest(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/citations/${occurrenceId}/evidence`,
    { method: "POST", csrfToken, body: JSON.stringify(payload) },
  )
}

export function decideCitationEvidence(
  projectId: string,
  chapterNo: number,
  reviewId: string,
  payload: {
    status: "SUPPORTS" | "CONTRADICTS" | "UNRELATED" | "INSUFFICIENT"
    expected_version: number
    idempotency_key: string
    note?: string
  },
  csrfToken?: string,
): Promise<CitationEvidenceReview> {
  return apiRequest<CitationEvidenceReview>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/citation-evidence/${reviewId}/decision`,
    { method: "POST", csrfToken, body: JSON.stringify(payload) },
  )
}

export function proposeCitationReplacement(
  projectId: string,
  chapterNo: number,
  occurrenceId: string,
  payload: {
    replacement_source_id: string
    rationale: string
    idempotency_key: string
  },
  csrfToken?: string,
): Promise<CitationReplacementProposal> {
  return apiRequest<CitationReplacementProposal>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/citations/${occurrenceId}/replacement-proposals`,
    { method: "POST", csrfToken, body: JSON.stringify(payload) },
  )
}

export function previewCitationReplacement(
  projectId: string,
  chapterNo: number,
  proposalId: string,
): Promise<CitationReplacementProposal> {
  return apiRequest<CitationReplacementProposal>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/citation-replacement-proposals/${proposalId}`,
  )
}

export function decideCitationReplacement(
  projectId: string,
  chapterNo: number,
  proposalId: string,
  payload: {
    action: "ACCEPTED" | "REJECTED"
    expected_document_version: number
    idempotency_key: string
    reason?: string
  },
  csrfToken?: string,
): Promise<CitationReplacementProposal> {
  return apiRequest<CitationReplacementProposal>(
    `/projects/${encodeURIComponent(projectId)}/chapters/${chapterNo}/citation-replacement-proposals/${proposalId}/decision`,
    { method: "POST", csrfToken, body: JSON.stringify(payload) },
  )
}
