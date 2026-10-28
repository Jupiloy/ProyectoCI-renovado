import { useCallback } from "react"
import type { Dispatch, SetStateAction } from "react"
import { ApiError } from "../../api/client"
import { getChapterState } from "../../api/chapters"
import { getChapterSnapshot, listChapterSnapshots, listComments } from "../../api/reviews"
import type {
  ChapterSnapshotDetailApi,
  ChapterSnapshotSummaryApi,
  ChapterState,
  ReviewComment,
} from "../../api/types"
import type { Anclaje } from "./anclaje"

/**
 * Carga inicial de la revisión del asesor: estado del capítulo, snapshots con
 * el contrato real (el módulo legacy de demo en src/features/ comparte
 * getChapterSnapshot/listChapterSnapshots con el contrato antiguo; aquí se
 * ajusta sin tocarlo), comentarios y detalle del snapshot enviado. Con guardia
 * de secuencia para descartar respuestas atrasadas.
 */
export function useCargaRevision(args: {
  projectId: string
  onUnauthorized: () => void
  onAccessLost: () => void
  secuencia: { current: number }
  setEstado: Dispatch<SetStateAction<ChapterState | null>>
  setSnapshots: Dispatch<SetStateAction<ChapterSnapshotSummaryApi[]>>
  setComentarios: Dispatch<SetStateAction<ReviewComment[]>>
  setDetalle: Dispatch<SetStateAction<ChapterSnapshotDetailApi | null>>
  setAnclaje: Dispatch<SetStateAction<Anclaje | null>>
  setCargandoDatos: Dispatch<SetStateAction<boolean>>
  setError: Dispatch<SetStateAction<string | null>>
  setNotice: Dispatch<SetStateAction<string | null>>
}) {
  const {
    projectId,
    onUnauthorized,
    onAccessLost,
    secuencia,
    setEstado,
    setSnapshots,
    setComentarios,
    setDetalle,
    setAnclaje,
    setCargandoDatos,
    setError,
    setNotice,
  } = args

  const cargar = useCallback(
    async (n: number) => {
      const s = ++secuencia.current
      setCargandoDatos(true)
      setError(null)
      setNotice(null)
      setAnclaje(null)
      setDetalle(null)
      try {
        const [st, snaps, comms] = await Promise.all([
          getChapterState(projectId, n) as Promise<ChapterState>,
          listChapterSnapshots(projectId, n)
            .then((r) => r as unknown as ChapterSnapshotSummaryApi[])
            .catch(() => [] as ChapterSnapshotSummaryApi[]),
          listComments(projectId, n).catch(() => [] as ReviewComment[]),
        ])
        if (s !== secuencia.current) return
        setEstado(st)
        setSnapshots(snaps)
        setComentarios(comms)
        if (st.submitted_snapshot_id) {
          const det = (await getChapterSnapshot(projectId, n, st.submitted_snapshot_id)) as unknown as ChapterSnapshotDetailApi
          if (s !== secuencia.current) return
          setDetalle(det)
        }
      } catch (cause) {
        if (s !== secuencia.current) return
        if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
        else if (cause instanceof ApiError && cause.status === 404) onAccessLost()
        setEstado(null)
        setError(cause instanceof Error ? cause.message : "Error al cargar los datos de revisión.")
      } finally {
        if (s === secuencia.current) setCargandoDatos(false)
      }
    },
    [projectId, onUnauthorized, onAccessLost, secuencia],
  )

  return { cargar }
}
