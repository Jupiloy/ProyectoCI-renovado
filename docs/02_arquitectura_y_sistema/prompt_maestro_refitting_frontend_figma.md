# Prompt maestro: re-fitting del frontend de Figma sobre la integración existente

**Fecha:** 27/10/2026. Documento-orden para el siguiente agente/chat. Antes de editarlo, lee el informe de continuidad `docs/02_arquitectura_y_sistema/continuidad_frontend_figma_refitting.md` (este prompt lo asume verificado al 27/10/2026).

## Prompt listo para pegar

```text
TAREA: RE-FITTING DEL FRONTEND DE TESISMCP — CONTINUAR LO EJECUTADO (BLOQUES R0, R1, R2 Y R5-LITE DE REVISIÓN QUEDAN HECHOS): FALTAN R3 (EDITOR), R4 (FUENTES), R5 (PANEL ASESOR COMPLETO) Y R6 (CIERRE). SIN ELIMINAR LO QUE YA FUNCIONA Y SIN DATOS FALSOS.

ESTADO DE EJECUCIÓN AL CORTE (27/10/2026, chat OpenCode — NO rehacer):
- Commits del header: 48a1ded (blindaje inicial), fc4e757 (R0-R2), e9d7ba3 (R5-lite). Verifica primero con `git log --oneline` y `git status --short`; el árbol debe estar limpio.
- HECHO: TesisMCP/src/app/base.tsx (Icon/Button/StatusBadge copiados del demo de Figma) y ShellWorkspace.tsx (AppShellTesis: sidebar/topbar reales con sesión, proyecto activo, rol OWNER/ADVISOR, descarga del borrador DOCX real, «Vista clásica» como respaldo; PanelPrincipal: saludo real, progreso N de M calculado de StepProgress+workflow, avance por capítulos con GET /chapters/{n}, próximo paso por order_index, recorrido vigente con versión real y aviso P26/P27, fuentes contadas con listSources). VistaRevision.tsx (Revisión de lectura: observaciones del asesor y snapshots con SHA real por capítulo). App.tsx: nueva vista «app» como destino al abrir proyecto; las pantallas de features/ se abren desde el shell y vuelven con onBack a vistaPantallas ('app' o 'workspace').
- PENDIENTE REGISTRADO: verificación visual en navegador de R1/R2/R5-lite (compilación tsc/build exit 0 verificada; la UI no fue probada por clics). Revalida al continuar.
- REGLA AL CONTINUAR: reutiliza src/app/base.tsx y AppShellTesis tal cual (no dupliques shell ni iconos); DemoApp.tsx sigue siendo solo-lectura; features/ sigue intacta como respaldo.

DIRECTORIO DE TRABAJO ÚNICO:
/home/janr/Documentos/Universidad/Apuntes_Obsidian/Estudiando/Ciclo7/Curso Integrador 1/ProyectoCI-renovado

Rol de directorios (verificado 27/10/2026):
- TesisMCP/ es el frontend activo conectado al backend Django. Trabaja SOLO ahí.
- TesisMCP/src/DemoApp.tsx (1617 líneas) es el diseño original de Figma, intacto: es tu ÚNICA referencia visual del producto (5 pantallas: student/Panel principal, Editor triple panel, Library/Fuentes, AdvisorDashboard y Review). No lo borres ni lo restiles fuera de lo necesario.
- TesisMCP/src/features/ contiene las pantallas que un agente anterior construyó por bloques (WorkflowScreen, LibraryScreen, AdvisorScreen, ChapterEditorScreen, AccessScreen, ProjectSelectionScreen, ConnectedProjectScreen, AIAssistantScreen, ResearchArtifactsScreen). DECISIÓN DEL USUARIO: consérvalas intactas como respaldo durante toda esta tarea. No las edites, no las borres.
- TesisMCP_Frontend/ es referencia antigua: no la toques.
- backend/ es el backend Django (Ninja) ya integrado: no lo modifiques salvo brecha acotada imprescindible, y entonces con prueba focalizada y registro explícito.

OBJETIVO:
La app conectada (acceso → proyecto → trabajo diario) debe usar el DISEÑO, la NAVEGACIÓN y los COMPONENTES del demo de Figma (sidebar oscuro, topbar, badges status-*, tarjetas, tres paneles del editor), pero con datos REALES de la capa src/api/. El modo demo de DemoApp debe seguir existiendo tal como está hoy (botón de demostración en la pantalla de acceso, sin mutar).

ARRANQUE OBLIGATORIO, ANTES DE EDITAR:
1. pwd; git status --short (el repo puede seguir sin commits; no descartes nada).
2. Lee completos: AGENTS.md, GUIA_AGENTE.md, TesisMCP/AGENTS.md, docs/02_arquitectura_y_sistema/continuidad_frontend_figma_refitting.md (el mapa pantalla↔API, §5, es tu especificación), continuidad_frontend_antigravity.md y matriz_integracion_frontend_backend.md.
3. Inspecciona físicamente TesisMCP/src/App.tsx, src/api/*.ts, src/DemoApp.tsx y la pantalla de features correspondiente al bloque. El código en disco prevalece sobre este prompt y sobre cualquier resumen.

ORDEN DE TRABAJO (un bloque a la vez; no avances si el anterior no compila):

R0. Respaldo: propone al usuario un commit local inicial del estado actual (revisa .gitignore primero; nada de medios/backups/secretos). Solo ejecuta si el usuario aprueba. Congela una copia del demo si aún no existe (por ejemplo demo_original_20261027/ fuera de src, para referencia de diseño).

R1. SHELL CONECTADO CON ASPECTO DE FIGMA. Crea el shell real (por ejemplo src/app/): mismo markup y clases que Sidebar, TopBar y componentes comunes del demo, pero alimentado por GET /auth/session (display_name real) y GET /projects/{id} (proyecto activo real, su estado y rol OWNER/ADVISOR de ProjectSummary). El punto de entrada pasa a ser este shell; DemoApp queda invocado solo desde el botón de demostración del AccessScreen, sin cambios funcionales. El indicador de guardado de la topbar se liga al estado real de concurrencia del editor (borrador/guardado/conflicto 409), no se imita.

R2. PANEL PRINCIPAL. Componente StudentDashboard adaptado a datos reales: saludo con display_name y hora del cliente; hero TÍTULO PROVISIONAL con ProjectState.title; progreso «N de M pasos» calculado con pasos COMPLETED reales (StepProgress) contra las tasks activas del GET /workflow; «Avance por capítulos» consultando Chapter status (GET /chapters/{n}) y mapeando con StatusBadge exacto: APPROVED→«Aprobado», CHANGES_REQUESTED→«Con observaciones», READY→«En revisión»; «En progreso» solo si el capítulo DRAFT tiene pasos IN_PROGRESS, «Borrador»/«No iniciado» en el otro caso (declara el criterio en la bitácora). PRÓXIMO PASO RECOMENDADO: primera task por order_index cuyo paso no esté COMPLETED; nunca un «9 de 32» fijo ni un paso recomendado inventado. RECORRIDO VIGENTE: conteo real de tasks del workflow publicado; conserva el aviso P26/P27 como decisión del profesor. Prohibidos: nombre del asesor si ningún endpoint lo entrega, «Licenciatura · 2025», cualquier métrica sin datos.

R3. EDITOR (bloque 2, el más delicado). Tres paneles con la disposición del demo usando datos reales: documento GET /chapters/{n}/document con el árbol content_tree VALIDADO con features/editor/editorDocument.ts (copia la función, no reescribas el contrato); guardado con expected_version + Idempotency-Key tal como ya lo hace la pantalla de Antigravity (reutiliza saveChapterDocument de src/api/chapters.ts); panel «versiones» con GET /chapters/{n}/snapshots (mostrar snapshot_no, SHA real, fecha); panel «comentarios» con GET/POST /chapters/{n}/comments y resolver según permisos can_review/can_edit (solo el asesor crea observaciones donde el backend lo aplique). Los componentes visuales del demo (Modal, TrackChange, AdvisorComment) pueden copiarse desde DemoApp hacia el shell real; no modificar DemoApp para esto.

R4. FUENTES. Tarjetas de fuente del demo alimentadas por listSources (SourceDocument) mapeando display_label, autores por cover (title_verified_against_cover), año, DOI y verification_status a los estilos status-* sin simular: TEXT_CHECKED→«Texto completo disponible», METADATA_CHECKED→«Solo metadatos», OCR_REQUIRED/PENDING_EXTRACTION→estados visibles honestos. Búsqueda de pasajes con searchPassages conservando la advertencia obligatoria «candidatos de recuperación semántica… no equivale a respuesta sintetizada ni verificación». Extractos con localizador físico (página real) y sin texto inventado.

R5. PANEL ASESOR + REVISIÓN. AdvisorDashboard del demo con GET /projects/advisor/dashboard (los únicos campos del contrato: project_name y status por capítulo; el resto queda vacío u omitido). Vista Revisión con snapshots, submit, decisión y resolver/sin resolver según rol real; el asesor ve el documento read-only si el contrato lo exige (según can_edit de su membresía). Nada de datos entre proyectos.

R6. CIERRE. Después de todos los re-fit: recorrer el flujo real de tesista y asesor en el shell nuevo (acceso, proyecto, panel principal, editor, guardado y conflicto 409, fuentes, panel asesor, revisión, exportación DOCX). Actualiza matriz_integracion_frontend_backend.md y agrega el corte a continuidad_frontend_figma_refitting.md (archivos tocados, contratos confirmados, comandos con exit codes, pendientes). Al final, una sola vez, python3 scripts/verify_project.py con entorno correctamente preparado (DJANGO_DEBUG=1, la DB de aislamiento documentada); declara [APROBADO_CON_EVIDENCIA / EXIT_CODE_0] solo si realmente sale 0.

REGLAS TÉCNICAS TRANSVERSALES:
- Reutiliza SIEMPRE los módulos de src/api (client, auth, projects, chapters, workflows, sources, research, reviews, exports, generation). No crees fetch ad hoc, no cambies contratos, no cambies formas de llamada.
- No introduzcas datos falsos, placeholders visuales con datos inventados, ni estados «demo» en la app conectada. Cada número que vea el usuario debe provenir de un GET o POST existente.
- Mantén el estilo del prototipo: usa las clases CSS ya existentes en src/index.css (app-shell, sidebar, status status-*, button button-*, tarjeta-…) y solo añade CSS nuevo si falta (con nombres no conflictivos).
- Maneja siempre los estados 401/403/404/409, carga, vacío y error igual que las pantallas de Antigravity (puedes copiar sus fragmentos de manejo de estado).
- No edites backend salvo brecha documentada y mínima. No toques TesisMCP_Frontend, TesisMCP/src/DemoApp.tsx (solo lectura), y TesisMCP/src/features/* (solo consulta).
- Verificación por bloque: cd TesisMCP && pnpm exec tsc --noEmit (exit 0) y pnpm run build (exit 0). No declares pruebas de UI por compilación; si usas navegador, registra la sesión, el proyecto y los datos usados; si no, marca «pendiente por navegador».
- No subas a GitHub, nada en la nube, nada con base activa ni secretos. Commits locales solo si el usuario aprueba.

SALIDA OBLIGATORIA POR BLOQUE (en la bitácora y en la respuesta al usuario):
1. Archivos nuevos/modificados con rutas relativas completas.
2. Contratos vivos observados (método, ruta, esquema, campos) y de dónde se copió cada componente del demo.
3. Comandos ejecutados con exit codes reales; qué quedó sin verificar y por qué.
4. Brechas honestas detectadas (contrato que falta en el backend, campo ausente) — documento, no simulación.
5. Siguiente bloque exacto.
```

## Notas de contexto firmes para el siguiente chat

- **Dónde se quedó el chat OpenCode (27/10/2026):** R0 (blindaje Git), R1 (shell Figma con datos reales), R2 (panel principal) y la vista Revisión de lectura (R5-lite) están ejecutados, compilados y commiteados (48a1ded → fc4e757 → e9d7ba3). Se detuvo por límite de contexto del chat, como pidió el usuario; **faltan exactamente R3, R4, R5 (asesor completo) y R6 (cierre con verify_project.py)**.
- Si el navegador está disponible, primero valida visualmente R1/R2/R5-lite (acceso → proyecto → shell Figma → panel, revisión) sobre datos de entorno aislado; la compilación ya verificó tipos y build, no la interfaz.
- La decisión del usuario (27/10/2026) sigue vigente: conservar `features/` de Antigravity como respaldo; el retiro final se decide con el usuario al cierre.
- Referencias: diseño objetivo `TesisMCP/src/DemoApp.tsx`; integración previa `continuidad_frontend_antigravity.md`; orden original del usuario `prompt_maestro_antigravity_frontend_restante.md`.
