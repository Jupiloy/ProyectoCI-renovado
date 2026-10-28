import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { ApiError } from "../../api/client"
import {
  disconnectZotero,
  getDocumentJob,
  getZoteroStatus,
  importBibliographyFile,
  importZoteroItem,
  listSearchStrategies,
  listSourceExcerpts,
  listSourceSegments,
  listSources,
  listZoteroItems,
  searchPassages,
  searchPeruDiscovery,
  searchSemanticScholar,
  selectDiscoveryCandidate,
  uploadSource,
} from "../../api/sources"
import type {
  DiscoveryCandidate,
  DocumentJob,
  PassageItem,
  ProjectState,
  ProjectSummary,
  SearchStrategy,
  SessionUser,
  SourceDocument,
  SourceExcerpt,
  SourceSegment,
  ZoteroConnectionStatus,
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

type Tab = "sources" | "passages" | "discovery" | "zotero"

export default function LibraryScreen({
  project,
  user,
  csrfToken,
  onBack,
  onUnauthorized,
  onAccessLost,
  onLogout,
}: Props) {
  const [tab, setTab] = useState<Tab>("sources")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [sources, setSources] = useState<SourceDocument[]>([])

  // Source selection for passage search
  const [selectedSourceIds, setSelectedSourceIds] = useState<Set<string>>(new Set())

  // Upload state
  const [uploadLabel, setUploadLabel] = useState("")
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [activeJob, setActiveJob] = useState<DocumentJob | null>(null)

  // Excerpts / Segments viewer modal
  const [viewingSource, setViewingSource] = useState<SourceDocument | null>(null)
  const [excerpts, setExcerpts] = useState<SourceExcerpt[]>([])
  const [segments, setSegments] = useState<SourceSegment[]>([])
  const [loadingExcerpts, setLoadingExcerpts] = useState(false)

  // Passages search
  const [passageQuery, setPassageQuery] = useState("")
  const [passageLimit, setPassageLimit] = useState(5)
  const [passageResults, setPassageResults] = useState<PassageItem[]>([])
  const [passageStatus, setPassageStatus] = useState<string | null>(null)
  const [searchingPassages, setSearchingPassages] = useState(false)

  // Discovery
  const [discoveryProvider, setDiscoveryProvider] = useState<"SEMANTIC" | "PERU" | "SCOPUS_WOS">("SEMANTIC")
  const [discoveryQuery, setDiscoveryQuery] = useState("")
  const [discoveryResults, setDiscoveryResults] = useState<DiscoveryCandidate[]>([])
  const [searchingDiscovery, setSearchingDiscovery] = useState(false)
  const [importingCandidateId, setImportingCandidateId] = useState<string | null>(null)

  // Bibliographic file upload (Scopus / WoS)
  const [bibFile, setBibFile] = useState<File | null>(null)
  const [bibProvider, setBibProvider] = useState<"SCOPUS" | "WOS" | "OTHER">("SCOPUS")
  const [importingBib, setImportingBib] = useState(false)

  // Zotero
  const [zoteroStatus, setZoteroStatus] = useState<ZoteroConnectionStatus | null>(null)
  const [zoteroItems, setZoteroItems] = useState<Array<Record<string, unknown>>>([])
  const [loadingZotero, setLoadingZotero] = useState(false)
  const [zoteroConfigError, setZoteroConfigError] = useState<string | null>(null)

  const loadSeq = useRef(0)
  const passageSearchSeq = useRef(0)

  const loadSourcesData = useCallback(async () => {
    const seq = ++loadSeq.current
    setLoading(true)
    setError(null)
    try {
      const list = await listSources(project.project_id)
      if (seq !== loadSeq.current) return
      setSources(list)
    } catch (cause) {
      if (seq !== loadSeq.current) return
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
      else if (cause instanceof ApiError && cause.status === 404) onAccessLost()
      else setError(cause instanceof Error ? cause.message : "Error al cargar las fuentes")
    } finally {
      if (seq === loadSeq.current) setLoading(false)
    }
  }, [project.project_id, onUnauthorized, onAccessLost])

  useEffect(() => {
    void loadSourcesData()
  }, [loadSourcesData])

  // Poll active document job if one exists
  useEffect(() => {
    if (!activeJob || activeJob.status === "SUCCEEDED" || activeJob.status === "FAILED") return
    const timer = setInterval(async () => {
      try {
        const updated = await getDocumentJob(project.project_id, activeJob.job_id)
        setActiveJob(updated)
        if (updated.status === "SUCCEEDED") {
          setNotice("Extracción del documento completada con éxito.")
          void loadSourcesData()
        } else if (updated.status === "FAILED") {
          setError(`Fallo en el trabajo de extracción: ${updated.error_message || updated.error_code || "Error desconocido"}`)
        }
      } catch {
        // Ignore transient poll error
      }
    }, 2500)
    return () => clearInterval(timer)
  }, [activeJob, project.project_id, loadSourcesData])

  // Load Zotero status on tab open
  useEffect(() => {
    if (tab !== "zotero") return
    let active = true
    setLoadingZotero(true)
    setZoteroConfigError(null)
    getZoteroStatus()
      .then((st) => {
        if (!active) return
        setZoteroStatus(st)
        if (st.connected) {
          listZoteroItems(project.project_id)
            .then((res) => {
              if (active && Array.isArray(res.items)) {
                setZoteroItems(res.items as Array<Record<string, unknown>>)
              }
            })
            .catch(() => {})
        }
      })
      .catch((cause) => {
        if (!active) return
        if (cause instanceof ApiError && cause.detail.includes("CONFIG_ERROR")) {
          setZoteroConfigError("El servidor no tiene configuradas las claves OAuth de Zotero (ZOTERO_OAUTH_CLIENT_KEY).")
        } else {
          setZoteroConfigError(cause instanceof Error ? cause.message : "No se pudo consultar el estado de Zotero.")
        }
      })
      .finally(() => {
        if (active) setLoadingZotero(false)
      })
    return () => {
      active = false
    }
  }, [tab, project.project_id])

  // Handle source file upload
  async function handleUpload(e: React.FormEvent) {
    e.preventDefault()
    if (!uploadFile) return
    const label = uploadLabel.trim() || uploadFile.name
    setUploading(true)
    setError(null)
    setNotice(null)
    try {
      const res = await uploadSource(project.project_id, label, uploadFile, csrfToken)
      setNotice(`Archivo subido correctamente (${res.verification_status}).`)
      setUploadFile(null)
      setUploadLabel("")
      if (res.job) {
        setActiveJob(res.job)
      }
      void loadSourcesData()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al subir el documento.")
    } finally {
      setUploading(false)
    }
  }

  // Handle view excerpts / segments
  async function handleViewExcerpts(source: SourceDocument) {
    setViewingSource(source)
    setLoadingExcerpts(true)
    setExcerpts([])
    setSegments([])
    try {
      const [exRes, segRes] = await Promise.all([
        listSourceExcerpts(project.project_id, source.source_id, 1, 50).catch(() => ({ source, excerpts: [] })),
        listSourceSegments(project.project_id, source.source_id, 0, 50).catch(() => ({ source, segments: [] })),
      ])
      setExcerpts(exRes.excerpts)
      setSegments(segRes.segments)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudieron cargar los extractos.")
    } finally {
      setLoadingExcerpts(false)
    }
  }

  // Toggle selection for passage search
  function toggleSourceSelection(sourceId: string) {
    passageSearchSeq.current += 1
    setPassageResults([])
    setPassageStatus(null)
    setSearchingPassages(false)
    setSelectedSourceIds((prev) => {
      const next = new Set(prev)
      if (next.has(sourceId)) next.delete(sourceId)
      else next.add(sourceId)
      return next
    })
  }

  // Handle passage search
  async function handleSearchPassages(e: React.FormEvent) {
    e.preventDefault()
    if (!passageQuery.trim()) return
    const requestNo = ++passageSearchSeq.current
    setSearchingPassages(true)
    setError(null)
    try {
      const res = await searchPassages(
        project.project_id, passageQuery.trim(), passageLimit,
        selectedSourceIds.size ? Array.from(selectedSourceIds) : undefined, csrfToken,
      )
      if (requestNo !== passageSearchSeq.current) return
      setPassageResults(res.results)
      setPassageStatus(res.search_status)
    } catch (cause) {
      if (requestNo === passageSearchSeq.current) {
        setError(cause instanceof Error ? cause.message : "Error al buscar pasajes.")
      }
    } finally {
      if (requestNo === passageSearchSeq.current) setSearchingPassages(false)
    }
  }

  // Handle Discovery search
  async function handleSearchDiscovery(e: React.FormEvent) {
    e.preventDefault()
    if (!discoveryQuery.trim()) return
    setSearchingDiscovery(true)
    setError(null)
    setDiscoveryResults([])
    try {
      if (discoveryProvider === "SEMANTIC") {
        const res = await searchSemanticScholar(project.project_id, discoveryQuery.trim(), 10)
        setDiscoveryResults(res.results)
      } else if (discoveryProvider === "PERU") {
        const res = await searchPeruDiscovery(project.project_id, discoveryQuery.trim(), 10)
        setDiscoveryResults(res.results)
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al buscar en el repositorio académico.")
    } finally {
      setSearchingDiscovery(false)
    }
  }

  // Handle selecting discovery candidate into project
  async function handleSelectCandidate(cand: DiscoveryCandidate) {
    if (project.role !== "OWNER") return
    setImportingCandidateId(cand.provider_record_id)
    setError(null)
    try {
      await selectDiscoveryCandidate(project.project_id, cand, csrfToken)
      setNotice(`"${cand.title}" importada a las fuentes del proyecto.`)
      void loadSourcesData()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al importar la fuente seleccionada.")
    } finally {
      setImportingCandidateId(null)
    }
  }

  // Handle bibliographic file import (Scopus / WoS)
  async function handleImportBibFile(e: React.FormEvent) {
    e.preventDefault()
    if (project.role !== "OWNER") return
    if (!bibFile) return
    setImportingBib(true)
    setError(null)
    try {
      const res = await importBibliographyFile(project.project_id, bibProvider, bibFile, csrfToken)
      setNotice(`Importación completada: ${res.imported_count || 0} registros incorporados desde ${bibProvider}.`)
      setBibFile(null)
      void loadSourcesData()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al importar el archivo bibliográfico.")
    } finally {
      setImportingBib(false)
    }
  }

  // Disconnect Zotero
  async function handleDisconnectZotero() {
    setLoadingZotero(true)
    setError(null)
    try {
      await disconnectZotero(csrfToken)
      setZoteroStatus(null)
      setNotice("Cuenta de Zotero desconectada.")
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al desconectar Zotero.")
    } finally {
      setLoadingZotero(false)
    }
  }

  return (
    <div className="connected-app-shell">
      <aside className="sidebar connected-sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">T</div>
          <div><b>TesisMCP</b><span>Biblioteca de fuentes</span></div>
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
            <strong>Biblioteca de fuentes y evidencia</strong>
          </div>
          <div className="top-actions">
            <span className="real-connection-pill"><i />Conectado a Django</span>
            <button className="button button-secondary" type="button" onClick={() => void onLogout()}>
              Cerrar sesión
            </button>
          </div>
        </header>

        <main className="library-page">
          <div className="workflow-header">
            <div>
              <span className="eyebrow blue">RESPALDO ACADÉMICO · CORPUS DOCUMENTAL</span>
              <h1>Biblioteca de fuentes y pasajes</h1>
              <p>Documentos cargados, texto extraído, localizadores de página y recuperación de pasajes.</p>
            </div>
            <div>
              <span className="status status-success">
                <span className="status-dot" />
                {sources.length} {sources.length === 1 ? "fuente registrada" : "fuentes registradas"}
              </span>
            </div>
          </div>

          {error && <div className="chapter-alert" role="alert">{error}</div>}
          {notice && <div className="chapter-notice" role="status">{notice}</div>}

          {/* Active Job status indicator */}
          {activeJob && (
            <div className="chapter-info" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong>Trabajo de extracción en progreso: {activeJob.kind}</strong>
                <p style={{ margin: "2px 0 0", fontSize: "11px" }}>
                  Estado: <b>{activeJob.status}</b> (Intento {activeJob.attempts}/3)
                </p>
              </div>
              <span className="status">{activeJob.status}</span>
            </div>
          )}

          {/* Nav tabs */}
          <nav className="workflow-nav-tabs" aria-label="Secciones de la biblioteca">
            <button
              className={`workflow-nav-tab ${tab === "sources" ? "active" : ""}`}
              onClick={() => setTab("sources")}
              type="button"
            >
              Fuentes del proyecto ({sources.length})
            </button>
            <button
              className={`workflow-nav-tab ${tab === "passages" ? "active" : ""}`}
              onClick={() => setTab("passages")}
              type="button"
            >
              Consulta de pasajes (NotebookLM) {selectedSourceIds.size > 0 ? `(${selectedSourceIds.size} selec.)` : ""}
            </button>
            <button
              className={`workflow-nav-tab ${tab === "discovery" ? "active" : ""}`}
              onClick={() => setTab("discovery")}
              type="button"
            >
              Descubrimiento y Scopus/WoS
            </button>
            <button
              className={`workflow-nav-tab ${tab === "zotero" ? "active" : ""}`}
              onClick={() => setTab("zotero")}
              type="button"
            >
              Zotero
            </button>
          </nav>

          {/* TAB 1: SOURCES */}
          {tab === "sources" && (
            <div>
              {/* Upload box */}
              {project.role === "OWNER" && (
                <form className="library-upload-box" onSubmit={(e) => void handleUpload(e)}>
                  <span className="eyebrow blue">SUBIR DOCUMENTO A LA BIBLIOTECA</span>
                  <h3 style={{ margin: "8px 0 4px", color: "var(--navy)", fontSize: "15px" }}>
                    Cargar archivo de investigación (.PDF, .DOCX, .PPTX, .XLSX)
                  </h3>
                  <p style={{ margin: "0 0 14px", color: "var(--muted)", fontSize: "12px" }}>
                    Límite máximo: 30 MB. El archivo se procesa extrayendo texto y localizadores físicos de página.
                  </p>
                  <div style={{ display: "flex", gap: "10px", justifyContent: "center", flexWrap: "wrap", alignItems: "center" }}>
                    <input
                      type="text"
                      placeholder="Etiqueta o título descriptivo (opcional)"
                      value={uploadLabel}
                      onChange={(e) => setUploadLabel(e.target.value)}
                      style={{ height: "36px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px", width: "260px", fontSize: "12px" }}
                    />
                    <input
                      type="file"
                      accept=".pdf,.docx,.pptx,.xlsx"
                      onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
                      style={{ fontSize: "12px" }}
                      disabled={uploading}
                    />
                    <button className="button button-primary" type="submit" disabled={!uploadFile || uploading}>
                      {uploading ? "Subiendo…" : "Subir y procesar"}
                    </button>
                  </div>
                </form>
              )}

              {loading ? (
                <div className="chapter-empty">Cargando biblioteca de fuentes…</div>
              ) : sources.length === 0 ? (
                <div className="chapter-empty">
                  No hay fuentes registradas en este proyecto. Puedes subir un documento o buscar en el catálogo académico.
                </div>
              ) : (
                <div className="library-source-grid">
                  {sources.map((src) => {
                    const isSelected = selectedSourceIds.has(src.source_id)
                    return (
                      <article
                        key={src.source_id}
                        className={`library-source-card ${isSelected ? "selected" : ""}`}
                      >
                        <div className="library-source-info">
                          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleSourceSelection(src.source_id)}
                              title="Seleccionar para consulta de pasajes"
                            />
                            <span className="workflow-badge-chapter" style={{ textTransform: "uppercase" }}>
                              {src.kind === "UPLOAD" ? "Archivo subido" : src.record_provider || "Externo"}
                            </span>
                            {src.physical_page_count !== null && (
                              <span className="workflow-badge-optional">{src.physical_page_count} páginas</span>
                            )}
                          </div>

                          <h3>{src.title || src.display_label || src.original_filename || "Documento sin título"}</h3>

                          <div className="library-source-meta">
                            {src.authors && src.authors.length > 0 && <span>Autores: {src.authors.join(", ")}</span>}
                            {src.publication_year && <span>Año: {src.publication_year}</span>}
                            {src.publication_venue && <span>Publicación: {src.publication_venue}</span>}
                            {src.doi && <span>DOI: {src.doi}</span>}
                            {src.original_filename && <span>Archivo: {src.original_filename}</span>}
                          </div>

                          <div>
                            {src.verification_status === "TEXT_CHECKED" && (
                              <span className="status status-success"><span className="status-dot" />Texto extraído ({src.excerpt_count} extractos)</span>
                            )}
                            {src.verification_status === "OCR_REQUIRED" && (
                              <span className="status status-warning">Requiere OCR</span>
                            )}
                            {src.verification_status === "PENDING_EXTRACTION" && (
                              <span className="status">Extracción pendiente</span>
                            )}
                            {src.verification_status === "METADATA_CHECKED" && (
                              <span className="status status-info">Solo metadatos</span>
                            )}
                          </div>
                        </div>

                        <div>
                          <button
                            className="button button-secondary"
                            type="button"
                            onClick={() => void handleViewExcerpts(src)}
                          >
                            Ver extractos / pasajes
                          </button>
                        </div>
                      </article>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: PASSAGES (NOTEBOOKLM EXPERIENCE) */}
          {tab === "passages" && (
            <div>
              <div className="chapter-info">
                <strong>Consulta y Recuperación Semántica de Pasajes (Experiencia tipo NotebookLM):</strong>
                <p style={{ margin: "4px 0 0", fontSize: "11px" }}>
                  Busca pasajes exactos dentro del corpus de textos extraídos del proyecto con distancia coseno
                  y localización de página. No reemplaza la lectura crítica humana ni certifica afirmaciones por sí sola.
                </p>
              </div>

              {selectedSourceIds.size > 0 && (
                <div style={{ margin: "12px 0", display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                  <span style={{ fontSize: "11px", fontWeight: 600 }}>Filtrando sobre {selectedSourceIds.size} fuente(s) seleccionada(s):</span>
                  <button className="button button-secondary" style={{ minHeight: "26px", padding: "0 8px", fontSize: "10px" }} onClick={() => {
                    passageSearchSeq.current += 1
                    setSelectedSourceIds(new Set())
                    setPassageResults([])
                    setPassageStatus(null)
                    setSearchingPassages(false)
                  }} type="button">
                    Limpiar selección (buscar en todo el proyecto)
                  </button>
                </div>
              )}

              <form onSubmit={(e) => void handleSearchPassages(e)} style={{ margin: "16px 0", display: "flex", gap: "10px", flexWrap: "wrap" }}>
                <input
                  type="text"
                  placeholder="Pregunta o consulta semántica sobre tus fuentes (hasta 500 caracteres)…"
                  value={passageQuery}
                  onChange={(e) => setPassageQuery(e.target.value)}
                  style={{ flex: 1, minWidth: "280px", height: "42px", padding: "0 14px", border: "1px solid var(--line)", borderRadius: "6px", fontSize: "13px" }}
                  maxLength={500}
                />
                <select
                  value={passageLimit}
                  onChange={(e) => setPassageLimit(Number(e.target.value))}
                  style={{ height: "42px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px", fontSize: "12px" }}
                >
                  <option value={3}>3 candidatos</option>
                  <option value={5}>5 candidatos</option>
                  <option value={10}>10 candidatos</option>
                  <option value={15}>15 candidatos</option>
                </select>
                <button className="button button-primary" type="submit" disabled={searchingPassages || !passageQuery.trim()}>
                  {searchingPassages ? "Buscando…" : "Buscar pasajes"}
                </button>
              </form>

              {passageStatus === "NO_INDEXED_PASSAGES" && (
                <div className="chapter-alert">
                  {selectedSourceIds.size ? "No hay pasajes indexados en las fuentes elegidas." : "No hay pasajes indexados en este proyecto."} Sube documentos con texto extraído para habilitar la búsqueda semántica.
                </div>
              )}

              {passageResults.length > 0 && (
                <div>
                  <div style={{ marginBottom: "14px", fontSize: "12px", color: "var(--muted)" }}>
                    Se encontraron <b>{passageResults.length} pasajes relevantes</b> ordenados por similitud vectorial:
                  </div>

                  {passageResults.map((p, idx) => (
                    <article key={p.passage_id || idx} className="passage-result-card">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                        <span className="workflow-task-id-badge">
                          {p.physical_page ? `Página física ${p.physical_page}` : p.locator_kind || "Segmento"}
                        </span>
                        <span style={{ fontSize: "11px", color: "var(--muted)" }}>
                          Distancia coseno: <b>{p.cosine_distance.toFixed(4)}</b>
                        </span>
                      </div>
                      <blockquote className="passage-quote">
                        «{p.text}»
                      </blockquote>
                      <div style={{ fontSize: "10px", color: "var(--muted)", display: "flex", justifyContent: "space-between" }}>
                        <span>Hash SHA-256: <code>{p.text_sha256.slice(0, 16)}…</code></span>
                        <span>{p.supports_claim_verified ? "Validado" : "Candidato no evaluado semánticamente"}</span>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: DISCOVERY (SEMANTIC SCHOLAR, PERU ALICIA, SCOPUS/WOS) */}
          {tab === "discovery" && (
            <div>
              <div style={{ display: "flex", gap: "8px", marginBottom: "18px" }}>
                <button
                  className={`button ${discoveryProvider === "SEMANTIC" ? "button-primary" : "button-secondary"}`}
                  type="button"
                  onClick={() => { setDiscoveryProvider("SEMANTIC"); setDiscoveryResults([]) }}
                >
                  Semantic Scholar
                </button>
                <button
                  className={`button ${discoveryProvider === "PERU" ? "button-primary" : "button-secondary"}`}
                  type="button"
                  onClick={() => { setDiscoveryProvider("PERU"); setDiscoveryResults([]) }}
                >
                  ALICIA / Perú Discovery
                </button>
                <button
                  className={`button ${discoveryProvider === "SCOPUS_WOS" ? "button-primary" : "button-secondary"}`}
                  type="button"
                  onClick={() => { setDiscoveryProvider("SCOPUS_WOS"); setDiscoveryResults([]) }}
                >
                  Scopus / Web of Science (Asistencia)
                </button>
              </div>

              {discoveryProvider !== "SCOPUS_WOS" ? (
                <div>
                  <form onSubmit={(e) => void handleSearchDiscovery(e)} style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
                    <input
                      type="text"
                      placeholder={`Buscar literatura en ${discoveryProvider === "SEMANTIC" ? "Semantic Scholar" : "repositorios de Perú (ALICIA)"}…`}
                      value={discoveryQuery}
                      onChange={(e) => setDiscoveryQuery(e.target.value)}
                      style={{ flex: 1, height: "40px", padding: "0 12px", border: "1px solid var(--line)", borderRadius: "6px", fontSize: "12px" }}
                    />
                    <button className="button button-primary" type="submit" disabled={searchingDiscovery || !discoveryQuery.trim()}>
                      {searchingDiscovery ? "Buscando…" : "Buscar"}
                    </button>
                  </form>

                  {discoveryResults.map((cand) => (
                    <article key={cand.provider_record_id} className="discovery-card">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px" }}>
                        <div>
                          <h4 style={{ margin: "0 0 6px", color: "var(--navy)", fontSize: "14px" }}>{cand.title}</h4>
                          <p style={{ margin: "0 0 8px", fontSize: "11px", color: "var(--muted)" }}>
                            {cand.authors?.join(", ")} · {cand.publication_year || "S/F"} {cand.publication_venue ? `· ${cand.publication_venue}` : ""}
                          </p>
                          {cand.abstract && (
                            <p style={{ margin: "0 0 10px", fontSize: "12px", color: "#344054", lineHeight: "1.5" }}>
                              {cand.abstract.slice(0, 320)}…
                            </p>
                          )}
                          {cand.record_url && (
                            <a href={cand.record_url} target="_blank" rel="noreferrer" style={{ fontSize: "11px", color: "var(--blue)" }}>
                              Ver registro oficial ↗
                            </a>
                          )}
                        </div>
                        {project.role === "OWNER" && (
                          <button
                            className="button button-secondary"
                            type="button"
                            onClick={() => void handleSelectCandidate(cand)}
                            disabled={importingCandidateId === cand.provider_record_id}
                          >
                            {importingCandidateId === cand.provider_record_id ? "Importando…" : "Importar a fuentes"}
                          </button>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div>
                  <div className="chapter-info">
                    <strong>Acceso y asistencia para Scopus y Web of Science:</strong>
                    <p style={{ margin: "4px 0 0", fontSize: "11px" }}>
                      TesisMCP no declara acceso automático a textos completos bajo suscripción institucional.
                      Formula aquí tu ecuación de búsqueda, ejecútala en el portal oficial y luego importa el archivo
                      de exportación (.RIS, .BIB o .CSV).
                    </p>
                  </div>

                  <div style={{ background: "white", padding: "20px", borderRadius: "8px", border: "1px solid var(--line)", marginBottom: "20px" }}>
                    <h3 style={{ margin: "0 0 10px", fontSize: "14px", color: "var(--navy)" }}>Enlaces a portales oficiales</h3>
                    <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                      <a href="https://www.scopus.com" target="_blank" rel="noreferrer" className="button button-secondary">
                        Abrir portal oficial de Scopus ↗
                      </a>
                      <a href="https://www.webofscience.com" target="_blank" rel="noreferrer" className="button button-secondary">
                        Abrir portal oficial de Web of Science ↗
                      </a>
                    </div>
                  </div>

                  {project.role === "OWNER" && <form onSubmit={(e) => void handleImportBibFile(e)} style={{ background: "white", padding: "20px", borderRadius: "8px", border: "1px solid var(--line)" }}>
                    <h3 style={{ margin: "0 0 6px", fontSize: "14px", color: "var(--navy)" }}>Importar exportación bibliográfica</h3>
                    <p style={{ margin: "0 0 14px", fontSize: "11px", color: "var(--muted)" }}>
                      Admite archivos .RIS, .BIB, .BIBTEX o .CSV exportados desde Scopus o Web of Science (hasta 5 MB).
                    </p>
                    <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
                      <select
                        value={bibProvider}
                        onChange={(e) => setBibProvider(e.target.value as "SCOPUS" | "WOS" | "OTHER")}
                        style={{ height: "36px", padding: "0 10px", border: "1px solid var(--line)", borderRadius: "6px", fontSize: "12px" }}
                      >
                        <option value="SCOPUS">Scopus (.ris, .bib, .csv)</option>
                        <option value="WOS">Web of Science (.ciw, .bib, .txt)</option>
                        <option value="OTHER">Otro gestor (.bib, .ris)</option>
                      </select>
                      <input
                        type="file"
                        accept=".ris,.bib,.bibtex,.csv"
                        onChange={(e) => setBibFile(e.target.files?.[0] ?? null)}
                        style={{ fontSize: "12px" }}
                        disabled={importingBib}
                      />
                      <button className="button button-primary" type="submit" disabled={!bibFile || importingBib}>
                        {importingBib ? "Importando…" : "Importar metadatos"}
                      </button>
                    </div>
                  </form>}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: ZOTERO */}
          {tab === "zotero" && (
            <div>
              <div className="chapter-info">
                <strong>Integración Zotero Web API:</strong>
                <p style={{ margin: "4px 0 0", fontSize: "11px" }}>
                  Permite sincronizar y consultar referencias de tu biblioteca personal de Zotero sin duplicar
                  su aplicación ni depender de Collabora Online.
                </p>
              </div>

              {loadingZotero ? (
                <div className="chapter-empty">Consultando estado de conexión con Zotero…</div>
              ) : zoteroConfigError ? (
                <div className="chapter-alert">
                  <strong>Configuración pendiente en el servidor:</strong> {zoteroConfigError}
                  <p style={{ margin: "6px 0 0", fontSize: "11px" }}>
                    Para probar OAuth real, el administrador debe definir <code>ZOTERO_OAUTH_CLIENT_KEY</code> y{" "}
                    <code>ZOTERO_OAUTH_CLIENT_SECRET</code> en el entorno.
                  </p>
                </div>
              ) : zoteroStatus?.connected ? (
                <div>
                  <div style={{ background: "white", padding: "20px", borderRadius: "8px", border: "1px solid var(--line)", marginBottom: "20px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <span className="status status-success"><span className="status-dot" />Zotero conectado</span>
                        <h3 style={{ margin: "8px 0 4px", fontSize: "15px", color: "var(--navy)" }}>
                          Usuario Zotero ID: {zoteroStatus.zotero_user_id}
                        </h3>
                        <p style={{ margin: 0, fontSize: "11px", color: "var(--muted)" }}>
                          Permisos concedidos: {zoteroStatus.granted_scopes.join(", ") || "Lectura personal"}
                        </p>
                      </div>
                      <button className="button button-secondary" type="button" onClick={() => void handleDisconnectZotero()}>
                        Desconectar Zotero
                      </button>
                    </div>
                  </div>

                  <h3 style={{ fontSize: "14px", color: "var(--navy)", margin: "0 0 12px" }}>Ítems en tu biblioteca personal de Zotero</h3>
                  {zoteroItems.length === 0 ? (
                    <div className="chapter-empty">No se encontraron ítems en tu biblioteca o la sincronización está en curso.</div>
                  ) : (
                    zoteroItems.map((item, idx) => {
                      const data = (item.data as Record<string, unknown>) || {}
                      const itemKey = (item.key as string) || (data.key as string) || ""
                      return (
                        <div key={itemKey || idx} className="discovery-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <div>
                            <b>{(data.title as string) || "Referencia sin título"}</b>
                            <p style={{ margin: "4px 0 0", fontSize: "11px", color: "var(--muted)" }}>
                              Tipo: {(data.itemType as string) || "Desconocido"} {data.date ? `· ${data.date}` : ""}
                            </p>
                          </div>
                          {project.role === "OWNER" && <button
                            className="button button-secondary"
                            type="button"
                            onClick={() => {
                              if (itemKey) {
                                void importZoteroItem(project.project_id, itemKey, csrfToken)
                                  .then(() => { setNotice("Ítem importado desde Zotero."); void loadSourcesData() })
                                  .catch((err) => setError(err instanceof Error ? err.message : "Error al importar de Zotero"))
                              }
                            }}
                          >
                            Importar al proyecto
                          </button>}
                        </div>
                      )
                    })
                  )}
                </div>
              ) : (
                <div style={{ background: "white", padding: "24px", borderRadius: "8px", border: "1px solid var(--line)", textAlign: "center" }}>
                  <h3 style={{ margin: "0 0 8px", fontSize: "16px", color: "var(--navy)" }}>Conectar cuenta de Zotero</h3>
                  <p style={{ margin: "0 auto 16px", maxWidth: "500px", fontSize: "12px", color: "var(--muted)", lineHeight: "1.5" }}>
                    Inicia el flujo OAuth para vincular tu biblioteca personal de Zotero y acceder a tus referencias
                    directamente desde TesisMCP.
                  </p>
                  <a
                    href="/api/v1/integrations/zotero/connect"
                    className="button button-primary"
                    style={{ textDecoration: "none", display: "inline-flex" }}
                  >
                    Iniciar conexión OAuth con Zotero ↗
                  </a>
                </div>
              )}
            </div>
          )}

          {/* VIEW EXCERPTS MODAL */}
          {viewingSource && (
            <div className="workflow-modal-backdrop" onClick={() => setViewingSource(null)}>
              <div className="workflow-modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "800px" }}>
                <span className="eyebrow blue">TEXTO EXTRAÍDO Y LOCALIZADORES</span>
                <h2>{viewingSource.title || viewingSource.display_label || viewingSource.original_filename}</h2>
                <p>
                  Estado: <b>{viewingSource.verification_status}</b> · Método: {viewingSource.text_extraction_method || "No especificado"} · Páginas físicas: {viewingSource.physical_page_count ?? "N/A"}
                </p>

                {loadingExcerpts ? (
                  <div className="chapter-empty">Cargando pasajes y extractos…</div>
                ) : excerpts.length === 0 && segments.length === 0 ? (
                  <div className="chapter-empty">
                    Este documento aún no tiene extractos de texto extraídos.
                    {viewingSource.verification_status === "OCR_REQUIRED" && " Requiere procesamiento OCR."}
                  </div>
                ) : (
                  <div style={{ maxHeight: "500px", overflowY: "auto", display: "grid", gap: "12px" }}>
                    {excerpts.map((ex) => (
                      <div key={ex.excerpt_id} style={{ padding: "12px", background: "#f8fafc", border: "1px solid var(--line)", borderRadius: "6px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--muted)", marginBottom: "6px" }}>
                          <span className="workflow-task-id-badge">Página física {ex.physical_page}</span>
                          <span>Pasaje #{ex.excerpt_id}</span>
                        </div>
                        <p style={{ margin: 0, font: "13px/1.6 'Source Serif 4', Georgia, serif", color: "var(--ink)", whiteSpace: "pre-wrap" }}>
                          {ex.text}
                        </p>
                        <div style={{ marginTop: "6px", fontSize: "10px", color: "var(--muted)" }}>
                          SHA-256: <code>{ex.text_sha256}</code>
                        </div>
                      </div>
                    ))}
                    {segments.map((seg) => (
                      <div key={seg.segment_id} style={{ padding: "12px", background: "#f8fafc", border: "1px solid var(--line)", borderRadius: "6px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--muted)", marginBottom: "6px" }}>
                          <span className="workflow-task-id-badge">{seg.kind || "Segmento"}</span>
                          <span>Secuencia #{seg.sequence_no}</span>
                        </div>
                        {seg.heading && <strong style={{ display: "block", marginBottom: "4px" }}>{seg.heading}</strong>}
                        <p style={{ margin: 0, font: "13px/1.6 'Source Serif 4', Georgia, serif", color: "var(--ink)", whiteSpace: "pre-wrap" }}>
                          {seg.text}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "18px" }}>
                  <button className="button button-primary" type="button" onClick={() => setViewingSource(null)}>
                    Cerrar
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
