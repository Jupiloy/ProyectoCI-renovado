import { Button } from "../base"
import { ZoteroEstado } from "./ZoteroEstado"
import { useZotero, type ZoteroItem } from "./useZotero"

const CONNECT_URL = "/api/v1/integrations/zotero/connect"

/**
 * Panel de integración Zotero: consume useZotero (estado y acciones reales
 * contra /integrations/zotero y /sources/zotero). El JSX solo compone la
 * tarjeta de conexión, el formulario de búsqueda y el listado importable.
 */
export function ZoteroPanel({
  projectId,
  csrfToken,
  puedeImportar,
  onUnauthorized,
  onAccessLost,
  alImportar,
}: {
  projectId: string
  csrfToken: string
  puedeImportar: boolean
  onUnauthorized: () => void
  onAccessLost: () => void
  alImportar: () => void
}) {
  const z = useZotero({ projectId, csrfToken, puedeImportar, onUnauthorized, onAccessLost, alImportar })

  return (
    <section className="section-card zotero-panel">
      <div className="section-title">
        <div>
          <h2>Zotero</h2>
          <p>Conexión con tu biblioteca personal vía OAuth; los registros importados quedan trazados</p>
        </div>
      </div>
      {z.error && <div className="aviso aviso-error" role="alert">{z.error}</div>}
      {z.notice && <div className="aviso" role="status">{z.notice}</div>}
      <ZoteroEstado
        estado={z.estado}
        cargandoEstado={z.cargandoEstado}
        desconectando={z.desconectando}
        onConectar={() => window.open(CONNECT_URL, "_blank")}
        onVerificar={() => void z.recargarEstado()}
        onDesconectar={() => void z.desconectar()}
      />
      {z.conectado && (
        <>
          <form className="passages-form" onSubmit={(e) => void z.buscar(e, 0, false)}>
            <input
              type="text"
              maxLength={200}
              placeholder="Buscar en tu biblioteca de Zotero (título, autor, año…)"
              value={z.consulta}
              onChange={(e) => z.setConsulta(e.target.value)}
            />
            <Button disabled={z.cargandoItems}>
              {z.cargandoItems ? "Consultando…" : "Buscar registros"}
            </Button>
          </form>
          {z.listado && z.listado.items.length === 0 && (
            <p className="aviso">
              Zotero no devolvió registros bibliográficos para esta consulta
              (excluye adjuntos, notas y anotaciones).
            </p>
          )}
          {z.listado && z.listado.items.length > 0 && (
            <ListaZotero
              listado={z.listado}
              puedeImportar={puedeImportar}
              importando={z.importando}
              cargandoItems={z.cargandoItems}
              onImportar={(item) => void z.importar(item)}
              onCargarMas={(e) => void z.cargarMas(e)}
            />
          )}
          {!puedeImportar && (
            <small className="version-sha">
              Como asesor puedes consultar tu propia biblioteca, pero la
              importación a este proyecto es del tesista propietario.
            </small>
          )}
        </>
      )}
    </section>
  )
}

/** Listado de registros de Zotero con importación individual y paginación. */
function ListaZotero({
  listado,
  puedeImportar,
  importando,
  cargandoItems,
  onImportar,
  onCargarMas,
}: {
  listado: { items: ZoteroItem[]; start: number; limit: number }
  puedeImportar: boolean
  importando: string | null
  cargandoItems: boolean
  onImportar: (item: ZoteroItem) => void
  onCargarMas: (evento: { preventDefault(): void }) => void
}) {
  return (
    <>
      <div className="chapter-list">
        {listado.items.map((item) => (
          <article className="chapter-row" key={item.item_key}>
            <span className="chapter-number">{item.item_type || "registro"}</span>
            <div>
              <strong>{item.title}</strong>
              <small>
                {item.authors.length > 0 ? item.authors.join(", ") : "Autoría no declarada"} ·{" "}
                {item.date || "sin fecha"}
                {item.doi ? ` · DOI ${item.doi}` : ""}
              </small>
            </div>
            <Button
              variant="secondary"
              disabled={!puedeImportar || importando !== null}
              title={
                puedeImportar
                  ? "Importar el registro a la biblioteca del proyecto"
                  : "Solo el propietario del proyecto puede importar registros"
              }
              onClick={() => onImportar(item)}
            >
              {importando === item.item_key ? "Importando…" : "Importar"}
            </Button>
          </article>
        ))}
      </div>
      {listado.items.length >= listado.limit && (
        <button className="text-link" disabled={cargandoItems} onClick={onCargarMas}>
          Cargar más registros
        </button>
      )}
    </>
  )
}
