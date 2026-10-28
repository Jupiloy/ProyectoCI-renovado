# Guía de continuidad del backend


**Alcance del prototipo acordado:** detener el recorrido antes de elaborar y aplicar instrumentos. P30–P32 no son obligatorios para la demostración; P26/P27 mencionan instrumentos previstos y deben decidirse en el recorrido concreto. Conservar pasos disponibles y recorridos editables, sin afirmar que se completa toda la tesis. IEEE es el estilo priorizado para el piloto; APA 7 sigue admitido por compatibilidad histórica. La web usará sesión Django; `GET /api/v1/auth/session/`, `POST /api/v1/auth/login/` y `POST /api/v1/auth/logout/` son los endpoints locales añadidos. El inicio requiere CSRF; no hay alta pública, recuperación ni CORS entre orígenes.
**Estado operativo local tras la reparación:** la base `tesismcp` de `tesismcp-local-pg` recibió las migraciones `0024`–`0044`, después de un respaldo conjunto DB+media y un ensayo de restauración/migración aislado. El desfase hasta `0023` fue el hallazgo inicial; las puertas históricas 7/7 no verificaban migraciones aplicadas. El verificador incorpora ahora ese control separado. Consultar el [registro B10](./paquete_b10_operacion_local_y_despliegue.md) para evidencia, comandos y límites; no confundir esta reparación local con el cierre de B10 o del producto.

**Actualizada:** 27/10/2026  
**Propósito:** que el equipo y el siguiente agente sepan qué está realmente implementado, cuál fue el último avance y qué hacer después sin repetir bloques.  
**Fuente de verdad:** código y migraciones vigentes; este documento resume su estado para navegación. B3.1–B3.6, B4.1–B4.5, B6.1–B6.4, B7 y B8.1–B8.4 están verificados. B8 pasó puerta integral 7/7, total 479.66 s, pytest 457.26 s, exit code 0 el 26/10/2026. B9 se evaluó: búsqueda asistida manual vigente; conectores Scopus/WoS API condicionados a autorización y caso de uso, sin implementación activa. B10 sigue parcial: existe respaldo conjunto manual DB+media, restauración aislada probada y actualización de la base activa hasta `0044`. Quedan programación/frecuencia/retención, copia independiente y configuración de despliegue; ver el registro B10. OAuth real Zotero requiere credenciales externas no disponibles.

**Cierre de reparación operativa local:** puerta 8/8, 214 pruebas aprobadas y exit code 0 (508.47 s de gate; 535.29 s con build/arranque). El [registro B10](./paquete_b10_operacion_local_y_despliegue.md) contiene respaldo, restauración, migraciones, evidencia y pendientes. B10 completo permanece abierto.

**Organización del código:** la API agrupa operaciones en `backend/thesis/api/routes_*.py` y contratos en `schemas.py`; `projects.py` conserva la fachada y el orden de registro. Se extrajeron funciones de presentación de capítulos, recorridos, trabajos IA y fuentes a módulos `*_serialization.py`; las funciones anteriores siguen disponibles en los servicios de origen. Esta reorganización no altera por sí sola funcionalidades, persistencia ni rendimiento. Las consultas de capítulos están en `chapter_queries.py`, el envío transaccional íntegro en `chapter_submission.py`, el contexto de IA en `ai_job_context.py` y las decisiones de propuestas en `ai_proposal_decisions.py`; `steps.py` y `ai_jobs.py` conservan sus nombres públicos anteriores. El guardado de pasos, el cuerpo del envío y los borradores de recorridos todavía contienen funciones extensas; dividirlas internamente requiere verificar sus transacciones y concurrencia, no solo mover líneas. La validación y la ejecución de tareas personalizadas se encuentran respectivamente en `workflow_validation.py` y `workflow_execution.py`, reexportadas desde `workflows.py`; sus funciones y transacciones conservan el comportamiento anterior.

## Sesión web y configuración IA añadidas en este corte

`backend/config/auth_views.py` ofrece consulta de sesión, inicio y cierre de sesión con autenticación Django por correo y cookie de sesión. El cliente solicita primero CSRF en `GET /api/v1/auth/session/`; para iniciar/cerrar envía el token en `X-CSRFToken` y conserva cookies. No se añadió registro público, recuperación de contraseña ni CORS; la futura web debe usar mismo origen/proxy en desarrollo. El modelo acordado para el recorrido normal es BYOA: el cliente del usuario ejecuta la IA y llama al servidor MCP; el backend determinista valida y persiste. El código B5.1 mantiene aparte una vía opcional de jobs que llama desde servidor a Gemini y está deshabilitada por defecto; su credencial/llamada real no se verificó. Compose conserva su configuración explícita para `ai_worker`, pero no inyecta la clave en `web` por defecto ni la requiere para BYOA. Estas modificaciones están pendientes de verificación automatizada por decisión del usuario; reunirlas con las correcciones siguientes para la próxima puerta integral.

## 1. En qué punto estamos

El backend ya tiene una base amplia: Django + Django Ninja + PostgreSQL/pgvector; P01–P32; recorridos editables/versionados; jobs de IA y worker; documentos canónicos por capítulo; revisión/aprobación por snapshot y exportación DOCX congelada. B3.1–B3.6 cubren importaciones manuales, búsqueda abierta/peruana, estrategias versionadas, selección y procedencia de candidatos, y decisiones humanas sobre posibles duplicados.

**Último corte integral verificado B8:** 58 modelos y 44 migraciones (`0001`–`0044`); 32 pasos, 34 herramientas MCP y 35 prompts. La puerta pasó 7/7 el 26/10/2026 (479.66 s; pytest 457.26 s; exit code 0).

## 2. Bloques ya cubiertos

| Bloque | Resultado actual | Límite que sigue vigente |
|---|---|---|
| B1.1 | `ChapterSnapshot` inmutable, manifest/procedencia, consulta autorizada y envío transaccional. | No congela automáticamente evidencia que no está en el manifest implementado. |
| B1.2 | Comentarios, decisiones y aprobaciones nuevas ancladas al snapshot; historial legado preservado. | Los comentarios usan offsets Unicode sobre `content_md`, todavía no IDs/anclas estables del editor por bloque. |
| B1.3 | DOCX separado para el snapshot actualmente aprobado. | No es certificación UTP, no prueba citas ni mantiene campos Zotero vivos. |
| B1+B2.1/B2.2 | Texto P05/P29 materializado y documento canónico por capítulo con árbol JSON versionado. | Ida/vuelta real con el frontend no se ha probado; tablas/figuras no forman parte del árbol v1; B4 sí añade marcas de cita estructuradas. |
| B1+B2.3 | Preview `REPLACE_DOCUMENT` y aceptación explícita de P05/P29 usando versión/hash; solo esas salidas se aplican al documento. | No verificar verdad académica/citas. Otros pasos y `USR_...` no se aplican al árbol. |
| B5/B5.1 | Recorridos/prompts configurables, tareas `USR_...`, trabajos de generación, aceptación/rechazo, worker y adaptador Gemini. | No hay llamada Gemini real comprobada; requiere credencial de servidor. |
| B6.1 | Lotes de trabajos IA con consulta agregada y cancelación de trabajos aún `QUEUED`. | Cada salida sigue siendo propuesta independiente; no incluye síntesis ni escritura al documento. |
| B6.2 | Reclamo atómico, concurrencia por hilos dentro de un solo proceso con límite configurable y recuperación conservadora de jobs abandonados. | Verificado por puerta integral 7/7; el gasto monetario no queda limitado por este control. B6.3/B6.4 se implementan en este corte. |
| B6.3 | Síntesis de 2–8 outputs `SUCCEEDED` del mismo lote; snapshot/hash, referencias a `task_id`, validación estricta, decisión auxiliar del titular y worker B6 compartido. | Implementado y verificado por puerta integral 7/7; no se incorpora a capítulos ni convierte outputs en aprobaciones. Ver [paquete B6.3](./paquete_b6_3_sintesis_trazable.md). |
| B6.4 | Invitaciones temporales a cuentas activas para tarea y fuentes específicas; respuesta textual append-only y descarga solo de PDFs compartidos con SHA verificado. | Implementado y verificado por puerta integral 7/7; no hay envío de correo, alta de cuenta, carga invitada, acceso global ni aprobación. Ver [paquete B6.4](./paquete_b6_4_invitaciones_apoyo.md). |
| B7 | Carga PDF/DOCX/PPTX/XLSX; `SourceSegment` y localizadores nativos; búsqueda junto a pasajes PDF; detección/OCR selectivo de páginas PDF sin texto digital; benchmark local ejecutado. | Implementado y verificado por puerta integral 7/7 (381.76 s, exit code 0). No incluye OCR de imágenes Office ni recálculo XLSX. Benchmark disponible: 9 PDF/971 páginas, no representativo, sin medir precisión OCR. Ver [paquete B7](./paquete_b7_multiformato.md). |
| B8.1 | Ingesta CSV UTF-8/XLSX, historial de originales/hash, esquema observado, acceso autenticado, idempotencia y descarga verificada. | Implementado y verificado; puerta 7/7, 383.36 s, exit code 0; pruebas focales 8/8. El alcance B8.1 no transforma valores; las recetas tabulares se documentan por separado en B8.2. Ver [paquete B8](./paquete_b8_datos_figuras.md). |
| B8.2 | Recetas declarativas versionadas, proyección/filtros/orden/límite, salida tabular con hash de entrada/spec/resultado; sin código libre ni análisis inferencial. | Implementado y verificado; puerta 7/7, 432.35 s, exit code 0. No inserta ni congela tablas en el manuscrito. Ver paquete B8. |
| B8.3 | Figuras BAR/LINE/SCATTER PNG desde tabla exacta; hashes, versión de renderer, texto alternativo, preview verificado, control de truncamiento e inmutabilidad. | Implementado y verificado por puerta integral 7/7. No admite inferencia, fechas, multi-series ni validez científica automática. |
| B8.4 | Bloques v2 de tabla/figura, comprobación de proyecto/hash al guardar, manifest incluido en el hash del snapshot y render DOCX aprobado desde versiones inmutables. | Implementado y verificado por puerta integral 7/7. El borrador general conserva su contrato; no hay exportación PDF. Ver [paquete B8](./paquete_b8_datos_figuras.md). |
| B4.1–B4.5 | Citas canónicas, manifest congelado, IEEE preliminar, evidencia y revisión humana, reemplazo con decisión, OAuth Zotero de solo lectura. | Ver [detalle B4](./implementacion_b4_citas_ieee_zotero.md). Falta configuración y prueba OAuth real; formato IEEE completo por tipo; no hay juicio automático de pertinencia. P20 admite IEEE y conserva APA 7 por compatibilidad; los recorridos publicados no se reescriben. |
| B3.1 | `SourceDocument` identifica proveedor y registro; conserva el hash del archivo de importación, actor, resumen y publicación/revista; no almacena el original RIS/BibTeX/CSV. Migración `0027` mantiene los registros previos. | Las fuentes candidatas enviadas por el cliente no son comprobadas de nuevo contra el proveedor. |
| B3.2 | Importación manual de RIS, BibTeX y CSV; `SCOPUS`, `WOS` u `OTHER`; idempotencia y posibles duplicados por DOI/título. | Los metadatos entran como no verificados; no se descargan PDFs ni se fusionan duplicados automáticamente. |
| B3.3 | Búsqueda peruana ALICIA/artículos expuesta en HTTP con clasificación y nivel `METADATA_ONLY`. | El dato presentado al endpoint de selección no se reconsulta ni valida automáticamente. |
| B3.4 | `SearchStrategy` crea series versionadas e inmutables; `SearchExecution` registra declaración manual, versión, actor, fecha, cantidad opcional y notas. Owner escribe; miembros leen; URL HTTPS y dominios Scopus/WoS validados. | No hay ejecución automática de bases licenciadas, prueba del acceso, adjunto de exportación ni enlace automático entre importación bibliográfica y ejecución. |
| B3.5 | Endpoint de selección de candidatos con `metadata_origin` y estado `UNVERIFIED_METADATA`, reporte de posibles duplicados y enlace inmutable fuente–ejecución. Las importaciones pueden ligarse a `execution_id`; cada relación conserva hash de archivo. Puerta integral aprobada 7/7. | Datos del candidato y ejecución son declaraciones del usuario; no se verifica autenticidad del archivo, precisión del registro ni correspondencia de la búsqueda. |
| B3.6 | Decisiones humanas inmutables/versionadas por par; registra si el indicio fue DOI, título normalizado o ambos, permite confirmar duplicidad, mantener registros separados o elegir explícitamente `primary_source_id`; historial consultable. | La coincidencia por DOI/título solo es sugerencia. No se eliminan ni fusionan fuentes, no se transfieren citas y la selección principal no certifica validez bibliográfica. |

## 3. Rutas HTTP incorporadas en este avance

- `GET /api/v1/projects/{project_id}/discovery/peru?query=...&scope_filter=todos&include_articles=true&limit=5`: ejecuta el servicio peruano actual. Requiere sesión y pertenencia al proyecto. Devuelve metadatos; no es una lectura de texto completo.
- `POST /api/v1/projects/{project_id}/sources/import-bibliography`: `multipart/form-data` con `provider` (`SCOPUS`, `WOS` o `OTHER`) y `file` con extensión `.ris`, `.bib`, `.bibtex` o `.csv`. Solo el titular importa. Límite del archivo: 5 MiB y máximo 500 registros. El título es obligatorio por registro; CSV exige encabezado `title`/`titulo` y acepta columnas reconocidas de autores, año, DOI, URL, abstract/resumen y revista.
- `POST /api/v1/projects/{project_id}/search-strategies`: crea versión inicial. Campos: `provider`, `title`, `topic`, `query_text`, `search_equation`, `concepts`, `filters`, `search_url`, `idempotency_key`. Solo el titular escribe; URL opcional HTTPS, con dominio oficial exigido si el proveedor es Scopus o WoS.
- `GET /api/v1/projects/{project_id}/search-strategies`: lista versiones actuales de cada serie para miembros autorizados.
- `GET /api/v1/projects/{project_id}/search-strategies/{strategy_id}`: devuelve todas las versiones de la serie indicada.
- `POST /api/v1/projects/{project_id}/search-strategies/{strategy_id}/revisions`: crea revisión inmutable; requiere `expected_version` y `idempotency_key`.
- `POST /api/v1/projects/{project_id}/search-strategies/{strategy_id}/executions/manual`: registra una declaración manual asociada a esa versión. Guarda fecha declarada, actor, cantidad opcional y notas. La respuesta se etiqueta `MANUAL_USER_DECLARED`; no prueba que el usuario efectivamente entró a la base.
- `GET /api/v1/projects/{project_id}/search-strategies/{strategy_id}/executions`: lista las declaraciones registradas para esa versión.
- `GET /api/v1/projects/{project_id}/search-strategies/{strategy_id}/executions/{execution_id}/sources`: lista las fuentes enlazadas, tipo de vínculo, hash de archivo si aplica, actor y procedencia de metadatos.
- `POST /api/v1/projects/{project_id}/sources/select-discovery`: titular guarda proveedor, ID de registro, título, autores y metadatos opcionales recibidos del cliente. Proveedores admitidos: OpenAlex, Semantic Scholar y ALICIA. No reconsulta el proveedor, no descarga archivos y etiqueta el resultado `USER_SUPPLIED_METADATA_UNVERIFIED`; informa posibles duplicados sin fusionarlos. `search_execution_id` es opcional y debe corresponder al mismo proyecto.
- `POST /api/v1/projects/{project_id}/sources/import-bibliography` admite `execution_id` multipart opcional. Si se proporciona, cada fuente importada se relaciona con la ejecución y con la huella SHA-256 del archivo.
- `POST /api/v1/projects/{project_id}/sources/duplicate-decisions`: titular registra una decisión inmutable del par; `SET_PRIMARY` requiere el `primary_source_id` exacto. No borra ni fusiona fuentes.
- `GET /api/v1/projects/{project_id}/sources/duplicate-decisions`: participantes autorizados consultan el historial con `is_current` por par.
- La respuesta registra `file_sha256`, registros creados/repetidos, proveedor y `possible_duplicates`. Repetir exactamente archivo/proveedor no crea duplicados nuevos. Igual DOI o título produce candidatos relacionados y ambos registros permanecen disponibles.

**Importante:** importar una exportación de Scopus/WoS no implica que TesisMCP accedió, buscó o descargó desde esa base. El usuario ejecuta la búsqueda por sus medios y carga su exportación. La importación no comprueba portada, revisión por pares, texto completo o pertinencia.

## 4. Cambios físicos de B3.1–B3.3 (corte ya verificado)

- `backend/thesis/models/sources.py`: `RecordProvider`, `provider_record_id`, `imported_file_sha256`, `imported_by`, `abstract`, `publication_venue` y restricción de identidad por proyecto/proveedor/registro.
- `backend/thesis/migrations/0027_remove_sourcedocument_source_kind_payload_and_more.py`: aditiva; rellena las identidades OpenAlex existentes y deja los PDF cargados por el usuario sin proveedor bibliográfico.
- `backend/thesis/integrations/bibliography_import.py`: parseo acotado RIS/BibTeX/CSV.
- `backend/thesis/services/bibliography.py`: permisos, límites, persistencia, idempotencia y detección de candidatos duplicados.
- `backend/thesis/api/projects.py`: rutas HTTP de importación y búsqueda peruana.
- `backend/thesis/services/sources.py`: representación de origen y metadatos por proveedor.
- `backend/thesis/tests/test_bibliography_import.py`: pruebas de parser, importación, permisos y HTTP.

## 5. Cambios físicos de B3.4–B3.6

- `backend/thesis/models/searches.py`: modelos `SearchStrategy` y `SearchExecution`; inmutabilidad exigida en PostgreSQL.
- `backend/thesis/migrations/0028_searchstrategy_searchexecution_and_more.py`: crea tablas, constraints, índices y triggers append-only.
- `backend/thesis/services/search_strategies.py`: normalización, hash, validación de proveedor/URL/límites, control de acceso, versionado, control optimista, idempotencia y registro/listado de ejecuciones manuales.
- `backend/thesis/api/projects.py`: seis rutas HTTP indicadas arriba.
- `backend/thesis/tests/test_search_strategies.py`: casos de versionado, conflictos, idempotencia, ejecución manual, inmutabilidad, URL, permisos y API.
- `backend/thesis/models/sources.py`: `SourceDocument.metadata_origin` distingue `PROVIDER_API`, `USER_FILE_IMPORT`, `USER_SELECTED_CANDIDATE` y `USER_UPLOADED_FILE`; la migración rellena la procedencia legada.
- `backend/thesis/models/searches.py`: `SearchExecutionSource` relaciona fuente, ejecución, tipo de vínculo, actor, fecha y hash de importación. La base impide modificar o borrar el vínculo.
- `backend/thesis/migrations/0029_sourcedocument_metadata_origin_searchexecutionsource.py`: campo, nuevo estado `UNVERIFIED_METADATA`, relación, constraints, índice, backfill de procedencia, trigger append-only y guardia PostgreSQL contra vínculos entre proyectos.
- `backend/thesis/services/discovery_sources.py`: validación y registro de candidatos enviados por cliente; URLs solo HTTPS; niveles no verificados; enlace opcional a ejecución.
- `backend/thesis/services/source_duplicates.py`: detección compartida por DOI/título para candidatos y archivos importados; no fusiona.
- `backend/thesis/services/bibliography.py`: acepta ejecución opcional y liga cada registro importado con la huella del archivo.
- Pruebas de selección, permisos, importación/enlace, idempotencia, posibles duplicados, separación entre proyectos y triggers en `test_discovery_sources.py` y `test_bibliography_import.py`.
- `backend/thesis/models/source_duplicates.py`, `services/source_duplicate_decisions.py`, `migrations/0030_source_duplicate_decisions.py` y `api/projects.py`: decisiones inmutables y versionadas por par; ordenamiento canónico de IDs, idempotencia, validación de mismo proyecto y tipo EXTERNAL, y comprobación de DOI/título coincidente.
- `backend/thesis/tests/test_source_duplicate_decisions.py`: versión de historial/idempotencia, permisos, error de par no coincidente, rutas HTTP, trigger append-only y trigger PostgreSQL contra cruces entre proyectos.
- Conteos del corte histórico B3.6: 40 modelos/30 migraciones. El corte B4.5 llega a 45 modelos/35 migraciones; el verificador mantiene controles exactos.

## 6. Verificación

**Puerta B8.2 ejecutada:** `TESISMCP_DB_CONTAINER=tesismcp-local-pg ./scripts/verify_podman.sh` → código 0; 7/7 comprobaciones; duración 432.35 s; pytest completa 410.33 s. Veredicto `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]`. B8.1 pasó previamente en 383.36 s (pytest 364.62 s). B7 también pasó puerta (381.76 s; pytest 362.49 s); esa puerta no midió precisión OCR ni representatividad amplia del corpus.

**Corte B3.4:** `TESISMCP_DB_CONTAINER=tesismcp-verify-tmp ./scripts/verify_podman.sh` → código `0`; puerta `7/7`; duración total `234.41 s`. Evidencia por paso: Grounded `7.41 s`; Django `check` `3.48 s`; migraciones `3.49 s`; pytest completa `216.76 s`; higiene `0.45 s`; consistencia doc-código `2.83 s`; auditoría adversaria `0.00 s`. Veredicto `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]`.

**Corte anterior B3.1–B3.3:** `TESISMCP_DB_CONTAINER=tesismcp-verify-tmp ./scripts/verify_podman.sh` → código `0`; puerta `7/7`; tiempo total `315.00 s`. Esta evidencia antecede a B3.4 y no es la validación de sus cambios.

**B3.5:** puerta completa aprobada 7/7; duración 247.81 s; código 0. Este resultado es independiente del corte B3.4.

**B3.6:** implementación y prueba focalizada PostgreSQL (5 casos); B3 queda documentado como base previa a B4.

## 7. Siguiente bloque de trabajo

### Estado actual y siguiente paso

B6.1–B6.4 quedan cerrados por puerta integral 7/7 (395.34 s, exit code 0); B6.3 y B6.4 se implementaron en una entrega conjunta. La síntesis es un artefacto auxiliar trazable; las invitaciones son grants acotados a una tarea y fuentes. La lista completa está en [pendientes backend después de B4](./pendientes_backend_despues_b4.md) y el diseño conjunto en [B6 completo](./paquete_b6_completo.md).

### Después, antes de declarar backend listo para frontend

1. Completar contratos de fuentes/búsqueda y correr todos los recorridos web con PostgreSQL.
2. Probar B1/B2 con el editor frontend: cargar árbol, editar, guardar con versión/idempotencia, mostrar diff, aceptar, comentar y exportar el snapshot aprobado.
3. Añadir localizadores de comentario por ID de bloque manteniendo los offsets para comentarios históricos.
4. Configurar Zotero OAuth real y probar lectura/importación/revocación con cuenta de prueba; completar el render IEEE por tipo de fuente contra la guía aprobada; probar campos Zotero activos en Word/LibreOffice por separado solo si se proponen como función.
5. B8.1–B8.4 está cerrado y verificado; B7 está cerrado y una evaluación representativa de corpus sigue siendo mejora empírica. Los resultados posteriores a P32 y ramas cuantitativa/cualitativa/mixta son trabajo de dominio aparte, no el siguiente incremento automático.
6. B6 y B8 están cerrados. B9 se evaluó y queda condicionado: no implementar APIs licenciadas hasta contar con evidencia de entitlement, uso permitido y caso de uso; la ruta manual existente no se bloquea. El siguiente trabajo priorizado es el round-trip frontend de B1/B2 y las brechas del [plan de entregas](./plan_entregas_backend.md). Llamada Gemini real, correo y APIs licenciadas siguen siendo dependencias externas separadas. Ver [paquete B9](./paquete_b9_conectores_licenciados.md).

## 8. Archivos canónicos para orientarse

1. `AGENTS.md` — reglas y puerta de verificación.
2. `GUIA_AGENTE.md` — arquitectura y estado de alto nivel.
3. `docs/07_desarrollo_prototipo/estado_version_producto.md` — implementado frente a objetivo.
4. `docs/02_arquitectura_y_sistema/plan_entregas_backend.md` — orden y entregas.
5. `docs/02_arquitectura_y_sistema/criterio_backend_listo_para_frontend.md` — condición de salida del backend.
6. `docs/02_arquitectura_y_sistema/especificacion_busqueda_y_revision_de_evidencia.md` — alcance de fuentes y evidencia.
7. [Pendientes backend después de B4](./pendientes_backend_despues_b4.md) — brechas abiertas, prioridades y estado actual.
8. [Paquete B6 completo](./paquete_b6_completo.md) — contrato integral B6.1–B6.4 y límites.
9. [Paquete B9](./paquete_b9_conectores_licenciados.md) — decisión, requisitos de acceso, diseño condicionado y criterios para habilitar conectores licenciados.
10. [Paquete B10](./paquete_b10_operacion_local_y_despliegue.md) — desarrollo local, configuración futura por entorno, estado de backups y criterio de operación/despliegue.

Si dos documentos difieren, primero inspeccionar el modelo/servicio/ruta/migración/test actual. Corregir el documento de estado y no recrear un endpoint, modelo o flujo que ya exista.
