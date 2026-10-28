import type { RefObject } from "react"
import type { ChapterSnapshotDetailApi } from "../../api/types"
import { Button } from "../base"
import type { Anclaje } from "./anclaje"

/** Área del documento en revisión: solo lectura, con captura de selección
 * (mouseup) para anclar una nueva observación al snapshot vigente. */
export function DocumentoRevision({
  detalle,
  anclaje,
  motivo,
  onMotivo,
  procesando,
  textoRef,
  onCapturarAnclaje,
  onRegistrarObservacion,
  onCancelarAnclaje,
}: {
  detalle: ChapterSnapshotDetailApi | null
  anclaje: Anclaje | null
  motivo: string
  onMotivo: (valor: string) => void
  procesando: string | null
  textoRef: RefObject<HTMLDivElement | null>
  onCapturarAnclaje: () => void
  onRegistrarObservacion: () => void
  onCancelarAnclaje: () => void
}) {
  return (
    <section className="review-document-area">
      {detalle ? (
        <>
          {anclaje && (
            <div className="decision-action-box">
              <b>Nueva observación sobre «{anclaje.selected_text.slice(0, 40)}…»</b>
              <textarea
                placeholder="Contenido de la observación (1 a 5000 caracteres)"
                maxLength={5000}
                value={motivo}
                onChange={(e) => onMotivo(e.target.value)}
              />
              <div className="decision-actions">
                <Button disabled={procesando !== null} onClick={onRegistrarObservacion}>
                  {procesando === "comentario" ? "Registrando…" : "Registrar observación"}
                </Button>
                <Button variant="secondary" onClick={onCancelarAnclaje}>
                  Cancelar
                </Button>
              </div>
            </div>
          )}
          <div ref={textoRef} onMouseUp={onCapturarAnclaje}>
            <article className="paper review-paper">
              <pre className="paper-snapshot">{detalle.content_md}</pre>
            </article>
          </div>
          <small className="aviso">
            Documento de solo lectura para el asesor. Selecciona un fragmento
            para anclar una observación al snapshot vigente.
          </small>
        </>
      ) : (
        <p className="aviso">
          Este capítulo no tiene una versión enviada que pueda recibir
          observaciones. El tesista debe enviarlo a revisión primero.
        </p>
      )}
    </section>
  )
}
