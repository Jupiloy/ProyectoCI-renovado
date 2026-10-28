import type { ChapterSnapshotDetailApi } from "../../api/types"

export type Anclaje = {
  snapshot_id: string
  start_cp: number
  end_cp: number
  selected_text: string
}

/**
 * Traduce una selección del usuario (Range del navegador) a offsets en puntos
 * de código Unicode sobre el content_md del snapshot. Devuelve `{ error }`
 * cuando la selección no coincide literalmente con el texto de la versión y
 * `{}` cuando no hay selección válida dentro del documento.
 */
export function calcularAnclaje(
  detalle: ChapterSnapshotDetailApi,
  contenedor: HTMLDivElement,
): { anclaje?: Anclaje; error?: string } {
  const seleccion = window.getSelection()
  if (!seleccion || seleccion.isCollapsed || seleccion.rangeCount === 0) return {}
  const rango = seleccion.getRangeAt(0)
  if (!contenedor.contains(rango.startContainer) || !contenedor.contains(rango.endContainer)) return {}

  const previo = rango.cloneRange()
  previo.selectNodeContents(contenedor)
  previo.setEnd(rango.startContainer, rango.startOffset)
  const hasta = rango.cloneRange()
  hasta.selectNodeContents(contenedor)
  hasta.setEnd(rango.endContainer, rango.endOffset)

  const inicioUtf16 = previo.toString().length
  const finUtf16 = hasta.toString().length
  const texto = detalle.content_md.slice(inicioUtf16, finUtf16)
  if (!texto || texto !== rango.toString()) {
    return { error: "La selección no coincide con el texto de la versión. Vuelve a seleccionar el fragmento." }
  }
  return {
    anclaje: {
      snapshot_id: detalle.id,
      start_cp: Array.from(detalle.content_md.slice(0, inicioUtf16)).length,
      end_cp: Array.from(detalle.content_md.slice(0, finUtf16)).length,
      selected_text: texto,
    },
  }
}
