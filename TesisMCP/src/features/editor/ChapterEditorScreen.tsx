import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { ApiError } from "../../api/client"
import { getChapterDocument, getChapterState, saveChapterDocument } from "../../api/chapters"
import { downloadApprovedChapterDocx, downloadDraftDocx } from "../../api/exports"
import ArtifactPicker from "./ArtifactPicker"
import type { ArtifactChoice } from "./ArtifactPicker"
import type { ChapterBlock, ChapterCitation, ChapterContentTree, ChapterDocument, ChapterState, ProjectSummary, SessionUser } from "../../api/types"
import { draftTextPreview, unsupportedDocumentReason } from "./editorDocument"

interface Props {
  project: ProjectSummary; user: SessionUser; csrfToken: string
  onBack: () => void; onUnauthorized: () => void; onAccessLost: () => void
  onRefreshCsrf: () => Promise<void>; onLogout: () => Promise<void>
}
type Loaded = { state: ChapterState; document: ChapterDocument }
type SaveCitation = { group_id: string; block_id: string; position: number; sources: Array<{ source_id: string; locator: string }> }
type PendingSave = { content_tree: ChapterContentTree; citations: SaveCitation[]; expected_version: number; idempotency_key: string }
const AVAILABLE_CHAPTERS = [1, 2, 3, 4, 5, 6, 7] // CHAPTER_STEPS physical se deriva hoy del catálogo de pasos.

function isArtifact(block: ChapterBlock): block is Extract<ChapterBlock, { type: "data_table" | "figure" }> {
  return block.type === "data_table" || block.type === "figure"
}
function editableCitations(citations: ChapterCitation[] | undefined): SaveCitation[] {
  return (citations ?? []).map(({ group_id, block_id, position, sources }) => ({
    group_id, block_id, position, sources: sources.map(({ source_id, locator }) => ({ source_id, locator })),
  }))
}
function sameCitationAnchors(left: ChapterCitation[] | undefined, right: ChapterCitation[] | undefined): boolean {
  const sorted = (citations: ChapterCitation[] | undefined) => editableCitations(citations)
    .sort((a, b) => a.group_id.localeCompare(b.group_id))
  return JSON.stringify(sorted(left)) === JSON.stringify(sorted(right))
}

export default function ChapterEditorScreen({ project, user, csrfToken, onBack, onUnauthorized, onAccessLost, onRefreshCsrf, onLogout }: Props) {
  const [chapterNo, setChapterNo] = useState(1)
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [draft, setDraft] = useState<ChapterContentTree | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [pending, setPending] = useState<PendingSave | null>(null)
  const [writeBlocked, setWriteBlocked] = useState(false)
  const [serverVersion, setServerVersion] = useState<string | null>(null)
  const [serverDocument, setServerDocument] = useState<ChapterDocument | null>(null)
  const [artifactPicker, setArtifactPicker] = useState<"data_table" | "figure" | null>(null)
  const loadSequence = useRef(0)
  const dirty = !!loaded && !!draft && JSON.stringify(draft) !== JSON.stringify(loaded.document.content_tree)
  const hasLocalWork = dirty || pending !== null
  const needsSave = dirty || !!loaded?.document.is_stale || (!!loaded && loaded.document.revision_id === null)
  const writable = !!loaded && !!draft && !writeBlocked && project.role === "OWNER" && project.permissions.can_edit_document
    && (loaded.state.status === "DRAFT" || loaded.state.status === "CHANGES_REQUESTED")
  const busy = loading || saving

  useEffect(() => {
    if (!hasLocalWork) return
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = "" }
    window.addEventListener("beforeunload", warn)
    return () => window.removeEventListener("beforeunload", warn)
  }, [hasLocalWork])

  const loadChapter = useCallback(async (number: number) => {
    const sequence = ++loadSequence.current
    setLoading(true); setError(null); setNotice(null); setPending(null); setWriteBlocked(false); setServerVersion(null); setServerDocument(null)
    try {
      const [state, document] = await Promise.all([
        getChapterState(project.project_id, number), getChapterDocument(project.project_id, number),
      ])
      if (sequence !== loadSequence.current) return
      if (state.chapter_no !== number || document.chapter_no !== number) throw new Error("El backend respondió con otro capítulo.")
      const unsupported = unsupportedDocumentReason(document)
      setLoaded({ state, document })
      setDraft(unsupported ? null : structuredClone(document.content_tree))
      if (unsupported) setError(unsupported)
    } catch (cause) {
      if (sequence !== loadSequence.current) return
      if (cause instanceof ApiError && cause.status === 401) onUnauthorized()
      if (cause instanceof ApiError && cause.status === 404) onAccessLost()
      setLoaded(null); setDraft(null); setError(cause instanceof Error ? cause.message : "No se pudo cargar el capítulo.")
    } finally { if (sequence === loadSequence.current) setLoading(false) }
  }, [project.project_id, onUnauthorized, onAccessLost])
  useEffect(() => { void loadChapter(chapterNo) }, [chapterNo, loadChapter])

  const citationsByBlock = useMemo(() => {
    const map = new Map<string, ChapterCitation[]>()
    for (const citation of loaded?.document.citations ?? []) map.set(citation.block_id, [...(map.get(citation.block_id) ?? []), citation])
    return map
  }, [loaded])

  function setBlock(blockId: string, update: (block: ChapterBlock) => ChapterBlock) {
    setDraft((tree) => tree ? { ...tree, blocks: tree.blocks.map((block) => block.id === blockId ? update(block) : block) } : tree)
    setPending(null); setNotice(null)
  }
  function addBlock(type: "heading" | "paragraph" | "blockquote" | "code_block" | "bullet_list" | "ordered_list") {
    if (!draft) return
    const block: ChapterBlock = type === "heading" ? { type, id: crypto.randomUUID(), level: 2, text: "Nuevo encabezado" }
      : type === "bullet_list" || type === "ordered_list" ? { type, id: crypto.randomUUID(), items: ["Nuevo elemento"] }
        : { type, id: crypto.randomUUID(), text: type === "code_block" ? "" : "Nuevo texto" }
    setDraft({ ...draft, blocks: [...draft.blocks, block] }); setPending(null)
  }
  function addArtifactBlock(type: "data_table" | "figure") {
    if (!draft || !writable || busy || draft.blocks.length >= 1000) return
    setArtifactPicker(type)
  }
  function insertArtifact(choice: ArtifactChoice) {
    if (!draft || !writable || busy || draft.blocks.length >= 1000 || choice.type !== artifactPicker) return
    const id = crypto.randomUUID()
    const block: ChapterBlock = choice.type === "data_table"
      ? { type: "data_table", id, table_version_id: choice.version.version_id,
          result_sha256: choice.version.result_sha256, caption: choice.caption }
      : { type: "figure", id, figure_version_id: choice.version.version_id,
          output_sha256: choice.version.output_sha256, caption: choice.caption }
    setDraft({ ...draft, schema_version: 2, blocks: [...draft.blocks, block] })
    setPending(null)
    setNotice(null)
    setArtifactPicker(null)
  }
  async function handleQuickExportDraft() {
    try {
      setNotice("Generando borrador DOCX...")
      const name = await downloadDraftDocx(project.project_id)
      setNotice(`Borrador descargado como '${name}'.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al descargar borrador DOCX.")
    }
  }
  async function handleQuickExportApproved() {
    try {
      setNotice(`Generando capítulo ${chapterNo} aprobado DOCX...`)
      const name = await downloadApprovedChapterDocx(project.project_id, chapterNo)
      setNotice(`Capítulo ${chapterNo} descargado como '${name}'.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : `No se pudo descargar el capítulo ${chapterNo}. Asegúrate de que el asesor lo haya aprobado formalmente.`)
    }
  }
  function moveBlock(index: number, delta: -1 | 1) {
    if (!draft) return
    const target = index + delta
    if (target < 0 || target >= draft.blocks.length) return
    const blocks = [...draft.blocks]; [blocks[index], blocks[target]] = [blocks[target], blocks[index]]
    setDraft({ ...draft, blocks }); setPending(null)
  }
  function changeChapter(number: number) {
    if (number === chapterNo) return
    if (hasLocalWork && !window.confirm("Hay cambios sin guardar o un guardado pendiente de confirmar. Al cambiar de capítulo se descartará el borrador. ¿Continuar?")) return
    loadSequence.current += 1
    setArtifactPicker(null)
    setLoaded(null); setDraft(null)
    setChapterNo(number)
  }
  async function save() {
    if (!loaded || !draft || !writable || busy || !needsSave) return
    const attempt = pending ?? {
      content_tree: structuredClone(draft), citations: editableCitations(loaded.document.citations),
      expected_version: loaded.document.document_version, idempotency_key: crypto.randomUUID(),
    }
    setPending(attempt); setSaving(true); setError(null); setNotice(null)
    let putConfirmed = false
    try {
      const result = await saveChapterDocument(project.project_id, chapterNo, attempt, csrfToken)
      putConfirmed = true
      // El reintento idempotente puede devolver una revisión histórica si hubo otro guardado después.
      const [state, current] = await Promise.all([
        getChapterState(project.project_id, chapterNo), getChapterDocument(project.project_id, chapterNo),
      ])
      if (current.revision_id !== result.revision_id) {
        setWriteBlocked(true)
        setServerVersion(`Versión vigente ${current.document_version} · ${state.status}`)
        setServerDocument(current)
        setError("El servidor confirmó tu intento, pero existe una versión posterior. Se conserva tu borrador para revisarlo antes de continuar.")
        return
      }
      const unsupported = unsupportedDocumentReason(current)
      if (unsupported) {
        setWriteBlocked(true); setError(unsupported); return
      }
      setLoaded({ state, document: current })
      setDraft(structuredClone(current.content_tree)); setPending(null); setServerVersion(null); setServerDocument(null)
      setWriteBlocked(state.status !== "DRAFT" && state.status !== "CHANGES_REQUESTED")
      setNotice(result.idempotent ? "El servidor confirmó este intento y su versión vigente." : "Cambios guardados y versión vigente comprobada.")
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) { onUnauthorized(); return }
      if (cause instanceof ApiError && cause.status === 404) { onAccessLost(); return }
      if (putConfirmed) {
        setWriteBlocked(true)
        setError("El servidor confirmó el guardado, pero no se pudo consultar la versión vigente. Conservamos el intento para revalidarlo.")
      } else if (cause instanceof ApiError && cause.kind === "csrf") {
        try { await onRefreshCsrf() } catch { /* conservar borrador */ }
        setError("Falló la protección CSRF. El borrador se conserva; vuelve a guardar para reintentar.")
      } else if (cause instanceof ApiError && cause.status === 409) {
        setWriteBlocked(true)
        setError("El documento cambió en el servidor o ya no admite edición. Tu borrador se conserva; recarga solo si deseas descartarlo.")
      } else if (cause instanceof ApiError && cause.kind === "permission") {
        setWriteBlocked(true)
        setError("Ya no tienes permiso para modificar este documento. El borrador se conserva solo en esta página.")
      } else setError(cause instanceof Error ? cause.message : "No se confirmó el guardado. El borrador se conserva.")
    } finally { setSaving(false) }
  }
  async function checkServerVersion() {
    if (!loaded || !draft || busy) return
    setLoading(true)
    try {
      const [state, current] = await Promise.all([
        getChapterState(project.project_id, chapterNo), getChapterDocument(project.project_id, chapterNo),
      ])
      setServerVersion(`Versión vigente ${current.document_version} · ${state.status}`)
      setServerDocument(current)
      const sameTree = JSON.stringify(current.content_tree) === JSON.stringify(draft)
      const sameCitations = sameCitationAnchors(current.citations, loaded.document.citations)
      const baseStillCurrent = current.revision_id === loaded?.document.revision_id
        && current.document_version === loaded.document.document_version
      if (sameTree && sameCitations && (!pending || !baseStillCurrent) && !unsupportedDocumentReason(current)) {
        setLoaded({ state, document: current }); setDraft(structuredClone(current.content_tree)); setPending(null); setServerDocument(null)
        setWriteBlocked(state.status !== "DRAFT" && state.status !== "CHANGES_REQUESTED")
        setError(null); setNotice("El contenido local coincide con la versión vigente del servidor.")
      } else if (baseStillCurrent && (state.status === "DRAFT" || state.status === "CHANGES_REQUESTED")) {
        setWriteBlocked(false)
        setError("El servidor aún muestra la versión anterior. Puedes reintentar el mismo guardado con su clave conservada.")
      } else {
        setWriteBlocked(true)
        setError("La versión vigente difiere de tu borrador. Este sigue local; recarga solo si aceptas descartarlo.")
      }
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) { onUnauthorized(); return }
      if (cause instanceof ApiError && cause.status === 404) { onAccessLost(); return }
      setError(cause instanceof Error ? cause.message : "No se pudo consultar la versión vigente.")
    } finally { setLoading(false) }
  }
  async function logout() {
    if (saving) return
    if (hasLocalWork && !window.confirm("Tienes cambios sin guardar o pendientes de confirmar. Cerrar sesión descartará el borrador. ¿Continuar?")) return
    try { await onLogout() } catch (cause) { setError(cause instanceof Error ? cause.message : "No se pudo cerrar la sesión.") }
  }

  return <div className="connected-app-shell editor-app-shell">
    <aside className="sidebar connected-sidebar">
      <div className="brand"><div className="brand-mark" aria-hidden="true">T</div><div><b>TesisMCP</b><span>Espacio académico</span></div></div>
      <div className="connected-project-sidebar"><span className="eyebrow">PROYECTO ACTIVO</span><strong>{project.name}</strong><span>{project.role === "OWNER" ? "Tesista" : "Asesor"}</span></div>
      <div className="sidebar-bottom"><button className="nav-item connected-change-project" disabled={saving} onClick={() => { if (!hasLocalWork || window.confirm("Se descartará el borrador local o el guardado pendiente de confirmar. ¿Volver al proyecto?")) onBack() }}>Volver al proyecto</button><div className="profile"><div className="avatar">{(user.display_name || user.email).slice(0, 1).toUpperCase()}</div><div><b>{user.display_name || user.email}</b><span>{project.role === "OWNER" ? "Tesista" : "Asesor"}</span></div></div></div>
    </aside>
    <div className="app-main"><header className="topbar"><div className="breadcrumbs"><span>{project.name}</span><strong>Editor de capítulos</strong></div><div className="top-actions"><span className="real-connection-pill"><i />API conectada</span><button className="button button-secondary" disabled={saving} onClick={() => void logout()}>Cerrar sesión</button></div></header>
      <main className="chapter-editor-page">
        <div className="chapter-editor-heading"><div><span className="eyebrow blue">DOCUMENTO VERSIONADO</span><h1>Editor del capítulo</h1><p>Edición por bloques conectada al documento canónico del proyecto.</p></div><label className="chapter-picker">Capítulo<select value={chapterNo} disabled={busy} onChange={(event) => changeChapter(Number(event.target.value))}>{AVAILABLE_CHAPTERS.map((number) => <option key={number} value={number}>{number}</option>)}</select></label></div>
        {error && <div className="chapter-alert" role="alert">{error}</div>}{notice && <div className="chapter-notice" role="status">{notice}</div>}
        {serverVersion && <div className="chapter-info" role="status">{serverVersion}</div>}
        {loading && <section className="chapter-empty" role="status">Cargando estado y documento del capítulo…</section>}
        {!loading && loaded && !draft && <section className="chapter-empty"><p>Documento en solo lectura: este editor no reconoce toda su estructura.</p><pre className="chapter-unsupported-text">{loaded.document.content_md}</pre></section>}
        {!loading && loaded && draft && <>
          <section className="chapter-status-row"><span className={`status ${loaded.state.status === "APPROVED" ? "status-success" : loaded.state.status === "READY" ? "status-violet" : "status-blue"}`}>{loaded.state.status}</span><span>Versión {loaded.document.document_version}</span><span>{loaded.document.is_legacy_projection ? "Proyección de revisiones anteriores" : loaded.document.revision_no ? `Revisión ${loaded.document.revision_no}` : "Sin revisión guardada"}</span>{dirty ? <strong className="chapter-dirty">Cambios sin guardar</strong> : <span className="chapter-saved">{notice ? "Confirmado por el servidor" : "Sin cambios locales"}</span>}</section>
          {loaded.document.is_stale && <div className="chapter-alert" role="status">El documento se creó con un estado anterior del proyecto. Revisa su contenido antes de enviarlo a revisión.</div>}
          {!writable && <div className="chapter-alert" role="status">{project.role !== "OWNER" ? "El asesor puede consultar el documento, pero no editarlo." : "Este capítulo está en estado de solo lectura."}</div>}
          {loaded.document.is_legacy_projection && <div className="chapter-info">El texto procede de revisiones anteriores. Al guardar, el backend creará la primera revisión del documento canónico.</div>}
          {serverDocument && <section className="chapter-compare" aria-label="Comparación de versiones"><div><h2>Versión vigente del servidor</h2><small>Versión {serverDocument.document_version} · {serverDocument.citations?.length ?? 0} grupos de citas</small><pre>{serverDocument.content_md}</pre></div><div><h2>Tu borrador local</h2><small>{loaded.document.citations?.length ?? 0} grupos de citas heredados del borrador</small><pre>{draftTextPreview(draft)}</pre></div></section>}
          {draft.blocks.length === 0 && <section className="chapter-empty">Este capítulo aún no tiene texto guardado.</section>}
          <section className="chapter-block-list" aria-label="Bloques del documento">{draft.blocks.map((block, index) => {
            const citations = citationsByBlock.get(block.id) ?? []; const cited = citations.length > 0
            return <article className="chapter-block-card" key={block.id}>
              <div className="chapter-block-toolbar"><span>{isArtifact(block) ? block.type === "data_table" ? "Tabla vinculada" : "Figura vinculada" : block.type.replace(/_/g, " ")}{cited && <b className="citation-lock"> · cita anclada</b>}{isArtifact(block) && <b className="citation-lock"> · artefacto protegido</b>}</span><div><button aria-label="Mover bloque arriba" disabled={!writable || busy || index === 0} onClick={() => moveBlock(index, -1)}>↑</button><button aria-label="Mover bloque abajo" disabled={!writable || busy || index === draft.blocks.length - 1} onClick={() => moveBlock(index, 1)}>↓</button><button aria-label="Eliminar bloque" title={isArtifact(block) ? "Los artefactos vinculados se preservan en este paso" : cited ? "No se puede eliminar mientras tenga citas" : "Eliminar bloque"} disabled={!writable || busy || cited || isArtifact(block)} onClick={() => { if (draft && !isArtifact(block) && !cited) { setDraft({ ...draft, blocks: draft.blocks.filter((item) => item.id !== block.id) }); setPending(null) } }}>×</button></div></div>
              {isArtifact(block) ? <div className="chapter-artifact"><b>{block.type === "data_table" ? "Tabla" : "Figura"}: {block.caption}</b><small>Artefacto preservado · {block.type === "data_table" ? block.table_version_id : block.figure_version_id}</small></div>
                : block.type === "heading" ? <div className="chapter-heading-fields"><select aria-label="Nivel del encabezado" value={block.level} disabled={!writable || busy || cited} onChange={(e) => setBlock(block.id, (item) => item.type === "heading" ? { ...item, level: Number(e.target.value) } : item)}>{[1, 2, 3, 4, 5, 6].map((level) => <option key={level} value={level}>Nivel {level}</option>)}</select><textarea aria-label="Texto del encabezado" value={block.text} maxLength={20000} disabled={!writable || busy || cited} onChange={(e) => setBlock(block.id, (item) => item.type === "heading" ? { ...item, text: e.target.value } : item)} /></div>
                  : "items" in block ? <textarea aria-label="Elementos de lista, uno por línea" value={block.items.join("\n")} disabled={!writable || busy} onChange={(e) => setBlock(block.id, (item) => "items" in item ? { ...item, items: e.target.value.split("\n") } : item)} />
                    : <textarea aria-label="Texto del bloque" value={block.text} maxLength={20000} disabled={!writable || busy || cited} onChange={(e) => setBlock(block.id, (item) => "text" in item ? { ...item, text: e.target.value } : item)} />}
              {cited && <div className="chapter-citations"><b>Citas y anclas conservadas</b>{citations.map((citation) => <div key={citation.group_id}>Posición {citation.position}: {citation.sources.map((source) => { const title = source.reference?.title; return `${typeof title === "string" ? title : source.source_id}${source.locator ? ` · ${source.locator}` : ""}` }).join("; ")}</div>)}<small>El texto está bloqueado para no desplazar el offset Unicode de la cita.</small></div>}
            </article>
          })}</section>
          {writable && <div className="chapter-editor-actions"><div className="chapter-add-actions">{([[
            "heading", "Encabezado"], ["paragraph", "Párrafo"], ["blockquote", "Cita textual"],
            ["code_block", "Código"], ["bullet_list", "Lista"], ["ordered_list", "Lista numerada"],
          ] as const).map(([type, label]) => <button key={type} className="button button-secondary" disabled={busy || draft.blocks.length >= 1000} onClick={() => addBlock(type)}>+ {label}</button>)}<button className="button button-secondary" disabled={busy || draft.blocks.length >= 1000} onClick={() => addArtifactBlock("data_table")}>+ Tabla</button><button className="button button-secondary" disabled={busy || draft.blocks.length >= 1000} onClick={() => addArtifactBlock("figure")}>+ Figura</button></div><div className="chapter-save-and-export"><button className="button button-secondary" disabled={busy} onClick={() => void handleQuickExportDraft()} title="Descarga el borrador compilado en formato DOCX">Exportar Borrador (.docx)</button><button className="button button-primary" disabled={busy || !needsSave} onClick={() => void save()}>{saving ? "Guardando…" : pending ? "Reintentar guardado" : "Guardar versión"}</button></div></div>}
          {error && <div className="chapter-recovery-actions"><button className="button button-secondary" disabled={busy} onClick={() => void checkServerVersion()}>Consultar versión vigente</button><button className="button button-secondary chapter-reload" disabled={busy} onClick={() => { if (!hasLocalWork || window.confirm("Se descartarán los cambios locales o el intento pendiente. ¿Recargar del servidor?")) void loadChapter(chapterNo) }}>Recargar y descartar borrador</button></div>}
        </>}
      </main>
    </div>
    {artifactPicker && <ArtifactPicker
      projectId={project.project_id}
      type={artifactPicker}
      onSelect={insertArtifact}
      onCancel={() => setArtifactPicker(null)}
    />}
  </div>
}
