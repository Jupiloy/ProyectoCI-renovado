import { useEffect, useState, type FormEvent } from "react"
import { ApiError } from "../../api/client"
import { createProject, listProjects } from "../../api/projects"
import type { ProjectSummary, SessionUser } from "../../api/types"

interface ProjectSelectionScreenProps {
  user: SessionUser
  csrfToken: string
  notice: string | null
  reloadKey: number
  openingProjectId: string | null
  onOpenProject: (project: ProjectSummary) => Promise<boolean>
  onUnauthorized: () => void
  onRefreshCsrf: () => Promise<void>
  onLogout: () => Promise<void>
}

function displayRole(role: ProjectSummary["role"]): string {
  return role === "OWNER" ? "Tesista" : "Asesor"
}

function errorMessage(cause: unknown, fallback: string): string {
  return cause instanceof Error ? cause.message : fallback
}

export default function ProjectSelectionScreen({
  user,
  csrfToken,
  notice,
  reloadKey,
  openingProjectId,
  onOpenProject,
  onUnauthorized,
  onRefreshCsrf,
  onLogout,
}: ProjectSelectionScreenProps) {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [listRefresh, setListRefresh] = useState(0)
  const [listError, setListError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [projectName, setProjectName] = useState("")
  const [projectTitle, setProjectTitle] = useState("")
  const [createdProjectId, setCreatedProjectId] = useState<string | null>(null)
  const [creationUncertain, setCreationUncertain] = useState(false)
  const [creating, setCreating] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    setListError(null)
    setProjects([])
    setOffset(0)
    setHasMore(false)
    listProjects().then((page) => {
      if (!active) return
      setProjects(page.projects)
      setOffset(page.offset + page.limit)
      setHasMore(page.has_more)
    }).catch((cause: unknown) => {
      if (!active) return
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
      } else {
        setListError(errorMessage(cause, "No se pudieron cargar los proyectos."))
      }
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [user.id, reloadKey, listRefresh, onUnauthorized])

  function refreshList() {
    if (loading) return
    setListRefresh((value) => value + 1)
  }

  async function loadMore() {
    if (loadingMore || !hasMore) return
    setLoadingMore(true)
    setActionError(null)
    try {
      const page = await listProjects(offset)
      setProjects((current) => {
        const known = new Set(current.map((project) => project.project_id))
        return [...current, ...page.projects.filter((project) => !known.has(project.project_id))]
      })
      setOffset(page.offset + page.limit)
      setHasMore(page.has_more)
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
      else setActionError(errorMessage(cause, "No se pudieron cargar más proyectos."))
    } finally {
      setLoadingMore(false)
    }
  }

  async function findNewProject(projectId: string): Promise<ProjectSummary | null> {
    let currentOffset = 0
    while (true) {
      const page = await listProjects(currentOffset, 100)
      const found = page.projects.find((project) => project.project_id === projectId)
      if (found) return found
      if (!page.has_more) return null
      currentOffset = page.offset + page.limit
    }
  }

  async function openCreatedProject(projectId: string) {
    try {
      const summary = await findNewProject(projectId)
      if (!summary) {
        setActionError("El proyecto ya se creó, pero no apareció en el listado autorizado. Actualiza la lista antes de continuar.")
        return
      }
      const opened = await onOpenProject(summary)
      if (!opened) {
        setActionError("El proyecto ya se creó, pero no se pudo abrir. Pulsa «Buscar proyecto creado» para intentarlo de nuevo sin repetir la creación.")
        setListRefresh((value) => value + 1)
        return
      }
      setCreatedProjectId(null)
      setProjectName("")
      setProjectTitle("")
      setFormOpen(false)
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
      } else {
        setActionError(`El proyecto ya se creó, pero no pudimos cargarlo: ${errorMessage(cause, "error de consulta")}. Pulsa «Buscar proyecto creado» para reintentar sin crearlo otra vez.`)
      }
    }
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (creating || creationUncertain || listError) return
    setCreating(true)
    setActionError(null)
    try {
      if (createdProjectId) {
        await openCreatedProject(createdProjectId)
        return
      }
      let createdId: string
      try {
        const created = await createProject(projectName.trim(), projectTitle.trim() || undefined, csrfToken)
        if (typeof created.project_id !== "string" || !created.project_id) {
          throw new Error("El servidor no devolvió el identificador del proyecto creado.")
        }
        createdId = created.project_id
        setCreatedProjectId(createdId)
      } catch (cause) {
        if (cause instanceof ApiError && cause.status === 401) {
          onUnauthorized()
        } else if (cause instanceof ApiError && cause.kind === "csrf") {
          try {
            await onRefreshCsrf()
            setActionError("La protección CSRF rechazó la creación. Actualizamos la sesión; pulsa «Crear y abrir» para volver a intentarlo.")
          } catch {
            setActionError("No se pudo actualizar la protección CSRF. Recarga la página antes de crear el proyecto.")
          }
        } else if (cause instanceof ApiError && cause.status < 500) {
          setActionError(cause.message)
        } else {
          // A lost response or server error does not prove whether the POST committed.
          setCreationUncertain(true)
          setActionError("No pudimos confirmar si el proyecto se creó. Revisa tus proyectos antes de decidir si quieres enviarlo de nuevo.")
        }
        return
      }
      await openCreatedProject(createdId)
    } finally {
      setCreating(false)
    }
  }

  async function handleLogout() {
    if (loggingOut) return
    setLoggingOut(true)
    setActionError(null)
    try {
      await onLogout()
    } catch (cause) {
      setActionError(errorMessage(cause, "No se pudo cerrar la sesión."))
    } finally {
      setLoggingOut(false)
    }
  }

  return (
    <main className="project-selection-page">
      <header className="project-selection-header">
        <div className="login-brand project-brand">
          <div className="brand-mark" aria-hidden="true">T</div>
          <div><b>TesisMCP</b><span>Espacio académico</span></div>
        </div>
        <div className="project-user-menu">
          <span className="avatar">{(user.display_name || user.email).slice(0, 1).toUpperCase()}</span>
          <span className="project-user-copy"><b>{user.display_name || user.email}</b><small>{user.email}</small></span>
          <button className="button button-secondary" type="button" onClick={handleLogout} disabled={loggingOut}>
            {loggingOut ? "Cerrando…" : "Cerrar sesión"}
          </button>
        </div>
      </header>

      <section className="project-selection-content">
        <div className="page-heading">
          <div>
            <span className="eyebrow blue">ESPACIO DE TRABAJO</span>
            <h1>Mis proyectos</h1>
            <p>El rol y las acciones disponibles dependen de tu participación en cada proyecto.</p>
          </div>
          <button className="button button-primary" type="button" onClick={() => { setFormOpen((open) => !open); setActionError(null) }} disabled={Boolean(listError) && !formOpen}>
            {formOpen ? "Cancelar" : "Crear proyecto"}
          </button>
        </div>

        {notice && <div className="auth-alert" role="status">{notice}</div>}
        {actionError && <div className="auth-alert" role="alert">{actionError}</div>}

        {formOpen && (
          <form className="create-project-card" onSubmit={handleCreate}>
            <h2>{createdProjectId ? "Proyecto creado" : "Crear un proyecto"}</h2>
            <label className="login-field">
              Nombre del proyecto
              <input value={projectName} onChange={(event) => setProjectName(event.target.value)} required maxLength={160} disabled={creating || Boolean(createdProjectId)} />
            </label>
            <label className="login-field">
              Título provisional <span className="field-optional">Opcional</span>
              <input value={projectTitle} onChange={(event) => setProjectTitle(event.target.value)} maxLength={300} disabled={creating || Boolean(createdProjectId)} />
            </label>
            {creationUncertain && (
              <div className="creation-uncertain" role="status">
                <p>La respuesta de creación no llegó o falló el servidor. Actualiza la lista y revisa si el proyecto figura allí antes de permitir otro envío.</p>
                <button className="button button-secondary" type="button" onClick={refreshList} disabled={loading}>Actualizar lista</button>
                <button className="button button-secondary" type="button" onClick={() => { setCreationUncertain(false); setActionError(null) }} disabled={loading || Boolean(listError)}>Ya revisé la lista; permitir otro intento</button>
              </div>
            )}
            <button className="button button-primary" type="submit" disabled={creating || creationUncertain || Boolean(listError) || (!createdProjectId && !projectName.trim())}>
              {creating ? "Procesando…" : createdProjectId ? "Buscar proyecto creado" : "Crear y abrir"}
            </button>
          </form>
        )}

        {loading ? (
          <div className="project-state-card" role="status">Cargando tus proyectos…</div>
        ) : listError ? (
          <div className="project-state-card" role="alert">
            <h2>No se pudo cargar la lista de proyectos</h2>
            <p>{listError}</p>
            <button className="button button-secondary" type="button" onClick={refreshList}>Reintentar carga</button>
          </div>
        ) : projects.length === 0 ? (
          <div className="project-empty-state">
            <span className="empty-mark" aria-hidden="true">＋</span>
            <h2>Aún no tienes proyectos asignados</h2>
            <p>Si eres tesista, puedes crear uno. Para trabajar como asesor, la persona titular debe asignarte a un proyecto con una cuenta institucional existente.</p>
            <button className="button button-primary" type="button" onClick={() => { setFormOpen(true); setActionError(null) }}>Crear mi primer proyecto</button>
          </div>
        ) : (
          <section className="project-card-list" aria-label="Proyectos disponibles">
            {projects.map((project) => (
              <button
                className="project-card"
                key={project.project_id}
                type="button"
                onClick={() => void onOpenProject(project)}
                disabled={openingProjectId !== null}
              >
                <span className="project-card-mark" aria-hidden="true">{project.role === "OWNER" ? "T" : "A"}</span>
                <span className="project-card-copy">
                  <b>{project.name}</b>
                  <span>{project.title}</span>
                  <small>{displayRole(project.role)} · Proyecto activo</small>
                </span>
                <span className="project-card-action">
                  {openingProjectId === project.project_id ? "Abriendo…" : "Abrir proyecto →"}
                </span>
              </button>
            ))}
          </section>
        )}
        {!loading && !listError && hasMore && (
          <button className="button button-secondary load-more-projects" type="button" onClick={() => void loadMore()} disabled={loadingMore}>
            {loadingMore ? "Cargando…" : "Cargar más proyectos"}
          </button>
        )}
      </section>
    </main>
  )
}
