import { ApiError } from "../../api/client"
import { getChapterDocument, getChapterState, saveChapterDocument } from "../../api/chapters"
import { unsupportedDocumentReason } from "../editorDocument"
import { editableCitations } from "./etiquetas"
import type { EditorCtx, PendingSave } from "./tipos"

/**
 * Guardado del borrador con `expected_version` e `Idempotency-Key`: envía el
 * intento, verifica la versión vigente del servidor y, ante cualquier
 * desalineación (409, CSRF, permiso, confirmación sin verificación), conserva
 * el borrador local y bloquea la escritura en lugar de descartar trabajo.
 */
export async function guardar(ctx: EditorCtx) {
  const {
    loaded,
    draft,
    writable,
    busy,
    needsSave,
    numeroCapitulo,
    pending,
    proyecto,
    csrfToken,
  } = ctx
  if (!loaded || !draft || !writable || busy || !needsSave || numeroCapitulo === null) return
  const intento: PendingSave =
    pending ?? {
      content_tree: structuredClone(draft),
      citations: editableCitations(loaded.document.citations),
      expected_version: loaded.document.document_version,
      idempotency_key: crypto.randomUUID(),
    }
  ctx.setPending(intento)
  ctx.setSaving(true)
  ctx.setError(null)
  ctx.setNotice(null)
  let confirmado = false
  try {
    const resultado = await saveChapterDocument(
      proyecto.project_id,
      numeroCapitulo,
      intento,
      csrfToken,
    )
    confirmado = true
    const [state, current] = await Promise.all([
      getChapterState(proyecto.project_id, numeroCapitulo),
      getChapterDocument(proyecto.project_id, numeroCapitulo),
    ])
    if (current.revision_id !== resultado.revision_id) {
      ctx.setWriteBlocked(true)
      ctx.setServerDocument(current)
      ctx.setError(
        "El servidor confirmó tu intento, pero existe una versión posterior. Se conserva tu borrador para revisarlo antes de continuar.",
      )
      return
    }
    const incompatible = unsupportedDocumentReason(current)
    if (incompatible) {
      ctx.setWriteBlocked(true)
      ctx.setError(incompatible)
      return
    }
    ctx.setLoaded({ state, document: current })
    ctx.setDraft(structuredClone(current.content_tree))
    ctx.setPending(null)
    ctx.setServerDocument(null)
    ctx.setWriteBlocked(state.status !== "DRAFT" && state.status !== "CHANGES_REQUESTED")
    ctx.setNotice(
      resultado.idempotent
        ? "El servidor confirmó este intento y su versión vigente."
        : "Cambios guardados y versión vigente comprobada.",
    )
  } catch (cause) {
    if (cause instanceof ApiError && cause.status === 401) {
      ctx.onUnauthorized()
      return
    }
    if (cause instanceof ApiError && cause.status === 404) {
      ctx.onAccessLost()
      return
    }
    if (confirmado) {
      ctx.setWriteBlocked(true)
      ctx.setError("El servidor confirmó el guardado, pero no se pudo consultar la versión vigente. Conservamos el intento para revalidarlo.")
    } else if (cause instanceof ApiError && cause.kind === "csrf") {
      try {
        await ctx.onRefreshCsrf()
      } catch {
        /* conservar borrador */
      }
      ctx.setError("Falló la protección CSRF. El borrador se conserva; vuelve a guardar para reintentar.")
    } else if (cause instanceof ApiError && cause.status === 409) {
      ctx.setWriteBlocked(true)
      ctx.setError("El documento cambió en el servidor o ya no admite edición. Tu borrador se conserva; recarga solo si deseas descartarlo.")
    } else if (cause instanceof ApiError && cause.kind === "permission") {
      ctx.setWriteBlocked(true)
      ctx.setError("Ya no tienes permiso para modificar este documento. El borrador se conserva solo en esta página.")
    } else {
      ctx.setError(cause instanceof Error ? cause.message : "No se confirmó el guardado. El borrador se conserva.")
    }
  } finally {
    ctx.setSaving(false)
  }
}

/**
 * Verificación honesta del conflicto: compara el borrador local con la versión
 * vigente del servidor y solo descarta el intento pendiente cuando el
 * contenido coincide exactamente (árbol + citas).
 */
export async function consultarVersionVigente(ctx: EditorCtx) {
  const { loaded, draft, busy, numeroCapitulo, pending, proyecto } = ctx
  if (!loaded || !draft || busy || numeroCapitulo === null) return
  ctx.setLoading(true)
  try {
    const [state, current] = await Promise.all([
      getChapterState(proyecto.project_id, numeroCapitulo),
      getChapterDocument(proyecto.project_id, numeroCapitulo),
    ])
    ctx.setServerDocument(current)
    const mismoArbol = JSON.stringify(current.content_tree) === JSON.stringify(draft)
    const mismasCitas =
      JSON.stringify(editableCitations(current.citations)) ===
      JSON.stringify(editableCitations(loaded.document.citations))
    const baseVigente =
      current.revision_id === loaded.document.revision_id &&
      current.document_version === loaded.document.document_version
    if (
      mismoArbol &&
      mismasCitas &&
      (!pending || !baseVigente) &&
      !unsupportedDocumentReason(current)
    ) {
      ctx.setLoaded({ state, document: current })
      ctx.setDraft(structuredClone(current.content_tree))
      ctx.setPending(null)
      ctx.setServerDocument(null)
      ctx.setWriteBlocked(state.status !== "DRAFT" && state.status !== "CHANGES_REQUESTED")
      ctx.setError(null)
      ctx.setNotice("El contenido local coincide con la versión vigente del servidor.")
    } else if (baseVigente && (state.status === "DRAFT" || state.status === "CHANGES_REQUESTED")) {
      ctx.setWriteBlocked(false)
      ctx.setError("El servidor aún muestra la versión anterior. Puedes reintentar el mismo guardado con su clave conservada.")
    } else {
      ctx.setWriteBlocked(true)
      ctx.setError("La versión vigente difiere de tu borrador. Este sigue local; recarga solo si aceptas descartarlo.")
    }
  } catch (cause) {
    if (cause instanceof ApiError && cause.status === 401) {
      ctx.onUnauthorized()
      return
    }
    if (cause instanceof ApiError && cause.status === 404) {
      ctx.onAccessLost()
      return
    }
    ctx.setError(cause instanceof Error ? cause.message : "No se pudo consultar la versión vigente.")
  } finally {
    ctx.setLoading(false)
  }
}
