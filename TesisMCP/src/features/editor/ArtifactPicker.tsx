import { useEffect, useState } from "react"
import {
  listDatasets, listDatasetVersions, listTableRecipes, listTableRecipeVersions,
  listFigures, listFigureVersions,
} from "../../api/research"
import type {
  ResearchDataset, ResearchDatasetVersion, TableRecipe, TableRecipeVersion,
  ResearchFigure, ResearchFigureVersion,
} from "../../api/types"

export type ArtifactChoice =
  | { type: "data_table"; version: TableRecipeVersion; caption: string }
  | { type: "figure"; version: ResearchFigureVersion; caption: string }

type Props = {
  projectId: string
  type: "data_table" | "figure"
  onSelect: (choice: ArtifactChoice) => void
  onCancel: () => void
}

export default function ArtifactPicker({ projectId, type, onSelect, onCancel }: Props) {
  const [datasets, setDatasets] = useState<ResearchDataset[]>([])
  const [datasetId, setDatasetId] = useState("")
  const [datasetVersions, setDatasetVersions] = useState<ResearchDatasetVersion[]>([])
  const [datasetVersionNo, setDatasetVersionNo] = useState(0)
  const [recipes, setRecipes] = useState<TableRecipe[]>([])
  const [recipeId, setRecipeId] = useState("")
  const [tableVersions, setTableVersions] = useState<TableRecipeVersion[]>([])
  const [tableVersionId, setTableVersionId] = useState("")
  const [figures, setFigures] = useState<ResearchFigure[]>([])
  const [figureId, setFigureId] = useState("")
  const [figureVersions, setFigureVersions] = useState<ResearchFigureVersion[]>([])
  const [figureVersionId, setFigureVersionId] = useState("")
  const [caption, setCaption] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    listDatasets(projectId).then((items) => {
      if (active) setDatasets(items)
    }).catch((cause) => {
      if (active) setError(cause instanceof Error ? cause.message : "No se pudieron cargar los datasets.")
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [projectId])

  useEffect(() => {
    if (!datasetId) return
    let active = true
    setLoading(true)
    setError(null)
    listDatasetVersions(projectId, datasetId).then((items) => {
      if (active) setDatasetVersions(items)
    }).catch((cause) => {
      if (active) setError(cause instanceof Error ? cause.message : "No se pudieron cargar las versiones del dataset.")
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [projectId, datasetId])

  useEffect(() => {
    if (!datasetId || !datasetVersionNo) return
    let active = true
    setLoading(true)
    setError(null)
    listTableRecipes(projectId, datasetId, datasetVersionNo).then((items) => {
      if (active) setRecipes(items)
    }).catch((cause) => {
      if (active) setError(cause instanceof Error ? cause.message : "No se pudieron cargar las recetas.")
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [projectId, datasetId, datasetVersionNo])

  useEffect(() => {
    if (!datasetId || !recipeId) return
    let active = true
    setLoading(true)
    setError(null)
    listTableRecipeVersions(projectId, datasetId, recipeId).then((items) => {
      if (active) setTableVersions(items.filter((item) => item.dataset_version_no === datasetVersionNo))
    }).catch((cause) => {
      if (active) setError(cause instanceof Error ? cause.message : "No se pudieron cargar las versiones de la tabla.")
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [projectId, datasetId, datasetVersionNo, recipeId])

  const tableVersion = tableVersions.find((item) => item.version_id === tableVersionId)
  useEffect(() => {
    if (type !== "figure" || !datasetId || !recipeId || !tableVersion) return
    let active = true
    setLoading(true)
    setError(null)
    listFigures(projectId, datasetId, recipeId, tableVersion.version_no).then((items) => {
      if (active) setFigures(items)
    }).catch((cause) => {
      if (active) setError(cause instanceof Error ? cause.message : "No se pudieron cargar las figuras.")
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [projectId, datasetId, recipeId, tableVersionId, type])

  useEffect(() => {
    if (type !== "figure" || !datasetId || !figureId) return
    let active = true
    setLoading(true)
    setError(null)
    listFigureVersions(projectId, datasetId, figureId).then((items) => {
      if (active) setFigureVersions(items.filter((item) => item.table_recipe_version_no === tableVersion?.version_no))
    }).catch((cause) => {
      if (active) setError(cause instanceof Error ? cause.message : "No se pudieron cargar las versiones de la figura.")
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [projectId, datasetId, figureId, tableVersionId, type])

  const figureVersion = figureVersions.find((item) => item.version_id === figureVersionId)
  const chosen = type === "data_table" ? tableVersion : figureVersion

  function insert() {
    if (!chosen || !caption.trim() || loading) return
    if (type === "data_table" && tableVersion) onSelect({ type, version: tableVersion, caption: caption.trim() })
    if (type === "figure" && figureVersion) onSelect({ type, version: figureVersion, caption: caption.trim() })
  }

  return <div className="workflow-modal-backdrop" role="presentation" onMouseDown={(event) => {
    if (event.target === event.currentTarget) onCancel()
  }}>
    <section className="workflow-modal-card artifact-picker" role="dialog" aria-modal="true" aria-label={type === "data_table" ? "Elegir tabla" : "Elegir figura"}>
      <h2>{type === "data_table" ? "Insertar tabla" : "Insertar figura"}</h2>
      <p>Elige una versión guardada. El editor tomará su identificador y hash del proyecto.</p>
      {error && <div className="chapter-alert" role="alert">{error}</div>}
      {loading && <p role="status">Cargando versiones…</p>}
      {!loading && datasets.length === 0 && <p>No hay datasets registrados en este proyecto.</p>}
      <label>Dataset
        <select value={datasetId} onChange={(e) => {
          setDatasetId(e.target.value); setDatasetVersionNo(0); setDatasetVersions([])
          setRecipeId(""); setRecipes([]); setTableVersionId(""); setTableVersions([])
          setFigureId(""); setFigures([]); setFigureVersionId(""); setFigureVersions([]); setCaption("")
        }}>
          <option value="">Selecciona un dataset</option>
          {datasets.map((item) => <option key={item.dataset_id} value={item.dataset_id}>{item.name}</option>)}
        </select>
      </label>
      {datasetId && <label>Versión del dataset
        <select value={datasetVersionNo} onChange={(e) => {
          setDatasetVersionNo(Number(e.target.value)); setRecipeId(""); setRecipes([])
          setTableVersionId(""); setTableVersions([]); setFigureId(""); setFigures([])
          setFigureVersionId(""); setFigureVersions([]); setCaption("")
        }}>
          <option value={0}>Selecciona una versión</option>
          {datasetVersions.map((item) => <option key={item.version_id} value={item.version_no}>v{item.version_no} · {item.original_filename}</option>)}
        </select>
      </label>}
      {!!datasetVersionNo && <label>Receta tabular
        <select value={recipeId} onChange={(e) => {
          setRecipeId(e.target.value); setTableVersionId(""); setTableVersions([])
          setFigureId(""); setFigures([]); setFigureVersionId(""); setFigureVersions([]); setCaption("")
        }}>
          <option value="">Selecciona una receta</option>
          {recipes.map((item) => <option key={item.recipe_id} value={item.recipe_id}>{item.name}</option>)}
        </select>
      </label>}
      {recipeId && <label>Versión de la tabla
        <select value={tableVersionId} onChange={(e) => {
          setTableVersionId(e.target.value); setFigureId(""); setFigures([])
          setFigureVersionId(""); setFigureVersions([])
          const item = tableVersions.find((version) => version.version_id === e.target.value)
          setCaption(type === "data_table" && item ? `Tabla. ${item.name}` : "")
        }}>
          <option value="">Selecciona una versión</option>
          {tableVersions.map((item) => <option key={item.version_id} value={item.version_id}>v{item.version_no} · {item.name} · {item.row_count} filas</option>)}
        </select>
      </label>}
      {type === "figure" && tableVersion && <label>Figura
        <select value={figureId} onChange={(e) => {
          setFigureId(e.target.value); setFigureVersionId(""); setFigureVersions([]); setCaption("")
        }}>
          <option value="">Selecciona una figura</option>
          {figures.map((item) => <option key={item.figure_id} value={item.figure_id}>{item.name}</option>)}
        </select>
      </label>}
      {type === "figure" && figureId && <label>Versión de la figura
        <select value={figureVersionId} onChange={(e) => {
          setFigureVersionId(e.target.value)
          const item = figureVersions.find((version) => version.version_id === e.target.value)
          setCaption(item ? `Figura. ${item.name}` : "")
        }}>
          <option value="">Selecciona una versión</option>
          {figureVersions.map((item) => <option key={item.version_id} value={item.version_id}>v{item.version_no} · {item.name}</option>)}
        </select>
      </label>}
      {chosen && <label>Leyenda
        <input value={caption} maxLength={500} onChange={(e) => setCaption(e.target.value)} />
      </label>}
      <div className="modal-actions">
        <button className="button button-secondary" type="button" onClick={onCancel}>Cancelar</button>
        <button className="button button-primary" type="button" disabled={!chosen || !caption.trim() || loading} onClick={insert}>Insertar en el borrador</button>
      </div>
    </section>
  </div>
}
