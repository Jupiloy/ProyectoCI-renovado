import type { Dispatch, SetStateAction } from "react"
import type { SaveChapterInput } from "../../api/chapters"
import type {
  ChapterContentTree,
  ChapterDocument,
  ChapterSnapshotDetailApi,
  ChapterSnapshotSummaryApi,
  ChapterState,
  ProjectSummary,
  ReviewComment,
} from "../../api/types"

export type Loaded = { state: ChapterState; document: ChapterDocument }
export type ModoDocumento = "draft" | "submitted" | "snapshot"
export type SaveCitation = SaveChapterInput["citations"][number]
export type PendingSave = SaveChapterInput

/**
 * Contexto de una renderización del editor: lecturas del render actual más
 * setters estables. Las acciones (guardado, versiones, observaciones) lo
 * reciben como parámetro explícito para mantener la lógica en archivos
 * separados del JSX, con la misma semántica de cierre que tenía la versión
 * monolítica (el objeto se construye en el render vigente y se consume en el
 * momento del evento, sin valores retardados).
 */
export interface EditorCtx {
  proyecto: ProjectSummary
  csrfToken: string
  numeroCapitulo: number | null
  loaded: Loaded | null
  draft: ChapterContentTree | null
  pending: PendingSave | null
  /** Citas agregadas o retiradas localmente; null = el manifiesto del documento cargado. */
  citasLocales: SaveCitation[] | null
  busy: boolean
  writable: boolean
  needsSave: boolean
  hasLocalWork: boolean
  modoDocumento: ModoDocumento
  resolviendoId: number | null
  loadSequence: { current: number }
  cargarCapitulo: (numero: number) => Promise<void>
  onUnauthorized: () => void
  onAccessLost: () => void
  onRefreshCsrf: () => Promise<void>
  setLoaded: Dispatch<SetStateAction<Loaded | null>>
  setDraft: Dispatch<SetStateAction<ChapterContentTree | null>>
  setPending: Dispatch<SetStateAction<PendingSave | null>>
  setWriteBlocked: Dispatch<SetStateAction<boolean>>
  setServerDocument: Dispatch<SetStateAction<ChapterDocument | null>>
  setLoading: Dispatch<SetStateAction<boolean>>
  setSaving: Dispatch<SetStateAction<boolean>>
  setError: Dispatch<SetStateAction<string | null>>
  setNotice: Dispatch<SetStateAction<string | null>>
  setSnapshots: Dispatch<SetStateAction<ChapterSnapshotSummaryApi[]>>
  setSnapshotDetalle: Dispatch<SetStateAction<ChapterSnapshotDetailApi | null>>
  setCargandoVersion: Dispatch<SetStateAction<boolean>>
  setComentarios: Dispatch<SetStateAction<ReviewComment[]>>
  setResolviendoId: Dispatch<SetStateAction<number | null>>
  setModoDocumento: Dispatch<SetStateAction<ModoDocumento>>
  setNumeroCapitulo: Dispatch<SetStateAction<number | null>>
  setCitasLocales: Dispatch<SetStateAction<SaveCitation[] | null>>
}
