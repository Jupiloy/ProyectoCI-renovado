import { useState, type ReactNode } from "react"

type Screen = "student" | "editor" | "library" | "advisor" | "review"
type IconName = "book" | "chevron" | "comment" | "document" | "download" | "edit" | "home" | "library" | "more" | "people" | "plus" | "search" | "settings" | "spark" | "upload" | "x"

const iconPaths: Record<IconName, ReactNode> = {
  home: (
    <>
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5.5 9.5V21h13V9.5M9 21v-7h6v7" />
    </>
  ),
  document: (
    <>
      <path d="M6 2.5h8l4 4V21H6z" />
      <path d="M14 2.5v4h4M9 11h6M9 15h6" />
    </>
  ),
  library: (
    <>
      <path d="M4 4h4v16H4zM10 4h4v16h-4zM16.5 5l3.5-1 3.5 15-3.5 1z" />
    </>
  ),
  people: (
    <>
      <circle cx="9" cy="8" r="3" />
      <path d="M3 20c0-4 2-6 6-6s6 2 6 6M16 4.5a3 3 0 0 1 0 6M17 14c2.7.4 4 2.4 4 5" />
    </>
  ),
  comment: <path d="M4 4h16v12H9l-5 4z" />,
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" />
    </>
  ),
  chevron: <path d="m9 18 6-6-6-6" />,
  plus: <path d="M12 5v14M5 12h14" />,
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </>
  ),
  edit: (
    <>
      <path d="m4 20 4.2-1 10.9-10.9-3.2-3.2L5 15.8zM14.8 6l3.2 3.2" />
    </>
  ),
  spark: (
    <>
      <path d="m12 3 1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4zM18.5 15l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z" />
    </>
  ),
  book: (
    <>
      <path d="M3 5.5A4.5 4.5 0 0 1 7.5 4H11v16H7.5A4.5 4.5 0 0 0 3 21.5zM21 5.5A4.5 4.5 0 0 0 16.5 4H13v16h3.5a4.5 4.5 0 0 1 4.5 1.5z" />
    </>
  ),
  upload: (
    <>
      <path d="M12 16V4M7 9l5-5 5 5M4 15v5h16v-5" />
    </>
  ),
  download: (
    <>
      <path d="M12 4v12M7 11l5 5 5-5M4 20h16" />
    </>
  ),
  more: (
    <>
      <circle cx="5" cy="12" r="1" />
      <circle cx="12" cy="12" r="1" />
      <circle cx="19" cy="12" r="1" />
    </>
  ),
  x: <path d="m6 6 12 12M18 6 6 18" />,
}

function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {iconPaths[name]}
    </svg>
  )
}

function Button({
  children,
  variant = "primary",
  icon,
  disabled,
  onClick,
}: {
  children: ReactNode
  variant?: "primary" | "secondary" | "danger" | "ghost"
  icon?: IconName
  disabled?: boolean
  onClick?: () => void
}) {
  return (
    <button
      className={`button button-${variant}`}
      disabled={disabled}
      onClick={onClick}
    >
      {icon && <Icon name={icon} size={16} />}
      <span>{children}</span>
    </button>
  )
}

const statusMap: Record<string, string> = {
  "No iniciado": "neutral",
  "En progreso": "blue",
  "En revisión": "violet",
  "Con observaciones": "danger",
  Aprobado: "success",
  Pendiente: "warning",
  "Texto completo disponible": "blue",
  "Texto completo disponible (demo)": "blue",
  "Pendiente de revisión (demo)": "warning",
  "Solo metadatos (demo)": "neutral",
  "Solo metadatos": "neutral",
  "Pendiente de revisión": "warning",
  Demostración: "warning",
}

function StatusBadge({
  children,
  dot = true,
}: {
  children: string
  dot?: boolean
}) {
  const tone = statusMap[children] || "neutral"
  return (
    <span className={`status status-${tone}`}>
      {dot && <span className="status-dot" />}
      {children}
    </span>
  )
}

function TopBar({
  screen,
  onExport,
  onLogout,
  onExitDemo,
}: {
  screen: Screen
  onExport: () => void
  onLogout: () => void
  onExitDemo: () => void
}) {
  const labels: Record<Screen, string> = {
    student: "Panel principal",
    editor: "Editor metodológico",
    library: "Biblioteca científica",
    advisor: "Supervisión de tesistas",
    review: "Revisión del capítulo",
  }
  return (
    <header className="topbar">
      <div className="breadcrumbs">
        <span>Proyecto de tesis</span>
        <Icon name="chevron" size={13} />
        <strong>{labels[screen]}</strong>
      </div>
      <div className="top-actions">
        <span className="demo-pill">MODO DEMOSTRACIÓN</span>
        <button className="demo-exit-button" type="button" onClick={onExitDemo}>Salir de demostración</button>
        <span className="save-indicator">
          <span className="save-dot" />
          Guardado hace unos segundos
        </span>
        {screen === "editor" && (
          <Button variant="secondary" icon="download" onClick={onExport}>
            Exportar
          </Button>
        )}
        <button className="icon-button" aria-label="Más opciones">
          <Icon name="more" />
        </button>
        <button className="profile-trigger" onClick={onLogout} title="Cerrar sesión">
          <span className="avatar">LC</span>
          <span>Cerrar sesión</span>
        </button>
      </div>
    </header>
  )
}

const navItems: { id: Screen; label: string; icon: IconName }[] = [
  { id: "student", label: "Mi tesis", icon: "home" },
  { id: "editor", label: "Editor", icon: "document" },
  { id: "library", label: "Fuentes", icon: "library" },
  { id: "advisor", label: "Panel asesor", icon: "people" },
  { id: "review", label: "Revisión", icon: "comment" },
]

function Sidebar({
  screen,
  setScreen,
  onLogout,
}: {
  screen: Screen
  setScreen: (screen: Screen) => void
  onLogout: () => void
}) {
  return (
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
        {navItems.map((item) => (
          <button
            key={item.id}
            className={screen === item.id ? "nav-item active" : "nav-item"}
            onClick={() => setScreen(item.id)}
          >
            <Icon name={item.icon} />
            <span>{item.label}</span>
            {item.id === "review" && <span className="nav-count">3</span>}
          </button>
        ))}
      </nav>
      <div className="sidebar-project">
        <span className="eyebrow">PROYECTO ACTIVO · DEMO</span>
        <strong>Adopción de plataformas digitales en estudiantes</strong>
        <span>Licenciatura · 2025</span>
      </div>
      <div className="sidebar-bottom">
        <a className="download-project" href="/TesisMCP-source.zip" download>
          <Icon name="download" />
          <span>Descargar código</span>
        </a>
        <button className="nav-item">
          <Icon name="settings" />
          <span>Configuración</span>
        </button>
        <button className="profile" onClick={onLogout} title="Cerrar sesión">
          <div className="avatar">LC</div>
          <div>
            <b>Lucía Campos</b>
            <span>Tesista · Cerrar sesión</span>
          </div>
        </button>
      </div>
    </aside>
  )
}

const chapters = [
  ["1", "Planteamiento del problema", "Aprobado"],
  ["2", "Marco teórico", "En progreso"],
  ["3", "Marco metodológico", "Con observaciones"],
  ["4", "Resultados", "No iniciado"],
  ["5", "Discusión", "No iniciado"],
  ["6", "Conclusiones", "No iniciado"],
  ["7", "Referencias y anexos", "No iniciado"],
]

function StudentDashboard({ goEditor }: { goEditor: () => void }) {
  const [methodologyOpen, setMethodologyOpen] = useState(false)
  return (
    <main className="page dashboard-page">
      <div className="demo-notice">
        <Icon name="spark" size={16} />
        <span>
          <b>Vista de demostración.</b> El avance, las actividades y las
          observaciones mostradas son datos de ejemplo, no datos del backend.
        </span>
      </div>
      <div className="page-heading">
        <div>
          <span className="eyebrow blue">PROYECTO DE TESIS</span>
          <h1>Buenos días, Lucía</h1>
          <p>Continúa con tu investigación desde el último avance guardado.</p>
        </div>
        <Button icon="edit" onClick={goEditor}>
          Continuar redactando
        </Button>
      </div>
      <section className="project-summary">
        <div>
          <span className="eyebrow">TÍTULO PROVISIONAL</span>
          <h2>
            Adopción de plataformas digitales y hábitos de estudio en
            estudiantes universitarios
          </h2>
          <div className="meta-row">
            <span>Universidad Nacional</span>
            <span>Educación</span>
            <span>Asesor: Dr. Roberto Salas</span>
          </div>
        </div>
        <div className="progress-block">
          <div className="progress-number">
            8 <span>de 32 pasos</span>
          </div>
          <div className="progress-track">
            <span />
          </div>
          <small>Ruta metodológica completada</small>
        </div>
      </section>
      {methodologyOpen && (
        <section className="methodology-config">
          <div className="section-title">
            <div>
              <span className="eyebrow blue">CONFIGURACIÓN DE DEMOSTRACIÓN</span>
              <h2>Recorrido metodológico del proyecto</h2>
              <p>
                Versión demo-v3 · 7 pasos activos de un catálogo disponible de 32
              </p>
            </div>
            <Button
              variant="secondary"
              onClick={() => setMethodologyOpen(false)}
            >
              Cerrar
            </Button>
          </div>
          <div className="methodology-warning">
            <Icon name="comment" size={16} />
            Cambiar el orden puede afectar dependencias y versiones ya enviadas.
            En producción esta acción requerirá permisos y una confirmación.
          </div>
          <div className="methodology-steps">
            {[
              ["P08", "Bases teóricas", "Depende de P04 · Activo"],
              ["P12", "Hipótesis y categorías", "Depende de P08 · Activo"],
              ["P18", "Diseño metodológico", "Depende de P12 · Activo"],
              ["P26", "Definición pendiente con profesor", "Sin decisión"],
              ["P27", "Definición pendiente con profesor", "Sin decisión"],
            ].map(([code, name, dependency]) => (
              <div key={code}>
                <span className="step-handle">⋮⋮</span>
                <b>{code}</b>
                <span>{name}</span>
                <small>{dependency}</small>
                <button>Editar prompt</button>
              </div>
            ))}
          </div>
          <p className="permission-note">
            Vista de tesista: puede proponer ajustes. La edición definitiva queda
            sujeta a los permisos configurados en el backend.
          </p>
        </section>
      )}
      <div className="dashboard-grid">
        <section className="section-card chapters-card">
          <div className="section-title">
            <div>
              <h2>Avance por capítulos</h2>
              <p>Estado actual de la estructura de tu tesis</p>
            </div>
            <button className="text-link">
              Ver metodología <Icon name="chevron" size={14} />
            </button>
          </div>
          <div className="chapter-list">
            {chapters.map(([n, title, status]) => (
              <button
                className="chapter-row"
                key={n}
                onClick={status === "En progreso" ? goEditor : undefined}
              >
                <span className="chapter-number">{n}</span>
                <div>
                  <strong>{title}</strong>
                  <small>
                    {n === "2"
                      ? "Paso actual: Bases teóricas"
                      : n === "1"
                        ? "6 pasos completados"
                        : "—"}
                  </small>
                </div>
                <StatusBadge>{status}</StatusBadge>
                <Icon name="chevron" size={15} />
              </button>
            ))}
          </div>
        </section>
        <aside className="dashboard-aside">
          <section className="next-step">
            <div className="step-icon">
              <Icon name="spark" />
            </div>
            <span className="eyebrow blue">PRÓXIMO PASO RECOMENDADO</span>
            <h3>Construye las bases teóricas</h3>
            <p>
              Define los conceptos centrales y compáralos usando las fuentes
              verificadas de tu biblioteca.
            </p>
            <div className="step-meta">
              <span>Paso 9 de 32</span>
              <span>Capítulo 2</span>
            </div>
            <Button onClick={goEditor}>Comenzar paso</Button>
          </section>
          <section className="methodology-card">
            <span className="eyebrow blue">RECORRIDO VIGENTE · DEMO</span>
            <h3>7 pasos seleccionados del catálogo de 32</h3>
            <p>
              El orden y las dependencias pertenecen al proyecto. P26 y P27
              quedan señalados para definición conjunta con el profesor.
            </p>
            <button
              className="text-link"
              onClick={() => setMethodologyOpen(true)}
            >
              Revisar recorrido y prompts <Icon name="chevron" size={14} />
            </button>
          </section>
          <section className="quick-access">
            <h3>Accesos rápidos</h3>
            <button>
              <Icon name="library" />
              <span>
                <b>Fuentes</b>
                <small>12 documentos de ejemplo · demo</small>
              </span>
              <Icon name="chevron" />
            </button>
            <button>
              <Icon name="comment" />
              <span>
                <b>Observaciones</b>
                <small>3 pendientes de atender</small>
              </span>
              <span className="count-badge">3</span>
            </button>
          </section>
        </aside>
      </div>
    </main>
  )
}

const sources = [
  [
    "Documento académico de ejemplo A.pdf",
    "Texto completo disponible",
    "Contenido demo",
    true,
  ],
  [
    "Documento académico de ejemplo B.pdf",
    "Texto completo disponible",
    "Contenido demo",
    true,
  ],
  [
    "Competencias digitales docentes.pdf",
    "Pendiente de revisión",
    "16 págs.",
    false,
  ],
  ["Informe regional de educación 2023", "Solo metadatos", "Referencia", false],
]

function SourceRow({
  source,
  compact = false,
}: {
  source: (string | boolean)[]
  compact?: boolean
}) {
  const [name, status, detail, checked] = source
  return (
    <label className={`source-row ${compact ? "compact" : ""}`}>
      <input type="checkbox" defaultChecked={Boolean(checked)} />
      <span className="pdf-icon">PDF</span>
      <span className="source-copy">
        <b>{String(name)}</b>
        <small>{String(detail)}</small>
        <StatusBadge dot={false}>{String(status)}</StatusBadge>
      </span>
      <button className="row-more">
        <Icon name="more" size={17} />
      </button>
    </label>
  )
}

function AssistantMessage() {
  return (
    <div className="assistant-message">
      <div className="message-author">
        <div className="assistant-avatar">
          <Icon name="spark" size={15} />
        </div>
        <b>Asistente metodológico</b>
      </div>
      <span className="demo-response-label">INTERACCIÓN DE DEMOSTRACIÓN</span>
      <p>
        El servicio de respuesta automática todavía no está conectado. Cuando
        exista un contrato validado, aquí aparecerán propuestas separadas de la
        evidencia localizada.
      </p>
      <blockquote>
        No hay un pasaje, autor ni página verificados para esta afirmación.
      </blockquote>
      <small className="ai-note">
        Ningún cambio se insertará en el documento sin una decisión explícita
        del usuario.
      </small>
      <div className="message-actions">
        <Button variant="secondary" disabled>
          Esperando servicio
        </Button>
      </div>
    </div>
  )
}

function AdvisorComment({ resolved = false }: { resolved?: boolean }) {
  return (
    <article className={`advisor-comment ${resolved ? "resolved" : ""}`}>
      <div className="comment-head">
        <div className="avatar advisor-avatar">RS</div>
        <div>
          <b>Dr. Roberto Salas</b>
          <span>{resolved ? "Atendida · 14 may." : "Hoy, 09:42"}</span>
        </div>
        <StatusBadge dot={false}>
          {resolved ? "Aprobado" : "Pendiente"}
        </StatusBadge>
      </div>
      <p>
        {resolved
          ? "Bien resuelta la delimitación. Mantén este criterio en el resto del capítulo."
          : "Precisa qué entiendes por “uso planificado” y vincúlalo con la dimensión de autonomía definida en el marco teórico."}
      </p>
      {!resolved && (
        <>
          <div className="anchored-quote">
            “...el uso planificado de plataformas digitales...”
          </div>
          <textarea placeholder="Responder al asesor..." />
          <div className="comment-actions">
            <Button variant="secondary">Responder</Button>
            <button className="text-link">Marcar como atendida</button>
          </div>
        </>
      )}
    </article>
  )
}

function TrackChange({
  onAccept,
  onDiscard,
}: {
  onAccept: () => void
  onDiscard: () => void
}) {
  return (
    <div className="track-change">
      <div className="change-label">
        <Icon name="spark" size={14} /> Sugerencia de redacción
      </div>
      <p>
        <span className="deleted">
          Las plataformas digitales son muy importantes para todos los
          estudiantes hoy.
        </span>{" "}
        <span className="inserted">
          Las plataformas digitales constituyen un entorno relevante para la
          organización y el desarrollo autónomo del aprendizaje universitario.
        </span>
      </p>
      <div className="change-actions">
        <Button onClick={onAccept}>Aceptar</Button>
        <Button variant="secondary" onClick={onDiscard}>
          Descartar
        </Button>
      </div>
    </div>
  )
}

function Editor({ openCitation }: { openCitation: () => void }) {
  const [leftTab, setLeftTab] = useState<"outline" | "sources">("outline")
  const [rightTab, setRightTab] = useState<"sources" | "assistant" | "comments">(
    "sources",
  )
  const [showChange, setShowChange] = useState(true)
  const [leftOpen, setLeftOpen] = useState(true)
  const [rightOpen, setRightOpen] = useState(true)
  const [documentMode, setDocumentMode] = useState<
    "draft" | "submitted" | "snapshot"
  >("draft")
  return (
    <main className="editor-page">
      <div className="editor-titlebar">
        <div>
          <b>Capítulo 2. Marco teórico</b>
          <span>Versión de demostración</span>
          <div className="document-modes">
            <button
              className={documentMode === "draft" ? "active" : ""}
              onClick={() => setDocumentMode("draft")}
            >
              Borrador editable
            </button>
            <button
              className={documentMode === "submitted" ? "active" : ""}
              onClick={() => setDocumentMode("submitted")}
            >
              Enviada al asesor
            </button>
            <button
              className={documentMode === "snapshot" ? "active" : ""}
              onClick={() => setDocumentMode("snapshot")}
            >
              Snapshot
            </button>
          </div>
        </div>
        <div className="document-status">
          <span className="save-dot" />
          Guardado local · demo
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
        <select aria-label="Estilo de texto" defaultValue="Normal">
          <option>Normal</option>
          <option>Título 1</option>
          <option>Título 2</option>
        </select>
        <span className="toolbar-divider" />
        <button aria-label="Negrita">
          <b>B</b>
        </button>
        <button aria-label="Cursiva">
          <i>I</i>
        </button>
        <button aria-label="Lista">≡</button>
        <button aria-label="Lista numerada">1.</button>
        <span className="toolbar-divider" />
        <button className="toolbar-label" onClick={openCitation}>
          <Icon name="book" size={16} /> Insertar cita
        </button>
        <button className="toolbar-label">
          <Icon name="comment" size={16} /> Comentar
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
        {leftOpen && <aside className="editor-left">
          <div className="panel-tabs">
            <button
              className={leftTab === "outline" ? "active" : ""}
              onClick={() => setLeftTab("outline")}
            >
              Estructura
            </button>
            <button
              className={leftTab === "sources" ? "active" : ""}
              onClick={() => setLeftTab("sources")}
            >
              Fuentes <span>4</span>
            </button>
          </div>
          {leftTab === "outline" ? (
            <div className="outline-tree">
              <div className="outline-progress">
                <span>8 de 32 pasos</span>
                <div>
                  <i />
                </div>
              </div>
              <button className="outline-chapter done">
                <Icon name="chevron" size={13} />
                <span>
                  <b>1. Planteamiento del problema</b>
                  <small>6 de 6 pasos</small>
                </span>
              </button>
              <button className="outline-chapter active">
                <Icon name="chevron" size={13} />
                <span>
                  <b>2. Marco teórico</b>
                  <small>2 de 7 pasos</small>
                </span>
              </button>
              <div className="outline-steps">
                <button className="done">
                  <span>✓</span>2.1 Antecedentes
                </button>
                <button className="current">
                  <span>2</span>2.2 Bases teóricas
                </button>
                <button>
                  <span>3</span>2.3 Definición de términos
                </button>
                <button>
                  <span>4</span>2.4 Hipótesis
                </button>
              </div>
              {[
                "3. Marco metodológico",
                "4. Resultados",
                "5. Discusión",
                "6. Conclusiones",
                "7. Referencias y anexos",
              ].map((title) => (
                <button className="outline-chapter" key={title}>
                  <Icon name="chevron" size={13} />
                  <span>
                    <b>{title}</b>
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="sources-panel">
              <p>Activa las fuentes que puede consultar el asistente.</p>
              {sources.map((source, i) => (
                <SourceRow key={i} source={source} compact />
              ))}
              <Button variant="secondary" icon="plus">
                Añadir fuente
              </Button>
            </div>
          )}
        </aside>}
        <section className="document-area">
          <div className="page-ruler">
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
          <article
            className={`paper ${documentMode !== "draft" ? "read-only" : ""}`}
            contentEditable={documentMode === "draft"}
            suppressContentEditableWarning
          >
            {documentMode !== "draft" && (
              <div className="read-only-banner">
                {documentMode === "submitted"
                  ? "Versión enviada: solo lectura"
                  : "Snapshot histórico: solo lectura"}
              </div>
            )}
            <span className="page-number">24</span>
            <p className="paper-kicker">CAPÍTULO II</p>
            <h1>Marco teórico</h1>
            <h2>2.2 Bases teóricas</h2>
            <h3>2.2.1 Plataformas digitales y aprendizaje autónomo</h3>
            <p>
              La incorporación de plataformas digitales en la educación superior
              ha modificado las formas en que los estudiantes organizan, acceden
              y desarrollan sus actividades académicas. Estas herramientas no
              solo facilitan la disponibilidad de contenidos, sino que también
              configuran nuevos espacios para la interacción y el seguimiento
              del aprendizaje.
            </p>
            {showChange ? (
              <TrackChange
                onAccept={() => setShowChange(false)}
                onDiscard={() => setShowChange(false)}
              />
            ) : (
              <p>
                Las plataformas digitales constituyen un entorno relevante para
                la organización y el desarrollo autónomo del aprendizaje
                universitario.
              </p>
            )}
            <p>
              Desde una perspectiva pedagógica, la autonomía se comprende como
              la capacidad del estudiante para establecer metas, seleccionar
              estrategias y evaluar sus propios resultados. En este proceso, la
              mediación tecnológica puede ampliar las oportunidades de
              autorregulación siempre que exista una intención formativa clara{" "}
              <span className="inline-citation">
                [Referencia IEEE pendiente de revisión]
              </span>
              .
            </p>
            <div className="selected-text">
              El uso planificado de plataformas digitales contribuye a
              fortalecer hábitos de estudio sostenidos.
              <div className="selection-menu">
                <button>
                  <Icon name="spark" size={14} />
                  Mejorar redacción
                </button>
                <button>Sintetizar</button>
                <button>Buscar respaldo</button>
                <button onClick={openCitation}>Insertar cita</button>
              </div>
            </div>
            <p>
              Por tanto, su valor no depende únicamente de la disponibilidad
              técnica, sino de las prácticas académicas que orientan su uso.
            </p>
          </article>
        </section>
        {rightOpen && <aside className="editor-right">
          <div className="panel-tabs right-tabs">
            <button
              className={rightTab === "sources" ? "active" : ""}
              onClick={() => setRightTab("sources")}
            >
              Consultar fuentes
            </button>
            <button
              className={rightTab === "assistant" ? "active" : ""}
              onClick={() => setRightTab("assistant")}
            >
              Propuestas
            </button>
            <button
              className={rightTab === "comments" ? "active" : ""}
              onClick={() => setRightTab("comments")}
            >
              Observaciones <span>3</span>
            </button>
          </div>
          {rightTab === "sources" ? (
            <div className="source-consultation">
              <div className="context-strip">
                <Icon name="library" size={15} />
                <span>
                  <b>2 documentos seleccionados · demo</b>
                  <small>Sin servicio de consulta conectado</small>
                </span>
              </div>
              <div className="consultation-empty">
                <div className="step-icon">
                  <Icon name="search" />
                </div>
                <h3>Busca respaldo para una afirmación</h3>
                <p>
                  Selecciona texto en la hoja para localizar evidencia en los
                  documentos activos. Primero se mostrará la fuente localizada,
                  luego la propuesta del agente y finalmente tu decisión.
                </p>
                <div className="evidence-stages">
                  <span>1 · Fuente localizada</span>
                  <span>2 · Propuesta del agente</span>
                  <span>3 · Decisión del usuario</span>
                </div>
                <Button variant="secondary" disabled>
                  Consulta no conectada
                </Button>
              </div>
              <div className="chat-input">
                <textarea
                  disabled
                  placeholder="Conecta el servicio para preguntar sobre las fuentes..."
                />
                <div>
                  <span>Demostración · sin respuesta automática</span>
                </div>
              </div>
            </div>
          ) : rightTab === "assistant" ? (
            <>
              <div className="context-strip">
                <Icon name="library" size={15} />
                <span>
                  <b>Agente opcional · no conectado</b>
                  <small>Las propuestas requieren confirmación</small>
                </span>
                <button>Gestionar</button>
              </div>
              <div className="chat-body">
                <div className="user-message">
                  ¿Cómo puedo sustentar mejor la relación entre plataformas
                  digitales y autonomía?
                </div>
                <AssistantMessage />
              </div>
              <div className="chat-input">
                <textarea placeholder="Pregunta sobre tu capítulo o fuentes..." />
                <div>
                  <span>Solo fuentes activas</span>
                  <button aria-label="Enviar">
                    <Icon name="chevron" size={17} />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="comments-summary">
                <b>3 observaciones abiertas</b>
                <span>Capítulo 2 · Versión 12</span>
              </div>
              <div className="comments-list">
                <AdvisorComment />
                <AdvisorComment resolved />
              </div>
            </>
          )}
        </aside>}
      </div>
    </main>
  )
}

const libraryRows = [
  [
    "Documento académico de ejemplo A",
    "Autoría no conectada",
    "—",
    "Carga local de demostración",
    "Nacional",
    "Texto completo disponible (demo)",
  ],
  [
    "Documento académico de ejemplo B",
    "Autoría no conectada",
    "—",
    "Carga local de demostración",
    "Local",
    "Texto completo disponible (demo)",
  ],
  [
    "Resultado pendiente de revisar",
    "Metadatos de ejemplo",
    "—",
    "Importación asistida",
    "Nacional",
    "Pendiente de revisión (demo)",
  ],
  [
    "Resultado con metadatos únicamente",
    "Metadatos de ejemplo",
    "—",
    "Catálogo de demostración",
    "Internacional",
    "Solo metadatos (demo)",
  ],
]

function Library() {
  const [selected, setSelected] = useState(0)
  return (
    <main className="page library-page">
      <div className="demo-notice">
        <Icon name="spark" size={16} />
        <span>
          <b>Biblioteca de demostración.</b> Los documentos, autores, pasajes y
          estados de esta vista son ejemplos visuales. No representan resultados
          recuperados de Scopus, Web of Science o Zotero.
        </span>
      </div>
      <div className="page-heading">
        <div>
          <h1>Biblioteca científica</h1>
          <p>Busca, verifica y organiza las fuentes de tu investigación.</p>
        </div>
        <div className="heading-actions">
          <Button variant="secondary">Conectar Zotero</Button>
          <Button icon="upload">Subir PDF</Button>
        </div>
      </div>
      <div className="search-box">
        <Icon name="search" />
        <input placeholder="Buscar por título, autor, institución o palabra clave" />
        <Button>Buscar</Button>
      </div>
      <div className="filter-bar">
        <span>Filtrar por</span>
        {["Autor", "Año", "Institución", "Ámbito", "Nivel de verificación"].map(
          (x) => (
            <button key={x}>
              {x}
              <span>⌄</span>
            </button>
          ),
        )}
        <button className="text-link">Limpiar filtros</button>
      </div>
      <div className="library-layout">
        <section className="results-panel">
          <div className="results-head">
            <div>
              <h2>Resultados de búsqueda</h2>
              <p>4 fuentes encontradas · sin referencias generadas</p>
            </div>
            <select>
              <option>Más relevantes</option>
              <option>Más recientes</option>
            </select>
          </div>
          <div className="source-table">
            <div className="table-head">
              <span>Título y autoría</span>
              <span>Año</span>
              <span>Procedencia</span>
              <span>Verificación</span>
            </div>
            {libraryRows.map((row, i) => (
              <button
                className={`table-row ${selected === i ? "selected" : ""}`}
                key={row[0]}
                onClick={() => setSelected(i)}
              >
                <div>
                  <b>{row[0]}</b>
                  <small>{row[1]}</small>
                </div>
                <span>{row[2]}</span>
                <div>
                  <b>{row[3]}</b>
                  <small>{row[4]}</small>
                </div>
                <StatusBadge>{row[5]}</StatusBadge>
              </button>
            ))}
          </div>
        </section>
        <aside className="preview-panel">
          <div className="preview-head">
            <div>
              <span className="pdf-icon">PDF</span>
              <div>
                <b>Vista previa</b>
                <small>Documento de demostración · ubicación no disponible</small>
              </div>
            </div>
            <button className="icon-button">
              <Icon name="more" />
            </button>
          </div>
          <div className="pdf-preview">
            <div className="fake-pdf">
              <b>Vista de documento pendiente de conexión</b>
              <span />
              <span />
              <span className="short" />
              <p>No hay texto extraído ni pasajes verificables en la demostración.</p>
              <span />
              <span className="short" />
              <small>47</small>
            </div>
          </div>
          <div className="fragment">
            <span className="eyebrow">EVIDENCIA</span>
            <p>
              La ubicación y el pasaje aparecerán aquí únicamente después de
              procesar un documento real.
            </p>
            <span>Sin página física verificada</span>
          </div>
          <Button variant="secondary" icon="plus">
            Añadir al proyecto
          </Button>
        </aside>
      </div>
    </main>
  )
}

const students = [
  [
    "AM",
    "Andrea Morales",
    "Cap. 4 · Resultados",
    "18 de 32 pasos",
    "Hoy, 08:20",
    "En revisión",
  ],
  [
    "JP",
    "Javier Paredes",
    "Cap. 3 · Metodología",
    "14 de 32 pasos",
    "Ayer, 16:45",
    "Con observaciones",
  ],
  [
    "LC",
    "Lucía Campos",
    "Cap. 2 · Marco teórico",
    "8 de 32 pasos",
    "Ayer, 11:30",
    "En progreso",
  ],
  [
    "CV",
    "Camila Vega",
    "Cap. 5 · Discusión",
    "24 de 32 pasos",
    "12 may.",
    "En revisión",
  ],
  [
    "DR",
    "Diego Ríos",
    "Cap. 1 · Problema",
    "5 de 32 pasos",
    "10 may.",
    "Aprobado",
  ],
]

function AdvisorDashboard({ goReview }: { goReview: () => void }) {
  return (
    <main className="page advisor-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow blue">ESPACIO DEL ASESOR</span>
          <h1>Supervisión de tesistas</h1>
          <p>Seguimiento académico y revisiones pendientes.</p>
        </div>
        <div className="date-chip">Periodo 2025-I</div>
      </div>
      <div className="advisor-summary">
        <div>
          <span>TESISTAS ASIGNADOS</span>
          <strong>5</strong>
          <small>Todos con actividad reciente</small>
        </div>
        <div>
          <span>CAPÍTULOS POR REVISAR</span>
          <strong>2</strong>
          <small>Andrea y Camila</small>
        </div>
        <div>
          <span>OBSERVACIONES ABIERTAS</span>
          <strong>7</strong>
          <small>En 3 documentos</small>
        </div>
      </div>
      <section className="advisor-content">
        <div className="advisor-main">
          <div className="section-title">
            <div>
              <h2>Tesistas asignados</h2>
              <p>Progreso metodológico y actividad reciente</p>
            </div>
            <div className="simple-filters">
              <button className="active">Todos</button>
              <button>En revisión</button>
              <button>Con observaciones</button>
            </div>
          </div>
          <div className="student-table">
            <div className="student-table-head">
              <span>Tesista</span>
              <span>Avance actual</span>
              <span>Pasos</span>
              <span>Última actividad</span>
              <span>Estado</span>
            </div>
            {students.map((s, i) => (
              <button
                className="student-row"
                key={s[1]}
                onClick={i === 0 ? goReview : undefined}
              >
                <div>
                  <span className="avatar small">{s[0]}</span>
                  <b>{s[1]}</b>
                </div>
                <span>{s[2]}</span>
                <span>{s[3]}</span>
                <span>{s[4]}</span>
                <StatusBadge>{s[5]}</StatusBadge>
                <Icon name="chevron" size={15} />
              </button>
            ))}
          </div>
        </div>
        <aside className="review-inbox">
          <div className="section-title">
            <div>
              <h2>Pendientes</h2>
              <p>Por orden de envío</p>
            </div>
            <span className="count-badge">2</span>
          </div>
          <button onClick={goReview}>
            <div>
              <span className="avatar small">AM</span>
              <span>
                <b>Andrea Morales</b>
                <small>Capítulo 4 · Resultados</small>
              </span>
            </div>
            <p>Enviado hoy a las 08:20</p>
            <StatusBadge>En revisión</StatusBadge>
          </button>
          <button>
            <div>
              <span className="avatar small">CV</span>
              <span>
                <b>Camila Vega</b>
                <small>Capítulo 5 · Discusión</small>
              </span>
            </div>
            <p>Enviado ayer a las 14:10</p>
            <StatusBadge>En revisión</StatusBadge>
          </button>
          <p className="inbox-note">
            Las revisiones se muestran según la fecha de envío. No se calculan
            métricas de desempeño.
          </p>
        </aside>
      </section>
    </main>
  )
}

function Review() {
  const [showBlock, setShowBlock] = useState(false)
  const [versionOpen, setVersionOpen] = useState(true)
  return (
    <main className="review-page">
      <div className="review-demo-strip">
        MODO DEMOSTRACIÓN · documento, versiones y observaciones de ejemplo
      </div>
      <div className="review-header">
        <div>
          <button className="back-button">
            <span>‹</span> Volver a pendientes
          </button>
          <div>
            <h1>Capítulo 4. Resultados</h1>
            <p>Andrea Morales · Enviado hoy, 08:20 · Versión 7</p>
          </div>
        </div>
        <div>
          <Button variant="secondary">Solicitar cambios</Button>
          <div className="approval-wrap">
            <Button disabled onClick={() => setShowBlock(true)}>
              Aprobar capítulo
            </Button>
            {showBlock && (
              <div className="approval-tip">
                <b>No es posible aprobar todavía</b>
                <p>
                  Resuelve o cierra las 2 observaciones abiertas antes de
                  aprobar.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
      <div className="review-toolbar">
        <button className="toolbar-label">
          <Icon name="comment" size={16} /> Nueva observación
        </button>
        <span className="toolbar-divider" />
        <button onClick={() => setVersionOpen(!versionOpen)}>
          <Icon name="document" size={16} /> Historial de versiones
        </button>
        <span className="open-comments">
          <span />2 observaciones abiertas
        </span>
      </div>
      <div className="review-workspace">
        {versionOpen && (
          <aside className="version-panel">
            <div className="panel-heading">
              <b>Historial de versiones</b>
              <button onClick={() => setVersionOpen(false)}>
                <Icon name="x" size={16} />
              </button>
            </div>
            {[
              ["Versión 7", "Actual · Hoy, 08:20"],
              ["Versión 6", "12 may., 17:34"],
              ["Versión 5", "8 may., 10:12"],
              ["Versión 4", "2 may., 15:48"],
            ].map((v, i) => (
              <button className={i === 0 ? "active" : ""} key={v[0]}>
                <span>{v[0]}</span>
                <small>{v[1]}</small>
              </button>
            ))}
          </aside>
        )}
        <section className="review-document-area">
          <article className="paper review-paper">
            <span className="page-number">52</span>
            <p className="paper-kicker">CAPÍTULO IV</p>
            <h1>Resultados</h1>
            <h2>4.1 Presentación de resultados</h2>
            <p>
              En este capítulo se presentan los hallazgos obtenidos a partir de
              la aplicación de los instrumentos de investigación. Los resultados
              se organizan según las dimensiones establecidas para cada variable
              de estudio.
            </p>
            <h3>4.1.1 Uso de plataformas digitales</h3>
            <p>
              Los participantes señalaron que emplean plataformas digitales
              principalmente para acceder a materiales académicos, coordinar
              trabajos colaborativos y registrar sus actividades pendientes.
            </p>
            <div className="review-selection">
              La mayoría de los estudiantes utiliza estas herramientas de forma
              frecuente y considera que contribuyen positivamente a su
              desempeño.
              <button>
                <Icon name="comment" size={14} /> Crear observación
              </button>
            </div>
            <p>
              Sin embargo, se identificaron diferencias en las estrategias de
              organización y seguimiento utilizadas por los participantes.
            </p>
          </article>
        </section>
        <aside className="margin-comments">
          <div className="comments-summary">
            <b>Comentarios marginales</b>
            <span>2 abiertos</span>
          </div>
          <div className="margin-spacer" />
          <AdvisorComment />
          <article className="advisor-comment">
            <div className="comment-head">
              <div className="avatar advisor-avatar">RS</div>
              <div>
                <b>Dr. Roberto Salas</b>
                <span>Hoy, 10:15</span>
              </div>
              <StatusBadge dot={false}>Pendiente</StatusBadge>
            </div>
            <p>
              Evita afirmar “la mayoría” sin remitir al resultado específico.
              Indica la tabla o evidencia correspondiente.
            </p>
            <div className="anchored-quote">
              “La mayoría de los estudiantes...”
            </div>
          </article>
        </aside>
      </div>
    </main>
  )
}

function Modal({
  type,
  close,
}: {
  type: "citation" | "export"
  close: () => void
}) {
  const citation = type === "citation"
  return (
    <div className="modal-backdrop" onMouseDown={close}>
      <div className="modal" onMouseDown={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <span className="modal-icon">
              <Icon name={citation ? "book" : "download"} />
            </span>
            <div>
              <h2>{citation ? "Insertar cita" : "Exportar documento"}</h2>
              <p>
                {citation
                  ? "Busca una fuente activa y selecciona el fragmento."
                  : "Elige el formato y el contenido que deseas incluir."}
              </p>
            </div>
          </div>
          <button className="icon-button" onClick={close}>
            <Icon name="x" />
          </button>
        </div>
        {citation ? (
          <>
            <div className="modal-search">
              <Icon name="search" />
              <input placeholder="Buscar en fuentes activas..." />
            </div>
            <div className="citation-source">
              <div>
                <span className="pdf-icon">PDF</span>
                <span>
                  <b>Referencia pendiente de localizar</b>
                  <small>Sin autor, año o página verificados</small>
                </span>
                <StatusBadge dot={false}>Demostración</StatusBadge>
              </div>
              <blockquote>
                No hay un pasaje localizado. Conecta una fuente real antes de
                insertar la cita.
              </blockquote>
              <label>
                Formato de cita
                <select>
                  <option>APA 7.ª edición</option>
                  <option>Vancouver</option>
                </select>
              </label>
            </div>
          </>
        ) : (
          <div className="export-options">
            <label className="option selected">
              <input type="radio" name="format" defaultChecked />
              <span className="file-format">W</span>
              <span>
                <b>Documento de Word (.docx)</b>
                <small>Conserva títulos, citas y comentarios.</small>
              </span>
            </label>
            <label className="option">
              <input type="radio" name="format" />
              <span className="file-format pdf">P</span>
              <span>
                <b>Documento PDF</b>
                <small>Versión lista para lectura.</small>
              </span>
            </label>
            <label className="check-option">
              <input type="checkbox" defaultChecked />
              Incluir comentarios del asesor
            </label>
            <label className="check-option">
              <input type="checkbox" />
              Incluir control de cambios
            </label>
          </div>
        )}
        <div className="modal-actions">
          <Button variant="secondary" onClick={close}>
            Cancelar
          </Button>
          <Button onClick={close} disabled={citation}>
            {citation ? "Insertar cita" : "Exportar DOCX"}
          </Button>
        </div>
      </div>
    </div>
  )
}

function LoginScreen({
  onEnter,
  onExitDemo,
}: {
  onEnter: (role: "student" | "advisor") => void
  onExitDemo: () => void
}) {
  const [role, setRole] = useState<"student" | "advisor">("student")
  return (
    <main className="login-screen">
      <section className="login-brand-panel">
        <div className="login-brand">
          <div className="brand-mark">
            <Icon name="book" size={24} />
          </div>
          <div>
            <b>TesisMCP</b>
            <span>Escritura e investigación académica</span>
          </div>
        </div>
        <div className="login-promise">
          <span className="eyebrow">TU TESIS, EN UN SOLO ESPACIO</span>
          <h1>Investiga, escribe y revisa con trazabilidad.</h1>
          <p>
            Un espacio de trabajo documental para estudiantes, asesores y
            fuentes académicas, preparado para conectarse con Django.
          </p>
        </div>
        <div className="login-feature-list">
          <span><Icon name="document" /> Editor académico con versiones</span>
          <span><Icon name="library" /> Evidencia y referencias revisables</span>
          <span><Icon name="comment" /> Observaciones ancladas al texto</span>
        </div>
      </section>
      <section className="login-form-panel">
        <div className="demo-notice login-demo">
          <Icon name="spark" size={16} />
          <span>
            <b>Modo demostración.</b> No se validan credenciales ni se consulta
            el backend.
          </span>
        </div>
        <div className="login-card">
          <span className="eyebrow blue">ACCESO AL ESPACIO ACADÉMICO</span>
          <h2>Continuar con TesisMCP</h2>
          <p>
            Selecciona una vista de demostración. El inicio de sesión real se
            conectará únicamente después de validar el contrato de sesión.
          </p>
          <div className="role-picker">
            <button
              className={role === "student" ? "active" : ""}
              onClick={() => setRole("student")}
            >
              <Icon name="edit" />
              <span><b>Tesista</b><small>Escribir y organizar fuentes</small></span>
            </button>
            <button
              className={role === "advisor" ? "active" : ""}
              onClick={() => setRole("advisor")}
            >
              <Icon name="people" />
              <span><b>Asesor</b><small>Leer, comentar y decidir</small></span>
            </button>
          </div>
          <label className="login-field">
            Proyecto de demostración
            <select defaultValue="demo-project">
              <option value="demo-project">
                Adopción de plataformas digitales
              </option>
            </select>
          </label>
          <Button onClick={() => onEnter(role)}>
            Entrar a la demostración como {role === "student" ? "tesista" : "asesor"}
          </Button>
          <Button variant="secondary" onClick={onExitDemo}>
            Volver al acceso real
          </Button>
          <small className="auth-scope">
            El registro público y la recuperación de contraseña no están
            disponibles en este prototipo.
          </small>
        </div>
      </section>
    </main>
  )
}

export default function DemoApp({ onExitDemo }: { onExitDemo: () => void }) {
  const [screen, setScreen] = useState<Screen>("editor")
  const [authenticated, setAuthenticated] = useState(false)
  const [modal, setModal] = useState<"citation" | "export" | null>(null)
  if (!authenticated) {
    return (
      <LoginScreen
        onExitDemo={onExitDemo}
        onEnter={(role) => {
          setScreen(role === "advisor" ? "advisor" : "student")
          setAuthenticated(true)
        }}
      />
    )
  }
  return (
    <div className="app-shell">
      <Sidebar
        screen={screen}
        setScreen={setScreen}
        onLogout={() => setAuthenticated(false)}
      />
      <div className="app-main">
        <TopBar
          screen={screen}
          onExport={() => setModal("export")}
          onLogout={() => setAuthenticated(false)}
          onExitDemo={onExitDemo}
        />
        {screen === "student" && (
          <StudentDashboard goEditor={() => setScreen("editor")} />
        )}
        {screen === "editor" && (
          <Editor openCitation={() => setModal("citation")} />
        )}
        {screen === "library" && <Library />}
        {screen === "advisor" && (
          <AdvisorDashboard goReview={() => setScreen("review")} />
        )}
        {screen === "review" && <Review />}
      </div>
      {modal && <Modal type={modal} close={() => setModal(null)} />}
    </div>
  )
}
