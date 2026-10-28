import { useCallback, useEffect, useState } from "react"
import { ApiError } from "../../api/client"
import { getChapterIeeeCitations } from "../../api/chapters"
import type { IeeeCitationView } from "../../api/types"
import { StatusBadge } from "../base"

/**
 * Pestaña «Citas IEEE» del panel derecho: vista preliminar de numeración y
 * referencias que produce el backend (`GET /chapters/{n}/citations/ieee`,
 * build_ieee_citation_view) a partir de la revisión canónica actual. El
 * render es preliminar desde metadatos: el backend declara su estado y sus
 * brechas (missing_fields) y la UI las muestra tal cual, sin completar nada.
 * Las citas locales sin guardar no aparecen aquí (la vista refleja la última
 * revisión confirmada en el servidor).
 */
export function PanelIeee({
  projectId,
  numeroCapitulo,
  activa,
  onUnauthorized,
}: {
  projectId: string
  numeroCapitulo: number | null
  activa: boolean
  onUnauthorized: () => void
}) {
  const [vista, setVista] = useState<IeeeCitationView | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cargar = useCallback(async () => {
    if (numeroCapitulo === null) return
    setCargando(true)
    setError(null)
    try {
      setVista(await getChapterIeeeCitations(projectId, numeroCapitulo))
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
        return
      }
      setVista(null)
      setError(cause instanceof Error ? cause.message : "No se pudo consultar la vista de citas IEEE.")
    } finally {
      setCargando(false)
    }
  }, [projectId, numeroCapitulo, onUnauthorized])

  useEffect(() => {
    if (activa) void cargar()
  }, [activa, cargar])

  if (!activa) return null
  if (cargando && !vista) {
    return <p className="aviso" role="status">Consultando la vista preliminar IEEE…</p>
  }
  if (error) {
    return (
      <div className="comments-list">
        <div className="aviso aviso-error" role="alert">{error}</div>
        <button className="text-link" onClick={() => void cargar()}>Reintentar</button>
      </div>
    )
  }
  if (!vista) return null

  const incompletas = vista.references.filter((r) => r.status === "INCOMPLETE_METADATA")

  return (
    <div className="comments-list">
      <div className="aviso">
        <b>{vista.rendering_status}</b> — {vista.notice}
      </div>
      {vista.marks.length === 0 ? (
        <p className="aviso">
          Este capítulo no tiene citas confirmadas en el servidor. Las citas
          locales sin guardar aparecen aquí después de guardar la versión.
        </p>
      ) : (
        <>
          <div className="chapter-list">
            {vista.marks.map((m) => (
              <article className="chapter-row" key={m.group_id}>
                <span className="chapter-number">{m.citation_text}</span>
                <div>
                  <small>
                    Párrafo {m.block_id.slice(0, 8)}… · posición {m.position} ·{" "}
                    {m.numbers.length > 1 ? `números ${m.numbers.join(", ")}` : `número ${m.numbers[0]}`}
                  </small>
                </div>
              </article>
            ))}
          </div>
          <span className="eyebrow blue">REFERENCIAS ({vista.references.length})</span>
          <div className="chapter-list">
            {vista.references.map((r) => (
              <article className="chapter-row" key={r.reference_sha256}>
                <span className="chapter-number">{r.number}</span>
                <div>
                  <small>{r.ieee_text}</small>
                  {r.status === "INCOMPLETE_METADATA" && (
                    <small className="version-sha">
                      Metadatos incompletos: {r.missing_fields.join(", ")}
                    </small>
                  )}
                </div>
                <StatusBadge dot={false}>
                  {r.status === "METADATA_COMPLETE" ? "Completa" : "Incompleta"}
                </StatusBadge>
              </article>
            ))}
          </div>
          {incompletas.length > 0 && (
            <small className="version-sha">
              {incompletas.length} de {vista.references.length} referencias tienen
              metadatos incompletos; complétalas desde la pestaña Fuentes
              (verificación contra portada) y vuelve a guardar para regenerar la vista.
            </small>
          )}
        </>
      )}
      <button className="text-link" onClick={() => void cargar()}>
        Actualizar vista IEEE
      </button>
    </div>
  )
}
