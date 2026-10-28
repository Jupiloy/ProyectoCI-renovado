import type { ChapterSnapshotSummaryApi } from "../../api/types"

/** Historial de versiones enviadas del capítulo, con el SHA del payload del
 * contrato real (payload_sha256) y la fecha de creación. */
export function PanelVersionesAsesor({
  snapshots,
  detalleId,
  procesando,
  onAbrir,
}: {
  snapshots: ChapterSnapshotSummaryApi[]
  detalleId: string | null
  procesando: string | null
  onAbrir: (s: ChapterSnapshotSummaryApi) => void
}) {
  return (
    <aside className="version-panel">
      <div className="panel-heading">
        <b>Versiones enviadas</b>
      </div>
      {snapshots.length === 0 ? (
        <small className="aviso">
          Sin versiones enviadas todavía.
        </small>
      ) : (
        snapshots.map((s) => (
          <button
            className={detalleId === s.id ? "active" : undefined}
            key={s.id}
            disabled={procesando !== null && procesando === `version:${s.id}`}
            onClick={() => onAbrir(s)}
          >
            <span>Versión {s.snapshot_no}</span>
            <small>
              SHA {s.payload_sha256.slice(0, 12)}… · {new Date(s.created_at).toLocaleString()}
            </small>
          </button>
        ))
      )}
    </aside>
  )
}
