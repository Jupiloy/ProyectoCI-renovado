import { StatusBadge } from "../base"
import type { ChapterSnapshotSummaryApi, ReviewComment } from "../../api/types"

/** Panel derecho del editor ("asistencia"): pestaña de versiones (snapshots
 * con SHA del contrato real) y pestaña de observaciones del asesor. */
export function PanelAsistencia({
  tab,
  onTab,
  snapshots,
  cargandoVersion,
  onAbrirVersion,
  comentarios,
  abiertas,
  resolviendoId,
  puedeResolver,
  onResolver,
}: {
  tab: "versiones" | "observaciones"
  onTab: (tab: "versiones" | "observaciones") => void
  snapshots: ChapterSnapshotSummaryApi[]
  cargandoVersion: boolean
  onAbrirVersion: (snapshotId: string) => void
  comentarios: ReviewComment[]
  abiertas: number
  resolviendoId: number | null
  puedeResolver: boolean
  onResolver: (c: ReviewComment) => void
}) {
  return (
    <aside className="editor-right">
      <div className="panel-tabs right-tabs">
        <button
          className={tab === "versiones" ? "active" : ""}
          onClick={() => onTab("versiones")}
        >
          Versiones {snapshots.length > 0 && <span>{snapshots.length}</span>}
        </button>
        <button
          className={tab === "observaciones" ? "active" : ""}
          onClick={() => onTab("observaciones")}
        >
          Observaciones {comentarios.length > 0 && <span>{abiertas}</span>}
        </button>
      </div>
      {tab === "versiones" ? (
        <div className="sources-panel">
          {cargandoVersion ? (
            <p className="aviso" role="status">Cargando versión…</p>
          ) : snapshots.length === 0 ? (
            <p className="aviso">
              Este capítulo no tiene versiones enviadas. Las versiones
              (snapshots) se crean al enviar el capítulo a revisión.
            </p>
          ) : (
            snapshots.map((s) => (
              <button
                className="chapter-row"
                key={s.id}
                onClick={() => onAbrirVersion(s.id)}
                title="Ver el contenido de esta versión"
              >
                <span className="chapter-number">{s.snapshot_no}</span>
                <div>
                  <strong>Versión de estado {s.state_version}</strong>
                  <small className="version-sha">
                    SHA {s.payload_sha256.slice(0, 12)}… ·{" "}
                    {new Date(s.created_at).toLocaleString()}
                  </small>
                </div>
              </button>
            ))
          )}
        </div>
      ) : (
        <div className="comments-list">
          {comentarios.length === 0 ? (
            <p className="aviso">
              No hay observaciones registradas para este capítulo.
            </p>
          ) : (
            comentarios.map((c) => (
              <article
                className={`advisor-comment ${c.status === "RESOLVED" ? "resolved" : ""}`}
                key={`${c.comment_id}:${c.snapshot_id ?? "base"}`}
              >
                <div className="comment-head">
                  <div className="avatar advisor-avatar">
                    {c.author.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <b>{c.author}</b>
                    <span>{new Date(c.created_at).toLocaleString()}</span>
                  </div>
                  <StatusBadge dot={false}>
                    {c.status === "OPEN" ? "Pendiente" : "Resuelta"}
                  </StatusBadge>
                </div>
                <p>{c.body}</p>
                {c.selected_text && <div className="anchored-quote">«{c.selected_text}»</div>}
                {c.status === "OPEN" && puedeResolver && (
                  <div className="comment-actions">
                    <button
                      className="text-link"
                      disabled={resolviendoId !== null}
                      onClick={() => onResolver(c)}
                    >
                      {resolviendoId === c.comment_id ? "Marcando…" : "Marcar como atendida"}
                    </button>
                  </div>
                )}
              </article>
            ))
          )}
          {!puedeResolver && comentarios.length > 0 && (
            <small className="version-sha">
              Las observaciones las crea y las resuelve el asesor del
              proyecto.
            </small>
          )}
        </div>
      )}
    </aside>
  )
}
