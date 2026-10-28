import type { ChapterContentTree, ChapterDocument } from "../../api/types"

const fields: Record<string, string[]> = {
  heading: ["type", "id", "level", "text"],
  paragraph: ["type", "id", "text"],
  blockquote: ["type", "id", "text"],
  code_block: ["type", "id", "text"],
  bullet_list: ["type", "id", "items"],
  ordered_list: ["type", "id", "items"],
  data_table: ["type", "id", "table_version_id", "result_sha256", "caption"],
  figure: ["type", "id", "figure_version_id", "output_sha256", "caption"],
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

/** Si el backend evoluciona el esquema, el editor evita enviar un árbol que no comprende. */
export function unsupportedDocumentReason(document: ChapterDocument): string | null {
  const tree: unknown = document.content_tree
  if (!isRecord(tree) || (tree.schema_version !== 1 && tree.schema_version !== 2)
    || tree.schema_version !== document.schema_version || !Array.isArray(tree.blocks)) {
    return "La versión del árbol documental no es compatible con este editor."
  }
  if (Object.keys(tree).sort().join() !== "blocks,schema_version") return "El árbol tiene campos que este editor no reconoce."
  const ids = new Set<string>()
  const paragraphs = new Map<string, string>()
  for (const block of tree.blocks) {
    if (!isRecord(block) || typeof block.type !== "string" || !fields[block.type]
      || typeof block.id !== "string" || ids.has(block.id)
      || (tree.schema_version === 1 && (block.type === "data_table" || block.type === "figure"))) {
      return "El documento contiene un bloque desconocido o incompatible."
    }
    ids.add(block.id)
    if (Object.keys(block).sort().join() !== [...fields[block.type]].sort().join()) {
      return "Un bloque contiene campos no reconocidos."
    }
    if (block.type === "heading" && (typeof block.text !== "string" || !Number.isInteger(block.level) || Number(block.level) < 1 || Number(block.level) > 6)) return "Hay un encabezado incompatible."
    if (["paragraph", "blockquote", "code_block"].includes(block.type) && typeof block.text !== "string") return "Hay un bloque de texto incompatible."
    if (block.type === "paragraph") paragraphs.set(block.id, block.text as string)
    if (["bullet_list", "ordered_list"].includes(block.type)
      && (!Array.isArray(block.items) || !block.items.every((item) => typeof item === "string"))) return "Hay una lista incompatible."
    if (block.type === "data_table" && (typeof block.table_version_id !== "string" || typeof block.result_sha256 !== "string" || typeof block.caption !== "string")) return "Hay una tabla incompatible."
    if (block.type === "figure" && (typeof block.figure_version_id !== "string" || typeof block.output_sha256 !== "string" || typeof block.caption !== "string")) return "Hay una figura incompatible."
  }
  if (document.revision_id !== null && !Array.isArray(document.citations)) {
    return "La respuesta omitió las citas de una revisión canónica; se bloqueó la edición para protegerlas."
  }
  if (document.citations !== undefined) {
    if (!Array.isArray(document.citations)) return "Las citas del documento son incompatibles."
    for (const citation of document.citations) {
      if (!isRecord(citation) || typeof citation.group_id !== "string" || typeof citation.block_id !== "string"
        || !Number.isInteger(citation.position) || !Array.isArray(citation.sources)
        || !paragraphs.has(citation.block_id) || Number(citation.position) < 0
        || Number(citation.position) > Array.from(paragraphs.get(citation.block_id) ?? "").length
        || citation.sources.length < 1
        || !citation.sources.every((source: unknown) => isRecord(source) && typeof source.source_id === "string" && typeof source.locator === "string")) {
        return "Las citas del documento son incompatibles."
      }
    }
  }
  return null
}

/** Vista orientativa para comparar borradores; el PUT siempre usa content_tree. */
export function draftTextPreview(tree: ChapterContentTree): string {
  return tree.blocks.map((block) => {
    if (block.type === "heading") return `${"#".repeat(block.level)} ${block.text}`
    if (block.type === "bullet_list") return block.items.map((item) => `• ${item}`).join("\n")
    if (block.type === "ordered_list") return block.items.map((item, index) => `${index + 1}. ${item}`).join("\n")
    if (block.type === "data_table") return `[Tabla: ${block.caption}]`
    if (block.type === "figure") return `[Figura: ${block.caption}]`
    return "text" in block ? block.text : ""
  }).join("\n\n")
}
