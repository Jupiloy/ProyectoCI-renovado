import { useCallback, useEffect, useState } from "react"
import { ApiError } from "./api/client"
import { getSession, login, logout } from "./api/auth"
import { getProject } from "./api/projects"
import type { ProjectState, ProjectSummary, SessionResponse, SessionUser } from "./api/types"
import AccessScreen from "./features/auth/AccessScreen"
import ConnectedProjectScreen from "./features/projects/ConnectedProjectScreen"
import ChapterEditorScreen from "./features/editor/ChapterEditorScreen"
import WorkflowScreen from "./features/workflow/WorkflowScreen"
import LibraryScreen from "./features/library/LibraryScreen"
import AdvisorScreen from "./features/advisor/AdvisorScreen"
import { AIAssistantScreen } from "./features/ai/AIAssistantScreen"
import { ResearchArtifactsScreen } from "./features/artifacts/ResearchArtifactsScreen"
import ProjectSelectionScreen from "./features/projects/ProjectSelectionScreen"
import DemoApp from "./DemoApp"

type AppView = "checking" | "access" | "projects" | "workspace" | "editor" | "workflow" | "library" | "advisor" | "ai" | "artifacts" | "demo"
type SessionAvailability = "checking" | "available" | "unavailable"

export default function App() {
  const [view, setView] = useState<AppView>("checking")
  const [sessionAvailability, setSessionAvailability] = useState<SessionAvailability>("checking")
  const [sessionUser, setSessionUser] = useState<SessionUser | null>(null)
  const [csrfToken, setCsrfToken] = useState<string | null>(null)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const [projectNotice, setProjectNotice] = useState<string | null>(null)
  const [reloadProjects, setReloadProjects] = useState(0)
  const [openingProjectId, setOpeningProjectId] = useState<string | null>(null)
  const [selectedProject, setSelectedProject] = useState<ProjectSummary | null>(null)
  const [projectDetails, setProjectDetails] = useState<ProjectState | null>(null)
  const [loggingOut, setLoggingOut] = useState(false)

  const refreshSession = useCallback(async () => {
    setSessionAvailability("checking")
    setConnectionError(null)
    try {
      const response = await getSession()
      setCsrfToken(response.csrf_token)
      setSessionUser(response.authenticated ? response.user : null)
      setSessionAvailability("available")
      setSelectedProject(null)
      setProjectDetails(null)
      setView(response.authenticated && response.user ? "projects" : "access")
    } catch (cause) {
      setCsrfToken(null)
      setSessionUser(null)
      setSessionAvailability("unavailable")
      setView("access")
      setConnectionError(cause instanceof Error ? cause.message : "No se pudo conectar con Django.")
    }
  }, [])

  useEffect(() => {
    void refreshSession()
  }, [refreshSession])

  const handleUnauthorized = useCallback(() => {
    setSessionUser(null)
    setSelectedProject(null)
    setProjectDetails(null)
    setProjectNotice(null)
    setView("checking")
    void refreshSession()
  }, [refreshSession])

  async function handleLogin(email: string, password: string, csrf: string): Promise<SessionResponse> {
    return login(email, password, csrf)
  }

  function handleAuthenticated(response: SessionResponse) {
    setCsrfToken(response.csrf_token)
    setSessionUser(response.user)
    setSessionAvailability("available")
    setConnectionError(null)
    setProjectNotice(null)
    setView("projects")
  }

  const refreshCsrf = useCallback(async () => {
    const response = await getSession()
    setCsrfToken(response.csrf_token)
    setSessionAvailability("available")
    setConnectionError(null)
    if (!response.authenticated || !response.user) {
      setSessionUser(null)
      setSelectedProject(null)
      setProjectDetails(null)
      setView("access")
      return
    }
    setSessionUser(response.user)
    setView((current) => current === "access" ? "projects" : current)
  }, [])

  const handleLogout = useCallback(async () => {
    if (!csrfToken) throw new Error("No hay un token de seguridad disponible. Recarga la sesión antes de cerrar.")
    if (loggingOut) return
    setLoggingOut(true)
    try {
      const response = await logout(csrfToken)
      if (response.authenticated) throw new Error("El servidor no confirmó el cierre de sesión.")
      setSessionUser(null)
      setSelectedProject(null)
      setProjectDetails(null)
      setProjectNotice(null)
      setView("access")
    } catch (cause) {
      if (cause instanceof ApiError && cause.kind === "csrf") {
        try {
          await refreshCsrf()
        } catch {
          throw new Error("No se pudo actualizar la protección CSRF. Recarga la página para cerrar sesión.")
        }
        throw new Error("Se actualizó la protección CSRF. Pulsa «Cerrar sesión» de nuevo.")
      }
      throw cause
    } finally {
      setLoggingOut(false)
    }
  }, [csrfToken, loggingOut, refreshCsrf])

  const handleOpenProject = useCallback(async (project: ProjectSummary) => {
    setOpeningProjectId(project.project_id)
    setProjectNotice(null)
    try {
      const details = await getProject(project.project_id)
      if (details.project_id !== project.project_id) {
        throw new Error("El servidor devolvió un proyecto distinto al seleccionado.")
      }
      setSelectedProject(project)
      setProjectDetails(details)
      setView("workspace")
      return true
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        handleUnauthorized()
      } else if (cause instanceof ApiError && (cause.status === 404 || cause.status === 409)) {
        setProjectNotice("El acceso a ese proyecto cambió. Actualizamos la lista de proyectos disponibles.")
        setReloadProjects((key) => key + 1)
        setView("projects")
      } else {
        setProjectNotice(cause instanceof Error ? cause.message : "No se pudo abrir el proyecto.")
      }
      return false
    } finally {
      setOpeningProjectId(null)
    }
  }, [handleUnauthorized])

  const handleChangeProject = useCallback(() => {
    setSelectedProject(null)
    setProjectDetails(null)
    setProjectNotice(null)
    setReloadProjects((key) => key + 1)
    setView("projects")
  }, [])

  const handleAccessLost = useCallback(() => {
    setSelectedProject(null)
    setProjectDetails(null)
    setProjectNotice("El proyecto o capítulo dejó de estar disponible. Se actualizó la lista de proyectos.")
    setReloadProjects((key) => key + 1)
    setView("projects")
  }, [])

  if (view === "checking") {
    return <main className="access-loading" role="status">Comprobando la sesión…</main>
  }

  if (view === "demo") {
    return <DemoApp onExitDemo={() => setView("access")} />
  }

  if (view === "access" || sessionAvailability === "unavailable" || !sessionUser) {
    return (
      <AccessScreen
        csrfToken={csrfToken}
        connectionError={connectionError}
        onRetryConnection={() => void refreshSession()}
        onRefreshCsrf={refreshCsrf}
        onLogin={handleLogin}
        onAuthenticated={handleAuthenticated}
        onDemo={() => setView("demo")}
      />
    )
  }

  if (view === "workspace" && selectedProject && projectDetails) {
    return (
      <ConnectedProjectScreen
        project={selectedProject}
        details={projectDetails}
        user={sessionUser}
        onChangeProject={handleChangeProject}
        onLogout={handleLogout}
        onOpenEditor={() => setView("editor")}
        onOpenWorkflow={() => setView("workflow")}
        onOpenLibrary={() => setView("library")}
        onOpenAdvisor={() => setView("advisor")}
        onOpenAI={() => setView("ai")}
        onOpenArtifacts={() => setView("artifacts")}
      />
    )
  }

  if (view === "ai" && selectedProject && projectDetails && sessionUser) {
    return (
      <AIAssistantScreen
        projectId={selectedProject.project_id}
        projectName={projectDetails.name || selectedProject.name}
        canWrite={selectedProject.role === "OWNER"}
        csrfToken={csrfToken ?? ""}
        stateVersion={projectDetails.state_version}
        onBack={() => setView("workspace")}
        onStateVersionChanged={(newVer) => {
          setProjectDetails((prev) => (prev ? { ...prev, state_version: newVer } : null))
        }}
      />
    )
  }

  if (view === "artifacts" && selectedProject && projectDetails && sessionUser) {
    return (
      <ResearchArtifactsScreen
        projectId={selectedProject.project_id}
        projectName={projectDetails.name || selectedProject.name}
        canWrite={selectedProject.role === "OWNER"}
        csrfToken={csrfToken ?? ""}
        stateVersion={projectDetails.state_version}
        onBack={() => setView("workspace")}
      />
    )
  }

  if (view === "advisor" && selectedProject && projectDetails && sessionUser) {
    return (
      <AdvisorScreen
        project={selectedProject}
        details={projectDetails}
        user={sessionUser}
        csrfToken={csrfToken ?? ""}
        onBack={() => setView("workspace")}
        onUnauthorized={handleUnauthorized}
        onAccessLost={handleAccessLost}
        onLogout={handleLogout}
      />
    )
  }

  if (view === "library" && selectedProject && projectDetails && sessionUser) {
    return (
      <LibraryScreen
        project={selectedProject}
        details={projectDetails}
        user={sessionUser}
        csrfToken={csrfToken ?? ""}
        onBack={() => setView("workspace")}
        onUnauthorized={handleUnauthorized}
        onAccessLost={handleAccessLost}
        onLogout={handleLogout}
      />
    )
  }

  if (view === "workflow" && selectedProject && projectDetails && sessionUser) {
    return (
      <WorkflowScreen
        project={selectedProject}
        details={projectDetails}
        user={sessionUser}
        csrfToken={csrfToken ?? ""}
        onBack={() => setView("workspace")}
        onUnauthorized={handleUnauthorized}
        onAccessLost={handleAccessLost}
        onRefreshCsrf={refreshCsrf}
        onLogout={handleLogout}
      />
    )
  }

  if (view === "editor" && selectedProject && sessionUser) {
    return (
      <ChapterEditorScreen
        project={selectedProject}
        user={sessionUser}
        csrfToken={csrfToken ?? ""}
        onBack={() => setView("workspace")}
        onUnauthorized={handleUnauthorized}
        onAccessLost={handleAccessLost}
        onRefreshCsrf={refreshCsrf}
        onLogout={handleLogout}
      />
    )
  }

  return (
    <ProjectSelectionScreen
      key={`${sessionUser.id}:${reloadProjects}`}
      user={sessionUser}
      csrfToken={csrfToken ?? ""}
      notice={projectNotice}
      reloadKey={reloadProjects}
      openingProjectId={openingProjectId}
      onOpenProject={handleOpenProject}
      onUnauthorized={handleUnauthorized}
      onRefreshCsrf={refreshCsrf}
      onLogout={handleLogout}
    />
  )
}
