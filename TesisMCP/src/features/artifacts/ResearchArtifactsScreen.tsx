import { useEffect, useRef, useState } from "react"
import {
  getChapterIeeeCitations,
  listCitationEvidence,
} from "../../api/chapters"
import CitationReviewPanel from "./CitationReviewPanel"
import { downloadApprovedChapterDocx, downloadDraftDocx, triggerBlobDownload } from "../../api/exports"
import {
  createDataset,
  createFigure,
  createTableRecipe,
  downloadDatasetFile,
  getFigurePreviewUrl,
  listDatasets,
  listDatasetVersions,
  listFigures,
  listFigureVersions,
  listTableRecipes,
  listTableRecipeVersions,
} from "../../api/research"
import type {
  CitationEvidenceReview,
  IeeeCitationView,
  ResearchDataset,
  ResearchDatasetVersion,
  ResearchFigure,
  ResearchFigureVersion,
  TableRecipe,
  TableRecipeVersion,
} from "../../api/types"

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

function recipeSpecFor(version?: ResearchDatasetVersion): string {
  if (!version || version.column_names.length === 0 || version.row_count === 0) return ""
  return JSON.stringify({ columns: version.column_names, filters: [], sort: [], limit: 50 }, null, 2)
}

function figureSpecFor(table: TableRecipeVersion): string {
  const numeric = table.result_columns.find((column) =>
    table.rows.length > 0 && table.rows.every((row) => {
      const value = row[column]
      return typeof value === "number" && Number.isFinite(value)
    }),
  )
  const x = table.result_columns.find((column) => column !== numeric) ?? numeric
  if (!x || !numeric || table.rows.length === 0 || table.rows.length > 30) return ""
  return JSON.stringify({
    chart_type: "BAR", x_column: x, y_column: numeric, title: table.name,
    x_label: x, y_label: numeric, alt_text: `Gráfico de barras de ${numeric} por ${x}`,
  }, null, 2)
}

export type ResearchArtifactsScreenProps = {
  projectId: string
  projectName: string
  canWrite: boolean
  csrfToken?: string
  stateVersion: number
  onBack: () => void
}

type TabKey = "datasets" | "tables" | "figures" | "citations" | "export"

export function ResearchArtifactsScreen({
  projectId,
  projectName,
  canWrite,
  csrfToken,
  stateVersion,
  onBack,
}: ResearchArtifactsScreenProps) {
  const [activeTab, setActiveTab] = useState<TabKey>("datasets")

  // Datasets state
  const [datasets, setDatasets] = useState<ResearchDataset[]>([])
  const [selectedDataset, setSelectedDataset] = useState<ResearchDataset | null>(null)
  const [datasetVersions, setDatasetVersions] = useState<ResearchDatasetVersion[]>([])
  const [datasetName, setDatasetName] = useState("")
  const [datasetDesc, setDatasetDesc] = useState("")
  const [datasetFile, setDatasetFile] = useState<File | null>(null)

  // Tables state
  const [tableRecipes, setTableRecipes] = useState<TableRecipe[]>([])
  const [selectedRecipe, setSelectedRecipe] = useState<TableRecipe | null>(null)
  const [recipeVersions, setRecipeVersions] = useState<TableRecipeVersion[]>([])
  const [newRecipeName, setNewRecipeName] = useState("")
  const [newRecipeSpec, setNewRecipeSpec] = useState("")

  // Figures state
  const [figures, setFigures] = useState<ResearchFigure[]>([])
  const [selectedFigure, setSelectedFigure] = useState<ResearchFigure | null>(null)
  const [figureVersions, setFigureVersions] = useState<ResearchFigureVersion[]>([])
  const [newFigureName, setNewFigureName] = useState("")
  const [newFigureSpec, setNewFigureSpec] = useState("")
  const [acceptTruncatedInput, setAcceptTruncatedInput] = useState(false)

  // Citations IEEE state
  const [selectedChapterNo, setSelectedChapterNo] = useState<number>(1)
  const [ieeeView, setIeeeView] = useState<IeeeCitationView | null>(null)
  const [selectedOccurrenceId, setSelectedOccurrenceId] = useState<string | null>(null)
  const [evidenceList, setEvidenceList] = useState<CitationEvidenceReview[]>([])
  const [loadingEvidence, setLoadingEvidence] = useState(false)
  const evidenceRequestRef = useRef(0)
  const citationRequestRef = useRef(0)
  const datasetVersionRequestRef = useRef(0)
  const recipeVersionRequestRef = useRef(0)

  // Global status
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Load datasets on mount
  useEffect(() => {
    loadDatasets()
  }, [projectId])

  const loadDatasets = async () => {
    try {
      const list = await listDatasets(projectId)
      setDatasets(list)
      if (list.length > 0 && !selectedDataset) {
        setSelectedDataset(list[0])
        loadDatasetVersions(list[0].dataset_id)
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    }
  }

  const loadDatasetVersions = async (datasetId: string) => {
    const requestNo = ++datasetVersionRequestRef.current
    try {
      const vers = await listDatasetVersions(projectId, datasetId)
      if (requestNo !== datasetVersionRequestRef.current) return
      setDatasetVersions(vers)
      setNewRecipeSpec(recipeSpecFor(vers[vers.length - 1]))
      if (vers.length > 0) {
        loadTableRecipes(datasetId, vers[vers.length - 1].version_no)
      }
    } catch {
      if (requestNo !== datasetVersionRequestRef.current) return
      setDatasetVersions([])
      setNewRecipeSpec("")
    }
  }

  const loadTableRecipes = async (datasetId: string, versionNo: number) => {
    try {
      const list = await listTableRecipes(projectId, datasetId, versionNo)
      setTableRecipes(list)
      if (list.length > 0) {
        setSelectedRecipe(list[0])
        loadTableRecipeVersions(datasetId, list[0].recipe_id)
      }
    } catch {
      setTableRecipes([])
    }
  }

  const loadTableRecipeVersions = async (datasetId: string, recipeId: string) => {
    const requestNo = ++recipeVersionRequestRef.current
    try {
      const vers = await listTableRecipeVersions(projectId, datasetId, recipeId)
      if (requestNo !== recipeVersionRequestRef.current) return
      setRecipeVersions(vers)
      setNewFigureSpec(vers.length ? figureSpecFor(vers[vers.length - 1]) : "")
      setAcceptTruncatedInput(false)
      if (vers.length > 0) {
        loadFigures(datasetId, recipeId, vers[vers.length - 1].version_no)
      }
    } catch {
      if (requestNo !== recipeVersionRequestRef.current) return
      setRecipeVersions([])
      setNewFigureSpec("")
    }
  }

  const loadFigures = async (datasetId: string, recipeId: string, tableVersionNo: number) => {
    try {
      const list = await listFigures(projectId, datasetId, recipeId, tableVersionNo)
      setFigures(list)
      if (list.length > 0) {
        setSelectedFigure(list[0])
        loadFigureVersions(datasetId, list[0].figure_id)
      }
    } catch {
      setFigures([])
    }
  }

  const loadFigureVersions = async (datasetId: string, figureId: string) => {
    try {
      const vers = await listFigureVersions(projectId, datasetId, figureId)
      setFigureVersions(vers)
    } catch {
      setFigureVersions([])
    }
  }

  // Load IEEE citations when switching to citations tab or chapter changes
  useEffect(() => {
    if (activeTab === "citations") {
      loadIeeeCitations(selectedChapterNo)
    }
  }, [activeTab, selectedChapterNo, projectId])

  const loadIeeeCitations = async (chapterNo: number) => {
    const requestNo = ++citationRequestRef.current
    evidenceRequestRef.current += 1
    setSelectedOccurrenceId(null)
    setEvidenceList([])
    setLoadingEvidence(false)
    setIeeeView(null)
    setLoading(true)
    setErrorMsg(null)
    try {
      const view = await getChapterIeeeCitations(projectId, chapterNo)
      if (requestNo === citationRequestRef.current) setIeeeView(view)
    } catch (err) {
      if (requestNo === citationRequestRef.current) {
        setErrorMsg(err instanceof Error ? err.message : String(err))
      }
    } finally {
      if (requestNo === citationRequestRef.current) setLoading(false)
    }
  }

  const loadOccurrenceEvidence = async (occurrenceId: string) => {
    const requestNo = ++evidenceRequestRef.current
    setSelectedOccurrenceId(occurrenceId)
    setEvidenceList([])
    setLoadingEvidence(true)
    setErrorMsg(null)
    try {
      const reviews = await listCitationEvidence(projectId, selectedChapterNo, occurrenceId)
      if (requestNo === evidenceRequestRef.current) setEvidenceList(reviews)
    } catch (err) {
      if (requestNo === evidenceRequestRef.current) {
        setErrorMsg(err instanceof Error ? err.message : "No se pudo consultar la evidencia de esta cita.")
      }
    } finally {
      if (requestNo === evidenceRequestRef.current) setLoadingEvidence(false)
    }
  }

  const refreshOccurrenceEvidence = async (occurrenceId: string) => {
    const requestNo = ++evidenceRequestRef.current
    const reviews = await listCitationEvidence(projectId, selectedChapterNo, occurrenceId)
    if (requestNo === evidenceRequestRef.current) setEvidenceList(reviews)
  }

  const handleUploadDataset = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canWrite) return
    if (!datasetFile || !datasetName.trim()) {
      setErrorMsg("Debe ingresar el nombre del dataset y seleccionar un archivo.")
      return
    }

    setLoading(true)
    setErrorMsg(null)
    setSuccessMsg(null)

    const fd = new FormData()
    fd.append("name", datasetName.trim())
    fd.append("description", datasetDesc.trim())
    fd.append("file", datasetFile)
    fd.append("idempotency_key", generateUuid())

    try {
      const res = await createDataset(projectId, fd, csrfToken)
      setSuccessMsg(`Dataset creado con éxito (Versión v${res.version_no}).`)
      setDatasetName("")
      setDatasetDesc("")
      setDatasetFile(null)
      loadDatasets()
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadDataset = async (datasetId: string, versionNo: number) => {
    try {
      const { blob, filename } = await downloadDatasetFile(projectId, datasetId, versionNo)
      triggerBlobDownload(blob, filename || `dataset-${datasetId.slice(0, 8)}-v${versionNo}.csv`)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    }
  }

  const handleCreateTableRecipe = async () => {
    if (!canWrite) return
    if (!selectedDataset || datasetVersions.length === 0 || !newRecipeName.trim()) {
      setErrorMsg("Seleccione un dataset y defina el nombre de la receta.")
      return
    }

    let parsedSpec: Record<string, unknown> = {}
    try {
      parsedSpec = JSON.parse(newRecipeSpec)
    } catch {
      setErrorMsg("La especificación de la receta debe ser un JSON válido.")
      return
    }
    const columns = datasetVersions[datasetVersions.length - 1]?.column_names ?? []
    if (!parsedSpec || Array.isArray(parsedSpec) || typeof parsedSpec !== "object"
        || !Array.isArray(parsedSpec.columns) || parsedSpec.columns.length === 0
        || parsedSpec.columns.some((column) => typeof column !== "string" || !columns.includes(column))
        || typeof parsedSpec.limit !== "number" || !Number.isInteger(parsedSpec.limit)
        || parsedSpec.limit < 1 || parsedSpec.limit > 10000) {
      setErrorMsg("La receta requiere columns con nombres del dataset y limit entre 1 y 10000.")
      return
    }

    setLoading(true)
    setErrorMsg(null)
    setSuccessMsg(null)

    const latestDatasetVersion = datasetVersions[datasetVersions.length - 1].version_no

    try {
      const res = await createTableRecipe(
        projectId,
        selectedDataset.dataset_id,
        latestDatasetVersion,
        {
          name: newRecipeName.trim(),
          spec: parsedSpec,
          idempotency_key: generateUuid(),
        },
        csrfToken,
      )
      setSuccessMsg(`Receta tabular creada con éxito (v${res.version_no}).`)
      setNewRecipeName("")
      loadTableRecipes(selectedDataset.dataset_id, latestDatasetVersion)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleCreateFigure = async () => {
    if (!canWrite) return
    if (!selectedDataset || !selectedRecipe || recipeVersions.length === 0 || !newFigureName.trim()) {
      setErrorMsg("Seleccione una receta tabular y defina el nombre de la figura.")
      return
    }

    let parsedSpec: Record<string, unknown> = {}
    try {
      parsedSpec = JSON.parse(newFigureSpec)
    } catch {
      setErrorMsg("La especificación de la figura debe ser un JSON válido.")
      return
    }
    const table = recipeVersions[recipeVersions.length - 1]
    const keys = ["chart_type", "x_column", "y_column", "title", "x_label", "y_label", "alt_text"]
    if (!table || !parsedSpec || Array.isArray(parsedSpec) || typeof parsedSpec !== "object"
        || Object.keys(parsedSpec).length !== keys.length || keys.some((key) => !(key in parsedSpec))
        || !["BAR", "LINE", "SCATTER"].includes(String(parsedSpec.chart_type))
        || !table.result_columns.includes(String(parsedSpec.x_column))
        || !table.result_columns.includes(String(parsedSpec.y_column))
        || keys.slice(3).some((key) => typeof parsedSpec[key] !== "string" || !String(parsedSpec[key]).trim())) {
      setErrorMsg("La figura requiere un tipo válido, columnas x/y de la tabla, título, etiquetas y texto alternativo.")
      return
    }

    setLoading(true)
    setErrorMsg(null)
    setSuccessMsg(null)

    const latestTableVersion = recipeVersions[recipeVersions.length - 1].version_no

    try {
      const res = await createFigure(
        projectId,
        selectedDataset.dataset_id,
        selectedRecipe.recipe_id,
        latestTableVersion,
        {
          name: newFigureName.trim(),
          spec: parsedSpec,
          idempotency_key: generateUuid(),
          accept_truncated_input: acceptTruncatedInput,
        },
        csrfToken,
      )
      setSuccessMsg(`Figura científica generada con éxito (v${res.version_no}).`)
      setNewFigureName("")
      loadFigures(selectedDataset.dataset_id, selectedRecipe.recipe_id, latestTableVersion)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleExportDraft = async () => {
    setLoading(true)
    setErrorMsg(null)
    setSuccessMsg(null)
    try {
      const name = await downloadDraftDocx(projectId)
      setSuccessMsg(`Borrador descargado correctamente como '${name}'.`)
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  const handleExportApprovedChapter = async () => {
    setLoading(true)
    setErrorMsg(null)
    setSuccessMsg(null)
    try {
      const name = await downloadApprovedChapterDocx(projectId, selectedChapterNo)
      setSuccessMsg(`Capítulo ${selectedChapterNo} aprobado descargado como '${name}'.`)
    } catch (err) {
      setErrorMsg(
        err instanceof Error
          ? err.message
          : `No se pudo descargar el capítulo ${selectedChapterNo}. Verifica que haya sido aprobado formalmente por el asesor.`,
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="connected-screen artifacts-screen">
      <header className="screen-header">
        <div>
          <button className="btn-secondary" onClick={onBack}>
            ← Volver al Proyecto
          </button>
          <h2>Datos de Investigación, Citas IEEE y Exportación</h2>
          <p className="screen-subtitle">
            Proyecto: <strong>{projectName}</strong> (v{stateVersion})
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

      <div className="screen-tabs">
        <button
          className={`tab-btn ${activeTab === "datasets" ? "active" : ""}`}
          onClick={() => setActiveTab("datasets")}
        >
          1. Datasets
        </button>
        <button
          className={`tab-btn ${activeTab === "tables" ? "active" : ""}`}
          onClick={() => setActiveTab("tables")}
        >
          2. Recetas Tabulares
        </button>
        <button
          className={`tab-btn ${activeTab === "figures" ? "active" : ""}`}
          onClick={() => setActiveTab("figures")}
        >
          3. Figuras Científicas
        </button>
        <button
          className={`tab-btn ${activeTab === "citations" ? "active" : ""}`}
          onClick={() => setActiveTab("citations")}
        >
          4. Citas IEEE y Evidencia
        </button>
        <button
          className={`tab-btn ${activeTab === "export" ? "active" : ""}`}
          onClick={() => setActiveTab("export")}
        >
          5. Exportación Word (.docx)
        </button>
      </div>

      {/* PESTAÑA 1: DATASETS */}
      {activeTab === "datasets" && (
        <div className="tab-content datasets-view">
          {canWrite && <div className="dataset-upload-card">
            <h3>Subir Nuevo Dataset de Investigación</h3>
            <p className="field-hint">
              Admite archivos estructurados (.csv, .xlsx) con datos experimentales o encuestas. Se preservan versiones inmutables y hashes SHA-256.
            </p>
            <form onSubmit={handleUploadDataset} className="form-grid">
              <div className="form-group">
                <label>Nombre del Dataset:</label>
                <input
                  type="text"
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  placeholder="Ej: Resultados_Experimento_Algoritmo_A"
                  required
                />
              </div>
              <div className="form-group">
                <label>Descripción:</label>
                <input
                  type="text"
                  value={datasetDesc}
                  onChange={(e) => setDatasetDesc(e.target.value)}
                  placeholder="Muestra de 100 ejecuciones con tiempos y consumo"
                />
              </div>
              <div className="form-group">
                <label>Archivo (.csv, .xlsx):</label>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={(e) => setDatasetFile(e.target.files?.[0] || null)}
                  required
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? "Subiendo..." : "Registrar Dataset"}
                </button>
              </div>
            </form>
          </div>}

          <div className="datasets-browser-grid">
            <div className="datasets-sidebar">
              <h4>Datasets Registrados ({datasets.length})</h4>
              {datasets.length === 0 ? (
                <p className="empty-hint">No hay datasets registrados en este proyecto.</p>
              ) : (
                <div className="datasets-list">
                  {datasets.map((d) => (
                    <div
                      key={d.dataset_id}
                      className={`dataset-item ${selectedDataset?.dataset_id === d.dataset_id ? "selected" : ""}`}
                      onClick={() => {
                        setSelectedDataset(d)
                        datasetVersionRequestRef.current += 1
                        recipeVersionRequestRef.current += 1
                        setDatasetVersions([])
                        setTableRecipes([])
                        setSelectedRecipe(null)
                        setRecipeVersions([])
                        setFigures([])
                        setSelectedFigure(null)
                        setFigureVersions([])
                        setNewRecipeSpec("")
                        setNewFigureSpec("")
                        void loadDatasetVersions(d.dataset_id)
                      }}
                    >
                      <strong>{d.name}</strong>
                      <small>v{d.current_version_no} · {new Date(d.created_at).toLocaleDateString()}</small>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="dataset-detail-panel">
              {selectedDataset ? (
                <div>
                  <h4>{selectedDataset.name}</h4>
                  <p>{selectedDataset.description || "Sin descripción."}</p>

                  <h5>Historial de Versiones:</h5>
                  {datasetVersions.length === 0 ? (
                    <p className="empty-hint">Cargando versiones...</p>
                  ) : (
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Versión</th>
                          <th>Archivo</th>
                          <th>Filas</th>
                          <th>Columnas</th>
                          <th>Hash SHA-256</th>
                          <th>Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {datasetVersions.map((v) => (
                          <tr key={v.version_no}>
                            <td><strong>v{v.version_no}</strong></td>
                            <td>{v.original_filename}</td>
                            <td>{v.row_count}</td>
                            <td>
                              <span title={v.column_names.join(", ")}>
                                {v.column_names.length} columnas
                              </span>
                            </td>
                            <td><code>{v.file_sha256.slice(0, 10)}...</code></td>
                            <td>
                              <button
                                className="btn-secondary btn-sm"
                                onClick={() => handleDownloadDataset(selectedDataset.dataset_id, v.version_no)}
                              >
                                Descargar
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              ) : (
                <p className="empty-hint">Selecciona un dataset de la lista izquierda.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* PESTAÑA 2: RECETAS TABULARES */}
      {activeTab === "tables" && (
        <div className="tab-content tables-view">
          {canWrite && <div className="recipe-creation-card">
            <h3>Definir Receta Tabular Declarativa</h3>
            <p className="field-hint">
              Crea tablas con columnas, filtros, orden y límite de filas. El backend no calcula agregaciones.
            </p>
            <div className="form-grid">
              <div className="form-group">
                <label>Nombre de la Receta:</label>
                <input
                  type="text"
                  value={newRecipeName}
                  onChange={(e) => setNewRecipeName(e.target.value)}
                  placeholder="Ej: Tabla_Comparativa_Métricas"
                />
              </div>
              <div className="form-group">
                <label>Especificación de Receta (JSON):</label>
                <textarea
                  rows={4}
                  value={newRecipeSpec}
                  onChange={(e) => setNewRecipeSpec(e.target.value)}
                  placeholder="Selecciona un dataset para cargar sus columnas reales."
                />
              </div>
              <div className="form-actions">
                <button
                  className="btn-primary"
                  onClick={handleCreateTableRecipe}
                  disabled={loading || !selectedDataset || !newRecipeSpec}
                >
                  {loading ? "Generando..." : "Crear Receta Tabular"}
                </button>
              </div>
              {!newRecipeSpec && selectedDataset && (
                <p className="field-hint">El dataset necesita columnas y al menos una fila para crear una receta.</p>
              )}
            </div>
          </div>}

          <div className="tables-browser-grid">
            <div className="tables-sidebar">
              <h4>Recetas en este Dataset ({tableRecipes.length})</h4>
              {tableRecipes.length === 0 ? (
                <p className="empty-hint">No hay recetas tabulares para este dataset.</p>
              ) : (
                <div className="recipes-list">
                  {tableRecipes.map((r) => (
                    <div
                      key={r.recipe_id}
                      className={`recipe-item ${selectedRecipe?.recipe_id === r.recipe_id ? "selected" : ""}`}
                      onClick={() => {
                        setSelectedRecipe(r)
                        recipeVersionRequestRef.current += 1
                        setRecipeVersions([])
                        setFigures([])
                        setSelectedFigure(null)
                        setFigureVersions([])
                        setNewFigureSpec("")
                        if (selectedDataset) void loadTableRecipeVersions(selectedDataset.dataset_id, r.recipe_id)
                      }}
                    >
                      <strong>{r.name}</strong>
                      <small>v{r.current_version_no}</small>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="table-detail-panel">
              {selectedRecipe && recipeVersions.length > 0 ? (
                <div>
                  {(() => {
                    const latest = recipeVersions[recipeVersions.length - 1]
                    return (
                      <div>
                        <div className="table-header-row">
                          <h4>{latest.name} (v{latest.version_no})</h4>
                          <span className="badge badge-info">{latest.row_count} filas {latest.truncated ? "(truncadas)" : ""}</span>
                        </div>

                        <div className="table-preview-box">
                          <table className="data-table">
                            <thead>
                              <tr>
                                {latest.result_columns.map((col) => (
                                  <th key={col}>{col}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {latest.rows.slice(0, 15).map((row, idx) => (
                                <tr key={idx}>
                                  {latest.result_columns.map((col) => (
                                    <td key={col}>{String(row[col] ?? "")}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {latest.rows.length > 15 && (
                            <small className="truncated-note">Mostrando 15 de {latest.row_count} filas.</small>
                          )}
                        </div>

                        <div className="artifact-embed-card">
                          <h5>Código de Bloque para Editor de Capítulos (Schema v2):</h5>
                          <pre className="code-block">
{JSON.stringify(
  {
    type: "data_table",
    id: generateUuid(),
    table_version_id: latest.version_id,
    result_sha256: latest.result_sha256,
    caption: `Tabla 1. ${latest.name}`,
  },
  null,
  2,
)}
                          </pre>
                        </div>
                      </div>
                    )
                  })()}
                </div>
              ) : (
                <p className="empty-hint">Selecciona una receta tabular para ver su contenido.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* PESTAÑA 3: FIGURAS CIENTÍFICAS */}
      {activeTab === "figures" && (
        <div className="tab-content figures-view">
          {canWrite && <div className="figure-creation-card">
            <h3>Generar Figura Científica</h3>
            <p className="field-hint">
              Crea visualizaciones (barras, líneas, etc.) a partir de una receta tabular. El backend genera un archivo PNG inmutable con hash SHA-256 verificado.
            </p>
            <div className="form-grid">
              <div className="form-group">
                <label>Título de la Figura:</label>
                <input
                  type="text"
                  value={newFigureName}
                  onChange={(e) => setNewFigureName(e.target.value)}
                  placeholder="Ej: Comparativa_Tiempos_Ejecucion"
                />
              </div>
              <div className="form-group">
                <label>Especificación Visual (JSON):</label>
                <textarea
                  rows={4}
                  value={newFigureSpec}
                  onChange={(e) => setNewFigureSpec(e.target.value)}
                  placeholder="Selecciona una receta con filas y una columna numérica para generar una propuesta válida."
                />
              </div>
              {recipeVersions[recipeVersions.length - 1]?.truncated && (
                <label className="field-hint">
                  <input type="checkbox" checked={acceptTruncatedInput} onChange={(e) => setAcceptTruncatedInput(e.target.checked)} />
                  Acepto que la figura use una tabla truncada.
                </label>
              )}
              {!newFigureSpec && selectedRecipe && (
                <p className="field-hint">La tabla necesita filas y una columna numérica; para barras admite hasta 30 filas. Ajusta la receta si es necesario.</p>
              )}
              <div className="form-actions">
                <button
                  className="btn-primary"
                  onClick={handleCreateFigure}
                  disabled={loading || !selectedRecipe || !newFigureSpec || (recipeVersions[recipeVersions.length - 1]?.truncated && !acceptTruncatedInput)}
                >
                  {loading ? "Generando..." : "Crear Figura"}
                </button>
              </div>
            </div>
          </div>}

          <div className="figures-browser-grid">
            <div className="figures-sidebar">
              <h4>Figuras ({figures.length})</h4>
              {figures.length === 0 ? (
                <p className="empty-hint">No hay figuras generadas para esta receta.</p>
              ) : (
                <div className="figures-list">
                  {figures.map((f) => (
                    <div
                      key={f.figure_id}
                      className={`figure-item ${selectedFigure?.figure_id === f.figure_id ? "selected" : ""}`}
                      onClick={() => {
                        setSelectedFigure(f)
                        if (selectedDataset) loadFigureVersions(selectedDataset.dataset_id, f.figure_id)
                      }}
                    >
                      <strong>{f.name}</strong>
                      <small>v{f.current_version_no}</small>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="figure-detail-panel">
              {selectedFigure && figureVersions.length > 0 && selectedDataset ? (
                <div>
                  {(() => {
                    const latest = figureVersions[figureVersions.length - 1]
                    const previewUrl = getFigurePreviewUrl(
                      projectId,
                      selectedDataset.dataset_id,
                      selectedFigure.figure_id,
                      latest.version_no,
                    )
                    return (
                      <div>
                        <h4>{latest.name} (v{latest.version_no})</h4>
                        <div className="figure-preview-box">
                          <img
                            src={previewUrl}
                            alt={latest.name}
                            className="figure-img-preview"
                            onError={(e) => {
                              // If preview fails, show placeholder
                              ;(e.target as HTMLElement).style.display = "none"
                            }}
                          />
                        </div>
                        <div className="figure-meta">
                          <span>Dimensiones: {latest.image_width_px} × {latest.image_height_px} px</span>
                          <span>Hash: <code>{latest.output_sha256.slice(0, 16)}...</code></span>
                        </div>

                        <div className="artifact-embed-card">
                          <h5>Código de Bloque para Editor (Schema v2):</h5>
                          <pre className="code-block">
{JSON.stringify(
  {
    type: "figure",
    id: generateUuid(),
    figure_version_id: latest.version_id,
    output_sha256: latest.output_sha256,
    caption: `Figura 1. ${latest.name}`,
  },
  null,
  2,
)}
                          </pre>
                        </div>
                      </div>
                    )
                  })()}
                </div>
              ) : (
                <p className="empty-hint">Selecciona una figura para ver su previsualización.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* PESTAÑA 4: CITAS IEEE Y EVIDENCIA */}
      {activeTab === "citations" && (
        <div className="tab-content citations-view">
          <div className="citations-header-card">
            <div className="chapter-selector-row">
              <label htmlFor="chap-select">Seleccionar Capítulo para Vista IEEE:</label>
              <select
                id="chap-select"
                value={selectedChapterNo}
                onChange={(e) => setSelectedChapterNo(Number(e.target.value))}
              >
                {[1, 2, 3, 4, 5, 6, 7].map((num) => (
                  <option key={num} value={num}>
                    Capítulo {num}
                  </option>
                ))}
              </select>
              <button
                className="btn-secondary btn-sm"
                onClick={() => loadIeeeCitations(selectedChapterNo)}
              >
                Actualizar Vista
              </button>
            </div>
            {ieeeView?.notice && (
              <p className="institutional-notice">
                ℹ <em>{ieeeView.notice}</em>
              </p>
            )}
          </div>

          <div className="citations-body-grid">
            <div className="references-panel">
              <h4>Referencias Numeradas IEEE ({ieeeView?.references.length ?? 0})</h4>
              {!ieeeView || ieeeView.references.length === 0 ? (
                <p className="empty-hint">No hay referencias registradas en este capítulo.</p>
              ) : (
                <div className="references-list">
                  {ieeeView.references.map((ref) => (
                    <div key={ref.number} className="reference-item">
                      <div className="ref-header">
                        <strong className="ref-number">[{ref.number}]</strong>
                        <span
                          className={`badge badge-sm ${
                            ref.status === "METADATA_COMPLETE" ? "badge-success" : "badge-warning"
                          }`}
                        >
                          {ref.status === "METADATA_COMPLETE" ? "Metadatos Completos" : "Metadatos Incompletos"}
                        </span>
                      </div>
                      <p className="ref-text">{ref.ieee_text}</p>
                      {ref.missing_fields.length > 0 && (
                        <p className="missing-fields-note">
                          Campos pendientes para norma institucional: {ref.missing_fields.join(", ")}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="occurrences-panel">
              <h4>Marcas de Citas en el Texto ({ieeeView?.marks.length ?? 0})</h4>
              {!ieeeView || ieeeView.marks.length === 0 ? (
                <p className="empty-hint">No hay anclas de citas en los párrafos de este capítulo.</p>
              ) : (
                <div className="marks-list">
                  {ieeeView.marks.map((mark, idx) => (
                    <div key={idx} className="mark-item">
                      <div className="mark-header">
                        <strong>Cita {mark.citation_text}</strong>
                        <small>Bloque: <code>{mark.block_id.slice(0, 8)}</code> · Posición: {mark.position}</small>
                      </div>
                      {mark.occurrence_ids.map((occurrenceId, sourceIndex) => (
                        <button
                          key={occurrenceId}
                          className="btn-secondary btn-sm"
                          type="button"
                          onClick={() => void loadOccurrenceEvidence(occurrenceId)}
                        >
                          Auditar evidencia [{mark.numbers[sourceIndex]}]
                        </button>
                      ))}
                    </div>
                  ))}
                </div>
              )}

              {selectedOccurrenceId && ieeeView && (loadingEvidence
                ? <p className="empty-hint">Consultando evidencia…</p>
                : <CitationReviewPanel key={selectedOccurrenceId} projectId={projectId} chapterNo={selectedChapterNo}
                    occurrenceId={selectedOccurrenceId} ieeeView={ieeeView} reviews={evidenceList}
                    canWrite={canWrite} canReview={!canWrite} csrfToken={csrfToken}
                    onEvidenceChanged={() => refreshOccurrenceEvidence(selectedOccurrenceId)}
                    onCitationChanged={() => loadIeeeCitations(selectedChapterNo)} />)}
            </div>
          </div>
        </div>
      )}

      {/* PESTAÑA 5: EXPORTACIÓN WORD (.DOCX) */}
      {activeTab === "export" && (
        <div className="tab-content export-view">
          <div className="export-cards-grid">
            <div className="export-card draft-card">
              <div className="card-badge">Borrador General</div>
              <h3>Descargar Manuscrito Completo (.docx)</h3>
              <p>
                Genera un documento Word editable que compila las revisiones guardadas de todos los pasos recorridos en la tesis.
              </p>
              <ul className="spec-list">
                <li>Formato institucional UTP / IEEE</li>
                <li>Tipografía Arial 11 pt, espaciado doble (2.0)</li>
                <li>Márgenes normativos: Izquierdo 3 cm, Inferior 3 cm, Superior 2.5 cm, Derecho 2.5 cm</li>
                <li>Encabezados estructurados por capítulo y títulos de pasos</li>
                <li>Tablas y figuras incrustadas desde artefactos v2</li>
              </ul>
              <button
                className="btn-primary btn-large"
                onClick={handleExportDraft}
                disabled={loading}
              >
                {loading ? "Generando documento..." : "Descargar Borrador Completo (.docx)"}
              </button>
            </div>

            <div className="export-card approved-card">
              <div className="card-badge approved-badge">Capítulo Aprobado</div>
              <h3>Descargar Capítulo Aprobado por Asesor (.docx)</h3>
              <p>
                Exporta el snapshot exacto congelado que fue aprobado formalmente por el asesor en la revisión académica.
              </p>
              <div className="form-group">
                <label>Seleccionar Capítulo:</label>
                <select
                  value={selectedChapterNo}
                  onChange={(e) => setSelectedChapterNo(Number(e.target.value))}
                >
                  {[1, 2, 3, 4, 5, 6, 7].map((num) => (
                    <option key={num} value={num}>
                      Capítulo {num}
                    </option>
                  ))}
                </select>
              </div>
              <p className="card-notice">
                ℹ <em>Solo disponible para capítulos que cuenten con un snapshot en estado <strong>APPROVED</strong>. Los borradores en curso deben descargarse mediante la opción de borrador general.</em>
              </p>
              <button
                className="btn-success btn-large"
                onClick={handleExportApprovedChapter}
                disabled={loading}
              >
                {loading ? "Descargando..." : `Descargar Capítulo ${selectedChapterNo} Aprobado (.docx)`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
