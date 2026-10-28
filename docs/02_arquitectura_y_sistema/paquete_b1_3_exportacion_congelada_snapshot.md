# B1.3 — Exportación DOCX congelada desde el snapshot aprobado

**Estado:** implementado y verificado el 26/10/2026; `python3 scripts/verify_project.py` pasó 7/7 comprobaciones con código 0.  
**Dependencia:** B1.1 crea `ChapterSnapshot`; B1.2 asocia las aprobaciones nuevas a `Chapter.approved_snapshot`.  
**Alcance:** producir una descarga DOCX independiente del borrador actual, tomando exclusivamente el snapshot que está aprobado en el capítulo en el momento de la solicitud.

## 1. Propósito y límites

La exportación debe permitir que tesista y asesor consulten o entreguen fuera de la plataforma el texto exacto que recibió aprobación. El documento debe exponer la procedencia del contenido para que pueda relacionarse con el registro inmutable que revisó el asesor.

Este DOCX es una **proyección descargable del texto** y no una certificación institucional, una tesis lista para sustentar, una verificación de citas ni un archivo de Zotero con campos activos. No incorpora portada institucional completa, similitud, bibliografía regenerada ni resultados estructurados convertidos a prosa. La exportación no debe reemplazar ni cambiar `GET /api/v1/projects/{project_id}/export/draft.docx`, que continúa reuniendo las revisiones guardadas más recientes como borrador.

## 2. Fuente de verdad y autorización

- La fuente única del texto es `Chapter.approved_snapshot`, que debe pertenecer al `Chapter` y al proyecto solicitados.
- El capítulo debe estar en estado `APPROVED` y tener `approved_snapshot`. Si está en revisión, tiene observaciones, fue reabierto o solo conserva una aprobación histórica por `approved_revision`, no hay snapshot exportable por esta ruta.
- La autorización del servicio comienza con `require_project(actor, project_id)`. Miembros activos del proyecto (tesista y asesor asignado) pueden descargarlo; usuarios ajenos reciben el comportamiento no revelador existente (`NOT_FOUND`).
- Al reabrir el capítulo, B1.2 limpia el puntero de aprobación vigente. La ruta entonces deja de exportar hasta que un nuevo snapshot sea aprobado. No se exporta automáticamente el último snapshot histórico como si siguiera aprobado.
- No se consulta `ChapterRevision`, `StepProgress`, workflow vigente ni contenido editado después de la aprobación para producir el documento.

## 3. Contrato del endpoint

`GET /api/v1/projects/{project_id}/chapters/{chapter_no}/export/approved.docx`

- Respuesta exitosa: archivo OOXML DOCX descargable, `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document` y nombre `capitulo-{chapter_no}-aprobado.docx`.
- Respuesta de capítulo inexistente o no visible al usuario: `404` según los errores de dominio actuales.
- Capítulo sin aprobación vigente basada en snapshot, incluido un registro histórico aprobado solo por revisión: `409 VERSION_CONFLICT`.
- El endpoint no crea ni modifica registros, snapshots, decisiones, eventos ni revisiones. Cada solicitud genera el archivo en memoria a partir de la fuente inmutable.

## 4. Contenido y formato del DOCX

El servicio `export_approved_snapshot_docx(actor, project_id, chapter_no)` debe:

1. Autorizar al actor y localizar el capítulo con su snapshot aprobado.
2. Fallar de forma cerrada si el estado, la relación o la procedencia no son coherentes.
3. Generar el documento desde `snapshot.project_title`, `snapshot.content_md`, número de capítulo y metadatos de aprobación disponibles.
4. Incluir el UUID, número y `payload_sha256` del snapshot; incluir `approved_at` si existe. `created_at` del snapshot no se etiqueta como fecha de aprobación.
5. Interpretar solo el Markdown ya permitido por el renderizador vigente: encabezados simples, listas con viñetas y párrafos. No inventar contenido para un snapshot vacío.
6. Indicar en el documento que el texto proviene de `content_md` y que los outputs estructurados del manifest no se convierten automáticamente en prosa.
7. Mantener el formato de página A4, Arial 11, interlineado doble y márgenes ya aplicados al borrador.

El hash que se muestra es el SHA-256 del payload canónico del snapshot; no es un hash binario del DOCX generado. La identidad reproducible de la fuente es el snapshot y su hash, no el archivo ZIP OOXML, que puede variar entre generaciones.

## 5. Compatibilidad

- `export_draft_docx` y su ruta no se modifican semánticamente ni cambian de nombre o respuesta.
- No se añade modelo ni migración: B1.1/B1.2 ya guardan el snapshot y la referencia de aprobación.
- No se modifica el snapshot, el manifest, los triggers append-only, el historial de revisiones ni la lógica de decisiones B1.2.
- No se afirma que las aprobaciones legadas por revisión tengan snapshot completo. Esas filas conservan su historia y no califican para esta descarga.

## 6. Pruebas de aceptación

1. Sin aprobación vigente, la exportación del servicio y de la API falla con conflicto.
2. Con una aprobación nueva, el DOCX incluye el texto de `content_md`, capítulo, UUID/número/hash del snapshot y formato esperado.
3. No incluye como prosa claves o valores del manifest estructurado (incluido contenido de tareas `USR_...`).
4. El endpoint devuelve DOCX y el nombre de archivo acordado.
5. Un miembro ajeno no puede exportar; los miembros autorizados sí.
6. Una aprobación histórica que solo tiene `approved_revision` no se representa como snapshot aprobado.
7. Reabrir el capítulo elimina la disponibilidad de exportación vigente hasta una nueva aprobación.
8. Las pruebas existentes del borrador confirman que `GET /export/draft.docx` mantiene contenido y formato.

## 7. Fuera de alcance

Exportación PDF; conservar una copia binaria del DOCX en almacenamiento; revisión de citas o campos Zotero; tablas/figuras generadas; estilos institucionales completos; exportar snapshots no aprobados o aprobaciones históricas basadas solo en revisión; cambios al editor web; B1.2 y B1.1 ya implementados.

## 8. Cierre de implementación

No se requiere alterar conteos de modelos ni migraciones. Ejecutar al final `python3 scripts/verify_project.py`; reportar su código real, duración y comprobaciones. No declarar el bloque terminado si la puerta no devuelve código 0.
