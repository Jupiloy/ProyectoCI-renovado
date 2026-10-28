import type {
  ChapterBlock,
  ChapterContentTree,
  ChapterDocument,
  ChapterSnapshotDetailApi,
  ProjectSummary,
} from "../../api/types"
import { BloquePaper } from "./BloquePaper"
import { PanelComparacion } from "./PanelComparacion"
import type { Loaded, ModoDocumento, SaveCitation } from "./tipos"

/** Área central del editor: avisos (error/aviso/vigencia), el documento como
 * bloques editables (con citas ancladas que bloquean el texto), el banner de
 * solo lectura según el modo, y la comparación de versiones ante conflicto. */
export function PanelDocumento({
  error,
  notice,
  esStale,
  serverDocument,
  loaded,
  draft,
  modoSoloLectura,
  modoDocumento,
  rol,
  snapshotDetalle,
  citasPorBloque,
  editable,
  busy,
  onSetBloque,
  onMoverBloque,
  onQuitarBloque,
  onInsertarCita,
  onRetirarCita,
  onConsultarVigente,
  onRecargar,
}: {
  error: string | null
  notice: string | null
  esStale: boolean
  serverDocument: ChapterDocument | null
  loaded: Loaded | null
  draft: ChapterContentTree | null
  modoSoloLectura: boolean
  modoDocumento: ModoDocumento
  rol: ProjectSummary["role"]
  snapshotDetalle: ChapterSnapshotDetailApi | null
  citasPorBloque: Map<string, SaveCitation[]>
  editable: boolean
  busy: boolean
  onSetBloque: (blockId: string, update: (block: ChapterBlock) => ChapterBlock) => void
  onMoverBloque: (index: number, delta: -1 | 1) => void
  onQuitarBloque: (blockId: string) => void
  onInsertarCita: (blockId: string, indexUtf16: number | null) => void
  onRetirarCita: (groupId: string) => void
  onConsultarVigente: () => void
  onRecargar: () => void
}) {
  return (
    <section className="document-area">
      <div className="page-ruler">
        <span /><span /><span /><span /><span />
      </div>
      {error && (
        <div className="aviso aviso-error" role="alert">
          {error}
          <span className="editor-recovery">
            <button className="button button-secondary" disabled={busy} onClick={onConsultarVigente}>
              Consultar versión vigente
            </button>
            <button
              className="button button-secondary"
              disabled={busy}
              onClick={onRecargar}
            >
              Recargar y descartar borrador
            </button>
          </span>
        </div>
      )}
      {notice && <div className="aviso" role="status">{notice}</div>}
      {esStale && (
        <div className="aviso">
          El documento se creó con un estado anterior del proyecto. Revisa su
          contenido antes de guardarlo.
        </div>
      )}
      {loaded && draft && (
        <article className={`paper ${modoSoloLectura ? "read-only" : ""}`}>
          {modoSoloLectura && (
            <div className="read-only-banner">
              {modoDocumento === "submitted"
                ? "Versión enviada: solo lectura"
                : modoDocumento === "snapshot"
                  ? "Snapshot histórico: solo lectura"
                  : rol !== "OWNER"
                    ? "El asesor puede consultar el documento, pero no editarlo."
                    : "Este capítulo está en estado de solo lectura."}
            </div>
          )}
          {modoDocumento !== "draft" && snapshotDetalle ? (
            <pre className="paper-snapshot">{snapshotDetalle.content_md}</pre>
          ) : (
            <>
              {draft.blocks.length === 0 && (
                <p className="aviso">Este capítulo aún no tiene texto guardado.</p>
              )}
              {draft.blocks.map((block, index) => (
                <BloquePaper
                  block={block}
                  index={index}
                  total={draft.blocks.length}
                  citas={citasPorBloque.get(block.id) ?? []}
                  editable={editable}
                  key={block.id}
                  onSetBloque={onSetBloque}
                  onMoverBloque={onMoverBloque}
                  onQuitarBloque={onQuitarBloque}
                  onInsertarCita={onInsertarCita}
                  onRetirarCita={onRetirarCita}
                />
              ))}
            </>
          )}
        </article>
      )}
      {serverDocument && loaded && (
        <PanelComparacion serverDocument={serverDocument} loaded={loaded} draft={draft} />
      )}
    </section>
  )
}
