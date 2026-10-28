import { useState } from "react"
import { ApiError } from "../../api/client"
import { searchPassages } from "../../api/sources"
import type { PassageItem } from "../../api/types"
import { Button } from "../base"

const advertenciaBusqueda =
  "Los resultados son candidatos de recuperación semántica por similitud vectorial: no equivalen a una respuesta sintetizada ni constituyen verificación de la afirmación."

/** Búsqueda de pasajes sobre el corpus extraído (POST /passages/search con
 * pgvector): consulta, número de candidatos y resultados con distancia
 * coseno y estado honesto cuando no hay pasajes indexados. */
export function PanelPasajes({
  projectId,
  csrfToken,
  onUnauthorized,
}: {
  projectId: string
  csrfToken: string
  onUnauthorized: () => void
}) {
  const [consulta, setConsulta] = useState("")
  const [limite, setLimite] = useState(5)
  const [buscando, setBuscando] = useState(false)
  const [pasajes, setPasajes] = useState<PassageItem[] | null>(null)
  const [estadoBusqueda, setEstadoBusqueda] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function buscarPasajes(evento: React.FormEvent) {
    evento.preventDefault()
    const q = consulta.trim()
    if (!q) return
    setBuscando(true)
    setError(null)
    try {
      const res = await searchPassages(projectId, q, limite, undefined, csrfToken)
      setPasajes(res.results)
      setEstadoBusqueda(res.search_status)
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
      } else {
        setError(cause instanceof Error ? cause.message : "No se pudo completar la búsqueda de pasajes.")
      }
    } finally {
      setBuscando(false)
    }
  }

  return (
    <section className="section-card passages-panel">
      <div className="section-title">
        <div>
          <h2>Búsqueda de pasajes</h2>
          <p>Consulta semántica sobre el corpus extraído del proyecto</p>
        </div>
      </div>
      <div className="aviso">
        <strong>Advertencia obligatoria:</strong> {advertenciaBusqueda}
      </div>
      {error && <div className="aviso aviso-error" role="alert">{error}</div>}
      <form className="passages-form" onSubmit={buscarPasajes}>
        <input
          type="text"
          maxLength={500}
          placeholder="Pregunta o consulta semántica sobre tus fuentes (hasta 500 caracteres)…"
          value={consulta}
          onChange={(e) => setConsulta(e.target.value)}
        />
        <select value={limite} onChange={(e) => setLimite(Number(e.target.value))} aria-label="Número de candidatos">
          <option value={3}>3 candidatos</option>
          <option value={5}>5 candidatos</option>
          <option value={10}>10 candidatos</option>
          <option value={15}>15 candidatos</option>
        </select>
        <Button disabled={buscando || !consulta.trim()}>
          {buscando ? "Buscando…" : "Buscar pasajes"}
        </Button>
      </form>
      {estadoBusqueda && estadoBusqueda !== "OK" && pasajes?.length === 0 && (
        <p className="aviso">
          Estado de la búsqueda: {estadoBusqueda}. No hay pasajes indexados
          para esta consulta; sube documentos con texto extraído para
          habilitar la búsqueda semántica.
        </p>
      )}
      {pasajes && pasajes.length > 0 && (
        <div className="chapter-list">
          {pasajes.map((p) => (
            <article className="chapter-row" key={p.passage_id}>
              <div>
                <strong>{p.physical_page ? `Página física ${p.physical_page}` : p.locator_kind || "Segmento"}</strong>
                <blockquote className="anchored-quote">«{p.text}»</blockquote>
                <small>
                  SHA {p.text_sha256.slice(0, 12)}… · distancia coseno {p.cosine_distance.toFixed(4)} ·{" "}
                  {p.supports_claim_verified ? "validado" : "candidato no evaluado semánticamente"}
                </small>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
