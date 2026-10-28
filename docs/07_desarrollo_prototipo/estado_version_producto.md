# Estado verificable del producto

**Frontend, corte 27/10/2026 (los cambios UI posteriores deben revisarse en el checkout):** `TesisMCP/` contiene la integración real de los bloques 1 al 8 con el backend Django:
- **Acceso y sesión:** Autenticación por sesión Django, CSRF en cabecera y cookies con credentials: `include`.
- **Selección de proyectos:** Listado paginado de membresías reales, creación autorizada y roles (`OWNER` / `ADVISOR`).
- **Recorrido metodológico configurable (Bloque 3):** Cálculo de avance sobre tareas activas (sin '8 de 32' ficticio), edición de borrador, protección de núcleo institucional, tareas `USR_...`, validación estructural y publicación/restauración de versiones inmutables.
- **Biblioteca y pasajes (Bloque 4):** Subida multiformato (PDF, DOCX, PPTX, XLSX) con localizadores físicos de página, consulta semántica tipo NotebookLM con distancia coseno y aviso anti-alucinaciones, asistencia Scopus/WoS e importador bibliográfico (.ris, .bib, .csv), y Zotero Web API v3 con manejo honesto de configuración.
- **Asesor y revisiones (Bloque 5):** Snapshots inmutables de capítulos enviados, observaciones con fragmentos anclados, decisiones del asesor (`REQUEST_CHANGES`, `APPROVE` bloqueado ante observaciones abiertas `ADVISOR_UNRESOLVED_COMMENTS`, `REOPEN`) e invitaciones acotadas a personas de apoyo.
- **Asistente de IA y Decisiones Humanas (Bloque 6):** Generación de propuestas estructuradas con polling, diff comparativo antes vs propuesta con hash, decisiones humanas obligatorias (aceptación canónica o rechazo), gestión de lotes/síntesis y explicación arquitectónica de BYOA/MCP.
- **Datos, Citas IEEE, Tablas, Figuras y Exportación (Bloque 7):** Datasets versionados, recetas tabulares declarativas con vista previa de filas y columnas, figuras científicas con PNG real generado por el backend, visualización preliminar de referencias IEEE numeradas con detección de metadatos faltantes, auditoría de evidencia con página física y descarga binaria segura de Borrador Completo y Capítulo Aprobado (.docx).
- **Editor de capítulos:** Edición por bloques con prevención de colisiones, anclaje de citas y soporte de artefactos v2 (`data_table`, `figure`).
TypeScript y build de producción Vite pasan con código de salida 0. La interacción visual interactiva en navegador sigue registrada como pendiente por falta de extensión Browser MCP conectada en esta sesión. Véase la [bitácora de continuidad](../02_arquitectura_y_sistema/continuidad_frontend_antigravity.md).


**Alcance del prototipo acordado:** detener el recorrido antes de elaborar y aplicar instrumentos. P30–P32 no son obligatorios para la demostración; P26/P27 mencionan instrumentos previstos y deben decidirse en el recorrido concreto. Conservar pasos disponibles y recorridos editables, sin afirmar que se completa toda la tesis. IEEE es el estilo priorizado para el piloto; APA 7 sigue admitido por compatibilidad histórica.
> **Corte integral B8 verificado (26/10/2026):** 58 modelos, 44 migraciones (`0001`–`0044`), 32 contratos metodológicos, 34 herramientas MCP y 35 prompts. Puerta 7/7, total 479.66 s, pytest completa 457.26 s, exit code 0. Es un registro histórico; BYOA local añade después tres migraciones y un modelo. OAuth Zotero real no se ha probado por falta de credenciales externas.

> **Estado BYOA local (28/10/2026, revisión de código; sin ejecución runtime real):** backend de conexiones por proyecto, despacho de jobs, leases, eventos, resultado validado y adaptador registrable con Antigravity CLI implementados. Conteo actual del verificador: 59 modelos y 47 migraciones (`0001`–`0047`). No se ejecutó la puerta integral en este corte. Falta UI de gestión/conexión BYOA, instalación/autenticación real de `agy` y verificación end-to-end. Solo Antigravity está implementado; otros runtimes requieren su adaptador.

## BYOA local: adaptadores de agentes (28/10/2026; revisión de código, sin runtime real)

- `AgentConnection` vincula usuario, proyecto y runtime; los secretos de conector/MCP solo se devuelven al crear la conexión y se almacenan como hashes. La revocación invalida ambos y cancela jobs activos.
- `AIGenerationJob` separa `SERVER` y `BYOA`; el worker server-side reclama únicamente `SERVER`. El job BYOA conserva contexto y esquema, lease, eventos acotados y procedencia declarada. La respuesta validada termina como propuesta pendiente de aceptación.
- Rutas de conexión: `POST/GET/DELETE /api/v1/integrations/agents`. Rutas de conector: `POST /api/v1/integrations/agents/connector/claim` y `/jobs/{job_id}/heartbeat|events|complete|fail`. Generación: ruta existente `POST /api/v1/projects/{id}/workflow/tasks/{task_id}/generate` con `execution_mode=BYOA` y `agent_connection_id`.
- `AgentRuntimeAdapter` y el registro de `backend/thesis/agent_runtimes/` separan invocación, configuración MCP y normalización de eventos. Solo `ANTIGRAVITY_CLI` tiene implementación ahora; cada nuevo runtime necesita su adaptador concreto.
- El comando `run_byoa_connector` necesita `agy` instalado y autenticado y permiso MCP explícito. No hay interfaz de gestión BYOA integrada ni ejecución real verificada. BYOA en nube está pendiente. Las migraciones `0045`–`0047` llevan el conteo del código a 59 modelos/47 migraciones; no se aplicaron ni se comprobaron contra una base en este corte.

## B8.1: datasets originales versionados (implementado y verificado)

- `POST /api/v1/projects/{project_id}/datasets` carga CSV UTF-8 o XLSX y crea el contenedor y la primera versión. `POST .../datasets/{dataset_id}/versions` agrega versiones con control optimista e idempotencia.
- El original se conserva con SHA-256, nombre base, formato, tamaño, dimensiones, esquema observado y metadatos de importación. XLSX con varias hojas requiere `sheet_name`; fórmulas y cachés no se recalculan.
- Solo el titular crea datasets/versiones; participantes activos del proyecto consultan y descargan dentro del proyecto. La descarga verifica el hash.
- Pruebas focalizadas B8.1: 8/8. La evidencia integral del corte anterior y los límites están en el [paquete B8](../02_arquitectura_y_sistema/paquete_b8_datos_figuras.md).

## B8.2: recetas tabulares declarativas (implementado y verificado)

- `ResearchTableRecipe` y `ResearchTableRecipeVersion` (migración `0042`) guardan identidad, especificación, número de versión, clave idempotente, entrada exacta y hashes SHA-256 de entrada, receta y resultado. PostgreSQL bloquea UPDATE/DELETE de versiones.
- Operaciones: filtros AND (`EQ/NE/GT/GTE/LT/LTE/CONTAINS/IS_EMPTY/NOT_EMPTY`), orden estable ascendente/descendente, proyección de columnas y límite explícito de 1–10 000 filas. El límite informa filas encontradas y si la salida quedó truncada.
- Solo hay JSON declarativo allowlist. No se ejecuta código libre, macros, SQL ni fórmulas. No incluye agregaciones, inferencia estadística, figura ni inserción automática en el manuscrito. Resultado vacío o superior a 4 MiB se rechaza.
- El titular escribe/versiona; los participantes activos leen. API: crear/versionar receta, listar recetas de una versión de dataset y consultar versiones/resultados.
- Pruebas focalizadas combinadas B8.1/B8.2: **13 pasaron**, 1 warning deprecado de `google.genai`; duración 68.36 s. Puerta integral B8.2: 7/7, 432.35 s, exit code 0; la suite completa tardó 410.33 s.

## B8.3: figuras PNG versionadas (implementado y verificado)

- `ResearchFigure` organiza figuras derivadas de una `ResearchTableRecipeVersion`; `ResearchFigureVersion` persiste versiones append-only. Cada versión lleva hash de entrada tabular, spec/hash, ruta y SHA del PNG, tamaño, dimensiones, tipo MIME, renderer/Pillow, metadatos de accesibilidad, actor y fecha. Migración `0043` añade dos modelos y trigger PostgreSQL contra UPDATE/DELETE.
- Renderer allowlist: barras, líneas y dispersión. Barras: hasta 30 puntos; líneas y dispersión: hasta 500. `y` siempre numérica y finita; `x` categórica solo para barras y numérica para líneas/dispersión. No descarta filas inválidas, no ejecuta código y no admite inferencia, fechas ni multi-series. Salida fija PNG 1200×800 con Pillow/DejaVu Sans.
- Título, ejes y texto alternativo son obligatorios. La accesibilidad se registra pero no se certifica: `accessibility_reviewed=false`. Una tabla truncada exige aceptación explícita y esa condición queda visible en metadatos.
- El titular crea/versiona; miembros del proyecto leen. Preview verifica los bytes contra el hash antes de devolverlos. Endpoints y límites están detallados en el [paquete B8](../02_arquitectura_y_sistema/paquete_b8_datos_figuras.md).

## B8.4: bloques de tabla/figura, snapshots y DOCX aprobado (implementado y verificado)

- El árbol editable conserva schema v1 y admite schema v2 para `data_table` y `figure`, que guardan ID de bloque, ID de versión exacta, hash exacto y caption. El guardado verifica pertenencia al proyecto y hashes. La proyección Markdown es un placeholder legible, no la representación de los datos.
- Al enviar el capítulo, el snapshot guarda `document_artifacts_manifest` con bloque, tipo, versión, hash, caption y metadatos aplicables; este manifest entra al hash canónico del snapshot. Migración `0044` es aditiva y permite árboles v1/v2. No reescribe revisiones o snapshots anteriores.
- El DOCX aprobado revisa cobertura e integridad del manifest, renderiza tabla desde el `result_json` versionado e incrusta los bytes del PNG congelado con texto alternativo. Falta o hash distinto causa error cerrado. Una versión nueva posterior de una figura no cambia la exportación anterior. `GET /export/draft.docx` conserva su comportamiento previo; no se implementa PDF.
- La prueba integrada B8.4 cubre envío, manifest, versiones posteriores de tabla/figura, aprobación y lectura de tabla/imagen/alt text en el DOCX. B8 completo pasó la puerta 7/7, total 479.66 s, pytest 457.26 s, exit code 0 el 26/10/2026. Datos sintéticos prueban el mecanismo, no validez académica.

## Estado actual implementado (corte verificado: 26/10/2026)

### B7: ingesta de fuentes multiformato (implementada y verificada)
- `POST /api/v1/projects/{project_id}/sources/upload` acepta PDF, DOCX, PPTX y XLSX; los originales y hashes se conservan. El procesamiento Office usa `DocumentJob.Kind.FORMAT_EXTRACT` y parsers `python-docx`, `python-pptx` y `openpyxl`.
- `SourceSegment` conserva localizadores de párrafo/tabla, diapositiva/forma, hoja/fila/celda y referencias a imágenes sin OCR. Fórmulas XLSX se guardan como fórmulas; valor cacheado se representa separado; el backend no las calcula.
- `SourcePassage` admite extracto PDF legado o segmento Office, nunca ambos. Búsqueda devuelve candidatos con localizador nativo; esto no aprueba la cita ni confirma respaldo semántico.
- Para PDF mixto, páginas que Poppler no puede leer ponen el archivo en `OCR_REQUIRED`; OCRmyPDF `--skip-text` intenta reconocimiento sin procesar páginas que ya tienen texto. El hash/copia OCR es aparte del original.
- La puerta integral aprobó B7 el 26/10/2026: 7/7, 381.76 s, exit code 0. El benchmark disponible se ejecutó sobre 9 PDF del corpus local; no incluye Office ni se considera representativo. No afirmar precisión OCR medida ni rendimiento general. Detalles y límites en [B7](../02_arquitectura_y_sistema/paquete_b7_multiformato.md).

El tesista usa un cliente MCP o la API Django Ninja; el frontend web propio y su editor enriquecido todavía no están implementados. El asesor usa Django Admin/Unfold o la API de revisión. B4 ya ofrece contratos backend para marcas de cita del documento canónico y revisión de evidencia, pero aún falta demostrar la ida/vuelta desde una interfaz visual.

### B1.1: snapshot inmutable de capítulo al enviar
- **Modelo dedicado e inmutabilidad:** `ChapterSnapshot` (`thesis.models.chapters`) creado en migración `0023_chaptersnapshot_and_submitted_snapshot`. Posee `snapshot_no` correlativo por capítulo, `format_version=1`, `project_title`, `state_version`, `workflow`, `workflow_version_no`, `content_md`, `sections_manifest`, `payload_sha256`, `created_by` y `created_at`. Inmutable en PostgreSQL mediante el trigger append-only `chapter_snapshot_append_only` que reutiliza la función PL/pgSQL `tesismcp_reject_history_change()`.
- **Congelamiento transaccional en `submit_chapter`:** Al enviar el capítulo, compila de forma atómica el contenido consolidado y el `sections_manifest` (en orden según `CHAPTER_STEPS` en modo legado o `WorkflowTask.order_index` en modo configurable), preservando `revision_id`, `output_json` estructurado congelado, `evidence_links` y outputs de tareas personalizadas `USR_...` (`execution_id`, `output_sha256`, `output_json`, `rendered_in_text=False`). Si el capítulo ya se encuentra en `READY`, el reintento es idempotente y devuelve el snapshot existente sin duplicar filas.
- **Relaciones y trazabilidad:** `Chapter.submitted_snapshot` enlaza el snapshot vigente al enviar; `ReviewEvent(SUBMIT)` apunta al snapshot. Las revisiones y comentarios legados se preservan intactos sin cambios destructivos.
- **API REST Django Ninja:** 2 nuevos endpoints bajo `/api/v1/projects/{project_id}/chapters/{chapter_no}/`: `GET /snapshots` (listado) y `GET /snapshots/{snapshot_id}` (detalle completo del snapshot y manifest), protegidos por membresía (`require_project`).
- **Límite explícito de B1.1:** Anclar comentarios y aprobación del asesor al snapshot corresponde a B1.2. Exportar DOCX congelado desde el snapshot corresponde a B1.3. El borrador actual `GET /export/draft.docx` continúa reuniendo las últimas revisiones de pasos.

### B1.2: comentarios y decisiones anclados al snapshot
- **Migración aditiva `0024`:** agrega `Chapter.approved_snapshot` y `ReviewComment.snapshot`, permite `ReviewComment.revision=NULL` y exige exactamente un ancla (`revision` XOR `snapshot`). No reescribe los comentarios, aprobaciones ni eventos legados.
- **Comentarios nuevos:** para un capítulo con snapshot vigente, el asesor debe enviar su `snapshot_id`; el backend verifica que siga siendo la versión vigente y valida offsets/texto seleccionado contra el `content_md` congelado. Los capítulos `READY` históricos sin snapshot conservan el anclaje por revisión.
- **Decisiones:** solicitar cambios y aprobar revisan comentarios abiertos de la versión vigente y escriben `ReviewEvent.snapshot`. La aprobación nueva queda en `Chapter.approved_snapshot`; las aprobaciones históricas siguen en `approved_revision`. Reabrir registra el snapshot aprobado antes de limpiar el puntero vigente.
- **Lectura y resolución:** el listado conserva comentarios de ambos tipos de ancla y admite filtro por `snapshot_id`; la resolución verifica membresía del proyecto y rol de asesor.
- **Límite:** los comentarios de snapshots anteriores no se trasladan al envío siguiente. El DOCX de borrador mantiene su comportamiento actual; exportación congelada es B1.3. Véase el [paquete B1.2](../02_arquitectura_y_sistema/paquete_b1_2_revision_anclada_snapshot.md).

### B1.3: exportación DOCX congelada desde el snapshot aprobado
- Endpoint nuevo: `GET /api/v1/projects/{id}/chapters/{chapter_no}/export/approved.docx`. Requiere membresía activa y capítulo `APPROVED` con `Chapter.approved_snapshot`; un capítulo reabierto o una aprobación histórica por revisión no se presenta como un snapshot aprobado.
- El DOCX se genera desde el `project_title`, contenido y metadatos del snapshot/aprobación. Incluye ID, número y hash SHA-256 de procedencia. Desde B4, las marcas y referencias IEEE preliminares del manifest de citas estructuradas se renderizan como texto estático desde metadatos congelados; esto no certifica que la cita respalde semánticamente la afirmación ni crea campos Zotero activos. Los demás outputs estructurados del manifest (incluidas tareas `USR_...`) no se convierten automáticamente en prosa.
- El borrador `GET /api/v1/projects/{id}/export/draft.docx` sigue compilando las últimas revisiones guardadas. No hubo cambios a ese contrato.
- Sin modelo ni migración. La implementación y sus límites están en el [paquete B1.3](../02_arquitectura_y_sistema/paquete_b1_3_exportacion_congelada_snapshot.md). La puerta integral pasó 7/7 comprobaciones el 26/10/2026.

### B1+B2.1: aceptación de propuestas con contenido textual
- Al aceptar propuestas P05 o P29, el backend guarda su campo contractual `contenido_markdown` como texto de la `ChapterRevision`; ya no lo envuelve en JSON para esa revisión.
- Los demás pasos P siguen conservando su output estructurado como JSON visible en el contenido de revisión, pues no se presume que sus campos sean prosa. Las salidas `USR_...` no se insertan automáticamente.
- No cambia el contrato HTTP ni requiere modelo/migración. Esta primera conexión tipada no implementa el editor canónico enriquecido, el árbol de bloques ni la integración de JSON custom con secciones. Véase el [paquete B1+B2.1](../02_arquitectura_y_sistema/paquete_b1_b2_1_materializacion_textual_propuestas.md).

### B1+B2.2: documento canónico versionado por capítulo
- `ChapterDocument` conserva el puntero a la revisión vigente; `ChapterDocumentRevision` guarda un árbol JSON de bloques v1, una proyección Markdown, hash, procedencia, estado e idempotencia. El trigger PostgreSQL hace las revisiones append-only.
- `GET /projects/{id}/chapters/{no}/document` lee el árbol o presenta una proyección legada de solo lectura. `PUT` guarda como titular con `expected_version` e `idempotency_key`; capítulos `READY`/`APPROVED` no se editan.
- `ChapterSnapshot.document_revision` fija la revisión canónica al enviar. Los snapshots nuevos usan formato 2 y el DOCX aprobado renderiza el árbol congelado; snapshots históricos formato 1 siguen usando Markdown.
- Migración aditiva `0025_canonical_chapter_documents`; al cierre de B1+B2.2: 36 modelos/25 migraciones. La ruta de borrador DOCX no cambia.
- Límites al cierre de B1+B2.2: ida/vuelta con el editor frontend aún por demostrar; comentarios anclados a offsets Markdown; entonces no existía aún el diff IA hacia el árbol; tablas, figuras y citas estructuradas quedaban fuera del árbol v1. El estado posterior está en B1+B2.3 y su [paquete](../02_arquitectura_y_sistema/paquete_b1_b2_3_diffs_ia_documento.md); el [paquete B1+B2.2](../02_arquitectura_y_sistema/paquete_b1_b2_2_documento_canonico.md) conserva el alcance de aquella entrega.

### B1+B2.3: diff de propuesta IA y aplicación controlada al documento
- `GET /projects/{id}/ai-jobs/{job_id}/document-diff` genera, sin escritura, una vista previa tipada `REPLACE_DOCUMENT` para P05/P29: muestra árbol/contenido anterior y propuesto, versión de estado y documento, salida fuente y hash `proposal_sha256`.
- Aceptar P05/P29 exige al tesista devolver la versión del documento y el hash de la vista previa que revisó. El servicio recalcula el diff y verifica ambos dentro de la transacción antes de guardar; el conflicto/alteración no modifica el documento.
- La aceptación conserva `ChapterRevision` y crea una `ChapterDocumentRevision` con `source=AI_PROPOSAL`; `AIGenerationJob.result_document_revision` conserva la trazabilidad. La misma `decision_key` devuelve el resultado existente.
- No se aplica ningún output de otros pasos ni `USR_...` al documento canónico; siguen siendo estructuras revisables bajo sus flujos actuales. El reemplazo propuesto es del capítulo entero, no una inserción invisible.
- Migración `0026_aigenerationjob_result_document_revision_and_more`; conserva 36 modelos y deja el esquema en 26 migraciones antes del siguiente bloque.

### B3.1–B3.3: fuentes bibliográficas y búsqueda peruana en HTTP
- `SourceDocument` conserva OpenAlex pero ahora admite identidad de otros proveedores, identificador del registro, huella del archivo de importación, actor que importó, resumen y publicación/revista. La migración `0027` rellena la identidad OpenAlex histórica sin borrar filas y deja las cargas PDF sin proveedor bibliográfico.
- `POST /api/v1/projects/{id}/sources/import-bibliography` admite archivos RIS, BibTeX y CSV, declara el proveedor `SCOPUS`, `WOS` u `OTHER`, conserva la procedencia y devuelve candidatos de posible duplicación por DOI/título. La importación repetida del mismo archivo/registro es idempotente mediante ID de proveedor o huella+posición. No fusiona registros automáticamente.
- `GET /api/v1/projects/{id}/discovery/peru` expone a la web el servicio existente de búsqueda ALICIA/artículos con filiación peruana, conservando límites y `METADATA_ONLY`.
- Alcance: los metadatos importados no se consideran verificados contra portada; el backend no ejecuta Scopus/WoS, no descarga PDFs desde esas filas y no decide arbitraje. La prueba de la migración y de rutas con PostgreSQL debe completarse en la puerta final.

### B3.4: estrategias de búsqueda versionadas y registro manual
- `SearchStrategy` guarda tema, consulta, ecuación, conceptos, filtros, proveedor objetivo, enlace HTTPS, hash y actor. Cada cambio crea una versión append-only enlazada con `supersedes`; `expected_version` e `idempotency_key` evitan pisar cambios concurrentes o repetir versiones.
- `SearchExecution` conserva la versión exacta de la estrategia, la fecha declarada por el usuario, el actor, cantidad opcional de resultados, notas y hora de registro del servidor. Su API solo permite `MANUAL_USER_DECLARED`; no afirma consulta automática de Scopus/WoS ni ejecución por proveedor.
- Migración `0028_searchstrategy_searchexecution_and_more` añade dos modelos y triggers PostgreSQL append-only. Su puerta integral pasó 7/7.

### B3.5: selección de candidatos y enlace con ejecución manual
- `POST /api/v1/projects/{id}/sources/select-discovery` registra un resultado seleccionado de OpenAlex, Semantic Scholar o ALICIA. Recibe metadatos del cliente; `metadata_origin=USER_SELECTED_CANDIDATE`, `verification_status=UNVERIFIED_METADATA` y `verification_level=USER_SUPPLIED_METADATA_UNVERIFIED` hacen explícito que no se consultó de nuevo al proveedor. No descarga el PDF ni certifica la referencia.
- `SearchExecutionSource` conserva vínculos inmutables entre una ejecución concreta y cada `SourceDocument`, con tipo de vínculo, actor y hora. Una importación bibliográfica puede recibir `execution_id`; sus vínculos guardan el hash de la exportación. No se verifica que el archivo sea auténtico ni se fusionan posibles duplicados.
- La migración `0029_sourcedocument_metadata_origin_searchexecutionsource` añade el origen del metadato, el estado `UNVERIFIED_METADATA` y la relación de procedencia; actualiza las filas previas distinguiendo importaciones de archivos, uploads y consultas API. B3.5 pasó la puerta integral 7/7 (247.81 s, código 0).

### B3.6: decisión humana sobre posibles duplicados
- `SourceDuplicateDecision` conserva una fila inmutable por decisión y versión del par, incluida la base de coincidencia observada (`DOI`, título normalizado o ambos). Las opciones son confirmar duplicidad, mantener registros separados o marcar de forma explícita cuál fuente prefiere el tesista. La detección por DOI/título solo propone pares; no decide por la persona.
- `POST /api/v1/projects/{id}/sources/duplicate-decisions` recibe `source_id`, `other_source_id`, `decision`, `idempotency_key`, `note?` y, para `SET_PRIMARY`, `primary_source_id`. Solo titular; los IDs deben corresponder a fuentes externas del mismo proyecto y el par debe coincidir por DOI o título normalizado.
- `GET /api/v1/projects/{id}/sources/duplicate-decisions` devuelve el historial de decisiones del proyecto e identifica la versión vigente de cada par. La clave de idempotencia se restringe al proyecto; reusar la clave con otro contenido da conflicto.
- La migración `0030_source_duplicate_decisions` impone par ordenado, secuencia positiva, decisión/registro preferido compatibles, guardia PostgreSQL para evitar mezcla de proyectos/tipos de fuente y trigger append-only.
- Ninguna opción elimina o fusiona fuentes, modifica citas o transfiere datos. El estado “preferido” es una decisión de organización del tesista, no una certificación académica ni una validación bibliográfica.
- Pruebas focalizadas: 5 casos en PostgreSQL (historial/idempotencia, autorización/validación, HTTP/lectura, inmutabilidad y aislamiento a nivel DB). La puerta integral de este corte se reporta en la entrega.

### B4.1–B4.5: citas, revisión de evidencia, sustitución y Zotero
- `ChapterCitationOccurrence` registra cada fuente de una marca dentro de una revisión `ChapterDocumentRevision`, con grupo, orden, UUID de bloque, offset, localizador y copia congelada de metadatos. La guarda PostgreSQL mantiene mismo proyecto y ancla de párrafo; las ocurrencias son append-only. `citation_manifest_sha256` se incorpora a revisiones, snapshot y exportación aprobada.
- `GET /api/v1/projects/{id}/chapters/{n}/citations/ieee` numera por primera aparición en orden del documento y reutiliza los números. Las marcas de varias fuentes se conservan. El render es genérico y preliminar: señala metadatos faltantes y no valida formato IEEE completo por tipo documental.
- La ruta de evidencia liga el rango de una afirmación que contiene la cita con un pasaje exacto de la misma fuente `TEXT_CHECKED`. Conserva texto, offsets, página y hashes. Crossref solo comprueba identidad/metadatos; la API declara `automated_semantic_assessment=NOT_PERFORMED`. El asesor registra en un historial versionado si respalda, contradice, no corresponde o es insuficiente.
- Las propuestas de sustitución congelan referencias anterior/nueva, motivo, revisión y hash. La vista previa informa la diferencia; únicamente la aceptación del titular crea una nueva revisión del documento. Rechazar no altera el manuscrito y la ocurrencia histórica sigue preservada.
- Zotero usa OAuth 1.0a con acceso de lectura a biblioteca personal, sin notas, escritura o grupos. La clave API queda cifrada con Fernet. Se pueden listar/importar registros bibliográficos, que entran como `UNVERIFIED_METADATA`; no se descargan adjuntos ni se escriben cambios a Zotero. Desconectar intenta revocar la clave remota y elimina la copia local.
- B4 no implementa campos Zotero vivos en DOCX, evaluación semántica automática ni estilos IEEE completos por tipo. La conexión OAuth real está pendiente de registrar/configurar la aplicación y probar credenciales. P20 admite IEEE y conserva APA 7 por compatibilidad; es independiente de la vista IEEE estructurada del editor.
- Endpoints, permisos, payloads, variables de entorno, datos y limitaciones están en [implementación B4](../02_arquitectura_y_sistema/implementacion_b4_citas_ieee_zotero.md). La puerta integral B4 pasó el 26/10/2026 (7/7, 287.61 s, exit code 0).

### B6.1: lotes de generación de tareas (implementado y verificado)
- Crea `AIGenerationBatch` y `AIGenerationBatchItem`, con migración `0036` y triggers append-only. Reutiliza `AIGenerationJob` B5.1: cada salida continúa como propuesta independiente.
- Rutas implementadas y verificadas: crear (`POST`), listar (`GET`), consultar (`GET` por ID) y cancelar (`POST`) bajo `/api/v1/projects/{project_id}/ai-batches`. Puerta completa 7/7, 288.97 s, exit code 0.
- Se valida máximo de 8 tareas distintas, versiones, idempotencia/hash, independencia por dependencias bloqueantes, permisos owner-only para crear/cancelar y rollback completo si falla un job.
- El estado agregado se calcula desde los jobs. La cancelación cambia solo jobs `QUEUED`. B6.2 añade reclamos atómicos y concurrencia limitada en un proceso; B6.3 incorpora síntesis supervisada en la misma cola y B6.4 invitaciones de alcance mínimo.
- Contrato y detalle en [paquete B6.1](../02_arquitectura_y_sistema/paquete_b6_1_lotes_generacion.md); pruebas focalizadas en `backend/thesis/tests/test_ai_batches.py`.

### B6.2: concurrencia acotada del worker IA (implementada y verificada)
- El reclamo cambia `QUEUED` a `RUNNING`, fija `started_at` y suma `attempts` dentro de la misma transacción que selecciona la fila; consumidores con `skip_locked` reclaman jobs distintos.
- `run_ai_worker --concurrency N` permite concurrencia dentro de un único proceso y conserva el advisory lock global. El valor predeterminado es 1; `TESISMCP_AI_WORKER_MAX_CONCURRENCY` limita el máximo (predeterminado 4). `--once` solo admite 1 consumidor.
- Al iniciar bajo el lock global, jobs que quedaron `RUNNING` se marcan `FAILED/WORKER_INTERRUPTED`. No se reintentan automáticamente porque el proveedor pudo haber completado/facturado la llamada antes de una caída.
- Compose incorpora `ai_worker` separado del trabajador documental y pasa credenciales solo desde el entorno. No se implementa un presupuesto monetario ni se modifica API/modelos/migraciones.
- Pruebas focalizadas: 19 pasaron en `backend/thesis/tests/test_ai_generation.py`. Puerta integral aprobada 7/7, 313.67 s, exit code 0. Contrato: [paquete B6.2](../02_arquitectura_y_sistema/paquete_b6_2_concurrencia_worker.md).

### B6.3: síntesis trazable de outputs de lote (implementada y verificada)
- El titular selecciona de 2 a 8 jobs `SUCCEEDED` del mismo lote. El sistema comprueba sus hashes y congela sus JSON y procedencia como snapshot inmutable con prompt/esquema versionados.
- El worker compartido procesa la síntesis con salida estructurada (resumen, acuerdos, diferencias, vacíos y recomendaciones). Cada referencia debe señalar a tareas seleccionadas; una referencia ajena invalida el resultado.
- El titular decide aceptar o rechazar el informe auxiliar. Esa decisión no acepta cada job de origen ni aprueba el capítulo; el informe no modifica el documento canónico.
- Las rutas están bajo `/api/v1/projects/{project_id}/ai-batches/{batch_id}/syntheses`. Ver [contrato B6.3](../02_arquitectura_y_sistema/paquete_b6_3_sintesis_trazable.md).

### B6.4: invitaciones de apoyo por tarea y materiales (implementada y verificada)
- Titular o asesor asignado invita una cuenta activa existente a una tarea de recorrido publicada y hasta 25 fuentes del proyecto. Aceptar requiere autenticación y coincidencia de correo.
- El token aleatorio se persiste como SHA-256 y se entrega una vez; expiración 1–720 horas (default 168), revocación y verificación de vigencia en cada operación.
- Invitado consulta solo la tarea, metadatos/extractos concedidos (hasta 200) y PDFs autorizados cuyo SHA-256 coincide. Puede enviar texto y citar hasta 30 extractos compartidos; el aporte es idempotente y append-only.
- El invitado no adquiere `ProjectParticipant`, no edita el manuscrito, no accede a jobs, no aprueba y no invita a terceros. No hay alta de usuarios, envío de correos ni carga de archivos en este bloque.
- Las rutas administrativas y de invitado están descritas en [contrato B6.4](../02_arquitectura_y_sistema/paquete_b6_4_invitaciones_apoyo.md). La migración conjunta es `0037`.

### B5.1: ciclo backend de generación por tarea (adaptador implementado; llamada real pendiente)
- **Modelos de generación y contratos:** `AIGenerationJob` se introduce en la migración `0021_ai_generation_job_and_task_output_schema`; los campos posteriores de versión de estado/decisión se añaden en `0022`. Tiene ciclo de vida (`QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED`), estados de aceptación (`PENDING_ACCEPTANCE`, `ACCEPTED`, `REJECTED`), snapshot de contexto, hash SHA-256 e idempotencia por proyecto. `WorkflowTask.output_schema` valida tareas personalizadas `USR_...`.
- **Estado del proveedor:** fábrica `get_llm_adapter` y normalización de errores. El mock solo se permite en `DEBUG`; el proveedor predeterminado es `DISABLED`. La opción `GEMINI` está implementada mediante `GeminiProviderAdapter` y el SDK oficial `google-genai` (`from google import genai`), con `GEMINI_API_KEY` y modelo `gemini-3.8-flash` configurados del lado del servidor, mapeo de errores y pruebas con SDK simulado. La llamada real queda pendiente de configurar credenciales; no se presenta la simulación como conexión en vivo.
- **Servicios de dominio y validación:** `request_task_generation`, `get_ai_job`, `cancel_ai_job`, `accept_ai_proposal` y `reject_ai_proposal` en `backend/thesis/services/ai_jobs.py`. Los jobs fijan la versión del estado al solicitarse, prompt, workflow, esquema y contexto; la salida se valida localmente. La aceptación usa solo la salida guardada en el job y reutiliza `save_step` para P01–P32 y `WorkflowTaskExecution` para `USR_...`.
- **API REST Django Ninja:** 5 endpoints bajo `/api/v1/projects/{project_id}/`: `.../tasks/{task_id}/generate` (`202`/`200`), `.../ai-jobs/{job_id}`, `.../ai-jobs/{job_id}/cancel`, `.../ai-jobs/{job_id}/accept` y `.../ai-jobs/{job_id}/reject`.
- **Trabajador en segundo plano:** comando `run_ai_worker` con bloqueo PostgreSQL (`pg_try_advisory_lock`) y soporte `--once`. La API encola por defecto; el modo síncrono es una opción explícita de desarrollo.
- **Límite explícito de B5.1:** La generación IA produce propuestas estructuradas que el tesista debe aceptar explícitamente. Las tareas `USR_...` aceptadas no se insertan automáticamente en el DOCX (la integración canónica a capítulos pertenece a B1+B2). Multiagentes paralelos y selección libre de modelo por el usuario quedan para entregas posteriores (B6).

## Dirección objetivo confirmada (25/10/2026; sin cambios en este corte)

- TesisMCP será web-first: el tesista y el asesor trabajarán principalmente dentro de nuestra plataforma. MCP seguirá disponible como conexión adicional.
- Se desarrollará un editor enriquecido propio dentro del frontend de TesisMCP. El flujo habitual de escritura, edición y revisión no dependerá de abrir otro procesador.
- P01–P32 y los capítulos 1–7 son la base implementada, no el límite funcional final. La dirección de producto contempla recorrido/prompts configurables por proyecto y acompañamiento hasta análisis real, resultados y entrega. Estas capacidades nuevas **no están implementadas en el corte de código de este documento**; antes de añadir código, verificar el estado real y completar solo las brechas.
- Zotero se integrará como gestor bibliográfico existente; no se clonará su aplicación. Las citas gestionadas en TesisMCP y los campos activos de Zotero en un DOCX externo son capacidades diferentes.
- La búsqueda asistida en Scopus/WoS debe funcionar sin API: TesisMCP prepara y guarda ecuaciones/filtros, abre el sitio oficial y procesa resultados exportados por el usuario. Las APIs quedan como conectores opcionales sujetos a permiso.
- El editor objetivo incluye revisión afirmación–cita: distinguir metadatos válidos de respaldo textual, mostrar pasaje/localizador/nivel de acceso y proponer cambios con diff. La IA no reemplaza citas ni edita el manuscrito canónico sin aceptación. B1+B2.3 cubre reemplazo supervisado para P05/P29; no verifica citas, no aplica otros pasos y aún requiere integración/round-trip real con el editor frontend.
- Expertos y bibliotecarios pueden ser invitados a tareas y paquetes de documentos delimitados; sus aportes reducen repetición, pero no les dan permisos generales ni aprobación académica. La configuración institucional de guías está separada del acceso a tesis privadas.
- La plataforma debe diseñarse para reducir tareas repetitivas de tesista, asesor y apoyos (búsquedas, deduplicación, cotejo, lotes de comentarios y seguimiento). El ahorro real se reportará solo después de medir tareas comparables con usuarios.
- DOCX, PDF y otros formatos serán salidas para entrega o edición externa. Collabora Online queda fuera de la propuesta.

La dirección objetivo no debe reportarse como implementada hasta que se verifique en el código y la interfaz.

Para programar el backend de esa dirección sin rehacer P01–P32, seguir la [guía de desarrollo de la versión completa](../02_arquitectura_y_sistema/guia_backend_version_completa_para_agentes.md), el [contrato de recorrido y prompts configurables](../02_arquitectura_y_sistema/contrato_recorrido_y_prompts_configurables.md) y la [especificación de búsqueda, lectura documental y revisión de afirmaciones](../02_arquitectura_y_sistema/especificacion_busqueda_y_revision_de_evidencia.md). Los puntos de este apartado son objetivo, no capacidades presentes en el corte de código.

## Funciones implementadas

- Guardado de P01–P32 con contratos, versiones, revisiones y flujo de observaciones del asesor; los proyectos heredados conservan modo secuencial y los proyectos configurables usan grafo de dependencias. El ciclo de generación backend dispone de adaptador Gemini; el proveedor sigue deshabilitado por defecto y una llamada real no se verificó por falta de credenciales. Las tareas `USR_...` también pueden persistir JSON recibido mediante `execute`.
- Incorporación de PDF en segundo plano, extracción por página física, OCR, análisis GROBID, cotejo DOI e indexación local cuando están disponibles sus servicios auxiliares.
- Búsqueda de literatura: internacional (OpenAlex y Semantic Scholar) y peruana (ALICIA y artículos catalogados por OpenAlex con filiación institucional en Perú). Todas las búsquedas devuelven metadatos (`METADATA_ONLY`); la filiación y el tipo `article` no acreditan revisión por pares.
- Clasificación geográfica explicable (`LOCAL_POR_INSTITUCION`, `LOCAL_POR_OBJETO_ESTUDIO`, `NACIONAL`) conectada con `profile.place`. Sin lugar configurado no se atribuye localidad; las fallas de proveedores se informan.
- P16 exige un PDF registrado con texto extraído, extractos y citas literales localizadas para metodología, muestra y hallazgo. Conserva página física y huellas de procedencia con nivel `TEXT_EXTRACTED_WITH_QUOTES`. Estas comprobaciones no sustituyen la lectura crítica del PDF ni verifican por sí solas la portada.
- La migración `0018` revisa fichas P16 antiguas: solo cambia su etiqueta al nivel de texto extraído si todavía existen el PDF registrado y las tres citas literales; en otro caso usa `LEGACY_UNVERIFIED`.
- P20 acepta IEEE y APA 7 como estilos declarados. No existe todavía un comprobador completo de sintaxis ni de correspondencia de todas las citas con la bibliografía.
- Descarga de borrador DOCX con el texto guardado. Usa A4, Arial 11, interlineado doble y márgenes indicados en el [Anexo 15 de la Guía del Egresado UTP v14](https://www.utp.edu.pe/web/sites/default/files/2026-05/Guia_del_egresado_Pregrado_V14_PT.pdf). No genera la carátula institucional completa, el reporte de similitud ni una tesis lista para sustentar.
- Prompts MCP (`mcp_server/prompts/`): el cliente LLM sigue tres roles secuenciales (Asesor Metodológico, Investigador Grounded, Revisor de Contratos). Con token válido, el servidor incorpora variables y matriz de consistencia desde PostgreSQL. Hay plantillas P01–P32 y prompts de rol; el flujo no equivale a agentes autónomos ni a una llamada de modelo iniciada por Django.
- Imagen de contenedor para la API y el trabajador, con volúmenes locales persistentes para documentos y modelos. `/health/` comprueba la conexión a PostgreSQL.

## Trabajo necesario antes de declarar una versión final pública

1. La demo local (`mcp_server/test_local.py`) incorpora el PDF real de ARIA, extrae texto por página y comprueba citas literales. Se corrigieron autores y DOI contra la [ficha oficial de arXiv](https://arxiv.org/abs/2502.07960). El estado `TEXT_EXTRACTED_WITH_QUOTES` no afirma revisión humana completa. La demo volvió a ejecutarse con PostgreSQL: completó P01–P32, bloqueó un antecedente inventado y recorrió la revisión de los siete capítulos. Los datos del caso y el coeficiente piloto son simulados.
2. El adaptador ALICIA/CONCYTEC y la clasificación nacional/local están implementados. Las pruebas verifican la normalización con respuestas simuladas, incluida la separación de autores y la ausencia de una institución inventada. En esta revisión no se pudo certificar la disponibilidad en vivo del endpoint externo; debe comprobarse en el entorno de despliegue.
3. Las plantillas de prompts y sus tres roles secuenciales están implementados. Los ejemplos JSON se validan automáticamente contra sus contratos. La suite completa con PostgreSQL pasó 59 pruebas tras las correcciones funcionales.
4. Completar carátula, secciones institucionales y reporte de similitud a partir de datos auténticos. El Anexo 15 de la guía UTP exige esas partes; el proyecto actual exporta un borrador editable.
5. Publicar API y trabajador en infraestructura con HTTPS, secretos y almacenamiento documental persistente compartido. El perfil de Compose es local; no se ha efectuado un despliegue público.
6. Realizar pruebas de uso con tesistas y asesores reales y una revisión académica de los documentos producidos. Las pruebas automatizadas comprueban reglas de software, no la aceptación institucional ni la validez científica de una tesis.
7. Vincular las métricas del piloto de P32 con datos de campo originales y un cálculo reproducible. El contrato actual recibe un coeficiente declarado por el cliente; sus límites numéricos no demuestran que provenga de respuestas reales.

## Verificación local

```bash
DJANGO_DEBUG=1 .venv/bin/python backend/manage.py check
DJANGO_DEBUG=1 .venv/bin/python backend/manage.py makemigrations --check --dry-run
DJANGO_DEBUG=1 .venv/bin/pytest --reuse-db -q
python3 -m core.grounding.audit_cli
```

### Reparación operativa local posterior a B8

La base activa estaba en `0023` y fue actualizada hasta `0044` tras un respaldo conjunto DB+media, restauración y ensayo aislado. Se comprobó conservación de datos previos y lectura de archivos. `scripts/local_recovery.py` es el procedimiento manual canónico; no hay periodicidad ni copia fuera del disco. El gate agrega una comprobación independiente de migraciones aplicadas. [Registro y límites B10](../02_arquitectura_y_sistema/paquete_b10_operacion_local_y_despliegue.md). Este avance no cierra el producto ni acredita integraciones externas.
