# Informe de continuidad: re-fitting del frontend de Figma sobre la capa de integración real

**Fecha:** 27/10/2026 · **Sesión de origen:** análisis OpenCode (GLM) a petición directa del usuario.
**Alcance:** `TesisMCP/` (frontend activo) y su conexión con el backend Django de este mismo repositorio.
**Propósito del documento:** dejar registrada, con evidencia verificable, la diferencia entre el diseño original de Figma (conservado) y la estructura que quedó tras la integración de Antigravity; definir el mapeo pantalla-Figma ↔ API real; y ser el punto de partida de un **re-fitting** (devolver el diseño de Figma a la app conectada) ejecutable por otro chat/agent.
**Historial relacionado:** la integración por bloques 1–8 de Antigravity está documentada en `docs/02_arquitectura_y_sistema/continuidad_frontend_antigravity.md`; la orden original es `docs/02_arquitectura_y_sistema/prompt_maestro_antigravity_frontend_restante.md`.

---

## 1. Contexto en palabras del usuario

> «Ya tengo el backend y a base de las funciones de ese backend se creó el frontend en Figma. Luego descargué el frontend que creó Figma para poder conectarlo con mi backend. Le pedí a Antigravity que conectara mi frontend con el backend; lo hizo, pero en el camino prácticamente modificó por completo mi frontend. El frontend de Figma original todavía lo tengo. ¿Puedes analizar el proyecto actual conectado y tomar esas conexiones como referencia para conectar el "frontend" original de Figma?»

### Decisiones ya registradas del usuario (27/10/2026)

1. **Conservar** las pantallas construidas por Antigravity en `TesisMCP/src/features/` como respaldo durante la migración (no borrarlas hasta decisión final del usuario).
2. No generar aún cambios de código en esta sesión: primero el presente informe y su prompt maestro (`docs/02_arquitectura_y_sistema/prompt_maestro_refitting_frontend_figma.md`).

---

## 2. Estado real verificado a 27/10/2026

### 2.1 Verificaciones ejecutadas en esta sesión de análisis (comando → resultado)

| Comando | Resultado |
|---|---|
| `cd TesisMCP && pnpm exec tsc --noEmit` | exit code 0 (0 errores de tipos) |
| `cd TesisMCP && pnpm run build` | exit code 0; `dist/assets/index-zGEu4PlL.js` 426.68 kB (gzip 115.41 kB), `index-BXA2owy0.css` 76.45 kB, build en 729 ms |
| Cruce endpoint-a-endpoint (grep de `src/api/*.ts` contra `backend/thesis/api/*.py`) | Sin brechas detectadas: todas las rutas que el cliente llama existen en el backend (incluida `PUT /{project_id}/workflow/draft` en `routes_workflows.py:14`) |
| Inspección física de `TesisMCP/src/DemoApp.tsx` (1617 líneas) y `TesisMCP/src/index.css` (956 líneas) | Diseño original de Figma intacto con modificaciones mínimas de Antigravity (ver §4) |

**No verificado en esta sesión (declarado explícitamente):** renderizado visual en navegador, pruebas HTTP con sesión real, `python3 scripts/verify_project.py` (aplazada al cierre integral por decisión del usuario registrada en el prompt anterior de Antigravity).

### 2.2 Dos frontends en el repositorio — roles oficiales

| Carpeta | Rol | Evidencia |
|---|---|---|
| `TesisMCP/` | **Frontend activo** conectado al backend Django | `prompt_maestro_antigravity_frontend_restante.md`: «TesisMCP/ es el frontend activo; TesisMCP_Frontend/ es referencia antigua»; `docs/07_desarrollo_prototipo/estado_version_producto.md` corte 27/10/2026 |
| `TesisMCP_Frontend/` | Referencia antigua (recorrido P01–P12) | Sin cambios desde el 21/10/2026 (timestamps de `App.tsx`, `RecorridoCapitulos.tsx`, `index.css`) |
| `TesisMCP/src/DemoApp.tsx` | **Diseño original de Figma** (5 pantallas), conservado como "modo demostración" | La orden a Antigravity: «la UI de la demo permanece separada» |

---

## 3. Arquitectura actual de la app conectada (obra de Antigravity, verificada en código)

### 3.1 Máquina de vistas (`TesisMCP/src/App.tsx`, 310 líneas, reescrito 27/10 18:57)

Lista de vistas `AppView`: `checking | access | projects | workspace | editor | workflow | library | advisor | ai | artifacts | demo` (línea 17).

Flujo real: sesión Django (`GET /api/v1/auth/session/`) → si no hay sesión o hay error de conexión: `AccessScreen` (login o demo) → con sesión: `ProjectSelectionScreen` (`GET /projects`) → proyecto abierto → `ConnectedProjectScreen` (hub con tarjetas) → pantallas por bloque: `ChapterEditorScreen`, `WorkflowScreen`, `LibraryScreen`, `AdvisorScreen`, `AIAssistantScreen`, `ResearchArtifactsScreen`. El modo demo activa `DemoApp` con `onExitDemo` (líneas 170–172).

### 3.2 Capa de API (`TesisMCP/src/api/`, 1927 líneas, 11 módulos) — REUTILIZABLE TAL CUAL

`client.ts` (116 líneas): `apiRequest`/`apiDownload` con `credentials: "include"`, cabeceras `X-CSRFToken`, `Idempotency-Key`, `If-Match`; clase `ApiError` con tipos `csrf | permission | unknown`; mensajes de error por estado 400/401/403/404/409/5xx en español. Se comparte con el backend vía proxy Vite (`vite.config.ts:41-46`, destino por defecto `http://127.0.0.1:8000`).

Módulos y endpoints verificados contra el backend (todos existen):

| Módulo cliente | Endpoints (relativos a `/api/v1`) | Verificado en backend |
|---|---|---|
| `auth.ts` | `GET /auth/session/`, `POST /auth/login/`, `POST /auth/logout/` | `config/auth_views.py`, `config/urls.py` |
| `projects.ts` | `GET /projects?...`, `POST /projects`, `GET /projects/{id}` | `routes_overview.py` |
| `chapters.ts` | `GET /projects/{id}/chapters/{n}`, `GET /projects/{id}/chapters/{n}/document` (+guardado), `GET …/citations/ieee`, evidencia de citas (GET/POST `citations/{oc}/evidence`), propuestas de reemplazo y decisión | `routes_chapters.py` |
| `workflows.ts` | `GET /projects/{id}/workflow`, `PUT /projects/{id}/workflow/draft`, `POST /workflow/validate`, `POST /workflow/publish`, `POST /workflow/restore`, `GET /workflow/tasks/{tid}/prompt`, `POST /workflow/tasks/{tid}/execute`, `GET /workflow/tasks/{tid}/executions` | `routes_workflows.py:14,20,25` |
| `sources.ts` | `GET /projects/{id}/sources`, `POST /sources/upload` (FormData), extractos/segmentos, `POST /passages/search`, jobs, descubrimiento (Semantic Scholar, Perú/ALICIA), estrategias de búsqueda, Zotero | `routes_sources.py` |
| `research.ts` | datasets, versiones, recetas de tabla, figuras PNG, descargas | `routes_research.py` |
| `reviews.ts` | `GET /projects/advisor/dashboard`, snapshots (GET lista/detalle), comentarios (`GET/POST /chapters/{n}/comments`, resolver), submit (`POST /chapters/{n}/submit`), decisión (`POST /chapters/{n}/decision`), invitaciones de apoyo | `routes_chapters.py` |
| `exports.ts` | `GET /projects/{id}/export/draft.docx`, `GET /chapters/{n}/export/approved.docx` | `routes_overview.py` |
| `generation.ts` | ai-jobs (GET job, diff, accept, reject, cancel; Generar con IA), ai-batches y síntesis | `routes_generation*.py` |

### 3.3 Pantallas de Antigravity (`TesisMCP/src/features/`, conservadas como respaldo)

`auth/AccessScreen.tsx` (4.8 KB), `projects/ProjectSelectionScreen.tsx` (12.6 KB), `projects/ConnectedProjectScreen.tsx` (8.6 KB), `editor/ChapterEditorScreen.tsx` (23.9 KB) + `editorDocument.ts` (validación de árbol documental), `workflow/WorkflowScreen.tsx` (53 KB), `library/LibraryScreen.tsx` (43 KB), `advisor/AdvisorScreen.tsx` (40 KB), `ai/AIAssistantScreen.tsx` (38 KB), `artifacts/ResearchArtifactsScreen.tsx` (41.8 KB) + `CitationReviewPanel.tsx` (14.7 KB). Todas compilan (tsc exit 0 del 27/10).

**Por qué el usuario percibe que "se desconfiguró":** la app conectada no sigue la navegación ni la maquetación del diseño de Figma; usa su propia estructura (acceso → lista → hub de tarjetas → pantallas grandes por bloque). El diseño de Figma solo es visible entrando al modo demostración.

---

## 4. Inventario del diseño original de Figma (`TesisMCP/src/DemoApp.tsx`)

Componentes internos y su función (números de línea verificados):

| Línea | Componente | Qué reproduce |
|---|---|---|
| 6–97 | `iconPaths`, `Icon` | set de iconos SVG propio |
| 99–122 | `Button` | botones con variantes primaria/secundaria/peligro/ghost |
| 124–154 | `statusMap`, `StatusBadge` | badges: «No iniciado», «En progreso», «En revisión», «Con observaciones», «Aprobado», «Pendiente» (+ variantes «(demo)») |
| 156–211 | `TopBar` | breadcrumb «Proyecto de tesis › Panel principal», indicador «Guardado hace unos segundos», pill MODO DEMOSTRACIÓN, avatar, botón «Salir de demostración» |
| 213–280 | `Sidebar` | marca «TesisMCP · Espacio académico», menú «Mi tesis / Editor / Fuentes / Panel asesor / Revisión (con badge 3)», tarjeta PROYECTO ACTIVO, bloque de descarga y perfil |
| 282–482 | `StudentDashboard` | saludo «Buenos días, Lucía», botón «Continuar redactando», hero TÍTULO PROVISIONAL con «8 de 32 pasos» y barra, «Avance por capítulos» (6 capítulos con estados), tarjeta PRÓXIMO PASO RECOMENDADO, panel RECORRIDO VIGENTE |
| 484–603 | `SourceRow`, `AssistantMessage`, `AdvisorComment`, `TrackChange` | piezas reutilizables de las pantallas |
| 605–981 | `Editor` | editor académico de tres paneles: documento, versiones y comentarios (con pedido de cita, diffs estilo track change) |
| 983–1144 | `Library` | biblioteca de fuentes con tarjeta por fuente, estados de acceso al texto, buscador de pasajes |
| 1146–1252 | `AdvisorDashboard` | dashboard del asesor con pendientes y navegación a Revisión |
| 1254–1384 | `Review` | revisión por capítulo con observaciones ancladas, convertir comentario en decisión |
| 1386–1482 | `Modal` | modales: cita, pedir datos, exportar |
| 1484–1571 | `LoginScreen` | selección de rol demo (tesista Lucía Campos / asesor Dr. Roberto Salas) |
| 1573–1616 | `DemoApp` | shell de las 5 pantallas + modales |

### 4.1 Qué tocó realmente Antigravity en el demo (todos los cambios son cosméticos y permisivos)

1. Añadió props de salida: `TopBar({ ..., onExitDemo })` (líneas 160, 165, 183: botón «Salir de demostración») y `DemoApp({ onExitDemo }: { onExitDemo: () => void })` (línea 1573).
2. Añadió sufijos «(demo)» a ciertos estados en `statusMap` (líneas 131–138: «Texto completo disponible (demo)», «Pendiente de revisión (demo)», «Solo metadatos (demo)») para diferenciar datos de maqueta.
3. No alteró el sistema visual: los tokens del prototipo permanecen en `src/index.css` (`--navy #102a43`, `--blue #1e5ea8`, Inter + Source Serif 4, `.sidebar`, `.status-*`, `.demo-pill`, `.app-shell`).

**Conclusión verificada:** el "desastre" percibido no es pérdida del diseño. El diseño está completo y compilando; lo que falló fue la **fidelidad visual del shell conectado**, que Antigravity construyó siguiendo el orden de bloques del backend y no la navegación de la maqueta.

---

## 5. Mapeo pantalla de Figma ↔ datos/endpoint real

Vocabulario de estados del backend (verificado en `backend/thesis/models/chapters.py`):

- `StepProgress.Status`: `IN_PROGRESS` («En curso»), `COMPLETED` («Completado»).
- `Chapter.Status`: `DRAFT` («Borrador»), `READY` («En revisión»), `CHANGES_REQUESTED` («Con observaciones»), `APPROVED` («Aprobado»).

Ojo: los badges de la maqueta usan casi el mismo vocabulario («En revisión», «Con observaciones», «Aprobado» son literales de los `TextChoices`). Solo «No iniciado» y «En progreso» no existen como estado de capítulo y corresponden a la lógica de pasos/avance calculada en el frontend.

| Zona del demo de Figma | Dato que la maqueta simula | Fuente real que la reemplaza (función de `src/api/`) | Notas honestas |
|---|---|---|---|
| Sidebar · perfil | «Lucia Campos · Tesista» | `SessionUser.display_name` (rol real: `ProjectSummary.role = OWNER/ADVISOR`) | Mostrar el nombre real de la sesión; el rol sale de membresías, no de la maqueta |
| Sidebar · PROYECTO ACTIVO | «Adopción de plataformas… · Licenciatura · 2025» | `ProjectState.name/title/status` (`GET /projects/{id}`) | No existe «nivel/año» en el contrato: no mostrar ese dato o se rompe la regla anti-inención |
| TopBar · «Guardado hace unos segundos» | autosave simulado | estados de guardado reales del editor (`saveChapterDocument` con `expected_version` + `Idempotency-Key`; manejo 409) | Mostrar guardado/borrador/conflicto según el resultado real |
| Panel principal · saludo | «Buenos días, Lucía» | `display_name` + hora local del cliente | El cálculo del saludo es de presentación; sin datos inventados |
| Panel principal · hero | «8 de 32 pasos · Ruta metodológica completada» | `WorkflowState.published` (`GET /projects/{id}/workflow`) + `StepProgress` = pasos `COMPLETED` reales del proyecto | **Prohibido** el «8 de 32» fijo: calcular desde datos actuales (regla del prompt original). Catálogo de 32 disponible en el workflow, no como constante visual |
| Panel principal · TÍTULO PROVISIONAL | título y «Asesor: Dr. Roberto Salas» | `ProjectState.title`; el asesor solo si el backend lo entrega | Si no hay endpoint con nombre del asesor, se omite o queda como brecha documentada |
| Panel principal · «Avance por capítulos» | 6 capítulos con estados («Aprobado», «En progreso», «Con observaciones», «No iniciado») | `GET /projects/{project_id}/chapters/{n}` (`ChapterState.status`) por cada capítulo, o `AdvisorDashboardProject.chapters` si el rol lo permite | Mapeo directo a `StatusBadge` del demo: `APPROVED→Aprobado`, `CHANGES_REQUESTED→Con observaciones`, `READY→En revisión`, `DRAFT→Borrador/En progreso según avance de pasos` |
| Panel principal · PRÓXIMO PASO RECOMENDADO | «Construye las bases teóricas · Paso 9 de 32 · Capítulo 2» | primer paso `IN_PROGRESS` (o sin completar) ordenado por `order_index` del workflow publicado | El backend no tiene endpoint de «recomendación»: se calcula en frontend; si nada está en curso, el primer `order_index` sin completar |
| Panel principal · RECORRIDO VIGENTE | «7 pasos seleccionados del catálogo de 32 · P26 y P27 señalados» | `WorkflowState.published.tasks` (conteo real) + `WorkflowDependency`/branch para P26–P27 («Definición metodológica pendiente con el profesor») | Mantener el aviso de P26/P27 tal como hizo `WorkflowScreen` |
| Botón «Continuar redactando» | → Editor | abrir capítulo activo en `ChapterDocument` | El editor debe apuntar al capítulo en curso, no al número fijo 2 |
| Editor · documento | texto de ejemplo con citas | `GET /chapters/{n}/document` (`ChapterDocument.content_tree`, schema v1/v2) | Reusar la validación de `features/editor/editorDocument.ts` para no romper el contrato del árbol |
| Editor · versiones | lista de versiones demo | `GET /chapters/{n}/snapshots` (`ChapterSnapshotSummary` con `content_sha256`) | Los hashes reales sustituyen a los de maqueta |
| Editor · comentarios | observaciones del asesor | `GET /chapters/{n}/comments` (`ReviewComment`: `start_cp`, `end_cp`, `selected_text`, `status OPEN/RESOLVED`) | Respetar permisos: solo el asesor escribe observaciones (`can_review_chapters`) |
| Fuentes | 4 fuentes con estados de acceso | `GET /projects/{id}/sources` (`SourceDocument.verification_status`: `TEXT_CHECKED`, `METADATA_CHECKED`, `OCR_REQUIRED`, `PENDING_EXTRACTION`) | Mostrar localizadores físicos (página, hash) como exige el proyecto; extractos y búsqueda de pasajes con el aviso de recuperación semántica |
| Panel asesor | pendientes de revisión demo | `GET /projects/advisor/dashboard` (`AdvisorDashboardProject`: name + status de capítulos) | El contrato devuelve poco: no inventar métricas de «última actividad» |
| Revisión | observaciones + decisión | `POST /chapters/{n}/submit`, `POST /chapters/{n}/decision`, resolver comentarios | La vista del asesor del documento es de solo lectura si el contrato lo exige |
| Modales (cita, exportar) | exportación demo | `exportDraftDocx` / `exportApprovedChapter` (`GET …/export/draft.docx` con `apiDownload`) | Solo DOCX que el backend entrega realmente; nada de PDF prometido |

---

## 6. Brechas honestas (no simulables, deben quedar visibles)

1. **«Próximo paso recomendado»**: no hay endpoint dedicado; se deriva de `StepProgress` + `order_index`. Si se implementa mal, fallaría silenciosamente: obligatorio entender primero `GET /workflow` y cómo `WorkflowScreen` calcula avance hoy.
2. **Asesor del proyecto**: el contrato no garantiza un endpoint con el nombre del asesor para el header del hero. Opción válida: omitirlo en el panel del tesista y mostrarlo en la vista de asesor donde sí hay datos reales.
3. **Indicador de guardado**: ligado a la lógica de concurrencia (`expected_version`, 409, borrador); no es cosmético.
4. **P26/P27**: deben conservarse visibles como decisión metodológica pendiente del profesor, con el mismo tratamiento que `WorkflowScreen`.
5. **Permisos**: `ProjectPermissions` (`can_read_project`, `can_edit_document`, `can_manage_workflow`, `can_review_chapters`) deben portar/deshabilitar botones del shell de Figma; la maqueta no tenía roles en cuenta.

---

## 7. Plan de re-fitting propuesto (bloques cerrados, uno a la vez)

| Bloque | Alcance | Criterio de cierre |
|---|---|---|
| R0 | Respaldo: commit local del estado actual (repo `main` **sin ningún commit** hoy) previa revisión de `.gitignore` con el usuario; congelar copia del demo (`DemoApp.tsx`) como referencia de diseño | `git log` con commit inicial; estado anterior recuperable |
| R1 | Shell conectado con diseño de Figma: sidebar real (proyecto activo, perfil de sesión), TopBar con estado de guardado real, punto de entrada demo intacto | Navegar sesión → proyecto con el aspecto de Figma; sin datos falsos |
| R2 | Panel principal: saludo, hero con progreso calculado, avance por capítulos real (`Chapter.status`), próximo paso calculado, recorrido vigente con aviso P26/P27 | Todos los números provienen de `GET /workflow`, `GET /chapters/{n}` o `StepProgress`; sin «8 de 32» fijo |
| R3 | Editor de tres paneles con documento/versiones/comentarios reales + manejo de conflicto 409 y permisos | Guardado ida/vuelta verificado por HTTP; comentarios según rol |
| R4 | Fuentes (biblioteca real + búsqueda de pasajes con avisos) | Estados de verificación y localizadores reales |
| R5 | Panel asesor + Revisión (roles reales OWNER/ADVISOR, submit, decisión, resolver) | Permiso correcto por rol; sin métricas inventadas |
| R6 | Cierre: matriz `matriz_integracion_frontend_backend.md` actualizada, bitácora ampliada, verificación integral `python3 scripts/verify_project.py` una sola vez con entorno preparado | Veredicto solo con exit code 0 |

**Regla transversal:** cada bloque: `pnpm exec tsc --noEmit` (exit 0) + `pnpm run build` (exit 0) + prueba HTTP focalizada cuando aplique; registrar comandos, exit codes y qué NO se probó (navegador u servicios externos). Las pantallas de `features/` permanecen intactas hasta que el usuario decida su retiro.

---

## 8. Chequeo de continuidad para el siguiente chat

- Arrancar por `docs/02_arquitectura_y_sistema/prompt_maestro_refitting_frontend_figma.md` (orden de trabajo lista para pegar).
- Este informe **no modifica código**; el estado del 27/10/2026 sigue siendo: integración de bloques 1–8 en `TesisMCP/`, tsc/build exit 0, demo intacto, repo Git sin commits.
- Ante cualquier discrepancia entre este documento y el código, el archivo en disco prevalece (regla del proyecto).

---

## 9. Corte de ejecución del chat OpenCode (27/10/2026, tarde)

El usuario pidió ejecutar el plan directamente en esta sesión y detenerse al acercarse al límite de contexto, actualizando el prompt maestro con «hecho / dónde quedó / qué falta».

**Ejecutado y commiteado (verificación tsc/build exit 0 por bloque):**

| Bloque | Estado | Commits y evidencia |
|---|---|---|
| R0 | ✅ Hecho | `48a1ded`: commit inicial (548 archivos tras revisión de `.gitignore`; `docs/antecedentes_descargados/` y `dist/` excluidos del historial sin borrarse del disco). Árbol limpio tras cada commit |
| R1 | ✅ Hecho | `fc4e757`: `TesisMCP/src/app/base.tsx` + `ShellWorkspace.tsx` — shell con diseño de Figma (sidebar/topbar) alimentado por sesión, proyecto y rol reales; borrador DOCX vía `downloadDraftDocx`; «Vista clásica» mantiene `ConnectedProjectScreen` accesible |
| R2 | ✅ Hecho | `fc4e757`: `PanelPrincipal` — saludo real por hora, heroe con progreso N de M de `StepProgress`+workflow, avance por capítulos (`Chapter.Status` mapeado a badges del demo), próximo paso por `order_index`, recorrido vigente con versión real y aviso P26/P27, fuentes contadas |
| R5-lite | ✅ Hecho | `e9d7ba3`: `VistaRevision.tsx` — Revisión de lectura del tesista (observaciones del asesor + snapshots con SHA real, selector de capítulo desde el workflow publicado); el elemento Revisión ya no está deshabilitado |

**Pendiente explícitos:** verificación visual en navegador (la sesión no tenía navegador: solo tsc/build/HTTP no; también quedó sin ejecutar suite backend). **Faltan:** R3 (editor de tres paneles real), R4 (biblioteca de fuentes real), R5 completo (panel de asesor: submit/decisión/resolver), R6 (cierre: matriz, bitácora y `verify_project.py` una vez).

El prompt maestro ya actualizado describe este corte al principio del bloque pegable (`ESTADO DE EJECUCIÓN AL CORTE`) y ordena reutilizar `src/app/base.tsx`/`AppShellTesis` sin duplicarlos.

---

## 10. Continuación: R3 y R4 (chat Antigravity posterior) + cierre de R5 (chat OpenCode, noche del 27/10)

**Chat que continuó la tarea (otro agente):** ejecutó y commiteó:
- `fa9639d` — R3: `TesisMCP/src/app/VistaEditor.tsx` (editor de tres paneles: documento real validado con árbol content_tree, guardado con `expected_version` + `Idempotency-Key` y conflicto 409 visible) + copia local de `editorDocument.ts`.
- `ed21ef0` — R4: `TesisMCP/src/app/VistaFuentes.tsx` (biblioteca real: estados de verificación, extractos con página física, subida de PDF con sondeo de job, búsqueda de pasajes con advertencia obligatoria).
- Quedó a mitad del R5: creó `VistaAsesor.tsx` (panel del asesor con dashboard y revisión: snapshots, observaciones ancladas por selección de texto, resolver, REQUEST_CHANGES/APPROVE/REOPEN) pero sin terminar: JSX truncado, sin rama de renderizado en `App.tsx`, sin commit.

**Cierre de R5 por el chat OpenCode (verificado con tsc/build exit 0):**
1. `VistaAsesor.tsx`: cerrados los 2 `<strong>` truncados (líneas 117/127).
2. `App.tsx`: añadida la rama `pantallaApp === "asesor"` que renderiza `VistaAsesor` dentro del shell (el chat anterior solo había importado el componente); eliminado el desvío al respaldo en `alConmutar`.
3. `base.tsx`: `Button` acepta prop `title` (la usaba `VistaAsesor` para documentar el botón «Solicitar cambios»).
4. Clases CSS usadas por `VistaAsesor` verificadas presentes en `index.css`.
5. Resultado: `tsc --noEmit` exit 0; `pnpm run build` exit 0 (490.33 kB gzip 131.19 kB).

**Pendientes hacia R6:** verificación visual en navegador (nunca ejecutada en toda la tarea), actualización de matriz/bitácora final y `python3 scripts/verify_project.py` única. La orden exacta para un chat nuevo está en `docs/02_arquitectura_y_sistema/prompt_maestro_cierre_r6_frontend_figma.md`.

---

## 11. Cierre R6: verificación visual en navegador, documentación y puerta integral (27/10/2026, noche)

Este cierre ejecuta la orden de `prompt_maestro_cierre_r6_frontend_figma.md`: R6.1 verificación visual real en navegador, R6.2 actualización de matriz y esta bitácora, y R6.3 la puerta integral `python3 scripts/verify_project.py` ejecutada **una sola vez**. No se agregó UI nueva ni refactorizaciones; los dos cambios de código surgieron de defectos heredados de `48a1ded` que impedían literalmente arrancar o usar la app, y se corrigieron como **fix mínimo** con decisión explícita del usuario («Fix mínimo (Recomendado)» en ambos casos).

### 11.1 Entorno aislado de verificación (ningún dato de la base activa)

| Componente | Valor literal |
|---|---|
| Base de datos | PostgreSQL `tesismcp_r6` en el contenedor podman `tesismcp-local-pg` (`DATABASE_URL=postgresql://tesismcp:tesismcp_local@127.0.0.1:5432/tesismcp_r6`); 64 migraciones aplicadas. La base activa `tesismcp` no fue usada ni tocada |
| Backend | `.venv/bin/python backend/manage.py runserver 127.0.0.1:8010 --noreload` con `PYTHONPATH=/tmp/opencode`, `DJANGO_DEBUG=1` y settings override `/tmp/opencode/dev_r6_settings.py` (MEDIA_ROOT `/tmp/opencode/r6_media`, CSRF_TRUSTED_ORIGINS `localhost:8443`); log `/tmp/opencode/django_r6.log` |
| Worker | `.venv/bin/python backend/manage.py run_document_worker` con la misma base; log `/tmp/opencode/worker_r6.log` |
| Frontend | `TESISMCP_API_TARGET=http://127.0.0.1:8010 pnpm dev` (Vite 8443, proxy `/api`); log `/tmp/opencode/vite_r6.log` |
| Puerto 8000 | Ocupado por un proceso ajeno preexistente (pid 128421, `runserver` en 127.0.0.1:8000, base `tesismcp_visual_smoke`): **no se tocó** |
| Datos sintéticos R6 | Sembrados con servicios reales del backend (no peticiones HTTP artificiales) mediante `/tmp/opencode/seed_r6.py` y `/tmp/opencode/seed_r6_continuacion.py`: usuarios `lucia.r6@demo.local` (Tesista) y `roberto.r6@demo.local` (Asesor), contraseña `R6-aislado-2026`; proyecto «R6 Aislado · Plataformas metodológicas» (id `567caee1-b6b6-430c-9d61-85a590b87f23`); workflow publicado v1 con 32 tareas; P01–P20 `COMPLETED` vía `save_step` con payloads literales de `mcp_server/demo/case_data.py`; Capítulo 1 `DRAFT` con documento, Capítulo 2 `READY` con 2 observaciones `OPEN`, Capítulo 3 `CHANGES_REQUESTED` con 1 observación, Capítulo 4 `APPROVED`; fuente INT1 con 34 páginas físicas y 34 extractos |

### 11.2 Fix mínimo backend — commit `d719f50`

Con el estado heredado de `48a1ded`, `manage.py check` fallaba con `NameError` por importaciones faltantes. Corrección de 1 línea por archivo, commiteada por separado:

- `backend/thesis/services/step_materializers/consistency.py`: `Project` añadido a la importación de la línea 3.
- `backend/thesis/services/ai_job_context.py`: `AIGenerationJob` añadido a las importaciones.

### 11.3 Fix mínimo shell — commit `108c269`

Durante la primera pasada por la vista Revisión del tesista, al seleccionar el Capítulo 3 la app quedó en **pantalla en blanco**. Causa verificada en consola del navegador: `TypeError: Cannot read properties of undefined (reading 'slice')` en `VistaRevision.tsx` (módulo servido por Vite, línea 295). Causa raíz en código: las vistas del shell usaban `s.content_sha256` / `s.snapshot_id` / `s.status` sobre el contrato real de snapshots del backend, que devuelve `id`, `payload_sha256`, `state_version`, `format_version`, `workflow_version_no`, `document_revision_id` y `created_at` (`backend/thesis/services/chapter_serialization.py`, `_snapshot_summary` y `_snapshot_detail`; confirmado por `GET /chapters/3/snapshots`).

Fix mínimo (4 archivos del shell; `src/features/` y `src/DemoApp.tsx` intactos):

- `TesisMCP/src/api/types.ts`: añadidos `ChapterSnapshotSummaryApi` y `ChapterSnapshotDetailApi` con el contrato real (los tipos sin sufijo se conservan porque el módulo legacy de demo los usa).
- `TesisMCP/src/app/VistaRevision.tsx`, `VistaEditor.tsx`, `VistaAsesor.tsx`: usos conmutados a los tipos reales (`key={s.id}`, `s.payload_sha256.slice(0, 12)`, `detalle.id`, y el rótulo truthful «Versión de estado {s.state_version}» en lugar del `status` inexistente).

Tras el fix: `pnpm exec tsc --noEmit` exit 0 y `pnpm run build` exit 0 (490.29 kB, gzip 131.22 kB), y la pantalla Revisión renderizó el Capítulo 3 sin crash (observación anclada «El diseño registra decisiones de instrumento pendientes con el profesor (P26 y P27)» con badge «Pendiente» y panel «VERSIONES ENVIADAS · Versión de estado 22 · SHA 9066e1618873…»).

### 11.4 R6.1 — recorrido probado en navegador (tab `tab_f33a4645-bf2a-4158-a8b6-7dddebad702c`)

**Como Tesista (Lucía):**

1. Login real (sesión + CSRF a través del proxy 8443→8010); pantalla «Mis proyectos» con rol Tesista.
2. Shell de Figma con proyecto activo real y «Estado 24» (luego 26 y 27 conforme operó la sesión).
3. Panel principal: saludo real, «20 de 32 pasos» calculado, capítulos con estados reales, próximo paso P21, aviso P26/P27, recorrido vigente v1.
4. Editor de tres paneles con el documento real del Capítulo 1 (P01–P05 verdes); panel Versiones con estado vacío honesto («Este capítulo no tiene versiones enviadas…»).
5. Edición de un bloque de texto + «Guardar versión»: `PUT /chapters/1/document` HTTP 200, `document_version: 2`, aviso «Confirmado por el servidor».
6. **Conflicto 409 provocado** (segundo `PUT` concurrente con `expected_version` desactualizado): la UI lo mostró («El documento cambió en el servidor o ya no admite edición. Tu borrador se conserva; recarga solo si deseas descartarlo.»), el documento pasó a solo lectura y quedó «Intento pendiente de confirmar» con «Reintentar guardado». Recuperación verificada por las dos salidas: «Consultar versión vigente» → panel «Comparación de versiones» con el texto del servidor (versión 3) y botones deshabilitados mientras se consulta; «Recargar y descartar borrador» → diálogo `confirm` nativo («Se descartarán los cambios locales o el intento pendiente. ¿Recargar del servidor?») → recarga a la versión 3 del servidor, editable y «Sin cambios locales».
7. «Descargar borrador (DOCX)»: `GET /projects/{id}/export/draft.docx` → archivo real descargado y verificado en disco (`Microsoft Word 2007+`, 39.117 bytes, contiene el título real del proyecto y los pasos P01–P05 sembrados).
8. Fuentes: listado de INT1 con metadatos reales (DOI `10.48550/arXiv.2502.07960`, «PÁGINAS FÍSICAS 34», «EXTRACTOS INDEXADOS 34», extracto «Página física 1» con la portada literal del paper); filtro con coincidencia («Multi-LLM» → «1 fuente») y sin coincidencia («0 de 1 fuentes»); búsqueda de pasajes **antes de indexar** → estado honesto `NO_INDEXED_PASSAGES` («No hay pasajes indexados para esta consulta…») bajo la advertencia obligatoria de recuperación semántica.
9. Subida de PDF por la UI (página 1 separada del PDF INT1 con `pdfseparate`, `r6_pag_1.pdf`, etiqueta «R6-aislado-pag1»): la fuente apareció como «USER_UPLOADED_FILE · Pendiente de extracción» con «Procesamiento: QUEUED (intentos 0)»; el worker ejecutó `PDF_EXTRACT SUCCEEDED` (parser Poppler, 1 página física, `verification_status: TEXT_CHECKED`) y la tarjeta pasó a «Texto completo disponible».
10. Búsqueda de pasajes **después de indexar** (indexación disparada por API — brecha B4): `POST /passages/search` HTTP 200 con candidatos reales («Página física 1», SHA `09c02828ba9a…`, distancia coseno 0.3933, rótulo «candidato no evaluado semánticamente»).
11. Revisión del tesista: Cap. 2 «2 total · 2 sin resolver», Cap. 3 «1 total · 1 sin resolver», versiones enviadas con SHA real (post-fix).
12. Editor: plegado y restauración de ambos paneles («Plegar panel izquierdo/derecho» ↔ «Mostrar navegación/Mostrar asistencia»); aviso honesto de proyección legada («El documento se creó con un estado anterior del proyecto. Revisa su contenido antes de guardarlo.»).

**Como Asesor (Roberto):**

13. Login real; «Mis proyectos» con rol Asesor; Panel principal compartido (saludo real «Buenas noches, Roberto»; hallazgo menor B7: el CTA «Continuar redactando» no se adapta al rol).
14. Panel asesor: métricas reales de `GET /projects/advisor/dashboard` («1 asignado», «1 en revisión», «1 con observaciones») y tarjeta del proyecto con «1 en revisión · 1 con observaciones · 1 aprobados».
15. Cap. 1 (DRAFT): ambos botones de decisión deshabilitados honestos y «Sin versiones enviadas todavía.».
16. Cap. 2 (READY): «Versión enviada disponible», «Solicitar cambios» habilitado, «Aprobar capítulo» bloqueado con el aviso «Resuelve o cierra las observaciones abiertas antes de aprobar (el backend lo exige)».
17. Observación anclada por selección real del texto (selección con `Range` sobre el documento + `mouseup`): caja «Nueva observación sobre «protocolos de herramientas…»» → «Registrar observación» → contador «2 abiertos» exacto y observación visible como «Pendiente».
18. «Marcar como atendida» sobre la observación sembrada: badge «Resuelta» y confirmación en BD (`status RESOLVED`).
19. «Solicitar cambios»: aviso «Decisión registrada: Con observaciones.» y estado `CHANGES_REQUESTED` confirmado en BD.
20. La aprobación quedó bloqueada correctamente tras el cambio de estado (el backend exige que el titular reenvíe). Al no existir el botón de envío en el shell (brecha B3), el reenvío se hizo por el contrato real documentado: `PUT /chapters/2/document` HTTP 200 (resincronización de `lock_version`; el primer intento de `POST /chapters/2/submit` devolvió **409 `CONTEXT_STALE`, evidencia de que la protección funciona**) y luego `POST /chapters/2/submit` HTTP 200 → `READY`.
21. «Aprobar capítulo» (habilitado con 0 observaciones abiertas): aviso «Decisión registrada: Aprobado.» y `APPROVED` confirmado en BD para el Cap. 2.

**Cierres transversales:**

22. «Vista clásica del proyecto (respaldo)»: accesible y renderiza con datos del servidor.
23. Modo demostración: `DemoApp` intacto; selector de rol demo, proyecto demo y banner «datos de ejemplo, no datos del backend» con la pill «MODO DEMOSTRACIÓN»; «Salir de demostración» funcional.
24. Responsive: breakpoints inspeccionados en `index.css` (1280/1180/920/900/800/700/620 px) y plegado de paneles probado; **no** se probó viewport < 1280 px (brecha B8, el entorno no permite redimensionar la ventana).

Capturas guardadas en `/tmp/opencode-browser-*/0/screenshot.jpeg` (7 tomas: panel principal, editor, conflicto 409, revisión del tesista post-fix, revisión del asesor con decisión, demo, editor con paneles plegados).

### 11.5 Brechas honestas registradas (no resueltas en R6, con evidencia)

1. **B3 — El shell no expone «Enviar a revisión»**: `submitChapter` (`TesisMCP/src/api/reviews.ts:16`) no se usa en `src/app/`; solo el módulo legacy (`src/features/advisor/AdvisorScreen.tsx:241`). El tesista no puede enviar un capítulo a revisión desde el shell de Figma.
2. **B4 — El shell no expone «Indexar pasajes»**: el endpoint `POST /api/v1/projects/{id}/sources/{id}/index` existe (`backend/thesis/api/routes_evidence.py:64`, job `INDEX`) pero `VistaFuentes.tsx` no tiene acción que lo invoque; sin indexación, la búsqueda de pasajes siempre responde `NO_INDEXED_PASSAGES` (comportamiento honesto, pero sin camino desde la UI).
3. **B5 — P18 inaccesible en `CONFIGURABLE_GRAPH`** (hallazgo del sembrado, no de la UI): la dependencia de plantilla exige `P17.patrones_metodologicos` y el contrato `P17Output` (con `extra="forbid"`) no admite ese campo; error literal «Dependencias no satisfechas para P18: completa P17.patrones_metodologicos». El sembrado usó `LEGACY_SEQUENTIAL`.
4. **B6 — Markdown literal en bloques**: un encabezado escrito como «## 1.1 Problema» dentro de un bloque de párrafo se muestra como texto crudo (el editor muestra `content_md` sin resintaxis de markdown); el documento no se corrompe pero la vista no renderiza la jerarquía.
5. **B7 — CTA del asesor no adaptado por rol**: el Panel principal del asesor muestra «Continúa con tu investigación desde el último avance guardado. / Continuar redactando», herencia de la vista del tesista.
6. **B8 — Viewport angosto no probado en navegador**: sin herramienta de redimensionamiento en el entorno; verificado por inspección de breakpoints CSS y plegado de paneles.

### 11.6 R6.3 — Puerta integral `python3 scripts/verify_project.py`

Ejecutada **una sola vez** en el cierre, con entorno aislado (`DJANGO_DEBUG=1`, `DATABASE_URL=postgresql://tesismcp:tesismcp_local@127.0.0.1:5432/tesismcp_r6`; pytest creó su propia base de prueba derivada, la base activa `tesismcp` no fue usada):

| Comprobación | Tiempo | Resultado literal del verificador |
|---|---|---|
| Auditoría Grounded (PDFs) | 6.91 s | 9/9 PDFs físicos validados (títulos y cifras literales) |
| `manage.py check` | 2.38 s | 0 errores o advertencias en configuración Django |
| `makemigrations --check --dry-run` | 2.23 s | 0 discrepancias entre modelos y archivos de migración |
| `migrate --check --database default` | 2.15 s | Sin migraciones pendientes en DATABASE_URL; no se aplicaron cambios |
| `pytest --reuse-db -q` | 507.23 s | Suite superada al 100 % (223 pruebas en verde) |
| Higiene de repositorio | 4.81 s | Árbol limpio: sin archivos masivos, sin residuos y con `.gitignore` íntegro |
| Consistencia doc-código | 2.06 s | 58 modelos, 44 migraciones, 32 pasos, 34 herramientas MCP, 35 prompts, 94 Markdowns con 0 enlaces rotos |
| Auditoría adversaria | 0.00 s | Contratos Pydantic estrictos (`extra='forbid'`) y 0 mocks en servicios de producción |

**Resultado: 8/8 comprobaciones exitosas · 527.77 s · veredicto del verificador `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]`.** El propio verificador aclara que esto no acredita validez científica, integraciones externas ni disponibilidad de despliegue.

### 11.7 Estado final y alcances del cierre R6

- **Commits del cierre:** `d719f50` (fix mínimo backend), `108c269` (fix mínimo shell), y el commit de esta documentación. Nada se subió a GitHub (decisión del usuario).
- **Verificado en navegador de punta a punta** (tesista y asesor, con los datos R6 aislados de §11.1) y **puerta integral en verde**.
- **No verificado / brechas abiertas:** B3 (sin botón «Enviar a revisión» en el shell), B4 (sin acción «Indexar pasajes» en el shell), B5 (P18 inaccesible en `CONFIGURABLE_GRAPH`), B6 (markdown literal en bloques), B7 (CTA del asesor heredado del rol tesista), B8 (viewport < 1280 px sin probar). Generación con IA, tablas/figuras, citas IEEE/evidencia, Zotero y discovery **no se probaron en navegador en R6** (fuera del alcance acordado para este cierre).
- **Artefactos de verificación:** scripts de sembrado y logs en `/tmp/opencode/` (`seed_r6.py`, `seed_r6_continuacion.py`, `dev_r6_settings.py`, `django_r6.log`, `worker_r6.log`, `vite_r6.log`); la base `tesismcp_r6` y el servicio quedan documentados aquí y pueden eliminarse sin afectar la base activa.

---

## 12. Evaluación de estructura del código del shell (27/10/2026, tras el cierre R6)

A petición expresa del usuario («¿has estructurado el código del frontend como normalmente se haría? porque no es ético tener archivos con grandes cantidades de código abarrotados»), se midió físicamente el tamaño de los archivos del frontend con `wc -l`. Resultado literal (orden descendente; solo los relevantes):

| Archivo | Líneas | Evaluación honesta |
|---|---|---|
| `src/DemoApp.tsx` | 1.617 | Diseño original de Figma, **congelado por decisión del usuario** (modo demostración). No se estructura: es el respaldo del diseño |
| `src/app/VistaEditor.tsx` | 954 | **Sobredimensionado**: mezcla 7 responsabilidades (carga de documento, panel de estructura, bloques editables, guardado con `expected_version`/`Idempotency-Key`, conflicto 409, panel de versiones, observaciones) en un solo componente |
| `src/api/types.ts` | 705 | Barrel de tipos: convención aceptada; sin queja |
| `src/app/VistaAsesor.tsx` | 590 | Grande: dashboard + revisión + anclaje de observaciones con lógica de `Range` en un archivo |
| `src/app/ShellWorkspace.tsx` | 474 | Moderado, aceptable |
| `src/app/VistaFuentes.tsx` | 457 | Moderado, aceptable |
| `src/App.tsx` | 417 | Moderado (máquina de vistas), aceptable |
| `src/api/*` (resto) | 21–227 | Capa bien separada: 11 módulos pequeños por dominio; sin queja |

**Origen de la deuda (registrado sin maquillar):** las vistas las construyeron los bloques R3–R5 (`fa9639d`, `ed21ef0`, `1103b68`, por otros chats) bajo la regla explícita del plan de re-fitting de «bloques cerrados sin refactorizaciones»: la prioridad era conectar datos reales conservando el diseño de Figma, no el orden interno. El cierre R6 solo aplicó fixes mínimos (`d719f50`, `108c269`). La deuda es deliberada, no accidental; la objeción del usuario es válida igualmente.

**Decisión del usuario (27/10/2026): opción 1 — registrar y aplazar.** No se refactoriza ahora. Motivo aceptado: conviven todavía los respaldos de Antigravity en `src/features/` (`WorkflowScreen.tsx` ~53 KB, `ResearchArtifactsScreen.tsx` ~41.8 KB, `LibraryScreen.tsx` ~43 KB, `AdvisorScreen.tsx` ~40 KB); dividir hoy implicaría reorganizar archivos que el usuario podría retirar después, es decir, trabajo doble. La división se hará como bloque futuro (**R7**) cuando se decida el retiro de `src/features/`.

**Alcance propuesto de R7 (para cuando se ejecute):** extraer de `VistaEditor.tsx` subcomponentes (panel de estructura, panel de documento, panel de versiones, panel de observaciones) y hooks de estado (carga/guardado/conflicto) apuntando a archivos de ~100–200 líneas, con idéntico comportamiento y apariencia; mismo tratamiento para `VistaAsesor.tsx`. Red de seguridad disponible: suite backend en verde (223 pruebas), tsc/build exit 0 y recorrido ya verificado en navegador (§11.4); tras la división se repetirán tsc, build, puerta integral y verificación visual focalizada.

> **Nota posterior:** la división R7 se ejecutó ese mismo día (27/10/2026) a petición expresa del usuario, que cambió su decisión de aplazar. Ver §13.

---

## 13. Bloque R7: división del shell sobredimensionado (27/10/2026, noche)

### 13.1 Decisión y alcance confirmados por el usuario

Tras el registro de la deuda en §12 (opción 1: aplazar), el usuario cambió su decisión y pidió ejecutar la organización de inmediato: «de hecho prefiero que ya hagamos la organizacion segun la estructura, sin pasarse de muchas lineas codigo y cada una su funcion». Alcance confirmado en preguntas directas:

- **Solo los sobredimensionados:** `src/app/VistaEditor.tsx` (954) y `src/app/VistaAsesor.tsx` (590). Los moderados (`ShellWorkspace.tsx` 474, `VistaFuentes.tsx` 457, `App.tsx` 417) no se tocan.
- **Techo guía ~200 líneas por archivo nuevo.**
- **Verificación completa estilo R6:** tsc + build, verificación visual focalizada en navegador y puerta integral `scripts/verify_project.py` con exit 0.

### 13.2 Estructura resultante (medida con `wc -l` tras la división)

**Editor del capítulo — `src/app/editor/` (11 módulos + orquestador):**

| Archivo | Líneas | Responsabilidad única |
|---|---|---|
| `editor/PanelComparacion.tsx` | 34 | Comparación versión vigente vs borrador (conflicto) |
| `editor/versiones.ts` | 61 | Acciones: abrir modo (draft/submitted/snapshot) y resolver observación |
| `editor/etiquetas.ts` | 71 | Etiquetas de estado/verificación + helpers puros (`editableCitations`, `estadoGuardado`, `getWorkflowRecursos`) |
| `editor/operaciones.ts` | 75 | Cambio de capítulo con confirmación + operaciones de bloques (actualizar/agregar/quitar/mover) |
| `editor/BarraSuperior.tsx` | 121 | Barra de título y toolbar (modos del documento, guardado, inserción de bloques, plegado) |
| `editor/PanelAsistencia.tsx` | 124 | Panel derecho: pestañas Versiones y Observaciones |
| `editor/carga.ts` | 127 | Hook `useCargaCapitulo`: estado + documento + snapshots + comentarios con guardia de secuencia |
| `editor/guardado.ts` | 162 | Acciones: guardar con `expected_version`/`Idempotency-Key` y consultar versión vigente (todas las ramas de error) |
| `editor/PanelEstructura.tsx` | 98 | Panel izquierdo: estructura (capítulos y pasos) y fuentes |
| `editor/PanelDocumento.tsx` | 205 | Área central: avisos, bloques editables con citas ancladas, banner de solo lectura |
| `editor/tipos.ts` | 60 | Tipos compartidos + interfaz `EditorCtx` |
| `src/app/VistaEditor.tsx` | 126 | Orquestador: consume `useEditorEstado` y compone la maqueta |

Más `editor/useEditorEstado.ts` (260): estado del editor, efectos, contexto y acciones enlazadas (responsabilidad única: estado y acciones; el mayor archivo nuevo y se declara honestamente que excede la guía en 60 líneas).

**Asesor — `src/app/asesor/` (8 módulos + orquestador):**

| Archivo | Líneas | Responsabilidad única |
|---|---|---|
| `asesor/etiquetas.ts` | 10 | Etiquetas de estado de capítulo |
| `asesor/PanelVersionesAsesor.tsx` | 42 | Historial de versiones enviadas (SHA real) |
| `asesor/anclaje.ts` | 46 | Traducción Range → offsets Unicode (`calcularAnclaje`, función pura) |
| `asesor/ComentariosMarginales.tsx` | 61 | Comentarios marginales con acción «Marcar como atendida» |
| `asesor/DocumentoRevision.tsx` | 70 | Documento de solo lectura + caja de observación anclada |
| `asesor/carga.ts` | 89 | Hook `useCargaRevision` con guardia de secuencia |
| `asesor/RevisionHeader.tsx` | 93 | Cabecera: volver, estado real, decisiones con «Aprobar» bloqueado por observaciones abiertas |
| `asesor/acciones.ts` | 125 | Acciones: abrir versión, registrar observación, decidir, resolver |
| `src/app/VistaAsesor.tsx` | 162 | Dashboard (GET /projects/advisor/dashboard) + composición de la revisión |

**Comportamiento idéntico garantizado por construcción:** el JSX se movió textual; la lógica de red se trasladó con los mismos cuerpos y dependencias; los estados derivados (`dirty`, `needsSave`, `writable`, `busy`) conservan sus expresiones. Los contextos `EditorCtx`/`RevisionCtx` pasan los valores del render vigente al momento del evento, con la misma semántica de cierre que la versión monolítica.

**Compatibilidad sin cambios en consumidores:** `App.tsx` sigue importando `./app/VistaEditor` y `./app/VistaAsesor`; `VistaFuentes.tsx` sigue importando `etiquetaVerificacion` desde `./VistaEditor` (re-exportado); `etiquetaEstadoCapitulo` se re-exporta desde `VistaAsesor`. `src/features/` y `src/DemoApp.tsx` quedan intactos.

### 13.3 Verificación ejecutada

1. **tsc:** `npx tsc --noEmit` → exit 0 (se corrigieron en el camino: rutas relativas de subcarpetas, prop faltante `needsSave` en `BarraSuperior`, `isArtifact` reubicado en `etiquetas.ts`).
2. **Build:** `npm run build` → exit 0 (62 módulos; bundle 497.55 kB).
3. **Navegador (tab `tab_3caaaa0a-e6ec-4b42-806f-ec167ec81dd7`, entorno aislado R6 de §11.1):**
   - Tesista (Lucía): carga del Editor con 7 capítulos y pasos P01–P05 reales; edición de bloque → «Cambios sin guardar» → «Guardar versión» → aviso «Cambios guardados y versión vigente comprobada.» con versión 3→4 del Cap 1; **conflicto 409 provocado por servicios Django** (script `/tmp/opencode/conflicto_r7.py`, sube el Cap 1 a lock_version 5 por detrás de la UI) → banner «El documento cambió en el servidor o ya no admite edición.» + «Consultar versión vigente» → error «La versión vigente difiere de tu borrador.» + panel de comparación con ambos textos → «Recargar y descartar borrador» → diálogo nativo aceptado → recarga editable de la v5 («Sin cambios locales»); plegado/desplegado de ambos paneles (`left-collapsed`/`right-collapsed`); pestaña Fuentes con 2 fuentes reales («Texto completo disponible»); pestaña Observaciones honesta («No hay observaciones registradas para este capítulo.»).
   - Asesor (Roberto): dashboard real (1 asignado, 0 READY, 1 con observaciones, 2 aprobados — estados consistentes con los finales de R6 y con la edición posterior del Cap 1); revisión del Cap 3 (CHANGES_REQUESTED): cabecera «Con observaciones · Versión enviada disponible», versiones con SHA `9066e1618873…`, documento `content_md`, comentario con cita anclada «El diseño registra…», «Aprobar capítulo» deshabilitado (estado ≠ READY); anclaje por selección real → caja «Nueva observación sobre «logía El estudio adopta un enfoque cual…»» → Cancelar cierra sin crear; plegado del historial de versiones; vista Revisión (archivo no tocado) sin regresión; Editor como asesor con banner «El asesor puede consultar el documento, pero no editarlo.» y sin botones de inserción.
   - **Cero errores de consola no provocados** (el único registro es el 409 deliberado de la prueba de conflicto). Captura de evidencia del editor como asesor tomada al cierre.
   - No se re-ejecutó «Marcar como atendida» en Cap 3 para preservar el estado documentado de la base aislada (su lógica es mecánicamente idéntica a la verificada en R6 pre-división).

### 13.4 Estado del bloque R7

- Sin cambios de contrato, endpoints ni estilos. Nada subido a GitHub.
- Puerta integral: ejecutada tras el commit de esta sección (ver resultado al final de esta bitácora).

---

## 14. Inventario de brechas demo ↔ shell ↔ backend (27/10/2026)

A petición del usuario («comparando el modo demostración con el modo normal… nos falta bastante formas de integrarlo… zotero tampoco lo veo agregado, las funciones que soporta en teoría el backend no se reflejan en el frontend»), se levantó un inventario con verificación física de los tres lados: `src/DemoApp.tsx` (maqueta, 1617 líneas), `src/app/` (shell real) y `backend/thesis/` (contratos reales). Resultado de la puerta integral R7 previa a este inventario: 8/8 PASÓ, 468.86 s, exit 0.

### 14.1 Funciones del demo que el shell NO conecta (con línea literal del demo)

**Editor:**

| # | Función del demo | Estado en shell | Sustento backend real |
|---|---|---|---|
| A1 | Formato en línea: Normal/Título 1/2, Negrita, Cursiva (`DemoApp.tsx:658-671`) | No existe | **Sin sustento en contrato**: `ChapterTextBlock` solo modela `heading/paragraph/blockquote/code_block/bullet_list/ordered_list` (`src/api/types.ts:54-56`); implementarlo exige cambio de contrato backend |
| A2 | «Insertar cita» con modal APA 7/Vancouver (`DemoApp.tsx:673, 1403-1476`) | Citas se conservan y anclan al guardar, pero no hay UI para insertarlas | Real: `PUT …/document` acepta `citations[]`; existe `GET …/chapters/{n}/citations/ieee` y `getChapterIeeeCitations()` en `src/api/reviews.ts` sin consumir |
| A3 | Menú de selección «Mejorar redacción / Sintetizar / Buscar respaldo / Insertar cita» (`DemoApp.tsx:831-835`) | No existe | Real vía IA: `ai-jobs` (accept/reject/document-diff) y `POST …/passages/search` |
| A4 | Pestañas «Consultar fuentes» / «Propuestas» en panel derecho (`DemoApp.tsx:850-856`) | Panel derecho solo Versiones/Observaciones | `searchPassages()` existe en `src/api/sources.ts:85` y solo se usa en `VistaFuentes` |
| A5 | TrackChange con Aceptar/Descartar (`DemoApp.tsx:573-605, 803`) | No existe | Real: `ai-jobs/{id}/document-diff` + accept/reject (`routes_generation_decisions.py`) |
| A6 | Botón «Comentar» en editor del tesista (`DemoApp.tsx:677`) | No existe | **Misleading**: `addComment` es acción de asesor (403 para tesista) |
| A7 | Modal Exportar DOCX/**PDF** (`DemoApp.tsx:190, 1403-1476`) | Solo «Descargar borrador (DOCX)» | `routes_overview.py:33,44` define solo `draft.docx` y `approved.docx`; **no existe exportación PDF en el backend** |

**Biblioteca/Fuentes:** «Conectar Zotero» (`DemoApp.tsx:992-1001`), filtros por Autor/Año/Institución y vista previa PDF del demo (falsa). El shell tiene lista honesta + extractos/segmentos/búsqueda de pasajes (verificado en R6) y **cero menciones de Zotero en `src/app/`**.

**Asesor:** el demo muestra «5 tesistas», «Periodo 2025-I» e inbox (`DemoApp.tsx:1155-1172`) con datos fabricados; el shell solo muestra lo que entrega `GET /projects/advisor/dashboard` (honesto). En observaciones el shell es superior al demo: anclaje real por selección del asesor vs comentario suelto.

### 14.2 Capacidades del backend sin UI en el shell

| Capacidad | Endpoints reales (`backend/thesis/api/`) | Capa API (`src/api/`) | UI shell |
|---|---|---|---|
| Zotero | `/integrations/zotero` GET (status), GET (connect), GET (callback), DELETE; `/{p}/sources/zotero`; `/{p}/sources/import-zotero` (`routes_integrations.py:7-22`) | ✅ `getZoteroStatus/disconnectZotero/listZoteroItems/importZoteroItem` (`sources.ts:176-212`) | ❌ 0 |
| Generación IA | `/{p}/ai-batches` (+syntheses/decision/cancel), `/{p}/ai-jobs/{id}` (accept/cancel/reject/document-diff), `/{p}/workflow/tasks/{id}/generate`, `/{p}/idea`, `/{p}/idea/explore` | ✅ 16 funciones (`generation.ts`) | ❌ 0 |
| Citas IEEE | `/{p}/chapters/{n}/citations/ieee` | ✅ | ❌ 0 |
| Evidencia de citas | `/{p}/evidence-links` (+review), `citations/{occ}/evidence` (+decision), `citation-replacement-proposals` (+decision) | ✅ (`reviews.ts`: addCitationEvidence, decideCitationEvidence, proposeCitationReplacement, previewCitationReplacement) | ❌ 0 |
| Fuentes avanzadas | `/{p}/sources/{id}/index`, `/doi-check`, `/locate`, `/ocr`, `/grobid`, `/select-discovery`, `/import-bibliography`; `discovery/peru`, `discovery/semantic-scholar`; `search-strategies` (+executions) | ✅ casi todo (`sources.ts`) | ❌ 0 («Indexar pasajes» = brecha B4 de §11.5) |
| Research | `/{p}/datasets` (+versions/table-recipes/figures/preview) | ✅ 15 funciones (`research.ts`) | ❌ 0 |
| Invitaciones de apoyo | `/{p}/support-invitations` (+accept/contributions/revoke) | ✅ | ❌ 0 |
| Manuscritos | `/{p}/manuscripts` (upload/list/get), inspección de campos Zotero/Word (`services/manuscripts.py`, `integrations/docx.py:24`) | ❌ ni wrapper | ❌ 0 |
| Enviar a revisión | `/{p}/chapters/{n}/submit` | ✅ (`reviews.ts:16`) | ❌ 0 (B3) |

Protocolo MCP: **34 herramientas y 35 prompts** (`scripts/verify_project.py:254`) operables sin UI; ninguna se refleja en el shell.

### 14.3 Lectura técnica honesta

El demo no es «más completo que el shell»: es una maqueta con datos fabricados (A6, A7-PDF, dashboard de 5 tesistas) y funciones que hoy exigirían cambiar el contrato del documento (A1). Lo que sí revela es que una parte grande del backend **ya está envuelta en `src/api/` sin consumir**: la brecha mayor es cableado de UI, no desarrollo backend. Clasificación de trabajo:

- **Solo UI (capa API lista):** Zotero, indexar pasajes (B4), importar bibliografía, discovery, citas IEEE, evidencia, generación IA, research, invitaciones, submit (B3).
- **Requiere wrapper nuevo en `src/api/`:** manuscritos.
- **Requiere cambio de contrato backend:** formato en línea (A1), exportación PDF (A7).

**Decisión del usuario:** documentar en §14 y ejecutar **R8: Zotero + Fuentes** (Zotero conectar/estado/importar, botón «Indexar pasajes» que cierra B4, e importación de bibliografía) con verificación completa estilo R6. R9 (citas en el editor) queda como bloque siguiente candidato.

### 14.4 Análisis del backend (a petición expresa del usuario, 27/10/2026)

El usuario pidió analizar el backend «para que sepas exactamente de qué va, qué tecnología usa, cómo se comporta, qué se puede aprovechar del backend para mejorar el frontend». Verificación física del código:

**Stack tecnológico** (`requirements-backend.txt`, literal): Django 5.2 + django-ninja (API REST), psycopg 3 + **pgvector** (embeddings de 384 dimensiones en `models/sources.py:166-167`, modelo `fastembed`), **django-fsm-2** (máquina de estados del workflow), django-reversion (versionado), python-docx (exportes DOCX), ocrmypdf (OCR), docling (formatos Office), rapidfuzz (duplicados), google-genai (adaptador Gemini), cryptography/Fernet (cifrado de la API key de Zotero), requests-oauthlib (OAuth Zotero), mcp>=2.3 (servidor MCP con `django_bridge`).

**Ejecución fuera de la petición HTTP — dos workers** (`backend/thesis/management/commands/`):
- `run_document_worker`: cola `DocumentJob` con kinds literales GROBID, INDEX, OCR, DOI_CHECK, DOCX, PDF_EXTRACT, OPENALEX_PDF, FORMAT_EXTRACT (`models/documents.py:16-24`); estados QUEUED/RUNNING/SUCCEEDED/FAILED/CANCELLED. Reglas (`services/document_jobs.py:31-51`): `enqueue_document_job` es **owner_only**; INDEX y GROBID exigen `TEXT_CHECKED`; OCR exige `OCR_REQUIRED`.
- `run_ai_worker`: concurrencia 4 (`TESISMCP_AI_WORKER_MAX_CONCURRENCY`); el proveedor LLM es `TESISMCP_LLM_PROVIDER` con **DISABLED por defecto** (`config/settings.py:101`); `DEVELOPMENT_MOCK` solo en DEBUG y `GEMINI` exige `GEMINI_API_KEY` (`integrations/llm/factory.py`). La API **encola siempre** y el worker procesa fuera de la petición (`services/ai_jobs.py:188-190`).

**Reglas de acceso verificadas que condicionan la UI:** `import_zotero_item` es owner_only, `list_zotero_items` es de cualquier miembro (`services/zotero.py:178-186, 236`); `import_bibliography` acepta provider SCOPUS/WOS/OTHER y archivos .ris/.bib/.bibtex/.csv de hasta 5 MiB (`services/bibliography.py:38-48`).

**Implicación para el frontend:** la mayoría de capacidades del backend son cableables desde la UI sin tocar Django (la capa `src/api/` ya las envuelve en su mayoría). La excepción estructural es la generación IA: sin proveedor LLM configurado en el servidor, los jobs fallarán con error honesto del backend; la UI debe mostrar ese error tal cual y no simular progreso.

---

## 15. Bloque R8: Zotero + Fuentes (27/10/2026)

Ejecución del bloque aprobado tras el inventario de §14: conservar la vista general de la Biblioteca científica y cablear capacidades reales del backend sin tocar Django.

### 15.1 Alcance implementado

| Capacidad | Implementación | Contrato real usado |
|---|---|---|
| **Zotero: estado y conexión** | Nueva tarjeta «Zotero» con estado real (`SIN CONEXIÓN` / `CUENTA CONECTADA` con usuario, fecha y alcances), botón «Conectar Zotero» (redirect OAuth del backend en pestaña nueva) y «Verificar estado» | `GET /api/v1/integrations/zotero` (status) y `GET /integrations/zotero/connect` |
| **Zotero: buscar e importar** | Formulario de búsqueda en la biblioteca personal (paginación «Cargar más») e importación por registro con aviso honesto de creado/duplicado | `GET /projects/{id}/sources/zotero`, `POST /sources/import-zotero` (owner_only) |
| **Indexar pasajes (cierra B4)** | Botón «Indexar pasajes» en el detalle de fuente, habilitado solo con `TEXT_CHECKED` y propietario; sondeo del job con aviso de finalización | `POST /sources/{id}/index` (202 + DocumentJob, kind INDEX) + `GET /jobs/{id}` |
| **Importar bibliografía** | Panel con origen (SCOPUS/WOS/OTHER) y archivo .ris/.bib/.bibtex/.csv (≤5 MiB); resumen literal de la importación y nota de que quedan **sin verificación contra portada** | `POST /sources/import-bibliography` |
| **Etiqueta nueva** | `UNVERIFIED_METADATA` → «Metadatos sin verificar» en `editor/etiquetas.ts`; además se corrigió el tipo `SourceDocument["verification_status"]` en `src/api/types.ts:253`, que no declaraba ese estado que el backend sí devuelve (`models/sources.py:22`) | — |

### 15.2 Estructura (techo ~200 líneas respetado)

- `src/app/fuentes/useZotero.ts` (170): estado y acciones de Zotero (misma separación lógica/JSX de R7).
- `src/app/fuentes/ZoteroPanel.tsx` (141): composición del panel + listado importable.
- `src/app/fuentes/ZoteroEstado.tsx` (59): tarjeta de conexión.
- `src/app/fuentes/PanelPasajes.tsx` (105): búsqueda de pasajes (extraída de VistaFuentes).
- `src/app/fuentes/PanelImportar.tsx` (121): importación de bibliografía.
- `src/app/VistaFuentes.tsx`: 457 → 476 líneas (agrega acción de indexación y sondeo; conserva tabla, detalle y formularios existentes).
- `src/api/sources.ts`: +`indexSourcePassages()`.

Reglas de acceso respetadas tal como las aplica el backend: indexar e importar (Zotero y bibliografía) solo propietario; la UI muestra nota honesta al asesor («Solo el propietario del proyecto puede importar»).

### 15.3 Verificación ejecutada (navegador, entorno aislado `tesismcp_r6`)

1. `npx tsc --noEmit` → exit 0; `npm run build` → exit 0.
2. Tesista (Lucía, OWNER): la pestaña Fuentes muestra los tres paneles nuevos; Zotero «SIN CONEXIÓN» honesto; **Conectar Zotero** abre el endpoint real y el backend responde con su error literal `CONFIG_ERROR: Zotero OAuth no está configurado para esta instalación` (la instalación aislada no tiene credenciales OAuth; la UI lo reporta tal cual, sin simular conexión); **importación de bibliografía** con un RIS de 2 registros → «registros leídos: 2; creados: 2; ya existentes: 0» y las 2 fuentes aparecen en la tabla con procedencia OTHER; **Indexar pasajes** sobre `R6-aislado-pag1` (TEXT_CHECKED) → 202 en cola → sondeo → «Indexación de pasajes completada: los pasajes ya son consultables.» (worker local procesó el job real); búsqueda de pasajes del panel movido: 5 resultados con distancia coseno.
3. Asesor (Roberto, ADVISOR): «Importar registros» y su input de archivo deshabilitados con nota «Solo el propietario del proyecto puede importar»; en el detalle de fuente, sin botón de indexación y con nota «La indexación y las acciones de procesamiento son del tesista propietario.»
4. Cero errores de consola no provocados. Captura de evidencia tomada (Fuentes como asesor).

Alcance no probado en R8: importación real de registros de Zotero (requiere OAuth configurado en el servidor) y OCR/GROBID/DOI-check (queda para bloque posterior).
