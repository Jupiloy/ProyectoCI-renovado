import { useEffect, useMemo, useState } from "react"
import {
  listChapterSnapshots,
  listComments,
} from "../api/reviews"
import { getWorkflowState } from "../api/workflows"
import type {
  ChapterSnapshotSummary,
  ProjectSummary,
  ReviewComment,
} from "../api/types"
import { Icon, StatusBadge } from "./base"

/**
 * Vista «Revisión» del tesista (diseño de la maqueta de Figma, datos reales).
 * Lectura pura: observaciones del asesor y versiones (snapshots) por capítulo.
 * Escribir observaciones o decidir corresponde al asesor (bloque R5).
 */
export function VistaRevision({
  proyecto,
}: {
  proyecto: ProjectSummary
}) {
  const [numerosCapitulo, setNumerosCapitulo] = useState<number[]>([])
  const [numeroCapitulo, setNumeroCapitulo] = useState<number | null>(null)
  const [snapshots, setSnapshots] = useState<ChapterSnapshotSummary[]>([])
  const [comentarios, setComentarios] = useState<ReviewComment[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let vigente = true
    getWorkflowState(proyecto.project_id)
      .then((w) => {
        if (!vigente) return
        const numeros = Array.from(
          new Set(
            (w.published?.tasks ?? [])
              .map((t) => t.chapter_no)
              .filter((n): n is number => typeof n === "number"),
          ),
        ).sort((a, b) => a - b)
        setNumerosCapitulo(numeros)
        setNumeroCapitulo(numeros.length > 0 ? numeros[0] : null)
        if (numeros.length === 0) setCargando(false)
      })
      .catch((cause) => {
        if (vigente) {
          setError(cause instanceof Error ? cause.message : "No se pudo cargar el recorrido del proyecto.")
          setCargando(false)
        }
      })
    return () => {
      vigente = false
    }
  }, [proyecto.project_id])

  useEffect(() => {
    if (numeroCapitulo === null) return
    let vigente = true
    async function cargar() {
      setCargando(true)
      setError("")
      const resumen = await listChapterSnapshots(proyecto.project_id, numeroCapitulo as number)
      const comentariosCap = await listComments(proyecto.project_id, numeroCapitulo as number)
      if (!vigente) return
      const detalle = await Promise.allSettled(
        resumen.map((s) => listComments(proyecto.project_id, numeroCapitulo as number, s.snapshot_id)),
      )
      if (!vigente) return
      const comentariosPorSnapshot = detalle
        .map((r) => (r.status === "fulfilled" ? (r as PromiseFulfilledResult<ReviewComment[]>).value : []))
        .flat()
      const vistos = new Set(comentariosPorSnapshot.map((c) => c.comment_id))
      const unificados = [
        ...comentariosCap.filter((c) => !vistos.has(c.comment_id)),
        ...comentariosPorSnapshot,
      ]
      setSnapshots(resumen)
      setComentarios(unificados)
      setCargando(false)
    }
    cargar().catch((cause) => {
      if (vigente) {
        setError(cause instanceof Error ? cause.message : "No se pudo cargar la revisión del capítulo.")
        setCargando(false)
      }
    })
    return () => {
      vigente = false
    }
  }, [proyecto.project_id, numeroCapitulo])

  const abiertos = useMemo(
    () => comentarios.filter((c) => c.status === "OPEN").length,
    [comentarios],
  )

  if (cargando) {
    return (
      <main className="page">
        <div className="estado-pantalla" role="status">Cargando la revisión del capítulo…</div>
      </main>
    )
  }

  return (
    <main className="page">
      <div className="page-heading">
        <div>
          <span className="eyebrow blue">OBSERVACIONES DE REVISIÓN</span>
          <h1>Revisión del capítulo</h1>
          <p>
            Observaciones ancladas del asesor a las versiones enviadas. El envío
            y la decisión por capítulo se administran en el panel del asesor.
          </p>
        </div>
      </div>

      {numerosCapitulo.length > 0 ? (
        <label style={{ display: "inline-flex", gap: 8, alignItems: "center", marginBottom: 16 }}>
          Capítulo
          <select
            value={numeroCapitulo ?? ""}
            onChange={(e) => setNumeroCapitulo(Number(e.target.value))}
          >
            {numerosCapitulo.map((n) => (
              <option key={n} value={n}>Capítulo {n}</option>
            ))}
          </select>
        </label>
      ) : (
        <p className="aviso">
          El recorrido del proyecto no tiene capítulos numerados aún.
        </p>
      )}

      {error && (
        <div className="aviso aviso-error" role="alert">{error}</div>
      )}

      {numeroCapitulo !== null && (
        <div className="dashboard-grid">
          <section className="section-card">
            <div className="section-title">
              <div>
                <h2>Observaciones</h2>
                <p>Capítulo {numeroCapitulo} · {comentarios.length} total · {abiertos} sin resolver</p>
              </div>
            </div>
            {comentarios.length === 0 ? (
              <p className="aviso">
                No hay observaciones registradas para este capítulo.
              </p>
            ) : (
              <div className="chapter-list">
                {comentarios.map((c) => (
                  <div className="chapter-row" key={`${c.comment_id}:${c.snapshot_id ?? "base"}`}>
                    <Icon name="comment" size={15} />
                    <div>
                      <strong>{c.selected_text ? `«${c.selected_text}»` : "Observación general"}</strong>
                      <small>
                        {c.author} · {new Date(c.created_at).toLocaleString()} ·{" "}
                        {c.snapshot_id ? "sobre versión enviada" : "texto base"}
                      </small>
                      <p>{c.body}</p>
                    </div>
                    <StatusBadge>{c.status === "OPEN" ? "Pendiente" : "Resuelta"}</StatusBadge>
                  </div>
                ))}
              </div>
            )}
          </section>
          <aside className="dashboard-aside">
            <section className="methodology-card">
              <span className="eyebrow blue">VERSIONES ENVIADAS</span>
              {snapshots.length === 0 ? (
                <p>
                  Este capítulo aún no tiene versiones enviadas a revisión.
                </p>
              ) : (
                <div className="chapter-list">
                  {snapshots.map((s) => (
                    <div className="chapter-row" key={s.snapshot_id}>
                      <span className="chapter-number">{s.snapshot_no}</span>
                      <div>
                        <strong>{s.status}</strong>
                        <small>
                          SHA {s.content_sha256.slice(0, 12)}… ·{" "}
                          {new Date(s.created_at).toLocaleString()}
                        </small>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </aside>
        </div>
      )}
    </main>
  )
}
