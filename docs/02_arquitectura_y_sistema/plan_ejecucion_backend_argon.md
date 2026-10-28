# Plan de ejecución verificable del backend TesisMCP

> **Actualización:** las referencias históricas a P20 solo APA describen un corte anterior. P20 ahora admite IEEE y APA_7; no se reescribieron recorridos publicados y falta comprobación completa del formato.

**Autor de esta auditoría:** Codex, en sustitución de Argon porque Argon no completó la tarea. **Fecha:** 25/10/2026. **Estado:** planificación basada en inspección del árbol local; no acredita implementación de las capacidades propuestas. El nombre del archivo se conserva para que el prompt de Flash lo encuentre sin cambios.

> **AVISO DE VIGENCIA:** el inventario original de este documento precede a B5 y es histórico. No iniciar de nuevo la configuración del workflow ni afirmar que solo existe un recorrido secuencial. El corte actual está en [estado_version_producto.md](../07_desarrollo_prototipo/estado_version_producto.md): tareas `USR_...`, `WorkflowTaskExecution`, B5.1 con jobs/worker/aceptación y migraciones `0021`–`0022`. El adaptador Gemini ya está implementado; el proveedor está deshabilitado por defecto y la llamada real sigue pendiente de credenciales. Antes de programar, leer la [guía backend completa](./guia_backend_version_completa_para_agentes.md), el [plan vigente](./plan_entregas_backend.md) y la [especificación de generación IA](./especificacion_generacion_ia_y_resultados.md), luego volver a inspeccionar el código real. No usar las filas antiguas de este plan como fuente de estado actual.

**Directriz de uso para Flash:** lee [AGENTS.md](../../AGENTS.md), [criterio de backend listo para frontend](./criterio_backend_listo_para_frontend.md) y [plan de entregas B0–B10](./plan_entregas_backend.md). Contrasta cada fila de esta auditoría con el código justo antes de tocarla. Una ruta propuesta no es un endpoint existente. Al añadir código, actualizar estado, pruebas, documentación y este plan con evidencia de la nueva versión. No detenerse al terminar B5.

## 1. Corte y método de verificación

Se inspeccionaron físicamente `backend/thesis/`, `backend/config/`, `mcp_server/`, las migraciones `0001`–`0018`, nombres y casos de pruebas en `backend/thesis/tests/`, y los documentos enlazados al final. La API efectiva se monta en `/api/v1/` por `backend/config/urls.py` y usa `backend/config/api.py`. Este plan distingue:

- **IMPLEMENTADO:** símbolo y comportamiento observados en el código; no implica cumplir el objetivo completo.
- **PARCIAL:** existe un componente, pero no el recorrido integral exigido.
- **PENDIENTE:** no se observó modelo/servicio/API que cumpla el caso.
- **DEPENDIENTE_DE_PERMISO:** conector sujeto a acceso/licencia/proveedor; el modo manual no queda bloqueado.
- **DECISIÓN_ABIERTA:** política académica, UX o contrato pendiente de validar; construir la infraestructura reversible donde sea posible.

No se evaluó aquí que un resultado IA sea científicamente correcto. Las pruebas actuales verifican comportamiento de software; los ejemplos de la demo no son resultados empíricos de una tesis del usuario. La [suite obligatoria](../../scripts/verify_project.py) se ejecuta al cerrar este cambio documental y su resultado debe acompañar la entrega.

## 2. Inventario código → requisito

| Dominio | Evidencia física observada | Estado frente al objetivo | Brecha para Flash y riesgo principal |
|---|---|---|---|
| Identidad y proyectos | `models/accounts.py::User`, `McpAccessToken`; `models/projects.py::Project`, `ProjectParticipant`; `services/access.py::require_project`; `services/projects.py::create_project/get_project_state/register_idea`; `api/projects.py` crea/consulta proyecto. | PARCIAL | Owner/advisor existen; falta superficie web completa de cuenta/proyecto y perfil normativo versionado. `ProjectParticipant` admite un OWNER y un ADVISOR activos; asesoría temática/metodológica es función, no dos personas obligatorias. Preservar permisos y datos previos. |
| Exploración de ideas | `services/projects.py::register_idea` guarda `ResearchProfile.topic`; `services/exploration.py::explore_idea`; `services/step_contracts.py::P01Output` exige 5–10 temas y P02 exactamente tres. | PARCIAL | No hay entidad persistente para todas las ideas, derivaciones/descartes y criterios. Cambiar solo límites Pydantic sin persistir alternativas no cumple producto. |
| P01–P32 y método | `step_catalogue.py`; `services/step_contracts.py::CONTRACTS`; `services/steps.py::save_step/submit_chapter`; `models/chapters.py::StepProgress`, `ChapterRevision`; tests `test_academic_flow.py`, `test_extended_steps.py`, `extended_steps/`. | PARCIAL | `save_step` exige P inmediato anterior; `submit_chapter` exige todos los P del capítulo. No existe catálogo/recorrido/prompt versionado por proyecto ni tareas personalizadas ejecutables. Migrar con compatibilidad; no suponer que reordenar una lista elimina dependencias ocultas. |
| Prompts y MCP | `mcp_server/prompts/catalog.py` registra plantillas de `templates/` y roles; `mcp_server/django_bridge.py` resuelve actor; `mcp_server/project_tools.py` expone herramientas; `test_mcp_prompts.py` comprueba plantillas. | PARCIAL | Prompts estáticos en código, no edición/publicación por proyecto ni orquestación multiagente web. Mantener MCP como fachada de servicios, no duplicar reglas. |
| Investigación cuantitativa/cualitativa/mixta | `models/research.py::ResearchProfile.Approach`, `ResearchVariable`, `ConsistencyRow`; `models/instruments.py::Instrument/InstrumentItem`; materializadores `consistency.py` e `instruments.py`. | PARCIAL | P11 obliga hipótesis y VI/VD, P12 variables; P30 usa matriz, P31 entrevista, P32 recibe coeficiente declarado con umbral fijo. El enum de enfoque no demuestra rutas metodológicas completas. Necesita contratos por rama, datos piloto y cálculo reproducible. |
| Literatura y antecedentes | `services/discovery.py`, `discovery_peru.py`, `geography.py`; `integrations/openalex.py`, `semantic_scholar.py`, `alicia.py`, `crossref.py`; `services/sources.py`, `models/sources.py::SourceDocument`; `step_materializers/literature.py`; tests de descubrimiento/fuentes. | PARCIAL | Descubrimiento y PDFs existen, pero el registro `EXTERNAL` exige `openalex_id`; falta importación RIS/BibTeX/CSV de Scopus/WoS y procedencias múltiples, deduplicación revisable y búsqueda manual registrada. P16 está acoplado a P15 PRISMA; no presentar esa dependencia como universal. |
| Corpus y extracción | `SourceExcerpt`/`SourcePassage` con página física y pgvector; `services/search.py`, `sources.py`, `grobid.py`; `integrations/pdf.py`, `ocr.py`, `grobid.py`; `DocumentJob` y trabajador; `ManuscriptDocument` DOCX; tests de documentos/search/manuscritos. | PARCIAL | PDF/DOCX tienen rutas observadas; no hay pipeline homogéneo para PPTX/XLSX ni preguntas documentales con respuesta fundamentada de extremo a extremo. Extracción/OCR es dato, no verificación semántica de figura o cita. Preservar originales/localizadores. |
| Citas y apoyo a afirmación | `EvidenceLink` candidato/confirmado/rechazado; `services/evidence_links.py`, `evidence.py::locate_quote/check_source_doi`; `SourceMetadataCheck`; `services/search.py` devuelve candidatos con `supports_claim_verified=False`; `ManuscriptCitation` detecta campos DOCX. | PARCIAL | No hay ocurrencia de cita del editor enlazada a referencia+pasaje, numeración IEEE dinámica ni evaluación automática afirmación–cita con estados/diff. P20 acepta solo `APA_7`; `test_academic_flow.py::test_p20_only_accepts_apa_7` lo confirma. No inferir respaldo de un DOI o embedding. |
| Manuscrito, asesor y aprobación | `ChapterRevision` por guardado P, `Chapter` con estados y `approved_revision`, `ReviewComment`, `ReviewEvent`; `services/reviews.py` comenta/decide última revisión y bloquea aprobación si esa revisión tiene comentarios abiertos. | PARCIAL | `submit_chapter` envía la **última revisión por paso**, no snapshot completo del capítulo; aprobación/exportación no comparten objeto integral. Comentarios anclan índices Unicode del `content_md` de esa revisión. Rediseñar sin perder comentarios/aprobaciones legadas. |
| IA web y multiagentes | `AIGenerationJob`, worker, contexto/prompt versionados, validación, API, aceptación/rechazo y adaptador Gemini implementados; `DocumentJob` sigue siendo documental. | PARCIAL | La llamada real Gemini requiere credenciales y aún no se verificó. Multiagentes/lotes y capacidades amplias siguen pendientes. El siguiente bloque es B1.1: seguir el [paquete de implementación del snapshot](./paquete_b1_1_implementacion_snapshot.md); el [paquete Gemini B5.1](./implementacion_adaptador_gemini_b5_1.md) es histórico y no se debe repetir. |
| Datos de campo, análisis y resultados | `Instrument`/ítems versionados; P32 acepta `coeficiente_confiabilidad_obtenido` declarado; `Chapter.number` tiene check 1..7. | PENDIENTE para recorrido empírico | No se observaron datasets originales/versionados, protocolo de campo/consentimiento/dictamen, transformaciones, análisis cuantitativo/cualitativo/mixto o capítulos de resultados/discusión/conclusiones. No añadir prompts como sustituto de datos y cálculos. |
| Figuras y exportación | `services/exports.py::export_draft_docx` concatena último `ChapterRevision` por P; `api/projects.py` ofrece `export/draft.docx`; test de borrador en `test_academic_flow.py`. | PARCIAL | DOCX de borrador no está ligado a snapshot aprobado ni incluye pipeline de figura/tabla y cita IEEE; no se observó exportación PDF final. Evitar llamar “tesis lista” a ese archivo. |
| Seguridad y operación | `config/api.py` usa sesión Django (`django_auth`), `access.py` filtra proyecto, `McpAccessToken` guarda hash; `DocumentJob` persiste cola; `health/` comprueba DB; migraciones existentes. | PARCIAL | Faltan contratos web completos, permisos de invitados, configuración/retención de proveedor IA, backup/restauración demostrados y observabilidad para recorridos nuevos. No guardar credenciales UTP/Scopus/WoS en prompts. |

**Pruebas existentes que sirven de base, no de evidencia del destino completo:** `test_academic_flow.py` cubre guardado, bloqueo secuencial, revisión y DOCX de borrador; `extended_steps/` cubre contratos/materializadores P; `test_mcp_prompts.py` cubre el catálogo estático; `test_sources.py`, `test_document_jobs.py`, `test_grobid_search.py`, `test_manuscripts.py` cubren rutas documentales. Los nombres localizan pruebas; Flash debe inspeccionar cada caso antes de considerarlo suficiente.

## 3. Dependencias ocultas y decisiones metodológicas que bloquean cambios ingenuos

| Símbolo actual | Dependencia o restricción observada | Tratamiento requerido |
|---|---|---|
| `steps.py::save_step` | Comprueba el P previo de la secuencia lineal. | Para recorrido nuevo, evaluar grafo publicado y entradas; preservar modo legado mientras migra. |
| `steps.py::submit_chapter` | Compara completados con todos los códigos del capítulo. | Evaluar tareas activas/exigibles y snapshot completo; P opcional no debe bloquear por estar desactivado. |
| `step_materializers/consistency.py` | P06/P09 leen P04; P10/P11 leen P09; P11 usa P04; P12 depende de variables materializadas. | Declarar estos datos como dependencias reales o refactorizar la fuente de contexto. No moverlos solo en UI. |
| `step_materializers/literature.py` | P16 lee P15 y P14, y compara su número de estudios con PRISMA; P20 lee P16; P22 comprueba variables P11. | Separar cribado ordinario de PRISMA opcional; mantener verificación de PDF/citas P16 sin fabricar registros; permitir categorías donde corresponda. |
| `step_materializers/instruments.py` | P25 lee P11; P30 usa dimensiones/indicadores derivados de P12; P31 permite eje sin dimensión; P32 umbral fijo sobre coeficiente declarado. | Contratos por enfoque e instrumento; piloto calculado desde datos, con método documentado. |
| `step_contracts.py` | P01 5..10, P02 3, P04 exige variables/periodo fijo, P11 VI/VD, P14/P16 años fijos, P20 `APA_7`, P30 limita escalas a Likert 5/7 o dicotómica y P32 recibe coeficiente. | Clasificar cada límite como regla protegida, default de plantilla o herencia a retirar; migrar datos y tests sin convertir límites históricos en norma UTP. |

Un **orden visible** distinto puede publicarse antes de que toda ejecución sea flexible; entonces la API debe mostrar ese alcance honestamente. No declarar B5-C completado hasta que `save_step`, materializadores y `submit_chapter` respeten dependencias reales y pruebas de adelanto/bloqueo.

## 4. Plan de entregas verticales hasta el cierre

El [plan B0–B10](./plan_entregas_backend.md) mantiene los nombres. La secuencia siguiente es de integración y prioridad, no un contrato de calendario. Cada entrega incluye: inspección de símbolo real → contrato/migración compatible → implementación → pruebas focalizadas → actualización de OpenAPI/README/estado → `verify_project.py` una vez al cierre. Los tests completos no se repiten por cada archivo pequeño.

| Orden | Entrega y resultado mínimo visible | Persistencia/API/compatibilidad | Pruebas decisivas y condición de cierre |
|---|---|---|---|
| 0 | **B0 focalizada:** cerrar inventario de símbolos, consumidores y dependencias para la primera migración. | Documentar 27 modelos/18 migraciones del corte real solo mientras esos conteos sigan vigentes; el verificador se actualiza con evidencia si cambian. | Tabla código→requisito; ninguna entidad nueva sin comprobar equivalentes. Este plan proporciona punto de partida, no reemplaza inspección de Flash. |
| 1 | **B5-A/B:** editar, agregar, desactivar y reordenar prompts/tareas por proyecto; validar y publicar versión con diff/restauración. | Entidades/servicios de versiones y dependencias; API Ninja autenticada; los proyectos anteriores siguen con catálogo legado. Evitar meter IDs arbitrarios en `StepProgress.step_code` de tres caracteres sin migración. | Dos usuarios aislados; conflicto concurrente; grafo cíclico rechazado; restauración crea versión; historial exacto. |
| 2 | **B5-C/D:** ejecución por dependencias efectivas y ramas condicionales, primero en un recorrido demostrable. | `save_step`, materializadores y `submit_chapter` consultan versión publicada; refactorizar acoplamientos P15/P16, P11/P25, etc. con migración compatible. | Una búsqueda independiente se adelanta; una dependencia real bloquea; cambio de contexto marca obsolescencia; legado pasa; cuant/qual/mixto no comparten controles inválidos. |
| 3 | **B1+B2:** manuscrito canónico, instantánea íntegra del capítulo, revisión/aprobación/exportación del mismo contenido, API web base. | Modelo de bloque/documento/revisión elegido tras comparar `ChapterRevision` y `ManuscriptDocument`; permisos, anclas, `expected_version` e idempotencia. | Asesor comenta versión exacta, no aprueba con observaciones abiertas, cambio posterior no altera aprobado; usuario ajeno no accede. |
| 4 | **B3+B7:** búsqueda web y manual asistida Scopus/WoS, importación de registros, deduplicación, corpus y extracción multiformato con localizadores. | Modelo de consulta/importación/procedencia; `SourceDocument` ya no requiere OpenAlex para toda fuente externa; adaptar jobs/formatos sin perder PDFs históricos. | Importar RIS/BibTeX/CSV real de prueba; distinguir metadatos de texto; pasaje abre página/hoja correcta; errores por fila; sin credenciales licenciadas. |
| 5 | **B4:** ocurrencias de cita estructuradas, IEEE del piloto, Zotero autorizado cuando acceso exista, revisión afirmación–cita y diff. | Bibliografía/ocurrencias/evaluación ligadas a versión de fuente y manuscrito; conservar APA legado. | Numeración IEEE se actualiza al mover cita; solo metadatos produce acceso insuficiente; pasaje discordante no se marca apoyo; reemplazo requiere aceptación. |
| 6 | **B6:** tareas IA web y multiagentes, contexto fijado, lotes paralelos, aceptación; invitaciones de apoyo si permiso definido. | Job tipado propio o extensión justificada de `DocumentJob`; proveedor configurable, límites/costos, cancelación, permisos por recurso. | Resultado IA obsoleto no escribe; dos antecedentes independientes terminan en lote; invitado ve solo paquete compartido; fallo de proveedor se informa. |
| 7 | **Etapas posteriores a P32 + B8:** protocolo/ética, datos originales, análisis reproducible por enfoque, resultados, tablas/figuras y exportación DOCX/PDF desde snapshot. | Nuevos agregados de dataset/análisis/figura y secciones posteriores; no reutilizar `Chapter.number <=7` sin migración; cuidar P32 legado. | Recalcular figura desde archivo identificado; sin datos no hay hallazgo; cita de participante localizable; mixto integra; DOCX/PDF abren y corresponden a snapshot. |
| 8 | **B10:** endurecimiento operativo y prueba integral sin frontend: autenticación, API, worker, almacenamiento, backup/restauración y documentación. | OpenAPI con ejemplos reales, errores estables, migraciones repetibles, secretos aislados y política de retención. | Recorridos A–D del [criterio](./criterio_backend_listo_para_frontend.md) pasan; gate 0; limitaciones de proveedores explícitas. Solo entonces decir «backend listo para frontend». |

**B9:** APIs licenciadas Scopus/WoS, n8n y otros conectores se agregan si hay permiso/caso útil; no son prerrequisito de B3 ni del núcleo. La conexión Zotero deseada se prueba con autorización real cuando esté disponible; si el acceso falta, declarar estado `DEPENDIENTE_DE_PERMISO` y sostener importación bibliográfica, sin falso OAuth. La decisión de proveedor LLM sí afecta el recorrido IA real; infraestructura/jobs pueden construirse en paralelo, pero no declarar B6 completo solo con mocks.

## 5. Contrato HTTP de traspaso al frontend

**Actual comprobado:** `backend/config/urls.py` monta `/api/v1/`; `backend/config/api.py` usa `django_auth` y responde errores de dominio como `{"detail":"CODE: mensaje"}`; `api/projects.py` publica proyectos, pasos, capítulos, comentarios, fuentes, evidencias, jobs documentales, pasajes, manuscritos y `export/draft.docx`. El router devuelve varios `dict` abiertos. Estos hechos se vuelven a inspeccionar antes de cambiar rutas.

**Grupos de operaciones objetivo (no son URLs implementadas):**

| Grupo lógico | Entradas y respuestas que debe diseñar Flash | Error/versionado indispensable |
|---|---|---|
| Proyecto/ideas/perfil | Crear/listar propios; leer/editar perfil y todas las ideas, incluso descartadas; devolver actor/permiso y `state_version`. | Proyecto ajeno `NOT_FOUND`; conflicto con versión vigente; no perder alternativas. |
| Método/prompts | Leer publicado/borrador, crear/editar/validar/publicar/restaurar, preparar tarea y obtener bloqueos. | IDs de versión, diff, ciclo/entrada faltante, `expected_version`, control protegido. |
| Manuscrito/citas | Leer/guardar bloques, crear snapshot, cita vinculada, evaluación preliminar y aceptar/rechazar diff. | Anclas estables, versión del texto/fuente, respaldo insuficiente, conflicto. |
| Revisión/apoyos | Enviar, comentar, resolver, decidir, invitar/revocar y consultar paquete permitido. | Snapshot ID/hash, comentarios abiertos, actor, vencimiento y permisos por recurso. |
| Búsqueda/corpus | Guardar ecuación/filtros/fuente/fecha, importar/exportar registros, cargar/extraer archivo, recuperar pasajes/preguntar corpus. | Procedencia de ejecución manual vs automática; formato/fila inválida; nivel de acceso/localizador. |
| IA | Crear/consultar/cancelar job, aceptar/rechazar propuesta, consultar lote. | Contexto/prompt/modelo versionados, idempotencia, estado/costo, actor; obsolescencia. |
| Campo/datos/figuras | Registrar protocolo/permiso, cargar datos, transformar/analizar/codificar, calcular figuras. | Datos originales/hash, procedimiento, permisos, ética aplicable, reproducibilidad. |
| Exportación | Solicitar/consultar/descargar DOCX/PDF de snapshot indicado. | Formato real, ID/hash, versión de plantilla, estado y falta de evidencias. |

Por cada operación nueva, fijar método/ruta después de comparar rutas existentes; esquema de request/response estricto; actor/scope; precondiciones; efectos transaccionales; paginación/límites; idempotencia; errores tipados y OpenAPI. La futura web consume decisiones calculadas por backend, no infiere normas, aprobación, numeración IEEE o procedencia desde cadenas de texto. MCP es fachada de los mismos servicios y deriva actor del token del servidor, nunca del prompt.

## 6. Matriz de recorridos de aceptación final

| Recorrido | Datos de prueba y operaciones | Evidencia objetiva de éxito |
|---|---|---|
| A. Método flexible | Proyecto nuevo + legado; dos usuarios; dos versiones de recorrido; tarea de búsqueda independiente y otra dependiente. | Adelanto válido y bloqueo real; ciclo rechazado; conflicto concurrente; prompt/restauración exactos; legado legible. |
| B. Evidencia y escritura | Archivo bibliográfico exportado, PDF físico permitido y pasaje localizado; afirmación/cita; fuente alternativa. | Importación con procedencia real; ficha y cita abren página; metadatos solos no verifican apoyo; diff aceptado crea revisión nueva. |
| C. Asesor/datos/entrega | Dataset de prueba identificado y etiquetado, permisos éticos aplicables, transformación, gráfico y manuscrito. | Figura/cifra reproducible; sin datos no hay hallazgo; asesor revisa snapshot íntegro; DOCX/PDF corresponden a aprobado y no cambian después. |
| D. Ramas | Casos cuantitativo, cualitativo y mixto separados. | Cuantitativo calcula desde datos; cualitativo no requiere VI/VD ni Alfa; mixto documenta integración; ningún resultado sintético se presenta como investigación real. |

Pruebas mínimas por entrega: éxito, entrada inválida, acceso cruzado, rol incorrecto, versión obsoleta, idempotencia, reintento/worker cuando aplica, datos históricos y prueba integrada del caso. El gate de `AGENTS.md` se ejecuta **una vez por entrega cerrada**, tras pruebas focalizadas durante el trabajo. No modificar expectativas del gate para forzar un pase: si crece el número real de modelos/migraciones/prompts, actualizar el conteo comprobado manteniendo la comprobación activa.

## 7. Decisiones abiertas y defaults reversibles

| Decisión | Default de diseño para avanzar | Evidencia necesaria antes de afirmación/activación |
|---|---|---|
| Profesor modifica orden/metodología | Recorrido editable por proyecto, versionado y con diff; asesor observa/sugiere. | Política de visto bueno si afecta plan previamente aprobado. No invalidar firma anterior en silencio. |
| UTP y citación | IEEE como perfil del piloto; reglas institucionales con fuente, fecha, carrera y modalidad. | Documento UTP aplicable para cada trámite/formato; no declarar IEEE universal. |
| Editor web | Árbol/estructura canónica versionada en backend, proyecciones Markdown/DOCX. | Prueba ida/vuelta y anclas de comentario/cita antes de congelar contrato. |
| Una o dos funciones de asesoría | Un asesor activo compatible con esquema actual puede cubrir ambas; capacidades separadas si se necesitan. | Caso institucional que obligue varios asesores, firmas y migración. |
| Scopus/WoS | Consulta manual asistida + importación; sin guardar contraseña UTP. | API solo con entitlement/uso confirmado; no atribuir consulta manual al backend. |
| Zotero | Citas internas propias e importación/exportación bibliográfica; adaptador de biblioteca separado. | Scopes/autorización probados; campos DOCX activos requieren refresco real en procesador compatible. |
| Proveedor IA/retención | Abstracción de proveedor y jobs auditables; secretos de servidor y mínimos datos necesarios. | Credenciales, política de datos/costos/retención y corrida real antes de anunciar generación web activa. |
| Campo y análisis | Datos originales versionados y análisis declarativo por enfoque; restricciones éticas por caso. | Revisión de asesor, permisos/dictamen aplicables y dataset original antes de resultados. |
| Despliegue | Entorno local PostgreSQL/worker reproducible; no exponer al público por defecto. | Seguridad, backups/restauración, recursos y responsables antes de usuarios reales. |

Una decisión abierta no bloquea dominios independientes. Sí bloquea cualquier etiqueta «IMPLEMENTADO» o «listo» que dependa de ella. Flash registra la decisión adoptada, fecha y efecto en contratos/datos en [registro de decisiones](./registro_decisiones_backend.md).

## 8. Instrucción inmediata y reporte esperado de Flash

Primera acción: volver a inspeccionar `step_catalogue.py`, `services/steps.py`, `services/step_materializers/`, `models/chapters.py`, `services/step_contracts.py`, `api/projects.py` y pruebas `test_academic_flow.py`/`extended_steps/`; confirmar que no cambió el árbol desde esta auditoría. Después implementar B5-A/B y B5-C como entregas verticales, manteniendo `ChapterRevision`, `StepProgress` y modo legado legibles. La personalización del prompt y la ejecución flexible son hitos distintos.

Al cerrar **cada** entrega, informar: (a) símbolos/rutas reales cambiados, (b) migración y compatibilidad, (c) ejemplo de petición/respuesta real con IDs/versiones, (d) pruebas y gate con exit code/tiempo, (e) casos del criterio de backend satisfechos, (f) límites/permiso externo pendiente, (g) siguiente entrega. No afirmar backend completo tras B5 ni por alcanzar cierto porcentaje de archivos. El cierre integral solo se produce cuando el [criterio de backend listo para frontend](./criterio_backend_listo_para_frontend.md) está demostrado de extremo a extremo.

## Fuentes internas de este plan

- [Criterio de backend listo para frontend](./criterio_backend_listo_para_frontend.md): alcance y recorridos finales.
- [Plan de entregas](./plan_entregas_backend.md): nombres B0–B10 y regla de cierre.
- [Contrato de recorrido y prompts](./contrato_recorrido_y_prompts_configurables.md): detalle de B5.
- [Propuesta de orden metodológico](../03_metodologia_y_prompts/propuesta_orden_metodologico_revisado.md): plantilla editable, no grafo ejecutable universal.
- [Búsqueda, corpus y revisión de afirmaciones](./especificacion_busqueda_y_revision_de_evidencia.md): contratos de evidencia, invitados y consulta manual.
- [Estado verificable del producto](../07_desarrollo_prototipo/estado_version_producto.md): corte anterior que debe revalidarse frente al código.
- [Contratos de dominio](./contratos_dominio_backend.md), [API](./contratos_api_backend.md), [permisos](./matriz_permisos_y_cuentas_backend.md) y [seguridad/operación](./seguridad_datos_operacion_backend.md): reglas transversales.
