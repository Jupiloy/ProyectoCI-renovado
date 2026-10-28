import type { Dispatch, SetStateAction } from "react"
import { ApiError } from "../../api/client"
import { addComment, decideChapter, getChapterSnapshot, listComments, resolveComment } from "../../api/reviews"
import type {
  ChapterSnapshotDetailApi,
  ChapterSnapshotSummaryApi,
  ChapterState,
  ReviewComment,
} from "../../api/types"
import type { Anclaje } from "./anclaje"
import { etiquetaEstadoCapitulo } from "./etiquetas"

/**
 * Contexto del render vigente de la revisión del asesor: lecturas actuales y
 * setters estables; las acciones lo reciben explícito, con la misma semántica
 * de cierre que tenía la versión monolítica.
 */
export interface RevisionCtx {
  projectId: string
  capituloNo: number
  csrfToken: string
  procesando: string | null
  motivo: string
  anclaje: Anclaje | null
  setEstado: Dispatch<SetStateAction<ChapterState | null>>
  setDetalle: Dispatch<SetStateAction<ChapterSnapshotDetailApi | null>>
  setComentarios: Dispatch<SetStateAction<ReviewComment[]>>
  setAnclaje: Dispatch<SetStateAction<Anclaje | null>>
  setProcesando: Dispatch<SetStateAction<string | null>>
  setError: Dispatch<SetStateAction<string | null>>
  setNotice: Dispatch<SetStateAction<string | null>>
  setMotivo: Dispatch<SetStateAction<string>>
  onUnauthorized: () => void
  onAccessLost: () => void
  onRefreshCsrf: () => Promise<void>
  alRefrescar: () => Promise<void>
}

/** Abre un snapshot del historial y sus comentarios asociados. */
export async function abrirVersionEnviada(ctx: RevisionCtx, s: ChapterSnapshotSummaryApi) {
  ctx.setError(null)
  ctx.setAnclaje(null)
  ctx.setProcesando(`version:${s.id}`)
  try {
    const det = (await getChapterSnapshot(ctx.projectId, ctx.capituloNo, s.id)) as unknown as ChapterSnapshotDetailApi
    ctx.setDetalle(det)
    ctx.setComentarios(await listComments(ctx.projectId, ctx.capituloNo, s.id).catch(() => []))
  } catch (cause) {
    ctx.setError(cause instanceof Error ? cause.message : "No se pudo cargar la versión.")
  } finally {
    ctx.setProcesando(null)
  }
}

/** Registra la observación anclada al snapshot vigente (start_cp/end_cp en
 * puntos de código Unicode). */
export async function registrarObservacion(ctx: RevisionCtx) {
  const anclaje = ctx.anclaje
  if (!anclaje) return
  const cuerpo = (ctx.motivo || "").trim()
  if (!cuerpo) {
    ctx.setError("Escribe el contenido de la observación antes de registrarla.")
    return
  }
  ctx.setProcesando("comentario")
  ctx.setError(null)
  try {
    const creado = await addComment(ctx.projectId, ctx.capituloNo, {
      start_cp: anclaje.start_cp,
      end_cp: anclaje.end_cp,
      selected_text: anclaje.selected_text,
      body: cuerpo,
      snapshot_id: anclaje.snapshot_id,
    }, ctx.csrfToken)
    ctx.setComentarios((lista) => [...lista, creado])
    ctx.setAnclaje(null)
    ctx.setMotivo("")
    ctx.setNotice("Observación registrada sobre la versión enviada.")
  } catch (c2) {
    if (c2 instanceof ApiError && c2.status === 401) ctx.onUnauthorized()
    else if (c2 instanceof ApiError && c2.status === 404) ctx.onAccessLost()
    else ctx.setError(c2 instanceof Error ? c2.message : "No se pudo registrar la observación.")
  } finally {
    ctx.setProcesando(null)
  }
}

/** Decisión del asesor sobre el capítulo (cambios / aprobar / reabrir). */
export async function decidirCapitulo(ctx: RevisionCtx, accion: "REQUEST_CHANGES" | "APPROVE" | "REOPEN") {
  ctx.setProcesando(accion)
  ctx.setError(null)
  try {
    const nuevo = await decideChapter(ctx.projectId, ctx.capituloNo, accion, ctx.motivo, ctx.csrfToken)
    ctx.setEstado(nuevo)
    ctx.setMotivo("")
    ctx.setNotice(`Decisión registrada: ${etiquetaEstadoCapitulo(nuevo.status)}.`)
    await ctx.alRefrescar()
  } catch (c2) {
    if (c2 instanceof ApiError && c2.status === 401) ctx.onUnauthorized()
    else if (c2 instanceof ApiError && c2.status === 404) ctx.onAccessLost()
    else if (c2 instanceof ApiError && c2.kind === "csrf") {
      try { await ctx.onRefreshCsrf() } catch { /* conservar estado */ }
      ctx.setError("Falló la protección CSRF. Vuelve a intentar la decisión.")
    } else ctx.setError(c2 instanceof Error ? c2.message : "No se pudo registrar la decisión.")
  } finally {
    ctx.setProcesando(null)
  }
}

/** Marca una observación como atendida (RESOLVED). */
export async function resolverComentarioAsesor(ctx: RevisionCtx, c: ReviewComment) {
  if (ctx.procesando !== null) return
  ctx.setProcesando(`resolver:${c.comment_id}`)
  ctx.setError(null)
  try {
    const r = await resolveComment(ctx.projectId, c.comment_id, ctx.csrfToken)
    ctx.setComentarios((lista) =>
      lista.map((item) => (item.comment_id === r.comment_id ? { ...item, status: r.status } : item)),
    )
  } catch (c2) {
    ctx.setError(c2 instanceof Error ? c2.message : "No se pudo resolver la observación.")
  } finally {
    ctx.setProcesando(null)
  }
}
