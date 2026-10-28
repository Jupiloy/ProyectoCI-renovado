import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { ApiError } from "../../api/client"
import { getChapterState } from "../../api/chapters"
import {
  executeCustomWorkflowTask,
  getEffectivePrompt,
  getWorkflowState,
  publishWorkflowDraft,
  restoreWorkflowVersion,
  saveStep,
  updateWorkflowDraft,
  validateWorkflowDraft,
} from "../../api/workflows"
import type {
  ChapterState,
  EffectivePrompt,
  ProjectState,
  ProjectSummary,
  SessionUser,
  WorkflowDraftInput,
  WorkflowState,
  WorkflowTask,
  WorkflowValidationResult,
} from "../../api/types"

interface Props {
  project: ProjectSummary
  details: ProjectState
  user: SessionUser
  csrfToken: string
  onBack: () => void
  onUnauthorized: () => void
  onAccessLost: () => void
  onRefreshCsrf: () => Promise<void>
  onLogout: () => Promise<void>
}

type Tab = "overview" | "editor" | "history"

export default function WorkflowScreen({
  project,
  details,
  user,
  csrfToken,
  onBack,
  onUnauthorized,
  onAccessLost,
  onLogout,
}: Props) {
  const [tab, setTab] = useState<Tab>("overview")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null)
  const [chapterSteps, setChapterSteps] = useState<Map<string, { status: string; output_json: Record<string, unknown> }>>(new Map())

  // Filters
  const [filterChapter, setFilterChapter] = useState<string>("ALL")
  const [searchQuery, setSearchQuery] = useState("")

  // Prompt modal
  const [selectedPrompt, setSelectedPrompt] = useState<EffectivePrompt | null>(null)
  const [loadingPrompt, setLoadingPrompt] = useState(false)

  // Step execute / save modal
  const [stepModalTask, setStepModalTask] = useState<WorkflowTask | null>(null)
  const [stepContentMd, setStepContentMd] = useState("")
  const [stepOutputJsonText, setStepOutputJsonText] = useState("{}")
  const [stepInputJsonText, setStepInputJsonText] = useState("{}")
  const [savingStep, setSavingStep] = useState(false)
  const [stepModalError, setStepModalError] = useState<string | null>(null)

  // Draft Editor local state
  const [draftTasks, setDraftTasks] = useState<WorkflowTask[]>([])
  const [draftDirty, setDraftDirty] = useState(false)
  const [savingDraft, setSavingDraft] = useState(false)
  const [validationResult, setValidationResult] = useState<WorkflowValidationResult | null>(null)
  const [validatingDraft, setValidatingDraft] = useState(false)

  // Publish / Restore modals
  const [showPublishModal, setShowPublishModal] = useState(false)
  const [publishSummary, setPublishSummary] = useState("")
  const [publishing, setPublishing] = useState(false)

  const [restoreTargetVersion, setRestoreTargetVersion] = useState<number | null>(null)
  const [restoreSummary, setRestoreSummary] = useState("")
  const [restoring, setRestoring] = useState(false)

  // New Custom Task modal
  const [showNewTaskModal, setShowNewTaskModal] = useState(false)
  const [newTaskId, setNewTaskId] = useState("USR_NUEVA_TAREA")
  const [newTaskTitle, setNewTaskTitle] = useState("")
  const [newTaskPrompt, setNewTaskPrompt] = useState("")
  const [newTaskChapter, setNewTaskChapter] = useState<number | null>(1)
  const [newTaskError, setNewTaskError] = useState<string | null>(null)

  const loadSeq = useRef(0)
  const canManage = project.role === "OWNER" && project.permissions.can_manage_workflow

  // Load workflow & chapter states
  const reloadData = useCallback(async () => {
    const seq = ++loadSeq.current
    setLoading(true)
    setError(null)
    try {
      const state = await getWorkflowState(project.project_id)
      if (seq !== loadSeq.current) return
      setWorkflowState(state)

      // Initialize draft editing state if draft exists or fallback to published tasks
      const sourceTasks = state.draft?.tasks ?? state.published?.tasks ?? []
      setDraftTasks(structuredClone(sourceTasks))
      setDraftDirty(false)

      // Fetch progress across chapters 1-7
      const stepMap = new Map<string, { status: string; output_json: Record<string, unknown> }>()
      const chaptersPromises = [1, 2, 3, 4, 5, 6, 7].map(async (ch) => {
        try {
          const chData = await getChapterState(project.project_id, ch)
          for (const s of chData.steps) {
            stepMap.set(s.step_code, { status: s.status, output_json: s.output_json })
          }
        } catch {
          // Chapter might not exist yet; ignore
        }
      })
      await Promise.all(chaptersPromises)
      if (seq !== loadSeq.current) return
      setChapterSteps(stepMap)
    } catch (cause) {
      if (seq !== loadSeq.current) return
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
      else if (cause instanceof ApiError && cause.status === 404) onAccessLost()
      else setError(cause instanceof Error ? cause.message : "Error al cargar el recorrido")
    } finally {
      if (seq === loadSeq.current) setLoading(false)
    }
  }, [project.project_id, onUnauthorized, onAccessLost])

  useEffect(() => {
    void reloadData()
  }, [reloadData])

  // Prevent leaving with unsaved draft changes
  useEffect(() => {
    if (!draftDirty) return
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault()
      event.returnValue = ""
    }
    window.addEventListener("beforeunload", warn)
    return () => window.removeEventListener("beforeunload", warn)
  }, [draftDirty])

  // Real progress calculation
  const progressStats = useMemo(() => {
    const published = workflowState?.published
    if (!published) return { totalActive: 0, completed: 0, percentage: 0 }
    const activeTasks = published.tasks.filter((t) => t.is_active)
    let completed = 0
    for (const t of activeTasks) {
      if (t.legacy_step_code && chapterSteps.get(t.legacy_step_code)?.status === "COMPLETED") {
        completed++
      }
    }
    const totalActive = activeTasks.length
    const percentage = totalActive > 0 ? Math.round((completed / totalActive) * 100) : 0
    return { totalActive, completed, percentage }
  }, [workflowState, chapterSteps])

  // Filtered tasks for viewing
  const displayedTasks = useMemo(() => {
    const tasks = workflowState?.published?.tasks ?? []
    return tasks.filter((t) => {
      if (filterChapter !== "ALL") {
        if (filterChapter === "NONE" && t.chapter_no !== null) return false
        if (filterChapter !== "NONE" && String(t.chapter_no) !== filterChapter) return false
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        return (
          t.task_id.toLowerCase().includes(q) ||
          t.title.toLowerCase().includes(q) ||
          t.description.toLowerCase().includes(q)
        )
      }
      return true
    })
  }, [workflowState, filterChapter, searchQuery])

  // Prompt view handler
  async function handleViewPrompt(taskId: string) {
    setLoadingPrompt(true)
    setError(null)
    try {
      const prompt = await getEffectivePrompt(project.project_id, taskId)
      setSelectedPrompt(prompt)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo consultar el prompt.")
    } finally {
      setLoadingPrompt(false)
    }
  }

  // Open step execution/save modal
  function handleOpenStepModal(task: WorkflowTask) {
    setStepModalTask(task)
    setStepModalError(null)
    if (task.legacy_step_code) {
      const existing = chapterSteps.get(task.legacy_step_code)
      setStepContentMd("")
      setStepOutputJsonText(existing ? JSON.stringify(existing.output_json, null, 2) : "{}")
    } else {
      setStepInputJsonText("{}")
      setStepOutputJsonText("{}")
    }
  }

  // Submit step execution/save
  async function handleSaveStepSubmit() {
    if (!stepModalTask) return
    setSavingStep(true)
    setStepModalError(null)
    let parsedOutput: Record<string, unknown>
    try {
      parsedOutput = JSON.parse(stepOutputJsonText)
    } catch {
      setStepModalError("El JSON de salida estructurada tiene un error de sintaxis.")
      setSavingStep(false)
      return
    }

    try {
      if (stepModalTask.legacy_step_code) {
        if (!stepContentMd.trim()) {
          setStepModalError("El contenido en Markdown de la revisión no puede estar vacío.")
          setSavingStep(false)
          return
        }
        await saveStep(
          project.project_id,
          stepModalTask.legacy_step_code,
          {
            content_md: stepContentMd,
            output_data: parsedOutput,
            expected_version: details.state_version,
            idempotency_key: crypto.randomUUID(),
          },
          csrfToken,
        )
        setNotice(`Paso ${stepModalTask.legacy_step_code} guardado con éxito.`)
      } else {
        let parsedInput = {}
        try {
          parsedInput = JSON.parse(stepInputJsonText)
        } catch {
          setStepModalError("El JSON de entrada tiene un error de sintaxis.")
          setSavingStep(false)
          return
        }
        await executeCustomWorkflowTask(
          project.project_id,
          stepModalTask.task_id,
          {
            input_data: parsedInput,
            output_data: parsedOutput,
            idempotency_key: crypto.randomUUID(),
          },
          csrfToken,
        )
        setNotice(`Tarea ${stepModalTask.task_id} ejecutada y guardada.`)
      }
      setStepModalTask(null)
      void reloadData()
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 409) {
        setStepModalError("Conflicto de versión (409): el perfil cambió o la versión esperada no coincide. Tu texto se conserva aquí; recarga los datos si es necesario.")
      } else if (cause instanceof ApiError && cause.detail.includes("PREREQUISITE_LOCKED")) {
        setStepModalError(`Bloqueado por prerrequisito: ${cause.detail}`)
      } else {
        setStepModalError(cause instanceof Error ? cause.message : "Error al guardar el paso.")
      }
    } finally {
      setSavingStep(false)
    }
  }

  // Draft operations
  function handleToggleActive(taskId: string) {
    setDraftTasks((prev) =>
      prev.map((t) => {
        if (t.task_id !== taskId) return t
        if (t.is_protected) return t
        return { ...t, is_active: !t.is_active }
      }),
    )
    setDraftDirty(true)
    setValidationResult(null)
  }

  function handleToggleOptional(taskId: string) {
    setDraftTasks((prev) =>
      prev.map((t) => {
        if (t.task_id !== taskId) return t
        if (t.is_protected) return t
        return { ...t, is_optional: !t.is_optional }
      }),
    )
    setDraftDirty(true)
    setValidationResult(null)
  }

  function handleMoveTask(index: number, delta: -1 | 1) {
    const target = index + delta
    if (target < 0 || target >= draftTasks.length) return
    const next = [...draftTasks]
    const temp = next[index]
    next[index] = next[target]
    next[target] = temp
    // Recalculate order_index
    const reordered = next.map((t, idx) => ({ ...t, order_index: idx + 1 }))
    setDraftTasks(reordered)
    setDraftDirty(true)
    setValidationResult(null)
  }

  function handleUpdatePromptText(taskId: string, newText: string) {
    setDraftTasks((prev) =>
      prev.map((t) => {
        if (t.task_id !== taskId) return t
        const currentPrompt = t.prompt ?? {
          prompt_text: "",
          prompt_version: 1,
          provenance: "USER_EDITED",
          parameters_schema: {},
        }
        return {
          ...t,
          prompt: { ...currentPrompt, prompt_text: newText },
        }
      }),
    )
    setDraftDirty(true)
    setValidationResult(null)
  }

  async function handleSaveDraft() {
    if (!workflowState) return
    setSavingDraft(true)
    setError(null)
    setNotice(null)
    const expectedVersion = workflowState.draft?.lock_version ?? 0
    const payload: WorkflowDraftInput = {
      tasks: draftTasks.map((t) => ({
        task_id: t.task_id,
        title: t.title,
        description: t.description,
        chapter_no: t.chapter_no,
        order_index: t.order_index,
        is_active: t.is_active,
        is_optional: t.is_optional,
        prompt_text: t.prompt?.prompt_text,
      })),
      dependencies: workflowState.draft?.dependencies ?? workflowState.published?.dependencies ?? [],
      expected_version: expectedVersion,
    }

    try {
      const updated = await updateWorkflowDraft(project.project_id, payload, csrfToken)
      setWorkflowState(updated)
      setDraftDirty(false)
      setNotice("Borrador del recorrido guardado con éxito.")
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 409) {
        setError("Conflicto de concurrencia (409): el borrador cambió en el servidor. Tus cambios no se han borrado de la pantalla; verifica antes de sobreescribir.")
      } else {
        setError(cause instanceof Error ? cause.message : "Error al guardar el borrador.")
      }
    } finally {
      setSavingDraft(false)
    }
  }

  async function handleValidateDraft() {
    setValidatingDraft(true)
    setError(null)
    try {
      const res = await validateWorkflowDraft(project.project_id, csrfToken)
      setValidationResult(res)
      if (res.valid) {
        setNotice("El borrador es estructuralmente válido (sin ciclos ni infracciones de núcleo).")
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al validar el borrador.")
    } finally {
      setValidatingDraft(false)
    }
  }

  async function handlePublishDraft() {
    if (!workflowState?.draft) return
    setPublishing(true)
    setError(null)
    try {
      const updated = await publishWorkflowDraft(
        project.project_id,
        {
          change_summary: publishSummary.trim() || "Nueva versión publicada",
          expected_version: workflowState.draft.lock_version,
        },
        csrfToken,
      )
      setWorkflowState(updated)
      setShowPublishModal(false)
      setPublishSummary("")
      setDraftDirty(false)
      setNotice(`Versión ${updated.published?.version_no} publicada exitosamente.`)
      setTab("overview")
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 409) {
        setError("Conflicto al publicar: el borrador cambió antes de confirmarlo.")
      } else {
        setError(cause instanceof Error ? cause.message : "Error al publicar el recorrido.")
      }
    } finally {
      setPublishing(false)
    }
  }

  async function handleRestoreVersion() {
    if (restoreTargetVersion === null) return
    setRestoring(true)
    setError(null)
    try {
      const updated = await restoreWorkflowVersion(
        project.project_id,
        {
          target_version_no: restoreTargetVersion,
          change_summary: restoreSummary.trim() || `Restaurado a versión ${restoreTargetVersion}`,
        },
        csrfToken,
      )
      setWorkflowState(updated)
      setRestoreTargetVersion(null)
      setRestoreSummary("")
      setNotice(`Se restauró la versión ${restoreTargetVersion} como nueva versión publicada.`)
      setTab("overview")
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al restaurar la versión.")
    } finally {
      setRestoring(false)
    }
  }

  function handleAddCustomTask() {
    setNewTaskError(null)
    const id = newTaskId.trim()
    if (!id.startsWith("USR_") || id.length < 8) {
      setNewTaskError("El ID de la tarea personalizada debe comenzar con USR_ y tener al menos 8 caracteres (ej. USR_ENTREVISTAS).")
      return
    }
    if (!newTaskTitle.trim()) {
      setNewTaskError("El título de la tarea no puede estar vacío.")
      return
    }
    if (!newTaskPrompt.trim()) {
      setNewTaskError("El prompt inicial no puede estar vacío.")
      return
    }
    if (draftTasks.some((t) => t.task_id === id)) {
      setNewTaskError("Ya existe una tarea con ese ID en el recorrido.")
      return
    }

    const newTask: WorkflowTask = {
      task_id: id,
      legacy_step_code: "",
      title: newTaskTitle.trim(),
      description: "Tarea metodológica personalizada",
      chapter_no: newTaskChapter,
      order_index: draftTasks.length + 1,
      is_active: true,
      is_optional: true,
      is_protected: false,
      contract_name: "",
      branch_condition: "",
      prompt: {
        prompt_text: newTaskPrompt.trim(),
        prompt_version: 1,
        provenance: "USER_EDITED",
        parameters_schema: {},
      },
    }

    setDraftTasks((prev) => [...prev, newTask])
    setDraftDirty(true)
    setShowNewTaskModal(false)
    setNewTaskId("USR_NUEVA_TAREA")
    setNewTaskTitle("")
    setNewTaskPrompt("")
    setNewTaskChapter(1)
  }

  return (
    <div className="connected-app-shell">
      <aside className="sidebar connected-sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">T</div>
          <div><b>TesisMCP</b><span>Recorrido metodológico</span></div>
        </div>
        <div className="connected-project-sidebar">
          <span className="eyebrow">PROYECTO ACTIVO</span>
          <strong>{project.name}</strong>
          <span>{project.role === "OWNER" ? "Tesista" : "Asesor"}</span>
        </div>
        <div className="sidebar-bottom">
          <button className="nav-item connected-change-project" type="button" onClick={onBack}>
            ← Volver al espacio
          </button>
          <div className="profile">
            <div className="avatar">{(user.display_name || user.email).slice(0, 1).toUpperCase()}</div>
            <div><b>{user.display_name || user.email}</b><span>{project.role === "OWNER" ? "Tesista" : "Asesor"}</span></div>
          </div>
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>{project.name}</span>
            <strong>Recorrido metodológico y tareas</strong>
          </div>
          <div className="top-actions">
            <span className="real-connection-pill"><i />Conectado a Django</span>
            <button className="button button-secondary" type="button" onClick={() => void onLogout()}>
              Cerrar sesión
            </button>
          </div>
        </header>

        <main className="workflow-page">
          <div className="workflow-header">
            <div>
              <span className="eyebrow blue">CONFIGURACIÓN ACADÉMICA DEL PROYECTO</span>
              <h1>Recorrido metodológico configurable</h1>
              <p>Tareas, dependencias, prompts versionados y guardado de pasos metodológicos.</p>
            </div>
            <div>
              {workflowState?.published && (
                <span className="status status-success">
                  <span className="status-dot" />
                  Versión {workflowState.published.version_no} publicada
                </span>
              )}
            </div>
          </div>

          {error && <div className="chapter-alert" role="alert">{error}</div>}
          {notice && <div className="chapter-notice" role="status">{notice}</div>}

          {/* Real progress card */}
          <section className="workflow-progress-card">
            <div className="workflow-progress-info">
              <span className="eyebrow">AVANCE METODOLÓGICO REAL</span>
              <h3>
                {progressStats.completed} de {progressStats.totalActive} tareas activas completadas
              </h3>
              <p>
                Calculado a partir de revisiones completadas en la base de datos (
                {progressStats.percentage}% de ruta activa).
              </p>
            </div>
            <div className="workflow-progress-bar-wrap">
              <div className="workflow-progress-bar" role="progressbar" aria-valuenow={progressStats.percentage} aria-valuemin={0} aria-valuemax={100}>
                <div className="workflow-progress-fill" style={{ width: `${progressStats.percentage}%` }} />
              </div>
            </div>
          </section>

          {/* Navigation tabs */}
          <nav className="workflow-nav-tabs" aria-label="Secciones del recorrido">
            <button
              className={`workflow-nav-tab ${tab === "overview" ? "active" : ""}`}
              onClick={() => setTab("overview")}
              type="button"
            >
              Tareas y dependencias ({workflowState?.published?.tasks.length ?? 0})
            </button>
            <button
              className={`workflow-nav-tab ${tab === "editor" ? "active" : ""}`}
              onClick={() => setTab("editor")}
              type="button"
            >
              Editor del recorrido {draftDirty ? "●" : ""}
            </button>
            <button
              className={`workflow-nav-tab ${tab === "history" ? "active" : ""}`}
              onClick={() => setTab("history")}
              type="button"
            >
              Historial de versiones ({workflowState?.history.length ?? 0})
            </button>
          </nav>

          {loading ? (
            <div className="chapter-empty">Cargando estado del recorrido desde el backend…</div>
          ) : (
            <>
              {/* TAB 1: OVERVIEW */}
              {tab === "overview" && (
                <div>
                  <div className="workflow-filters">
                    <label htmlFor="filter-chapter" className="sr-only">Filtrar por capítulo</label>
                    <select
                      id="filter-chapter"
                      value={filterChapter}
                      onChange={(e) => setFilterChapter(e.target.value)}
                    >
                      <option value="ALL">Todos los capítulos</option>
                      <option value="1">Capítulo 1: Introducción</option>
                      <option value="2">Capítulo 2: Marco Teórico</option>
                      <option value="3">Capítulo 3: Metodología</option>
                      <option value="4">Capítulo 4: Resultados</option>
                      <option value="5">Capítulo 5: Discusión</option>
                      <option value="6">Capítulo 6: Conclusiones</option>
                      <option value="7">Capítulo 7: Recomendaciones</option>
                      <option value="NONE">Sin capítulo asignado</option>
                    </select>

                    <label htmlFor="search-tasks" className="sr-only">Buscar tarea</label>
                    <input
                      id="search-tasks"
                      type="search"
                      placeholder="Buscar por ID, título o descripción…"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>

                  <div className="workflow-task-grid">
                    {displayedTasks.map((t) => {
                      const completed = t.legacy_step_code
                        ? chapterSteps.get(t.legacy_step_code)?.status === "COMPLETED"
                        : false
                      const isP26P27 = t.task_id === "P26" || t.task_id === "P27"

                      return (
                        <article
                          key={t.task_id}
                          className={`workflow-task-card ${!t.is_active ? "inactive" : ""}`}
                        >
                          <div className="workflow-task-top">
                            <div className="workflow-task-title-group">
                              <span className="workflow-task-id-badge">{t.task_id}</span>
                              <h2 className="workflow-task-title">{t.title}</h2>
                            </div>
                            <div className="workflow-task-badges">
                              {t.is_protected && (
                                <span className="workflow-badge-protected">Núcleo protegido</span>
                              )}
                              {t.is_optional && (
                                <span className="workflow-badge-optional">Opcional</span>
                              )}
                              {t.chapter_no && (
                                <span className="workflow-badge-chapter">Capítulo {t.chapter_no}</span>
                              )}
                              {completed ? (
                                <span className="status status-success"><span className="status-dot" />Completado</span>
                              ) : t.is_active ? (
                                <span className="status"><span className="status-dot" />Pendiente</span>
                              ) : (
                                <span className="status status-warning">Inactivo</span>
                              )}
                            </div>
                          </div>

                          {t.description && <p className="workflow-task-desc">{t.description}</p>}

                          {isP26P27 && (
                            <div className="workflow-p26-banner">
                              <strong>Definición metodológica pendiente con el asesor / profesor:</strong>{" "}
                              El piloto académico de TesisMCP se detiene antes de elaborar o aplicar instrumentos.
                              Esta tarea permanece en el catálogo pero requiere acuerdo académico explícito.
                            </div>
                          )}

                          {/* Dependencies */}
                          {workflowState?.published?.dependencies.filter((d) => d.source === t.task_id).length ? (
                            <div className="workflow-task-deps">
                              <strong>Prerrequisitos de entrada:</strong>
                              <ul style={{ margin: "4px 0 0", paddingLeft: "16px" }}>
                                {workflowState.published.dependencies
                                  .filter((d) => d.source === t.task_id)
                                  .map((d, idx) => (
                                    <li key={idx}>
                                      Requiere de <strong>{d.target}</strong>
                                      {d.field ? ` (campo: ${d.field})` : ""}
                                      {d.blocking ? " · Bloqueante" : " · Informativo"}
                                      {d.reason ? ` — ${d.reason}` : ""}
                                    </li>
                                  ))}
                              </ul>
                            </div>
                          ) : null}

                          <div className="workflow-task-actions">
                            <button
                              className="button button-secondary"
                              type="button"
                              onClick={() => void handleViewPrompt(t.task_id)}
                              disabled={loadingPrompt}
                            >
                              Ver prompt
                            </button>
                            {project.role === "OWNER" && t.is_active && (
                              <button
                                className="button button-primary"
                                type="button"
                                onClick={() => handleOpenStepModal(t)}
                              >
                                {completed ? "Actualizar paso" : "Guardar paso"}
                              </button>
                            )}
                          </div>
                        </article>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* TAB 2: EDITOR */}
              {tab === "editor" && (
                <div>
                  {!canManage ? (
                    <div className="chapter-info">
                      <strong>Modo de consulta (Asesor / Rol sin gestión de flujo):</strong> Solo el
                      tesista titular con permisos puede modificar el orden, activar o desactivar tareas
                      y publicar nuevas versiones del recorrido.
                    </div>
                  ) : (
                    <div>
                      <div className="chapter-info" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                        <div>
                          <strong>Versión borrador editable</strong>
                          <p style={{ margin: "4px 0 0", fontSize: "11px" }}>
                            {workflowState?.draft
                              ? `Borrador activo (lock_version: ${workflowState.draft.lock_version}). Puedes reordenar, activar/desactivar y ajustar prompts.`
                              : "No hay borrador pendiente. Al guardar cualquier cambio se creará una versión borrador clonada de la versión publicada."}
                          </p>
                        </div>
                        <div style={{ display: "flex", gap: "8px" }}>
                          <button
                            className="button button-secondary"
                            type="button"
                            onClick={() => setShowNewTaskModal(true)}
                          >
                            + Tarea personalizada (USR_)
                          </button>
                          <button
                            className="button button-secondary"
                            type="button"
                            onClick={() => void handleValidateDraft()}
                            disabled={validatingDraft}
                          >
                            {validatingDraft ? "Validando…" : "Validar borrador"}
                          </button>
                          <button
                            className="button button-primary"
                            type="button"
                            onClick={() => void handleSaveDraft()}
                            disabled={savingDraft || !draftDirty}
                          >
                            {savingDraft ? "Guardando…" : "Guardar borrador"}
                          </button>
                          <button
                            className="button button-primary"
                            type="button"
                            onClick={() => setShowPublishModal(true)}
                            disabled={!workflowState?.draft || draftDirty}
                          >
                            Publicar recorrido
                          </button>
                        </div>
                      </div>

                      {/* Validation results banner */}
                      {validationResult && (
                        <div
                          className={validationResult.valid ? "chapter-notice" : "chapter-alert"}
                          style={{ margin: "14px 0" }}
                        >
                          <strong>{validationResult.valid ? "✓ Validación exitosa" : "✗ Errores de validación estructural:"}</strong>
                          {validationResult.errors.length > 0 && (
                            <ul style={{ margin: "6px 0 0", paddingLeft: "18px" }}>
                              {validationResult.errors.map((err, i) => (
                                <li key={i}>{err}</li>
                              ))}
                            </ul>
                          )}
                          {validationResult.warnings.length > 0 && (
                            <ul style={{ margin: "6px 0 0", paddingLeft: "18px", color: "var(--amber)" }}>
                              {validationResult.warnings.map((w, i) => (
                                <li key={i}>Advertencia: {w}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      )}

                      {/* Tasks editor list */}
                      <div className="workflow-task-grid" style={{ marginTop: "16px" }}>
                        {draftTasks.map((t, idx) => (
                          <div
                            key={t.task_id}
                            className={`workflow-task-card ${!t.is_active ? "inactive" : ""}`}
                          >
                            <div className="workflow-task-top">
                              <div className="workflow-task-title-group">
                                <span className="workflow-task-id-badge">{t.task_id}</span>
                                <strong>{t.title}</strong>
                                <span style={{ fontSize: "11px", color: "var(--muted)" }}>
                                  Orden: #{t.order_index}
                                </span>
                              </div>
                              <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                                <button
                                  className="button button-secondary"
                                  style={{ minHeight: "28px", padding: "0 8px" }}
                                  disabled={idx === 0}
                                  onClick={() => handleMoveTask(idx, -1)}
                                  type="button"
                                  title="Subir orden"
                                >
                                  ▲
                                </button>
                                <button
                                  className="button button-secondary"
                                  style={{ minHeight: "28px", padding: "0 8px" }}
                                  disabled={idx === draftTasks.length - 1}
                                  onClick={() => handleMoveTask(idx, 1)}
                                  type="button"
                                  title="Bajar orden"
                                >
                                  ▼
                                </button>
                              </div>
                            </div>

                            <div style={{ display: "flex", gap: "16px", margin: "12px 0 8px", flexWrap: "wrap", fontSize: "12px" }}>
                              <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                                <input
                                  type="checkbox"
                                  checked={t.is_active}
                                  disabled={t.is_protected}
                                  onChange={() => handleToggleActive(t.task_id)}
                                />
                                Activa
                                {t.is_protected && <small style={{ color: "var(--muted)" }}> (Protegida)</small>}
                              </label>

                              <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                                <input
                                  type="checkbox"
                                  checked={t.is_optional}
                                  disabled={t.is_protected}
                                  onChange={() => handleToggleOptional(t.task_id)}
                                />
                                Opcional
                              </label>
                            </div>

                            {/* Prompt editor snippet */}
                            <div style={{ marginTop: "10px" }}>
                              <label style={{ fontSize: "11px", fontWeight: 600, color: "var(--navy)", display: "block", marginBottom: "4px" }}>
                                Prompt de la tarea {t.prompt ? `(v${t.prompt.prompt_version})` : ""}:
                              </label>
                              <textarea
                                style={{ width: "100%", minHeight: "64px", fontSize: "12px", padding: "8px", border: "1px solid var(--line)", borderRadius: "6px" }}
                                value={t.prompt?.prompt_text ?? ""}
                                onChange={(e) => handleUpdatePromptText(t.task_id, e.target.value)}
                                placeholder="Escribe las instrucciones del prompt para esta tarea…"
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: HISTORY */}
              {tab === "history" && (
                <div>
                  <div className="chapter-info">
                    <strong>Inmutabilidad y trazabilidad académica:</strong> Cada publicación genera una
                    versión inmutable con su hash SHA-256 de contenido. Puedes restaurar una versión
                    anterior creando una nueva publicación sin alterar las revisiones pasadas.
                  </div>

                  <div style={{ marginTop: "16px" }}>
                    {workflowState?.history.map((h) => (
                      <div key={h.version_no} className="workflow-history-item">
                        <div className="workflow-history-info">
                          <b>Versión {h.version_no} · {h.status}</b>
                          <span>Resumen: {h.change_summary || "Sin resumen"}</span>
                          <div style={{ marginTop: "4px", fontSize: "10px", color: "var(--muted)" }}>
                            Hash SHA-256: <code>{h.content_sha256 ? `${h.content_sha256.slice(0, 16)}…` : "—"}</code> · Fecha: {new Date(h.created_at).toLocaleString()}
                          </div>
                        </div>
                        {canManage && h.status !== "DRAFT" && (
                          <button
                            className="button button-secondary"
                            type="button"
                            onClick={() => {
                              setRestoreTargetVersion(h.version_no)
                              setRestoreSummary(`Restauración a versión ${h.version_no}`)
                            }}
                          >
                            Restaurar versión
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* VIEW PROMPT MODAL */}
          {selectedPrompt && (
            <div className="workflow-modal-backdrop" onClick={() => setSelectedPrompt(null)}>
              <div className="workflow-modal-card" onClick={(e) => e.stopPropagation()}>
                <span className="eyebrow blue">PROMPT EFECTIVO · VERSIÓN {selectedPrompt.prompt_version}</span>
                <h2>{selectedPrompt.task_id} — {selectedPrompt.title}</h2>
                <p>
                  Origen: <b>{selectedPrompt.provenance}</b> · Recorrido versión #{selectedPrompt.workflow_version_no}
                  {selectedPrompt.is_protected ? " · Núcleo protegido UTP" : ""}
                </p>
                <textarea
                  readOnly
                  value={selectedPrompt.prompt_text || "Esta tarea no tiene texto de prompt asignado."}
                />
                <div style={{ marginTop: "18px", display: "flex", justifyContent: "flex-end" }}>
                  <button className="button button-primary" type="button" onClick={() => setSelectedPrompt(null)}>
                    Cerrar
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP EXECUTION / SAVE MODAL */}
          {stepModalTask && (
            <div className="workflow-modal-backdrop" onClick={() => setStepModalTask(null)}>
              <div className="workflow-modal-card" onClick={(e) => e.stopPropagation()}>
                <span className="eyebrow blue">
                  {stepModalTask.legacy_step_code ? "GUARDAR PASO METODOLÓGICO" : "EJECUTAR TAREA PERSONALIZADA"}
                </span>
                <h2>{stepModalTask.task_id} — {stepModalTask.title}</h2>
                <p>
                  {stepModalTask.legacy_step_code
                    ? `Paso P01–P32 enlazado al Capítulo ${stepModalTask.chapter_no}. Requiere contenido Markdown y salida JSON validada.`
                    : "Tarea personalizada USR_. Registra una ejecución con contrato estructurado JSON."}
                </p>

                {stepModalError && <div className="chapter-alert" role="alert">{stepModalError}</div>}

                {stepModalTask.legacy_step_code ? (
                  <>
                    <div style={{ marginBottom: "14px" }}>
                      <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                        Contenido en Markdown de la revisión académica:
                      </label>
                      <textarea
                        value={stepContentMd}
                        onChange={(e) => setStepContentMd(e.target.value)}
                        placeholder="# Avance metodológico&#10;&#10;Redacta aquí el texto del paso…"
                        style={{ minHeight: "120px" }}
                      />
                    </div>
                    <div style={{ marginBottom: "14px" }}>
                      <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                        Salida estructurada (JSON validado por contrato Pydantic):
                      </label>
                      <textarea
                        value={stepOutputJsonText}
                        onChange={(e) => setStepOutputJsonText(e.target.value)}
                        style={{ minHeight: "120px" }}
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ marginBottom: "14px" }}>
                      <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                        Entrada (JSON input_data):
                      </label>
                      <textarea
                        value={stepInputJsonText}
                        onChange={(e) => setStepInputJsonText(e.target.value)}
                        style={{ minHeight: "80px" }}
                      />
                    </div>
                    <div style={{ marginBottom: "14px" }}>
                      <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                        Salida producida (JSON output_data):
                      </label>
                      <textarea
                        value={stepOutputJsonText}
                        onChange={(e) => setStepOutputJsonText(e.target.value)}
                        style={{ minHeight: "120px" }}
                      />
                    </div>
                  </>
                )}

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "16px" }}>
                  <button
                    className="button button-secondary"
                    type="button"
                    onClick={() => setStepModalTask(null)}
                    disabled={savingStep}
                  >
                    Cancelar
                  </button>
                  <button
                    className="button button-primary"
                    type="button"
                    onClick={() => void handleSaveStepSubmit()}
                    disabled={savingStep}
                  >
                    {savingStep ? "Guardando…" : "Guardar en backend"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* PUBLISH MODAL */}
          {showPublishModal && (
            <div className="workflow-modal-backdrop" onClick={() => setShowPublishModal(false)}>
              <div className="workflow-modal-card" onClick={(e) => e.stopPropagation()}>
                <span className="eyebrow blue">CONFIRMACIÓN INMUTABLE</span>
                <h2>Publicar nueva versión del recorrido</h2>
                <p>
                  Se validará la consistencia del grafo, se calculará el hash criptográfico del recorrido
                  y se activará el modo de grafo configurable en el perfil de investigación.
                </p>
                <div style={{ marginBottom: "16px" }}>
                  <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                    Resumen de cambios para la auditoría:
                  </label>
                  <input
                    type="text"
                    value={publishSummary}
                    onChange={(e) => setPublishSummary(e.target.value)}
                    placeholder="Ej. Reordenamiento de literatura y nueva tarea de entrevista"
                    style={{ width: "100%", height: "38px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px" }}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                  <button
                    className="button button-secondary"
                    type="button"
                    onClick={() => setShowPublishModal(false)}
                    disabled={publishing}
                  >
                    Cancelar
                  </button>
                  <button
                    className="button button-primary"
                    type="button"
                    onClick={() => void handlePublishDraft()}
                    disabled={publishing}
                  >
                    {publishing ? "Publicando…" : "Confirmar publicación"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* RESTORE MODAL */}
          {restoreTargetVersion !== null && (
            <div className="workflow-modal-backdrop" onClick={() => setRestoreTargetVersion(null)}>
              <div className="workflow-modal-card" onClick={(e) => e.stopPropagation()}>
                <span className="eyebrow blue">RESTAURACIÓN HISTÓRICA</span>
                <h2>Restaurar a versión {restoreTargetVersion}</h2>
                <p>
                  Esta acción clonará la configuración histórica de la versión {restoreTargetVersion} y
                  la publicará como una nueva versión inmutable sin alterar el historial existente.
                </p>
                <div style={{ marginBottom: "16px" }}>
                  <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                    Motivo o resumen de restauración:
                  </label>
                  <input
                    type="text"
                    value={restoreSummary}
                    onChange={(e) => setRestoreSummary(e.target.value)}
                    style={{ width: "100%", height: "38px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px" }}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                  <button
                    className="button button-secondary"
                    type="button"
                    onClick={() => setRestoreTargetVersion(null)}
                    disabled={restoring}
                  >
                    Cancelar
                  </button>
                  <button
                    className="button button-primary"
                    type="button"
                    onClick={() => void handleRestoreVersion()}
                    disabled={restoring}
                  >
                    {restoring ? "Restaurando…" : "Confirmar restauración"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* NEW CUSTOM TASK MODAL */}
          {showNewTaskModal && (
            <div className="workflow-modal-backdrop" onClick={() => setShowNewTaskModal(false)}>
              <div className="workflow-modal-card" onClick={(e) => e.stopPropagation()}>
                <span className="eyebrow blue">NUEVA TAREA PERSONALIZADA</span>
                <h2>Crear tarea USR_</h2>
                <p>
                  Agrega una tarea personalizada al borrador. Requiere un ID con prefijo <code>USR_</code>,
                  título y prompt inicial.
                </p>

                {newTaskError && <div className="chapter-alert" role="alert">{newTaskError}</div>}

                <div style={{ display: "grid", gap: "12px" }}>
                  <div>
                    <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                      Identificador único (ID):
                    </label>
                    <input
                      type="text"
                      value={newTaskId}
                      onChange={(e) => setNewTaskId(e.target.value.toUpperCase())}
                      placeholder="USR_ENTREVISTA_PILOTO"
                      style={{ width: "100%", height: "36px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px" }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                      Título de la tarea:
                    </label>
                    <input
                      type="text"
                      value={newTaskTitle}
                      onChange={(e) => setNewTaskTitle(e.target.value)}
                      placeholder="Ej. Entrevistas semiestructuradas a docentes"
                      style={{ width: "100%", height: "36px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px" }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                      Capítulo asociado (opcional):
                    </label>
                    <select
                      value={newTaskChapter ?? ""}
                      onChange={(e) => setNewTaskChapter(e.target.value ? Number(e.target.value) : null)}
                      style={{ width: "100%", height: "36px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px" }}
                    >
                      <option value="">Sin capítulo asignado</option>
                      <option value="1">Capítulo 1: Introducción</option>
                      <option value="2">Capítulo 2: Marco Teórico</option>
                      <option value="3">Capítulo 3: Metodología</option>
                      <option value="4">Capítulo 4: Resultados</option>
                      <option value="5">Capítulo 5: Discusión</option>
                      <option value="6">Capítulo 6: Conclusiones</option>
                      <option value="7">Capítulo 7: Recomendaciones</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                      Prompt de la tarea:
                    </label>
                    <textarea
                      value={newTaskPrompt}
                      onChange={(e) => setNewTaskPrompt(e.target.value)}
                      placeholder="Instrucciones metodológicas que orientan esta tarea…"
                      style={{ minHeight: "100px" }}
                    />
                  </div>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "18px" }}>
                  <button
                    className="button button-secondary"
                    type="button"
                    onClick={() => setShowNewTaskModal(false)}
                  >
                    Cancelar
                  </button>
                  <button
                    className="button button-primary"
                    type="button"
                    onClick={handleAddCustomTask}
                  >
                    Agregar al borrador
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
