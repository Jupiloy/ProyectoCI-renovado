import type { ChapterState } from "../../api/types"
import { Button } from "../base"
import { etiquetaEstadoCapitulo } from "./etiquetas"

/** Cabecera de la revisión: volver al dashboard, estado real del capítulo y
 * decisiones (solicitar cambios / aprobar / reabrir con motivo). "Aprobar"
 * queda bloqueado mientras existan observaciones abiertas: el backend lo
 * exige, y así se explica en el tip visible. */
export function RevisionHeader({
  estado,
  capituloNo,
  nombreProyecto,
  procesando,
  hayObservacionesAbiertas,
  motivo,
  onMotivo,
  onVolver,
  onDecidir,
}: {
  estado: ChapterState | null
  capituloNo: number
  nombreProyecto: string
  procesando: string | null
  hayObservacionesAbiertas: boolean
  motivo: string
  onMotivo: (valor: string) => void
  onVolver: () => void
  onDecidir: (accion: "REQUEST_CHANGES" | "APPROVE" | "REOPEN") => void
}) {
  return (
    <div className="review-header">
      <div>
        <button className="back-button" onClick={onVolver}>
          <span>‹</span> Volver a proyectos
        </button>
        <div>
          <h1>{nombreProyecto} · Capítulo {capituloNo}</h1>
          <p>
            {estado
              ? `${etiquetaEstadoCapitulo(estado.status)} · Versión enviada ${estado.submitted_snapshot_id ? "disponible" : "no disponible"}`
              : "Sin estado"}
          </p>
        </div>
      </div>
      <div>
        <Button
          variant="secondary"
          disabled={procesando !== null || estado?.status !== "READY"}
          onClick={() => onDecidir("REQUEST_CHANGES")}
          title="Marca el capítulo con observaciones y lo devuelve al tesista"
        >
          Solicitar cambios
        </Button>
        <div className="approval-wrap">
          <Button
            disabled={
              procesando !== null ||
              estado?.status !== "READY" ||
              hayObservacionesAbiertas
            }
            onClick={() => onDecidir("APPROVE")}
          >
            Aprobar capítulo
          </Button>
          {estado?.status === "READY" && hayObservacionesAbiertas && (
            <div className="approval-tip">
              <b>No es posible aprobar todavía</b>
              <p>
                Resuelve o cierra las observaciones abiertas antes de aprobar
                (el backend lo exige).
              </p>
            </div>
          )}
        </div>
        {estado?.status === "APPROVED" && (
          <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
            Motivo de reapertura
            <input value={motivo} onChange={(e) => onMotivo(e.target.value)} />
          </label>
        )}
        {estado?.status === "APPROVED" && (
          <Button
            variant="ghost"
            disabled={procesando !== null || !motivo.trim()}
            onClick={() => onDecidir("REOPEN")}
          >
            Reabrir capítulo
          </Button>
        )}
      </div>
    </div>
  )
}
