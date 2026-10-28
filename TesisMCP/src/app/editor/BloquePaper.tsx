import { useRef } from "react"
import type { ChapterBlock } from "../../api/types"
import { isArtifact } from "./etiquetas"
import type { SaveCitation } from "./tipos"

/**
 * Un bloque del papel del editor: artefacto vinculado, encabezado, lista o
 * texto (paragraph/blockquote/code_block). Para los párrafos registra la
 * posición del cursor (selectionStart, unidades UTF-16) para anclar citas
 * nuevas, ofrece «Insertar cita» y muestra las citas ancladas con su acción
 * «Quitar»; mientras un bloque tenga citas su texto queda bloqueado para no
 * desplazar el offset Unicode (regla del backend, citation_occurrences.py).
 */
export function BloquePaper({
  block,
  index,
  total,
  citas,
  editable,
  onSetBloque,
  onMoverBloque,
  onQuitarBloque,
  onInsertarCita,
  onRetirarCita,
}: {
  block: ChapterBlock
  index: number
  total: number
  citas: SaveCitation[]
  editable: boolean
  onSetBloque: (blockId: string, update: (block: ChapterBlock) => ChapterBlock) => void
  onMoverBloque: (index: number, delta: -1 | 1) => void
  onQuitarBloque: (blockId: string) => void
  onInsertarCita: (blockId: string, indexUtf16: number | null) => void
  onRetirarCita: (groupId: string) => void
}) {
  const caret = useRef<number | null>(null)
  const anclado = citas.length > 0
  const esArtefacto = isArtifact(block)
  const esParrafo = block.type === "paragraph"

  function registrarCaret(elemento: HTMLTextAreaElement) {
    caret.current = elemento.selectionStart
  }

  return (
    <div className="paper-block">
      {esArtefacto ? (
        <div className="paper-artifact">
          <b>{block.type === "data_table" ? "Tabla" : "Figura"}: {block.caption}</b>
          <small>
            Artefacto vinculado ·{" "}
            {block.type === "data_table" ? block.table_version_id : block.figure_version_id}
          </small>
        </div>
      ) : block.type === "heading" ? (
        <div className="paper-heading-block">
          <select
            aria-label="Nivel del encabezado"
            value={block.level}
            disabled={!editable || anclado}
            onChange={(e) =>
              onSetBloque(block.id, (item) =>
                item.type === "heading" ? { ...item, level: Number(e.target.value) } : item,
              )
            }
          >
            {[1, 2, 3, 4, 5, 6].map((nivel) => (
              <option key={nivel} value={nivel}>Nivel {nivel}</option>
            ))}
          </select>
          <textarea
            aria-label="Texto del encabezado"
            className="paper-block-textarea heading"
            value={block.text}
            maxLength={20000}
            disabled={!editable || anclado}
            onChange={(e) =>
              onSetBloque(block.id, (item) =>
                item.type === "heading" ? { ...item, text: e.target.value } : item,
              )
            }
          />
        </div>
      ) : "items" in block ? (
        <textarea
          aria-label="Elementos de lista, uno por línea"
          className="paper-block-textarea"
          value={block.items.join("\n")}
          disabled={!editable}
          onChange={(e) =>
            onSetBloque(block.id, (item) =>
              "items" in item ? { ...item, items: e.target.value.split("\n") } : item,
            )
          }
        />
      ) : (
        <textarea
          aria-label="Texto del bloque"
          className={`paper-block-textarea ${block.type === "paragraph" ? "" : block.type}`}
          value={block.text}
          maxLength={20000}
          disabled={!editable || anclado}
          onSelect={(e) => {
            if (esParrafo) registrarCaret(e.currentTarget)
          }}
          onKeyUp={(e) => {
            if (esParrafo) registrarCaret(e.currentTarget)
          }}
          onClick={(e) => {
            if (esParrafo) registrarCaret(e.currentTarget)
          }}
          onChange={(e) =>
            onSetBloque(block.id, (item) =>
              "text" in item ? { ...item, text: e.target.value } : item,
            )
          }
        />
      )}
      {anclado && (
        <small className="paper-citations">
          {citas.map((c) => (
            <span key={c.group_id}>
              Cita anclada · posición {c.position} · {c.sources.length}{" "}
              {c.sources.length === 1 ? "fuente" : "fuentes"}
              {editable && (
                <button
                  className="text-link"
                  title="Retirar esta cita del borrador (se confirma al guardar la versión)"
                  onClick={() => onRetirarCita(c.group_id)}
                >
                  Quitar
                </button>
              )}
            </span>
          ))}
          {" · el texto está bloqueado para no desplazar el offset Unicode de la cita."}
        </small>
      )}
      {editable && !esArtefacto && (
        <span className="paper-block-actions">
          {esParrafo && (
            <button
              aria-label="Insertar cita en este párrafo"
              title="Anclar una cita a este párrafo en la posición del cursor (o al final del texto)"
              onClick={() => onInsertarCita(block.id, caret.current)}
            >
              Cita
            </button>
          )}
          <button aria-label="Mover bloque arriba" disabled={index === 0} onClick={() => onMoverBloque(index, -1)}>↑</button>
          <button aria-label="Mover bloque abajo" disabled={index === total - 1} onClick={() => onMoverBloque(index, 1)}>↓</button>
          <button
            aria-label="Eliminar bloque"
            title={anclado ? "No se puede eliminar mientras tenga citas" : "Eliminar bloque"}
            disabled={anclado}
            onClick={() => onQuitarBloque(block.id)}
          >
            ×
          </button>
        </span>
      )}
    </div>
  )
}
