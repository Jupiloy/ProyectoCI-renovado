# B1.2 — Revisión y aprobación ancladas al snapshot

**Estado actual:** implementado en código y cubierto por pruebas de flujo de capítulo; la migración es `0024_chapter_approved_snapshot_reviewcomment_snapshot_and_more`. Este documento describe el contrato original del bloque. Los comentarios nuevos se anclan al snapshot usando offsets Unicode sobre `content_md`; anclas estables por bloque/nodo del editor aún son trabajo pendiente. Para el estado general ver [guía de continuidad](./guia_continuidad_backend.md) y [estado del producto](../07_desarrollo_prototipo/estado_version_producto.md).

**Objetivo:** hacer que las observaciones y decisiones del asesor identifiquen la versión exacta del capítulo enviado que están revisando. B1.2 se apoya en `ChapterSnapshot` de B1.1. No implementa la exportación congelada de B1.3.

## Estado que debe respetar

- `ChapterSnapshot` congela el capítulo enviado y su manifest. `Chapter.submitted_snapshot` apunta al envío vigente; `ReviewEvent.snapshot` ya existe desde B1.1.
- Hoy `ReviewComment.revision` es obligatorio y `add_comment` ancla el texto a la última `ChapterRevision`. La última revisión de paso no equivale necesariamente al contenido consolidado del capítulo.
- Los datos existentes pueden contener comentarios, decisiones o capítulos `READY`/`APPROVED` creados antes de B1.1, sin snapshot asociado. No inventar ni migrarles un snapshot.
- `ReviewEvent` y `ChapterRevision` son append-only mediante triggers PostgreSQL. `ReviewComment` tiene estado mutable para su resolución.
- No cambiar el significado del borrador DOCX ni su ruta.

## Modelo y migración aditiva

1. Agregar `ReviewComment.snapshot`, FK nullable `PROTECT` a `ChapterSnapshot`.
2. Hacer nullable `ReviewComment.revision`, manteniendo la FK y todos los comentarios históricos.
3. Agregar restricción de base de datos que exija exactamente uno de los destinos:
   - comentario histórico/compatibilidad: `revision != NULL`, `snapshot = NULL`;
   - comentario B1.2: `revision = NULL`, `snapshot != NULL`.
4. Agregar `Chapter.approved_snapshot`, FK nullable `PROTECT` a `ChapterSnapshot`.
5. No rellenar `approved_snapshot` para aprobaciones existentes. No reescribir comentarios ni eventos históricos.
6. Crear migración `0024` sin retirar ni alterar triggers históricos.

## Reglas del servicio

### Crear una observación

- Mantener el permiso exclusivo del asesor activo asignado y el estado `READY`.
- Cuando el capítulo tenga `submitted_snapshot`, el cliente debe enviar su `snapshot_id`. Rechazar IDs que no coincidan con el snapshot vigente; esto evita asociar selecciones de una vista antigua a una versión nueva.
- Validar `start_cp`, `end_cp` y `selected_text` contra `snapshot.content_md`, que es la proyección textual consolidada congelada. No calcular offsets sobre la última revisión individual.
- Crear el comentario con `snapshot` y `revision=NULL`.
- Para capítulos históricos que todavía estén en `READY` sin `submitted_snapshot`, conservar temporalmente el camino anterior y anclar a la revisión existente. No aceptar un `snapshot_id` en ese camino.

### Listar y resolver observaciones

- Listar comentarios legados y nuevos sin ocultar su ancla; la respuesta expone `revision_id` o `snapshot_id`, y para snapshots incluye `snapshot_no` y `payload_sha256`.
- Aceptar un filtro opcional `snapshot_id` para mostrar las observaciones de una versión concreta. Si no se envía, devolver el historial del capítulo.
- Resolver comentarios solo para asesores autorizados, incluyendo los anclados a snapshots. La resolución no cambia el snapshot ni el texto que originó la observación.

### Decidir el capítulo

- En el flujo B1.1, `REQUEST_CHANGES` y `APPROVE` actúan sobre `Chapter.submitted_snapshot` vigente y sus comentarios abiertos. Registrar el `ReviewEvent` con `snapshot` y sin `revision`.
- Al aprobar un snapshot, asignar `Chapter.approved_snapshot` y dejar `approved_revision` vacío. La respuesta de estado debe exponer ambos IDs para distinguir datos nuevos de aprobaciones legadas.
- Al solicitar cambios, exigir al menos un comentario abierto anclado al snapshot vigente. Comentarios de snapshots anteriores permanecen en su historial y no se trasladan ni se cuentan como comentarios abiertos del snapshot nuevo.
- Al reabrir una aprobación B1.2, registrar el evento contra `approved_snapshot` antes de limpiar la aprobación. En aprobaciones históricas, conservar el evento ligado a la revisión aprobada disponible.
- Si un capítulo histórico `READY` no tiene snapshot, mantener el camino anterior basado en revisión/comentarios. Si el snapshot vigente falta en un flujo B1.1 nuevo, fallar de forma cerrada donde no se pueda identificar una fuente revisada.

## API

- `POST /projects/{id}/chapters/{no}/comments`: agregar `snapshot_id` opcional en el esquema de transición. Es obligatorio en runtime si existe un snapshot vigente; se conserva el fallback histórico solo cuando el capítulo no tiene snapshot.
- `GET /projects/{id}/chapters/{no}/comments?snapshot_id=...`: agregar filtro opcional, conservar la respuesta histórica añadiendo campos de ancla.
- Las rutas actuales de resolver comentario y decisión no cambian de URL. Mantener autenticación, pertenencia al proyecto y rol del asesor.
- `GET /chapters/{no}` debe incluir `approved_snapshot_id` junto a los IDs ya existentes.

## Pruebas de aceptación

1. Un comentario B1.2 apunta al snapshot vigente, y su fragmento/offset se valida contra el texto consolidado del snapshot.
2. El comentario rechaza snapshot inexistente, de otro capítulo, histórico/no vigente o texto que no coincide.
3. Listado con filtro devuelve solo el snapshot solicitado y expone metadatos del ancla; listado sin filtro incluye comentarios históricos.
4. Un comentario B1.1 bloquea `REQUEST_CHANGES`/`APPROVE` solo en el snapshot donde se creó; comentarios previos no se transfieren a una versión nueva.
5. La aprobación fija `approved_snapshot`; la reapertura conserva el snapshot en el evento y luego limpia la aprobación vigente.
6. Los registros históricos basados en `revision` siguen listándose, resolviéndose y sosteniendo el fallback de capítulos sin snapshot.
7. Usuario ajeno no puede leer, comentar, resolver ni decidir.
8. La migración preserva filas existentes y la restricción rechaza comentarios con ambos destinos nulos o ambos destinos definidos.
9. Mantener las pruebas B1.1 de snapshots e inmutabilidad; no modificar `GET /export/draft.docx`.

## Fuera de alcance

- Exportación DOCX/PDF desde snapshot (B1.3).
- Rediseño del editor, formato de citas, estados nuevos de asesor, traslado automático de comentarios a versiones nuevas, o migración artificial del historial.
- Cambios al contenido o hash de `ChapterSnapshot` y a los triggers append-only existentes.

## Verificación y cierre

- Inspeccionar el estado físico de modelos, migraciones, servicios, API, Admin y pruebas antes de cambiar.
- Ejecutar una vez `python3 scripts/verify_project.py` al final; debe acabar con código 0. Si falla, diagnosticar y reparar antes del reporte final.
- Actualizar `AGENTS.md`, `GUIA_AGENTE.md`, `scripts/verify_project.py` y la documentación del esquema porque la migración nueva cambia los conteos vigentes.
- Reportar explícitamente que B1.3 permanece pendiente.
