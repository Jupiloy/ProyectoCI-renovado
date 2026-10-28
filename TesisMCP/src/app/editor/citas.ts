import type { Dispatch, SetStateAction } from "react"
import type { ChapterContentTree } from "../../api/types"
import { editableCitations } from "./etiquetas"
import type { Loaded, PendingSave, SaveCitation } from "./tipos"

/**
 * Lógica de citas del editor: el conjunto efectivo de citas es el del documento
 * cargado (base) o, cuando el tesista agregó o retiró citas locales, ese
 * conjunto local (que el guardado envía completo en el PUT, reemplazando el
 * manifiesto del servidor). Reglas del backend verificadas en
 * `services/citation_occurrences.py`: cada cita requiere exactamente
 * {group_id, block_id, position, sources}; `position` es un offset Unicode
 * (puntos de código, no unidades UTF-16) dentro del texto de un bloque
 * `paragraph`; locator de texto de hasta 200 caracteres.
 */

/** Conjunto base: las citas del documento cargado, reducidas al contrato del PUT. */
export function citasBase(loaded: Loaded | null): SaveCitation[] {
  return loaded ? editableCitations(loaded.document.citations) : []
}

/** Citas con las que se guardará y contra las que se compara la versión vigente. */
export function citasEfectivas(loaded: Loaded | null, citasLocales: SaveCitation[] | null): SaveCitation[] {
  return citasLocales ?? citasBase(loaded)
}

/**
 * Convierte un índice UTF-16 del textarea (selectionStart) en un offset de
 * puntos de código Unicode, que es la unidad que valida el backend para
 * `position` (0..len del párrafo en Python). Índices fuera de rango se recortan.
 */
export function utf16ACodePoints(text: string, indexUtf16: number): number {
  const recortado = Math.max(0, Math.min(indexUtf16, text.length))
  return Array.from(text.slice(0, recortado)).length
}

/** Agrega una cita local de una sola fuente anclada a un párrafo del borrador.
 * Devuelve false si el bloque no es un párrafo (el backend solo ancla citas a
 * paragraphs) o no hay documento cargado. Toda edición de citas anula el
 * intento de guardado pendiente, igual que las ediciones de bloques. */
export function agregarCita(args: {
  loaded: Loaded | null
  draft: ChapterContentTree | null
  citasLocales: SaveCitation[] | null
  blockId: string
  /** selectionStart del textarea en unidades UTF-16; null = final del texto. */
  indexUtf16: number | null
  sourceId: string
  locator: string
  setCitasLocales: Dispatch<SetStateAction<SaveCitation[] | null>>
  setPending: Dispatch<SetStateAction<PendingSave | null>>
  setNotice: Dispatch<SetStateAction<string | null>>
}): boolean {
  const bloque = args.draft?.blocks.find((b) => b.id === args.blockId)
  if (!args.loaded || !bloque || bloque.type !== "paragraph") return false
  const posicion = utf16ACodePoints(bloque.text, args.indexUtf16 ?? bloque.text.length)
  const nueva: SaveCitation = {
    group_id: crypto.randomUUID(),
    block_id: args.blockId,
    position: posicion,
    sources: [{ source_id: args.sourceId, locator: args.locator.trim().slice(0, 200) }],
  }
  args.setCitasLocales([...citasEfectivas(args.loaded, args.citasLocales), nueva])
  args.setPending(null)
  args.setNotice(
    `Cita local preparada en el párrafo (posición ${posicion}). Se confirma en el servidor al guardar la versión.`,
  )
  return true
}

/** Retira una cita (por group_id) del conjunto efectivo: sirve tanto para
 * deshacer una cita local sin guardar como para eliminar una cita ya
 * confirmada (el guardado reemplaza el manifiesto completo). */
export function quitarCita(args: {
  loaded: Loaded | null
  citasLocales: SaveCitation[] | null
  groupId: string
  setCitasLocales: Dispatch<SetStateAction<SaveCitation[] | null>>
  setPending: Dispatch<SetStateAction<PendingSave | null>>
  setNotice: Dispatch<SetStateAction<string | null>>
}): void {
  args.setCitasLocales(citasEfectivas(args.loaded, args.citasLocales).filter((c) => c.group_id !== args.groupId))
  args.setPending(null)
  args.setNotice("Cita retirada del borrador. El cambio se confirma al guardar la versión.")
}
