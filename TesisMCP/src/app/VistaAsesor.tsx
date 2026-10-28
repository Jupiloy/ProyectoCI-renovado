import { useCallback, useEffect, useRef, useState } from "react"
import { ApiError } from "../api/client"
import { getChapterDocument, getChapterState } from "../api/chapters"
import {
  addComment,
  decideChapter,
  getAdvisorDashboard,
  getChapterSnapshot,
  listChapterSnapshots,
  listComments,
  resolveComment,
} from "../api/reviews"
import type {
  AdvisorDashboardProject,
  ChapterSnapshotDetail,
  ChapterSnapshotSummary,
  ChapterState,
  ProjectSummary,
  ReviewComment,
} from "../api/types"
import { Button, Icon, StatusBadge } from "./base"

const etiquetaPorEstado: Record<string, string> = {
  DRAFT: "Borrador",
  READY: "En revisión",
  CHANGES_REQUESTED: "Con observaciones",
  APPROVED: "Aprobado",
}

type EstadoVista = "dashboard" | "revision"

/**
 * Panel asesor (disposición del demo de Figma) alimentado por
 * GET /projects/advisor/dashboard. El contrato entrega solo project_name
 * y el status de cada capítulo: no se inventan métricas de actividad ni
 * de avance de pasos.
 */
export function VistaAsesor({
  proyectoActivo,
  csrfToken,
  onUnauthorized,
  onAccessLost,
  onRefreshCsrf,
}: {
  proyectoActivo: ProjectSummary
  csrfToken: string
  onUnauthorized: () => void
  onAccessLost: () => void
  onRefreshCsrf: () => Promise<void>
}) {
  const [dashboard, setDashboard] = useState<AdvisorDashboardProject[] | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [proyectoSel, setProyectoSel] = useState<AdvisorDashboardProject | null>(null)

  const cargarDashboard = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const lista = await getAdvisorDashboard()
      setDashboard(lista)
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
      else if (cause instanceof ApiError && (cause.status === 404 || cause.status === 403)) onAccessLost()
      setDashboard(null)
      setError(cause instanceof Error ? cause.message : "No se pudo cargar el panel del asesor.")
    } finally {
      setCargando(false)
    }
  }, [onUnauthorized, onAccessLost])

  useEffect(() => {
    void cargarDashboard()
  }, [cargarDashboard])

  if (cargando && dashboard === null) {
    return (
      <main className="page">
        <div className="estado-pantalla" role="status">Cargando el panel del asesor…</div>
      </main>
    )
  }

  return (
    <>
      {proyectoSel === null ? (
        <main className="page advisor-page">
          <div className="page-heading">
            <div>
              <span className="eyebrow blue">ESPACIO DEL ASESOR</span>
              <h1>Supervisión de tesistas</h1>
              <p>Seguimiento académico y revisiones pendientes.</p>
            </div>
          </div>
          {error && <div className="aviso aviso-error" role="alert">{error}</div>}
          {dashboard !== null && dashboard.length === 0 && (
            <p className="aviso">
              No tienes proyectos asignados como asesor todavía.
            </p>
          )}
          {dashboard !== null && dashboard.length > 0 && (
            <>
              <div className="advisor-summary">
                <div>
                  <span>PROYECTOS ASIGNADOS</span>
                  <strong>{dashboard.length}</strong>
                  <small>Datos de GET /projects/advisor/dashboard</small>
                </div>
                <div>
                  <span>CAPÍTULOS EN REVISIÓN</span>
                  <strong>
                    {dashboard.reduce(
                      (total, p) => total + p.chapters.filter((c) => c.status === "READY").length,
                      0,
                    )}
                  </strong>
                  <small>Solo estados READY reales</small>
                </div>
                <div>
                  <span>CAPÍTULOS CON OBSERVACIONES</span>
                  <strong>
                    {dashboard.reduce(
                      (total, p) => total + p.chapters.filter((c) => c.status === "CHANGES_REQUESTED").length,
                      0,
                    )}
                  </strong>
                  <small>Solo estados CHANGES_REQUESTED reales</small>
                </div>
              </div>
              <section className="advisor-content">
                <div className="section-card">
                  <div className="section-title">
                    <div>
                      <h2>Proyectos</h2>
                      <p>El contrato entrega nombre del proyecto y estado por capítulo</p>
                    </div>
                  </div>
                  <div className="chapter-list">
                    {dashboard.map((p) => (
                      <button
                        className="chapter-row"
                        key={p.project_id}
                        onClick={() => setProyectoSel(p)}
                        title="Abrir el espacio de revisión de este proyecto"
                      >
                        <span className="chapter-number">{p.chapters.length}</span>
                        <div>
                          <strong>{p.project_name}</strong>
                          <small>
                            {p.chapters.filter((c) => c.status === "READY").length} en revisión ·{" "}
                            {p.chapters.filter((c) => c.status === "CHANGES_REQUESTED").length} con observaciones ·{" "}
                            {p.chapters.filter((c) => c.status === "APPROVED").length} aprobados
                          </small>
                        </div>
                        <Icon name="chevron" size={15} />
                      </button>
                    ))}
                  </div>
                  <small className="aviso">
                    La membresía como asesor ({proyectoActivo.name} u otro proyecto asignado) no concede edición
                    de documento: el envío a revisión lo realiza el tesista propietario.
                  </small>
                </div>
              </section>
            </>
          )}
        </main>
      ) : (
        <AdvisorRevision
          sel={proyectoSel}
          csrfToken={csrfToken}
          onUnauthorized={onUnauthorized}
          onAccessLost={onAccessLost}
          onRefreshCsrf={onRefreshCsrf}
          alVolver={() => setProyectoSel(null)}
          alRefrescar={cargarDashboard}
        />
      )}
    </>
  )
}

/** Revisión del asesor sobre una versión concreta del capítulo. */
function AdvisorRevision({
  sel,
  csrfToken,
  onUnauthorized,
  onAccessLost,
  onRefreshCsrf,
  alVolver,
  alRefrescar,
}: {
  sel: AdvisorDashboardProject
  csrfToken: string
  onUnauthorized: () => void
  onAccessLost: () => void
  onRefreshCsrf: () => Promise<void>
  alVolver: () => void
  alRefrescar: () => Promise<void>
}) {
  const [capituloNo, setCapituloNo] = useState<number>(sel.chapters[0]?.chapter_no ?? 1)
  const [estado, setEstado] = useState<ChapterState | null>(null)
  const [snapshots, setSnapshots] = useState<ChapterSnapshotSummary[]>([])
  const [detalle, setDetalle] = useState<ChapterSnapshotDetail | null>(null)
  const [comentarios, setComentarios] = useState<ReviewComment[]>([])
  const [anclaje, setAnclaje] = useState<null | {
    snapshot_id: string
    start_cp: number
    end_cp: number
    selected_text: string
  }>(null)
  const [cargandoDatos, setCargandoDatos] = useState(true)
  const [procesando, setProcesando] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [motivo, setMotivo] = useState("")
  const [versionAbierta, setVersionAbierta] = useState(true)
  const textoRef = useRef<HTMLDivElement | null>(null)
  const secuencia = useRef(0)

  const cargar = useCallback(async (n: number) => {
    const s = ++secuencia.current
    setCargandoDatos(true)
    setError(null)
    setNotice(null)
    setAnclaje(null)
    setDetalle(null)
    try {
      const [st, snaps, comms] = await Promise.all([
        getChapterState(sel.project_id, n),
        listChapterSnapshots(sel.project_id, n).catch(() => [] as ChapterSnapshotSummary[]),
        listComments(sel.project_id, n).catch(() => [] as ReviewComment[]),
      ])
      if (s !== secuencia.current) return
      setEstado(st)
      setSnapshots(snaps)
      setComentarios(comms)
      if (st.submitted_snapshot_id) {
        const det = await getChapterSnapshot(sel.project_id, n, st.submitted_snapshot_id)
        if (s !== secuencia.current) return
        setDetalle(det)
      }
    } catch (cause) {
      if (s !== secuencia.current) return
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
      else if (cause instanceof ApiError && cause.status === 404) onAccessLost()
      setEstado(null)
      setError(cause instanceof Error ? cause.message : "Error al cargar los datos de revisión.")
    } finally {
      if (s === secuencia.current) setCargandoDatos(false)
    }
  }, [sel.project_id, onUnauthorized, onAccessLost])

  useEffect(() => {
    void cargar(capituloNo)
  }, [capituloNo, cargar])

  function abrirVersion(s: ChapterSnapshotSummary) {
    setError(null)
    setAnclaje(null)
    void (async () => {
      setProcesando(`version:${s.snapshot_id}`)
      try {
        const det = await getChapterSnapshot(sel.project_id, capituloNo, s.snapshot_id)
        setDetalle(det)
        setComentarios(await listComments(sel.project_id, capituloNo, s.snapshot_id).catch(() => []))
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "No se pudo cargar la versión.")
      } finally {
        setProcesando(null)
      }
    })()
  }

  function capturarAnclaje() {
    if (!detalle || !textoRef.current) return
    const sel2 = window.getSelection()
    if (!sel2 || sel2.isCollapsed || sel2.rangeCount === 0) return
    const rango = sel2.getRangeAt(0)
    const contenedor = textoRef.current
    if (!contenedor.contains(rango.startContainer) || !contenedor.contains(rango.endContainer)) return

    const previo = rango.cloneRange()
    previo.selectNodeContents(contenedor)
    previo.setEnd(rango.startContainer, rango.startOffset)
    const hasta = rango.cloneRange()
    hasta.selectNodeContents(contenedor)
    hasta.setEnd(rango.endContainer, rango.endOffset)

    const inicioUtf16 = previo.toString().length
    const finUtf16 = hasta.toString().length
    const texto = detalle.content_md.slice(inicioUtf16, finUtf16)
    if (!texto || texto !== rango.toString()) {
      setError("La selección no coincide con el texto de la versión. Vuelve a seleccionar el fragmento.")
      return
    }
    setAnclaje({
      snapshot_id: detalle.snapshot_id,
      start_cp: Array.from(detalle.content_md.slice(0, inicioUtf16)).length,
      end_cp: Array.from(detalle.content_md.slice(0, finUtf16)).length,
      selected_text: texto,
    })
    setError(null)
  }

  async function crearObservacion() {
    if (!anclaje) return
    const cuerpo = (motivo || "").trim()
    if (!cuerpo) {
      setError("Escribe el contenido de la observación antes de registrarla.")
      return
    }
    setProcesando("comentario")
    setError(null)
    try {
      const creado = await addComment(sel.project_id, capituloNo, {
        start_cp: anclaje.start_cp,
        end_cp: anclaje.end_cp,
        selected_text: anclaje.selected_text,
        body: cuerpo,
        snapshot_id: anclaje.snapshot_id,
      }, csrfToken)
      setComentarios((lista) => [...lista, creado])
      setAnclaje(null)
      setMotivo("")
      setNotice("Observación registrada sobre la versión enviada.")
    } catch (c2) {
      if (c2 instanceof ApiError && c2.status === 401) onUnauthorized()
      else if (c2 instanceof ApiError && c2.status === 404) onAccessLost()
      else setError(c2 instanceof Error ? c2.message : "No se pudo registrar la observación.")
    } finally {
      setProcesando(null)
    }
  }

  async function decidir(accion: "REQUEST_CHANGES" | "APPROVE" | "REOPEN") {
    setProcesando(accion)
    setError(null)
    try {
      const nuevo = await decideChapter(sel.project_id, capituloNo, accion, motivo, csrfToken)
      setEstado(nuevo)
      setMotivo("")
      setNotice(`Decisión registrada: ${etiquetaPorEstado[nuevo.status] ?? nuevo.status}.`)
      await alRefrescar()
    } catch (c2) {
      if (c2 instanceof ApiError && c2.status === 401) onUnauthorized()
      else if (c2 instanceof ApiError && c2.status === 404) onAccessLost()
      else if (c2 instanceof ApiError && c2.kind === "csrf") {
        try { await onRefreshCsrf() } catch { /* conservar estado */ }
        setError("Falló la protección CSRF. Vuelve a intentar la decisión.")
      } else setError(c2 instanceof Error ? c2.message : "No se pudo registrar la decisión.")
    } finally {
      setProcesando(null)
    }
  }

  async function resolver(c: ReviewComment) {
    if (procesando !== null) return
    setProcesando(`resolver:${c.comment_id}`)
    setError(null)
    try {
      const r = await resolveComment(sel.project_id, c.comment_id, csrfToken)
      setComentarios((lista) =>
        lista.map((item) => (item.comment_id === r.comment_id ? { ...item, status: r.status } : item)),
      )
    } catch (c2) {
      setError(c2 instanceof Error ? c2.message : "No se pudo resolver la observación.")
    } finally {
      setProcesando(null)
    }
  }

  const abiertas = comentarios.filter((c) => c.status === "OPEN").length

  if (cargandoDatos) {
    return (
      <main className="page">
        <div className="estado-pantalla" role="status">Cargando la revisión del proyecto…</div>
      </main>
    )
  }

  return (
    <main className="page review-page">
      <div className="review-header">
        <div>
          <button className="back-button" onClick={alVolver}>
            <span>‹</span> Volver a proyectos
          </button>
          <div>
            <h1>{sel.project_name} · Capítulo {capituloNo}</h1>
            <p>
              {estado
                ? `${etiquetaPorEstado[estado.status] ?? estado.status} · Versión enviada ${estado.submitted_snapshot_id ? "disponible" : "no disponible"}`
                : "Sin estado"}
            </p>
          </div>
        </div>
        <div>
          <Button
            variant="secondary"
            disabled={procesando !== null || estado?.status !== "READY"}
            onClick={() => void decidir("REQUEST_CHANGES")}
            title="Marca el capítulo con observaciones y lo devuelve al tesista"
          >
            Solicitar cambios
          </Button>
          <div className="approval-wrap">
            <Button
              disabled={
                procesando !== null ||
                estado?.status !== "READY" ||
                comentarios.some((c) => c.status === "OPEN")
              }
              onClick={() => void decidir("APPROVE")}
            >
              Aprobar capítulo
            </Button>
            {estado?.status === "READY" && comentarios.some((c) => c.status === "OPEN") && (
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
              <input value={motivo} onChange={(e) => setMotivo(e.target.value)} />
            </label>
          )}
          {estado?.status === "APPROVED" && (
            <Button
              variant="ghost"
              disabled={procesando !== null || !motivo.trim()}
              onClick={() => void decidir("REOPEN")}
            >
              Reabrir capítulo
            </Button>
          )}
        </div>
      </div>

      {error && <div className="aviso aviso-error" role="alert">{error}</div>}
      {notice && <div className="aviso" role="status">{notice}</div>}

      <div className="review-toolbar">
        <label style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
          Capítulo
          <select value={capituloNo} onChange={(e) => setCapituloNo(Number(e.target.value))}>
            {sel.chapters.map((c) => (
              <option key={c.chapter_no} value={c.chapter_no}>Capítulo {c.chapter_no}</option>
            ))}
          </select>
        </label>
        <span className="toolbar-divider" />
        <button onClick={() => setVersionAbierta(!versionAbierta)}>
          <Icon name="document" size={16} /> Historial de versiones
        </button>
        <span className="open-comments">
          <span />{abiertas} observaciones abiertas
        </span>
      </div>

      <div className="review-workspace">
        {versionAbierta && (
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
                  className={detalle?.snapshot_id === s.snapshot_id ? "active" : undefined}
                  key={s.snapshot_id}
                  disabled={procesando !== null && procesando === `version:${s.snapshot_id}`}
                  onClick={() => abrirVersion(s)}
                >
                  <span>Versión {s.snapshot_no}</span>
                  <small>
                    SHA {s.content_sha256.slice(0, 12)}… · {new Date(s.created_at).toLocaleString()}
                  </small>
                </button>
              ))
            )}
          </aside>
        )}

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
                    onChange={(e) => setMotivo(e.target.value)}
                  />
                  <div className="decision-actions">
                    <Button disabled={procesando !== null} onClick={() => void crearObservacion()}>
                      {procesando === "comentario" ? "Registrando…" : "Registrar observación"}
                    </Button>
                    <Button variant="secondary" onClick={() => { setAnclaje(null); setMotivo("") }}>
                      Cancelar
                    </Button>
                  </div>
                </div>
              )}
              <div ref={textoRef} onMouseUp={capturarAnclaje}>
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
                        onClick={() => void resolver(c)}
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
      </div>
    </main>
  )
}

export function etiquetaEstadoCapitulo(status: string): string {
  return etiquetaPorEstado[status] ?? status
}
