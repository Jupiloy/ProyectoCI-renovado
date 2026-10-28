# Contratos de API del backend

**Estado:** referencia para evolución compatible de Django Ninja. **Actualizado:** 26/10/2026.

El catálogo exacto de endpoints implementados se conserva en [README del backend](../../backend/README.md). No copiar aquí esa lista como si describiera el objetivo completo. La API web y MCP deben llamar los mismos servicios; el frontend no accede a PostgreSQL directamente y MCP no acepta una identidad elegida por el modelo.

## Inventario de rutas HTTP observadas en el código

La API se monta bajo `/api/v1/`; estas rutas están declaradas en `backend/thesis/api/projects.py` en el corte inspeccionado. La autenticación global es `django_auth` (sesión Django); las escrituras autenticadas usan CSRF. El servicio vuelve a comprobar membresía/capacidad. `owner_only` se exige, entre otras, para guardar idea/pasos, incorporar OpenAlex encolado, subir archivos y solicitar jobs documentales. El asesor se valida en las operaciones de revisión. Verificar la guarda concreta en el servicio antes de ampliar cada operación.

| Método y ruta | Entrada declarada en API | Uso/resultado resumido |
|---|---|---|
| `POST /projects` | JSON `{name, title?}` | Crea proyecto y titular; título puede omitirse. |
| `GET /projects/{project_id}` | Path UUID | Estado del proyecto autorizado. |
| `GET /projects/{project_id}/export/draft.docx` | Path UUID | Descarga DOCX de borrador. |
| `PUT /projects/{project_id}/idea` | `{description, expected_version}` | Guarda idea provisional con control de versión. |
| `GET /projects/{project_id}/idea/explore` | Path UUID | Explora idea; metadatos de OpenAlex o preguntas si falta idea. |
| `GET /projects/{project_id}/discovery/semantic-scholar` | Query `query`, `limit=5` | Resultados marcados `METADATA_ONLY`. |
| `GET /projects/{project_id}/discovery/peru` | Query `query`, `scope_filter=todos`, `include_articles=true`, `limit=5` | Búsqueda ALICIA/OpenAlex con clasificación geográfica explicable; solo metadatos. |
| `POST /projects/{project_id}/search-strategies` | `{provider, title, topic, query_text, search_equation?, concepts?, filters?, search_url?, idempotency_key}` | Titular crea una estrategia versión 1 inmutable; la URL opcional debe ser HTTPS y, para Scopus/WoS, del dominio oficial correspondiente. |
| `GET /projects/{project_id}/search-strategies` | Path UUID | Lista la versión más reciente de cada serie; miembros autorizados pueden consultar. |
| `GET /projects/{project_id}/search-strategies/{strategy_id}` | Path UUID | Devuelve el historial de versiones de la serie a la que pertenece la versión indicada. |
| `POST /projects/{project_id}/search-strategies/{strategy_id}/revisions` | Datos de estrategia más `expected_version` | Titular crea una versión nueva; no edita la anterior y rechaza conflictos de versión. |
| `POST /projects/{project_id}/search-strategies/{strategy_id}/executions/manual` | `{execution_date, reported_result_count?, notes?, idempotency_key}` | Titular registra una declaración manual asociada a esa versión. Respuesta `execution_mode=MANUAL_USER_DECLARED`; no acredita que el backend consultó Scopus/WoS. |
| `GET /projects/{project_id}/search-strategies/{strategy_id}/executions` | Path UUID | Lista declaraciones manuales ligadas a esa versión de estrategia. |
| `GET /projects/{project_id}/search-strategies/{strategy_id}/executions/{execution_id}/sources` | Path UUIDs | Lista vínculos históricos de fuentes para la ejecución, con tipo, hash del archivo, actor y datos de la fuente. La consulta exige que ejecución y estrategia pertenezcan al proyecto indicado. |
| `POST /projects/{project_id}/advisor` | `{email}` | Asigna cuenta activa existente como asesor. |
| `GET /projects/advisor/dashboard` | Sesión | Panel de proyectos del asesor autenticado. |
| `PUT /projects/{project_id}/steps/{step_code}` | `{content_md, output_data, expected_version, idempotency_key}` | Valida/guarda un paso y crea revisión asociada. |
| `GET /projects/{project_id}/chapters/{chapter_no}` | Path UUID/int | Progreso, última revisión y estado autorizado. |
| `GET /projects/{project_id}/chapters/{chapter_no}/document` | Path UUID/int | Lee documento canónico vigente; si solo existen revisiones legadas, devuelve proyección de solo lectura con `is_legacy_projection=true`. |
| `PUT /projects/{project_id}/chapters/{chapter_no}/document` | `{content_tree, citations?, expected_version, idempotency_key}` | Titular guarda revisión inmutable; valida bloques y marcas de cita por párrafo, ancla y fuente del proyecto; control optimista e idempotencia. |
| `POST /projects/{project_id}/chapters/{chapter_no}/submit` | Sin body | Envía capítulo cuando sus pasos están completos. |
| `POST /projects/{project_id}/chapters/{chapter_no}/comments` | `{start_cp, end_cp, selected_text, body}` | Asesor comenta una selección exacta de la revisión vigente. |
| `GET /projects/{project_id}/chapters/{chapter_no}/comments` | Path | Lista comentarios del participante autorizado. |
| `POST /projects/{project_id}/comments/{comment_id}/resolve` | Path | Asesor resuelve observación. |
| `POST /projects/{project_id}/chapters/{chapter_no}/decision` | `{action, reason?}` | Asesor solicita cambios, aprueba o reabre según estado y guardas. |
| `POST /projects/{project_id}/datasets` | multipart `name`, `file`, `idempotency_key`, `description?`, `sheet_name?` | Titular crea dataset CSV/XLSX y versión inicial. |
| `GET /projects/{project_id}/datasets` | Path UUID | Participante autorizado consulta datasets del proyecto. |
| `POST /projects/{project_id}/datasets/{dataset_id}/versions` | multipart `file`, `expected_version`, `idempotency_key`, `sheet_name?` | Titular agrega versión inmutable del original. |
| `GET /projects/{project_id}/datasets/{dataset_id}/versions` | Path UUIDs | Miembro autorizado consulta historial de versiones. |
| `GET /projects/{project_id}/datasets/{dataset_id}/versions/{version_no}` | Path UUID/int | Consulta metadatos de la versión exacta. |
| `GET /projects/{project_id}/datasets/{dataset_id}/versions/{version_no}/download` | Path UUID/int | Descarga original tras cotejar SHA-256. |
| `POST /projects/{project_id}/datasets/{dataset_id}/versions/{version_no}/table-recipes` | `{name, spec, idempotency_key, expected_version?}` | Titular crea o versiona receta declarativa; produce resultado tabular derivado con hashes. |
| `GET /projects/{project_id}/datasets/{dataset_id}/versions/{version_no}/table-recipes` | Path UUID/int | Lista recetas ligadas a esa versión exacta del dataset. |
| `GET /projects/{project_id}/datasets/{dataset_id}/table-recipes/{recipe_id}/versions` | Path UUIDs | Lista historial de versiones inmutables de una receta. |
| `GET /projects/{project_id}/datasets/{dataset_id}/table-recipes/{recipe_id}/versions/{version_no}` | Path UUID/int | Lee especificación, salida y hashes verificados de la versión exacta. |
| `POST /projects/{project_id}/sources` | `{openalex_id}` | Registra metadatos; devuelve `200` o `202` si encola PDF. |
| `POST /projects/{project_id}/sources/upload` | multipart `label`, `file` | Carga PDF/DOCX/PPTX/XLSX, máximo local 30 MiB; conserva original/hash y encola extracción (`202`). DOCX de fuentes usa este recurso; manuscrito DOCX sigue su endpoint independiente. |
| `POST /projects/{project_id}/sources/import-bibliography` | multipart `provider` (`SCOPUS`, `WOS`, `OTHER`), `file` (`.ris`, `.bib`/`.bibtex`, `.csv`) y `execution_id?` | Importa registros y posibles duplicados; con `execution_id` crea vínculos inmutables por fila que conservan la huella del archivo. No verifica autenticidad del archivo ni que corresponda a esa búsqueda. |
| `POST /projects/{project_id}/sources/select-discovery` | `{provider, provider_record_id, title, authors?, publication_year?, doi?, abstract?, publication_venue?, record_url?, pdf_url?, search_execution_id?}` | El titular registra un candidato de OpenAlex, Semantic Scholar o ALICIA. Los metadatos provienen del cliente y se etiquetan `USER_SUPPLIED_METADATA_UNVERIFIED`; posibles duplicados se informan sin fusionar. Puede enlazarse a una ejecución manual del proyecto. |
| `POST /projects/{project_id}/sources/duplicate-decisions` | `{source_id, other_source_id, decision, primary_source_id?, note?, idempotency_key}` | Solo el titular registra una decisión versionada para un par candidato. `decision`: `MARK_DUPLICATE`, `KEEP_SEPARATE` o `SET_PRIMARY`; esta última exige que `primary_source_id` sea uno de los dos. No borra ni fusiona registros. |
| `GET /projects/{project_id}/sources/duplicate-decisions` | Path UUID | Miembros autorizados consultan el historial y la marca `is_current` por par. |
| `GET /projects/{project_id}/chapters/{chapter_no}/citations/ieee` | Path | Vista IEEE preliminar de citas estructuradas de revisión vigente; numeración por primera aparición. |
| `POST /projects/{project_id}/chapters/{chapter_no}/citations/{occurrence_id}/evidence` | `{excerpt_id, claim_start, claim_end, excerpt_start, excerpt_end, idempotency_key}` | Titular crea candidato de evidencia ligado a cita y extracto exactos de la misma fuente `TEXT_CHECKED`. No evalúa semántica. |
| `GET /projects/{project_id}/chapters/{chapter_no}/citations/{occurrence_id}/evidence` | Path | Miembro autorizado consulta historial y estados de evidencia. |
| `POST /projects/{project_id}/chapters/{chapter_no}/citation-evidence/{review_id}/decision` | `{status, expected_version, idempotency_key, note?}` | Asesor crea estado humano versionado (`SUPPORTS`, `CONTRADICTS`, `UNRELATED`, `INSUFFICIENT`). |
| `POST /projects/{project_id}/chapters/{chapter_no}/citations/{occurrence_id}/replacement-proposals` | `{replacement_source_id, rationale, idempotency_key}` | Titular/asesor propone otra fuente; no modifica aún el documento. |
| `GET /projects/{project_id}/chapters/{chapter_no}/citation-replacement-proposals/{proposal_id}` | Path | Vista comparativa de referencias congeladas y IEEE preliminar. |
| `POST /projects/{project_id}/chapters/{chapter_no}/citation-replacement-proposals/{proposal_id}/decision` | `{action, expected_document_version, idempotency_key, reason?}` | Solo titular acepta/rechaza. Aceptar crea una revisión canónica nueva. |
| `GET /integrations/zotero` | Sesión autenticada | Estado de conexión sin devolver claves ni secretos. |
| `GET /integrations/zotero/connect` | Sesión y callback OAuth configurados | Inicia autorización Zotero OAuth 1.0a con biblioteca personal de lectura. |
| `GET /integrations/zotero/callback` | `oauth_token`, `oauth_verifier` | Completa intercambio OAuth atado a sesión; guarda clave cifrada. |
| `DELETE /integrations/zotero` | Sesión autenticada | Intenta revocación remota y borra secreto local; reporta si hace falta revocar manualmente. |
| `GET /projects/{project_id}/sources/zotero` | Query `query?`, `start=0`, `limit=25` | Lista biblioteca personal; no descarga adjuntos. |
| `POST /projects/{project_id}/sources/import-zotero` | `{item_key}` | Titular copia metadatos como `UNVERIFIED_METADATA`; no verifica texto/portada ni escribe en Zotero. |
| `GET /projects/{project_id}/sources` | Path | Lista fuentes y nivel de verificación. |
| `GET /projects/{project_id}/sources/{source_id}/excerpts` | `page_no?`, `limit=20` | Extractos localizados por página. |
| `GET /projects/{project_id}/sources/{source_id}/segments` | `offset=0`, `limit=50` (máximo 100) | Segmentos multiformato con `kind`, hash y localizador JSON (párrafo/tabla, diapositiva/forma, hoja/celda). |
| `POST /projects/{project_id}/sources/{source_id}/doi-check` | Path | Encola cotejo DOI (`202`). |
| `GET /projects/{project_id}/sources/{source_id}/doi-check` | Path | Consulta resultado del cotejo. |
| `POST /projects/{project_id}/sources/{source_id}/locate` | `{quote, limit=5}` | Localiza coincidencias candidatas en texto extraído. |
| `POST /projects/{project_id}/evidence-links` | `{excerpt_id, claim_text, start_char, end_char, matched_text, revision_id?}` | Crea vínculo candidato de evidencia. |
| `GET /projects/{project_id}/evidence-links` | `limit=50` | Lista vínculos autorizados. |
| `POST /projects/{project_id}/evidence-links/{link_id}/review` | `{decision, note?}` | Asesor confirma o rechaza el vínculo. |
| `POST /projects/{project_id}/sources/{source_id}/ocr` | Path | Encola OCR (`202`) cuando corresponde. |
| `POST /projects/{project_id}/sources/{source_id}/grobid` | Path | Encola análisis GROBID (`202`). |
| `GET /projects/{project_id}/sources/{source_id}/grobid` | `offset=0`, `limit=20` | Consulta referencias extraídas. |
| `POST /projects/{project_id}/sources/{source_id}/index` | Path | Encola indexación de pasajes (`202`). |
| `GET /projects/{project_id}/jobs/{job_id}` | Path UUID | Consulta estado/resultado/error del trabajo autorizado. |
| `POST /projects/{project_id}/passages/search` | `{query, limit=5}` | Busca candidatos; mantiene página física para PDF y `segment_id`/localizador para Office. No confirma respaldo semántico. |
| `POST /projects/{project_id}/manuscripts/upload` | multipart `label`, `file` | Carga DOCX para conversión asíncrona (`202`). |
| `GET /projects/{project_id}/manuscripts` | Path | Lista manuscritos del proyecto. |
| `GET /projects/{project_id}/manuscripts/{manuscript_id}` | Path UUID | Obtiene Markdown y campos detectados; citas no verificadas. |
| `GET /projects/{project_id}/workflow` | Path UUID | Consulta publicado, borrador e historial del recorrido. |
| `PUT /projects/{project_id}/workflow/draft` | `{tasks, dependencies?, expected_version}` | Crea/actualiza borrador del recorrido y prompts; admite tareas `USR_...`. |
| `POST /projects/{project_id}/workflow/validate` | Sin body | Valida borrador y dependencias antes de publicar. |
| `POST /projects/{project_id}/workflow/publish` | `{change_summary?, expected_version}` | Publica una versión del recorrido. |
| `POST /projects/{project_id}/workflow/restore` | `{target_version_no, change_summary?}` | Crea versión publicada restaurada. |
| `GET /projects/{project_id}/workflow/tasks/{task_id}/prompt` | Path | Devuelve el prompt efectivo de la tarea publicada. |
| `POST /projects/{project_id}/workflow/tasks/{task_id}/execute` | `{input_data?, output_data, idempotency_key}` | Persiste output JSON suministrado por el cliente para tarea custom; no llama a un LLM. |
| `GET /projects/{project_id}/workflow/tasks/{task_id}/executions` | `workflow_version_no?` | Recupera las últimas ejecuciones almacenadas de una tarea custom. |
| `POST /projects/{project_id}/workflow/tasks/{task_id}/generate` | `{input_data?, context_refs?, idempotency_key, expected_state_version?, workflow_version_no?}` | Solicita propuesta asistida con IA (`202`/`200`); genera `AIGenerationJob` observable. |
| `POST /projects/{project_id}/ai-batches` | `{tasks:[{task_id,input_data?,context_refs?}], expected_state_version, workflow_version_no, idempotency_key}` | Titular crea atómicamente un lote de 1–8 tareas independientes; un job B5.1 por tarea; responde `202`. Repetición idéntica devuelve el mismo lote; clave con payload distinto entra en conflicto. |
| `GET /projects/{project_id}/ai-batches` | Path UUID | Lista hasta 50 lotes del proyecto para participantes autorizados. |
| `GET /projects/{project_id}/ai-batches/{batch_id}` | Path UUID | Consulta estado agregado derivado, orden de items y datos seguros de los jobs asociados. |
| `POST /projects/{project_id}/ai-batches/{batch_id}/cancel` | Path UUID | Titular cancela jobs `QUEUED` solamente; informa los ya terminales y los que siguen `RUNNING`. |
| `POST /projects/{project_id}/ai-batches/{batch_id}/syntheses` | `{job_ids:[UUID×2..8], idempotency_key}` | Titular crea síntesis auxiliar `QUEUED` desde outputs `SUCCEEDED` del lote; fija snapshot/hash. Responde `202`; no modifica manuscrito ni aceptación de jobs fuente. |
| `GET /projects/{project_id}/ai-batches/{batch_id}/syntheses` | Path UUID | Participante autorizado lista hasta 50 síntesis. |
| `GET /projects/{project_id}/ai-batches/{batch_id}/syntheses/{synthesis_id}` | Path UUID | Participante consulta estado, snapshot de fuentes y salida validada si terminó con éxito. |
| `POST /projects/{project_id}/ai-batches/{batch_id}/syntheses/{synthesis_id}/cancel` | Path UUID | Titular cancela solo una síntesis `QUEUED`. |
| `POST /projects/{project_id}/ai-batches/{batch_id}/syntheses/{synthesis_id}/decision` | `{decision: ACCEPTED\|REJECTED, decision_key, reason?}` | Titular acepta/rechaza el informe auxiliar `SUCCEEDED`; no es aprobación académica ni inserta contenido en capítulo. |
| `POST /projects/{project_id}/support-invitations` | `{invited_email, task_id, task_instructions, source_ids:[UUID], ttl_hours=168}` | Titular o asesor asignado invita una cuenta activa a una tarea publicada y fuentes explícitas; devuelve token plano de un solo uso. No se envía correo. |
| `GET /projects/{project_id}/support-invitations` | Path UUID | Titular o asesor asignado lista invitaciones del proyecto. |
| `POST /projects/{project_id}/support-invitations/{invitation_id}/revoke` | Path UUID | Titular o asesor asignado revoca invitación vigente sin borrar aportes históricos. |
| `GET /projects/{project_id}/support-invitations/{invitation_id}/contributions` | Path UUID | Titular o asesor asignado consulta aportes append-only. |
| `POST /projects/support-invitations/{invitation_id}/accept` | `{invite_token}` | Cuenta autenticada con email igual al invitado acepta; token persistido solo como SHA-256. |
| `GET /projects/support-invitations/{invitation_id}/workspace` | Path UUID | Invitado aceptado/vigente consulta solo la tarea y recursos concedidos. |
| `GET /projects/support-invitations/{invitation_id}/sources/{source_id}/file` | Path UUID | Descarga PDF solo si está grant, bajo MEDIA_ROOT y coincide SHA-256. |
| `POST /projects/support-invitations/{invitation_id}/contributions` | `{response_text, source_excerpt_ids:[integer], idempotency_key}` | Invitado vigente registra texto append-only con extractos concedidos. No edita manuscrito ni crea membresía de proyecto. |
| `GET /projects/{project_id}/ai-jobs/{job_id}` | Path UUID | Consulta estado seguro, resultado y errores del trabajo de IA. |
| `GET /projects/{project_id}/ai-jobs/{job_id}/document-diff` | Path UUID | Para P05/P29, prepara un `REPLACE_DOCUMENT` con contenido anterior/propuesto, `expected_document_version` y hash; no persiste cambios. Solo titular y job exitoso pendiente con contexto vigente. |
| `POST /projects/{project_id}/ai-jobs/{job_id}/cancel` | Path UUID | Cancela job en cola (`QUEUED`). |
| `POST /projects/{project_id}/ai-jobs/{job_id}/accept` | `{expected_state_version, decision_key, expected_document_version?, proposal_sha256?}` | Acepta la salida guardada. P05/P29 requieren los dos últimos campos de la vista previa y, en una transacción, crean `ChapterRevision` y reemplazan el documento canónico con `ChapterDocumentRevision` origen `AI_PROPOSAL`; otros pasos usan el flujo previo y `USR_...` persiste ejecución estructurada. No acepta contenido alternativo del cliente. |
| `POST /projects/{project_id}/ai-jobs/{job_id}/reject` | `{decision_key, reason?}` | Rechaza la propuesta sin alterar el manuscrito canónico ni el perfil. |

Esta tabla registra firmas HTTP declaradas, no sustituye el código para inferir permisos detallados o semántica del servicio. La [matriz de cuentas y permisos](./matriz_permisos_y_cuentas_backend.md) declara estado actual/objetivo. B3.5 liga importaciones y selecciones a ejecuciones mediante `SearchExecutionSource`; B3.6 conserva decisiones humanas append-only sobre posibles duplicados. Ninguna de estas funciones acredita autenticidad de una exportación o verifica metadatos remitidos por el cliente. B6.4 incorpora invitaciones limitadas a una tarea/recursos; registro de cuentas, verificación de correo, envío de email y recuperación de contraseña siguen pendientes. B8.1–B8.4 implementan carga versionada, recetas tabulares, figuras PNG y congelamiento de tablas/figuras en snapshot y DOCX aprobado; B8 pasó la puerta integral 7/7 (479.66 s; pytest 457.26 s; exit code 0) el 26/10/2026. La integración de biblioteca Zotero de solo lectura está implementada; requiere credenciales y registro OAuth externo para prueba en vivo. Las ejecuciones IA B5.1 y el adaptador Gemini están implementados; la llamada real queda pendiente de credenciales, según [el paquete de implementación](./implementacion_adaptador_gemini_b5_1.md).

## Respuestas actuales representativas

Las siguientes formas se observaron en los servicios. Los campos internos pueden evolucionar con una versión del contrato; se anotan aquí para que el agente compare el comportamiento al generar OpenAPI.

- **Estado de proyecto:** `project_id`, `name`, `title`, `status`, `idea_provisional`, `problem_statement`, `ods_code`, `unit_of_analysis`, `place`, `period_text`, `approach`, `consistency_matrix[]`, `variables[]`, `instruments[]`, `state_version`.
- **Guardado de paso:** `revision_id`, `revision_no`, `chapter_no`, `step_code`, `content_md`, `content_sha256`, `created_at`, `state_version`, `idempotent`.
- **Capítulo:** `chapter_no`, `status`, `latest_revision` (o null), `approved_revision_id` (o null), `steps[]` con `step_code`, `status`, `output_json`.
- **Documento de capítulo:** `chapter_no`, `document_version`, `revision_id`, `revision_no`, `schema_version`, `content_tree`, `content_md`, `content_sha256`, `state_version`, `is_legacy_projection`, `is_stale`. `PUT` devuelve además `idempotent`.
- **Trabajo documental:** `job_id`, `project_id`, `source_id`/`manuscript_id`, `kind`, `status`, `attempts`, timestamps, `result`, `error_code`, `error_message`. Los estados físicos actuales son `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`; no existe `CANCELLED` en el enum documentado.
- **Vista previa de aplicación de IA (P05/P29):** `job_id`, `task_id`, `chapter_no`, `operation`, `expected_state_version`, `expected_document_version`, `before_tree`, `before_content_md`, `after_tree`, `after_content_md`, `operations[]`, `source_output_sha256`, `proposal_sha256`. El hash cubre el contenido serializado devuelto salvo el propio hash; la aceptación lo recalcula en servidor.
- **Error de dominio actual:** `{"detail":"CODE: mensaje"}` con status HTTP mapeado por `backend/config/api.py`. El objeto `error{...}` mostrado antes en este documento es una propuesta de evolución, no la respuesta vigente.

B4 define contratos para citas estructuradas, vista IEEE, evidencia humana, sustitución y Zotero; sus detalles están en [implementación B4](./implementacion_b4_citas_ieee_zotero.md). El render IEEE es preliminar y el OAuth real está condicionado a credenciales. B8.1 define datasets CSV/XLSX inmutables y B8.2 recetas/tablas declarativas; B8.3 figuras y B8.4 integración al documento/exportación todavía requieren contratos. Al ampliar contratos, generar OpenAPI, guardar ejemplos y añadir pruebas de contrato.

## Deltas de contrato requeridos

1. Formalizar respuestas del proyecto con esquemas en lugar de `dict` abierto y paginar listas crecientes.
2. Añadir `expected_version` a operaciones mutables de agregado que aún no lo reciban (por ejemplo, decisiones de revisión si la inspección confirma que no tienen control equivalente).
3. Distinguir IDs de `ChapterRevision` por paso, `ChapterDocumentRevision` canónica y `ChapterSnapshot`; no reutilizar nombres entre esas identidades.
4. Exponer errores por `code`, `message`, `retryable` y versión vigente de forma compatible con consumidores.
5. Definir límites para `limit`, offsets, cuerpos, archivo, consultas y frecuencia; documentar valores vigentes y defaults configurables.
6. Usar `202 Accepted` solo si se creó o recuperó un job pendiente; retornar el mismo job en solicitudes concurrentes idempotentes.
7. Los nuevos endpoints de autenticación/invitación deben tener rate limits y respuestas que no revelen existencia de cuentas.

## Principios de contrato

- Mantener `/api/v1/` para el contrato vigente hasta que exista una migración/versionado explícito.
- Adaptadores traducen HTTP/MCP; validaciones, autorización y transacciones viven en servicios.
- Esquemas request/response son explícitos y estrictos. No aceptar campos extra silenciosamente en mutaciones sensibles.
- Errores tienen `code` estable, mensaje legible en español, datos recuperables seguros y `current_version` si es conflicto. La API vigente puede tener respuestas más simples: evolucionar con compatibilidad comprobada.
- Paginación en colecciones; filtros/orden solo si están documentados. Tareas lentas retornan `202` y un identificador consultable.
- Las escrituras incluyen expected version cuando cambian un agregado compartido. Las operaciones repetibles usan idempotency key y almacenan resultado suficiente para reconocer una repetición igual.
- No se devuelve secreto de proveedor, token MCP completo, ruta arbitraria del filesystem ni datos de otro proyecto.

## Matriz de operaciones HTTP objetivo

Los nombres a continuación son **grupos lógicos**, no endpoints ya aprobados. El agente debe comparar cada uno con las rutas reales antes de añadir una.

| Grupo lógico | Operaciones | Actor típico | Resultado |
|---|---|---|---|
| Proyectos | crear, listar propios, obtener, editar configuración | Tesista / participante autorizado | Proyecto y versión/configuración. |
| Tema y perfil | explorar candidatos, guardar elección/delimitación, recuperar alternativa | Tesista | Lista con criterios y procedencia; versión del perfil. |
| Metodología | obtener versión asignada, preparar paso, guardar borrador, proponer cambio, validar/publicar versión | Tesista; editor metodológico autorizado | Contexto/versiones; propuesta diff; versión inmutable publicada solo tras aprobación. |
| Capítulos | consultar progreso/snapshot, crear snapshot, enviar, reabrir/exportar | Tesista/asesor según acción | Estado, snapshot/version, bloqueos y eventos. |
| Revisión | comentar, listar/resolver comentarios, solicitar cambios, aprobar/reabrir | Asesor/tesista según operación | Comentario/evento ligado a revisión exacta. |
| Fuentes | buscar proveedor, importar RIS/BibTeX/CSV, cargar archivo, listar, obtener extractos, verificar metadatos/evidencia | Tesista y servicios | Registro con procedencia/nivel y trabajo si asíncrono. |
| Búsqueda licenciada manual | preparar/editar ecuación, guardar protocolo, abrir Scopus/WoS, importar exportación | Tesista; asesor/bibliotecario invitado al compartir | Consulta reproducible y resultados importados sin requerir API ni afirmar ejecución automática del proveedor. |
| Biblioteca documental | procesar, listar, preguntar al corpus, localizar pasaje/página, consultar estado de extracción | Participante autorizado del proyecto | Respuesta ligada a documentos/versiones y citas navegables; si no hay evidencia suficiente, estado explícito. |
| Auditoría afirmación–cita | seleccionar afirmación/cita, evaluar relación, recuperar pasajes, buscar candidatas, aceptar/rechazar diff | Tesista; asesor revisa según flujo del capítulo | Estado preliminar y evidencia; nunca muta el manuscrito hasta aceptación explícita. |
| Apoyos invitados | invitar, aceptar, consultar paquete compartido, responder, revocar | Tesista/asesor autorizado; invitado limitado | Solo tarea/recursos concedidos; respuesta no equivale a edición o aprobación. |
| Zotero | iniciar autorización, consultar conexión, seleccionar colección, sincronizar, revocar | Usuario titular del vínculo | Estado y elementos sincronizados sin exponer token. |
| IA/agentes | crear ejecución, consultar, cancelar, aceptar/rechazar propuesta | Tesista o asesor según contexto | Job, output tipado y estado de aceptación. |
| Datos/figuras | **B8.1/B8.2:** cargar/listar versiones; crear y versionar recetas de selección, filtro, orden y límite; consultar tabla, historial y hashes. Figuras y vínculo con documento/exportación permanecen en B8.3/B8.4. | Titular para datasets/recetas; participantes activos para lectura | Receta limitada a campos permitidos, sin código libre ni inferencia estadística. Se registran entrada, especificación, motor y salida con hashes. Ver [paquete B8](./paquete_b8_datos_figuras.md). |
| Exportaciones | solicitar DOCX/PDF/LaTeX según soporte, consultar job y descargar artefacto | Titular/actor con permiso | Archivo congelado ligado a snapshot y plantilla. |

Los flujos detallados de búsqueda asistida, lectura de documentos, auditoría afirmación–cita y apoyos con acceso acotado están en la [especificación de búsqueda, lectura documental y revisión de afirmaciones](./especificacion_busqueda_y_revision_de_evidencia.md). Estos grupos lógicos no implican rutas implementadas.

**Generación IA B5.1 (rutas verificadas en el router):** `POST /api/v1/projects/{project_id}/workflow/tasks/{task_id}/generate`, `GET /api/v1/projects/{project_id}/ai-jobs/{job_id}`, y `POST` a las rutas hermanas `/cancel`, `/accept` y `/reject`. La creación encola por defecto y devuelve un job; la generación síncrona solo existe como opción de configuración para desarrollo. El adaptador Gemini está implementado; el proveedor predeterminado sigue deshabilitado y la llamada real no se verificó por falta de credenciales. Aceptar usa únicamente la salida validada guardada en el job; el cliente no puede enviar texto alternativo. En P05/P29, el campo contractual `contenido_markdown` se convierte en el texto de la revisión; otras salidas siguen siendo estructuradas y no se infieren como prosa. El editor enriquecido canónico continúa pendiente.

## Esquema conceptual de error

El formato preciso queda sujeto a compatibilidad con clientes existentes. La intención semántica mínima:

```json
{
  "error": {
    "code": "VERSION_CONFLICT",
    "message": "El proyecto cambió desde que abriste esta versión.",
    "current_version": 18,
    "retryable": true
  }
}
```

No filtrar SQL, stack trace, secretos ni contenido de proyectos ajenos. Los códigos existentes documentados incluyen errores de esquema, prerrequisito, versión, fuente no verificada y desajuste de consistencia; confirmar el código real antes de renombrarlos.

## Operaciones asíncronas

OCR, extracción, GROBID, indexación, búsquedas amplias en fuentes que permiten ese acceso, consultas extensas al corpus, auditoría de capítulos/citas, sincronización de biblioteca, generación larga y exportaciones pueden ser trabajos asíncronos. Preparar una ecuación o abrir el sitio de una base puede ser inmediato; la búsqueda manual licenciada y la importación del archivo son acciones explícitas del usuario. El patrón deberá exponer:

- `job_id`, tipo y estado (`QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED` o equivalentes compatibles con el código actual).
- progreso sin datos sensibles, timestamps y error recuperable.
- actor/proyecto y versión de contexto asociados.
- deduplicación/idempotencia cuando repetir cree trabajo/costo.
- cancelación segura y reintento definido por tipo; no reintentar automáticamente cambios externos no idempotentes.
- autorización en consulta, descarga y cancelación.

No renombrar estados existentes sin revisar `DocumentJob`, migraciones y clientes. La máquina exacta debe derivarse del enum real.

## Coherencia con MCP

Cada herramienta MCP debe ser una fachada tipada sobre un caso de uso compartido, con identidad del token validada por servidor. No añadir un segundo motor de reglas en `mcp_server/`. La salida MCP puede ser más concisa, pero debe conservar códigos de error, IDs, versiones y nivel de evidencia suficientes para que el cliente actúe correctamente.

## Compatibilidad y aceptación

Antes de modificar un endpoint: registrar método/ruta/esquema actual, consumidores (frontend, pruebas, MCP indirecto), transición de compatibilidad y ejemplo viejo/nuevo. La aceptación requiere comprobar autenticación, aislamiento de proyecto, errores, conflicto concurrente, idempotencia y serialización. La documentación del `backend/README.md` se actualiza en el mismo cambio.
