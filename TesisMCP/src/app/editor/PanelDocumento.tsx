import type {
  ChapterBlock,
  ChapterCitation,
  ChapterContentTree,
  ChapterDocument,
  ChapterSnapshotDetailApi,
  ProjectSummary,
} from "../../api/types"
import { isArtifact } from "./etiquetas"
import { PanelComparacion } from "./PanelComparacion"
import type { Loaded, ModoDocumento } from "./tipos"

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
  citasPorBloque: Map<string, ChapterCitation[]>
  editable: boolean
  busy: boolean
  onSetBloque: (blockId: string, update: (block: ChapterBlock) => ChapterBlock) => void
  onMoverBloque: (index: number, delta: -1 | 1) => void
  onQuitarBloque: (blockId: string) => void
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
              {draft.blocks.map((block, index) => {
                const citas = citasPorBloque.get(block.id) ?? []
                const anclado = citas.length > 0
                const esArtefacto = isArtifact(block)
                return (
                  <div className="paper-block" key={block.id}>
                    {esArtefacto ? (
                      <div className="paper-artifact">
                        <b>{block.type === "data_table" ? "Tabla" : "Figura"}: {block.caption}</b>
                        <small>
                          Artefacto vinculado ·{" "}
                          {block.type === "data_table" ? block.table_version_id : block.figure_version_id}
                        </small>
                      </div>
                    ) : block.type === "heading" ? (
                      <div className="paper-heading-block">
                        <select
                          aria-label="Nivel del encabezado"
                          value={block.level}
                          disabled={!editable || anclado}
                          onChange={(e) =>
                            onSetBloque(block.id, (item) =>
                              item.type === "heading" ? { ...item, level: Number(e.target.value) } : item,
                            )
                          }
                        >
                          {[1, 2, 3, 4, 5, 6].map((nivel) => (
                            <option key={nivel} value={nivel}>Nivel {nivel}</option>
                          ))}
                        </select>
                        <textarea
                          aria-label="Texto del encabezado"
                          className="paper-block-textarea heading"
                          value={block.text}
                          maxLength={20000}
                          disabled={!editable || anclado}
                          onChange={(e) =>
                            onSetBloque(block.id, (item) =>
                              item.type === "heading" ? { ...item, text: e.target.value } : item,
                            )
                          }
                        />
                      </div>
                    ) : "items" in block ? (
                      <textarea
                        aria-label="Elementos de lista, uno por línea"
                        className="paper-block-textarea"
                        value={block.items.join("\n")}
                        disabled={!editable}
                        onChange={(e) =>
                          onSetBloque(block.id, (item) =>
                            "items" in item ? { ...item, items: e.target.value.split("\n") } : item,
                          )
                        }
                      />
                    ) : (
                      <textarea
                        aria-label="Texto del bloque"
                        className={`paper-block-textarea ${block.type === "paragraph" ? "" : block.type}`}
                        value={block.text}
                        maxLength={20000}
                        disabled={!editable || anclado}
                        onChange={(e) =>
                          onSetBloque(block.id, (item) =>
                            "text" in item ? { ...item, text: e.target.value } : item,
                          )
                        }
                      />
                    )}
                    {anclado && (
                      <small className="paper-citations">
                        Cita anclada: posición {citas.map((c) => c.position).join(", ")} · el texto está bloqueado
                        para no desplazar el offset Unicode de la cita.
                      </small>
                    )}
                    {editable && !esArtefacto && (
                      <span className="paper-block-actions">
                        <button aria-label="Mover bloque arriba" disabled={index === 0} onClick={() => onMoverBloque(index, -1)}>↑</button>
                        <button aria-label="Mover bloque abajo" disabled={index === draft!.blocks.length - 1} onClick={() => onMoverBloque(index, 1)}>↓</button>
                        <button
                          aria-label="Eliminar bloque"
                          title={anclado ? "No se puede eliminar mientras tenga citas" : "Eliminar bloque"}
                          disabled={anclado}
                          onClick={() => onQuitarBloque(block.id)}
                        >
                          ×
                        </button>
                      </span>
                    )}
                  </div>
                )
              })}
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
