import { apiDownload } from "./client"

export function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  window.URL.revokeObjectURL(url)
}

export async function downloadDraftDocx(projectId: string): Promise<string> {
  const { blob, filename } = await apiDownload(`/projects/${projectId}/export/draft.docx`)
  const targetName = filename || "tesis-borrador.docx"
  triggerBlobDownload(blob, targetName)
  return targetName
}

export async function downloadApprovedChapterDocx(
  projectId: string,
  chapterNo: number,
): Promise<string> {
  const { blob, filename } = await apiDownload(
    `/projects/${projectId}/chapters/${chapterNo}/export/approved.docx`,
  )
  const targetName = filename || `capitulo-${chapterNo}-aprobado.docx`
  triggerBlobDownload(blob, targetName)
  return targetName
}
