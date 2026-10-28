import { apiDownload, apiRequest } from "./client"
import type {
  ResearchDataset,
  ResearchDatasetVersion,
  ResearchFigure,
  ResearchFigureVersion,
  TableRecipe,
  TableRecipeVersion,
} from "./types"

export async function listDatasets(projectId: string): Promise<ResearchDataset[]> {
  const res = await apiRequest<{ datasets: ResearchDataset[] }>(
    `/projects/${projectId}/datasets`,
  )
  return res.datasets
}

export async function createDataset(
  projectId: string,
  formData: FormData,
  csrfToken?: string,
): Promise<{ created: boolean; dataset_id: string; version_no: number }> {
  return apiRequest(`/projects/${projectId}/datasets`, {
    method: "POST",
    body: formData,
    csrfToken,
  })
}

export async function listDatasetVersions(
  projectId: string,
  datasetId: string,
): Promise<ResearchDatasetVersion[]> {
  const res = await apiRequest<{ versions: ResearchDatasetVersion[] }>(
    `/projects/${projectId}/datasets/${datasetId}/versions`,
  )
  return res.versions
}

export async function getDatasetVersion(
  projectId: string,
  datasetId: string,
  versionNo: number,
): Promise<ResearchDatasetVersion> {
  return apiRequest<ResearchDatasetVersion>(
    `/projects/${projectId}/datasets/${datasetId}/versions/${versionNo}`,
  )
}

export async function addDatasetVersion(
  projectId: string,
  datasetId: string,
  formData: FormData,
  csrfToken?: string,
): Promise<{ created: boolean; version_no: number }> {
  return apiRequest(`/projects/${projectId}/datasets/${datasetId}/versions`, {
    method: "POST",
    body: formData,
    csrfToken,
  })
}

export async function downloadDatasetFile(
  projectId: string,
  datasetId: string,
  versionNo: number,
): Promise<{ blob: Blob; filename?: string }> {
  return apiDownload(
    `/projects/${projectId}/datasets/${datasetId}/versions/${versionNo}/download`,
  )
}

export async function listTableRecipes(
  projectId: string,
  datasetId: string,
  versionNo: number,
): Promise<TableRecipe[]> {
  const res = await apiRequest<{ recipes: TableRecipe[] }>(
    `/projects/${projectId}/datasets/${datasetId}/versions/${versionNo}/table-recipes`,
  )
  return res.recipes
}

export async function createTableRecipe(
  projectId: string,
  datasetId: string,
  versionNo: number,
  payload: {
    name: string
    spec: Record<string, unknown>
    idempotency_key: string
    expected_version?: number
  },
  csrfToken?: string,
): Promise<{ created: boolean; recipe_id: string; version_no: number; recipe_version: TableRecipeVersion }> {
  return apiRequest(
    `/projects/${projectId}/datasets/${datasetId}/versions/${versionNo}/table-recipes`,
    {
      method: "POST",
      body: JSON.stringify(payload),
      csrfToken,
    },
  )
}

export async function listTableRecipeVersions(
  projectId: string,
  datasetId: string,
  recipeId: string,
): Promise<TableRecipeVersion[]> {
  const res = await apiRequest<{ versions: TableRecipeVersion[] }>(
    `/projects/${projectId}/datasets/${datasetId}/table-recipes/${recipeId}/versions`,
  )
  return res.versions
}

export async function getTableRecipeVersion(
  projectId: string,
  datasetId: string,
  recipeId: string,
  versionNo: number,
): Promise<TableRecipeVersion> {
  return apiRequest<TableRecipeVersion>(
    `/projects/${projectId}/datasets/${datasetId}/table-recipes/${recipeId}/versions/${versionNo}`,
  )
}

export async function listFigures(
  projectId: string,
  datasetId: string,
  recipeId: string,
  tableVersionNo: number,
): Promise<ResearchFigure[]> {
  const res = await apiRequest<{ figures: ResearchFigure[] }>(
    `/projects/${projectId}/datasets/${datasetId}/table-recipes/${recipeId}/versions/${tableVersionNo}/figures`,
  )
  return res.figures
}

export async function createFigure(
  projectId: string,
  datasetId: string,
  recipeId: string,
  tableVersionNo: number,
  payload: {
    name: string
    spec: Record<string, unknown>
    idempotency_key: string
    expected_version?: number
    accept_truncated_input?: boolean
  },
  csrfToken?: string,
): Promise<{ created: boolean; figure_id: string; version_no: number; figure_version: ResearchFigureVersion }> {
  return apiRequest(
    `/projects/${projectId}/datasets/${datasetId}/table-recipes/${recipeId}/versions/${tableVersionNo}/figures`,
    {
      method: "POST",
      body: JSON.stringify(payload),
      csrfToken,
    },
  )
}

export async function listFigureVersions(
  projectId: string,
  datasetId: string,
  figureId: string,
): Promise<ResearchFigureVersion[]> {
  const res = await apiRequest<{ versions: ResearchFigureVersion[] }>(
    `/projects/${projectId}/datasets/${datasetId}/figures/${figureId}/versions`,
  )
  return res.versions
}

export async function getFigureVersion(
  projectId: string,
  datasetId: string,
  figureId: string,
  versionNo: number,
): Promise<ResearchFigureVersion> {
  return apiRequest<ResearchFigureVersion>(
    `/projects/${projectId}/datasets/${datasetId}/figures/${figureId}/versions/${versionNo}`,
  )
}

export function getFigurePreviewUrl(
  projectId: string,
  datasetId: string,
  figureId: string,
  versionNo: number,
): string {
  return `/api/v1/projects/${projectId}/datasets/${datasetId}/figures/${figureId}/versions/${versionNo}/preview.png`
}
