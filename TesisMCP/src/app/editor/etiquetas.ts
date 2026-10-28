import { getWorkflowState } from "../../api/workflows"
import type { ChapterBlock, ChapterCitation, SourceDocument } from "../../api/types"
import type { PendingSave, SaveCitation } from "./tipos"

export const etiquetaPorEstado: Record<string, string> = {
  DRAFT: "Borrador",
  READY: "En revisión",
  CHANGES_REQUESTED: "Con observaciones",
  APPROVED: "Aprobado",
}

export function editableCitations(citations: ChapterCitation[] | undefined): SaveCitation[] {
  return (citations ?? []).map(({ group_id, block_id, position, sources }) => ({
    group_id,
    block_id,
    position,
    sources: sources.map(({ source_id, locator }) => ({ source_id, locator })),
  }))
}

export function isArtifact(block: ChapterBlock): block is Extract<ChapterBlock, { type: "data_table" | "figure" }> {
  return block.type === "data_table" || block.type === "figure"
}

/** Estado honesto del indicador de guardado (no cosmético: depende de la concurrencia real). */
export function estadoGuardado(args: {
  saving: boolean
  dirty: boolean
  pending: PendingSave | null
  writeBlocked: boolean
  serverChanged: boolean
  notice: string | null
}): string {
  if (args.saving) return "Guardando…"
  if (args.pending && args.serverChanged) return "Conflicto: existe una versión posterior"
  if (args.pending) return "Intento pendiente de confirmar"
  if (args.writeBlocked) return "Solo lectura"
  if (args.dirty) return "Cambios sin guardar"
  if (args.notice) return "Confirmado por el servidor"
  return "Sin cambios locales"
}

/** Números de capítulo del recorrido publicado (helper local de una sola llamada). */
export async function getWorkflowRecursos(projectId: string): Promise<{ numeros: number[] }> {
  const w = await getWorkflowState(projectId)
  const numeros = Array.from(
    new Set(
      (w.published?.tasks ?? [])
        .map((t) => t.chapter_no)
        .filter((n): n is number => typeof n === "number"),
    ),
  ).sort((a, b) => a - b)
  return { numeros }
}

export function etiquetaVerificacion(estado: SourceDocument["verification_status"]): string {
  switch (estado) {
    case "TEXT_CHECKED":
      return "Texto completo disponible"
    case "METADATA_CHECKED":
      return "Solo metadatos"
    case "UNVERIFIED_METADATA":
      return "Metadatos sin verificar"
    case "OCR_REQUIRED":
      return "OCR requerido"
    case "PENDING_EXTRACTION":
      return "Pendiente de extracción"
    case "REJECTED":
      return "Rechazado"
    default:
      return estado
  }
}
