import type { Dispatch, SetStateAction } from "react"
import type { ChapterBlock, ChapterContentTree } from "../../api/types"
import type { EditorCtx, PendingSave } from "./tipos"

/** Cambio de capítulo con confirmación honesta cuando hay trabajo local sin
 * guardar (borrador o intento pendiente): incrementa la secuencia de carga
 * para invalidar respuestas atrasadas y limpia el documento abierto. */
export function cambiarCapitulo(ctx: EditorCtx, numero: number) {
  if (numero === ctx.numeroCapitulo) return
  if (
    ctx.hasLocalWork &&
    !window.confirm(
      "Hay cambios sin guardar o un guardado pendiente de confirmar. Al cambiar de capítulo se descartará el borrador. ¿Continuar?",
    )
  ) {
    return
  }
  ctx.loadSequence.current += 1
  ctx.setLoaded(null)
  ctx.setDraft(null)
  ctx.setNumeroCapitulo(numero)
}

/** Operaciones de edición de bloques del borrador: actualizar, agregar,
 * quitar y reordenar. Quedan como funciones sobre el árbol y sus setters;
 * toda edición anula el intento de guardado pendiente. */
export function operacionesBloque(args: {
  draft: ChapterContentTree | null
  setDraft: Dispatch<SetStateAction<ChapterContentTree | null>>
  setPending: Dispatch<SetStateAction<PendingSave | null>>
  setNotice: Dispatch<SetStateAction<string | null>>
}) {
  const { draft, setDraft, setPending, setNotice } = args

  function setBloque(blockId: string, update: (block: ChapterBlock) => ChapterBlock) {
    setDraft((tree) =>
      tree
        ? { ...tree, blocks: tree.blocks.map((b) => (b.id === blockId ? update(b) : b)) }
        : tree,
    )
    setPending(null)
    setNotice(null)
  }

  function agregarBloque(type: "heading" | "paragraph" | "blockquote" | "code_block" | "bullet_list" | "ordered_list") {
    if (!draft) return
    const block: ChapterBlock =
      type === "heading"
        ? { type, id: crypto.randomUUID(), level: 2, text: "Nuevo encabezado" }
        : type === "bullet_list" || type === "ordered_list"
          ? { type, id: crypto.randomUUID(), items: ["Nuevo elemento"] }
          : { type, id: crypto.randomUUID(), text: type === "code_block" ? "" : "Nuevo texto" }
    setDraft({ ...draft, blocks: [...draft.blocks, block] })
    setPending(null)
  }

  function quitarBloque(blockId: string) {
    if (!draft) return
    setDraft({ ...draft, blocks: draft.blocks.filter((b) => b.id !== blockId) })
    setPending(null)
  }

  function moverBloque(index: number, delta: -1 | 1) {
    if (!draft) return
    const target = index + delta
    if (target < 0 || target >= draft.blocks.length) return
    const blocks = [...draft.blocks]
    const [item] = blocks.splice(index, 1)
    blocks.splice(target, 0, item)
    setDraft({ ...draft, blocks })
    setPending(null)
  }

  return { setBloque, agregarBloque, quitarBloque, moverBloque }
}
