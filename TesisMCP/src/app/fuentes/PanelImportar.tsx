import { useState } from "react"
import { ApiError } from "../../api/client"
import { importBibliographyFile } from "../../api/sources"
import { Button } from "../base"

/** Resumen literal de la importación (services/bibliography.py). */
type ResumenImportacion = {
  provider: string
  filename: string
  file_sha256: string
  records_seen: number
  records_created: number
  records_already_imported: number
  imported: Array<{
    source_id: string
    created: boolean
    title: string
    provider_record_id: string
    possible_duplicates: unknown[]
  }>
}

const PROVEEDORES: Array<{ valor: string; etiqueta: string }> = [
  { valor: "SCOPUS", etiqueta: "Scopus (exportación de resultados)" },
  { valor: "WOS", etiqueta: "Web of Science (exportación de resultados)" },
  { valor: "OTHER", etiqueta: "Otro gestor (RIS/BibTeX/CSV)" },
]

/** Importación de bibliografía desde archivo de exportación (RIS/BibTeX/CSV,
 * hasta 5 MiB): crea fuentes con metadatos del archivo, sin verificación
 * contra portada (estado honesto IMPORTED_METADATA_UNVERIFIED). */
export function PanelImportar({
  projectId,
  csrfToken,
  puedeImportar,
  onUnauthorized,
  alImportar,
}: {
  projectId: string
  csrfToken: string
  puedeImportar: boolean
  onUnauthorized: () => void
  alImportar: () => void
}) {
  const [proveedor, setProveedor] = useState("OTHER")
  const [archivo, setArchivo] = useState<File | null>(null)
  const [importando, setImportando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resumen, setResumen] = useState<ResumenImportacion | null>(null)

  async function importar(evento: React.FormEvent) {
    evento.preventDefault()
    if (!archivo || !puedeImportar) return
    setImportando(true)
    setError(null)
    setResumen(null)
    try {
      const res = (await importBibliographyFile(projectId, proveedor, archivo, csrfToken)) as ResumenImportacion
      setResumen(res)
      alImportar()
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
      } else {
        setError(cause instanceof Error ? cause.message : "No se pudo importar la bibliografía.")
      }
    } finally {
      setImportando(false)
    }
  }

  return (
    <section className="section-card import-panel">
      <div className="section-title">
        <div>
          <h2>Importar bibliografía desde archivo</h2>
          <p>
            Exportaciones .ris, .bib, .bibtex o .csv (hasta 5 MiB) de Scopus,
            Web of Science u otro gestor de referencias
          </p>
        </div>
      </div>
      {error && <div className="aviso aviso-error" role="alert">{error}</div>}
      <form className="passages-form" onSubmit={importar}>
        <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
          Origen
          <select value={proveedor} onChange={(e) => setProveedor(e.target.value)}>
            {PROVEEDORES.map((p) => (
              <option key={p.valor} value={p.valor}>{p.etiqueta}</option>
            ))}
          </select>
        </label>
        <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
          Archivo
          <input
            type="file"
            accept=".ris,.bib,.bibtex,.csv"
            disabled={!puedeImportar}
            onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
          />
        </label>
        <Button disabled={importando || !archivo || !puedeImportar}>
          {importando ? "Importando…" : "Importar registros"}
        </Button>
        {!puedeImportar && (
          <small className="version-sha">Solo el propietario del proyecto puede importar.</small>
        )}
      </form>
      {resumen && (
        <div className="aviso" role="status">
          <b>
            {resumen.provider} · {resumen.filename}
          </b>{" "}
          — registros leídos: {resumen.records_seen}; creados: {resumen.records_created}; ya existentes:{" "}
          {resumen.records_already_imported}. Los registros importados quedan{" "}
          <b>sin verificación contra portada</b> (metadatos del archivo).
        </div>
      )}
    </section>
  )
}
