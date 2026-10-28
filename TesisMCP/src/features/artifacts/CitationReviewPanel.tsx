import { useEffect, useState } from "react"
import {
  addCitationEvidence, decideCitationEvidence, decideCitationReplacement,
  getChapterDocument, previewCitationReplacement, proposeCitationReplacement,
} from "../../api/chapters"
import { listSourceExcerpts, listSources } from "../../api/sources"
import type {
  ChapterDocument, CitationEvidenceReview, CitationReplacementProposal,
  IeeeCitationView, SourceDocument, SourceExcerpt,
} from "../../api/types"

type Range = { start: number; end: number }
type EvidenceDecision = "SUPPORTS" | "CONTRADICTS" | "UNRELATED" | "INSUFFICIENT"

type Props = {
  projectId: string
  chapterNo: number
  occurrenceId: string
  ieeeView: IeeeCitationView
  reviews: CitationEvidenceReview[]
  canWrite: boolean
  canReview: boolean
  csrfToken?: string
  onEvidenceChanged: () => Promise<void>
  onCitationChanged: () => Promise<void>
}

const message = (cause: unknown) => cause instanceof Error ? cause.message : "No se pudo completar la operación."
const cpOffset = (value: string, utf16Offset: number) => Array.from(value.slice(0, utf16Offset)).length

export default function CitationReviewPanel({
  projectId, chapterNo, occurrenceId, ieeeView, reviews, canWrite, canReview,
  csrfToken, onEvidenceChanged, onCitationChanged,
}: Props) {
  const [document, setDocument] = useState<ChapterDocument | null>(null)
  const [sources, setSources] = useState<SourceDocument[]>([])
  const [excerpts, setExcerpts] = useState<SourceExcerpt[]>([])
  const [pageText, setPageText] = useState("")
  const [excerptId, setExcerptId] = useState(0)
  const [claimRange, setClaimRange] = useState<Range | null>(null)
  const [excerptRange, setExcerptRange] = useState<Range | null>(null)
  const [decision, setDecision] = useState<EvidenceDecision>("SUPPORTS")
  const [note, setNote] = useState("")
  const [replacementSourceId, setReplacementSourceId] = useState("")
  const [rationale, setRationale] = useState("")
  const [proposalId, setProposalId] = useState("")
  const [proposal, setProposal] = useState<CitationReplacementProposal | null>(null)
  const [reason, setReason] = useState("")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const mark = ieeeView.marks.find((item) => item.occurrence_ids.includes(occurrenceId))
  const sourceIndex = mark?.occurrence_ids.indexOf(occurrenceId) ?? -1
  const sourceId = sourceIndex >= 0 ? mark?.source_ids[sourceIndex] : undefined
  const source = sources.find((item) => item.source_id === sourceId)
  const block = document?.content_tree.blocks.find((item) => item.id === mark?.block_id)
  const paragraph = block?.type === "paragraph" ? block.text : ""
  const currentRevision = !!document?.revision_id && document.revision_id === ieeeView.document_revision_id
  const selectedExcerpt = excerpts.find((item) => item.excerpt_id === excerptId)
  const latestReview = reviews[reviews.length - 1]
  const selectedClaim = claimRange ? Array.from(paragraph).slice(claimRange.start, claimRange.end).join("") : ""
  const selectedPassage = selectedExcerpt && excerptRange
    ? Array.from(selectedExcerpt.text).slice(excerptRange.start, excerptRange.end).join("") : ""
  const claimValid = !!mark && !!claimRange && claimRange.start <= mark.position && mark.position <= claimRange.end
    && selectedClaim.trim().length >= 10 && selectedClaim.trim().length <= 1000
  const passageValid = !!selectedExcerpt && !!excerptRange && selectedPassage.trim().length > 0

  useEffect(() => {
    let active = true
    setDocument(null); setSources([]); setExcerpts([]); setClaimRange(null); setExcerptRange(null)
    setExcerptId(0); setProposal(null); setProposalId(""); setError(null); setNotice(null)
    Promise.all([getChapterDocument(projectId, chapterNo), listSources(projectId)])
      .then(([chapter, availableSources]) => {
        if (!active) return
        setDocument(chapter); setSources(availableSources)
      })
      .catch((cause) => { if (active) setError(message(cause)) })
    return () => { active = false }
  }, [projectId, chapterNo, occurrenceId, ieeeView.document_revision_id])

  useEffect(() => {
    if (!sourceId || source?.verification_status !== "TEXT_CHECKED") return
    let active = true
    setExcerpts([]); setExcerptId(0); setExcerptRange(null)
    const pageNo = pageText.trim() ? Number(pageText) : undefined
    if (pageNo !== undefined && (!Number.isInteger(pageNo) || pageNo < 1)) return
    listSourceExcerpts(projectId, sourceId, pageNo, 50)
      .then((result) => { if (active) setExcerpts(result.excerpts) })
      .catch((cause) => { if (active) setError(message(cause)) })
    return () => { active = false }
  }, [projectId, sourceId, source?.verification_status, pageText])

  async function createEvidence() {
    if (!canWrite || !currentRevision || !claimValid || !passageValid || !selectedExcerpt || !claimRange || !excerptRange) return
    setBusy(true); setError(null); setNotice(null)
    try {
      await addCitationEvidence(projectId, chapterNo, occurrenceId, {
        excerpt_id: selectedExcerpt.excerpt_id,
        claim_start: claimRange.start, claim_end: claimRange.end,
        excerpt_start: excerptRange.start, excerpt_end: excerptRange.end,
        idempotency_key: crypto.randomUUID(),
      }, csrfToken)
      await onEvidenceChanged()
      setNotice("Pasaje candidato registrado. Falta la evaluación del asesor.")
    } catch (cause) { setError(message(cause)) }
    finally { setBusy(false) }
  }

  async function reviewEvidence() {
    if (!canReview || !latestReview || !currentRevision) return
    setBusy(true); setError(null); setNotice(null)
    try {
      await decideCitationEvidence(projectId, chapterNo, latestReview.review_id, {
        status: decision, expected_version: latestReview.review_version,
        idempotency_key: crypto.randomUUID(), note,
      }, csrfToken)
      await onEvidenceChanged()
      setNotice("Evaluación del asesor registrada como nueva versión.")
    } catch (cause) { setError(message(cause)) }
    finally { setBusy(false) }
  }

  async function openProposal(id: string) {
    setBusy(true); setError(null); setNotice(null)
    try {
      const loaded = await previewCitationReplacement(projectId, chapterNo, id)
      if (loaded.occurrence_id !== occurrenceId) throw new Error("La propuesta pertenece a otra cita.")
      setProposal(loaded); setProposalId(loaded.proposal_id)
    } catch (cause) { setError(message(cause)) }
    finally { setBusy(false) }
  }

  async function createProposal() {
    if (!currentRevision || !replacementSourceId || replacementSourceId === sourceId || rationale.trim().length < 10) return
    setBusy(true); setError(null); setNotice(null)
    try {
      const created = await proposeCitationReplacement(projectId, chapterNo, occurrenceId, {
        replacement_source_id: replacementSourceId,
        rationale: rationale.trim(), idempotency_key: crypto.randomUUID(),
      }, csrfToken)
      const loaded = await previewCitationReplacement(projectId, chapterNo, created.proposal_id)
      setProposal(loaded); setProposalId(created.proposal_id)
      setNotice("Propuesta creada. Compara ambas referencias antes de decidir.")
    } catch (cause) { setError(message(cause)) }
    finally { setBusy(false) }
  }

  async function decideProposal(action: "ACCEPTED" | "REJECTED") {
    if (!canWrite || !proposal || proposal.decision || !currentRevision) return
    if (action === "ACCEPTED" && !window.confirm("¿Sustituir la fuente de esta cita y guardar una nueva revisión del documento?")) return
    setBusy(true); setError(null); setNotice(null)
    try {
      const updated = await decideCitationReplacement(projectId, chapterNo, proposal.proposal_id, {
        action, expected_document_version: proposal.expected_document_version,
        idempotency_key: crypto.randomUUID(), reason: reason.trim(),
      }, csrfToken)
      setProposal(updated)
      setNotice(action === "ACCEPTED" ? "Sustitución aceptada y nueva revisión guardada." : "Sustitución rechazada.")
      if (action === "ACCEPTED") await onCitationChanged()
    } catch (cause) { setError(message(cause)) }
    finally { setBusy(false) }
  }

  return <div className="citation-review-panel">
    <h5>Revisión de la cita seleccionada</h5>
    <p>Fuente citada: {source?.display_label ?? sourceId ?? "Cargando…"}. Posición {mark?.position ?? "—"} en el párrafo.</p>
    {error && <p className="chapter-alert" role="alert">{error}</p>}
    {notice && <p className="chapter-notice" role="status">{notice}</p>}
    {!currentRevision && document && <p className="chapter-alert">El documento cambió desde esta vista IEEE. Actualízala antes de registrar evidencia o propuestas.</p>}
    <div className="evidence-audit-panel">
      <h5>Historial de evidencia ({reviews.length})</h5>
      {reviews.length === 0 && <p>No hay pasajes candidatos para esta cita.</p>}
      {reviews.map((item) => <div key={item.review_id} className="evidence-card">
        <b>v{item.review_version} · {item.status} · página física {item.physical_page}</b>
        <p>Afirmación: {item.claim_text}</p><p>Pasaje: {item.matched_text}</p>
        {item.review_note && <p>Nota del asesor: {item.review_note}</p>}
        <small>Evaluación semántica automática: {item.automated_semantic_assessment}</small>
      </div>)}
      {canReview && latestReview && currentRevision && <div className="citation-review-form">
        <h6>Evaluación del asesor</h6>
        <select value={decision} onChange={(event) => setDecision(event.target.value as EvidenceDecision)}>
          <option value="SUPPORTS">Respalda</option><option value="CONTRADICTS">Contradice</option>
          <option value="UNRELATED">No relacionada</option><option value="INSUFFICIENT">Insuficiente</option>
        </select>
        <textarea value={note} maxLength={2000} onChange={(event) => setNote(event.target.value)} placeholder="Motivo de la evaluación" />
        <button className="btn-primary btn-sm" disabled={busy} onClick={() => void reviewEvidence()}>Registrar evaluación</button>
      </div>}
    </div>
    {canWrite && currentRevision && source?.verification_status === "TEXT_CHECKED" && paragraph && <div className="citation-review-form">
      <h5>Vincular un pasaje candidato</h5>
      <p>Selecciona con el cursor la afirmación que incluye el ancla de la cita (10 a 1000 caracteres).</p>
      <textarea readOnly value={paragraph} onSelect={(event) => {
        const input = event.currentTarget
        setClaimRange({ start: cpOffset(paragraph, input.selectionStart), end: cpOffset(paragraph, input.selectionEnd) })
      }} />
      {claimRange && <small>Afirmación: {selectedClaim || "selección vacía"} {claimValid ? "✓" : "· debe incluir el ancla y cumplir la longitud"}</small>}
      <label>Página física (vacía: primeros pasajes)
        <input inputMode="numeric" value={pageText} onChange={(event) => setPageText(event.target.value)} />
      </label>
      <select value={excerptId} onChange={(event) => { setExcerptId(Number(event.target.value)); setExcerptRange(null) }}>
        <option value={0}>Selecciona un pasaje de la fuente citada</option>
        {excerpts.map((item) => <option key={item.excerpt_id} value={item.excerpt_id}>Página {item.physical_page} · pasaje {item.excerpt_id}</option>)}
      </select>
      {selectedExcerpt && <>
        <p>Selecciona en el pasaje el fragmento que respalda la afirmación.</p>
        <textarea readOnly value={selectedExcerpt.text} onSelect={(event) => {
          const input = event.currentTarget
          setExcerptRange({ start: cpOffset(selectedExcerpt.text, input.selectionStart), end: cpOffset(selectedExcerpt.text, input.selectionEnd) })
        }} />
        {excerptRange && <small>Fragmento: {selectedPassage || "selección vacía"}</small>}
      </>}
      <button className="btn-primary btn-sm" disabled={busy || !claimValid || !passageValid} onClick={() => void createEvidence()}>Registrar pasaje candidato</button>
    </div>}
    {canWrite && source && source.verification_status !== "TEXT_CHECKED" && <p>La fuente citada no tiene texto extraído apto para vincular pasajes.</p>}
    {currentRevision && <div className="citation-review-form">
      <h5>Proponer reemplazo de fuente</h5>
      <select value={replacementSourceId} onChange={(event) => setReplacementSourceId(event.target.value)}>
        <option value="">Selecciona otra fuente del proyecto</option>
        {sources.filter((item) => item.source_id !== sourceId).map((item) =>
          <option key={item.source_id} value={item.source_id}>{item.display_label}</option>)}
      </select>
      <textarea value={rationale} maxLength={2000} onChange={(event) => setRationale(event.target.value)} placeholder="Justificación de la propuesta (10 a 2000 caracteres)" />
      <button className="btn-secondary btn-sm" disabled={busy || !replacementSourceId || rationale.trim().length < 10} onClick={() => void createProposal()}>Crear propuesta revisable</button>
      <label>Recuperar propuesta por ID
        <input value={proposalId} onChange={(event) => setProposalId(event.target.value)} placeholder="UUID de la propuesta" />
      </label>
      <button className="btn-secondary btn-sm" disabled={busy || !proposalId.trim()} onClick={() => void openProposal(proposalId.trim())}>Abrir propuesta</button>
      {proposal && <div className="citation-proposal-preview">
        <b>Propuesta {proposal.proposal_id}</b><p>{proposal.rationale}</p>
        <div className="citation-proposal-columns">
          <div><h6>Referencia anterior</h6><pre>{JSON.stringify(proposal.previous_reference, null, 2)}</pre></div>
          <div><h6>Referencia propuesta</h6><pre>{JSON.stringify(proposal.replacement_reference, null, 2)}</pre></div>
        </div>
        <small>Versión de documento prevista: {proposal.expected_document_version}. Estado: {proposal.decision?.status ?? "Sin decidir"}.</small>
        {canWrite && !proposal.decision && <div className="citation-proposal-actions">
          <input value={reason} maxLength={2000} onChange={(event) => setReason(event.target.value)} placeholder="Motivo de la decisión (opcional)" />
          <button className="btn-success btn-sm" disabled={busy || proposal.document_revision_id !== ieeeView.document_revision_id} onClick={() => void decideProposal("ACCEPTED")}>Aceptar reemplazo</button>
          <button className="btn-danger btn-sm" disabled={busy || proposal.document_revision_id !== ieeeView.document_revision_id} onClick={() => void decideProposal("REJECTED")}>Rechazar</button>
        </div>}
      </div>}
    </div>}
  </div>
}
