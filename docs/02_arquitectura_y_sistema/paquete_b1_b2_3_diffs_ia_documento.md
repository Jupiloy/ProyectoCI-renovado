# B1+B2.3 — Diff de propuestas IA y aceptación del documento canónico

**Estado del bloque:** implementado y verificado con la puerta integral en el corte B1+B2.3; el desarrollo posterior añadió migración `0027`, cuya puerta actual está pendiente. Este paquete conserva el alcance y evidencia de B1+B2.3.
**Fecha:** 26/10/2026.  
**Alcance:** enlazar al documento canónico las salidas que explícitamente contienen texto de capítulo. El bloque cubre P05 y P29; no convierte otras salidas JSON a prosa ni edita por acción del worker.

## Por qué se limita a P05/P29

Los contratos `P05Output` y `P29Output` declaran el campo `contenido_markdown` como texto del capítulo. En cambio, otros pasos producen temas, matrices, instrumentos, preguntas u otras estructuras; las tareas `USR_...` tienen esquemas configurables. Sin mapping explícito, esas salidas no identifican bloques de documento y no se deben insertar como texto arbitrario.

P05 genera el capítulo 1; P29 genera el capítulo 6, según `WorkflowTask.chapter_no` del recorrido publicado. Ambas salidas representan contenido del capítulo entero, así que la propuesta de esta entrega es `REPLACE_DOCUMENT`, no una inserción automática que pueda duplicar o mezclar secciones sin intención.

## Recorrido

1. Se solicita y procesa el job normal B5.1. La salida válida queda en `AIGenerationJob.output_data` con su hash, estado y contexto congelados.
2. El titular consulta `GET /projects/{project_id}/ai-jobs/{job_id}/document-diff`.
3. El backend verifica pertenencia, job exitoso aún pendiente, tarea P05/P29, contexto vigente y capítulo editable.
4. Lee el árbol canónico vigente; si solo hay revisiones por paso, obtiene la proyección legada de solo lectura. Convierte el `contenido_markdown` contractual de la salida en bloques v1 con IDs deterministas asociados al job.
5. Devuelve una vista previa estructurada con contenido/árbol anterior y propuesto, versión del documento, versión del estado, hash de la salida y `proposal_sha256`. La consulta no crea `ChapterDocument` ni `ChapterDocumentRevision`.
6. El usuario compara y acepta o rechaza. Para aceptar, el cliente envía el `expected_document_version` y `proposal_sha256` que vio, junto con `expected_state_version` y `decision_key`.
7. En una transacción, el servicio bloquea job/perfil, vuelve a comprobar la frescura, recalcula la vista previa, compara versiones y hash, guarda la salida P05/P29 mediante el `save_step` existente y crea una nueva revisión canónica con el árbol propuesto.
8. La aceptación guarda `ChapterDocumentRevision.source=AI_PROPOSAL` y `AIGenerationJob.result_document_revision`; `decision_by`, `decision_at`, `decision_key` y hashes permiten trazar la decisión. La operación actualiza el control de estado por cada agregado que modifica.

Una excepción en cualquier paso revierte todas las escrituras de la aceptación. Si la edición concurrente cambia la versión del documento/estado o si el hash ya no coincide, devuelve un error de conflicto sin cambiar ni revisión de paso ni documento.

## Contratos de API

### Vista previa

`GET /api/v1/projects/{project_id}/ai-jobs/{job_id}/document-diff`

Devuelve `job_id`, `task_id`, `chapter_no`, `operation=REPLACE_DOCUMENT`, `expected_state_version`, `expected_document_version`, `before_content_sha256`, `before_tree`, `before_content_md`, `after_tree`, `after_content_md`, `operations[]`, `source_output_sha256` y `proposal_sha256`.

La operación tipada indica qué cambió: reemplazar el documento vigente con `after_tree`; conserva el árbol antes del reemplazo para que la interfaz construya una comparación legible. El hash se calcula sobre la respuesta determinista sin incluir el propio campo de hash. No es una firma ni reemplaza la autorización.

Solo el titular consulta el diff. Errores de dominio esperados: `NOT_FOUND`, `VALIDATION_ERROR` para una tarea sin mapping explícito, `VERSION_CONFLICT` cuando el capítulo/job no está en estado editable/pendiente y `CONTEXT_STALE` si cambió el contexto.

### Aceptación

`POST /api/v1/projects/{project_id}/ai-jobs/{job_id}/accept`

Para todas las tareas continúan siendo obligatorios `expected_state_version` y `decision_key`. Para P05/P29 además son obligatorios:

```json
{
  "expected_document_version": 3,
  "proposal_sha256": "hash-devuelto-por-document-diff"
}
```

El servicio recomputa el contenido de la propuesta en servidor; nunca recibe `after_tree` ni contenido Markdown elegido por el cliente en la aceptación. Una `decision_key` ya usada devuelve el resultado anterior solo si es la misma decisión.

Las tareas que no sean P05/P29 mantienen su aceptación vigente: P01–P32 guardan su revisión tipada y `USR_...` guarda `WorkflowTaskExecution`. Este paquete no incorpora esos resultados al árbol.

## Persistencia y migración

- La migración `0026_aigenerationjob_result_document_revision_and_more` agrega `AIGenerationJob.result_document_revision` (`FK PROTECT`, nullable) hacia `ChapterDocumentRevision`.
- `ChapterDocumentRevision.Source` añade `AI_PROPOSAL`; no se modifica el historial existente ni el contenido de revisiones.
- No se añade un modelo nuevo. En ese corte eran 36 modelos y 26 migraciones; el corte posterior de fuentes añade `0027` sin modelo nuevo.
- La revisión generada sigue siendo append-only por trigger; el registro del job conserva el destino resultante.

## Casos que deben quedar cubiertos

1. Job P05 válido produce preview, muestra reemplazo y no escribe.
2. Hash de preview adulterado no guarda nada.
3. Aceptación válida crea `ChapterRevision` y `ChapterDocumentRevision`, enlaza el resultado al job y establece origen IA aceptada.
4. Repetir `decision_key` es idempotente y no crea revisiones duplicadas.
5. Contexto o versión desactualizados bloquean sin escrituras parciales.
6. Capítulo READY/APPROVED no acepta reemplazo hasta volver a edición.
7. Un usuario ajeno no obtiene preview ni puede aceptar.
8. P01 and custom `USR_...` maintain their previous behavior and do not generate a document diff; P29, like P05, uses its explicit chapter-text contract.
9. La aceptación P05/P29 requiere `expected_document_version` y hash; no usa datos alternativos del cliente.

## Límites y decisiones posteriores

- `REPLACE_DOCUMENT` reemplaza el capítulo entero. Antes de aceptar, la interfaz debe hacer visible ese alcance. Si producto necesita insertar/reemplazar secciones, primero definir contrato de sección y semántica por tarea, no inferirlo del texto generado.
- El Markdown parser v1 reconoce encabezados, párrafos, citas en bloque, fences de código y listas simples. Formato inline, tablas, figuras, citas IEEE enlazadas y referencias estructuradas no se enriquecen ni validan mediante este diff.
- El sistema comprueba identidad del output y versión del documento, no la verdad académica, validez de citas ni aprobación del asesor. La revisión/aprobación del capítulo continúa siendo un flujo separado.
- La API de preview/diff necesita integración en frontend. Los comentarios siguen anclados a offsets `content_md`; comentarios por bloque y compatibilidad con localizadores del editor deben tratarse después.
- No se verificó una llamada Gemini real en este bloque; pruebas deterministas usan un adaptador de prueba sin credenciales externas.

## Siguiente bloque sugerido

Validar el formato de preview con el editor frontend y diseñar un mapping versionado para una tarea adicional solo cuando su contrato identifique inequívocamente destino y operación. Mantener fuera el contenido libre de `USR_...` hasta que cada tarea declare una operación/tipo de bloque compatible y consentimiento explícito.
