import { StatusBadge } from "../base"
import type { ReviewComment } from "../../api/types"

/** Comentarios marginales de la revisión: listado con estado (Pendiente/
 * Resuelta), cita anclada y acción "Marcar como atendida". */
export function ComentariosMarginales({
  comentarios,
  abiertas,
  procesando,
  onResolver,
}: {
  comentarios: ReviewComment[]
  abiertas: number
  procesando: string | null
  onResolver: (c: ReviewComment) => void
}) {
  return (
    <aside className="margin-comments">
      <div className="comments-summary">
        <b>Comentarios marginales</b>
        <span>{abiertas} abiertos</span>
      </div>
      <div className="comments-list">
        {comentarios.length === 0 ? (
          <p className="aviso">Sin observaciones registradas.</p>
        ) : (
          comentarios.map((c) => (
            <article
              className={`advisor-comment ${c.status === "RESOLVED" ? "resolved" : ""}`}
              key={`${c.comment_id}:${c.snapshot_id ?? "base"}`}
            >
              <div className="comment-head">
                <div className="avatar advisor-avatar">{c.author.slice(0, 2).toUpperCase()}</div>
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
              {c.status === "OPEN" && (
                <div className="comment-actions">
                  <button
                    className="text-link"
                    disabled={procesando !== null}
                    onClick={() => onResolver(c)}
                  >
                    Marcar como atendida
                  </button>
                </div>
              )}
            </article>
          ))
        )}
      </div>
    </aside>
  )
}
