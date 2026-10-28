import { getChapterSnapshot, resolveComment } from "../../api/reviews"
import type { ChapterSnapshotDetailApi, ReviewComment } from "../../api/types"
import type { EditorCtx, ModoDocumento } from "./tipos"

/**
 * Cambio de modo del documento: borrador editable, versión enviada al asesor
 * o snapshot histórico (solo lectura). Los modos no borrador cargan el
 * detalle del snapshot con el contrato real del backend.
 */
export async function abrirModo(ctx: EditorCtx, modo: ModoDocumento, snapshotId?: string) {
  if (modo === ctx.modoDocumento && !snapshotId) return
  if (modo === "draft") {
    ctx.setModoDocumento("draft")
    ctx.setSnapshotDetalle(null)
    ctx.setNotice(null)
    ctx.setError(null)
    return
  }
  if (!ctx.loaded) return
  const objetivo =
    modo === "submitted"
      ? ctx.loaded.state.submitted_snapshot_id
      : modo === "snapshot"
        ? (snapshotId ?? null)
        : null
  if (!objetivo) {
    ctx.setNotice(
      modo === "submitted"
        ? "Este capítulo aún no tiene una versión enviada al asesor."
        : "Este capítulo aún no tiene versiones guardadas.",
    )
    return
  }
  ctx.setCargandoVersion(true)
  ctx.setError(null)
  try {
    const detalle = (await getChapterSnapshot(ctx.proyecto.project_id, ctx.numeroCapitulo as number, objetivo)) as unknown as ChapterSnapshotDetailApi
    ctx.setSnapshotDetalle(detalle)
    ctx.setModoDocumento(modo)
  } catch (cause) {
    ctx.setError(cause instanceof Error ? cause.message : "No se pudo cargar la versión.")
  } finally {
    ctx.setCargandoVersion(false)
  }
}

/** Marca una observación como atendida (solo el rol asesor puede hacerlo). */
export async function resolverObservacion(ctx: EditorCtx, c: ReviewComment) {
  if (!ctx.proyecto.permissions.can_review_chapters || ctx.resolviendoId !== null) return
  ctx.setResolviendoId(c.comment_id)
  try {
    const actualizado = await resolveComment(ctx.proyecto.project_id, c.comment_id, ctx.csrfToken)
    ctx.setComentarios((lista) =>
      lista.map((item) => (item.comment_id === actualizado.comment_id ? { ...item, status: actualizado.status } : item)),
    )
  } catch (cause) {
    ctx.setError(cause instanceof Error ? cause.message : "No se pudo resolver la observación.")
  } finally {
    ctx.setResolviendoId(null)
  }
}
