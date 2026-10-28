# B6.3 — Síntesis trazable y revisión de resultados de lote

**Estado:** implementado y verificado; B6 completo pasó puerta integral 7/7, 395.34 s, exit code 0.  
**Propósito:** reducir la lectura repetitiva de resultados de tareas independientes mediante un informe comparativo que conserve su procedencia y requiera revisión del tesista.

## Alcance implementado

- Reutiliza el lote y los `AIGenerationJob` de B6.1, además del worker concurrente B6.2. No crea una segunda cola ni escribe en capítulos.
- El tesista solicita una síntesis de entre 2 y 8 jobs `SUCCEEDED` del mismo lote. Se comprueban las salidas persistidas contra sus hashes; la entrada queda congelada con `job_id`, `task_id`, hash, estado de aceptación y JSON de salida.
- La síntesis tiene prompt y esquema versionados, hash de snapshot, estado de job, proveedor/modelo/uso/error, resultado validado y estado de decisión separado. El worker la procesa mediante el mismo adaptador estructurado del sistema.
- El resultado diferencia resumen, acuerdos, diferencias, vacíos y recomendaciones. Cada referencia debe resolver a un `task_id` seleccionado en el snapshot; referencias externas al conjunto provocan `FAILED/OUTPUT_INVALID`.
- El tesista puede aceptar o rechazar el informe auxiliar con clave de idempotencia y motivo. Asesores y participantes autorizados pueden consultarlo; la decisión final no equivale a aprobar la tesis.
- Triggers PostgreSQL protegen procedencia, snapshot, resultado exitoso, decisión y borrado. Reintentos automáticos no se introducen; la recuperación del worker marca las síntesis `RUNNING` abandonadas como `FAILED/WORKER_INTERRUPTED`.

## API

Todas las rutas están bajo `/api/v1/projects/{project_id}`:

| Método y ruta | Permiso/efecto |
|---|---|
| `POST /ai-batches/{batch_id}/syntheses` | Solo titular; `job_ids` (2–8 UUID) e `idempotency_key`; responde `202` y crea una síntesis `QUEUED`. |
| `GET /ai-batches/{batch_id}/syntheses` | Participante activo; lista hasta 50 síntesis del lote. |
| `GET /ai-batches/{batch_id}/syntheses/{synthesis_id}` | Participante activo; consulta estado, fuentes congeladas y salida si tuvo éxito. |
| `POST /ai-batches/{batch_id}/syntheses/{synthesis_id}/cancel` | Solo titular; cancela únicamente si sigue `QUEUED`. |
| `POST /ai-batches/{batch_id}/syntheses/{synthesis_id}/decision` | Solo titular; `decision` (`ACCEPTED`/`REJECTED`), `decision_key` UUID y `reason` opcional (máx. 1000 caracteres). |

## Límites deliberados

- El informe no se convierte en prosa, tablas ni citas del manuscrito, no acepta las propuestas fuente, no modifica `ChapterDocument`, `ChapterRevision`, `WorkflowTaskExecution` ni `StepProgress`.
- `USR_...` sigue siendo una salida JSON de ejecución, no una aprobación. Estar `SUCCEEDED` solo indica que la ejecución terminó y pasó validación de esquema.
- La salida generada por adaptador simulado prueba el contrato de software, no una llamada real a Gemini. Credencial, disponibilidad, política de datos y coste deben verificarse aparte.
- Una decisión del tesista se conserva como revisión del informe auxiliar; no la interpreta el asesor como aprobación académica.

## Archivos principales

- `backend/thesis/models/ai_batches.py`: entidad `AIGenerationBatchSynthesis`.
- `backend/thesis/services/batch_synthesis.py`: snapshot, hash, esquema estricto, worker, permisos y decisiones.
- `backend/thesis/services/ai_jobs.py`: reclamo de generación o síntesis por antigüedad; recuperación de trabajos interrumpidos.
- `backend/thesis/api/projects.py`: rutas REST.
- `backend/thesis/migrations/0037_projectsupportinvitation_supportcontribution_and_more.py`: creación de entidades y triggers; agrupa también B6.4.
- `backend/thesis/tests/test_ai_batches.py`: síntesis, referencia inválida, worker, decisiones, aislamiento del manuscrito y triggers PostgreSQL.

## Criterios cubiertos por la verificación

Las pruebas cubren idempotencia/conflicto, pertenencia al lote, estados de origen, hashes, task IDs autorizados, permisos, cancelación, decisión repetida, protección PostgreSQL y que ningún artefacto canónico cambie. El cierre conjunto B6.3/B6.4 está registrado en [B6 completo](./paquete_b6_completo.md) con puerta integral aprobada.
