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
