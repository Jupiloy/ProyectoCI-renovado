import { useEffect, useMemo, useState, type ReactNode } from "react"
import { getChapterState } from "../api/chapters"
import { getWorkflowState } from "../api/workflows"
import { listSources } from "../api/sources"
import type {
  ChapterState,
  ProjectState,
  ProjectSummary,
  SessionUser,
  WorkflowState,
} from "../api/types"
import {
  Button,
  Icon,
  StatusBadge,
  type IconNameTesis,
} from "./base"

/** Pantallas del espacio real de trabajo con el shell de la maqueta de Figma. */
export type PantallaApp = "tesis" | "editor" | "fuentes" | "asesor" | "revision"

const navItems: { id: PantallaApp; label: string; icon: IconNameTesis }[] = [
  { id: "tesis", label: "Mi tesis", icon: "home" },
  { id: "editor", label: "Editor", icon: "document" },
  { id: "fuentes", label: "Fuentes", icon: "library" },
  { id: "asesor", label: "Panel asesor", icon: "people" },
]

const topLabels: Record<PantallaApp, string> = {
  tesis: "Panel principal",
  editor: "Editor académico",
  fuentes: "Biblioteca científica",
  asesor: "Supervisión de tesistas",
  revision: "Revisión del capítulo",
}

function iniciales(nombre: string): string {
  const partes = nombre.trim().split(/\s+/).slice(0, 2)
  return partes.map((p) => p[0]?.toUpperCase() ?? "").join("") || "??"
}

function nivelRol(role: ProjectSummary["role"]): string {
  return role === "ADVISOR" ? "Asesor" : "Tesista"
}

export function AppShellTesis({
  pantalla,
  usuario,
  proyecto,
  detalles,
  alConmutar,
  alRecorrido,
  alVistaClasica,
  alDescargarBorrador,
  alCerrarSesion,
  children,
}: {
  pantalla: PantallaApp
  usuario: SessionUser
  proyecto: ProjectSummary
  detalles: ProjectState
  alConmutar: (pantalla: PantallaApp) => void
  alRecorrido: () => void
  alVistaClasica: () => void
  alDescargarBorrador: () => void
  alCerrarSesion: () => void
  children: ReactNode
}) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Icon name="book" size={21} />
          </div>
          <div>
            <b>TesisMCP</b>
            <span>Espacio académico</span>
          </div>
        </div>
        <nav className="main-nav">
          {navItems
            .filter((item) => item.id !== "asesor" || proyecto.role === "ADVISOR")
            .map((item) => (
              <button
                key={item.id}
                className={pantalla === item.id ? "nav-item active" : "nav-item"}
                onClick={() => alConmutar(item.id)}
              >
                <Icon name={item.icon} />
                <span>{item.label}</span>
              </button>
            ))}
          <button
            className="nav-item"
            type="button"
            disabled
            title="Se integra con la revisión de capítulo en los siguientes bloques del re-fitting (R3/R5)"
          >
            <Icon name="comment" />
            <span>Revisión</span>
          </button>
        </nav>
        <div className="sidebar-project">
          <span className="eyebrow">PROYECTO ACTIVO</span>
          <strong>{proyecto.title || proyecto.name}</strong>
          <span>
            {nivelRol(proyecto.role)} · Estado {detalles.state_version}
          </span>
        </div>
        <div className="sidebar-bottom">
          <button className="download-project" type="button" onClick={alDescargarBorrador}>
            <Icon name="download" />
            <span>Descargar borrador (DOCX)</span>
          </button>
          <button className="text-link" type="button" onClick={alVistaClasica}>
            Vista clásica del proyecto (respaldo)
          </button>
          <button className="profile" onClick={alCerrarSesion} title="Cerrar sesión">
            <div className="avatar">{iniciales(usuario.display_name)}</div>
            <div>
              <b>{usuario.display_name}</b>
              <span>{nivelRol(proyecto.role)} · Cerrar sesión</span>
            </div>
          </button>
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>Proyecto de tesis</span>
            <Icon name="chevron" size={13} />
            <strong>{topLabels[pantalla]}</strong>
          </div>
          <div className="top-actions">
            <button className="profile-trigger" onClick={alCerrarSesion} title="Cerrar sesión">
              <span className="avatar">{iniciales(usuario.display_name)}</span>
              <span>Cerrar sesión</span>
            </button>
          </div>
        </header>
        {children}
      </div>
    </div>
  )
}

const etiquetaPorEstado: Record<string, string> = {
  DRAFT: "Borrador",
  READY: "En revisión",
  CHANGES_REQUESTED: "Con observaciones",
  APPROVED: "Aprobado",
}

function saludoParaHora(): string {
  const hora = new Date().getHours()
  if (hora < 12) return "Buenos días"
  if (hora < 19) return "Buenas tardes"
  return "Buenas noches"
}

function mensajeDe(cause: unknown): string {
  return cause instanceof Error
    ? cause.message
    : "No se pudo cargar el avance del proyecto."
}

type CapituloVista = {
  numero: number
  etiqueta: string
  subtitulo: string
}

export function PanelPrincipal({
  usuario,
  proyecto,
  detalles,
  alContinuar,
  alRecorrido,
  alFuentes,
}: {
  usuario: SessionUser
  proyecto: ProjectSummary
  detalles: ProjectState
  alContinuar: () => void
  alRecorrido: () => void
  alFuentes: () => void
}) {
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null)
  const [estados, setEstados] = useState<Array<{ numero: number; estado: ChapterState | null }>>([])
  const [totalFuentes, setTotalFuentes] = useState<number | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let vigente = true
    async function cargar() {
      setCargando(true)
      setError("")
      const proyectoId = proyecto.project_id
      const w = await getWorkflowState(proyectoId)
      const tasksActivas = (w.published?.tasks ?? [])
        .filter((t) => t.is_active)
        .sort((a, b) => a.order_index - b.order_index)
      const numeros = Array.from(
        new Set(
          tasksActivas
            .map((t) => t.chapter_no)
            .filter((n): n is number => typeof n === "number"),
        ),
      ).sort((a, b) => a - b)
      const resultados = await Promise.allSettled(
        numeros.map((n) => getChapterState(proyectoId, n)),
      )
      if (!vigente) return
      setWorkflow(w)
      setEstados(
        numeros.map((numero, indice) => ({
          numero,
          estado:
            resultados[indice].status === "fulfilled"
              ? (resultados[indice] as PromiseFulfilledResult<ChapterState>).value
              : null,
        })),
      )
      setCargando(false)
    }
    cargar().catch((cause) => {
      if (vigente) {
        setError(mensajeDe(cause))
        setCargando(false)
      }
    })
    listSources(proyecto.project_id)
      .then((lista) => {
        if (vigente) setTotalFuentes(lista.length)
      })
      .catch(() => {
        if (vigente) setTotalFuentes(null)
      })
    return () => {
      vigente = false
    }
  }, [proyecto.project_id, detalles.state_version])

  const { totalActivas, completadas, proximo, capitulos, avisoP2627 } =
    useMemo(() => {
      const tasksActivas = (workflow?.published?.tasks ?? [])
        .filter((t) => t.is_active)
        .sort((a, b) => a.order_index - b.order_index)
      const completadosPorCodigo = new Set<string>()
      for (const item of estados) {
        if (!item.estado) continue
        for (const paso of item.estado.steps) {
          if (paso.status === "COMPLETED") completadosPorCodigo.add(paso.step_code)
        }
      }
      const pasoActualPorCapitulo = new Map<number, string>()
      for (const task of tasksActivas) {
        if (
          task.chapter_no !== null &&
          !completadosPorCodigo.has(task.legacy_step_code) &&
          !pasoActualPorCapitulo.has(task.chapter_no)
        ) {
          pasoActualPorCapitulo.set(task.chapter_no, task.title)
        }
      }
      const vistas: CapituloVista[] = estados.map(({ numero, estado }) => {
        const completados = (estado?.steps ?? []).filter(
          (p) => p.status === "COMPLETED",
        ).length
        let etiqueta = "No iniciado"
        if (estado) {
          etiqueta = etiquetaPorEstado[estado.status] ?? estado.status
          if (estado.status === "DRAFT" && completados > 0) etiqueta = "En progreso"
        }
        return {
          numero,
          etiqueta,
          subtitulo: pasoActualPorCapitulo.has(numero)
            ? `Paso actual: ${pasoActualPorCapitulo.get(numero)}`
            : completados > 0
              ? `${completados} pasos completados`
              : "—",
        }
      })
      const primeroPendiente = tasksActivas.find(
        (t) => !completadosPorCodigo.has(t.legacy_step_code),
      )
      return {
        totalActivas: tasksActivas.length,
        completadas: tasksActivas.filter((t) =>
          completadosPorCodigo.has(t.legacy_step_code),
        ).length,
        proximo: primeroPendiente ?? null,
        capitulos: vistas,
        avisoP2627: tasksActivas.some(
          (t) => t.legacy_step_code === "P26" || t.legacy_step_code === "P27",
        ),
      }
    }, [workflow, estados])

  if (cargando) {
    return (
      <main className="page">
        <div className="estado-pantalla" role="status">
          Cargando el avance real del proyecto…
        </div>
      </main>
    )
  }

  const publicado = workflow?.published
  const indiceProximo =
    proximo !== null
      ? (publicado?.tasks ?? [])
          .filter((t) => t.is_active)
          .sort((a, b) => a.order_index - b.order_index)
          .findIndex((t) => t.task_id === proximo.task_id)
      : -1

  return (
    <main className="page dashboard-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow blue">PROYECTO DE TESIS</span>
          <h1>{`${saludoParaHora()}, ${usuario.display_name.split(" ")[0]}`}</h1>
          <p>Continúa con tu investigación desde el último avance guardado.</p>
        </div>
        <Button icon="edit" onClick={alContinuar}>
          Continuar redactando
        </Button>
      </div>

      {error && (
        <div className="aviso aviso-error" role="alert">
          {error}
        </div>
      )}

      <section className="project-summary">
        <div>
          <span className="eyebrow">TÍTULO PROVISIONAL</span>
          <h2>{detalles.title || detalles.name}</h2>
        </div>
        <div className="progress-block">
          <div className="progress-number">
            {completadas} <span>de {totalActivas} pasos</span>
          </div>
          <div className="progress-track">
            <span
              style={
                totalActivas > 0
                  ? { width: `${Math.round((completadas / totalActivas) * 100)}%` }
                  : undefined
              }
            />
          </div>
          <small>
            {totalActivas > 0
              ? `Ruta metodológica activa: ${totalActivas} tarea${totalActivas === 1 ? "" : "s"}`
              : "El recorrido del proyecto no tiene tareas activas publicadas"}
          </small>
        </div>
      </section>

      <div className="dashboard-grid">
        <section className="section-card">
          <div className="section-title">
            <div>
              <h2>Avance por capítulos</h2>
              <p>Estado actual de la estructura de tu tesis</p>
            </div>
            <button className="text-link" onClick={alRecorrido}>
              Ver metodología <Icon name="chevron" size={14} />
            </button>
          </div>
          {capitulos.length === 0 ? (
            <p className="aviso">
              El recorrido publicado no asigna capítulos con número. Revisa la
              metodología del proyecto.
            </p>
          ) : (
            <div className="chapter-list">
              {capitulos.map((capitulo) => (
                <button className="chapter-row" key={capitulo.numero} onClick={alContinuar}>
                  <span className="chapter-number">{capitulo.numero}</span>
                  <div>
                    <strong>Capítulo {capitulo.numero}</strong>
                    <small>{capitulo.subtitulo}</small>
                  </div>
                  <StatusBadge>{capitulo.etiqueta}</StatusBadge>
                  <Icon name="chevron" size={15} />
                </button>
              ))}
            </div>
          )}
        </section>
        <aside className="dashboard-aside">
          <section className="next-step">
            <div className="step-icon">
              <Icon name="spark" />
            </div>
            <span className="eyebrow blue">PRÓXIMO PASO RECOMENDADO</span>
            {proximo ? (
              <>
                <h3>{proximo.title}</h3>
                <p>{proximo.description}</p>
                <div className="step-meta">
                  <span>
                    Paso {indiceProximo + 1} de {totalActivas}
                  </span>
                  <span>
                    {proximo.chapter_no === null
                      ? "General"
                      : `Capítulo ${proximo.chapter_no}`}
                  </span>
                </div>
                <Button onClick={alContinuar}>Comenzar paso</Button>
              </>
            ) : (
              <p>
                No hay pasos pendientes calculados. Esto ocurre cuando el
                recorrido no está publicado o todas las tareas activas ya están
                completadas.
              </p>
            )}
          </section>
          <section className="methodology-card">
            <span className="eyebrow blue">RECORRIDO VIGENTE</span>
            {publicado ? (
              <>
                <h3>{totalActivas} pasos seleccionados</h3>
                <p>
                  Versión {publicado.version_no} del recorrido del proyecto.
                  {avisoP2627 &&
                    " P26 y P27 quedan señalados para definición conjunta con el profesor."}
                </p>
              </>
            ) : (
              <p>
                El proyecto aún no tiene una versión publicada del recorrido
                metodológico.
              </p>
            )}
            <button className="text-link" onClick={alRecorrido}>
              Revisar recorrido y prompts <Icon name="chevron" size={14} />
            </button>
          </section>
          <section className="quick-access">
            <h3>Accesos rápidos</h3>
            <button onClick={alFuentes}>
              <Icon name="library" />
              <span>
                <b>Fuentes</b>
                <small>
                  {totalFuentes === null
                    ? "Fuentes del proyecto"
                    : totalFuentes === 0
                      ? "Aún no hay fuentes cargadas"
                      : `${totalFuentes} fuente${totalFuentes === 1 ? "" : "s"} cargada${totalFuentes === 1 ? "" : "s"}`}
                </small>
              </span>
              <Icon name="chevron" />
            </button>
          </section>
        </aside>
      </div>
    </main>
  )
}
