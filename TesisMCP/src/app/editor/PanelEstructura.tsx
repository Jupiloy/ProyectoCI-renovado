import type { ChapterState, SourceDocument } from "../../api/types"
import { Icon, StatusBadge } from "../base"
import { etiquetaVerificacion } from "./etiquetas"

/** Panel izquierdo del editor: navegación de capítulos del recorrido
 * publicado con sus pasos de metodología, y pestaña de fuentes reales. */
export function PanelEstructura({
  numerosCapitulo,
  numeroCapitulo,
  onCambiarCapitulo,
  loaded,
  fuentes,
  tab,
  onTab,
}: {
  numerosCapitulo: number[]
  numeroCapitulo: number | null
  onCambiarCapitulo: (numero: number) => void
  loaded: { state: ChapterState } | null
  fuentes: SourceDocument[] | null
  tab: "estructura" | "fuentes"
  onTab: (tab: "estructura" | "fuentes") => void
}) {
  return (
    <aside className="editor-left">
      <div className="panel-tabs">
        <button
          className={tab === "estructura" ? "active" : ""}
          onClick={() => onTab("estructura")}
        >
          Estructura
        </button>
        <button
          className={tab === "fuentes" ? "active" : ""}
          onClick={() => onTab("fuentes")}
        >
          Fuentes {fuentes && <span>{fuentes.length}</span>}
        </button>
      </div>
      {tab === "estructura" ? (
        <div className="outline-tree">
          <div className="outline-progress">
            <span>
              {numerosCapitulo.length} capítulos con pasos del recorrido
            </span>
          </div>
          {numerosCapitulo.map((n) => (
            <button
              key={n}
              className={n === numeroCapitulo ? "outline-chapter active" : "outline-chapter"}
              onClick={() => onCambiarCapitulo(n)}
            >
              <Icon name="chevron" size={13} />
              <span>
                <b>Capítulo {n}</b>
              </span>
            </button>
          ))}
          {loaded && (
            <div className="outline-steps">
              {loaded.state.steps.length === 0 ? (
                <small className="version-sha">
                  Este capítulo no tiene pasos de metodología asignados.
                </small>
              ) : (
                loaded.state.steps.map((paso) => (
                  <button key={paso.step_code} className={paso.status === "COMPLETED" ? "done" : undefined}>
                    <span>{paso.status === "COMPLETED" ? "✓" : "•"}</span>
                    {paso.step_code}
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="sources-panel">
          {fuentes === null ? (
            <p className="aviso">No se pudo listar las fuentes del proyecto.</p>
          ) : fuentes.length === 0 ? (
            <p className="aviso">Aún no hay fuentes cargadas en el proyecto.</p>
          ) : (
            fuentes.map((f) => (
              <label className="source-row compact" key={f.source_id}>
                <span className="pdf-icon">PDF</span>
                <span className="source-copy">
                  <b>{f.title || f.display_label}</b>
                  <small>{f.authors && f.authors.length > 0 ? f.authors.join(", ") : f.display_label}</small>
                  <StatusBadge dot={false}>{etiquetaVerificacion(f.verification_status)}</StatusBadge>
                </span>
              </label>
            ))
          )}
        </div>
      )}
    </aside>
  )
}
