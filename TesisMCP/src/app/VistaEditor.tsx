import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { ApiError } from "../api/client"
import {
  getChapterDocument,
  getChapterState,
  saveChapterDocument,
  type SaveChapterInput,
} from "../api/chapters"
import { getWorkflowState } from "../api/workflows"
import { getChapterSnapshot, listChapterSnapshots, listComments, resolveComment } from "../api/reviews"
import { listSources } from "../api/sources"
import type {
  ChapterBlock,
  ChapterContentTree,
  ChapterCitation,
  ChapterDocument,
  ChapterSnapshotDetailApi,
  ChapterSnapshotSummaryApi,
  ChapterState,
  ProjectSummary,
  ReviewComment,
  SourceDocument,
} from "../api/types"
import { Button, Icon, StatusBadge } from "./base"
import { draftTextPreview, unsupportedDocumentReason } from "./editorDocument"

type Loaded = { state: ChapterState; document: ChapterDocument }
type ModoDocumento = "draft" | "submitted" | "snapshot"
type SaveCitation = SaveChapterInput["citations"][number]
type PendingSave = SaveChapterInput

const etiquetaPorEstado: Record<string, string> = {
  DRAFT: "Borrador",
  READY: "En revisión",
  CHANGES_REQUESTED: "Con observaciones",
  APPROVED: "Aprobado",
}

function editableCitations(citations: ChapterCitation[] | undefined): SaveCitation[] {
  return (citations ?? []).map(({ group_id, block_id, position, sources }) => ({
    group_id,
    block_id,
    position,
    sources: sources.map(({ source_id, locator }) => ({ source_id, locator })),
  }))
}

function isArtifact(block: ChapterBlock): block is Extract<ChapterBlock, { type: "data_table" | "figure" }> {
  return block.type === "data_table" || block.type === "figure"
}

/** Estado honesto del indicador de guardado (no cosmético: depende de la concurrencia real). */
function estadoGuardado(args: {
  saving: boolean
  dirty: boolean
  pending: PendingSave | null
  writeBlocked: boolean
  serverChanged: boolean
  notice: string | null
}): string {
  if (args.saving) return "Guardando…"
  if (args.pending && args.serverChanged) return "Conflicto: existe una versión posterior"
  if (args.pending) return "Intento pendiente de confirmar"
  if (args.writeBlocked) return "Solo lectura"
  if (args.dirty) return "Cambios sin guardar"
  if (args.notice) return "Confirmado por el servidor"
  return "Sin cambios locales"
}

/**
 * Editor del capítulo con la disposición de tres paneles del demo de Figma
 * (documento · versiones · observaciones) y datos reales de src/api.
 */
export function VistaEditor({
  proyecto,
  csrfToken,
  onUnauthorized,
  onAccessLost,
  onRefreshCsrf,
}: {
  proyecto: ProjectSummary
  csrfToken: string
  onUnauthorized: () => void
  onAccessLost: () => void
  onRefreshCsrf: () => Promise<void>
}) {
  const [numerosCapitulo, setNumerosCapitulo] = useState<number[]>([])
  const [numeroCapitulo, setNumeroCapitulo] = useState<number | null>(null)
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [draft, setDraft] = useState<ChapterContentTree | null>(null)
  const [pending, setPending] = useState<PendingSave | null>(null)
  const [writeBlocked, setWriteBlocked] = useState(false)
  const [serverDocument, setServerDocument] = useState<ChapterDocument | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [snapshots, setSnapshots] = useState<ChapterSnapshotSummaryApi[]>([])
  const [snapshotDetalle, setSnapshotDetalle] = useState<ChapterSnapshotDetailApi | null>(null)
  const [cargandoVersion, setCargandoVersion] = useState(false)
  const [comentarios, setComentarios] = useState<ReviewComment[]>([])
  const [resolviendoId, setResolviendoId] = useState<number | null>(null)
  const [fuentes, setFuentes] = useState<SourceDocument[] | null>(null)
  const [modoDocumento, setModoDocumento] = useState<ModoDocumento>("draft")
  const [leftOpen, setLeftOpen] = useState(true)
  const [rightOpen, setRightOpen] = useState(true)
  const [leftTab, setLeftTab] = useState<"estructura" | "fuentes">("estructura")
  const [rightTab, setRightTab] = useState<"versiones" | "observaciones">("versiones")
  const loadSequence = useRef(0)

  const dirty =
    !!loaded && !!draft && JSON.stringify(draft) !== JSON.stringify(loaded.document.content_tree)
  const hasLocalWork = dirty || pending !== null
  const needsSave =
    dirty ||
    !!loaded?.document.is_stale ||
    (!!loaded && loaded.document.revision_id === null)
  const writable =
    !!loaded &&
    !!draft &&
    !writeBlocked &&
    proyecto.role === "OWNER" &&
    proyecto.permissions.can_edit_document &&
    (loaded.state.status === "DRAFT" || loaded.state.status === "CHANGES_REQUESTED")
  const busy = loading || saving
  const servidorCambio = pending !== null && serverDocument !== null

  // Advertencia de trabajo local sin guardar.
  useEffect(() => {
    if (!hasLocalWork) return
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault()
      event.returnValue = ""
    }
    window.addEventListener("beforeunload", warn)
    return () => window.removeEventListener("beforeunload", warn)
  }, [hasLocalWork])

  // Capítulos con número a partir del recorrido publicado (igual que VistaRevision).
  useEffect(() => {
    let vigente = true
    getWorkflowRecursos(proyecto.project_id).then(({ numeros }) => {
      if (!vigente) return
      setNumerosCapitulo(numeros)
      setNumeroCapitulo(numeros.length > 0 ? numeros[0] : null)
      if (numeros.length === 0) setLoading(false)
    })
    return () => {
      vigente = false
    }
  }, [proyecto.project_id])

  // Fuentes reales para el panel izquierdo (pestaña Fuentes).
  useEffect(() => {
    let vigente = true
    listSources(proyecto.project_id)
      .then((lista) => {
        if (vigente) setFuentes(lista)
      })
      .catch(() => {
        if (vigente) setFuentes(null)
      })
    return () => {
      vigente = false
    }
  }, [proyecto.project_id])

  const cargarComentarios = useCallback(async (capitulo: number) => {
    // El módulo legacy de demo (src/features/) comparte listChapterSnapshots con el
    // contrato antiguo; aquí se ajusta al contrato real del backend sin tocarlo.
    const resumen = (await listChapterSnapshots(proyecto.project_id, capitulo)) as unknown as ChapterSnapshotSummaryApi[]
    const base = await listComments(proyecto.project_id, capitulo)
    const detalle = await Promise.allSettled(
      resumen.map((s) => listComments(proyecto.project_id, capitulo, s.id)),
    )
    const porSnapshot = detalle
      .map((r) => (r.status === "fulfilled" ? (r as PromiseFulfilledResult<ReviewComment[]>).value : []))
      .flat()
    const vistos = new Set(porSnapshot.map((c) => c.comment_id))
    return {
      snapshots: resumen,
      comentarios: [
        ...base.filter((c) => !vistos.has(c.comment_id)),
        ...porSnapshot,
      ],
    }
  }, [proyecto.project_id])

  const cargarCapitulo = useCallback(async (numero: number) => {
    const secuencia = ++loadSequence.current
    setLoading(true)
    setError(null)
    setNotice(null)
    setPending(null)
    setWriteBlocked(false)
    setServerDocument(null)
    setSnapshotDetalle(null)
    setModoDocumento("draft")
    try {
      const [state, document, versiones] = await Promise.all([
        getChapterState(proyecto.project_id, numero),
        getChapterDocument(proyecto.project_id, numero),
        cargarComentarios(numero),
      ])
      if (secuencia !== loadSequence.current) return
      if (state.chapter_no !== numero || document.chapter_no !== numero) {
        throw new Error("El backend respondió con otro capítulo.")
      }
      const incompatible = unsupportedDocumentReason(document)
      setLoaded({ state, document })
      setDraft(incompatible ? null : structuredClone(document.content_tree))
      setSnapshots(versiones.snapshots)
      setComentarios(versiones.comentarios)
      if (incompatible) setError(incompatible)
    } catch (cause) {
      if (secuencia !== loadSequence.current) return
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
      if (cause instanceof ApiError && cause.status === 404) onAccessLost()
      setLoaded(null)
      setDraft(null)
      setError(cause instanceof Error ? cause.message : "No se pudo cargar el capítulo.")
    } finally {
      if (secuencia === loadSequence.current) setLoading(false)
    }
  }, [proyecto.project_id, onUnauthorized, onAccessLost, cargarComentarios])

  useEffect(() => {
    if (numeroCapitulo === null) return
    void cargarCapitulo(numeroCapitulo)
  }, [numeroCapitulo, cargarCapitulo])

  function cambiarCapitulo(numero: number) {
    if (numero === numeroCapitulo) return
    if (
      hasLocalWork &&
      !window.confirm(
        "Hay cambios sin guardar o un guardado pendiente de confirmar. Al cambiar de capítulo se descartará el borrador. ¿Continuar?",
      )
    ) {
      return
    }
    loadSequence.current += 1
    setLoaded(null)
    setDraft(null)
    setNumeroCapitulo(numero)
  }

  function setBloque(blockId: string, update: (block: ChapterBlock) => ChapterBlock) {
    setDraft((tree) =>
      tree
        ? { ...tree, blocks: tree.blocks.map((b) => (b.id === blockId ? update(b) : b)) }
        : tree,
    )
    setPending(null)
    setNotice(null)
  }

  function agregarBloque(type: "heading" | "paragraph" | "blockquote" | "code_block" | "bullet_list" | "ordered_list") {
    if (!draft) return
    const block: ChapterBlock =
      type === "heading"
        ? { type, id: crypto.randomUUID(), level: 2, text: "Nuevo encabezado" }
        : type === "bullet_list" || type === "ordered_list"
          ? { type, id: crypto.randomUUID(), items: ["Nuevo elemento"] }
          : { type, id: crypto.randomUUID(), text: type === "code_block" ? "" : "Nuevo texto" }
    setDraft({ ...draft, blocks: [...draft.blocks, block] })
    setPending(null)
  }

  function quitarBloque(blockId: string) {
    if (!draft) return
    setDraft({ ...draft, blocks: draft.blocks.filter((b) => b.id !== blockId) })
    setPending(null)
  }

  function moverBloque(index: number, delta: -1 | 1) {
    if (!draft) return
    const target = index + delta
    if (target < 0 || target >= draft.blocks.length) return
    const blocks = [...draft.blocks]
    const [item] = blocks.splice(index, 1)
    blocks.splice(target, 0, item)
    setDraft({ ...draft, blocks })
    setPending(null)
  }

  const citasPorBloque = useMemo(() => {
    const map = new Map<string, ChapterCitation[]>()
    for (const cita of loaded?.document.citations ?? []) {
      map.set(cita.block_id, [...(map.get(cita.block_id) ?? []), cita])
    }
    return map
  }, [loaded])

  async function guardar() {
    if (!loaded || !draft || !writable || busy || !needsSave || numeroCapitulo === null) return
    const intento: PendingSave =
      pending ?? {
        content_tree: structuredClone(draft),
        citations: editableCitations(loaded.document.citations),
        expected_version: loaded.document.document_version,
        idempotency_key: crypto.randomUUID(),
      }
    setPending(intento)
    setSaving(true)
    setError(null)
    setNotice(null)
    let confirmado = false
    try {
      const resultado = await saveChapterDocument(
        proyecto.project_id,
        numeroCapitulo,
        intento,
        csrfToken,
      )
      confirmado = true
      const [state, current] = await Promise.all([
        getChapterState(proyecto.project_id, numeroCapitulo),
        getChapterDocument(proyecto.project_id, numeroCapitulo),
      ])
      if (current.revision_id !== resultado.revision_id) {
        setWriteBlocked(true)
        setServerDocument(current)
        setError(
          "El servidor confirmó tu intento, pero existe una versión posterior. Se conserva tu borrador para revisarlo antes de continuar.",
        )
        return
      }
      const incompatible = unsupportedDocumentReason(current)
      if (incompatible) {
        setWriteBlocked(true)
        setError(incompatible)
        return
      }
      setLoaded({ state, document: current })
      setDraft(structuredClone(current.content_tree))
      setPending(null)
      setServerDocument(null)
      setWriteBlocked(state.status !== "DRAFT" && state.status !== "CHANGES_REQUESTED")
      setNotice(
        resultado.idempotent
          ? "El servidor confirmó este intento y su versión vigente."
          : "Cambios guardados y versión vigente comprobada.",
      )
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
        return
      }
      if (cause instanceof ApiError && cause.status === 404) {
        onAccessLost()
        return
      }
      if (confirmado) {
        setWriteBlocked(true)
        setError("El servidor confirmó el guardado, pero no se pudo consultar la versión vigente. Conservamos el intento para revalidarlo.")
      } else if (cause instanceof ApiError && cause.kind === "csrf") {
        try {
          await onRefreshCsrf()
        } catch {
          /* conservar borrador */
        }
        setError("Falló la protección CSRF. El borrador se conserva; vuelve a guardar para reintentar.")
      } else if (cause instanceof ApiError && cause.status === 409) {
        setWriteBlocked(true)
        setError("El documento cambió en el servidor o ya no admite edición. Tu borrador se conserva; recarga solo si deseas descartarlo.")
      } else if (cause instanceof ApiError && cause.kind === "permission") {
        setWriteBlocked(true)
        setError("Ya no tienes permiso para modificar este documento. El borrador se conserva solo en esta página.")
      } else {
        setError(cause instanceof Error ? cause.message : "No se confirmó el guardado. El borrador se conserva.")
      }
    } finally {
      setSaving(false)
    }
  }

  async function consultarVersionVigente() {
    if (!loaded || !draft || busy || numeroCapitulo === null) return
    setLoading(true)
    try {
      const [state, current] = await Promise.all([
        getChapterState(proyecto.project_id, numeroCapitulo),
        getChapterDocument(proyecto.project_id, numeroCapitulo),
      ])
      setServerDocument(current)
      const mismoArbol = JSON.stringify(current.content_tree) === JSON.stringify(draft)
      const mismasCitas =
        JSON.stringify(editableCitations(current.citations)) ===
        JSON.stringify(editableCitations(loaded.document.citations))
      const baseVigente =
        current.revision_id === loaded.document.revision_id &&
        current.document_version === loaded.document.document_version
      if (
        mismoArbol &&
        mismasCitas &&
        (!pending || !baseVigente) &&
        !unsupportedDocumentReason(current)
      ) {
        setLoaded({ state, document: current })
        setDraft(structuredClone(current.content_tree))
        setPending(null)
        setServerDocument(null)
        setWriteBlocked(state.status !== "DRAFT" && state.status !== "CHANGES_REQUESTED")
        setError(null)
        setNotice("El contenido local coincide con la versión vigente del servidor.")
      } else if (baseVigente && (state.status === "DRAFT" || state.status === "CHANGES_REQUESTED")) {
        setWriteBlocked(false)
        setError("El servidor aún muestra la versión anterior. Puedes reintentar el mismo guardado con su clave conservada.")
      } else {
        setWriteBlocked(true)
        setError("La versión vigente difiere de tu borrador. Este sigue local; recarga solo si aceptas descartarlo.")
      }
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
        return
      }
      if (cause instanceof ApiError && cause.status === 404) {
        onAccessLost()
        return
      }
      setError(cause instanceof Error ? cause.message : "No se pudo consultar la versión vigente.")
    } finally {
      setLoading(false)
    }
  }

  async function abrirModo(modo: ModoDocumento, snapshotId?: string) {
    if (modo === modoDocumento && !snapshotId) return
    if (modo === "draft") {
      setModoDocumento("draft")
      setSnapshotDetalle(null)
      setNotice(null)
      setError(null)
      return
    }
    if (!loaded) return
    const objetivo =
      modo === "submitted"
        ? loaded.state.submitted_snapshot_id
        : modo === "snapshot"
          ? (snapshotId ?? null)
          : null
    if (!objetivo) {
      setNotice(
        modo === "submitted"
          ? "Este capítulo aún no tiene una versión enviada al asesor."
          : "Este capítulo aún no tiene versiones guardadas.",
      )
      return
    }
    setCargandoVersion(true)
    setError(null)
    try {
      const detalle = (await getChapterSnapshot(proyecto.project_id, numeroCapitulo as number, objetivo)) as unknown as ChapterSnapshotDetailApi
      setSnapshotDetalle(detalle)
      setModoDocumento(modo)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo cargar la versión.")
    } finally {
      setCargandoVersion(false)
    }
  }

  async function resolver(c: ReviewComment) {
    if (!proyecto.permissions.can_review_chapters || resolviendoId !== null) return
    setResolviendoId(c.comment_id)
    try {
      const actualizado = await resolverComentario(proyecto.project_id, c.comment_id, csrfToken)
      setComentarios((lista) =>
        lista.map((item) => (item.comment_id === actualizado.comment_id ? { ...item, status: actualizado.status } : item)),
      )
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No se pudo resolver la observación.")
    } finally {
      setResolviendoId(null)
    }
  }

  const abiertas = comentarios.filter((c) => c.status === "OPEN").length
  const modoSoloLectura = modoDocumento !== "draft" || !writable
  const estadoGuardadoTexto = estadoGuardado({
    saving,
    dirty,
    pending,
    writeBlocked,
    serverChanged: servidorCambio,
    notice,
  })

  if (numeroCapitulo === null && !loading) {
    return (
      <main className="page">
        <p className="aviso">
          El recorrido publicado del proyecto no asigna capítulos con número, por
          lo que el editor no tiene documentos que abrir.
        </p>
      </main>
    )
  }

  return (
    <main className="editor-page">
      <div className="editor-titlebar">
        <div>
          <b>{numeroCapitulo !== null ? `Capítulo ${numeroCapitulo}` : "Editor"}</b>
          {loaded && (
            <span>
              Versión {loaded.document.document_version} ·{" "}
              {etiquetaPorEstado[loaded.state.status] ?? loaded.state.status}
            </span>
          )}
          <div className="document-modes">
            <button
              className={modoDocumento === "draft" ? "active" : ""}
              onClick={() => void abrirModo("draft")}
            >
              Borrador editable
            </button>
            <button
              className={modoDocumento === "submitted" ? "active" : ""}
              onClick={() => void abrirModo("submitted")}
            >
              Enviada al asesor
            </button>
            <button
              className={modoDocumento === "snapshot" ? "active" : ""}
              onClick={() => void abrirModo("snapshot")}
            >
              Snapshot
            </button>
          </div>
        </div>
        <div className="document-status">
          <span className="save-dot" />
          {estadoGuardadoTexto}
        </div>
      </div>
      <div className="editor-toolbar">
        <button
          className="toolbar-label"
          onClick={() => setLeftOpen(!leftOpen)}
          aria-label="Plegar panel izquierdo"
        >
          <Icon name="library" size={16} />
          {leftOpen ? "Ocultar navegación" : "Mostrar navegación"}
        </button>
        <span className="toolbar-divider" />
        {writable && (
          <>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => agregarBloque("heading")}>Encabezado</button>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => agregarBloque("paragraph")}>Párrafo</button>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => agregarBloque("blockquote")}>Cita textual</button>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => agregarBloque("code_block")}>Código</button>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => agregarBloque("bullet_list")}>Lista</button>
            <button disabled={busy || !!draft && draft.blocks.length >= 1000} onClick={() => agregarBloque("ordered_list")}>Lista numerada</button>
            <span className="toolbar-divider" />
          </>
        )}
        <button
          className="button button-primary"
          disabled={busy || !writable || !needsSave}
          onClick={() => void guardar()}
        >
          {saving ? "Guardando…" : pending ? "Reintentar guardado" : "Guardar versión"}
        </button>
        <button
          className="toolbar-label panel-toggle-right"
          onClick={() => setRightOpen(!rightOpen)}
          aria-label="Plegar panel derecho"
        >
          <Icon name="spark" size={16} />
          {rightOpen ? "Ocultar asistencia" : "Mostrar asistencia"}
        </button>
      </div>
      <div
        className={`editor-workspace ${!leftOpen ? "left-collapsed" : ""} ${!rightOpen ? "right-collapsed" : ""}`}
      >
        {leftOpen && (
          <aside className="editor-left">
            <div className="panel-tabs">
              <button
                className={leftTab === "estructura" ? "active" : ""}
                onClick={() => setLeftTab("estructura")}
              >
                Estructura
              </button>
              <button
                className={leftTab === "fuentes" ? "active" : ""}
                onClick={() => setLeftTab("fuentes")}
              >
                Fuentes {fuentes && <span>{fuentes.length}</span>}
              </button>
            </div>
            {leftTab === "estructura" ? (
              <div className="outline-tree">
                <div className="outline-progress">
                  <span>
                    {numerosCapitulo.length} capítulos con pasos del recorrido
                  </span>
                </div>
                {numerosCapitulo.map((n) => (
                  <button
                    key={n}
                    className={n === numeroCapitulo ? "outline-chapter active" : "outline-chapter"}
                    onClick={() => cambiarCapitulo(n)}
                  >
                    <Icon name="chevron" size={13} />
                    <span>
                      <b>Capítulo {n}</b>
                    </span>
                  </button>
                ))}
                {loaded && (
                  <div className="outline-steps">
                    {loaded.state.steps.length === 0 ? (
                      <small className="version-sha">
                        Este capítulo no tiene pasos de metodología asignados.
                      </small>
                    ) : (
                      loaded.state.steps.map((paso) => (
                        <button key={paso.step_code} className={paso.status === "COMPLETED" ? "done" : undefined}>
                          <span>{paso.status === "COMPLETED" ? "✓" : "•"}</span>
                          {paso.step_code}
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="sources-panel">
                {fuentes === null ? (
                  <p className="aviso">No se pudo listar las fuentes del proyecto.</p>
                ) : fuentes.length === 0 ? (
                  <p className="aviso">Aún no hay fuentes cargadas en el proyecto.</p>
                ) : (
                  fuentes.map((f) => (
                    <label className="source-row compact" key={f.source_id}>
                      <span className="pdf-icon">PDF</span>
                      <span className="source-copy">
                        <b>{f.title || f.display_label}</b>
                        <small>{f.authors && f.authors.length > 0 ? f.authors.join(", ") : f.display_label}</small>
                        <StatusBadge dot={false}>{etiquetaVerificacion(f.verification_status)}</StatusBadge>
                      </span>
                    </label>
                  ))
                )}
              </div>
            )}
          </aside>
        )}
        <section className="document-area">
          <div className="page-ruler">
            <span /><span /><span /><span /><span />
          </div>
          {error && (
            <div className="aviso aviso-error" role="alert">
              {error}
              <span className="editor-recovery">
                <button className="button button-secondary" disabled={busy} onClick={() => void consultarVersionVigente()}>
                  Consultar versión vigente
                </button>
                <button
                  className="button button-secondary"
                  disabled={busy}
                  onClick={() => {
                    if (!hasLocalWork || window.confirm("Se descartarán los cambios locales o el intento pendiente. ¿Recargar del servidor?")) {
                      void cargarCapitulo(numeroCapitulo as number)
                    }
                  }}
                >
                  Recargar y descartar borrador
                </button>
              </span>
            </div>
          )}
          {notice && <div className="aviso" role="status">{notice}</div>}
          {loaded?.document.is_stale && (
            <div className="aviso">
              El documento se creó con un estado anterior del proyecto. Revisa su
              contenido antes de guardarlo.
            </div>
          )}
          {loaded && draft && (
            <article className={`paper ${modoSoloLectura ? "read-only" : ""}`}>
              {modoSoloLectura && (
                <div className="read-only-banner">
                  {modoDocumento === "submitted"
                    ? "Versión enviada: solo lectura"
                    : modoDocumento === "snapshot"
                      ? "Snapshot histórico: solo lectura"
                      : proyecto.role !== "OWNER"
                        ? "El asesor puede consultar el documento, pero no editarlo."
                        : "Este capítulo está en estado de solo lectura."}
                </div>
              )}
              {modoDocumento !== "draft" && snapshotDetalle ? (
                <pre className="paper-snapshot">{snapshotDetalle.content_md}</pre>
              ) : (
                <>
                  {draft.blocks.length === 0 && (
                    <p className="aviso">Este capítulo aún no tiene texto guardado.</p>
                  )}
                  {draft.blocks.map((block, index) => {
                    const citas = citasPorBloque.get(block.id) ?? []
                    const anclado = citas.length > 0
                    const esArtefacto = isArtifact(block)
                    const editable = writable && !busy && modoDocumento === "draft"
                    return (
                      <div className="paper-block" key={block.id}>
                        {esArtefacto ? (
                          <div className="paper-artifact">
                            <b>{block.type === "data_table" ? "Tabla" : "Figura"}: {block.caption}</b>
                            <small>
                              Artefacto vinculado ·{" "}
                              {block.type === "data_table" ? block.table_version_id : block.figure_version_id}
                            </small>
                          </div>
                        ) : block.type === "heading" ? (
                          <div className="paper-heading-block">
                            <select
                              aria-label="Nivel del encabezado"
                              value={block.level}
                              disabled={!editable || anclado}
                              onChange={(e) =>
                                setBloque(block.id, (item) =>
                                  item.type === "heading" ? { ...item, level: Number(e.target.value) } : item,
                                )
                              }
                            >
                              {[1, 2, 3, 4, 5, 6].map((nivel) => (
                                <option key={nivel} value={nivel}>Nivel {nivel}</option>
                              ))}
                            </select>
                            <textarea
                              aria-label="Texto del encabezado"
                              className="paper-block-textarea heading"
                              value={block.text}
                              maxLength={20000}
                              disabled={!editable || anclado}
                              onChange={(e) =>
                                setBloque(block.id, (item) =>
                                  item.type === "heading" ? { ...item, text: e.target.value } : item,
                                )
                              }
                            />
                          </div>
                        ) : "items" in block ? (
                          <textarea
                            aria-label="Elementos de lista, uno por línea"
                            className="paper-block-textarea"
                            value={block.items.join("\n")}
                            disabled={!editable}
                            onChange={(e) =>
                              setBloque(block.id, (item) =>
                                "items" in item ? { ...item, items: e.target.value.split("\n") } : item,
                              )
                            }
                          />
                        ) : (
                          <textarea
                            aria-label="Texto del bloque"
                            className={`paper-block-textarea ${block.type === "paragraph" ? "" : block.type}`}
                            value={block.text}
                            maxLength={20000}
                            disabled={!editable || anclado}
                            onChange={(e) =>
                              setBloque(block.id, (item) =>
                                "text" in item ? { ...item, text: e.target.value } : item,
                              )
                            }
                          />
                        )}
                        {anclado && (
                          <small className="paper-citations">
                            Cita anclada: posición {citas.map((c) => c.position).join(", ")} · el texto está bloqueado
                            para no desplazar el offset Unicode de la cita.
                          </small>
                        )}
                        {editable && !esArtefacto && (
                          <span className="paper-block-actions">
                            <button aria-label="Mover bloque arriba" disabled={index === 0} onClick={() => moverBloque(index, -1)}>↑</button>
                            <button aria-label="Mover bloque abajo" disabled={index === draft!.blocks.length - 1} onClick={() => moverBloque(index, 1)}>↓</button>
                            <button
                              aria-label="Eliminar bloque"
                              title={anclado ? "No se puede eliminar mientras tenga citas" : "Eliminar bloque"}
                              disabled={anclado}
                              onClick={() => quitarBloque(block.id)}
                            >
                              ×
                            </button>
                          </span>
                        )}
                      </div>
                    )
                  })}
                </>
              )}
            </article>
          )}
          {serverDocument && loaded && (
            <section className="chapter-compare" aria-label="Comparación de versiones">
              <div>
                <h2>Versión vigente del servidor</h2>
                <small>
                  Versión {serverDocument.document_version} · {serverDocument.citations?.length ?? 0} grupos de citas
                </small>
                <pre>{serverDocument.content_md}</pre>
              </div>
              <div>
                <h2>Tu borrador local</h2>
                <small>
                  {loaded.document.citations?.length ?? 0} grupos de citas heredados del borrador
                </small>
                <pre>{draft ? draftTextPreview(draft) : ""}</pre>
              </div>
            </section>
          )}
        </section>
        {rightOpen && (
          <aside className="editor-right">
            <div className="panel-tabs right-tabs">
              <button
                className={rightTab === "versiones" ? "active" : ""}
                onClick={() => setRightTab("versiones")}
              >
                Versiones {snapshots.length > 0 && <span>{snapshots.length}</span>}
              </button>
              <button
                className={rightTab === "observaciones" ? "active" : ""}
                onClick={() => setRightTab("observaciones")}
              >
                Observaciones {comentarios.length > 0 && <span>{abiertas}</span>}
              </button>
            </div>
            {rightTab === "versiones" ? (
              <div className="sources-panel">
                {cargandoVersion ? (
                  <p className="aviso" role="status">Cargando versión…</p>
                ) : snapshots.length === 0 ? (
                  <p className="aviso">
                    Este capítulo no tiene versiones enviadas. Las versiones
                    (snapshots) se crean al enviar el capítulo a revisión.
                  </p>
                ) : (
                  snapshots.map((s) => (
                    <button
                      className="chapter-row"
                      key={s.id}
                      onClick={() => void abrirModo("snapshot", s.id)}
                      title="Ver el contenido de esta versión"
                    >
                      <span className="chapter-number">{s.snapshot_no}</span>
                      <div>
                        <strong>Versión de estado {s.state_version}</strong>
                        <small className="version-sha">
                          SHA {s.payload_sha256.slice(0, 12)}… ·{" "}
                          {new Date(s.created_at).toLocaleString()}
                        </small>
                      </div>
                    </button>
                  ))
                )}
              </div>
            ) : (
              <div className="comments-list">
                {comentarios.length === 0 ? (
                  <p className="aviso">
                    No hay observaciones registradas para este capítulo.
                  </p>
                ) : (
                  comentarios.map((c) => (
                    <article
                      className={`advisor-comment ${c.status === "RESOLVED" ? "resolved" : ""}`}
                      key={`${c.comment_id}:${c.snapshot_id ?? "base"}`}
                    >
                      <div className="comment-head">
                        <div className="avatar advisor-avatar">
                          {c.author.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <b>{c.author}</b>
                          <span>{new Date(c.created_at).toLocaleString()}</span>
                        </div>
                        <StatusBadge dot={false}>
                          {c.status === "OPEN" ? "Pendiente" : "Resuelta"}
                        </StatusBadge>
                      </div>
                      <p>{c.body}</p>
                      {c.selected_text && <div className="anchored-quote">«{c.selected_text}»</div>}
                      {c.status === "OPEN" && proyecto.permissions.can_review_chapters && (
                        <div className="comment-actions">
                          <button
                            className="text-link"
                            disabled={resolviendoId !== null}
                            onClick={() => void resolver(c)}
                          >
                            {resolviendoId === c.comment_id ? "Marcando…" : "Marcar como atendida"}
                          </button>
                        </div>
                      )}
                    </article>
                  ))
                )}
                {!proyecto.permissions.can_review_chapters && comentarios.length > 0 && (
                  <small className="version-sha">
                    Las observaciones las crea y las resuelve el asesor del
                    proyecto.
                  </small>
                )}
              </div>
            )}
          </aside>
        )}
      </div>
    </main>
  )
}

/** Números de capítulo del recorrido publicado (helper local de una sola llamada). */
async function getWorkflowRecursos(projectId: string): Promise<{ numeros: number[] }> {
  const w = await getWorkflowState(projectId)
  const numeros = Array.from(
    new Set(
      (w.published?.tasks ?? [])
        .map((t) => t.chapter_no)
        .filter((n): n is number => typeof n === "number"),
    ),
  ).sort((a, b) => a - b)
  return { numeros }
}

async function resolverComentario(projectId: string, commentId: number, csrfToken: string) {
  return resolveComment(projectId, commentId, csrfToken)
}

export function etiquetaVerificacion(estado: SourceDocument["verification_status"]): string {
  switch (estado) {
    case "TEXT_CHECKED":
      return "Texto completo disponible"
    case "METADATA_CHECKED":
      return "Solo metadatos"
    case "OCR_REQUIRED":
      return "OCR requerido"
    case "PENDING_EXTRACTION":
      return "Pendiente de extracción"
    case "REJECTED":
      return "Rechazado"
    default:
      return estado
  }
}
