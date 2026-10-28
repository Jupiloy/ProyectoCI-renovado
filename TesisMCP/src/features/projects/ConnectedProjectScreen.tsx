import { useState } from "react"
import type { ProjectState, ProjectSummary, SessionUser } from "../../api/types"

interface ConnectedProjectScreenProps {
  project: ProjectSummary
  details: ProjectState
  user: SessionUser
  onChangeProject: () => void
  onLogout: () => Promise<void>
  onOpenEditor: () => void
  onOpenWorkflow: () => void
  onOpenLibrary: () => void
  onOpenAdvisor: () => void
  onOpenAI: () => void
  onOpenArtifacts: () => void
}

export default function ConnectedProjectScreen({
  project,
  details,
  user,
  onChangeProject,
  onLogout,
  onOpenEditor,
  onOpenWorkflow,
  onOpenLibrary,
  onOpenAdvisor,
  onOpenAI,
  onOpenArtifacts,
}: ConnectedProjectScreenProps) {
  const [logoutError, setLogoutError] = useState<string | null>(null)
  const [loggingOut, setLoggingOut] = useState(false)
  const role = project.role === "OWNER" ? "Tesista" : "Asesor"
  async function handleLogout() {
    if (loggingOut) return
    setLoggingOut(true)
    setLogoutError(null)
    try {
      await onLogout()
    } catch (cause) {
      setLogoutError(cause instanceof Error ? cause.message : "No se pudo cerrar la sesión.")
    } finally {
      setLoggingOut(false)
    }
  }

  return (
    <div className="connected-app-shell">
      <aside className="sidebar connected-sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">T</div>
          <div><b>TesisMCP</b><span>Espacio académico</span></div>
        </div>
        <div className="connected-project-sidebar">
          <span className="eyebrow">PROYECTO ACTIVO</span>
          <strong>{project.name}</strong>
          <span>{role}</span>
        </div>
        <div className="sidebar-bottom">
          <button className="nav-item connected-change-project" type="button" onClick={onChangeProject}>Cambiar proyecto</button>
          <div className="profile">
            <div className="avatar">{(user.display_name || user.email).slice(0, 1).toUpperCase()}</div>
            <div><b>{user.display_name || user.email}</b><span>{role}</span></div>
          </div>
        </div>
      </aside>
      <div className="app-main">
        <header className="topbar">
          <div className="breadcrumbs"><span>{project.name}</span><strong>Espacio del proyecto</strong></div>
          <div className="top-actions">
            <span className="real-connection-pill"><i />Conectado al backend</span>
            <button className="button button-secondary" type="button" onClick={() => void handleLogout()} disabled={loggingOut}>{loggingOut ? "Cerrando…" : "Cerrar sesión"}</button>
          </div>
        </header>
        <main className="connected-project-page">
          <div className="connected-welcome">
            <span className="eyebrow blue">PROYECTO DE TESIS · DATOS DEL SERVIDOR</span>
            <h1>{details.title || project.title || project.name}</h1>
            <p>{details.name} <span>·</span> {role}</p>
          </div>
          {logoutError && <div className="auth-alert" role="alert">{logoutError}</div>}
          <section className="connected-status-card">
            <span className="status status-success"><span className="status-dot" />Proyecto activo</span>
            <h2>Tu espacio está conectado</h2>
            <p>La sesión y el acceso a este proyecto se verifican con el backend. {project.permissions.can_edit_document ? "Puedes abrir y editar el documento versionado." : "Puedes consultar el documento y registrar tu revisión según tus permisos."}</p>
            {details.idea_provisional && (
              <div className="connected-idea">
                <span className="eyebrow">IDEA PROVISIONAL REGISTRADA</span>
                <p>{details.idea_provisional}</p>
              </div>
            )}
          </section>
          <section className="connected-permissions-card">
            <div>
              <span className="eyebrow blue">TU PARTICIPACIÓN</span>
              <h2>{role} en este proyecto</h2>
              <p>Las acciones se vuelven a validar en el servidor cada vez que se solicitan.</p>
            </div>
            <ul>
              <li><span>{project.permissions.can_read_project ? "✓" : "—"}</span>Consultar este proyecto</li>
              <li><span>{project.permissions.can_edit_document ? "✓" : "—"}</span>Editar el documento</li>
              <li><span>{project.permissions.can_manage_workflow ? "✓" : "—"}</span>Administrar el recorrido metodológico</li>
              <li><span>{project.permissions.can_review_chapters ? "✓" : "—"}</span>Revisar capítulos como asesor</li>
            </ul>
          </section>
          <div className="connected-next-step" style={{ background: "#f0f4f9", border: "1px solid #dbe4ee" }}>
            <span className="step-icon" aria-hidden="true" style={{ background: "var(--blue)", color: "white" }}>☲</span>
            <div>
              <b>Recorrido metodológico y prompts</b>
              <p>{project.permissions.can_manage_workflow ? "Consulta tareas y dependencias; edita, valida y publica versiones del recorrido." : "Consulta las tareas y dependencias del recorrido metodológico."}</p>
            </div>
            <button className="button button-primary" type="button" onClick={onOpenWorkflow}>Ver recorrido</button>
          </div>
          <div className="connected-next-step" style={{ background: "#f8fafd", border: "1px solid #d0e0f0" }}>
            <span className="step-icon" aria-hidden="true" style={{ background: "#1f6f8b", color: "white" }}>📚</span>
            <div>
              <b>Biblioteca y consulta de pasajes</b>
              <p>{project.role === "OWNER" ? "Sube documentos, consulta pasajes y gestiona fuentes bibliográficas." : "Consulta documentos, pasajes y fuentes del proyecto."}</p>
            </div>
            <button className="button button-primary" type="button" onClick={onOpenLibrary}>Abrir biblioteca</button>
          </div>
          <div className="connected-next-step" style={{ background: "#fdf8f4", border: "1px solid #ebd8cb" }}>
            <span className="step-icon" aria-hidden="true" style={{ background: "#a85d26", color: "white" }}>⚖️</span>
            <div>
              <b>{project.role === "ADVISOR" ? "Panel del Asesor (Revisión y decisiones)" : "Revisión del Asesor, Snapshots y Apoyos"}</b>
              <p>{project.role === "ADVISOR" ? "Consulta instantáneas y registra observaciones y decisiones académicas." : "Consulta el estado de revisión, instantáneas y personas de apoyo."}</p>
            </div>
            <button className="button button-primary" type="button" onClick={onOpenAdvisor}>Abrir revisión</button>
          </div>
          <div className="connected-next-step" style={{ background: "#f5f3ff", border: "1px solid #ddd6fe" }}>
            <span className="step-icon" aria-hidden="true" style={{ background: "#7c3aed", color: "white" }}>✨</span>
            <div>
              <b>Asistente de IA y Decisiones Humanas</b>
              <p>{project.role === "OWNER" ? "Genera y decide propuestas estructuradas, revisa diferencias y crea lotes de tareas." : "Consulta los lotes y las síntesis existentes del proyecto."}</p>
            </div>
            <button className="button button-primary" type="button" onClick={onOpenAI}>Abrir asistente IA</button>
          </div>
          <div className="connected-next-step" style={{ background: "#f0fdf4", border: "1px solid #bbf7d0" }}>
            <span className="step-icon" aria-hidden="true" style={{ background: "#16a34a", color: "white" }}>📊</span>
            <div>
              <b>Datos, Citas IEEE, Tablas y Exportación</b>
              <p>{project.role === "OWNER" ? "Gestiona datos, tablas, figuras y citas IEEE; exporta el manuscrito." : "Consulta datos, tablas, figuras, citas IEEE y exportaciones autorizadas."}</p>
            </div>
            <button className="button button-primary" type="button" onClick={onOpenArtifacts}>Abrir datos y exportación</button>
          </div>
          <div className="connected-next-step">
            <span className="step-icon" aria-hidden="true">→</span>
            <div><b>Documento de tesis</b><p>{project.permissions.can_edit_document ? "Abre un capítulo, edita bloques y guarda una nueva versión." : "Abre un capítulo para consultar su estado y contenido."}</p></div>
            <button className="button button-secondary" type="button" onClick={onOpenEditor}>Abrir editor</button>
          </div>
        </main>
      </div>
    </div>
  )
}
