import type { ChapterContentTree } from "../../api/types"
import { Icon } from "../base"
import { etiquetaPorEstado } from "./etiquetas"
import type { Loaded, ModoDocumento, PendingSave } from "./tipos"

/** Barra de título y toolbar del editor: selector de modo del documento,
 * indicador honesto de guardado, inserción de bloques y plegado de paneles. */
export function BarraSuperior({
  numeroCapitulo,
  loaded,
  modoDocumento,
  onAbrirModo,
  estadoGuardadoTexto,
  leftOpen,
  onAlternarIzquierdo,
  rightOpen,
  onAlternarDerecho,
  writable,
  busy,
  draft,
  saving,
  pending,
  needsSave,
  onAgregarBloque,
  onGuardar,
}: {
  numeroCapitulo: number | null
  loaded: Loaded | null
  modoDocumento: ModoDocumento
  onAbrirModo: (modo: ModoDocumento) => void
  estadoGuardadoTexto: string
  leftOpen: boolean
  onAlternarIzquierdo: () => void
  rightOpen: boolean
  onAlternarDerecho: () => void
  writable: boolean
  busy: boolean
  draft: ChapterContentTree | null
  saving: boolean
  pending: PendingSave | null
  needsSave: boolean
  onAgregarBloque: (type: "heading" | "paragraph" | "blockquote" | "code_block" | "bullet_list" | "ordered_list") => void
  onGuardar: () => void
}) {
  return (
    <>
      <div className="editor-titlebar">
        <div>
          <b>{numeroCapitulo !== null ? `Capítulo ${numeroCapitulo}` : "Editor"}</b>
          {loaded && (
            <span>
              Versión {loaded.document.document_version} ·{" "}
              {etiquetaPorEstado[loaded.state.status] ?? loaded.state.status}
            </span>
          )}
          <div className="document-modes">
            <button
              className={modoDocumento === "draft" ? "active" : ""}
              onClick={() => onAbrirModo("draft")}
            >
              Borrador editable
            </button>
            <button
              className={modoDocumento === "submitted" ? "active" : ""}
              onClick={() => onAbrirModo("submitted")}
            >
              Enviada al asesor
            </button>
            <button
              className={modoDocumento === "snapshot" ? "active" : ""}
              onClick={() => onAbrirModo("snapshot")}
            >
              Snapshot
            </button>
          </div>
        </div>
        <div className="document-status">
          <span className="save-dot" />
          {estadoGuardadoTexto}
        </div>
      </div>
      <div className="editor-toolbar">
        <button
          className="toolbar-label"
          onClick={onAlternarIzquierdo}
          aria-label="Plegar panel izquierdo"
        >
          <Icon name="library" size={16} />
          {leftOpen ? "Ocultar navegación" : "Mostrar navegación"}
        </button>
        <span className="toolbar-divider" />
        {writable && (
          <>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => onAgregarBloque("heading")}>Encabezado</button>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => onAgregarBloque("paragraph")}>Párrafo</button>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => onAgregarBloque("blockquote")}>Cita textual</button>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => onAgregarBloque("code_block")}>Código</button>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => onAgregarBloque("bullet_list")}>Lista</button>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => onAgregarBloque("ordered_list")}>Lista numerada</button>
            <span className="toolbar-divider" />
          </>
        )}
        <button
          className="button button-primary"
          disabled={busy || !writable || !needsSave}
          onClick={onGuardar}
        >
          {saving ? "Guardando…" : pending ? "Reintentar guardado" : "Guardar versión"}
        </button>
        <button
          className="toolbar-label panel-toggle-right"
          onClick={onAlternarDerecho}
          aria-label="Plegar panel derecho"
        >
          <Icon name="spark" size={16} />
          {rightOpen ? "Ocultar asistencia" : "Mostrar asistencia"}
        </button>
      </div>
    </>
  )
}
