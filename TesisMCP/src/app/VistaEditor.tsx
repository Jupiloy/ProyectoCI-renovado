import type { ProjectSummary } from "../api/types"
import { BarraSuperior } from "./editor/BarraSuperior"
import { ModalCita } from "./editor/ModalCita"
import { PanelAsistencia } from "./editor/PanelAsistencia"
import { PanelDocumento } from "./editor/PanelDocumento"
import { PanelComparacion } from "./editor/PanelComparacion"
import { PanelEstructura } from "./editor/PanelEstructura"
import { useEditorEstado } from "./editor/useEditorEstado"
import { operacionesBloque } from "./editor/operaciones"

/** re-export para compatibilidad con VistaFuentes, que las consume desde este
 * módulo desde antes de la división R7. */
export { etiquetaVerificacion } from "./editor/etiquetas"

/**
 * Editor del capítulo con la disposición de tres paneles del demo de Figma
 * (documento · versiones · observaciones) y datos reales de src/api.
 *
 * Este archivo es la vista: consume el estado y las acciones de
 * editor/useEditorEstado y compone la maqueta con BarraSuperior y los
 * paneles; no concentra lógica de datos.
 */
export function VistaEditor({
  proyecto,
  csrfToken,
  onUnauthorized,
  onAccessLost,
  onRefreshCsrf,
}: {
  proyecto: ProjectSummary
  csrfToken: string
  onUnauthorized: () => void
  onAccessLost: () => void
  onRefreshCsrf: () => Promise<void>
}) {
  const editor = useEditorEstado({ proyecto, csrfToken, onUnauthorized, onAccessLost, onRefreshCsrf })
  const bloques = operacionesBloque({
    draft: editor.draft,
    setDraft: editor.setDraft,
    setPending: editor.setPending,
    setNotice: editor.setNotice,
  })

  if (editor.numeroCapitulo === null && !editor.loading) {
    return (
      <main className="page">
        <p className="aviso">
          El recorrido publicado del proyecto no asigna capítulos con número, por
          lo que el editor no tiene documentos que abrir.
        </p>
      </main>
    )
  }

  return (
    <main className="editor-page">
      <BarraSuperior
        numeroCapitulo={editor.numeroCapitulo}
        loaded={editor.loaded}
        modoDocumento={editor.modoDocumento}
        onAbrirModo={editor.abrirVersion}
        estadoGuardadoTexto={editor.estadoGuardadoTexto}
        leftOpen={editor.leftOpen}
        onAlternarIzquierdo={() => editor.setLeftOpen(!editor.leftOpen)}
        rightOpen={editor.rightOpen}
        onAlternarDerecho={() => editor.setRightOpen(!editor.rightOpen)}
        writable={editor.writable}
        busy={editor.busy}
        draft={editor.draft}
        saving={editor.saving}
        pending={editor.pending}
        needsSave={editor.needsSave}
        onAgregarBloque={bloques.agregarBloque}
        onGuardar={editor.ejecutarGuardado}
      />
      <div
        className={`editor-workspace ${!editor.leftOpen ? "left-collapsed" : ""} ${!editor.rightOpen ? "right-collapsed" : ""}`}
      >
        {editor.leftOpen && (
          <PanelEstructura
            numerosCapitulo={editor.numerosCapitulo}
            numeroCapitulo={editor.numeroCapitulo}
            onCambiarCapitulo={editor.cambiar}
            loaded={editor.loaded}
            fuentes={editor.fuentes}
            tab={editor.leftTab}
            onTab={editor.setLeftTab}
          />
        )}
        <PanelDocumento
          error={editor.error}
          notice={editor.notice}
          esStale={!!editor.loaded?.document.is_stale}
          serverDocument={editor.serverDocument}
          loaded={editor.loaded}
          draft={editor.draft}
          modoSoloLectura={editor.modoSoloLectura}
          modoDocumento={editor.modoDocumento}
          rol={proyecto.role}
          snapshotDetalle={editor.snapshotDetalle}
          citasPorBloque={editor.citasPorBloque}
          editable={editor.writable && !editor.busy && editor.modoDocumento === "draft"}
          busy={editor.busy}
          onSetBloque={bloques.setBloque}
          onMoverBloque={bloques.moverBloque}
          onQuitarBloque={bloques.quitarBloque}
          onInsertarCita={editor.insertarCita}
          onRetirarCita={editor.retirarCita}
          onConsultarVigente={editor.ejecutarConsulta}
          onRecargar={editor.recargarBorrador}
        />
        {editor.rightOpen && (
          <PanelAsistencia
            tab={editor.rightTab}
            onTab={editor.setRightTab}
            projectId={proyecto.project_id}
            numeroCapitulo={editor.numeroCapitulo}
            draft={editor.draft}
            csrfToken={csrfToken}
            esPropietario={proyecto.role === "OWNER"}
            esAsesor={proyecto.role === "ADVISOR"}
            snapshots={editor.snapshots}
            cargandoVersion={editor.cargandoVersion}
            onAbrirVersion={(id) => editor.abrirVersion("snapshot", id)}
            comentarios={editor.comentarios}
            abiertas={editor.abiertas}
            resolviendoId={editor.resolviendoId}
            puedeResolver={proyecto.permissions.can_review_chapters}
            onResolver={editor.resolver}
            onUnauthorized={onUnauthorized}
          />
        )}
      </div>
      {editor.modalCita &&
        editor.draft &&
        (() => {
          const bloque = editor.draft.blocks.find((b) => b.id === editor.modalCita!.blockId)
          if (!bloque) return null
          return (
            <ModalCita
              bloque={bloque}
              indexUtf16={editor.modalCita.indexUtf16}
              fuentes={editor.fuentes}
              onCancelar={editor.cerrarModalCita}
              onConfirmar={editor.confirmarCita}
            />
          )
        })()}
    </main>
  )
}
