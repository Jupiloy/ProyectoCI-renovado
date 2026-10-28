# Prompt maestro solo R6: cierre integral del re-fitting del frontend de Figma

**Fecha:** 27/10/2026. Orden final para un chat nuevo. Todo el trabajo de código del re-fitting (R0–R5) está commiteado y compilando; este chat NO debe crear pantallas nuevas ni refactorizar: es el cierre.

## Prompt listo para pegar

```text
TAREA: CIERRE INTEGRAL (R6) DEL RE-FITTING DEL FRONTEND DE TESISMCP. NO HAY TRABAJO NUEVO DE UI: SOLO VERIFICACIÓN, DOCUMENTACIÓN Y LA PUERTA GLOBAL. NO CREES PANTALLAS NI REFACTORIZAR EL VIEJO CÓDIGO.

DIRECTORIO DE TRABAJO ÚNICO:
/home/janr/Documentos/Universidad/Apuntes_Obsidian/Estudiando/Ciclo7/Curso Integrador 1/ProyectoCI-renovado

ARRANQUE OBLIGATORIO, ANTES DE NADA:
1. pwd; git log --oneline -9; git status --short (el árbol debe estar limpio y con los commits: 48a1ded blindaje, fc4e757 R0-R2, e9d7ba3 R5-lite, fa9639d R3, ed21ef0 R4, +1 commit de cierre de R5 del panel del asesor). Si falta algún commit o hay archivos modificados sin inferir qué es, pregunta al usuario: no descartes nada.
2. Lee completos: AGENTS.md (raíz), GUIA_AGENTE.md, TesisMCP/AGENTS.md, docs/02_arquitectura_y_sistema/continuidad_frontend_figma_refitting.md (§8–§10 describen TODOS los bloques ejecutados: shell real TesisMCP/src/app/ {base, ShellWorkspace, PanelPrincipal (en ShellWorkspace), VistaRevision, VistaEditor, VistaFuentes, VistaAsesor, editorDocument}; App.tsx con vista «app» y ramas tesis/editor/fuentes/asesor/revision).
3. Verificación de arranque: cd TesisMCP && pnpm exec tsc --noEmit (esperado exit 0) y pnpm run build (esperado exit 0). Si falla, detente e informa; el código no se toca sin causa registrada.

CONTEXTO FUNDAMENTAL (verificado; no lo contradigas):
- R0–R5 quedaron así: shell de Figma con datos reales (panel principal calcula avance con StepProgress+workflow, sin «8 de 32» fijo; aviso P26/P27), editor de tres paneles con guardado idempotente y 409 visible, biblioteca de fuentes real con jobs y pasajes, revisión de lectura del tesista y panel/ revisión completa del asesor (snapshots, observaciones ancladas, resolver, REQUEST_CHANGES/APPROVE/REOPEN).
- TesisMCP/src/DemoApp.tsx y TesisMCP/src/features/* NO se tocan (respaldo).
- La verificación visual en navegador NUNCA se ejecutó en toda la tarea (declare «pendiente por navegador» en cada bloque anterior). Idem la suite backend completa.

ORDEN DE TRABAJO DE R6:

R6.1 VERIFICACIÓN VISUAL EN NAVEGADOR (si hay navegador disponible; si no marca «pendiente por navegador» y continúa con R6.2):
  a. Sobre entorno aislado con datos sintéticos, levanta Django (backend, puerto 8000, DJANGO_DEBUG=1, DB de prueba documentada, NO la base activa) y Vite (pnpm --dir TesisMCP dev, proxy /api → 8000).
  b. Recorre el flujo del TESISTA: acceso → selección de proyecto → shell de Figma → Panel principal (progreso y avance por capítulos con datos reales, próximo paso calculado) → Editor (edición, guardado y releer; provocar 409 si es posible para ver el conflicto en pantalla) → Fuentes (listar, subir PDF pequeño, extractos, búsqueda de pasajes con su advertencia) → Revisión del tesista (observaciones y versiones) → «Descargar borrador (DOCX)» real.
  c. Recorre el flujo del ASESOR (cuenta con rol ADVISOR sintético): panel del asesor con GET /projects/advisor/dashboard → abrir proyecto → versión con SHA real → anclar observación por selección → resolver observación → Solicitar cambios → flujo del tesista hasta APPROVE (can_view/can_edit reales).
  d. Comprueba también «Vista clásica» (respaldo) y el modo demostración (DemoApp intacto), y móvil/reducción mínima del shell.
  e. REGISTRA paso a paso qué se probó, con qué datos y qué falló. NO marques nada aprobado por compilación.

R6.2 DOCUMENTACIÓN DE CIERRE:
  a. Actualiza docs/02_arquitectura_y_sistema/matriz_integracion_frontend_backend.md: filas de las pantallas reales de src/app/ (PanelPrincipal, VistaEditor, VistaFuentes, VistaRevision, VistaAsesor) con su endpoint(s) backend y estado (implementado / pendiente por navegador).
  b. Agrega a continuidad_frontend_figma_refitting.md un §11 «Cierre R6» con: comandos ejecutados + exit codes, qué se probó en navegador y qué quedó pendiente, las brechas honestas definitivas (p. ej. si el backend no entrega datos que la maqueta de Figma representaba), y el estado final del proyecto.
  c. NO edites prompt maestro ni bitácoras de bloques anteriores salvo el corte final mencionado.

R6.3 PUERTA GLOBAL (única vez, al final):
  - python3 scripts/verify_project.py con el entorno correctamente preparado (DJANGO_DEBUG=1, DATABASE_URL de aislamiento; NO la base activa). La puerta integra: auditoría grounded de PDFs, manage.py check, makemigrations --check, migrate --check, pytest, higiene de repo y consistencia doc-código.
  - Si falla: corrige SOLO lo del alcance (échale la culpa al re-fitting o a la doc nueva; si la causa está en R0–R5 o en bloques previos de la integración de bloques 1–8, corrige con cambio mínimo y registro; si está fuera de alcance, reporta el fallo tal cual).
  - Si pasa: declara al usuario el veredicto explícito [APROBADO_CON_EVIDENCIA / EXIT_CODE_0] con la tabla de evidencia: comando, tiempo, código de salida.
  - Commit final de la documentación actualizada. No subas a GitHub ni la nube. Nada con secretos o medios nuevos.

REGLAS TRANSVERSALES:
- El código del re-fitting ya está verificado con tsc/build exit 0; si el arranque muestra errores nuevos, documenta y pregunta, no improvises.
- Nada de datos inventados en la documentación: citas literales de rutas, endpoints y estados (los mismos verificados: /api/v1/projects/... StepProgress IN_PROGRESS/COMPLETED, Chapter DRAFT/READY/CHANGES_REQUESTED/APPROVED).
- No toques TesisMCP_Frontend/, DemoApp.tsx ni src/features/* (solo lectura).
- Preparación del entorno según AGENTS.md (la base de pruebas puede restaurarse desde backup aislado); nunca la base activa sin confirmación explícita del usuario.
```

## Notas firmes para el chat de R6

- Estado de partida: R0–R5 commiteados y en verde (tsc/build 0); la última evidencia del cierre de R5 está en `continuidad_frontend_figma_refitting.md` §10.
- Lo único que conquista R6: pruebas visuales reales, matriz actualizada, corte final en la bitácora y ejecución ÚNICA de `verify_project.py`.
- Si el navegador no está disponible en R6.1: quedaría declarado un pendiente honesto y R6 continúa con documentación y puerta global. No se simulan pruebas.
- Ante cualquier discrepancia entre este prompt, la bitácora y el código: prevalece el código en disco.
