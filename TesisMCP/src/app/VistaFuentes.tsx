import { useCallback, useEffect, useMemo, useState } from "react"
import { ApiError } from "../api/client"
import {
  getDocumentJob,
  indexSourcePassages,
  listSourceExcerpts,
  listSourceSegments,
  listSources,
  uploadSource,
} from "../api/sources"
import type {
  DocumentJob,
  ProjectSummary,
  SourceDocument,
  SourceExcerpt,
  SourceSegment,
} from "../api/types"
import { Button, Icon, StatusBadge } from "./base"
import { etiquetaVerificacion } from "./VistaEditor"
import { PanelImportar } from "./fuentes/PanelImportar"
import { PanelPasajes } from "./fuentes/PanelPasajes"
import { ZoteroPanel } from "./fuentes/ZoteroPanel"

function etiquetaProcedencia(f: SourceDocument): string {
  if (f.kind === "UPLOAD") return f.original_filename ? `Carga local · ${f.original_filename}` : "Carga local"
  if (f.record_provider) return `Registro externo · ${f.record_provider}`
  return "Registro externo"
}

export function VistaFuentes({
  proyecto,
  csrfToken,
  onUnauthorized,
  onAccessLost,
}: {
  proyecto: ProjectSummary
  csrfToken: string
  onUnauthorized: () => void
  onAccessLost: () => void
}) {
  const [fuentes, setFuentes] = useState<SourceDocument[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [filtro, setFiltro] = useState("")
  const [seleccionada, setSeleccionada] = useState<SourceDocument | null>(null)
  const [extractos, setExtractos] = useState<SourceExcerpt[] | null>(null)
  const [segmentos, setSegmentos] = useState<SourceSegment[] | null>(null)
  const [cargandoExtractos, setCargandoExtractos] = useState(false)
  const [activeJob, setActiveJob] = useState<DocumentJob | null>(null)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadLabel, setUploadLabel] = useState("")
  const [subiendo, setSubiendo] = useState(false)
  const [indexando, setIndexando] = useState(false)
  const [indexJob, setIndexJob] = useState<DocumentJob | null>(null)
  const esPropietario = proyecto.role === "OWNER"
  // Regla literal del backend (document_jobs.py:51): INDEX exige TEXT_CHECKED.
  const indexJobPermitida = seleccionada?.verification_status === "TEXT_CHECKED"

  const recargar = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const lista = await listSources(proyecto.project_id)
      setFuentes(lista)
      setSeleccionada((prev) => (prev ? (lista.find((f) => f.source_id === prev.source_id) ?? null) : null))
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
      else if (cause instanceof ApiError && cause.status === 404) onAccessLost()
      setFuentes(null)
      setError(cause instanceof Error ? cause.message : "No se pudo cargar la biblioteca del proyecto.")
    } finally {
      setLoading(false)
    }
  }, [proyecto.project_id, onUnauthorized, onAccessLost])

  useEffect(() => {
    void recargar()
  }, [recargar])

  // Sondeo honesto del trabajo de extracción (igual que la biblioteca de respaldo).
  useEffect(() => {
    if (!activeJob || activeJob.status === "SUCCEEDED" || activeJob.status === "FAILED") return
    const timer = setInterval(async () => {
      try {
        const updated = await getDocumentJob(proyecto.project_id, activeJob.job_id)
        setActiveJob(updated)
        if (updated.status === "SUCCEEDED") {
          setNotice("Extracción del documento completada con éxito.")
          void recargar()
        } else if (updated.status === "FAILED") {
          setError(`Fallo en el trabajo de extracción: ${updated.error_message || updated.error_code || "Error desconocido"}`)
        }
      } catch {
        /* error transitorio de sondeo */
      }
    }, 2500)
    return () => clearInterval(timer)
  }, [activeJob, proyecto.project_id, recargar])

  // Sondeo del trabajo de indexación de pasajes (kind INDEX).
  useEffect(() => {
    if (!indexJob || indexJob.status === "SUCCEEDED" || indexJob.status === "FAILED") return
    const timer = setInterval(async () => {
      try {
        const updated = await getDocumentJob(proyecto.project_id, indexJob.job_id)
        setIndexJob(updated)
        if (updated.status === "SUCCEEDED") {
          setNotice("Indexación de pasajes completada: los pasajes ya son consultables.")
          void recargar()
        } else if (updated.status === "FAILED") {
          setError(`Fallo en la indexación: ${updated.error_message || updated.error_code || "Error desconocido"}`)
        }
      } catch {
        /* error transitorio de sondeo */
      }
    }, 2500)
    return () => clearInterval(timer)
  }, [indexJob, proyecto.project_id, recargar])

  const visibles = useMemo(() => {
    const lista = fuentes ?? []
    const t = filtro.trim().toLowerCase()
    if (!t) return lista
    return lista.filter((f) => {
      const campos = [
        f.title,
        f.display_label,
        f.authors?.join(" "),
        f.publication_year !== null ? String(f.publication_year) : "",
        f.doi,
        f.publication_venue,
        f.record_provider,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
      return campos.includes(t)
    })
  }, [fuentes, filtro])

  const resumen = useMemo(() => {
    const conteo = new Map<SourceDocument["verification_status"], number>()
    for (const f of fuentes ?? []) {
      conteo.set(f.verification_status, (conteo.get(f.verification_status) ?? 0) + 1)
    }
    return Array.from(conteo.entries())
  }, [fuentes])

  async function abrir(f: SourceDocument) {
    setSeleccionada(f)
    setExtractos(null)
    setSegmentos(null)
    setCargandoExtractos(true)
    try {
      const [exRes, segRes] = await Promise.all([
        listSourceExcerpts(proyecto.project_id, f.source_id, 1, 50).catch(() => ({ source: f, excerpts: [] })),
        listSourceSegments(proyecto.project_id, f.source_id, 0, 50).catch(() => ({ source: f, segments: [] })),
      ])
      setExtractos(exRes.excerpts)
      setSegmentos(segRes.segments)
    } finally {
      setCargandoExtractos(false)
    }
  }

  async function indexarPasajes() {
    const f = seleccionada
    if (!f || indexando || !esPropietario) return
    setIndexando(true)
    setError(null)
    setNotice(null)
    try {
      const job = await indexSourcePassages(proyecto.project_id, f.source_id, csrfToken)
      setIndexJob(job)
      setNotice("Indexación de pasajes en cola (trabajo del backend).")
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
      } else {
        setError(cause instanceof Error ? cause.message : "No se pudo encolar la indexación.")
      }
    } finally {
      setIndexando(false)
    }
  }

  async function subir(evento: React.FormEvent) {
    evento.preventDefault()
    if (!uploadFile) return
    const label = uploadLabel.trim() || uploadFile.name
    setSubiendo(true)
    setError(null)
    setNotice(null)
    try {
      const res = await uploadSource(proyecto.project_id, label, uploadFile, csrfToken)
      setNotice(`Archivo subido correctamente (${etiquetaVerificacion(res.verification_status)}).`)
      setUploadFile(null)
      setUploadLabel("")
      if (res.job) setActiveJob(res.job)
      void recargar()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Error al subir el documento.")
    } finally {
      setSubiendo(false)
    }
  }

  if (loading && fuentes === null) {
    return (
      <main className="page">
        <div className="estado-pantalla" role="status">Cargando la biblioteca del proyecto…</div>
      </main>
    )
  }

  return (
    <main className="page library-page">
      {resumen.length > 0 ? (
        <div className="library-summary">
          <span className="eyebrow blue">RESUMEN DE LA BIBLIOTECA</span>
          <span>
            {visibles.length === (fuentes ?? []).length
              ? `${(fuentes ?? []).length} fuente${(fuentes ?? []).length === 1 ? "" : "s"}`
              : `${visibles.length} de ${(fuentes ?? []).length} fuentes`}{" "}
            en el proyecto.{" "}
            {resumen
              .map(([estado, n]) => `${etiquetaVerificacion(estado)}: ${n}`)
              .join(" · ")}
          </span>
        </div>
      ) : (
        <div className="library-summary">
          <span className="eyebrow blue">RESUMEN DE LA BIBLIOTECA</span>
          <span>El proyecto aún no tiene fuentes cargadas.</span>
        </div>
      )}

      <div className="page-heading">
        <div>
          <h1>Biblioteca científica</h1>
          <p>Busca, verifica y organiza las fuentes de tu investigación.</p>
        </div>
      </div>

      {error && <div className="aviso aviso-error" role="alert">{error}</div>}
      {notice && <div className="aviso" role="status">{notice}</div>}

      <ZoteroPanel
        projectId={proyecto.project_id}
        csrfToken={csrfToken}
        puedeImportar={esPropietario}
        onUnauthorized={onUnauthorized}
        onAccessLost={onAccessLost}
        alImportar={recargar}
      />

      <PanelImportar
        projectId={proyecto.project_id}
        csrfToken={csrfToken}
        puedeImportar={esPropietario}
        onUnauthorized={onUnauthorized}
        alImportar={recargar}
      />

      <form className="search-box" onSubmit={(e) => e.preventDefault()}>
        <Icon name="library" size={16} />
        <input
          placeholder="Filtrar por título, autor, DOI, publicación o procedencia"
          value={filtro}
          onChange={(e) => setFiltro(e.target.value)}
        />
        {filtro && (
          <button className="text-link" onClick={() => setFiltro("")}>Limpiar filtro</button>
        )}
      </form>

      <form className="upload-box" onSubmit={subir}>
        <label>
          Etiqueta (opcional)
          <input
            value={uploadLabel}
            onChange={(e) => setUploadLabel(e.target.value)}
            placeholder="Etiqueta visible de la fuente"
          />
        </label>
        <label>
          Documento (PDF)
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
          />
        </label>
        <Button icon="download" disabled={subiendo || !uploadFile}>
          {subiendo ? "Subiendo…" : "Subir PDF"}
        </Button>
        {activeJob && activeJob.status !== "SUCCEEDED" && activeJob.status !== "FAILED" && (
          <span className="version-sha" role="status">
            Procesamiento: {activeJob.status} (intentos {activeJob.attempts})
          </span>
        )}
      </form>

      <div className="library-layout">
        <section className="results-panel">
          <div className="results-head">
            <div>
              <h2>Fuentes del proyecto</h2>
              <p>Estados de verificación y localizadores reales del backend</p>
            </div>
          </div>
          {visibles.length === 0 ? (
            <p className="aviso">
              {fuentes && fuentes.length > 0
                ? "Ninguna fuente coincide con el filtro."
                : "Sube un PDF o importa un registro externo para empezar."}
            </p>
          ) : (
            <div className="source-table">
              <div className="table-head">
                <span>Título y autoría</span>
                <span>Año</span>
                <span>Procedencia</span>
                <span>Verificación</span>
              </div>
              {visibles.map((f) => (
                <button
                  className={`table-row ${seleccionada?.source_id === f.source_id ? "selected" : ""}`}
                  key={f.source_id}
                  onClick={() => void abrir(f)}
                >
                  <div>
                    <b>{f.title || f.display_label}</b>
                    <small>
                      {f.authors && f.authors.length > 0
                        ? f.authors.join(", ")
                        : "Autoría no verificada contra portada"}
                    </small>
                  </div>
                  <span>{f.publication_year ?? "—"}</span>
                  <div>
                    <b>{f.kind === "UPLOAD" ? "Carga local" : f.record_provider || "Registro externo"}</b>
                    <small>{f.metadata_origin}</small>
                  </div>
                  <StatusBadge>{etiquetaVerificacion(f.verification_status)}</StatusBadge>
                </button>
              ))}
            </div>
          )}
        </section>
        <aside className="preview-panel">
          <div className="preview-head">
            <div>
              <span className="pdf-icon">PDF</span>
              <div>
                <b>Vista previa</b>
                <small>
                  {seleccionada
                    ? seleccionada.title || seleccionada.display_label
                    : "Selecciona una fuente de la lista"}
                </small>
              </div>
            </div>
          </div>
          {seleccionada ? (
            <div className="source-detail">
              <dl>
                {seleccionada.doi && <div><dt>DOI</dt><dd><code>{seleccionada.doi}</code></dd></div>}
                {seleccionada.publication_venue && <div><dt>Publicación</dt><dd>{seleccionada.publication_venue}</dd></div>}
                {seleccionada.publication_year !== null && <div><dt>Año</dt><dd>{seleccionada.publication_year}</dd></div>}
                <div>
                  <dt>Título verificado contra portada</dt>
                  <dd>{seleccionada.title_verified_against_cover ? "Sí" : "No"}</dd>
                </div>
                {seleccionada.physical_page_count !== null && (
                  <div><dt>Páginas físicas</dt><dd>{seleccionada.physical_page_count}</dd></div>
                )}
                <div><dt>Extractos indexados</dt><dd>{seleccionada.excerpt_count}</dd></div>
                <div><dt>Segmentos</dt><dd>{seleccionada.segment_count}</dd></div>
                {seleccionada.record_url && (
                  <div>
                    <dt>Registro</dt>
                    <dd>
                      <a href={seleccionada.landing_page_url || seleccionada.record_url} target="_blank" rel="noreferrer">
                        Abrir página de la fuente
                      </a>
                    </dd>
                  </div>
                )}
              </dl>

              <div className="fragment">
                <span className="eyebrow">INDEXACIÓN Y EXTRACCIÓN</span>
                {esPropietario ? (
                  <Button
                    variant="secondary"
                    disabled={indexando || !indexJobPermitida}
                    title={
                      indexJobPermitida
                        ? "Encola la indexación de pasajes de esta fuente (trabajo del backend)"
                        : "La indexación exige texto completo verificado (TEXT_CHECKED) en el backend"
                    }
                    onClick={() => void indexarPasajes()}
                  >
                    {indexando ? "Encolando…" : "Indexar pasajes"}
                  </Button>
                ) : (
                  <small className="version-sha">
                    La indexación y las acciones de procesamiento son del tesista propietario.
                  </small>
                )}
                {indexJob && indexJob.status !== "SUCCEEDED" && indexJob.status !== "FAILED" && (
                  <small className="version-sha" role="status">
                    Indexación: {indexJob.status} (intentos {indexJob.attempts})
                  </small>
                )}
              </div>

              <div className="fragment">
                <span className="eyebrow">EXTRACTOS CON LOCALIZADOR FÍSICO</span>
                {cargandoExtractos ? (
                  <p className="aviso" role="status">Cargando extractos…</p>
                ) : extractos === null || extractos.length === 0 ? (
                  <p className="aviso">
                    {seleccionada.verification_status === "OCR_REQUIRED"
                      ? "Este documento requiere OCR: el backend no extrajo texto digital todavía."
                      : seleccionada.verification_status === "PENDING_EXTRACTION"
                        ? "La extracción de texto está pendiente en el backend."
                        : seleccionada.verification_status === "METADATA_CHECKED"
                          ? "Solo hay metadatos verificados: no hay texto completo cargado."
                          : "Sin extractos registrados todavía."}
                  </p>
                ) : (
                  extractos.map((e) => (
                    <blockquote key={e.excerpt_id}>
                      <span className="version-sha">Página física {e.physical_page}</span>
                      <p>«{e.text}»</p>
                      <span className="version-sha">SHA {e.text_sha256.slice(0, 12)}…</span>
                    </blockquote>
                  ))
                )}
                {segmentos && segmentos.length > 0 && (
                  <details>
                    <summary className="version-sha">
                      Ver {segmentos.length} segmentos estructurados del documento
                    </summary>
                    {segmentos.map((s) => (
                      <div key={s.segment_id}>
                        <b className="version-sha">#{s.sequence_no} · {s.heading || s.kind}</b>
                        <p>«{s.text}»</p>
                      </div>
                    ))}
                  </details>
                )}
              </div>
            </div>
          ) : (
            <div className="fragment">
              <p>
                La ubicación y el pasaje aparecen aquí únicamente de fuentes
                reales del proyecto.
              </p>
            </div>
          )}
        </aside>
      </div>

      <PanelPasajes
        projectId={proyecto.project_id}
        csrfToken={csrfToken}
        onUnauthorized={onUnauthorized}
      />
    </main>
  )
}
