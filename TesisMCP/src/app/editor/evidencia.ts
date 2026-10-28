import { useCallback, useEffect, useState } from "react"
import { ApiError } from "../../api/client"
import {
  addCitationEvidence,
  decideCitationEvidence,
  getChapterIeeeCitations,
  listCitationEvidence,
} from "../../api/chapters"
import { listSourceExcerpts } from "../../api/sources"
import type {
  ChapterContentTree,
  CitationEvidenceReview,
  IeeeCitationView,
  SourceExcerpt,
} from "../../api/types"
import { utf16ACodePoints } from "./citas"

/** Opción de evidencia: un par (ocurrencia, fuente) aplanado de la vista IEEE.
 * Los pares source_ids[i] ↔ occurrence_ids[i] corresponden a la misma fuente
 * dentro del grupo de la cita (citation_evidence.py exige que el pasaje
 * pertenezca a la fuente de la ocurrencia). */
export type OpcionEvidencia = {
  groupId: string
  indice: number
  occurrenceId: string
  sourceId: string
  citationText: string
  blockId: string
  position: number
  number: number
}

export function opcionesDeEvidencia(vista: IeeeCitationView | null): OpcionEvidencia[] {
  if (!vista) return []
  const opciones: OpcionEvidencia[] = []
  for (const marca of vista.marks) {
    marca.source_ids.forEach((sourceId, indice) => {
      const occurrenceId = marca.occurrence_ids[indice] ?? ""
      if (occurrenceId) {
        opciones.push({
          groupId: marca.group_id,
          indice,
          occurrenceId,
          sourceId,
          citationText: marca.citation_text,
          blockId: marca.block_id,
          position: marca.position,
          number: marca.numbers[indice] ?? marca.numbers[0],
        })
      }
    })
  }
  return opciones
}

/** Rango de afirmación por defecto: una ventana de hasta 1000 caracteres que
 * siempre incluye el ancla de la cita (regla del backend). */
export function rangoAfirmacionInicial(texto: string, position: number): { start: number; end: number } {
  const largo = utf16ACodePoints(texto, texto.length)
  const start = Math.max(0, Math.min(position - 300, Math.max(0, largo - 1000)))
  const end = Math.min(largo, start + 1000)
  return { start, end: Math.max(end, start + 1) }
}

function textoDeParrafo(draft: ChapterContentTree | null, blockId: string): string | null {
  const bloque = draft?.blocks.find((b) => b.id === blockId)
  return bloque && bloque.type === "paragraph" ? bloque.text : null
}

/**
 * Estado y acciones del panel de evidencia de citas: carga la vista IEEE para
 * listar ocurrencias, carga los extractos de la fuente citada, permite al
 * tesista (owner_only en citation_evidence.py) crear un candidato con el
 * rango de afirmación y el rango del pasaje, y al asesor (solo rol ADVISOR)
 * decidir sobre la última revisión. Todo con estados y errores reales.
 */
export function useEvidencia(args: {
  projectId: string
  numeroCapitulo: number | null
  csrfToken: string
  activa: boolean
  esPropietario: boolean
  esAsesor: boolean
  draft: ChapterContentTree | null
  onUnauthorized: () => void
}) {
  const { projectId, numeroCapitulo, activa, draft } = args
  const [vista, setVista] = useState<IeeeCitationView | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [opcion, setOpcion] = useState<OpcionEvidencia | null>(null)
  const [textoClaim, setTextoClaim] = useState<string | null>(null)
  const [extractos, setExtractos] = useState<SourceExcerpt[] | null>(null)
  const [extractoId, setExtractoId] = useState<number | null>(null)
  const [claimStart, setClaimStart] = useState(0)
  const [claimEnd, setClaimEnd] = useState(0)
  const [exStart, setExStart] = useState(0)
  const [exEnd, setExEnd] = useState(0)
  const [creando, setCreando] = useState(false)
  const [historial, setHistorial] = useState<CitationEvidenceReview[] | null>(null)
  const [cargandoHistorial, setCargandoHistorial] = useState(false)
  const [nota, setNota] = useState("")
  const [decidiendo, setDecidiendo] = useState(false)

  const cargarHistorial = useCallback(async (occurrenceId: string) => {
    if (numeroCapitulo === null) return
    setCargandoHistorial(true)
    try {
      setHistorial(await listCitationEvidence(projectId, numeroCapitulo, occurrenceId))
    } catch (cause) {
      setHistorial(null)
      setError(cause instanceof Error ? cause.message : "No se pudo cargar el historial de evidencia.")
    } finally {
      setCargandoHistorial(false)
    }
  }, [projectId, numeroCapitulo])

  const cargarVista = useCallback(async () => {
    if (numeroCapitulo === null) return
    setCargando(true)
    setError(null)
    try {
      setVista(await getChapterIeeeCitations(projectId, numeroCapitulo))
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        args.onUnauthorized()
        return
      }
      setVista(null)
      setError(cause instanceof Error ? cause.message : "No se pudo consultar la vista de citas IEEE.")
    } finally {
      setCargando(false)
    }
  }, [projectId, numeroCapitulo, args.onUnauthorized])

  useEffect(() => {
    if (activa) void cargarVista()
  }, [activa, cargarVista])

  /** Elegir (ocurrencia, fuente): fija el texto del párrafo (del borrador,
   * que coincide con la revisión del servidor porque los bloques citados
   * están bloqueados), carga extractos de esa fuente e historial. */
  const elegirOpcion = async (o: OpcionEvidencia) => {
    setOpcion(o)
    setExtractos(null)
    setExtractoId(null)
    setHistorial(null)
    setNotice(null)
    setError(null)
    const texto = textoDeParrafo(draft, o.blockId)
    setTextoClaim(texto)
    if (texto) {
      const rango = rangoAfirmacionInicial(texto, o.position)
      setClaimStart(rango.start)
      setClaimEnd(rango.end)
    }
    void cargarHistorial(o.occurrenceId)
    try {
      setExtractos((await listSourceExcerpts(projectId, o.sourceId)).excerpts)
    } catch (cause) {
      setExtractos(null)
      setError(cause instanceof Error ? cause.message : "No se pudieron cargar los extractos de la fuente.")
    }
  }

  /** Recalcula el rango de pasaje al elegir otro extracto. */
  const elegirExtracto = (e: SourceExcerpt) => {
    setExtractoId(e.excerpt_id)
    setExStart(0)
    setExEnd(utf16ACodePoints(e.text, e.text.length))
  }

  const crearCandidato = async () => {
    if (!opcion || extractoId === null || !args.esPropietario || creando || !textoClaim) return
    setCreando(true)
    setError(null)
    setNotice(null)
    try {
      await addCitationEvidence(
        projectId,
        numeroCapitulo as number,
        opcion.occurrenceId,
        {
          excerpt_id: extractoId,
          claim_start: claimStart,
          claim_end: claimEnd,
          excerpt_start: exStart,
          excerpt_end: exEnd,
          idempotency_key: crypto.randomUUID(),
        },
        args.csrfToken,
      )
      setNotice("Candidato de evidencia creado (CANDIDATE); queda pendiente de la decisión del asesor.")
      await cargarHistorial(opcion.occurrenceId)
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        args.onUnauthorized()
      } else {
        setError(cause instanceof Error ? cause.message : "No se pudo crear el candidato de evidencia.")
      }
    } finally {
      setCreando(false)
    }
  }

  const decidir = async (status: "SUPPORTS" | "CONTRADICTS" | "UNRELATED" | "INSUFFICIENT") => {
    const ultima = historial?.[historial.length - 1]
    if (!opcion || !ultima || !args.esAsesor || decidiendo) return
    setDecidiendo(true)
    setError(null)
    setNotice(null)
    try {
      await decideCitationEvidence(projectId, numeroCapitulo as number, ultima.review_id, {
        status,
        expected_version: ultima.review_version,
        idempotency_key: crypto.randomUUID(),
        note: nota,
      }, args.csrfToken)
      setNotice(`Decisión registrada: ${status}.`)
      await cargarHistorial(opcion.occurrenceId)
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        args.onUnauthorized()
      } else {
        setError(cause instanceof Error ? cause.message : "No se pudo registrar la decisión.")
      }
    } finally {
      setDecidiendo(false)
    }
  }

  return {
    vista, cargando, error, notice, opcion, textoClaim, extractos, extractoId,
    claimStart, claimEnd, exStart, exEnd, creando, historial, cargandoHistorial,
    nota, decidiendo,
    setClaimStart, setClaimEnd, setExStart, setExEnd, setNota,
    cargarVista, elegirOpcion, elegirExtracto, crearCandidato, decidir,
  }
}
