# B1.1 — Auditoría previa de instantánea integral de capítulo

**Estado:** auditoría de solo lectura completada; incluye contraste crítico del primer informe. **Actualizado:** 26/10/2026. Este documento conserva la evidencia y las correcciones; la implementación se rige por el [paquete B1.1 de implementación](./paquete_b1_1_implementacion_snapshot.md).

## 1. Propósito

Precisar cómo debe capturarse una versión íntegra e inmutable de un capítulo para que el asesor pueda revisar una versión identificable y, en una entrega posterior, su aprobación y exportación se refieran al mismo contenido. Esta auditoría precede a cualquier cambio de esquema.

El problema confirmado es una diferencia entre las unidades actuales: el backend guarda revisiones de texto por paso, el envío y la aprobación se apoyan en una `ChapterRevision`, y el DOCX actual reúne la última revisión de varios pasos. El estado aprobado no congela hoy todo lo que luego puede aparecer en el borrador exportado.

## 2. Estado actual verificado que debe volver a inspeccionarse en el checkout

La lista es una guía de lectura, no sustituto del código. Si un símbolo cambió, informar el estado observado y citar su ruta/símbolo real.

| Componente | Hecho observado | Consecuencia para B1 |
|---|---|---|
| `backend/thesis/models/chapters.py::ChapterRevision` | Guarda `step_code`, `content_md`, hash, recorrido/prompt/contexto y autor; es una revisión de un paso. La migración `0009` instala un trigger append-only para esta tabla. | No reinterpretar las filas existentes como capítulos completos. Preservar historial y comentarios. |
| `backend/thesis/models/chapters.py::Chapter` | Conserva estado y `approved_revision`; no tiene relación a una instantánea integral observada en este corte. | Cualquier nuevo puntero de envío/aprobación debe coexistir con datos y referencias legadas. |
| `backend/thesis/models/chapters.py::ReviewComment` | Apunta obligatoriamente a `ChapterRevision`; offsets y selección se comprueban contra `content_md` de esa revisión. | Identificar compatibilidad necesaria para comentarios históricos y definir si los comentarios nuevos deben anclarse a la futura instantánea. No migrar silenciosamente sus offsets. |
| `backend/thesis/models/chapters.py::ReviewEvent` | Apunta opcionalmente a `ChapterRevision`. | Conservar eventos anteriores; una decisión nueva debe identificar de forma inequívoca la unidad revisada. |
| `backend/thesis/services/steps.py::save_step` | Crea revisiones por paso; `StepProgress.output_json` es el estado actual del resultado estructurado. | Determinar cómo una instantánea preservaría la salida estructurada usada, no solo el texto. |
| `backend/thesis/services/steps.py::submit_chapter` | Comprueba tareas exigibles según el modo del proyecto y registra el evento con la revisión más reciente. | Determinar dónde y cuándo se crea la instantánea, cómo se identifica y cómo se evita enviar una mezcla posterior de cambios. |
| `backend/thesis/services/reviews.py::add_comment` y `decide_chapter` | Comentan/deciden sobre la revisión más reciente y mantienen la aprobación en `approved_revision`. | Proponer transición compatible para comentarios, observaciones, aprobación y reapertura. |
| `backend/thesis/services/exports.py::export_draft_docx` | Exporta un borrador concatenando la última `ChapterRevision` de cada paso. | La exportación aprobada futura debe consumir una instantánea identificada; no cambiar el significado de exportación actual sin revisar consumidores. |
| `backend/thesis/models/documents.py::ManuscriptDocument` | Conserva DOCX cargados por el usuario y su conversión; no es el editor ni el manuscrito canónico del proyecto. | No reutilizarlo como modelo canónico sin evidencia adicional y una razón explícita. |
| `backend/thesis/api/projects.py` | Tiene rutas de pasos, capítulos, comentarios, decisiones y exportación de borrador. | Enumerar cambios de contrato compatibles; no crear rutas antes de justificar la necesidad y revisar consumidores. |
| `backend/thesis/tests/test_academic_flow.py` y `test_flexible_execution.py` | Cubren envío, comentarios, aprobación, exportación y exigibilidad de tareas. | Identificar qué pruebas se conservan y qué comportamiento debe añadirse; no borrar ni debilitar aserciones existentes. |

## 3. Alcance de esta auditoría

El agente debe leer `AGENTS.md`, `GUIA_AGENTE.md`, este paquete, [plan de entregas](./plan_entregas_backend.md), [criterio de backend listo para frontend](./criterio_backend_listo_para_frontend.md), [guía backend completa](./guia_backend_version_completa_para_agentes.md), [contratos API](./contratos_api_backend.md), [registro de decisiones](./registro_decisiones_backend.md), modelos, servicios, migraciones y pruebas directamente relacionados.

Entregar solo un informe con:

1. Confirmación/corrección de cada hecho de la tabla, con ruta y símbolo; señalar hechos que ya no coincidan con el checkout.
2. Flujo actual real desde `save_step` hasta `submit_chapter`, comentario, decisión y exportación, incluyendo qué revisiones/output estructurado toma cada operación.
3. Alternativas de diseño para una instantánea completa, con campos requeridos, relaciones, inmutabilidad en PostgreSQL, forma de crearla, numeración/idempotencia y cómo se reconstruye el contenido exacto.
4. Comparación explícita de cómo preservaría: proyectos legados, revisiones por paso, outputs estructurados, tareas `USR_...`, comentarios/eventos, aprobaciones, recorrido y prompts versionados.
5. Cambios de API mínimos y compatibles que harían falta en fases separadas: creación/consulta de snapshot; revisión y decisión; exportación desde el mismo snapshot. Distinguir lo que pertenece a B1.1 de lo posterior.
6. Pruebas de aceptación propuestas, incluyendo conflicto/concurrencia, permisos, comentarios abiertos, reapertura, alteraciones posteriores a la aprobación y verificación de que exportar un snapshot antiguo no cambia después de editar el proyecto.
7. Riesgos, decisiones que el equipo debe cerrar y recomendación razonada de la opción más pequeña que garantice que revisión y exportación puedan referirse al mismo capítulo.

Las recomendaciones deben respetar `ADR-BE-05` y coordinarse con `ADR-BE-06`: Markdown puede ser una proyección/intercambio, no debe declararse automáticamente el formato canónico final del editor enriquecido. Si los modelos existentes no guardan citas, figuras u outputs necesarios, indicarlo como brecha; no inventar entidades ya existentes.

## 4. Fuera de alcance

- No editar ni crear archivos del repositorio durante esta auditoría.
- No ejecutar migraciones, pruebas ni `scripts/verify_project.py` en la fase de auditoría de solo lectura.
- No crear todavía modelos, serializers, endpoints, migraciones, comentarios ni exportadores.
- No rehacer B5/B5.1, el adaptador Gemini, los prompts P01–P32, el workflow, Zotero o el frontend.
- No declarar resuelto el editor enriquecido, las citas IEEE, figuras o resultados empíricos si el código no los conserva.

## 5. Criterio para pasar a implementación

La auditoría debe identificar una alternativa que preserve datos legados y cierre el vínculo de identidad entre capítulo presentado, versión comentada/aprobada y contenido exportable. Debe enumerar los cambios por archivos/símbolos y proponer una secuencia acotada. Solo después se prepara el paquete de implementación B1 con decisiones resueltas y aceptación verificable. Esta auditoría, por sí sola, no significa que B1 esté implementado.

## 6. Revisión crítica del primer informe de auditoría

**Estado de esta revisión:** contraste con el código físico del proyecto. El informe de Gemini acertó en la brecha principal y en proponer una entidad dedicada; los siguientes puntos corrigen afirmaciones o decisiones que no se deben trasladar literalmente a la implementación.

1. En el catálogo actual, **P01–P05 pertenecen al capítulo 1** y P06–P08 al capítulo 2. No escribir una prueba que trate P01–P08 como tareas de capítulo 1. Para el flujo legado, obtener el conjunto desde `CHAPTER_STEPS`, no codificar cantidades por recuerdo.
2. `WorkflowTaskExecution` no tiene un campo de estado/aprobación. La fila representa una ejecución persistida; no afirmar que una ejecución está “aprobada” por existir. El snapshot debe conservar su ID, hash, workflow y salida, e identificarla como resultado persistido. Cualquier semántica adicional de aprobación exige una decisión y cambio separados.
3. Para que `ReviewComment` pueda apuntar a una instantánea conservando comentarios antiguos, un FK opcional `snapshot` no basta: `revision` es obligatorio hoy. Si se reutiliza la tabla, la migración debe permitir `revision=NULL` para comentarios nuevos de snapshot y añadir una restricción que exija exactamente uno de `revision` o `snapshot`; la alternativa es una tabla nueva con semántica explícita. Esto corresponde a B1.2, no a B1.1.
4. Un campo `full_content_md` puede ser una proyección versionada del contenido textual disponible en los pasos actuales. No se debe declarar el Markdown como el modelo canónico final del editor: ADR-BE-06 deja pendiente la representación estructurada. B1.1 debe conservar además un manifest con las fuentes exactas del contenido y outputs estructurados.
5. No convertir automáticamente outputs JSON `USR_...` en tablas, advertencias o prosa. Registrar output, hash, tarea, versión y procedencia en el snapshot; representarlo visualmente en el manuscrito requiere un contrato de contenido posterior.
6. El catálogo del producto no contiene actualmente un modelo de figura estructurada ni un modelo de cita del editor. `EvidenceLink` conserva vínculos a `ChapterRevision` y `SourceExcerpt`; cualquier manifest de evidencia debe capturar los valores/localizadores efectivamente existentes y no afirmar que cubre futuras citas/figuras del editor.
7. El nuevo ciclo no debe cambiar silenciosamente `GET /export/draft.docx` para exportar aprobados. B1.3 debe añadir una operación explícita de exportación por snapshot y demostrar que corresponde a su contenido. Al comparar DOCX, verificar el contenido extraído o XML normalizado; la igualdad de bytes del ZIP no está garantizada por este contrato.
8. El informe afirma que `test_flexible_execution.py` prueba que `approved_revision_id` apunta a la última revisión. Esa suite prueba envío con una tarea opcional desactivada; la aserción de aprobación citada está en `test_academic_flow.py`. No atribuir cobertura a una prueba que no la contiene.
9. “Alternativa B es la única” es una valoración del informe, no un hecho. La entidad dedicada `ChapterSnapshot` es el default recomendado por separación semántica y compatibilidad, pero su esquema final debe justificarse frente a los contratos existentes.

El siguiente paso técnico está especificado en [Paquete de implementación B1.1](./paquete_b1_1_implementacion_snapshot.md). El informe de auditoría por sí solo no implementa el snapshot.
