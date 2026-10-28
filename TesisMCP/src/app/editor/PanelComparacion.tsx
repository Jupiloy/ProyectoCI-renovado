import type { ChapterDocument, ChapterContentTree } from "../../api/types"
import { draftTextPreview } from "../editorDocument"
import type { Loaded } from "./tipos"

/** Comparación ante conflicto: versión vigente del servidor frente al
 * borrador local, para que el tesista decida con evidencia qué conservar. */
export function PanelComparacion({
  serverDocument,
  loaded,
  draft,
}: {
  serverDocument: ChapterDocument
  loaded: Loaded
  draft: ChapterContentTree | null
}) {
  return (
    <section className="chapter-compare" aria-label="Comparación de versiones">
      <div>
        <h2>Versión vigente del servidor</h2>
        <small>
          Versión {serverDocument.document_version} · {serverDocument.citations?.length ?? 0} grupos de citas
        </small>
        <pre>{serverDocument.content_md}</pre>
      </div>
      <div>
        <h2>Tu borrador local</h2>
        <small>
          {loaded.document.citations?.length ?? 0} grupos de citas heredados del borrador
        </small>
        <pre>{draft ? draftTextPreview(draft) : ""}</pre>
      </div>
    </section>
  )
}
