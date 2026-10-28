import { useRef } from "react"
import type { ChapterContentTree, SourceExcerpt } from "../../api/types"
import { utf16ACodePoints } from "./citas"
import { opcionesDeEvidencia, useEvidencia } from "./evidencia"
import { Button } from "../base"

/**
 * Pestaña «Evidencia» del panel derecho: vincula una afirmación del párrafo
 * citado con un pasaje real de la fuente citada (candidato CANDIDATE) y
 * muestra el historial de evaluaciones. La afirmación se selecciona con el
 * cursor sobre el texto del párrafo y el rango del pasaje sobre su texto;
 * los offsets se convierten a puntos de código Unicode (regla del backend).
 * Crear candidato: solo propietario (owner_only en citation_evidence.py).
 * Decidir (SUPPORTS/CONTRADICTS/UNRELATED/INSUFFICIENT): solo asesor.
 */
export function PanelEvidencia({
  projectId,
  numeroCapitulo,
  csrfToken,
  activa,
  draft,
  esPropietario,
  esAsesor,
  onUnauthorized,
}: {
  projectId: string
  numeroCapitulo: number | null
  csrfToken: string
  activa: boolean
  draft: ChapterContentTree | null
  esPropietario: boolean
  esAsesor: boolean
  onUnauthorized: () => void
}) {
  const ev = useEvidencia({ projectId, numeroCapitulo, csrfToken, activa, draft, esPropietario, esAsesor, onUnauthorized })
  const claimArea = useRef<HTMLTextAreaElement | null>(null)
  const excerptArea = useRef<HTMLTextAreaElement | null>(null)
  const opciones = opcionesDeEvidencia(ev.vista)
  const opcion = ev.opcion
  const extracto: SourceExcerpt | null =
    ev.extractos?.find((e) => e.excerpt_id === ev.extractoId) ?? null
  const ultima = ev.historial?.[ev.historial.length - 1] ?? null

  function registrarClaim() {
    const el = claimArea.current
    if (!el) return
    ev.setClaimStart(utf16ACodePoints(el.value, el.selectionStart))
    ev.setClaimEnd(utf16ACodePoints(el.value, el.selectionEnd))
  }
  function registrarPasaje() {
    const el = excerptArea.current
    if (!el) return
    ev.setExStart(utf16ACodePoints(el.value, el.selectionStart))
    ev.setExEnd(utf16ACodePoints(el.value, el.selectionEnd))
  }

  if (!activa) return null
  if (ev.cargando && !ev.vista) {
    return <p className="aviso" role="status">Consultando las citas confirmadas del capítulo…</p>
  }
  if (ev.error && !ev.vista) {
    return (
      <div className="comments-list">
        <div className="aviso aviso-error" role="alert">{ev.error}</div>
        <button className="text-link" onClick={() => void ev.cargarVista()}>Reintentar</button>
      </div>
    )
  }
  if (opciones.length === 0) {
    return (
      <p className="aviso">
        Este capítulo no tiene citas confirmadas en el servidor: crea una cita
        y guarda la versión para poder vincular evidencia.
      </p>
    )
  }
  return (
    <div className="comments-list">
      {ev.error && <div className="aviso aviso-error" role="alert">{ev.error}</div>}
      {ev.notice && <div className="aviso" role="status">{ev.notice}</div>}
      <div className="artifact-picker">
        <label>
          Cita (ocurrencia y fuente)
          <select
            value={opcion ? `${opcion.groupId}:${opcion.indice}` : ""}
            onChange={(e) => {
              const [groupId, indice] = e.target.value.split(":")
              const o = opciones.find((x) => x.groupId === groupId && x.indice === Number(indice))
              if (o) void ev.elegirOpcion(o)
            }}
          >
            <option value="">— Elegir cita —</option>
            {opciones.map((o) => (
              <option key={`${o.groupId}:${o.indice}`} value={`${o.groupId}:${o.indice}`}>
                {o.citationText} · {o.number} · posición {o.position}
              </option>
            ))}
          </select>
        </label>
        {opcion && (
          <label>
            Extracto de la fuente citada
            <select value={ev.extractoId ?? ""} onChange={(e) => {
              const sel = ev.extractos?.find((x) => x.excerpt_id === Number(e.target.value))
              if (sel) ev.elegirExtracto(sel)
            }}>
              <option value="">— Elegir extracto —</option>
              {(ev.extractos ?? []).map((x) => (
                <option key={x.excerpt_id} value={x.excerpt_id}>
                  Página física {x.physical_page} · {x.text.slice(0, 60)}…
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      {opcion && ev.textoClaim === null && (
        <p className="aviso">
          El párrafo citado no está disponible en el borrador actual; recarga el
          capítulo para vincular evidencia.
        </p>
      )}
      {opcion && extracto && ev.textoClaim !== null && (
        <>
          <small className="version-sha">
            Selecciona con el cursor la afirmación en el párrafo (debe incluir el
            ancla de la cita, posición {opcion.position}) y el tramo del pasaje
            que la respalda.
          </small>
          <textarea
            ref={claimArea}
            className="paper-block-textarea"
            aria-label="Texto del párrafo citado"
            readOnly
            rows={4}
            value={ev.textoClaim}
            onSelect={registrarClaim}
            onKeyUp={registrarClaim}
          />
          <small className="version-sha">
            Afirmación: caracteres {ev.claimStart}–{ev.claimEnd}
          </small>
          <textarea
            ref={excerptArea}
            className="paper-block-textarea"
            aria-label="Texto del extracto"
            readOnly
            rows={4}
            value={extracto.text}
            onSelect={registrarPasaje}
            onKeyUp={registrarPasaje}
          />
          <small className="version-sha">
            Pasaje: caracteres {ev.exStart}–{ev.exEnd}
          </small>
          {esPropietario ? (
            <Button disabled={ev.creando || ev.extractoId === null} onClick={() => void ev.crearCandidato()}>
              {ev.creando ? "Creando…" : "Crear candidato de evidencia"}
            </Button>
          ) : (
            <small className="version-sha">
              Solo el propietario del proyecto puede crear candidatos de evidencia.
            </small>
          )}
        </>
      )}
      {opcion && (
        <>
          <span className="eyebrow blue">HISTORIAL DE EVALUACIONES</span>
          {ev.cargandoHistorial ? (
            <p className="aviso" role="status">Cargando historial…</p>
          ) : (ev.historial ?? []).length === 0 ? (
            <p className="aviso">Sin evaluaciones registradas para esta ocurrencia.</p>
          ) : (
            (ev.historial ?? []).map((r) => (
              <article className="chapter-row" key={r.review_id}>
                <div>
                  <b>v{r.review_version} · {r.status}</b>
                  <small>
                    Afirmación: «{r.claim_text.slice(0, 80)}{r.claim_text.length > 80 ? "…" : ""}» ·{" "}
                    página física {r.physical_page} · pasaje: «{r.matched_text.slice(0, 60)}…»
                  </small>
                  {r.review_note && <small>Nota: {r.review_note}</small>}
                </div>
              </article>
            ))
          )}
          {esAsesor && ultima && (
            <div className="artifact-picker">
              <label>
                Nota de la decisión (opcional)
                <input type="text" maxLength={2000} value={ev.nota} onChange={(e) => ev.setNota(e.target.value)} />
              </label>
              <div className="workflow-task-actions">
                {(["SUPPORTS", "CONTRADICTS", "UNRELATED", "INSUFFICIENT"] as const).map((s) => (
                  <Button key={s} variant="secondary" disabled={ev.decidiendo} onClick={() => void ev.decidir(s)}>
                    {s === "SUPPORTS" ? "Respalda" : s === "CONTRADICTS" ? "Contradice" : s === "UNRELATED" ? "No relacionada" : "Insuficiente"}
                  </Button>
                ))}
              </div>
            </div>
          )}
          {esAsesor && !ultima && (
            <small className="version-sha">
              Las evaluaciones las registra el asesor sobre un candidato creado por el tesista.
            </small>
          )}
          {!esAsesor && (
            <small className="version-sha">
              La decisión (respalda / contradice / no relacionada / insuficiente)
              la toma el asesor del proyecto.
            </small>
          )}
        </>
      )}
    </div>
  )
}
