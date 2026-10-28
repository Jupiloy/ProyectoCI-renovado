import { useEffect, useRef, useState } from "react"
import type {
  AdvisorDashboardProject,
  ChapterSnapshotDetailApi,
  ChapterSnapshotSummaryApi,
  ChapterState,
  ReviewComment,
} from "../../api/types"
import { Icon } from "../base"
import { calcularAnclaje, type Anclaje } from "./anclaje"
import { useCargaRevision } from "./carga"
import { ComentariosMarginales } from "./ComentariosMarginales"
import { DocumentoRevision } from "./DocumentoRevision"
import { PanelVersionesAsesor } from "./PanelVersionesAsesor"
import { RevisionHeader } from "./RevisionHeader"
import {
  abrirVersionEnviada,
  decidirCapitulo,
  registrarObservacion,
  resolverComentarioAsesor,
  type RevisionCtx,
} from "./acciones"

/** Revisión del asesor sobre una versión concreta del capítulo: historial de
 * versiones, documento con anclaje por selección y decisiones (cambiar /
 * aprobar / reabrir). El estado y las acciones enlazadas viven aquí; la
 * lógica de red vive en carga.ts y acciones.ts, y el JSX en los subcomponentes. */
export function RevisionAsesor({
  sel,
  csrfToken,
  onUnauthorized,
  onAccessLost,
  onRefreshCsrf,
  alVolver,
  alRefrescar,
}: {
  sel: AdvisorDashboardProject
  csrfToken: string
  onUnauthorized: () => void
  onAccessLost: () => void
  onRefreshCsrf: () => Promise<void>
  alVolver: () => void
  alRefrescar: () => Promise<void>
}) {
  const [capituloNo, setCapituloNo] = useState<number>(sel.chapters[0]?.chapter_no ?? 1)
  const [estado, setEstado] = useState<ChapterState | null>(null)
  const [snapshots, setSnapshots] = useState<ChapterSnapshotSummaryApi[]>([])
  const [detalle, setDetalle] = useState<ChapterSnapshotDetailApi | null>(null)
  const [comentarios, setComentarios] = useState<ReviewComment[]>([])
  const [anclaje, setAnclaje] = useState<Anclaje | null>(null)
  const [cargandoDatos, setCargandoDatos] = useState(true)
  const [procesando, setProcesando] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [motivo, setMotivo] = useState("")
  const [versionAbierta, setVersionAbierta] = useState(true)
  const textoRef = useRef<HTMLDivElement | null>(null)
  const secuencia = useRef(0)

  const { cargar } = useCargaRevision({
    projectId: sel.project_id,
    onUnauthorized,
    onAccessLost,
    secuencia,
    setEstado,
    setSnapshots,
    setComentarios,
    setDetalle,
    setAnclaje,
    setCargandoDatos,
    setError,
    setNotice,
  })

  useEffect(() => {
    void cargar(capituloNo)
  }, [capituloNo, cargar])

  function capturarAnclaje() {
    if (!detalle || !textoRef.current) return
    const resultado = calcularAnclaje(detalle, textoRef.current)
    if (resultado.error) {
      setError(resultado.error)
      return
    }
    if (resultado.anclaje) {
      setAnclaje(resultado.anclaje)
      setError(null)
    }
  }

  // Contexto del render vigente para las acciones (mismos valores que un
  // cierre en línea del render actual).
  const ctx: RevisionCtx = {
    projectId: sel.project_id,
    capituloNo,
    csrfToken,
    procesando,
    motivo,
    anclaje,
    setEstado,
    setDetalle,
    setComentarios,
    setAnclaje,
    setProcesando,
    setError,
    setNotice,
    setMotivo,
    onUnauthorized,
    onAccessLost,
    onRefreshCsrf,
    alRefrescar,
  }

  const abiertas = comentarios.filter((c) => c.status === "OPEN").length

  if (cargandoDatos) {
    return (
      <main className="page">
        <div className="estado-pantalla" role="status">Cargando la revisión del proyecto…</div>
      </main>
    )
  }

  return (
    <main className="page review-page">
      <RevisionHeader
        estado={estado}
        capituloNo={capituloNo}
        nombreProyecto={sel.project_name}
        procesando={procesando}
        hayObservacionesAbiertas={abiertas > 0}
        motivo={motivo}
        onMotivo={setMotivo}
        onVolver={alVolver}
        onDecidir={(accion) => void decidirCapitulo(ctx, accion)}
      />

      {error && <div className="aviso aviso-error" role="alert">{error}</div>}
      {notice && <div className="aviso" role="status">{notice}</div>}

      <div className="review-toolbar">
        <label style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
          Capítulo
          <select value={capituloNo} onChange={(e) => setCapituloNo(Number(e.target.value))}>
            {sel.chapters.map((c) => (
              <option key={c.chapter_no} value={c.chapter_no}>Capítulo {c.chapter_no}</option>
            ))}
          </select>
        </label>
        <span className="toolbar-divider" />
        <button onClick={() => setVersionAbierta(!versionAbierta)}>
          <Icon name="document" size={16} /> Historial de versiones
        </button>
        <span className="open-comments">
          <span />{abiertas} observaciones abiertas
        </span>
      </div>

      <div className="review-workspace">
        {versionAbierta && (
          <PanelVersionesAsesor
            snapshots={snapshots}
            detalleId={detalle?.id ?? null}
            procesando={procesando}
            onAbrir={(s) => void abrirVersionEnviada(ctx, s)}
          />
        )}

        <DocumentoRevision
          detalle={detalle}
          anclaje={anclaje}
          motivo={motivo}
          onMotivo={setMotivo}
          procesando={procesando}
          textoRef={textoRef}
          onCapturarAnclaje={capturarAnclaje}
          onRegistrarObservacion={() => void registrarObservacion(ctx)}
          onCancelarAnclaje={() => { setAnclaje(null); setMotivo("") }}
        />

        <ComentariosMarginales
          comentarios={comentarios}
          abiertas={abiertas}
          procesando={procesando}
          onResolver={(c) => void resolverComentarioAsesor(ctx, c)}
        />
      </div>
    </main>
  )
}
