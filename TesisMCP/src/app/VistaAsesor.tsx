import { useCallback, useEffect, useState } from "react"
import { ApiError } from "../api/client"
import { getAdvisorDashboard } from "../api/reviews"
import type { AdvisorDashboardProject, ProjectSummary } from "../api/types"
import { Icon } from "./base"
import { RevisionAsesor } from "./asesor/RevisionAsesor"

/** Etiquetas de estado de capítulo; re-export para compatibilidad con los
 * consumidores de este módulo desde antes de la división. */
export { etiquetaEstadoCapitulo } from "./asesor/etiquetas"

/**
 * Panel asesor (disposición del demo de Figma) alimentado por
 * GET /projects/advisor/dashboard. El contrato entrega solo project_name
 * y el status de cada capítulo: no se inventan métricas de actividad ni
 * de avance de pasos. La revisión de un proyecto vive en asesor/RevisionAsesor.
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
        <RevisionAsesor
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
