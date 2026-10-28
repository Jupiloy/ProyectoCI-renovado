import { useState } from "react"
import type { ChapterBlock, SourceDocument } from "../../api/types"
import { utf16ACodePoints } from "./citas"
import { etiquetaVerificacion } from "./etiquetas"
import { Button } from "../base"

/**
 * Modal de inserción de cita IEEE sobre un párrafo del borrador: elige una
 * fuente de la biblioteca del proyecto (ya cargada en el editor), un
 * localizador opcional (hasta 200 caracteres) y confirma. La posición es la
 * del cursor del párrafo (o el final del texto); la conversión UTF-16 →
 * puntos de código la hace la lógica de citas. Honestidad declarada: esta
 * interfaz inserta un grupo de una sola fuente (el backend admite hasta 20
 * por grupo) y la cita solo se confirma en el servidor al guardar la versión.
 */
export function ModalCita({
  bloque,
  indexUtf16,
  fuentes,
  onCancelar,
  onConfirmar,
}: {
  bloque: ChapterBlock
  /** selectionStart capturado en el párrafo (UTF-16); null = final del texto. */
  indexUtf16: number | null
  fuentes: SourceDocument[] | null
  onCancelar: () => void
  onConfirmar: (sourceId: string, locator: string) => void
}) {
  const [filtro, setFiltro] = useState("")
  const [sourceId, setSourceId] = useState("")
  const [locator, setLocator] = useState("")

  if (bloque.type !== "paragraph") return null
  const texto = bloque.text
  const posicion = utf16ACodePoints(texto, indexUtf16 ?? texto.length)
  const coinciden = (fuentes ?? []).filter((f) =>
    (f.title || "").toLowerCase().includes(filtro.trim().toLowerCase()),
  )
  const seleccionada = (fuentes ?? []).find((f) => f.source_id === sourceId) ?? null

  return (
    <div className="workflow-modal-backdrop" onClick={onCancelar}>
      <section
        className="workflow-modal-card"
        role="dialog"
        aria-label="Insertar cita"
        onClick={(e) => e.stopPropagation()}
      >
        <h2>Insertar cita en el párrafo</h2>
        <p>La cita se ancla a este párrafo y usa la fuente elegida de la biblioteca del proyecto</p>
        <blockquote className="anchored-quote">
          «{texto.length > 160 ? `${texto.slice(0, 160)}…` : texto || "(párrafo vacío)"}»
        </blockquote>
        <small className="version-sha">
          Posición de anclaje: carácter {posicion} del párrafo (offset Unicode;{" "}
          {indexUtf16 === null ? "final del texto" : "posición del cursor"}).
        </small>
        {!fuentes || fuentes.length === 0 ? (
          <p className="aviso">
            La biblioteca del proyecto no tiene fuentes todavía. Importa o
            registra fuentes en la pestaña Fuentes antes de citar.
          </p>
        ) : (
          <div className="artifact-picker">
            <label>
              Filtrar fuentes
              <input
                type="text"
                maxLength={120}
                placeholder="Filtrar por título…"
                value={filtro}
                onChange={(e) => setFiltro(e.target.value)}
              />
            </label>
            <label>
              Fuente citada
              <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
                <option value="">— Elegir fuente —</option>
                {coinciden.map((f) => (
                  <option key={f.source_id} value={f.source_id}>
                    {f.title || "(sin título)"} ({etiquetaVerificacion(f.verification_status)})
                  </option>
                ))}
              </select>
            </label>
            <label>
              Localizador (opcional, hasta 200 caracteres)
              <input
                type="text"
                maxLength={200}
                placeholder="p. ej. p. 23, §4.2, tabla 1"
                value={locator}
                onChange={(e) => setLocator(e.target.value)}
              />
            </label>
            <small className="version-sha">
              {seleccionada
                ? `Cita de una sola fuente en un grupo (el backend admite hasta 20 fuentes por grupo). La numeración IEEE se asigna por primera aparición en la revisión confirmada.`
                : "La numeración IEEE se asigna por primera aparición en la revisión confirmada."}{" "}
              La cita queda local hasta guardar la versión del capítulo.
            </small>
            <div className="workflow-task-actions">
              <Button variant="secondary" onClick={onCancelar}>
                Cancelar
              </Button>
              <Button
                disabled={!sourceId}
                title={sourceId ? "Preparar la cita local" : "Elegir una fuente"}
                onClick={() => onConfirmar(sourceId, locator)}
              >
                Preparar cita
              </Button>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
