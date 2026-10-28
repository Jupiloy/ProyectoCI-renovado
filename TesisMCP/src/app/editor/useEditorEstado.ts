import { useEffect, useMemo, useRef, useState } from "react"
import type {
  ChapterCitation,
  ChapterContentTree,
  ChapterDocument,
  ChapterSnapshotDetailApi,
  ChapterSnapshotSummaryApi,
  ProjectSummary,
  ReviewComment,
  SourceDocument,
} from "../../api/types"
import { listSources } from "../../api/sources"
import { useCargaCapitulo } from "./carga"
import { estadoGuardado, getWorkflowRecursos } from "./etiquetas"
import { consultarVersionVigente, guardar } from "./guardado"
import { cambiarCapitulo } from "./operaciones"
import type { EditorCtx, Loaded, ModoDocumento, PendingSave } from "./tipos"
import { abrirModo, resolverObservacion } from "./versiones"

/**
 * Estado y acciones del editor del capítulo: navegación de capítulos, carga
 * del documento, borrador editable, guardado con verificación de versión,
 * snapshots y observaciones. La vista (VistaEditor) solo consume este bundle;
 * la lógica pesada vive en carga/guardado/versiones y el JSX en los paneles.
 */
export function useEditorEstado(args: {
  proyecto: ProjectSummary
  csrfToken: string
  onUnauthorized: () => void
  onAccessLost: () => void
  onRefreshCsrf: () => Promise<void>
}) {
  const { proyecto, csrfToken, onUnauthorized, onAccessLost, onRefreshCsrf } = args
  const projectId = proyecto.project_id

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
    getWorkflowRecursos(projectId).then(({ numeros }) => {
      if (!vigente) return
      setNumerosCapitulo(numeros)
      setNumeroCapitulo(numeros.length > 0 ? numeros[0] : null)
      if (numeros.length === 0) setLoading(false)
    })
    return () => {
      vigente = false
    }
  }, [projectId, setLoading])

  // Fuentes reales para el panel izquierdo (pestaña Fuentes).
  useEffect(() => {
    let vigente = true
    listSources(projectId)
      .then((lista) => {
        if (vigente) setFuentes(lista)
      })
      .catch(() => {
        if (vigente) setFuentes(null)
      })
    return () => {
      vigente = false
    }
  }, [projectId])

  const { cargarCapitulo } = useCargaCapitulo({
    projectId,
    onUnauthorized,
    onAccessLost,
    loadSequence,
    setLoading,
    setError,
    setNotice,
    setPending,
    setWriteBlocked,
    setServerDocument,
    setSnapshotDetalle,
    setModoDocumento,
    setLoaded,
    setDraft,
    setSnapshots,
    setComentarios,
  })

  useEffect(() => {
    if (numeroCapitulo === null) return
    void cargarCapitulo(numeroCapitulo)
  }, [numeroCapitulo, cargarCapitulo])

  const citasPorBloque = useMemo(() => {
    const map = new Map<string, ChapterCitation[]>()
    for (const cita of loaded?.document.citations ?? []) {
      map.set(cita.block_id, [...(map.get(cita.block_id) ?? []), cita])
    }
    return map
  }, [loaded])

  // Contexto del render vigente: lo consumen las acciones al producirse el
  // evento, con los mismos valores que un cierre en línea del render actual.
  const ctx: EditorCtx = {
    proyecto,
    csrfToken,
    numeroCapitulo,
    loaded,
    draft,
    pending,
    busy,
    writable,
    needsSave,
    hasLocalWork,
    modoDocumento,
    resolviendoId,
    loadSequence,
    cargarCapitulo,
    onUnauthorized,
    onAccessLost,
    onRefreshCsrf,
    setLoaded,
    setDraft,
    setPending,
    setWriteBlocked,
    setServerDocument,
    setLoading,
    setSaving,
    setError,
    setNotice,
    setSnapshots,
    setSnapshotDetalle,
    setCargandoVersion,
    setComentarios,
    setResolviendoId,
    setModoDocumento,
    setNumeroCapitulo,
  }

  const ejecutarGuardado = () => {
    void guardar(ctx)
  }
  const ejecutarConsulta = () => {
    void consultarVersionVigente(ctx)
  }
  const abrirVersion = (modo: ModoDocumento, snapshotId?: string) => {
    void abrirModo(ctx, modo, snapshotId)
  }
  const resolver = (c: ReviewComment) => {
    void resolverObservacion(ctx, c)
  }
  const recargarBorrador = () => {
    if (!hasLocalWork || window.confirm("Se descartarán los cambios locales o el intento pendiente. ¿Recargar del servidor?")) {
      void cargarCapitulo(numeroCapitulo as number)
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

  return {
    numerosCapitulo,
    numeroCapitulo,
    fuentes,
    loaded,
    draft,
    pending,
    serverDocument,
    modoDocumento,
    snapshotDetalle,
    cargandoVersion,
    loading,
    saving,
    error,
    notice,
    snapshots,
    comentarios,
    resolviendoId,
    citasPorBloque,
    abiertas,
    needsSave,
    writable,
    busy,
    modoSoloLectura,
    estadoGuardadoTexto,
    leftOpen,
    setLeftOpen,
    rightOpen,
    setRightOpen,
    leftTab,
    setLeftTab,
    rightTab,
    setRightTab,
    // setters que la vista enlaza a las operaciones de bloques del borrador
    setDraft,
    setPending,
    setNotice,
    cambiar: (numero: number) => cambiarCapitulo(ctx, numero),
    ejecutarGuardado,
    ejecutarConsulta,
    abrirVersion,
    resolver,
    recargarBorrador,
  }
}
