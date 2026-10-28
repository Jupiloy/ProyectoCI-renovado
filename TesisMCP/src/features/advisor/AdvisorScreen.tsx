import { useCallback, useEffect, useRef, useState } from "react"
import { ApiError } from "../../api/client"
import { getChapterDocument, getChapterState } from "../../api/chapters"
import {
  addComment,
  createSupportInvitation,
  decideChapter,
  getAdvisorDashboard,
  getChapterSnapshot,
  listChapterSnapshots,
  listComments,
  listSupportContributions,
  listSupportInvitations,
  resolveComment,
  revokeSupportInvitation,
  submitChapter,
} from "../../api/reviews"
import type {
  AdvisorDashboardProject,
  ChapterDocument,
  ChapterSnapshotDetail,
  ChapterSnapshotSummary,
  ChapterState,
  ProjectState,
  ProjectSummary,
  ReviewComment,
  SessionUser,
  SupportContribution,
  SupportInvitation,
} from "../../api/types"

interface Props {
  project: ProjectSummary
  details: ProjectState
  user: SessionUser
  csrfToken: string
  onBack: () => void
  onUnauthorized: () => void
  onAccessLost: () => void
  onLogout: () => Promise<void>
}

type Tab = "review" | "advisor_overview" | "support"
type CommentAnchor = { snapshotId: string; start_cp: number; end_cp: number; selected_text: string }

export default function AdvisorScreen({
  project,
  user,
  csrfToken,
  onBack,
  onUnauthorized,
  onAccessLost,
  onLogout,
}: Props) {
  const isAdvisor = project.role === "ADVISOR"
  const isOwner = project.role === "OWNER"
  const [tab, setTab] = useState<Tab>(isAdvisor ? "review" : "support")
  const [chapterNo, setChapterNo] = useState(1)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  // Chapter and Snapshot data
  const [chapterState, setChapterState] = useState<ChapterState | null>(null)
  const [chapterDoc, setChapterDoc] = useState<ChapterDocument | null>(null)
  const [snapshots, setSnapshots] = useState<ChapterSnapshotSummary[]>([])
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(null)
  const [activeSnapshotDetail, setActiveSnapshotDetail] = useState<ChapterSnapshotDetail | null>(null)

  // Comments
  const [comments, setComments] = useState<ReviewComment[]>([])
  const [newCommentBody, setNewCommentBody] = useState("")
  const [commentAnchor, setCommentAnchor] = useState<CommentAnchor | null>(null)
  const documentTextRef = useRef<HTMLDivElement | null>(null)
  const [submittingComment, setSubmittingComment] = useState(false)

  // Advisor Decisions
  const [decisionReason, setDecisionReason] = useState("")
  const [processingDecision, setProcessingDecision] = useState(false)
  const [submittingChapter, setSubmittingChapter] = useState(false)

  // Advisor Multi-Project Dashboard
  const [advisorProjects, setAdvisorProjects] = useState<AdvisorDashboardProject[]>([])
  const [loadingDashboard, setLoadingDashboard] = useState(false)

  // Support Invitations
  const [supportInvitations, setSupportInvitations] = useState<SupportInvitation[]>([])
  const [loadingSupport, setLoadingSupport] = useState(false)
  const [selectedInvitationContributions, setSelectedInvitationContributions] = useState<{ id: string; items: SupportContribution[] } | null>(null)

  // New Support Invitation Form
  const [newSupportEmail, setNewSupportEmail] = useState("")
  const [newSupportTaskId, setNewSupportTaskId] = useState("P01")
  const [newSupportInstructions, setNewSupportInstructions] = useState("")
  const [creatingSupport, setCreatingSupport] = useState(false)

  const loadSeq = useRef(0)
  const canCommentOnSnapshot = isAdvisor && chapterState?.status === "READY"
    && !!selectedSnapshotId && selectedSnapshotId === chapterState.submitted_snapshot_id
    && activeSnapshotDetail?.snapshot_id === selectedSnapshotId

  function captureCommentAnchor() {
    if (!canCommentOnSnapshot || !activeSnapshotDetail || !documentTextRef.current) return
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed || selection.rangeCount === 0) return
    const range = selection.getRangeAt(0)
    const container = documentTextRef.current
    if (!container.contains(range.startContainer) || !container.contains(range.endContainer)) return

    const before = range.cloneRange()
    before.selectNodeContents(container)
    before.setEnd(range.startContainer, range.startOffset)
    const through = range.cloneRange()
    through.selectNodeContents(container)
    through.setEnd(range.endContainer, range.endOffset)

    const source = activeSnapshotDetail.content_md
    const startUtf16 = before.toString().length
    const endUtf16 = through.toString().length
    const selectedText = source.slice(startUtf16, endUtf16)
    if (!selectedText || selectedText !== range.toString()) {
      setError("La selección no coincide con el texto del snapshot. Vuelve a seleccionar el fragmento.")
      return
    }
    setCommentAnchor({
      snapshotId: activeSnapshotDetail.snapshot_id,
      start_cp: Array.from(source.slice(0, startUtf16)).length,
      end_cp: Array.from(source.slice(0, endUtf16)).length,
      selected_text: selectedText,
    })
    setError(null)
  }

  // Load Chapter review data
  const loadReviewData = useCallback(async (chNo: number) => {
    const seq = ++loadSeq.current
    setLoading(true)
    setError(null)
    setSelectedSnapshotId(null)
    setActiveSnapshotDetail(null)
    setCommentAnchor(null)
    try {
      const [st, doc, snaps, comms] = await Promise.all([
        getChapterState(project.project_id, chNo),
        getChapterDocument(project.project_id, chNo),
        listChapterSnapshots(project.project_id, chNo).catch(() => []),
        listComments(project.project_id, chNo).catch(() => []),
      ])
      if (seq !== loadSeq.current) return
      setChapterState(st)
      setChapterDoc(doc)
      setSnapshots(snaps)
      setComments(comms)

      // If chapter is READY and has submitted snapshot, default to it
      if (st.submitted_snapshot_id) {
        setSelectedSnapshotId(st.submitted_snapshot_id)
        getChapterSnapshot(project.project_id, chNo, st.submitted_snapshot_id)
          .then((detail) => {
            if (seq === loadSeq.current) setActiveSnapshotDetail(detail)
          })
          .catch(() => {})
      }
    } catch (cause) {
      if (seq !== loadSeq.current) return
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
      else if (cause instanceof ApiError && cause.status === 404) onAccessLost()
      else setError(cause instanceof Error ? cause.message : "Error al cargar datos del capítulo")
    } finally {
      if (seq === loadSeq.current) setLoading(false)
    }
  }, [project.project_id, onUnauthorized, onAccessLost])

  useEffect(() => {
    void loadReviewData(chapterNo)
  }, [chapterNo, loadReviewData])

  // Load selected snapshot details
  async function handleSelectSnapshot(snapId: string) {
    setCommentAnchor(null)
    setActiveSnapshotDetail(null)
    if (!snapId) {
      setSelectedSnapshotId(null)
      setActiveSnapshotDetail(null)
      const comms = await listComments(project.project_id, chapterNo)
      setComments(comms)
      return
    }
    setSelectedSnapshotId(snapId)
    setLoading(true)
    try {
      const [detail, comms] = await Promise.all([
        getChapterSnapshot(project.project_id, chapterNo, snapId),
        listComments(project.project_id, chapterNo, snapId),
      ])
      setActiveSnapshotDetail(detail)
      setComments(comms)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al cargar el snapshot")
    } finally {
      setLoading(false)
    }
  }

  // Load Advisor Dashboard (all assigned projects)
  useEffect(() => {
    if (tab !== "advisor_overview" || !isAdvisor) return
    setLoadingDashboard(true)
    getAdvisorDashboard()
      .then((data) => setAdvisorProjects(data))
      .catch((cause) => setError(cause instanceof Error ? cause.message : "Error al cargar dashboard"))
      .finally(() => setLoadingDashboard(false))
  }, [tab, isAdvisor])

  // Load Support Invitations
  const loadSupportData = useCallback(async () => {
    setLoadingSupport(true)
    try {
      const res = await listSupportInvitations(project.project_id)
      setSupportInvitations(res.items)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al cargar invitaciones de apoyo")
    } finally {
      setLoadingSupport(false)
    }
  }, [project.project_id])

  useEffect(() => {
    if (tab === "support") {
      void loadSupportData()
    }
  }, [tab, loadSupportData])

  // Submit Chapter to Advisor Review (Owner action)
  async function handleSubmitChapter() {
    setSubmittingChapter(true)
    setError(null)
    setNotice(null)
    try {
      await submitChapter(project.project_id, chapterNo, csrfToken)
      setNotice(`Capítulo ${chapterNo} enviado a revisión del asesor. Se ha congelado una instantánea (snapshot).`)
      void loadReviewData(chapterNo)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al enviar el capítulo a revisión.")
    } finally {
      setSubmittingChapter(false)
    }
  }

  // Add Comment (Advisor action)
  async function handleAddComment(e: React.FormEvent) {
    e.preventDefault()
    if (!newCommentBody.trim()) return
    if (!canCommentOnSnapshot || !activeSnapshotDetail || !commentAnchor
        || commentAnchor.snapshotId !== activeSnapshotDetail.snapshot_id
        || Array.from(activeSnapshotDetail.content_md).slice(commentAnchor.start_cp, commentAnchor.end_cp).join("") !== commentAnchor.selected_text) {
      setError("Selecciona un fragmento del snapshot vigente antes de registrar la observación.")
      return
    }
    setSubmittingComment(true)
    setError(null)
    try {
      await addComment(
        project.project_id,
        chapterNo,
        {
          start_cp: commentAnchor.start_cp,
          end_cp: commentAnchor.end_cp,
          selected_text: commentAnchor.selected_text,
          body: newCommentBody.trim(),
          snapshot_id: commentAnchor.snapshotId,
        },
        csrfToken,
      )
      setNewCommentBody("")
      setCommentAnchor(null)
      setNotice("Observación registrada con éxito.")
      const comms = await listComments(project.project_id, chapterNo, selectedSnapshotId ?? undefined)
      setComments(comms)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al registrar la observación.")
    } finally {
      setSubmittingComment(false)
    }
  }

  // Resolve Comment
  async function handleResolveComment(commentId: number) {
    setError(null)
    try {
      await resolveComment(project.project_id, commentId, csrfToken)
      setNotice(`Observación #${commentId} resuelta.`)
      const comms = await listComments(project.project_id, chapterNo, selectedSnapshotId ?? undefined)
      setComments(comms)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al resolver la observación.")
    }
  }

  // Academic Decision (Advisor action)
  async function handleDecision(action: "REQUEST_CHANGES" | "APPROVE" | "REOPEN") {
    setProcessingDecision(true)
    setError(null)
    setNotice(null)
    try {
      const updated = await decideChapter(project.project_id, chapterNo, action, decisionReason.trim(), csrfToken)
      setChapterState(updated)
      setDecisionReason("")
      if (action === "REQUEST_CHANGES") {
        setNotice(`Se han solicitado cambios para el Capítulo ${chapterNo}.`)
      } else if (action === "APPROVE") {
        setNotice(`Capítulo ${chapterNo} APROBADO formalmente por el asesor.`)
      } else {
        setNotice(`Capítulo ${chapterNo} reabierto a borrador.`)
      }
      void loadReviewData(chapterNo)
    } catch (cause) {
      if (cause instanceof ApiError && cause.detail.includes("ADVISOR_UNRESOLVED_COMMENTS")) {
        setError("No puedes aprobar el capítulo mientras existan observaciones abiertas (OPEN). Resuélvelas primero.")
      } else {
        setError(cause instanceof Error ? cause.message : "Error al procesar la decisión.")
      }
    } finally {
      setProcessingDecision(false)
    }
  }

  // Create Support Invitation
  async function handleCreateSupport(e: React.FormEvent) {
    e.preventDefault()
    if (!newSupportEmail.trim() || !newSupportInstructions.trim()) return
    setCreatingSupport(true)
    setError(null)
    try {
      const inv = await createSupportInvitation(
        project.project_id,
        {
          invited_email: newSupportEmail.trim(),
          task_id: newSupportTaskId.trim(),
          task_instructions: newSupportInstructions.trim(),
          ttl_hours: 168,
        },
        csrfToken,
      )
      setNotice(`Invitación creada para ${inv.invited_email} con token: ${inv.invite_token || "generado"}.`)
      setNewSupportEmail("")
      setNewSupportInstructions("")
      void loadSupportData()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al crear la invitación de apoyo.")
    } finally {
      setCreatingSupport(false)
    }
  }

  // Revoke Support Invitation
  async function handleRevokeSupport(invitationId: string) {
    setError(null)
    try {
      await revokeSupportInvitation(project.project_id, invitationId, csrfToken)
      setNotice("Invitación revocada.")
      void loadSupportData()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al revocar invitación.")
    }
  }

  // View Contributions for an invitation
  async function handleViewContributions(invId: string) {
    try {
      const res = await listSupportContributions(project.project_id, invId)
      setSelectedInvitationContributions({ id: invId, items: res.items })
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al cargar contribuciones.")
    }
  }

  const openCommentsCount = comments.filter((c) => c.status === "OPEN").length

  return (
    <div className="connected-app-shell">
      <aside className="sidebar connected-sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">T</div>
          <div><b>TesisMCP</b><span>Revisión y Asesor</span></div>
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
            <strong>Revisión académica y asesoría</strong>
          </div>
          <div className="top-actions">
            <span className="real-connection-pill"><i />Conectado a Django</span>
            <button className="button button-secondary" type="button" onClick={() => void onLogout()}>
              Cerrar sesión
            </button>
          </div>
        </header>

        <main className="advisor-page">
          <div className="workflow-header">
            <div>
              <span className="eyebrow blue">ACOMPAÑAMIENTO ACADÉMICO · CONTROL DE VERSIONES</span>
              <h1>Panel del Asesor, Snapshots y Apoyos</h1>
              <p>Revisión anclada de borradores e instantáneas, gestión de observaciones y decisiones formales.</p>
            </div>
            <div>
              <span className="status status-success">
                <span className="status-dot" />
                Rol: {project.role === "OWNER" ? "Tesista Titular" : "Asesor Asignado"}
              </span>
            </div>
          </div>

          {error && <div className="chapter-alert" role="alert">{error}</div>}
          {notice && <div className="chapter-notice" role="status">{notice}</div>}

          {/* Nav tabs */}
          <nav className="workflow-nav-tabs" aria-label="Secciones del panel de asesor">
            <button
              className={`workflow-nav-tab ${tab === "review" ? "active" : ""}`}
              onClick={() => setTab("review")}
              type="button"
            >
              Revisión de Capítulos y Observaciones
            </button>
            {isAdvisor && (
              <button
                className={`workflow-nav-tab ${tab === "advisor_overview" ? "active" : ""}`}
                onClick={() => setTab("advisor_overview")}
                type="button"
              >
                Proyectos asignados al Asesor
              </button>
            )}
            <button
              className={`workflow-nav-tab ${tab === "support" ? "active" : ""}`}
              onClick={() => setTab("support")}
              type="button"
            >
              Personas de Apoyo (Expertos)
            </button>
          </nav>

          {/* TAB 1: CHAPTER REVIEW & DECISIONS */}
          {tab === "review" && (
            <div>
              {/* Chapter and Snapshot Selector Bar */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "14px", flexWrap: "wrap", background: "white", padding: "14px 18px", borderRadius: "8px", border: "1px solid var(--line)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <label htmlFor="chapter-select" style={{ fontSize: "12px", fontWeight: 600 }}>Capítulo:</label>
                  <select
                    id="chapter-select"
                    value={chapterNo}
                    onChange={(e) => setChapterNo(Number(e.target.value))}
                    style={{ height: "36px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px", fontSize: "12px" }}
                  >
                    {[1, 2, 3, 4, 5, 6, 7].map((num) => (
                      <option key={num} value={num}>Capítulo {num}</option>
                    ))}
                  </select>

                  {chapterState && (
                    <span className={`status ${chapterState.status === "APPROVED" ? "status-success" : chapterState.status === "READY" ? "status-info" : chapterState.status === "CHANGES_REQUESTED" ? "status-warning" : ""}`}>
                      Estado: <b>{chapterState.status}</b>
                    </span>
                  )}
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <label htmlFor="snapshot-select" style={{ fontSize: "12px", fontWeight: 600 }}>Versión de lectura:</label>
                  <select
                    id="snapshot-select"
                    value={selectedSnapshotId ?? ""}
                    onChange={(e) => void handleSelectSnapshot(e.target.value)}
                    style={{ height: "36px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px", fontSize: "12px" }}
                  >
                    <option value="">Borrador actual en edición</option>
                    {snapshots.map((s) => (
                      <option key={s.snapshot_id} value={s.snapshot_id}>
                        Instantánea #{s.snapshot_no} ({s.status}) — {new Date(s.created_at).toLocaleDateString()}
                      </option>
                    ))}
                  </select>
                </div>

                {isOwner && (chapterState?.status === "DRAFT" || chapterState?.status === "CHANGES_REQUESTED") && (
                  <button
                    className="button button-primary"
                    type="button"
                    onClick={() => void handleSubmitChapter()}
                    disabled={submittingChapter}
                  >
                    {submittingChapter ? "Enviando…" : "Enviar capítulo a revisión"}
                  </button>
                )}
              </div>

              {loading ? (
                <div className="chapter-empty">Cargando revisión del capítulo…</div>
              ) : (
                <div className="advisor-review-grid">
                  {/* Left Column: Document / Snapshot content */}
                  <section className="advisor-doc-panel">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", borderBottom: "1px solid var(--line)", paddingBottom: "12px" }}>
                      <div>
                        <h2 style={{ margin: 0, fontSize: "17px", color: "var(--navy)" }}>
                          {activeSnapshotDetail
                            ? `Instantánea congelada #${activeSnapshotDetail.snapshot_no} (Solo lectura)`
                            : `Borrador del Capítulo ${chapterNo} (Vista de lectura)`}
                        </h2>
                        {activeSnapshotDetail && (
                          <div style={{ fontSize: "11px", color: "var(--muted)", marginTop: "4px" }}>
                            Hash SHA-256: <code>{activeSnapshotDetail.content_sha256}</code>
                          </div>
                        )}
                      </div>
                    </div>

                    <div ref={documentTextRef} onMouseUp={captureCommentAnchor} onKeyUp={captureCommentAnchor} style={{ font: "14px/1.8 'Source Serif 4', Georgia, serif", color: "var(--ink)", whiteSpace: "pre-wrap" }}>
                      {activeSnapshotDetail
                        ? activeSnapshotDetail.content_md || "Esta instantánea no contiene texto plano."
                        : chapterDoc?.content_md || "No hay texto redactado en este capítulo todavía."}
                    </div>
                  </section>

                  {/* Right Column: Comments & Academic Decisions */}
                  <aside className="advisor-comments-panel">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                      <h3 style={{ margin: 0, fontSize: "15px", color: "var(--navy)" }}>
                        Observaciones ({comments.length})
                      </h3>
                      {openCommentsCount > 0 && (
                        <span className="workflow-badge-protected">
                          {openCommentsCount} {openCommentsCount === 1 ? "abierta" : "abiertas"}
                        </span>
                      )}
                    </div>

                    {/* Add observation form (Advisor action) */}
                    {canCommentOnSnapshot && (
                      <form onSubmit={(e) => void handleAddComment(e)} style={{ marginBottom: "18px", padding: "12px", background: "#f8fafc", borderRadius: "7px", border: "1px solid var(--line)" }}>
                        <strong style={{ fontSize: "12px", display: "block", marginBottom: "6px" }}>Registrar observación como Asesor:</strong>
                        <p style={{ fontSize: "11px", color: "var(--muted)" }}>Selecciona con el cursor el fragmento exacto en la instantánea de la izquierda.</p>
                        <div className="review-comment-anchor" style={{ whiteSpace: "pre-wrap" }}>
                          {commentAnchor?.selected_text ?? "Aún no has seleccionado un fragmento."}
                        </div>
                        <textarea
                          placeholder="Escribe la observación metodológica o temática…"
                          value={newCommentBody}
                          onChange={(e) => setNewCommentBody(e.target.value)}
                          style={{ width: "100%", minHeight: "70px", padding: "8px", border: "1px solid var(--line)", borderRadius: "5px", fontSize: "12px", marginBottom: "8px" }}
                        />
                        <div style={{ display: "flex", justifyContent: "flex-end" }}>
                          <button className="button button-primary" type="submit" disabled={submittingComment || !newCommentBody.trim() || !commentAnchor}>
                            {submittingComment ? "Guardando…" : "Agregar observación"}
                          </button>
                        </div>
                      </form>
                    )}

                    {isAdvisor && !canCommentOnSnapshot && (
                      <p className="empty-hint">Las observaciones se registran sobre la instantánea vigente cuando el capítulo está en revisión.</p>
                    )}

                    {/* Comments list */}
                    <div style={{ maxHeight: "360px", overflowY: "auto" }}>
                      {comments.length === 0 ? (
                        <div style={{ textAlign: "center", padding: "20px 0", color: "var(--muted)", fontSize: "12px" }}>
                          No hay observaciones registradas en esta versión.
                        </div>
                      ) : (
                        comments.map((comm) => (
                          <div
                            key={comm.comment_id}
                            className={`review-comment-card ${comm.status === "RESOLVED" ? "resolved" : ""}`}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px", color: "var(--muted)" }}>
                              <span><b>{comm.author}</b></span>
                              <span className={`status ${comm.status === "RESOLVED" ? "status-success" : "status-warning"}`}>
                                {comm.status === "RESOLVED" ? "Resuelta" : "Abierta"}
                              </span>
                            </div>

                            {comm.selected_text && (
                              <div className="review-comment-anchor">
                                «{comm.selected_text}»
                              </div>
                            )}

                            <p style={{ margin: "6px 0 8px", fontSize: "12px", color: "var(--ink)", lineHeight: "1.5" }}>
                              {comm.body}
                            </p>

                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                              <span style={{ fontSize: "10px", color: "var(--muted)" }}>
                                {new Date(comm.created_at).toLocaleString()}
                              </span>
                              {comm.status === "OPEN" && (
                                <button
                                  className="button button-secondary"
                                  style={{ minHeight: "26px", padding: "0 8px", fontSize: "10px" }}
                                  type="button"
                                  onClick={() => void handleResolveComment(comm.comment_id)}
                                >
                                  Marcar resuelta ✓
                                </button>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>

                    {/* Decision Action Box (Advisor) */}
                    {isAdvisor && (
                      <div className="decision-action-box">
                        <strong style={{ fontSize: "13px", color: "var(--navy)", display: "block", marginBottom: "8px" }}>
                          Decisión formal del Asesor:
                        </strong>
                        <input
                          type="text"
                          placeholder="Motivo o justificación de la decisión…"
                          value={decisionReason}
                          onChange={(e) => setDecisionReason(e.target.value)}
                          style={{ width: "100%", height: "34px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px", fontSize: "12px", marginBottom: "10px" }}
                        />

                        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                          {chapterState?.status === "READY" && (
                            <>
                              <button
                                className="button button-secondary"
                                type="button"
                                onClick={() => void handleDecision("REQUEST_CHANGES")}
                                disabled={processingDecision || openCommentsCount === 0}
                                title={openCommentsCount === 0 ? "Exige al menos una observación abierta" : ""}
                              >
                                Solicitar cambios ({openCommentsCount})
                              </button>
                              <button
                                className="button button-primary"
                                type="button"
                                onClick={() => void handleDecision("APPROVE")}
                                disabled={processingDecision || openCommentsCount > 0}
                                title={openCommentsCount > 0 ? "Resuelve las observaciones antes de aprobar" : ""}
                              >
                                Aprobar capítulo ✓
                              </button>
                            </>
                          )}
                          {chapterState?.status === "APPROVED" && (
                            <button
                              className="button button-secondary"
                              type="button"
                              onClick={() => void handleDecision("REOPEN")}
                              disabled={processingDecision || !decisionReason.trim()}
                              title="Requiere motivo para reabrir"
                            >
                              Reabrir capítulo a borrador
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </aside>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: ADVISOR MULTI-PROJECT OVERVIEW */}
          {tab === "advisor_overview" && isAdvisor && (
            <div>
              <div className="chapter-info">
                <strong>Proyectos bajo tu asesoría:</strong>
                <p style={{ margin: "4px 0 0", fontSize: "11px" }}>
                  Datos entregados exactamente por el servidor según membresías vigentes.
                </p>
              </div>

              {loadingDashboard ? (
                <div className="chapter-empty">Cargando proyectos…</div>
              ) : advisorProjects.length === 0 ? (
                <div className="chapter-empty">No tienes proyectos asignados como asesor activo.</div>
              ) : (
                <div style={{ display: "grid", gap: "14px", marginTop: "14px" }}>
                  {advisorProjects.map((p) => (
                    <div key={p.project_id} style={{ background: "white", padding: "18px", borderRadius: "8px", border: "1px solid var(--line)", boxShadow: "var(--shadow-sm)" }}>
                      <h3 style={{ margin: "0 0 10px", fontSize: "15px", color: "var(--navy)" }}>{p.project_name}</h3>
                      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                        {p.chapters.map((ch) => (
                          <div
                            key={ch.chapter_no}
                            style={{
                              padding: "6px 10px",
                              borderRadius: "6px",
                              border: "1px solid var(--line)",
                              background: ch.status === "READY" ? "#eef4fa" : "#fafbfc",
                              fontSize: "11px",
                            }}
                          >
                            Capítulo {ch.chapter_no}: <b>{ch.status}</b>
                            {ch.status === "READY" && <span style={{ color: "var(--blue)", marginLeft: "4px" }}>● Pendiente</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: SUPPORT INVITATIONS */}
          {tab === "support" && (
            <div>
              <div className="chapter-info">
                <strong>Personas de Apoyo (Participación Opcional con Alcance Restringido):</strong>
                <p style={{ margin: "4px 0 0", fontSize: "11px" }}>
                  Invita a expertos temáticos o metodológicos para resolver consultas concretas sobre tareas y fuentes
                  específicas. Los apoyos no son miembros generales del proyecto ni asesores, y su acceso está delimitado
                  por token temporal.
                </p>
              </div>

              {/* Create Invitation Form (Owner only) */}
              {isOwner && (
                <form onSubmit={(e) => void handleCreateSupport(e)} style={{ background: "white", padding: "20px", borderRadius: "8px", border: "1px solid var(--line)", margin: "16px 0 24px" }}>
                  <h3 style={{ margin: "0 0 12px", fontSize: "15px", color: "var(--navy)" }}>Invitar persona de apoyo</h3>
                  <div style={{ display: "grid", gap: "12px", maxWidth: "600px" }}>
                    <div>
                      <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>Correo del experto / apoyo:</label>
                      <input
                        type="email"
                        placeholder="ejemplo@utp.edu.pe"
                        value={newSupportEmail}
                        onChange={(e) => setNewSupportEmail(e.target.value)}
                        style={{ width: "100%", height: "36px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px", fontSize: "12px" }}
                        required
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>Tarea asociada:</label>
                      <input
                        type="text"
                        placeholder="Ej. P10, P16 o USR_ENTREVISTA"
                        value={newSupportTaskId}
                        onChange={(e) => setNewSupportTaskId(e.target.value)}
                        style={{ width: "100%", height: "36px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px", fontSize: "12px" }}
                        required
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: "12px", fontWeight: 600, display: "block", marginBottom: "4px" }}>Instrucciones específicas para el apoyo:</label>
                      <textarea
                        placeholder="Indica con claridad la consulta técnica, metodológica o revisión requerida…"
                        value={newSupportInstructions}
                        onChange={(e) => setNewSupportInstructions(e.target.value)}
                        style={{ width: "100%", minHeight: "80px", padding: "8px", border: "1px solid var(--line)", borderRadius: "6px", fontSize: "12px" }}
                        required
                      />
                    </div>
                    <button className="button button-primary" type="submit" disabled={creatingSupport}>
                      {creatingSupport ? "Generando invitación…" : "Enviar invitación de apoyo"}
                    </button>
                  </div>
                </form>
              )}

              {/* Invitations List */}
              {loadingSupport ? (
                <div className="chapter-empty">Cargando personas de apoyo…</div>
              ) : supportInvitations.length === 0 ? (
                <div className="chapter-empty">No hay invitaciones de apoyo activas en este proyecto.</div>
              ) : (
                <div>
                  {supportInvitations.map((inv) => (
                    <article key={inv.invitation_id} className="support-invitation-card">
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                          <span className="workflow-task-id-badge">{inv.task_id}</span>
                          <span className={`status ${inv.status === "ACCEPTED" ? "status-success" : inv.status === "PENDING" ? "status-info" : "status-warning"}`}>
                            {inv.status}
                          </span>
                        </div>
                        <h4 style={{ margin: "0 0 4px", fontSize: "14px", color: "var(--navy)" }}>{inv.invited_email}</h4>
                        <p style={{ margin: "0 0 8px", fontSize: "12px", color: "var(--ink)", fontStyle: "italic" }}>
                          «{inv.task_instructions}»
                        </p>
                        <div style={{ fontSize: "11px", color: "var(--muted)" }}>
                          Creada: {new Date(inv.created_at).toLocaleDateString()} · Vence: {new Date(inv.expires_at).toLocaleDateString()}
                          {inv.invite_token && <span> · Token: <code>{inv.invite_token}</code></span>}
                        </div>
                      </div>

                      <div style={{ display: "flex", gap: "8px" }}>
                        <button
                          className="button button-secondary"
                          type="button"
                          onClick={() => void handleViewContributions(inv.invitation_id)}
                        >
                          Ver aportes
                        </button>
                        {isOwner && inv.status !== "REVOKED" && inv.status !== "EXPIRED" && (
                          <button
                            className="button button-secondary"
                            type="button"
                            onClick={() => void handleRevokeSupport(inv.invitation_id)}
                          >
                            Revocar
                          </button>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
              )}

              {/* Contributions view modal */}
              {selectedInvitationContributions && (
                <div className="workflow-modal-backdrop" onClick={() => setSelectedInvitationContributions(null)}>
                  <div className="workflow-modal-card" onClick={(e) => e.stopPropagation()}>
                    <span className="eyebrow blue">APORTES DE LA PERSONA DE APOYO</span>
                    <h2>Contribuciones registradas</h2>
                    {selectedInvitationContributions.items.length === 0 ? (
                      <div className="chapter-empty">Aún no se han recibido aportes de esta persona de apoyo.</div>
                    ) : (
                      selectedInvitationContributions.items.map((c) => (
                        <div key={c.contribution_id} style={{ padding: "12px", background: "#f8fafc", border: "1px solid var(--line)", borderRadius: "6px", marginBottom: "10px" }}>
                          <div style={{ fontSize: "11px", color: "var(--muted)", marginBottom: "6px" }}>
                            Registrado: {new Date(c.created_at).toLocaleString()}
                          </div>
                          <p style={{ margin: 0, font: "13px/1.6 'Source Serif 4', Georgia, serif" }}>
                            {c.response_text}
                          </p>
                        </div>
                      ))
                    )}
                    <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "16px" }}>
                      <button className="button button-primary" type="button" onClick={() => setSelectedInvitationContributions(null)}>
                        Cerrar
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
