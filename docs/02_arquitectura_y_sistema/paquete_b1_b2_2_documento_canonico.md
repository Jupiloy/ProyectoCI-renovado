# B1+B2.2 — Documento canónico versionado por capítulo

**Estado de implementación:** código y migración incorporados; ejecutar la puerta integral antes de tratar este corte como verificado.  
**Fecha del cambio:** 26/10/2026.  
**Objetivo:** dar al futuro editor web un almacenamiento canónico estructurado e inmutable por versión, enlazar exactamente esa versión al snapshot de capítulo y exportar desde el contenido congelado. No implica que el editor frontend esté construido ni que la IA inserte contenido automáticamente.

**Actualización posterior:** B1+B2.3 agrega preview/diff y aceptación controlada para P05/P29. Consultar el [paquete B1+B2.3](./paquete_b1_b2_3_diffs_ia_documento.md) para el flujo actual de propuestas IA.

## Decisión técnica que materializa

ADR-BE-06 mantiene estado `PROPOSED`: la implementación adopta como default técnico un árbol JSON de bloques con `schema_version=1`. El Markdown se deriva de ese árbol para interoperabilidad con servicios existentes. La decisión no se considera confirmada hasta que el contrato real del editor/frontend demuestre ida/vuelta sin pérdida para los bloques admitidos.

No se importan ni se reescriben automáticamente las revisiones antiguas. Cuando un capítulo no tiene documento canónico, `GET` construye una proyección de solo lectura desde las últimas revisiones por paso. El tesista crea el documento editable guardando una nueva versión.

## Modelo persistente

- `ChapterDocument`: agregado uno-a-uno con `Chapter`; conserva `current_revision`, `lock_version`, autor de la última actualización y fecha.
- `ChapterDocumentRevision`: identidad UUID, número secuencial por documento, versión del esquema, árbol JSON congelado, Markdown proyectado, hash del árbol, `state_version`, clave de idempotencia, origen, autor y fecha. En B1+B2.2 el único origen era `USER_EDIT`; B1+B2.3 añade `AI_PROPOSAL`. Las revisiones son append-only en PostgreSQL mediante `tesismcp_reject_history_change()`.
- `ChapterSnapshot.document_revision`: FK nullable con `PROTECT`. Es nula en snapshots anteriores. El snapshot nuevo conserva tanto una proyección textual como el identificador exacto de la revisión canónica; por eso el historial previo sigue siendo legible.
- Migración aditiva `0025_canonical_chapter_documents`: crea las dos tablas, relaciones, unicidad/índices/constraints y trigger. No borra ni reescribe revisiones, comentarios, eventos o aprobaciones existentes.

El hash `content_sha256` identifica la serialización JSON canónica normalizada (claves ordenadas y codificación UTF-8); no es el hash del Markdown ni certifica que el contenido sea correcto académicamente.

## Contrato del árbol v1

Raíz exacta:

```json
{
  "schema_version": 1,
  "blocks": []
}
```

Tipos permitidos y campos exactos:

| Tipo | Campos además de `type` e `id` | Renderizado de exportación |
|---|---|---|
| `heading` | `level` (entero 1–6), `text` | Estilo Heading 1–6 |
| `paragraph` | `text` | Párrafo |
| `blockquote` | `text` | Párrafo con estilo de cita |
| `code_block` | `text` | Párrafo monoespaciado |
| `bullet_list` | `items` (1–500 textos) | Lista con viñetas |
| `ordered_list` | `items` (1–500 textos) | Lista numerada |

Cada bloque tiene `id` UUID canónico y único dentro del árbol. Se rechazan campos extra, tipos desconocidos, texto vacío donde no aplique, más de 1,000 bloques, texto por bloque/list item mayor de 20,000 caracteres y contenido o proyección Markdown superior a 200,000 caracteres. `schema_version` desconocida se rechaza; no se interpreta como v1.

Este contrato es una base backend para acordar con el frontend, no la declaración de compatibilidad con un editor específico. No incluye tablas, figuras, citas bibliográficas estructuradas, notas, ecuaciones, comentarios por bloque, posiciones enriquecidas ni importación DOCX. No se debe degradar silenciosamente esos elementos a texto: requieren diseño/versionado posterior.

## API implementada

Base: `/api/v1`, autenticación de sesión Django y comprobación de autorización en el servicio.

### `GET /projects/{project_id}/chapters/{chapter_no}/document`

- Requiere participación autorizada en el proyecto.
- Devuelve la versión canónica vigente y sus `content_tree`, `content_md`, `revision_id`, `document_version`, `state_version`, `content_sha256`, `is_stale` e indicadores de proyección legada.
- Si aún no hay `ChapterDocument`, proyecta las últimas revisiones de pasos siguiendo el orden del catálogo/workflow. No persiste una migración implícita ni atribuye esa proyección al árbol fuente.
- La proyección heredada es de lectura. La edición se materializa con `PUT`.

### `PUT /projects/{project_id}/chapters/{chapter_no}/document`

Entrada: `content_tree`, `expected_version`, `idempotency_key` UUID.

- Solo el titular puede escribir. La API no acepta identidad del autor desde el cuerpo.
- Transacción: bloquea perfil/capítulo/documento; valida versión optimista; crea revisión inmutable y actualiza el puntero mutable `current_revision`.
- Clave de idempotencia repetida con el mismo hash devuelve la revisión previa; la misma clave con otro árbol devuelve `IDEMPOTENCY_CONFLICT`.
- Una discrepancia de `expected_version` devuelve `VERSION_CONFLICT`; el cliente debe volver a cargar antes de guardar.
- Un capítulo `READY` o `APPROVED` no se edita. En `CHANGES_REQUESTED`, el guardado reanuda la edición con la transición existente.
- Guardar incrementa `ResearchProfile.lock_version`; por ello propuestas/documentos basados en un estado previo se reconocen como obsoletos.

## Snapshot, asesor y exportación

Al enviar un capítulo con documento canónico, `submit_chapter` comprueba que su `state_version` coincide con el estado actual y que el documento no está vacío. Crea `ChapterSnapshot` formato 2 enlazado a `ChapterDocumentRevision`; el texto congelado procede de `content_md`, mientras el DOCX aprobado formato 2 renderiza el árbol estructurado congelado. El manifest mantiene la procedencia/output JSON de los pasos, marcando que esos outputs no se concatenaron al texto del editor. `USR_...` no se convierte automáticamente en contenido.

Los snapshots formato 1, comentarios existentes y exportaciones históricas conservan su comportamiento previo. El DOCX aprobado utiliza Markdown para snapshots legados sin `document_revision` y el árbol JSON para snapshots que sí la tienen. `GET /export/draft.docx` mantiene su significado histórico.

**Límite importante:** los comentarios B1.2 siguen anclados por offsets contra `content_md`, no por ID de bloque. La correspondencia de offsets con renderizado visual enriquecido debe cerrarse en una entrega posterior; B1+B2.2 no declara resuelto el anclaje en el editor frontend.

## Integración con generación IA

B5.1 genera y acepta propuestas hacia el modelo de revisiones por paso/ejecuciones de tareas. Este bloque no cambia ese contrato ni inserta resultados IA directamente en `ChapterDocument`. El siguiente cambio debe producir un diff tipado (insertar/reemplazar/eliminar bloque, destino y procedencia), presentarlo al tesista y guardar una nueva revisión canónica solo tras aceptación explícita. Un resultado `USR_...` requiere mapping declarado; no se convierte mediante `str(output_json)` ni por coincidencia de capítulo.

## Archivos principales del cambio

- Modelos: `backend/thesis/models/chapters.py`, exportaciones en `backend/thesis/models/__init__.py`.
- Servicio y validación: `backend/thesis/services/chapter_documents.py`.
- API: `backend/thesis/api/projects.py`.
- Integración snapshot/consulta: `backend/thesis/services/steps.py`.
- DOCX aprobado: `backend/thesis/services/exports.py`.
- Migración: `backend/thesis/migrations/0025_canonical_chapter_documents.py`.
- Pruebas: `backend/thesis/tests/test_academic_flow.py` y `backend/thesis/tests/test_chapter_snapshots.py`.

## Criterios de cierre del bloque

1. `GET` muestra una proyección legada determinista sin escritura lateral y devuelve el documento canónico cuando existe.
2. `PUT` crea versiones append-only y cubre autorización, esquema inválido, idempotencia, conflicto de versión y estados de capítulo.
3. Guardar una tarea/paso después de editar el documento marca su versión como obsoleta; enviar con estado desactualizado se bloquea hasta reconciliar/guardar de nuevo.
4. El snapshot conserva el ID/hash/revisión de documento y no altera el texto histórico al editar después.
5. DOCX aprobado representa los bloques de ese snapshot; no incluye outputs JSON como prosa por inferencia.
6. Migración aditiva, trigger PostgreSQL, documentación y `python3 scripts/verify_project.py` pasan. El último criterio requiere ejecutar la puerta; no se declara verificado antes de obtener `exit code 0`.

## Siguiente trabajo recomendado

1. Cerrar el contrato ida/vuelta con el editor del frontend y añadir round-trip tests para cada tipo de bloque.
2. Diseñar anclas de comentarios por bloque/rango manteniendo lectura/resolución de offsets Markdown de snapshots históricos.
3. Añadir aceptación de propuestas IA como diff canónico auditable; no escribir directamente desde el worker.
4. Ampliar bloques a citas IEEE, tablas y figuras solo con metadatos/procedencia/versiones explícitas y renderizadores comprobables.
