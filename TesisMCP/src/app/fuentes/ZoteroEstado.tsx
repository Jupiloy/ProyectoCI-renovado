import type { ZoteroConnectionStatus } from "../../api/types"
import { Button } from "../base"

/** Tarjeta de estado de la conexión Zotero: cuenta conectada (con fecha y
 * alcances reales) o sin conexión, con las acciones Conectar (redirect OAuth
 * del backend, en pestaña nueva) / Verificar estado / Desconectar. */
export function ZoteroEstado({
  estado,
  cargandoEstado,
  desconectando,
  onConectar,
  onVerificar,
  onDesconectar,
}: {
  estado: ZoteroConnectionStatus | null
  cargandoEstado: boolean
  desconectando: boolean
  onConectar: () => void
  onVerificar: () => void
  onDesconectar: () => void
}) {
  const conectado = estado?.connected === true
  if (cargandoEstado && estado === null) {
    return (
      <div className="library-summary">
        <span className="eyebrow blue">ZOTERO</span>
        <span role="status">Consultando el estado de la conexión Zotero…</span>
      </div>
    )
  }
  if (conectado && estado) {
    return (
      <div className="library-summary">
        <span className="eyebrow blue">CUENTA CONECTADA</span>
        <span>
          Usuario Zotero {estado.zotero_user_id} · conectada{" "}
          {estado.connected_at ? new Date(estado.connected_at).toLocaleString() : "—"} ·{" "}
          {estado.granted_scopes.length > 0 ? estado.granted_scopes.join(", ") : "sin alcances declarados"}
        </span>
        <Button variant="secondary" disabled={desconectando} onClick={onDesconectar}>
          {desconectando ? "Cerrando…" : "Desconectar Zotero"}
        </Button>
      </div>
    )
  }
  return (
    <div className="library-summary">
      <span className="eyebrow blue">SIN CONEXIÓN</span>
      <span>
        La cuenta Zotero no está conectada. La conexión se autoriza en Zotero
        (OAuth del backend) y puede requerir configuración del servidor.
      </span>
      <Button onClick={onConectar}>Conectar Zotero</Button>
      <Button variant="secondary" disabled={cargandoEstado} onClick={onVerificar}>
        Verificar estado
      </Button>
    </div>
  )
}
