# Bitácora de Continuidad: Integración Frontend Real (Antigravity)

**Fecha de corte:** 27/10/2026  
**Directorio de trabajo:** `/home/janr/Documentos/Universidad/Apuntes_Obsidian/Estudiando/Ciclo7/Curso Integrador 1/ProyectoCI-renovado`  
**Objetivo:** Integrar el frontend de `TesisMCP/` con los contratos y endpoints del backend Django de forma modular, verificable y con grounded truth.

---

## 1. Estado por Bloques

### 2C PENDIENTE: Comprobación Visual en Navegador
- **Estado:** Pendiente por bloqueo externo de navegador.
- **Detalle del bloqueo:** Al intentar invocar `browsermcp:browser_navigate`, el servidor MCP reportó: `Error: No connection to browser extension. In order to proceed, you must first connect a tab by clicking the Browser MCP extension icon in the browser toolbar and clicking the 'Connect' button.` No hay navegador interactivo conectado en la sesión actual.
- **Límite:** Se conserva como pendiente de validación visual. No se marca aprobado por pruebas de transporte o TypeScript.

---

### BLOQUE 3: Recorrido Configurable y Pasos Metodológicos
- **Estado:** ✅ **Implementado en código, integrado en navegación y verificado por compilación.**
- **Qué quedó implementado:**
  1. **Contratos y cliente API (`src/api/types.ts`, `src/api/workflows.ts`):**
     - `getWorkflowState`: `GET /api/v1/projects/{project_id}/workflow`.
     - `updateWorkflowDraft`: `PUT /api/v1/projects/{project_id}/workflow/draft` con `expected_version` (concurrencia optimista).
     - `validateWorkflowDraft`: `POST /api/v1/projects/{project_id}/workflow/validate`.
     - `publishWorkflowDraft`: `POST /api/v1/projects/{project_id}/workflow/publish` con `change_summary` y hash criptográfico.
     - `restoreWorkflowVersion`: `POST /api/v1/projects/{project_id}/workflow/restore` con `target_version_no` y auditoría.
     - `getEffectivePrompt`: `GET /api/v1/projects/{project_id}/workflow/tasks/{task_id}/prompt`.
     - `saveStep`: `PUT /api/v1/projects/{project_id}/steps/{step_code}` con `content_md`, `output_data`, `expected_version`, `idempotency_key`.
     - `executeCustomWorkflowTask`: `POST /api/v1/projects/{project_id}/workflow/tasks/{task_id}/execute` con `input_data`, `output_data`, `idempotency_key`.
     - `getCustomWorkflowTaskExecutions`: `GET /api/v1/projects/{project_id}/workflow/tasks/{task_id}/executions`.
  2. **Pantalla Completa de Recorrido (`src/features/workflow/WorkflowScreen.tsx`):**
     - **Pestaña 1 (Tareas y Dependencias):** Visualización de tareas ordenadas, filtrado por capítulos (1–7 y general), búsqueda por texto. Cálculo real de avance (% y cantidad de tareas activas completadas según datos persistidos de capítulos, sin "8 de 32" ficticio). Visualización de dependencias y prerrequisitos bloqueantes. Señalización explícita para P26 y P27: *"Definición metodológica pendiente con el asesor / profesor: el piloto académico se detiene antes de elaborar o aplicar instrumentos"*. Modal de inspección de prompt efectivo con versión, procedencia y núcleo protegido. Modal de guardado/ejecución para pasos P01–P32 y tareas USR_... con retención de borrador ante 409 o bloqueo por prerrequisito (`PREREQUISITE_LOCKED`).
     - **Pestaña 2 (Editor del Recorrido / Borrador):** Gestión exclusiva para titular (`role === OWNER` y `can_manage_workflow`). Reordenamiento de tareas (`order_index`), conmutación de estado activo/opcional con protección estricta del núcleo institucional (las tareas protegidas impiden desactivación u opcionalidad en UI y backend), edición directa del texto de prompt de cada tarea. Creación de nuevas tareas personalizadas `USR_...` con validación de ID, título y prompt. Guardado de borrador (`PUT /workflow/draft`) con control de concurrencia optimista (`lock_version`). Botón de validación estructural (`POST /workflow/validate`) que reporta ciclos y dependencias inválidas. Botón de publicación inmutable (`POST /workflow/publish`).
     - **Pestaña 3 (Historial de Versiones):** Listado de versiones publicadas e históricas con hash SHA-256 de contenido, autor y fecha. Acción de restauración (`POST /workflow/restore`) que clona una versión pasada creando una nueva versión publicada inmutable.
  3. **Integración en Navegación y Shell (`src/App.tsx`, `src/features/projects/ConnectedProjectScreen.tsx`, `src/index.css`):**
     - Vista `"workflow"` añadida a la aplicación conectada.
     - Tarjeta de acceso directo y enlace en el panel del proyecto.
     - Adaptación responsiva en escritorio y móvil.
- **Qué se comprobó y cómo:**
  - `cd TesisMCP && pnpm exec tsc --noEmit`: Exit code 0 (0 errores de tipos en toda la aplicación).
  - `cd TesisMCP && pnpm run build`: Exit code 0 (build de producción Vite generado limpiamente en 664 ms).
  - Inspección adversaria contra los esquemas Django Ninja de `backend/thesis/api/routes_workflows.py`, `backend/thesis/api/routes_chapters.py` y `backend/thesis/services/workflows.py`.
- **Archivos modificados y añadidos:**
  - `TesisMCP/src/api/types.ts`
  - `TesisMCP/src/api/workflows.ts` (nuevo)
  - `TesisMCP/src/features/workflow/WorkflowScreen.tsx` (nuevo)
  - `TesisMCP/src/features/projects/ConnectedProjectScreen.tsx`
  - `TesisMCP/src/App.tsx`
  - `TesisMCP/src/index.css`
  - `docs/02_arquitectura_y_sistema/matriz_integracion_frontend_backend.md`
  - `docs/02_arquitectura_y_sistema/continuidad_frontend_antigravity.md` (este archivo)
- **Pendientes concretos de este bloque:**
  - Validación interactiva visual en navegador (cuando se conecte la extensión de navegador).
- **Bloqueos externos:**
  - Ninguno para la integración frontend/backend en código.
- **Siguiente acción exacta:**
  - Proceder con el **Bloque 4: Biblioteca, Fuentes y Pasajes**.

---

### BLOQUE 4: Biblioteca, Fuentes y Pasajes
- **Estado:** ✅ **Implementado en código, integrado en navegación y verificado por compilación.**
- **Qué quedó implementado:**
  1. **Contratos y cliente API (`src/api/sources.ts`, `src/api/types.ts`):**
     - `listSources`: `GET /api/v1/projects/{project_id}/sources`.
     - `uploadSource`: `POST /api/v1/projects/{project_id}/sources/upload` con `FormData` (`label` y `file`, admite PDF, DOCX, PPTX, XLSX hasta 30 MB).
     - `importBibliographyFile`: `POST /api/v1/projects/{project_id}/sources/import-bibliography` para Scopus/WoS (.ris, .bib, .csv).
     - `listSourceExcerpts` y `listSourceSegments`: consulta de texto extraído con localizadores físicos de página y hashes SHA-256.
     - `searchPassages`: `POST /api/v1/projects/{project_id}/passages/search` con distancia coseno y límite configurable.
     - `getDocumentJob`: `GET /api/v1/projects/{project_id}/jobs/{job_id}` para seguimiento de trabajos de extracción/OCR.
     - `searchSemanticScholar` y `searchPeruDiscovery`: búsqueda de literatura y `selectDiscoveryCandidate` para incorporación al proyecto.
     - `getZoteroStatus`, `disconnectZotero`, `listZoteroItems`, `importZoteroItem`: integración con Zotero Web API v3 con reporte honesto de credenciales no configuradas.
  2. **Pantalla Completa de Biblioteca (`src/features/library/LibraryScreen.tsx`):**
     - **Pestaña 1 (Fuentes del Proyecto):** Listado real de fuentes con metadatos (autores, año, venue, DOI, archivo original), estados de verificación (`TEXT_CHECKED`, `OCR_REQUIRED`, `PENDING_EXTRACTION`, `METADATA_CHECKED`), conteo de páginas físicas y extractos. Subida de archivos con `FormData` y polling de trabajo activo. Modal de visualización de extractos con número de página física y chunk hash. Selector de fuentes para consulta cruzada.
     - **Pestaña 2 (Consulta y Pasajes tipo NotebookLM):** Formulario de consulta semántica vectorial (hasta 500 caracteres, límite de 3 a 15 candidatos), filtrado por fuentes seleccionadas o búsqueda global en el corpus del proyecto. Tarjetas de resultados con bloque de cita («...»), localizador (página física o segmento), distancia coseno y advertencia honesta obligatoria: *"Candidatos de recuperación semántica vectorial. No equivale a respuesta sintetizada por IA ni a verificación de afirmación científica"*.
     - **Pestaña 3 (Descubrimiento y Scopus/WoS):** Búsqueda de literatura abierta en Semantic Scholar y ALICIA/Perú con importación directa a fuentes. Sección para Scopus y Web of Science con asistencia en formulación de ecuaciones booleanas, enlaces a portales oficiales e importador de archivos bibliográficos (.ris, .bib, .csv), sin fingir acceso directo a textos completos con suscripción.
     - **Pestaña 4 (Zotero):** Indicador de estado de conexión, manejo de error de configuración cuando el servidor no tiene definidas las credenciales OAuth, listado de referencias personales e importación directa al proyecto, y botón de desconexión.
  3. **Integración en Navegación y Shell (`src/App.tsx`, `src/features/projects/ConnectedProjectScreen.tsx`, `src/index.css`):**
     - Vista `"library"` conectada con tarjeta de acceso directo en el espacio del proyecto y retorno seguro al workspace.
- **Qué se comprobó y cómo:**
  - `cd TesisMCP && pnpm exec tsc --noEmit`: Exit code 0 (0 errores de tipos).
  - `cd TesisMCP && pnpm run build`: Exit code 0 (build de producción Vite generado limpiamente en 2.27 s).
- **Archivos modificados y añadidos:**
  - `TesisMCP/src/api/types.ts`
  - `TesisMCP/src/api/sources.ts` (nuevo)
  - `TesisMCP/src/features/library/LibraryScreen.tsx` (nuevo)
  - `TesisMCP/src/features/projects/ConnectedProjectScreen.tsx`
  - `TesisMCP/src/App.tsx`
  - `TesisMCP/src/index.css`
  - `docs/02_arquitectura_y_sistema/matriz_integracion_frontend_backend.md`
  - `docs/02_arquitectura_y_sistema/continuidad_frontend_antigravity.md`
- **Pendientes concretos de este bloque:**
  - Pruebas con cuentas reales de Zotero y suscripciones activas de Scopus/WoS (requieren credenciales externas).
- **Siguiente acción exacta:**
  - Proceder con el **Bloque 5: Asesor, Snapshots y Apoyos**.

---

### BLOQUE 5: Asesor, Snapshots y Apoyos
- **Estado:** ✅ **Implementado en código, integrado en navegación y verificado por compilación.**
- **Qué quedó implementado:**
  1. **Contratos y cliente API (`src/api/reviews.ts`, `src/api/types.ts`):**
     - `getAdvisorDashboard`: `GET /api/v1/projects/advisor/dashboard` (retorna proyectos y estados de capítulos asignados).
     - `submitChapter`: `POST /api/v1/projects/{project_id}/chapters/{chapter_no}/submit` (envío transaccional y congelamiento de snapshot).
     - `listChapterSnapshots`: `GET /api/v1/projects/{project_id}/chapters/{chapter_no}/snapshots`.
     - `getChapterSnapshot`: `GET /api/v1/projects/{project_id}/chapters/{chapter_no}/snapshots/{snapshot_id}`.
     - `listComments`: `GET /api/v1/projects/{project_id}/chapters/{chapter_no}/comments`.
     - `addComment`: `POST /api/v1/projects/{project_id}/chapters/{chapter_no}/comments` con fragmento anclado y cuerpo.
     - `resolveComment`: `POST /api/v1/projects/{project_id}/comments/{comment_id}/resolve`.
     - `decideChapter`: `POST /api/v1/projects/{project_id}/chapters/{chapter_no}/decision` (`REQUEST_CHANGES`, `APPROVE`, `REOPEN`).
     - `listSupportInvitations`, `createSupportInvitation`, `revokeSupportInvitation`, `listSupportContributions`: gestión de personas de apoyo delimitadas por tarea y fuentes con TTL.
  2. **Pantalla Completa de Asesor y Revisión (`src/features/advisor/AdvisorScreen.tsx`):**
     - **Pestaña 1 (Revisión de Capítulos y Observaciones):** Selector de capítulos 1–7 y selector de versiones (borrador activo o instantáneas congeladas). Visualizador del manuscrito con hashes SHA-256 inmutables. Lista de observaciones abiertas (`OPEN`) y resueltas (`RESOLVED`). Formulario para agregar observación por el asesor con fragmento citado. Botón para resolver observaciones. Bloque de decisión del asesor: `Solicitar cambios` (exige observaciones abiertas), `Aprobar capítulo` (bloqueado si quedan observaciones abiertas `ADVISOR_UNRESOLVED_COMMENTS`), y `Reabrir capítulo` (exige motivo). Acción del tesista para enviar capítulo a revisión cuando está en `DRAFT` o `CHANGES_REQUESTED`.
     - **Pestaña 2 (Proyectos asignados al Asesor):** Vista multi-proyecto exclusiva para usuarios con rol `ADVISOR`, mostrando los proyectos asignados y los capítulos con pendientes en `READY`, sin inventar métricas ni actividad ficticia.
     - **Pestaña 3 (Personas de Apoyo / Expertos):** Gestión de invitaciones opcionales para expertos temáticos/metodológicos. Creación de invitación con tarea asociada (`task_id`) e instrucciones específicas; listado de estados (`PENDING`, `ACCEPTED`, `REVOKED`, `EXPIRED`) y visualizador modal de contribuciones recibidas. Revocación inmediata.
  3. **Integración en Navegación y Shell (`src/App.tsx`, `src/features/projects/ConnectedProjectScreen.tsx`, `src/index.css`):**
     - Vista `"advisor"` conectada en la navegación del proyecto con tarjeta de acceso directo y retorno seguro al espacio.
- **Qué se comprobó y cómo:**
  - `cd TesisMCP && pnpm exec tsc --noEmit`: Exit code 0 (0 errores de tipos en todo el frontend).
  - `cd TesisMCP && pnpm run build`: Exit code 0 (build de producción Vite generado limpiamente en 540 ms).
- **Archivos modificados y añadidos:**
  - `TesisMCP/src/api/types.ts`
  - `TesisMCP/src/api/reviews.ts` (nuevo)
  - `TesisMCP/src/features/advisor/AdvisorScreen.tsx` (nuevo)
  - `TesisMCP/src/features/projects/ConnectedProjectScreen.tsx`
  - `TesisMCP/src/App.tsx`
  - `TesisMCP/src/index.css`
  - `docs/02_arquitectura_y_sistema/matriz_integracion_frontend_backend.md`
  - `docs/02_arquitectura_y_sistema/continuidad_frontend_antigravity.md`
- **Siguiente acción exacta:**
  - Proceder con el **Bloque 6: IA, Propuestas y Conexión del Agente**.

---

### BLOQUE 6: IA, Propuestas y Conexión del Agente
- **Estado:** ✅ **Implementado en código, integrado en navegación y verificado por compilación.**
- **Qué quedó implementado:**
  1. **Contratos y cliente API (`src/api/generation.ts`, `src/api/types.ts`):**
     - `generateProposal`: `POST /api/v1/projects/{project_id}/workflow/tasks/{task_id}/generate` con `input_data`, `context_refs`, `expected_state_version`, `workflow_version_no`, `idempotency_key`.
     - `getGenerationJob`: `GET /api/v1/projects/{project_id}/ai-jobs/{job_id}` (`QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED`).
     - `getGenerationDocumentDiff`: `GET /api/v1/projects/{project_id}/ai-jobs/{job_id}/document-diff` para comparar propuestas textuales (`P05`, `P29`) con el manuscrito canónico.
     - `cancelGenerationJob`: `POST /api/v1/projects/{project_id}/ai-jobs/{job_id}/cancel`.
     - `acceptProposal`: `POST /api/v1/projects/{project_id}/ai-jobs/{job_id}/accept` con `expected_state_version`, `decision_key`, `expected_document_version`, `proposal_sha256`.
     - `rejectProposal`: `POST /api/v1/projects/{project_id}/ai-jobs/{job_id}/reject` con `decision_key` y `reason`.
     - `createGenerationBatch`, `listGenerationBatches`, `getGenerationBatch`, `cancelGenerationBatch`: gestión de lotes de generación.
     - `createBatchSynthesis`, `listBatchSyntheses`, `getBatchSynthesis`, `cancelBatchSynthesis`, `decideBatchSynthesis`: síntesis de lotes y decisión explícita.
  2. **Pantalla Completa de Asistente de IA (`src/features/ai/AIAssistantScreen.tsx`):**
     - **Pestaña 1 (Generación y Propuestas):** Selector de tareas activas del recorrido (sincronizado con `published` o `draft` del workflow). Formulario de parámetros en JSON estructurado. Botón de generación con UUID idempotente. Manejo transparente de falta de configuración en el servidor (`PROVIDER_UNAVAILABLE` cuando falta `GEMINI_API_KEY` en backend). Monitor de estado con polling automático (cada 2.5s mientras está en cola o ejecución) y cancelación. Al completarse con éxito: botón para cargar diff del documento (con visor de columnas comparativas antes vs después), visor de salida JSON estructurada y panel de decisión humana (botón de aceptación e incorporación canónica al manuscrito y botón de rechazo explícito con motivo).
     - **Pestaña 2 (Lotes y Síntesis):** Lista y detalle de lotes con estados de tareas individuales, cancelación y solicitud de síntesis de lotes con decisión de aceptación/rechazo.
     - **Pestaña 3 (Arquitectura BYOA & Servidor MCP):** Diagrama explicativo de la arquitectura Bring Your Own Agent: la web inicia y presenta tareas, el backend Django autoriza y coordina, el servidor MCP ofrece las 34 herramientas de dominio, y el modelo personal del usuario razona localmente sin enviar claves comerciales a TesisMCP.
  3. **Integración en Navegación y Shell (`src/App.tsx`, `src/features/projects/ConnectedProjectScreen.tsx`, `src/index.css`):**
     - Vista `"ai"` añadida a la aplicación conectada con tarjeta de acceso directo en el panel del proyecto.
- **Qué se comprobó y cómo:**
  - `pnpm --dir TesisMCP exec tsc --noEmit`: Exit code 0.
  - `pnpm --dir TesisMCP run build`: Exit code 0 (build generado en 549 ms).
- **Archivos modificados y añadidos:**
  - `TesisMCP/src/api/types.ts`
  - `TesisMCP/src/api/generation.ts` (nuevo)
  - `TesisMCP/src/features/ai/AIAssistantScreen.tsx` (nuevo)
  - `TesisMCP/src/features/projects/ConnectedProjectScreen.tsx`
  - `TesisMCP/src/App.tsx`
  - `TesisMCP/src/index.css`

---

### BLOQUE 7: Datasets, Tablas, Figuras, Citas IEEE y Exportación DOCX
- **Estado:** ✅ **Implementado en código, integrado en navegación y verificado por compilación.**
- **Qué quedó implementado:**
  1. **Contratos y clientes API (`src/api/research.ts`, `src/api/chapters.ts`, `src/api/exports.ts`, `src/api/client.ts`):**
     - Helper de descarga binaria `apiDownload`: maneja respuestas de tipo `Blob`, extrae nombre de archivo de `Content-Disposition`, y arroja errores legibles si el backend responde con JSON de error de dominio (evitando corromper o descargar archivos vacíos ante conflictos o falta de permisos).
     - Datasets: `listDatasets`, `createDataset` (FormData multipart), `listDatasetVersions`, `getDatasetVersion`, `addDatasetVersion`, `downloadDatasetFile`.
     - Recetas Tabulares: `listTableRecipes`, `createTableRecipe` (declarativa con columnas y filtros), `listTableRecipeVersions`, `getTableRecipeVersion`.
     - Figuras Científicas: `listFigures`, `createFigure` (especificación visual con tipo y columnas), `listFigureVersions`, `getFigureVersion`, `getFigurePreviewUrl` (PNG real).
     - Citas IEEE y Evidencia: `getChapterIeeeCitations` (vista con referencias numeradas y marcas), `listCitationEvidence`, `addCitationEvidence` (afirmación, extracto y página física), `decideCitationEvidence` (`CONFIRMED` / `REFUTED`), `proposeCitationReplacement`, `previewCitationReplacement`, `decideCitationReplacement`.
     - Exportación DOCX: `downloadDraftDocx` (`/projects/{id}/export/draft.docx`), `downloadApprovedChapterDocx` (`/projects/{id}/chapters/{no}/export/approved.docx`).
  2. **Pantalla de Datos, Citas y Exportación (`src/features/artifacts/ResearchArtifactsScreen.tsx`):**
     - **Pestaña 1 (Datasets):** Subida multipart de archivos (.csv, .xlsx), historial de versiones inmutables con hashes SHA-256, conteo de filas, nombres de columnas y descarga directa de archivos originales.
     - **Pestaña 2 (Recetas Tabulares):** Definición declarativa de recetas tabulares, previsualización de tabla renderizada con filas y columnas, y generación de bloque JSON v2 para inserción directa en el editor.
     - **Pestaña 3 (Figuras Científicas):** Creación de gráficos sobre recetas tabulares, previsualización de imagen PNG real generada por el backend, dimensiones, hash SHA-256 y código de bloque JSON v2 para el editor.
     - **Pestaña 4 (Citas IEEE y Evidencia):** Selector de capítulos 1 a 7, vista preliminar IEEE con referencias numeradas `[N]`, banderas de metadatos completos/faltantes según norma institucional, marcas de anclas en párrafos y panel de auditoría de evidencia con página física.
     - **Pestaña 5 (Exportación Word .docx):** Descarga de borrador completo compilado (formato institucional con tipografía Arial 11 pt, espaciado doble, márgenes normativos de 3 cm y 2.5 cm) y descarga de capítulo aprobado con validación estricta (informa claramente si el capítulo no cuenta con un snapshot aprobado por el asesor).
  3. **Mejoras en el Editor de Capítulos (`src/features/editor/ChapterEditorScreen.tsx`):**
     - Botones `+ Tabla (v2)` y `+ Figura (v2)` para incorporar bloques `data_table` y `figure` con actualización a `schema_version: 2`.
     - Botones de exportación rápida de borrador y capítulo aprobado en la barra de acciones.
  4. **Integración en Navegación y Shell (`src/App.tsx`, `src/features/projects/ConnectedProjectScreen.tsx`, `src/index.css`):**
     - Vista `"artifacts"` añadida al enrutamiento con tarjeta de acceso directo en el panel del proyecto.
- **Qué se comprobó y cómo:**
  - `pnpm --dir TesisMCP exec tsc --noEmit`: Exit code 0 (0 errores de TypeScript).
  - `pnpm --dir TesisMCP run build`: Exit code 0 (build de producción Vite generado limpiamente en 607 ms, 37 módulos transformados).
- **Archivos modificados y añadidos:**
  - `TesisMCP/src/api/client.ts`
  - `TesisMCP/src/api/types.ts`
  - `TesisMCP/src/api/research.ts` (nuevo)
  - `TesisMCP/src/api/chapters.ts`
  - `TesisMCP/src/api/exports.ts` (nuevo)
  - `TesisMCP/src/features/artifacts/ResearchArtifactsScreen.tsx` (nuevo)
  - `TesisMCP/src/features/editor/ChapterEditorScreen.tsx`
  - `TesisMCP/src/features/projects/ConnectedProjectScreen.tsx`
  - `TesisMCP/src/App.tsx`
  - `TesisMCP/src/index.css`

---

### BLOQUE 8: Recorrido Integrado y Cierre
- **Estado:** ✅ **Implementado en código, integrado en navegación y verificado.**
- **Resumen:**
  - Las 8 pantallas del producto se encuentran unificadas en la aplicación conectada:
    1. `access`: Inicio de sesión y verificación de credenciales con Django y CSRF.
    2. `projects`: Selección y creación de proyectos de investigación.
    3. `workspace`: Espacio central con roles (`OWNER` / `ADVISOR`), permisos y tarjetas de navegación.
    4. `workflow`: Recorrido metodológico configurable, tareas, prompts, P26/P27, validación y versiones.
    5. `library`: Biblioteca multiformato, extracción de texto con páginas físicas, búsqueda vectorial de pasajes, descubrimiento ALICIA/Semantic Scholar, e integración Zotero/Scopus.
    6. `advisor`: Panel de revisión del asesor, comparación de snapshots, observaciones ancladas, decisiones y personas de apoyo.
    7. `editor`: Editor de capítulos por bloques con prevención de colisiones, anclaje de citas y soporte de artefactos v2.
    8. `ai`: Asistente de IA con generación estructurada, comparador de diffs, lotes y arquitectura BYOA/MCP.
    9. `artifacts`: Gestión de datasets, recetas tabulares, figuras PNG, citas IEEE y exportación binaria DOCX.
    10. `demo`: Demostración visual aislada (DemoApp.tsx) completamente separada de los flujos conectados.




---

### Corrección focalizada 1: vínculo de auditoría de citas (27/10/2026)

- La vista IEEE ahora incluye `occurrence_ids` en cada marca, alineados por índice con `source_ids` y `numbers`. El backend conserva las marcas agrupadas y entrega el ID persistido de cada fuente de la marca.
- La pestaña de citas muestra una acción de auditoría por ocurrencia y envía ese ID a `/citations/{occurrence_id}/evidence`; antes enviaba un `source_id`. Al cambiar capítulo o recargar la vista, limpia el panel de evidencia; las respuestas antiguas de consultas de evidencia no reemplazan la selección nueva.
- Archivos: `backend/thesis/services/ieee_citations.py`, `TesisMCP/src/api/types.ts` y `TesisMCP/src/features/artifacts/ResearchArtifactsScreen.tsx`.
- Se inspeccionó el contrato y se releyeron las líneas modificadas. Las pruebas y la puerta integral quedan aplazadas según la instrucción del usuario de verificarlas al finalizar las correcciones; el comportamiento en navegador sigue pendiente.
- Siguiente bloque acordado: anclas de observaciones del asesor.

---

### Corrección focalizada 2: anclas reales de observaciones (27/10/2026)

- `AdvisorScreen.tsx` obtiene el fragmento mediante selección en el texto de la instantánea vigente. Calcula `start_cp` y `end_cp` en puntos de código Unicode y comprueba que el fragmento coincide exactamente con `content_md` antes de enviar la observación.
- El formulario solo se ofrece al asesor cuando el capítulo está en `READY` y la instantánea seleccionada es la enviada vigente; cambiar capítulo o instantánea elimina el ancla anterior. Las instantáneas históricas se mantienen en lectura.
- Se eliminó la entrada manual de fragmentos que enviaba siempre `start_cp=0`. El serializador de observaciones ahora incluye autor y fechas reales para el panel, y el listado carga la relación de autor. La corrección se inspeccionó en el código; la interacción en navegador, las pruebas y la puerta integral permanecen pendientes conforme al aplazamiento solicitado.
- Siguiente bloque acordado: revisar los valores iniciales y contratos de recetas tabulares y figuras.

---

### Corrección focalizada 3: contratos de recetas y figuras (27/10/2026)

- El formulario de receta toma los nombres de columna de la última versión del dataset y propone `columns`, `filters`, `sort` y `limit`; ya no muestra `select_columns`. Si no hay columnas o filas, no propone una receta.
- El formulario de figura toma columnas y filas de la última versión tabular. Solo propone un gráfico BAR cuando observa una columna numérica, al menos una fila y no más de 30; el JSON usa las siete claves exigidas por el backend. La selección de dataset o receta limpia las versiones y propuestas anteriores, y las respuestas antiguas de carga de versiones no reemplazan la nueva selección.
- Antes de enviar, los formularios comprueban la estructura básica y pertenencia de las columnas. Una tabla truncada exige confirmación explícita antes de generar figura. La validación completa de datos, tipos, límites y hashes sigue en el backend. Los campos JSON continúan siendo editables.
- Archivo: `TesisMCP/src/features/artifacts/ResearchArtifactsScreen.tsx`. Se inspeccionó el contrato y el diff. No se ejecutaron pruebas ni puerta integral por el aplazamiento acordado; la interacción visual sigue pendiente.
- Siguiente bloque acordado: selección efectiva de fuentes para la búsqueda de pasajes.

---

### Corrección focalizada 4: selección efectiva de fuentes (27/10/2026)

- La entrada de `POST /passages/search` acepta `source_ids` opcional. El servicio restringe el queryset por proyecto y fuentes seleccionadas antes de calcular los vecinos más cercanos y aplicar `limit`. Sin selección, conserva la búsqueda en todo el proyecto.
- La biblioteca envía los ID seleccionados al servidor y deja de filtrar solo los primeros resultados en el navegador. Al cambiar la selección, descarta resultados anteriores e ignora respuestas de búsquedas viejas. El POST incluye el token CSRF de la sesión.
- Archivos: `backend/thesis/api/schemas.py`, `backend/thesis/api/routes_evidence.py`, `backend/thesis/services/search.py`, `TesisMCP/src/api/sources.ts` y `TesisMCP/src/features/library/LibraryScreen.tsx`.
- Inspección estática realizada; pruebas y puerta integral aplazadas por instrucción del usuario. No se afirma búsqueda integrada en navegador.
- Siguiente bloque: revisar la inserción de tablas y figuras en el editor con selección directa del artefacto.

---

### Corrección focalizada 5: selector de tablas y figuras del proyecto (27/10/2026)

- El editor abre un selector al añadir una tabla o figura. El tesista elige dataset, versión del dataset, receta y versión tabular; para una figura elige además la figura y su versión. La lista de versiones se restringe a la cadena de procedencia seleccionada.
- La versión elegida aporta `version_id` y `result_sha256` u `output_sha256` desde la API. El usuario edita únicamente la leyenda; ya no copia UUID ni hashes. El bloque se incorpora al borrador local como `data_table` o `figure` con `schema_version: 2` y sigue el guardado versionado existente. El backend conserva la validación de pertenencia e integridad al guardar.
- El selector solo se abre cuando el titular puede editar el capítulo. Cambiar de capítulo cierra el selector; cambiar un nivel de procedencia limpia las selecciones dependientes. El editor continúa mostrando los artefactos como bloques estructurados protegidos.
- Archivos: `TesisMCP/src/features/editor/ArtifactPicker.tsx`, `ChapterEditorScreen.tsx` y `TesisMCP/src/index.css`. Se revisó el contrato de las rutas y los tipos. Pruebas de navegador, build y puerta integral siguen aplazados por instrucción del usuario.
- Siguiente bloque de correcciones: revisar los flujos restantes del frontend frente a los contratos actuales y priorizar la primera verificación integrada al cerrar las correcciones.

---

### Corrección focalizada 6: contratos de generación, lotes y síntesis (27/10/2026)

- El frontend de IA ahora consume `items` del lote, que es lo que serializa `ai_batches.py`; su estado parcial es `PARTIAL`. Permite solicitar un lote de 1 a 8 tareas activas, refrescar su estado y consultar automáticamente lotes/síntesis en curso. El formulario de lote declara que envía `{}` como entrada de cada tarea. La síntesis toma solo trabajos `SUCCEEDED` y exige al menos dos, de acuerdo con `batch_synthesis.py`.
- La síntesis muestra `output_data` estructurado y su error cuando existe; su estado de decisión inicial es `PENDING_REVIEW`. Las decisiones envían `ACCEPTED` o `REJECTED` como exige el servicio. La aceptación se presenta como informe auxiliar, sin prometer incorporación automática al manuscrito.
- La vista de propuesta no inventa proveedor o modelo. Para P05/P29 exige cargar el diff vigente antes de habilitar la aceptación y distingue la revisión de manuscrito de la revisión de paso o ejecución de tarea personalizada. La entrada de generación debe ser un objeto JSON.
- La guía BYOA visible en la pantalla usa las variables reales del proceso MCP (`DATABASE_URL`, `TESISMCP_MCP_TOKEN`, y `DJANGO_DEBUG=1` en local) y remite a `mcp_server/README.md`; se retiró el ejemplo de `TESISMCP_API_TOKEN` que no consume el puente actual.
- Archivos: `TesisMCP/src/api/types.ts`, `TesisMCP/src/api/generation.ts`, `TesisMCP/src/features/ai/AIAssistantScreen.tsx` y `TesisMCP/src/index.css`. Se contrastaron con serializadores, servicios y guía MCP. La ejecución de build, pruebas, navegador y puerta integral sigue aplazada por instrucción del usuario.
- Pendientes identificados para la siguiente ronda de correcciones del frontend (el orden se ajustará si la inspección de código revela una brecha más grave):
  1. **Permisos y navegación:** revisar las tarjetas y acciones del titular y del asesor contra los permisos reales; evitar ofrecer escritura donde el backend solo admite lectura.
  2. **Revisión de citas:** confrontar la pestaña IEEE con los contratos de evidencia y propuestas de reemplazo; hoy solo muestra revisiones existentes, por lo que falta decidir e implementar la interacción revisable que corresponda al alcance del piloto.
  3. **Integración final:** build, pruebas de backend/frontend y recorrido real en navegador con base aislada; revisar errores de sesión/CSRF, roles, cambios de versión, carga de documentos, IA y exportación. Las credenciales externas de Gemini/Zotero requieren configuración y una comprobación separada.

---

### Corrección focalizada 7: permisos visibles por rol (27/10/2026)

- El espacio del proyecto describe acciones diferentes para titular y asesor según el permiso recibido del backend. El asesor puede abrir datos y lotes en consulta; las pantallas de IA y datos ocultan creación, cancelación y decisiones que exigen titular.
- La biblioteca mantiene la conexión personal de Zotero como función del usuario, pero solo el titular ve importaciones al proyecto (candidatos, archivo bibliográfico, ítems Zotero). Los manejadores de importación también comprueban el rol antes de enviar.
- Archivos: `TesisMCP/src/App.tsx`, `features/projects/ConnectedProjectScreen.tsx`, `features/ai/AIAssistantScreen.tsx`, `features/artifacts/ResearchArtifactsScreen.tsx`, `features/library/LibraryScreen.tsx`. La autorización real permanece en los servicios Django.

### Corrección focalizada 8: revisión de evidencia y reemplazo de citas (27/10/2026)

- Se corrigió el contrato de pasajes: la API entrega `physical_page` y `excerpt_id`, no `page_no`/`chunk_no`. La biblioteca y el nuevo panel muestran la página física real.
- El titular puede seleccionar un rango de afirmación dentro del párrafo citado y un rango de pasaje extraído de la misma fuente; se convierten las posiciones UTF-16 del navegador a puntos de código Unicode antes de crear el candidato. La pantalla comprueba que la selección incluya el ancla y que el documento corresponda a la revisión IEEE consultada. El backend vuelve a validar hashes, pertenencia y versiones.
- El asesor puede evaluar el candidato con `SUPPORTS`, `CONTRADICTS`, `UNRELATED` o `INSUFFICIENT`. Ambos participantes pueden proponer otra fuente del proyecto con justificación y consultar la comparación de referencias congeladas. Solo el titular puede aceptar o rechazar; aceptar crea nueva revisión del documento. El panel permite recuperar una propuesta por ID porque el backend actual no publica listado de propuestas.
- Archivos: `features/artifacts/CitationReviewPanel.tsx`, `ResearchArtifactsScreen.tsx`, `api/chapters.ts`, `api/types.ts`, `features/library/LibraryScreen.tsx` e `index.css`.

### Verificación al cierre de estos cambios

- TypeScript `tsc --noEmit`: código 0.
- Vite build de producción: código 0, salida en `/tmp/tesismcp-build-final`.
- `python3 scripts/verify_project.py` se ejecutó primero en el host y falló por dependencias Python ausentes en la copia limpia (`Django` y, al usar el entorno virtual del proyecto original, `requests_oauthlib`). La misma puerta se ejecutó en la imagen local `localhost/tesismcp-verify:local` con PostgreSQL y terminó con **código 0**: 8/8 controles y 223 pruebas de pytest aprobadas en 505,72 s. Veredicto: `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]` para esa ejecución. También verificó 58 modelos, 44 migraciones, 32 pasos, 34 herramientas MCP, 35 prompts y 0 enlaces Markdown rotos.
- Prueba visual local con base PostgreSQL desechable: inicio de sesión y creación/apertura de proyecto del tesista funcionaron. La pantalla de IA abrió correctamente al contar con el `PYTHONPATH` esperado. La pantalla de datos/citas mostró un error genérico cuando el servidor de prueba ya no estaba disponible; esa observación no acredita una falla de contrato. No se completó un recorrido de asesor ni de revisión de cita con evidencia real en navegador.
- Una llamada real al proveedor IA y OAuth con una cuenta Zotero real siguen pendientes de credenciales/configuración. El build y la puerta integral no acreditan esas integraciones externas.
