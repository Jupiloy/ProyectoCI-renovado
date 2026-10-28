import type { ReactNode } from "react"

/** Copia literal del sistema de iconos de la maqueta de Figma (DemoApp.tsx). */
export type IconNameTesis =
  | "book"
  | "chevron"
  | "comment"
  | "document"
  | "download"
  | "edit"
  | "home"
  | "library"
  | "people"
  | "settings"
  | "spark"

const iconPathsTesis: Record<IconNameTesis, ReactNode> = {
  book: (
    <>
      <path d="M3 5.5A4.5 4.5 0 0 1 7.5 4H11v16H7.5A4.5 4.5 0 0 0 3 21.5zM21 5.5A4.5 4.5 0 0 0 16.5 4H13v16h3.5a4.5 4.5 0 0 1 4.5 1.5z" />
    </>
  ),
  chevron: <path d="m9 18 6-6-6-6" />,
  comment: <path d="M4 4h16v12H9l-5 4z" />,
  document: (
    <>
      <path d="M6 2.5h8l4 4V21H6z" />
      <path d="M14 2.5v4h4M9 11h6M9 15h6" />
    </>
  ),
  download: (
    <>
      <path d="M12 4v12M7 11l5 5 5-5M4 20h16" />
    </>
  ),
  edit: (
    <>
      <path d="m4 20 4.2-1 10.9-10.9-3.2-3.2L5 15.8zM14.8 6l3.2 3.2" />
    </>
  ),
  home: (
    <>
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5.5 9.5V21h13V9.5M9 21v-7h6v7" />
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
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.6 1.6 0 0 1 1.6-1 1.7 1.7 0 0 0 1.6-1Z" />
      <path d="m6 6 12 12M18 6 6 18" />
    </>
  ),
  spark: (
    <>
      <path d="m12 3 1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4zM18.5 15l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z" />
    </>
  ),
}

export function Icon({
  name,
  size = 18,
}: {
  name: IconNameTesis
  size?: number
}) {
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
      {iconPathsTesis[name]}
    </svg>
  )
}

export function Button({
  children,
  variant = "primary",
  icon,
  disabled,
  onClick,
}: {
  children: ReactNode
  variant?: "primary" | "secondary" | "danger" | "ghost"
  icon?: IconNameTesis
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
  Borrador: "neutral",
  "Solo metadatos": "neutral",
  "En progreso": "blue",
  "En curso": "blue",
  "Texto completo disponible": "blue",
  "En revisión": "violet",
  "Con observaciones": "danger",
  Aprobado: "success",
  Pendiente: "warning",
  "Pendiente de revisión": "warning",
}

export function StatusBadge({
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
