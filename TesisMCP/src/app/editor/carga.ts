import { useCallback } from "react"
import type { Dispatch, SetStateAction } from "react"
import { ApiError } from "../../api/client"
import { getChapterDocument, getChapterState } from "../../api/chapters"
import { listChapterSnapshots, listComments } from "../../api/reviews"
import type {
  ChapterDocument,
  ChapterSnapshotDetailApi,
  ChapterSnapshotSummaryApi,
  ChapterState,
  ChapterContentTree,
  ReviewComment,
} from "../../api/types"
import { unsupportedDocumentReason } from "../editorDocument"
import type { Loaded, ModoDocumento, PendingSave } from "./tipos"

/**
 * Carga de un capítulo del editor: estado + documento + versiones (snapshots
 * con el contrato real) + comentarios, con guardia de secuencia para descartar
 * respuestas atrasadas. Devuelve callbacks estables con las mismas
 * dependencias que tenía la versión monolítica de VistaEditor, de modo que el
 * efecto de carga se comporta exactamente igual.
 */
export function useCargaCapitulo(args: {
  projectId: string
  onUnauthorized: () => void
  onAccessLost: () => void
  loadSequence: { current: number }
  setLoading: Dispatch<SetStateAction<boolean>>
  setError: Dispatch<SetStateAction<string | null>>
  setNotice: Dispatch<SetStateAction<string | null>>
  setPending: Dispatch<SetStateAction<PendingSave | null>>
  setWriteBlocked: Dispatch<SetStateAction<boolean>>
  setServerDocument: Dispatch<SetStateAction<ChapterDocument | null>>
  setSnapshotDetalle: Dispatch<SetStateAction<ChapterSnapshotDetailApi | null>>
  setModoDocumento: Dispatch<SetStateAction<ModoDocumento>>
  setLoaded: Dispatch<SetStateAction<Loaded | null>>
  setDraft: Dispatch<SetStateAction<ChapterContentTree | null>>
  setSnapshots: Dispatch<SetStateAction<ChapterSnapshotSummaryApi[]>>
  setComentarios: Dispatch<SetStateAction<ReviewComment[]>>
}) {
  const {
    projectId,
    onUnauthorized,
    onAccessLost,
    loadSequence,
    setLoading,
    setError,
    setNotice,
    setPending,
    setWriteBlocked,
    setServerDocument,
    setSnapshotDetalle,
    setModoDocumento,
    setLoaded,
    setDraft,
    setSnapshots,
    setComentarios,
  } = args

  const cargarComentarios = useCallback(
    async (capitulo: number) => {
      // El módulo legacy de demo (src/features/) comparte listChapterSnapshots con el
      // contrato antiguo; aquí se ajusta al contrato real del backend sin tocarlo.
      const resumen = (await listChapterSnapshots(projectId, capitulo)) as unknown as ChapterSnapshotSummaryApi[]
      const base = await listComments(projectId, capitulo)
      const detalle = await Promise.allSettled(
        resumen.map((s) => listComments(projectId, capitulo, s.id)),
      )
      const porSnapshot = detalle
        .map((r) => (r.status === "fulfilled" ? (r as PromiseFulfilledResult<ReviewComment[]>).value : []))
        .flat()
      const vistos = new Set(porSnapshot.map((c) => c.comment_id))
      return {
        snapshots: resumen,
        comentarios: [
          ...base.filter((c) => !vistos.has(c.comment_id)),
          ...porSnapshot,
        ],
      }
    },
    [projectId],
  )

  const cargarCapitulo = useCallback(
    async (numero: number) => {
      const secuencia = ++loadSequence.current
      setLoading(true)
      setError(null)
      setNotice(null)
      setPending(null)
      setWriteBlocked(false)
      setServerDocument(null)
      setSnapshotDetalle(null)
      setModoDocumento("draft")
      try {
        const [state, document, versiones] = await Promise.all([
          getChapterState(projectId, numero) as Promise<ChapterState>,
          getChapterDocument(projectId, numero) as Promise<ChapterDocument>,
          cargarComentarios(numero),
        ])
        if (secuencia !== loadSequence.current) return
        if (state.chapter_no !== numero || document.chapter_no !== numero) {
          throw new Error("El backend respondió con otro capítulo.")
        }
        const incompatible = unsupportedDocumentReason(document)
        setLoaded({ state, document })
        setDraft(incompatible ? null : structuredClone(document.content_tree))
        setSnapshots(versiones.snapshots)
        setComentarios(versiones.comentarios)
        if (incompatible) setError(incompatible)
      } catch (cause) {
        if (secuencia !== loadSequence.current) return
        if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
        if (cause instanceof ApiError && cause.status === 404) onAccessLost()
        setLoaded(null)
        setDraft(null)
        setError(cause instanceof Error ? cause.message : "No se pudo cargar el capítulo.")
      } finally {
        if (secuencia === loadSequence.current) setLoading(false)
      }
    },
    [projectId, onUnauthorized, onAccessLost, cargarComentarios, loadSequence],
  )

  return { cargarComentarios, cargarCapitulo }
}
