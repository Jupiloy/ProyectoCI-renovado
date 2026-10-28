# B1+B2.1 — Incorporación tipada de propuestas textuales aceptadas

**Estado:** implementado y verificado el 26/10/2026; `python3 scripts/verify_project.py` pasó 7/7 comprobaciones con código 0.  
**Objetivo:** evitar que una propuesta de redacción ya aceptada por el tesista termine en el capítulo como un bloque JSON, manteniendo separadas las salidas estructuradas que no tienen un contrato explícito de prosa.

## 1. Hechos del checkout que delimitan esta entrega

- `AIGenerationJob` persiste `output_data` validado y la aceptación del tesista crea una `ChapterRevision` para P01–P32 mediante `save_step`.
- Antes de este bloque, `accept_ai_proposal` serializaba todos los outputs P como un bloque JSON Markdown, incluso cuando el contrato tipado tenía un campo de redacción.
- `P05Output` y `P29Output` declaran `contenido_markdown`; los demás contratos P tienen estructuras distintas (preguntas, matrices, criterios, instrumentos, metadatos, etc.).
- B1.1 forma el `ChapterSnapshot` desde revisiones aceptadas; B1.2 ancla revisión/aprobación a ese snapshot y B1.3 permite exportarlo.
- `ManuscriptDocument` sigue siendo un DOCX cargado/importado, no el editor canónico web. Esta entrega no resuelve ADR-BE-06 ni implementa el árbol enriquecido del editor.

## 2. Regla de proyección segura

En `backend/thesis/services/ai_jobs.py`, `_accepted_proposal_content_md` mantiene una lista explícita de tareas con texto de capítulo (`P05`, `P29`):

- Para P05/P29, devuelve exactamente el valor contractual `output_data["contenido_markdown"]` como `ChapterRevision.content_md`.
- Si ese valor no existe, no es texto o está vacío, falla con `OUTPUT_INVALID`; no crea una revisión parcialmente materializada.
- Para las demás tareas P, conserva el comportamiento previo: serializa el objeto validado como bloque JSON visible. No adivina qué cadena podría convertirse en prosa.
- `USR_...` no se incorpora a una revisión textual. Se mantiene como ejecución/output estructurado conforme al contrato de workflows.
- El `output_json` original y su hash siguen persistidos en `StepProgress`/`AIGenerationJob`; aceptar la prosa no elimina la salida estructurada ni implica aprobación del asesor.

La generación continúa siendo propuesta hasta la aceptación explícita del tesista. La aprobación del asesor sigue siendo una decisión separada sobre el snapshot de capítulo.

## 3. Alcance y compatibilidad

- No cambia la ruta ni el esquema HTTP de aceptar propuesta; tampoco acepta `output_data` nuevo enviado por el cliente.
- Se reutiliza `save_step`, por lo que se conservan contratos Pydantic, controles de paso, revisión inmutable, estado/versionado e idempotencia existentes.
- No se añaden modelos ni migraciones.
- No se afirma que exista un editor enriquecido, árbol de bloques, citas IEEE estructuradas, tablas/figuras editables ni integración automática de resultados `USR_...`.
- El proveedor Gemini no se invocó en esta entrega: `GEMINI_API_KEY` no estaba configurada en el entorno. Esta modificación es determinista y no prueba una conexión real al proveedor.

## 4. Aceptación

1. P05/P29 aceptados proyectan exactamente `contenido_markdown` como contenido de la revisión.
2. P05/P29 sin texto válido fallan cerradamente con `OUTPUT_INVALID`.
3. Un output estructurado de otra tarea P continúa serializado y no se interpreta como prosa.
4. Las pruebas existentes confirman que aceptar P01 continúa creando su revisión con el JSON estructurado y que salidas custom `USR_...` no se insertan al exportar.
5. La suite integral y verificaciones documentales pasan según `AGENTS.md`.

## 5. Continuación pendiente de B1+B2

Esta es una primera integración vertical de propuestas con el contenido de capítulos existentes, no la finalización de B1+B2. Siguen pendientes la decisión y el diseño de ADR-BE-06 (documento/editor canónico versionado), la edición web de borradores con conflicto de versión, el contrato para mapear resultados estructurados por tarea a secciones/bloques y la ampliación del snapshot/renderer para ese árbol. No reutilizar `ManuscriptDocument` ni inferir prosa de JSON para resolver esas brechas.
