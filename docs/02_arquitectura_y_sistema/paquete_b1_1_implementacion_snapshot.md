# B1.1 — Implementación del snapshot de capítulo

**Estado del bloque B1.1:** implementado y verificado con pruebas automatizadas y trigger PostgreSQL. **Actualizado:** 26/10/2026. Implementa la captura persistente e inmutable del snapshot (`ChapterSnapshot`), consulta autorizada e idempotencia de envío. **Actualización del plan:** B1.2 (anclaje de comentarios/aprobación) y B1.3 (exportación DOCX congelada) también fueron implementados posteriormente; consultar sus [paquetes B1.2](./paquete_b1_2_revision_anclada_snapshot.md) y [B1.3](./paquete_b1_3_exportacion_congelada_snapshot.md). Este archivo conserva el alcance original de B1.1.

## 1. Resultado de B1.1

Cuando el tesista envía un capítulo válido, el backend crea o recupera una instantánea inmutable de ese envío. La instantánea conserva el contenido textual de pasos disponibles, los outputs estructurados usados, la versión del recorrido y los IDs/hashes de sus fuentes. El tesista y los participantes autorizados pueden consultar el snapshot exacto.

B1.1 establece la identidad congelada que usan B1.2 (comentarios y decisiones del asesor) y B1.3 (exportación desde esa versión). Ambos bloques se implementaron después. Este archivo conserva el alcance original de B1.1; el estado actual comprobable está en los paquetes B1.2/B1.3 y en el código.

## 2. Hechos de partida confirmados

- `ChapterRevision` es append-only y representa el texto de un paso (`step_code`), no un capítulo completo.
- `submit_chapter` verifica tareas exigibles, luego registra en `ReviewEvent` la última revisión de paso; no crea una copia integral.
- `ReviewComment.revision` es obligatorio y sus offsets apuntan al `content_md` de esa revisión.
- `WorkflowTaskExecution` guarda `input_json`, `output_json`, `output_sha256`, `revision_no`, prompt y workflow. **No** tiene campo de aprobación.
- `StepProgress.output_json` conserva el último estado estructurado del P correspondiente; `ChapterRevision` no conserva una copia de dicho JSON.
- Capítulo 1 contiene P01–P05; P06–P08 son del capítulo 2. La fuente de la asignación es `backend/thesis/step_catalogue.py`/`CHAPTER_STEPS`, no números fijados en pruebas.
- `ManuscriptDocument` corresponde a un DOCX importado; no reutilizarlo como manuscrito canónico.
- No se encontró en el corte auditado un modelo de figura estructurada ni de cita del editor. Los `EvidenceLink` actuales apuntan a revisiones y extractos existentes.

Antes de cambiar código, releer `AGENTS.md`, `GUIA_AGENTE.md`, este paquete y los modelos/servicios/migraciones/rutas/pruebas vigentes. Si algún hecho ya cambió, reportar la discrepancia y adaptar el cambio mínimo, sin inventar capacidades.

## 3. Decisiones de implementación para este bloque

### 3.1 Entidad e inmutabilidad

Crear una entidad dedicada `ChapterSnapshot` (el nombre puede ajustarse solo si ya existe una entidad equivalente en el checkout) relacionada con `Chapter` mediante `PROTECT`. No reutilizar `ChapterRevision` con un `step_code` reservado ni `ManuscriptDocument`.

El modelo debe identificar, como mínimo:

- UUID del snapshot; capítulo; número correlativo positivo y único por capítulo.
- Versión del formato/renderizador del snapshot.
- Título del proyecto congelado al envío.
- Proyección de texto disponible (`content_md`), si existe texto.
- Manifest JSON determinista que enumere tareas/secciones en orden, estados de inclusión, contenido fuente, outputs estructurados, procedencia, hashes y metadatos de evidencia que realmente se encuentren.
- Workflow y versión exacta usados, si aplica; para modo legado, versión/catálogo base identificable.
- Autor y fecha de creación.
- Hash SHA-256 del payload canónico completo (contenido + manifest + formato + título/versiones). Serializar con reglas deterministas explícitas; no hashear representaciones JSON dependientes del orden de claves.

La tabla debe ser append-only en PostgreSQL. Reutilizar la función `tesismcp_reject_history_change()` creada por migración `0009` si sigue vigente; crear/eliminar únicamente el trigger de la tabla nueva. No eliminar ni reemplazar la función compartida al revertir la migración.

No exigir `content_md` no vacío si un capítulo configurable válido pudiera contener resultados estructurados no renderables. El manifest y el hash deben seguir existiendo. No representar un JSON como prosa/tablas automáticamente.

### 3.2 Compilación y fuentes del snapshot

Crear el snapshot dentro de la transacción de `submit_chapter`, después de verificar los prerrequisitos y mientras se bloquean las filas de `ResearchProfile` y `Chapter` de forma consistente con las escrituras existentes. Leer de nuevo el workflow publicado y la completitud dentro de esa transacción. Evitar que un guardado concurrente se mezcle parcialmente con el envío.

Para modo legado:

- Enumerar las tareas desde `CHAPTER_STEPS[chapter_no]`.
- Para cada tarea completada, capturar la revisión de paso vigente con su `revision_id`, `step_code`, `revision_no`, `content_sha256`, `content_md`, `workflow_version_no`/prompt disponibles y el `output_json` de `StepProgress` usado al compilar.
- Mantener el orden legado declarado por el catálogo; no asignar pasos de otro capítulo.

Para `CONFIGURABLE_GRAPH`:

- Usar únicamente tareas del workflow publicado exacto con `chapter_no` coincidente; conservar `workflow_id`, `version_no`, `content_sha256`, `task_id`, `legacy_step_code`, `order_index`, `is_active` e `is_optional`.
- Ordenar tareas por `order_index` y desempatar de forma determinista por `task_id`.
- Para tareas P legadas, capturar la revisión y `StepProgress.output_json` correspondientes al workflow/version exactos.
- Para tareas `USR_...`, capturar la ejecución más reciente del workflow/tarea con `execution_id`, `revision_no`, `output_sha256`, `output_json`, prompt/version y autor. Etiquetarla como salida persistida; no etiquetarla como aprobada. Incluirla en el texto solo si existe un contrato explícito de contenido textual y la implementación ya lo valida; en otro caso conservarla solo en el manifest como no renderizada.
- Capturar tareas opcionales completadas; representar tareas opcionales no realizadas como omitidas si el manifest necesita reconstruir el conjunto visible. No crear outputs ficticios.

Si los requisitos de envío actual permiten un estado que no tenga una fuente exacta para congelar, fallar de forma explícita y segura antes de pasar el capítulo a `READY`; no crear snapshots incompletos como si fueran íntegros.

Capturar en el manifest los `EvidenceLink` vinculados a las revisiones incluidas, con claim, texto coincidente, hash del extracto, estado y localizador/ID de fuente disponibles. No afirmar que esto equivale a un sistema de citas IEEE ni que congela figuras inexistentes.

### 3.3 Reintentos, curso del capítulo y compatibilidad

- Añadir a `Chapter` un puntero nullable al snapshot de envío vigente, con `PROTECT`; usar nombre semántico como `submitted_snapshot`. El historial completo vive en `ChapterSnapshot`, no en ese único puntero.
- Un reintento del mismo envío mientras el capítulo siga en `READY` debe devolver el snapshot ya vinculado, sin crear otra fila. Una vez solicitados cambios y el tesista vuelve a editar, el siguiente envío crea un nuevo `snapshot_no`; los snapshots previos no se actualizan.
- No migrar aprobaciones, eventos o comentarios históricos para fingir que ya tenían una instantánea completa. Mantener `approved_revision` para lecturas legadas. La relación `approved_snapshot` y la modificación de decisiones pertenecen a B1.2.
- No alterar `ReviewComment` en B1.1. La implementación B1.2 que permita comentarios sobre snapshots debe resolver la exclusión entre `revision` y `snapshot`: si reutiliza la tabla, hacer nullable la FK histórica y añadir una restricción de base de datos que exija exactamente uno de los destinos; si crea una tabla separada, justificar el contrato y conservar comentarios legados.
- No modificar todavía el renderizador ni el endpoint `GET /export/draft.docx`. Exportación por snapshot es B1.3; no cambiar el significado del borrador actual.
- No afirmar que `ResearchProfile.lock_version` versiona todas las ejecuciones custom si el servicio de ejecución no lo incrementa. Usar los IDs/hashes del manifest para la identidad del snapshot y documentar el alcance real de cualquier número de estado.

## 4. API B1.1

Revisar el router y los esquemas antes de añadir rutas. Mantener la ruta actual de envío y hacer su respuesta compatible, agregando `snapshot` con ID, número, hash, fecha y formato. Agregar operaciones autenticadas y aisladas por proyecto para:

- listar snapshots de un capítulo (metadatos, no todo el JSON en listados);
- obtener el snapshot por `snapshot_id`, verificando que pertenece al capítulo y proyecto solicitado.

Las respuestas deben distinguir `content_md` como proyección textual y `manifest` como fuentes/outputs congelados. No exponer rutas de filesystem, secretos ni información de otro proyecto. `GET /chapters/{chapter_no}` puede devolver el identificador del envío vigente, con compatibilidad para clientes existentes.

B1.1 no cambia el contrato de comentarios ni de decisión del asesor. No se presenta el snapshot como “aprobado” en esta fase.

## 5. Pruebas de aceptación de B1.1

Agregar solo cobertura que falte, preservando las pruebas actuales:

1. En modo legado, completar las tareas exigibles reales de un capítulo (usar la asignación del catálogo), enviar y comprobar orden, texto, IDs de revisiones, `output_json`, hash y formato del snapshot.
2. En modo configurable, comprobar orden de workflow, filtro por capítulo/versión, tarea opcional completada/no completada y persistencia de salida `USR_...` con `execution_id`/hash sin estado “aprobado” inventado.
3. Un envío repetido en `READY` devuelve el mismo snapshot; después de cambios/reapertura y nuevo envío se crea otro snapshot, y el primero conserva contenido/hash/manifest.
4. Usuario ajeno no puede listar ni leer snapshots. Verificar identidad por `request.user` y `require_project` del servicio.
5. Una escritura/DELETE directa a una fila snapshot falla por trigger PostgreSQL. La migración reversible no desactiva triggers append-only existentes.
6. Conflictos/concurrencia no producen dos snapshots correlativos para un único envío ni una mezcla de revisiones de antes/después del guardado concurrente.
7. Los tests existentes de revisión/exportación P01–P32 continúan pasando; B1.1 no declara aún que comentarios o DOCX consuman snapshot.

No comparar hashes binarios de DOCX en esta fase. B1.3 debe verificar el contenido extraído/XML normalizado del artefacto o establecer explícitamente un empaquetado determinista.

## 6. Fuera de alcance

- Comentarios y decisiones anclados a snapshots (B1.2).
- Campo `approved_snapshot`, aprobación/reapertura sobre snapshots o cambio de estados de asesor (B1.2).
- Exportación DOCX/PDF desde snapshot y cambio del exportador de borradores (B1.3).
- Diseño final del árbol/documento canónico del editor (ADR-BE-06/B2); Markdown es una proyección de transición.
- Nuevos modelos de citas IEEE, Zotero, figuras, datasets o capítulos posteriores a P32.
- Render automático de `USR_...` como prosa o tablas.
- Cambios generales a dependencias metodológicas o secuencia P01–P32.

## 7. Instrucciones de ejecución para el agente

Implementar solo este paquete. Antes de editar, presentar brevemente inventario de símbolos actuales y archivos que cambiará. No empezar una refactorización general. Mantener migraciones aditivas, preservar historial, actualizar documentación impactada y ejecutar las comprobaciones obligatorias de `AGENTS.md`, incluida `python3 scripts/verify_project.py`. Si una prueba no puede ejecutarse por disponibilidad del PostgreSQL local, reportar el bloqueo exacto; no declarar éxito simulado.

Al terminar, informar rutas tocadas, migración/modelo/rutas añadidas, casos cubiertos, riesgos que quedan para B1.2/B1.3 y resultado real del verificador. No afirmar que B1 completo ni el backend completo están listos.
