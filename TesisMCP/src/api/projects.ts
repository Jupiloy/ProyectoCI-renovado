import { apiRequest } from "./client"
import type { ProjectPage, ProjectState } from "./types"

export function listProjects(offset = 0, limit = 50): Promise<ProjectPage> {
  const query = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  return apiRequest<ProjectPage>(`/projects?${query.toString()}`)
}

export function createProject(
  name: string,
  title: string | undefined,
  csrfToken: string,
): Promise<ProjectState> {
  return apiRequest<ProjectState>("/projects", {
    method: "POST",
    csrfToken,
    body: JSON.stringify({ name, ...(title ? { title } : {}) }),
  })
}

export function getProject(projectId: string): Promise<ProjectState> {
  return apiRequest<ProjectState>(`/projects/${encodeURIComponent(projectId)}`)
}
