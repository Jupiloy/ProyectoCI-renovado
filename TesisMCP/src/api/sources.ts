import { apiRequest } from "./client"
import type {
  DiscoveryCandidate,
  DocumentJob,
  PassageSearchResult,
  SearchStrategy,
  SourceDocument,
  SourceExcerpt,
  SourceSegment,
  ZoteroConnectionStatus,
} from "./types"

export function listSources(projectId: string): Promise<SourceDocument[]> {
  return apiRequest<SourceDocument[]>(`/projects/${encodeURIComponent(projectId)}/sources`)
}

export function uploadSource(
  projectId: string,
  label: string,
  file: File,
  csrfToken: string,
): Promise<SourceDocument & { job?: DocumentJob }> {
  const formData = new FormData()
  formData.append("label", label)
  formData.append("file", file)

  return apiRequest<SourceDocument & { job?: DocumentJob }>(
    `/projects/${encodeURIComponent(projectId)}/sources/upload`,
    {
      method: "POST",
      csrfToken,
      body: formData,
    },
  )
}

export function importBibliographyFile(
  projectId: string,
  provider: string,
  file: File,
  csrfToken: string,
  executionId = "",
): Promise<Record<string, unknown>> {
  const formData = new FormData()
  formData.append("provider", provider)
  formData.append("file", file)
  if (executionId) formData.append("execution_id", executionId)

  return apiRequest<Record<string, unknown>>(
    `/projects/${encodeURIComponent(projectId)}/sources/import-bibliography`,
    {
      method: "POST",
      csrfToken,
      body: formData,
    },
  )
}

export function listSourceExcerpts(
  projectId: string,
  sourceId: string,
  pageNo?: number,
  limit = 20,
): Promise<{ source: SourceDocument; excerpts: SourceExcerpt[] }> {
  const params = new URLSearchParams()
  if (pageNo !== undefined) params.set("page_no", String(pageNo))
  params.set("limit", String(limit))
  return apiRequest<{ source: SourceDocument; excerpts: SourceExcerpt[] }>(
    `/projects/${encodeURIComponent(projectId)}/sources/${encodeURIComponent(sourceId)}/excerpts?${params.toString()}`,
  )
}

export function listSourceSegments(
  projectId: string,
  sourceId: string,
  offset = 0,
  limit = 50,
): Promise<{ source: SourceDocument; segments: SourceSegment[] }> {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  return apiRequest<{ source: SourceDocument; segments: SourceSegment[] }>(
    `/projects/${encodeURIComponent(projectId)}/sources/${encodeURIComponent(sourceId)}/segments?${params.toString()}`,
  )
}

export function searchPassages(
  projectId: string,
  query: string,
  limit = 5,
  sourceIds?: string[],
  csrfToken?: string,
): Promise<PassageSearchResult> {
  return apiRequest<PassageSearchResult>(
    `/projects/${encodeURIComponent(projectId)}/passages/search`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify({ query, limit, ...(sourceIds?.length ? { source_ids: sourceIds } : {}) }),
    },
  )
}

export function getDocumentJob(projectId: string, jobId: string): Promise<DocumentJob> {
  return apiRequest<DocumentJob>(
    `/projects/${encodeURIComponent(projectId)}/jobs/${encodeURIComponent(jobId)}`,
  )
}

export function searchSemanticScholar(
  projectId: string,
  query: string,
  limit = 10,
): Promise<{ query: string; results: DiscoveryCandidate[] }> {
  const params = new URLSearchParams({ query, limit: String(limit) })
  return apiRequest<{ query: string; results: DiscoveryCandidate[] }>(
    `/projects/${encodeURIComponent(projectId)}/discovery/semantic-scholar?${params.toString()}`,
  )
}

export function searchPeruDiscovery(
  projectId: string,
  query: string,
  limit = 10,
): Promise<{ query: string; results: DiscoveryCandidate[] }> {
  const params = new URLSearchParams({ query, limit: String(limit) })
  return apiRequest<{ query: string; results: DiscoveryCandidate[] }>(
    `/projects/${encodeURIComponent(projectId)}/discovery/peru?${params.toString()}`,
  )
}

export function selectDiscoveryCandidate(
  projectId: string,
  candidate: DiscoveryCandidate,
  csrfToken: string,
): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(
    `/projects/${encodeURIComponent(projectId)}/sources/select-discovery`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify(candidate),
    },
  )
}

export function listSearchStrategies(projectId: string): Promise<SearchStrategy[]> {
  return apiRequest<SearchStrategy[]>(
    `/projects/${encodeURIComponent(projectId)}/search-strategies`,
  )
}

export function createSearchStrategy(
  projectId: string,
  strategy: {
    provider: string
    title: string
    topic: string
    query_text: string
    search_equation?: string
    concepts?: string[]
    filters?: Record<string, unknown>
    search_url?: string
    idempotency_key: string
  },
  csrfToken: string,
): Promise<SearchStrategy> {
  return apiRequest<SearchStrategy>(
    `/projects/${encodeURIComponent(projectId)}/search-strategies`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify(strategy),
    },
  )
}

/** Encola la indexación de pasajes de una fuente (kind INDEX del backend,
 * DocumentJob en cola; exige TEXT_CHECKED y rol OWNER). Devuelve el job 202. */
export function indexSourcePassages(
  projectId: string,
  sourceId: string,
  csrfToken: string,
): Promise<DocumentJob> {
  return apiRequest<DocumentJob>(
    `/projects/${encodeURIComponent(projectId)}/sources/${encodeURIComponent(sourceId)}/index`,
    {
      method: "POST",
      csrfToken,
    },
  )
}

export function getZoteroStatus(): Promise<ZoteroConnectionStatus> {
  return apiRequest<ZoteroConnectionStatus>("/integrations/zotero")
}

export function disconnectZotero(csrfToken: string): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>("/integrations/zotero", {
    method: "DELETE",
    csrfToken,
  })
}

export function listZoteroItems(
  projectId: string,
  query = "",
  start = 0,
  limit = 25,
): Promise<Record<string, unknown>> {
  const params = new URLSearchParams({ query, start: String(start), limit: String(limit) })
  return apiRequest<Record<string, unknown>>(
    `/projects/${encodeURIComponent(projectId)}/sources/zotero?${params.toString()}`,
  )
}

export function importZoteroItem(
  projectId: string,
  itemKey: string,
  csrfToken: string,
): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(
    `/projects/${encodeURIComponent(projectId)}/sources/import-zotero`,
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify({ item_key: itemKey }),
    },
  )
}
