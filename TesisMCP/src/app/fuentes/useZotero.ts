import { useCallback, useEffect, useState } from "react"
import { ApiError } from "../../api/client"
import {
  disconnectZotero,
  getZoteroStatus,
  importZoteroItem,
  listZoteroItems,
} from "../../api/sources"
import type { ZoteroConnectionStatus } from "../../api/types"

/** Registro bibliográfico de la biblioteca personal de Zotero: campos
 * literales de la respuesta del backend (services/zotero.py, list_zotero_items). */
export type ZoteroItem = {
  item_key: string
  item_type: string | null
  title: string
  authors: string[]
  date: string
  doi: string
  publication_venue: string
  url: string
  abstract: string
}

export type ListadoZotero = {
  items: ZoteroItem[]
  start: number
  limit: number
  total_results: number | null
  last_modified_version: number | null
}

/**
 * Estado y acciones de la integración Zotero: estado real de la conexión
 * OAuth del usuario, búsqueda en la biblioteca personal, importación de
 * registros (owner_only) y desconexión. No simula ningún estado: lo que el
 * backend no configura (OAuth, conexión) se reporta como error textual del
 * propio backend.
 */
export function useZotero(args: {
  projectId: string
  csrfToken: string
  puedeImportar: boolean
  onUnauthorized: () => void
  onAccessLost: () => void
  alImportar: () => void
}) {
  const { projectId, csrfToken, puedeImportar, onUnauthorized, onAccessLost, alImportar } = args
  const [estado, setEstado] = useState<ZoteroConnectionStatus | null>(null)
  const [cargandoEstado, setCargandoEstado] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [consulta, setConsulta] = useState("")
  const [listado, setListado] = useState<ListadoZotero | null>(null)
  const [cargandoItems, setCargandoItems] = useState(false)
  const [importando, setImportando] = useState<string | null>(null)
  const [desconectando, setDesconectando] = useState(false)

  const recargarEstado = useCallback(async () => {
    setCargandoEstado(true)
    setError(null)
    try {
      setEstado(await getZoteroStatus())
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
        return
      }
      setEstado(null)
      setError(cause instanceof Error ? cause.message : "No se pudo consultar el estado de Zotero.")
    } finally {
      setCargandoEstado(false)
    }
  }, [onUnauthorized])

  useEffect(() => {
    void recargarEstado()
  }, [recargarEstado])

  async function buscar(evento: { preventDefault: () => void }, inicio = 0, acumular = false) {
    evento.preventDefault()
    setCargandoItems(true)
    setError(null)
    try {
      const res = (await listZoteroItems(projectId, consulta.trim(), inicio, 25)) as ListadoZotero
      setListado((previo) =>
        acumular && previo ? { ...res, items: [...previo.items, ...res.items] } : res,
      )
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
      } else if (cause instanceof ApiError && cause.status === 404) {
        onAccessLost()
      } else {
        setError(cause instanceof Error ? cause.message : "No se pudo listar la biblioteca de Zotero.")
      }
    } finally {
      setCargandoItems(false)
    }
  }

  async function importar(item: ZoteroItem) {
    if (!puedeImportar || importando !== null) return
    setImportando(item.item_key)
    setError(null)
    setNotice(null)
    try {
      const res = (await importZoteroItem(projectId, item.item_key, csrfToken)) as { created?: boolean }
      setNotice(
        res.created
          ? `Registro importado a la biblioteca: ${item.title}`
          : `El registro ya estaba en la biblioteca: ${item.title}`,
      )
      alImportar()
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
      } else {
        setError(cause instanceof Error ? cause.message : "No se pudo importar el registro.")
      }
    } finally {
      setImportando(null)
    }
  }

  async function desconectar() {
    if (desconectando) return
    setDesconectando(true)
    setError(null)
    try {
      await disconnectZotero(csrfToken)
      await recargarEstado()
      setListado(null)
      setNotice("Conexión Zotero cerrada.")
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) {
        onUnauthorized()
      } else {
        setError(cause instanceof Error ? cause.message : "No se pudo cerrar la conexión.")
      }
    } finally {
      setDesconectando(false)
    }
  }

  /** Página siguiente con el mismo filtro (paginación por start/limit). */
  async function cargarMas(evento: { preventDefault(): void }) {
    const inicio = listado ? listado.start + listado.limit : 0
    await buscar(evento, inicio, true)
  }

  return {
    estado,
    cargandoEstado,
    error,
    notice,
    consulta,
    setConsulta,
    listado,
    cargandoItems,
    importando,
    desconectando,
    conectado: estado?.connected === true,
    recargarEstado,
    buscar,
    cargarMas,
    importar,
    desconectar,
  }
}
