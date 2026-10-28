import { useEffect, useRef, useState } from "react"
import {
  acceptProposal,
  cancelBatchSynthesis,
  cancelGenerationBatch,
  cancelGenerationJob,
  createBatchSynthesis,
  createGenerationBatch,
  decideBatchSynthesis,
  generateProposal,
  getGenerationBatch,
  getGenerationDocumentDiff,
  getGenerationJob,
  listBatchSyntheses,
  listGenerationBatches,
  rejectProposal,
} from "../../api/generation"
import type {
  AIBatch,
  AIGenerationJob,
  BatchSynthesis,
  DocumentDiff,
  WorkflowState,
  WorkflowTask,
} from "../../api/types"
import { getWorkflowState } from "../../api/workflows"

function generateUuid(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID()
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === "x" ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

export type AIAssistantScreenProps = {
  projectId: string
  projectName: string
  canWrite: boolean
  csrfToken?: string
  stateVersion: number
  onBack: () => void
  onStateVersionChanged?: (newVersion: number) => void
}

type TabKey = "proposals" | "batches" | "byoa"

export function AIAssistantScreen({
  projectId,
  projectName,
  canWrite,
  csrfToken,
  stateVersion,
  onBack,
  onStateVersionChanged,
}: AIAssistantScreenProps) {
  const [activeTab, setActiveTab] = useState<TabKey>(canWrite ? "proposals" : "batches")
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null)
  const [selectedTaskId, setSelectedTaskId] = useState<string>("P01")
  const [inputJson, setInputJson] = useState<string>("{}")
  const [activeJob, setActiveJob] = useState<AIGenerationJob | null>(null)
  const [diff, setDiff] = useState<DocumentDiff | null>(null)
  const [batches, setBatches] = useState<AIBatch[]>([])
  const [selectedBatch, setSelectedBatch] = useState<AIBatch | null>(null)
  const [batchTaskIds, setBatchTaskIds] = useState<string[]>([])
  const [syntheses, setSyntheses] = useState<BatchSynthesis[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [batchBusy, setBatchBusy] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [providerUnavailable, setProviderUnavailable] = useState<boolean>(false)

  // Polling ref for generation job
  const pollIntervalRef = useRef<number | null>(null)
  const synthesisLoadSeq = useRef(0)

  // Load workflow tasks on mount
  const hasPendingSynthesis = syntheses.some((item) => item.status === "QUEUED" || item.status === "RUNNING")
  useEffect(() => {
    let mounted = true
    getWorkflowState(projectId)
      .then((wf) => {
        if (!mounted) return
        setWorkflow(wf)
        const currentWf = wf.published ?? wf.draft
        if (currentWf && currentWf.tasks.length > 0) {
          setSelectedTaskId(currentWf.tasks[0].task_id)
        }
      })
      .catch((err) => {
        if (!mounted) return
        setErrorMsg(err instanceof Error ? err.message : String(err))
      })
    return () => {
      mounted = false
    }
  }, [projectId])

  // Polling for active job if running or queued
  useEffect(() => {
    if (!activeJob || (activeJob.status !== "QUEUED" && activeJob.status !== "RUNNING")) {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
      return
    }

    pollIntervalRef.current = window.setInterval(async () => {
      try {
        const updated = await getGenerationJob(projectId, activeJob.job_id)
        setActiveJob(updated)
        if (updated.status === "SUCCEEDED" || updated.status === "FAILED" || updated.status === "CANCELLED") {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current)
            pollIntervalRef.current = null
          }
          if (updated.status === "SUCCEEDED") {
            setSuccessMsg(`Propuesta generada con éxito (ID: ${updated.job_id.slice(0, 8)}).`)
            // Auto check diff if textual
            if (updated.task_id === "P05" || updated.task_id === "P29") {
              try {
                const diffData = await getGenerationDocumentDiff(projectId, updated.job_id)
                setDiff(diffData)
              } catch {
                // Non-fatal if diff cannot be loaded yet
              }
            }
          } else if (updated.status === "FAILED") {
            setErrorMsg(`Falló la generación: ${updated.error_message || updated.error_code || "Error desconocido"}`)
          }
        }
      } catch (err) {
        console.error("Error polling AI job:", err)
      }
    }, 2500)

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
        pollIntervalRef.current = null
      }
    }
  }, [projectId, activeJob])

  // Load batches when switching to batches tab
  useEffect(() => {
    if (activeTab === "batches") {
      void loadBatches()
    }
  }, [activeTab, projectId])

  const loadBatches = async (preferredBatchId?: string) => {
    try {
      const list = await listGenerationBatches(projectId)
      setBatches(list)
      const selected = list.find((item) => item.batch_id === (preferredBatchId ?? selectedBatch?.batch_id)) ?? list[0] ?? null
      setSelectedBatch(selected)
      if (selected) await loadSyntheses(selected.batch_id)
      else setSyntheses([])
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    }
  }

  const loadSyntheses = async (batchId: string) => {
    const sequence = ++synthesisLoadSeq.current
    try {
      const list = await listBatchSyntheses(projectId, batchId)
      if (sequence === synthesisLoadSeq.current) setSyntheses(list)
    } catch (err) {
      if (sequence === synthesisLoadSeq.current) setErrorMsg(err instanceof Error ? err.message : "No se pudieron cargar las síntesis del lote.")
    }
  }

  useEffect(() => {
    if (activeTab !== "batches" || !selectedBatch) return
    const batchId = selectedBatch.batch_id
    const pendingBatch = selectedBatch.status === "QUEUED" || selectedBatch.status === "RUNNING"
    if (!pendingBatch && !hasPendingSynthesis) return
    let active = true
    const timer = window.setInterval(async () => {
      try {
        const [batch, currentSyntheses] = await Promise.all([
          getGenerationBatch(projectId, batchId), listBatchSyntheses(projectId, batchId),
        ])
        if (!active) return
        setSelectedBatch((current) => current?.batch_id === batchId ? batch : current)
        setBatches((current) => current.map((item) => item.batch_id === batchId ? batch : item))
        setSyntheses(currentSyntheses)
      } catch (err) {
        if (active) setErrorMsg(err instanceof Error ? err.message : String(err))
      }
    }, 3000)
    return () => { active = false; window.clearInterval(timer) }
  }, [activeTab, projectId, selectedBatch?.batch_id, selectedBatch?.status, hasPendingSynthesis])

  const handleCreateBatch = async () => {
    if (!canWrite) return
    const currentWorkflow = workflow?.published ?? workflow?.draft
    if (!currentWorkflow || batchTaskIds.length < 1 || batchTaskIds.length > 8) return
    setBatchBusy(true)
    setErrorMsg(null)
    try {
      const batch = await createGenerationBatch(projectId, {
        tasks: batchTaskIds.map((task_id) => ({ task_id, input_data: {}, context_refs: [] })),
        expected_state_version: stateVersion,
        workflow_version_no: currentWorkflow.version_no,
        idempotency_key: generateUuid(),
      }, csrfToken)
      setBatchTaskIds([])
      await loadBatches(batch.batch_id)
      setSuccessMsg(`Lote ${batch.batch_id.slice(0, 8)} solicitado. Revisa el estado de cada trabajo antes de sintetizar.`)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    } finally {
      setBatchBusy(false)
    }
  }

  const handleGenerate = async () => {
    if (!canWrite) return
    setLoading(true)
    setErrorMsg(null)
    setSuccessMsg(null)
    setProviderUnavailable(false)
    setDiff(null)

    let parsedInput: Record<string, unknown> = {}
    try {
      if (inputJson.trim()) {
        parsedInput = JSON.parse(inputJson)
      }
      if (parsedInput === null || typeof parsedInput !== "object" || Array.isArray(parsedInput)) {
        throw new Error("JSON_OBJECT_REQUIRED")
      }
    } catch {
      setErrorMsg("Los datos de entrada deben ser un objeto JSON válido.")
      setLoading(false)
      return
    }

    const idempotencyKey = generateUuid()

    const activeWf = workflow?.published ?? workflow?.draft

    try {
      const job = await generateProposal(
        projectId,
        selectedTaskId,
        {
          input_data: parsedInput,
          context_refs: [],
          expected_state_version: stateVersion,
          workflow_version_no: activeWf?.version_no,
          idempotency_key: idempotencyKey,
        },
        csrfToken,
      )
      setActiveJob(job)
      setSuccessMsg(`Trabajo de generación encolado (ID: ${job.job_id.slice(0, 8)}).`)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      if (msg.includes("PROVIDER_UNAVAILABLE") || msg.includes("LLMProviderUnavailableError")) {
        setProviderUnavailable(true)
        setErrorMsg("El proveedor de IA del servidor no está configurado (falta GEMINI_API_KEY en backend).")
      } else {
        setErrorMsg(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCancelJob = async () => {
    if (!canWrite) return
    if (!activeJob) return
    setLoading(true)
    try {
      const updated = await cancelGenerationJob(projectId, activeJob.job_id, csrfToken)
      setActiveJob(updated)
      setSuccessMsg("Trabajo cancelado.")
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleLoadDiff = async () => {
    if (!activeJob) return
    setLoading(true)
    try {
      const diffData = await getGenerationDocumentDiff(projectId, activeJob.job_id)
      setDiff(diffData)
      setSuccessMsg("Diferencia calculada respecto al borrador actual.")
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleAcceptProposal = async () => {
    if (!canWrite) return
    if (!activeJob) return
    const requiresDocumentDiff = activeJob.task_id === "P05" || activeJob.task_id === "P29"
    if (requiresDocumentDiff && (!diff || diff.job_id !== activeJob.job_id)) {
      setErrorMsg("Revisa primero la comparación vigente con el manuscrito.")
      return
    }
    if (!window.confirm(requiresDocumentDiff
      ? "¿Aceptar la propuesta e incorporar la revisión de paso y el cambio mostrado en el manuscrito?"
      : "¿Aceptar esta propuesta e incorporarla como resultado de la tarea del proyecto?")) return

    setLoading(true)
    setErrorMsg(null)
    setSuccessMsg(null)

    const decisionKey = generateUuid()

    try {
      const res = await acceptProposal(
        projectId,
        activeJob.job_id,
        {
          expected_state_version: stateVersion,
          decision_key: decisionKey,
          expected_document_version: diff?.expected_document_version,
          proposal_sha256: diff?.proposal_sha256,
        },
        csrfToken,
      )
      setActiveJob((prev) => (prev ? {
        ...prev, acceptance_status: "ACCEPTED",
        result_revision_id: res.result_revision_id,
        result_execution_id: res.result_execution_id,
        result_document_revision_id: res.result_document_revision_id,
      } : null))
      const result = res.result_document_revision_id
        ? `Revisión del manuscrito ${res.result_document_revision_id.slice(0, 8)}.`
        : res.result_revision_id !== null
          ? `Revisión del paso ${res.result_revision_id}.`
          : res.result_execution_id !== null
            ? `Ejecución de tarea ${res.result_execution_id}.`
            : "Decisión registrada."
      setSuccessMsg(`Propuesta aceptada. ${result}`)
      if (res.state_version !== undefined && onStateVersionChanged) {
        onStateVersionChanged(res.state_version)
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleRejectProposal = async () => {
    if (!canWrite) return
    if (!activeJob) return
    const reason = window.prompt("Motivo del rechazo de la propuesta (opcional):")
    if (reason === null) return

    setLoading(true)
    setErrorMsg(null)
    setSuccessMsg(null)

    const decisionKey = generateUuid()

    try {
      const res = await rejectProposal(
        projectId,
        activeJob.job_id,
        {
          decision_key: decisionKey,
          reason: reason.trim(),
        },
        csrfToken,
      )
      setActiveJob((prev) => (prev ? { ...prev, acceptance_status: "REJECTED", decision_reason: res.decision_reason } : null))
      setSuccessMsg("Propuesta rechazada explícitamente.")
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const activeVersion = workflow?.published ?? workflow?.draft
  const selectedTask = activeVersion?.tasks.find((t: WorkflowTask) => t.task_id === selectedTaskId)

  return (
    <div className="connected-screen ai-screen">
      <header className="screen-header">
        <div>
          <button className="btn-secondary" onClick={onBack}>
            ← Volver al Proyecto
          </button>
          <h2>Asistente de IA y Decisiones Humanas</h2>
          <p className="screen-subtitle">
            Proyecto: <strong>{projectName}</strong> (v{stateVersion}) · Recorrido: v{activeVersion?.version_no ?? 1}
          </p>
        </div>
      </header>

      {errorMsg && (
        <div className="alert alert-error" role="alert">
          {errorMsg}
        </div>
      )}

      {successMsg && (
        <div className="alert alert-success" role="alert">
          {successMsg}
        </div>
      )}

      {providerUnavailable && (
        <div className="alert alert-warning" role="alert">
          <strong>Aviso de Configuración del Servidor:</strong>
          <p>
            El adaptador LLM interno del servidor no tiene configurada una clave de API (falta{" "}
            <code>GEMINI_API_KEY</code> en las variables de entorno de Django).
          </p>
          <p>
            Para trabajar con IA en este entorno, puedes configurar dicha clave o utilizar el modelo{" "}
            <strong>BYOA (Bring Your Own Agent)</strong> conectando tu agente personal mediante el servidor MCP.
          </p>
        </div>
      )}

      <div className="screen-tabs">
        {canWrite && <button
          className={`tab-btn ${activeTab === "proposals" ? "active" : ""}`}
          onClick={() => setActiveTab("proposals")}
        >
          Generación y Propuestas
        </button>}
        <button
          className={`tab-btn ${activeTab === "batches" ? "active" : ""}`}
          onClick={() => setActiveTab("batches")}
        >
          Lotes y Síntesis
        </button>
        <button
          className={`tab-btn ${activeTab === "byoa" ? "active" : ""}`}
          onClick={() => setActiveTab("byoa")}
        >
          Arquitectura BYOA & MCP
        </button>
      </div>

      {canWrite && activeTab === "proposals" && (
        <div className="tab-content ai-proposals-grid">
          {/* Panel Izquierdo: Selección y Generación */}
          <div className="ai-controls-card">
            <h3>1. Solicitar Propuesta Asistida</h3>
            <p className="field-hint">
              Selecciona una tarea activa del recorrido para que el asistente analice las entradas y genere una propuesta estructurada.
            </p>

            <div className="form-group">
              <label htmlFor="task-select">Tarea del Recorrido:</label>
              <select
                id="task-select"
                value={selectedTaskId}
                onChange={(e) => setSelectedTaskId(e.target.value)}
                disabled={loading}
              >
                {activeVersion?.tasks.map((task: WorkflowTask) => (
                  <option key={task.task_id} value={task.task_id}>
                    {task.task_id} - {task.title} {task.is_active ? "" : "(Inactiva)"}
                  </option>
                ))}
              </select>
            </div>

            {selectedTask && (
              <div className="task-preview-info">
                <span className="badge badge-info">Capítulo {selectedTask.chapter_no}</span>
                {selectedTask.is_optional && <span className="badge badge-warning">Opcional</span>}
                <p className="task-desc">{selectedTask.description || "Sin descripción adicional."}</p>
              </div>
            )}

            <div className="form-group">
              <label htmlFor="input-json">Parámetros de Entrada (JSON):</label>
              <textarea
                id="input-json"
                rows={5}
                value={inputJson}
                onChange={(e) => setInputJson(e.target.value)}
                placeholder='{"tema": "...", "enfoque": "..."}'
                disabled={loading}
              />
            </div>

            <div className="actions-row">
              <button
                className="btn-primary"
                onClick={handleGenerate}
                disabled={loading || !selectedTask?.is_active}
              >
                {loading ? "Procesando..." : "Generar Propuesta con IA"}
              </button>
            </div>
          </div>

          {/* Panel Derecho: Estado, Propuesta y Decisión Humana */}
          <div className="ai-results-card">
            <h3>2. Revisión y Decisión Humana</h3>
            {!activeJob ? (
              <p className="empty-hint">No hay un trabajo de generación activo en este momento.</p>
            ) : (
              <div className="job-details">
                <div className="job-header">
                  <div>
                    <strong>Trabajo:</strong> <code>{activeJob.job_id.slice(0, 8)}</code>
                    <span className="separator">·</span>
                    <strong>Tarea:</strong> <code>{activeJob.task_id}</code>
                  </div>
                  <div className="job-badges">
                    <span className={`badge badge-status-${activeJob.status.toLowerCase()}`}>
                      {activeJob.status}
                    </span>
                    <span className={`badge badge-acceptance-${activeJob.acceptance_status.toLowerCase()}`}>
                      {activeJob.acceptance_status}
                    </span>
                  </div>
                </div>

                {activeJob.status === "QUEUED" && (
                  <div className="job-progress-box">
                    <p>En cola de procesamiento. Esperando asignación...</p>
                    <button className="btn-danger btn-sm" onClick={handleCancelJob} disabled={loading}>
                      Cancelar Solicitud
                    </button>
                  </div>
                )}

                {activeJob.status === "RUNNING" && (
                  <div className="job-progress-box">
                    <p>El modelo está razonando y generando la propuesta estructurada...</p>
                  </div>
                )}

                {activeJob.status === "SUCCEEDED" && (
                  <div className="job-output-box">
                    <div className="output-meta">
                      <span>Proveedor: {activeJob.provider || "No informado"}</span>
                      <span>Modelo: {activeJob.model || "No informado"}</span>
                      {activeJob.output_sha256 && (
                        <span>Hash: <code>{activeJob.output_sha256.slice(0, 12)}...</code></span>
                      )}
                    </div>

                    {(activeJob.task_id === "P05" || activeJob.task_id === "P29") && (
                      <div className="diff-action-row">
                        <button className="btn-secondary btn-sm" onClick={handleLoadDiff} disabled={loading}>
                          {diff ? "Actualizar Comparación Diff" : "Comparar Diff con Manuscrito"}
                        </button>
                      </div>
                    )}

                    {diff && (
                      <div className="diff-viewer">
                        <h4>Comparación de Manuscrito (Capítulo {diff.chapter_no}):</h4>
                        <div className="diff-columns">
                          <div className="diff-col diff-before">
                            <h5>Borrador Actual (v{diff.expected_document_version})</h5>
                            <pre className="diff-content">{diff.before_content_md || "(Capítulo vacío)"}</pre>
                          </div>
                          <div className="diff-col diff-after">
                            <h5>Propuesta Nueva</h5>
                            <pre className="diff-content">{diff.after_content_md}</pre>
                          </div>
                        </div>
                        <div className="diff-meta">
                          <small>Hash de propuesta validada: <code>{diff.proposal_sha256.slice(0, 16)}...</code></small>
                        </div>
                      </div>
                    )}

                    <div className="output-content">
                      <h4>Salida Estructurada de la Propuesta:</h4>
                      <pre className="json-pre">
                        {JSON.stringify(activeJob.output_data, null, 2)}
                      </pre>
                    </div>

                    {activeJob.acceptance_status === "PENDING_ACCEPTANCE" && (
                      <div className="decision-actions">
                        <p className="decision-notice">
                          <strong>Acción Humana Requerida:</strong> La IA propone; tú decides. Ningún cambio se incorporará a la tesis sin tu aprobación explícita.
                        </p>
                        <div className="actions-buttons">
                          <button
                            className="btn-success"
                            onClick={handleAcceptProposal}
                            disabled={loading || ((activeJob.task_id === "P05" || activeJob.task_id === "P29") && diff?.job_id !== activeJob.job_id)}
                          >
                            {activeJob.task_id === "P05" || activeJob.task_id === "P29" ? "Aceptar e incorporar al manuscrito" : "Aceptar resultado de la tarea"}
                          </button>
                          <button
                            className="btn-danger"
                            onClick={handleRejectProposal}
                            disabled={loading}
                          >
                            Rechazar Propuesta
                          </button>
                        </div>
                      </div>
                    )}

                    {activeJob.acceptance_status === "ACCEPTED" && (
                      <div className="decision-resolved-box accepted">
                        ✓ Propuesta aceptada en el proyecto.
                        {activeJob.result_revision_id && (
                          <span> (Revisión #{activeJob.result_revision_id})</span>
                        )}
                        {activeJob.result_execution_id && <span> (Ejecución #{activeJob.result_execution_id})</span>}
                        {activeJob.result_document_revision_id && <span> (Documento {activeJob.result_document_revision_id.slice(0, 8)})</span>}
                      </div>
                    )}

                    {activeJob.acceptance_status === "REJECTED" && (
                      <div className="decision-resolved-box rejected">
                        ✗ Propuesta rechazada. Motivo: {activeJob.decision_reason || "No especificado"}.
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "batches" && (
        <div className="tab-content ai-batches-view">
          <div className="batches-sidebar">
            <div className="sidebar-header">
              <h3>Lotes de Generación</h3>
              <button className="btn-secondary btn-sm" onClick={() => void loadBatches()}>
                Actualizar
              </button>
            </div>
            {canWrite && <div className="form-group">
              <label>Crear lote (1 a 8 tareas activas)</label>
              {(activeVersion?.tasks ?? []).filter((task) => task.is_active).map((task) => (
                <label key={task.task_id} className="batch-task-choice">
                  <input type="checkbox" checked={batchTaskIds.includes(task.task_id)} disabled={batchBusy || (!batchTaskIds.includes(task.task_id) && batchTaskIds.length >= 8)}
                    onChange={(event) => setBatchTaskIds((current) => event.target.checked
                      ? [...current, task.task_id] : current.filter((id) => id !== task.task_id))} />
                  {task.task_id} · {task.title}
                </label>
              ))}
              <button className="btn-primary btn-sm" disabled={batchBusy || batchTaskIds.length === 0} onClick={() => void handleCreateBatch()}>
                {batchBusy ? "Solicitando…" : `Solicitar lote (${batchTaskIds.length})`}
              </button>
              <small>Este lote envía <code>{"{}"}</code> como entrada de cada tarea. Usa la generación individual cuando debas indicar parámetros distintos.</small>
            </div>}
            {batches.length === 0 ? (
              <p className="empty-hint">No hay lotes creados.</p>
            ) : (
              <div className="batches-list">
                {batches.map((b) => (
                  <div
                    key={b.batch_id}
                    className={`batch-item ${selectedBatch?.batch_id === b.batch_id ? "selected" : ""}`}
                    onClick={() => {
                      setSelectedBatch(b)
                      loadSyntheses(b.batch_id)
                    }}
                  >
                    <div className="batch-title">
                      <strong>Lote #{b.batch_id.slice(0, 6)}</strong>
                      <span className={`badge badge-sm badge-status-${b.status.toLowerCase()}`}>
                        {b.status}
                      </span>
                    </div>
                    <div className="batch-sub">
                      <span>{b.item_count} tareas</span> · <span>v{b.workflow_version_no}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="batch-detail-panel">
            {selectedBatch ? (
              <div>
                <div className="batch-header-row">
                  <div>
                    <h4>Detalle de Lote: <code>{selectedBatch.batch_id}</code></h4>
                    <p>Estado: <strong>{selectedBatch.status}</strong> · Creado: {new Date(selectedBatch.created_at).toLocaleString()}</p>
                  </div>
                  {canWrite && selectedBatch.status === "QUEUED" && (
                    <button
                      className="btn-danger btn-sm"
                      onClick={async () => {
                        try {
                          await cancelGenerationBatch(projectId, selectedBatch.batch_id, csrfToken)
                          await loadBatches()
                        } catch (err) {
                          setErrorMsg(err instanceof Error ? err.message : String(err))
                        }
                      }}
                    >
                      Cancelar Lote
                    </button>
                  )}
                </div>

                <h5>Tareas en este Lote:</h5>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Tarea</th>
                      <th>Estado</th>
                      <th>Job ID</th>
                      <th>Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedBatch.items.map((t) => (
                      <tr key={t.task_id}>
                        <td><strong>{t.task_id}</strong></td>
                        <td><span className="badge badge-sm">{t.status}</span></td>
                        <td><code>{t.job_id.slice(0, 8)}</code></td>
                        <td>{t.error_message || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div className="syntheses-section">
                  <div className="section-header-row">
                    <h5>Síntesis del Lote:</h5>
                    {canWrite && <button
                      className="btn-secondary btn-sm"
                      onClick={async () => {
                        const completedJobs = selectedBatch.items.filter((item) => item.status === "SUCCEEDED").map((item) => item.job_id)
                        if (completedJobs.length < 2) {
                          setErrorMsg("La síntesis requiere al menos dos trabajos completados con éxito en este lote.")
                          return
                        }
                        try {
                          setBatchBusy(true)
                          await createBatchSynthesis(
                            projectId,
                            selectedBatch.batch_id,
                            { job_ids: completedJobs, idempotency_key: generateUuid() },
                            csrfToken,
                          )
                          await loadSyntheses(selectedBatch.batch_id)
                        } catch (err) {
                          setErrorMsg(err instanceof Error ? err.message : String(err))
                        } finally {
                          setBatchBusy(false)
                        }
                      }}
                      disabled={batchBusy || selectedBatch.items.filter((item) => item.status === "SUCCEEDED").length < 2}
                    >
                      + Solicitar Nueva Síntesis
                    </button>}
                  </div>
                  <p className="field-hint">Se requieren de 2 a 8 trabajos completados con éxito. Actualiza el lote para consultar su estado.</p>

                  {syntheses.length === 0 ? (
                    <p className="empty-hint">No hay síntesis solicitadas para este lote.</p>
                  ) : (
                    <div className="syntheses-list">
                      {syntheses.map((s) => (
                        <div key={s.synthesis_id} className="synthesis-card">
                          <div className="synthesis-header">
                            <strong>Síntesis #{s.synthesis_id.slice(0, 8)}</strong>
                            <span className="badge badge-sm">{s.status}</span>
                            <span className="badge badge-sm">{s.decision_status}</span>
                          </div>
                          {s.output_data && <pre className="json-pre">{JSON.stringify(s.output_data, null, 2)}</pre>}
                          {s.error_message && <p role="alert">{s.error_code ? `${s.error_code}: ` : ""}{s.error_message}</p>}
                          {canWrite && s.status === "QUEUED" && <button className="btn-danger btn-sm" disabled={batchBusy} onClick={async () => {
                            try {
                              setBatchBusy(true)
                              await cancelBatchSynthesis(projectId, selectedBatch.batch_id, s.synthesis_id, csrfToken)
                              await loadSyntheses(selectedBatch.batch_id)
                            } catch (err) {
                              setErrorMsg(err instanceof Error ? err.message : String(err))
                            } finally {
                              setBatchBusy(false)
                            }
                          }}>Cancelar síntesis en cola</button>}
                          {canWrite && s.decision_status === "PENDING_REVIEW" && s.status === "SUCCEEDED" && (
                            <div className="decision-row">
                              <button
                                className="btn-success btn-sm"
                                onClick={async () => {
                                  try {
                                    await decideBatchSynthesis(
                                      projectId,
                                      selectedBatch.batch_id,
                                      s.synthesis_id,
                                      { decision: "ACCEPTED", decision_key: generateUuid() },
                                      csrfToken,
                                    )
                                    await loadSyntheses(selectedBatch.batch_id)
                                  } catch (err) {
                                    setErrorMsg(err instanceof Error ? err.message : String(err))
                                  }
                                }}
                              >
                                Aceptar informe auxiliar
                              </button>
                              <button
                                className="btn-danger btn-sm"
                                onClick={async () => {
                                  try {
                                    await decideBatchSynthesis(
                                      projectId,
                                      selectedBatch.batch_id,
                                      s.synthesis_id,
                                      { decision: "REJECTED", decision_key: generateUuid() },
                                      csrfToken,
                                    )
                                    await loadSyntheses(selectedBatch.batch_id)
                                  } catch (err) {
                                    setErrorMsg(err instanceof Error ? err.message : String(err))
                                  }
                                }}
                              >
                                Rechazar
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <p className="empty-hint">Selecciona un lote de la lista izquierda.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === "byoa" && (
        <div className="tab-content byoa-architecture-view">
          <div className="byoa-card">
            <h3>Arquitectura BYOA (Bring Your Own Agent) & Servidor MCP</h3>
            <p>
              TesisMCP está diseñado para permitir que el tesista trabaje con su propio asistente o entorno de IA (Claude Desktop, Cursor, Antigravity, Cline, etc.) sin depender exclusivamente de llamadas directas desde nuestro servidor.
            </p>

            <div className="byoa-flowchart">
              <div className="byoa-box web-box">
                <strong>Web TesisMCP</strong>
                <p>Navegador del Tesista</p>
                <small>Inicia tareas, revisa diffs y decide</small>
              </div>
              <div className="byoa-arrow">⇄ (API REST)</div>
              <div className="byoa-box backend-box">
                <strong>Backend Django</strong>
                <p>PostgreSQL + pgvector</p>
                <small>Autorización, estados y versiones</small>
              </div>
              <div className="byoa-arrow">⇄ (MCP)</div>
              <div className="byoa-box mcp-box">
                <strong>Servidor MCP</strong>
                <p>mcp_server</p>
                <small>Búsqueda, pasajes, capítulos</small>
              </div>
              <div className="byoa-arrow">⇄</div>
              <div className="byoa-box agent-box">
                <strong>Agente del Usuario</strong>
                <p>Modelo Personal / Local</p>
                <small>Razona, consulta herramientas</small>
              </div>
            </div>

            <div className="byoa-rules">
              <h4>Garantías de Seguridad y Rigor Académico:</h4>
              <ul>
                <li><strong>Cero auto-aprobación del modelo:</strong> El agente puede redactar y proponer, pero jamás puede aprobar directamente su propia salida ni sobrescribir el manuscrito sin revisión humana.</li>
                <li><strong>Permisos por identidad:</strong> El servidor MCP valida tokens y membresías en la base de datos; el agente no puede acceder a proyectos ni fuentes ajenas.</li>
                <li><strong>Privacidad de credenciales:</strong> TesisMCP no solicita tus claves privadas de suscripciones comerciales; tu agente se ejecuta en tu propio equipo.</li>
              </ul>
            </div>

            <div className="byoa-setup">
              <h4>Configuración Local de MCP:</h4>
              <p>El cliente MCP debe iniciar el proceso desde la raíz del proyecto renovado. Configura en tu entorno local la conexión a PostgreSQL y un token MCP emitido para tu cuenta; no pegues el token en la web ni en documentos compartidos.</p>
              <pre className="code-block">
{`{
  "mcpServers": {
    "tesismcp": {
      "command": "python",
      "args": ["-m", "mcp_server.server"]
    }
  }
}`}
              </pre>
              <p>Variables requeridas para ese proceso: <code>DATABASE_URL</code> y <code>TESISMCP_MCP_TOKEN</code>; en desarrollo local, <code>DJANGO_DEBUG=1</code>. Usa el Python del entorno del proyecto. La guía de <code>mcp_server/README.md</code> explica cómo emitir el token y arrancar el servicio.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
