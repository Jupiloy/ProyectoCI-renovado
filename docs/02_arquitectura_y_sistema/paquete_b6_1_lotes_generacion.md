# B6.1 — Lotes trazables para generación de tareas independientes

**Propósito:** dejar de solicitar manualmente y por separado varias tareas independientes ya soportadas por B5.1, sin reemplazar el job unitario ni mezclar outputs.  
**Estado:** implementado y verificado por puerta integral: 7/7 comprobaciones, 288.97 s, exit code 0 (26/10/2026).
**Paquete de trabajo:** [`pendientes_backend_despues_b4.md`](./pendientes_backend_despues_b4.md).

## 1. Resultado que debe ofrecer

El titular manda una lista pequeña de tareas del workflow ya publicado. El backend valida todas antes de persistir, crea un lote y un `AIGenerationJob` existente por cada tarea, y devuelve un identificador consultable. El usuario ve estado agregado y estado individual. Puede cancelar las tareas que permanezcan `QUEUED`.

Cada job usa el mismo estado/perfil y versión del workflow solicitados al lote. Cada output queda como propuesta B5.1, con su contrato, hash y aceptación individual. No se sintetizan resultados, no se acepta un grupo entero y no se escribe el manuscrito automáticamente.

**Nota sobre paralelismo:** el worker B5.1 es singleton en el corte actual. B6.1 agrupa y despacha tareas, pero todavía no afirma ejecución concurrente real. Habilitar varios workers y fijar límites de concurrencia/proveedor queda en B6.2.

## 2. Alcance

Incluye:

- modelo `AIGenerationBatch` con proyecto, titular, UUID idempotente, hash/JSON canónico de solicitud, versión de estado y versión de workflow;
- modelo `AIGenerationBatchItem` que conserva orden, `task_id` y relación uno a uno con el `AIGenerationJob` generado;
- límite fijo inicial de ocho tareas por lote, sin alias ni repetición de `task_id`;
- validación de independencia: una tarea del lote no puede depender mediante arista bloqueante de otra tarea incluida;
- creación atómica del batch, jobs e items mediante el servicio `request_task_generation` existente;
- rechazo completo si una tarea, dependencia, permisos, esquema, proveedor o versión falla;
- consulta de estado agregado derivado de los jobs vinculados, outputs y errores por tarea;
- cancelación idempotente de jobs aún `QUEUED`; jobs `RUNNING` quedan visibles como no cancelables;
- endpoints HTTP autenticados, permisos owner-only y control de proyecto en servicio.

No incluye: proveedor nuevo, reimplementación de worker, paralelismo, fan-out desde listas de prompts libres, tareas `USR_...` no ejecutables por contratos existentes, síntesis/merge, aceptación masiva, gasto monetario estimado, presupuesto real no suministrado por proveedor, invitaciones, ni edición del manuscrito.

## 3. Contrato HTTP

### `POST /api/v1/projects/{project_id}/ai-batches`

Request:

```json
{
  "tasks": [
    {"task_id": "P14", "input_data": {}, "context_refs": []},
    {"task_id": "USR_ANTECEDENTES_LOCAL", "input_data": {}, "context_refs": []}
  ],
  "expected_state_version": 7,
  "workflow_version_no": 3,
  "idempotency_key": "UUID"
}
```

El ejemplo `USR_...` es solo estructural; debe existir en el workflow publicado y tener `output_schema` ejecutable por B5.1. La tarea debe cumplir las dependencias de ese workflow.

Campos por tarea: `task_id` requerido, `input_data` objeto opcional, `context_refs` lista opcional de referencias ya admitidas por el servicio unitario. Los IDs del lote deben ser únicos. Rechazar lista vacía o mayor al límite.

Respuesta inicial `202`: `batch_id`, `project_id`, estado agregado, cantidad de items, `request_sha256`, versiones fijadas y resumen por item con `job_id`, `task_id`, estado, versión de prompt, error seguro si existe y estado de aceptación. La salida completa solo aparece a través de lecturas autorizadas B5.1.

### `GET /api/v1/projects/{project_id}/ai-batches/{batch_id}`

Devuelve estado actual derivado, conteos por estado (`queued`, `running`, `succeeded`, `failed`, `cancelled`) y `completed_count`:

- `QUEUED`: queda al menos un job en cola y ninguno está corriendo (pueden existir resultados terminales previos);
- `RUNNING`: al menos un job sigue corriendo;
- `SUCCEEDED`: todos terminaron generación exitosamente;
- `FAILED`: todos fallaron;
- `CANCELLED`: todos se cancelaron antes de iniciar;
- `PARTIAL`: mezcla de resultados exitosos con fallidos/cancelados o alguna combinación terminal distinta.

`SUCCEEDED` describe generación, no aceptación humana. Cada item mantiene su `acceptance_status`; todos permanecen `PENDING_ACCEPTANCE` hasta aceptar individualmente por la ruta B5.1.

### `POST /api/v1/projects/{project_id}/ai-batches/{batch_id}/cancel`

Cancela los items `QUEUED`. Devuelve estados de todos los items y conteos `cancelled`, `already_terminal`, `still_running`. No interrumpe HTTP/modelo de un item `RUNNING`. Repetir no altera resultados y devuelve el estado agregado actual.

## 4. Invariantes transaccionales y de seguridad

1. Actor de sesión autenticado; únicamente titular crea o cancela. No aceptar `user_id` desde JSON.
2. Batch, tareas, workflow y jobs pertenecen al mismo proyecto. Tarea activa y workflow publicado exacto.
3. Comprobar `expected_state_version` y `workflow_version_no` bajo transacción antes de crear jobs.
4. Para cada par de tareas, rechazar dependencia bloqueante de una tarea del mismo lote. No asumir independencia por nombres similares.
5. Llamar el caso de uso unitario para reconstruir snapshot de contexto y validar entradas/contratos; nunca confiar en snapshot entregado por cliente.
6. Toda creación es atómica: lote y todos sus jobs/items, o ninguna fila. La llamada externa al proveedor no ocurre durante la petición porque jobs permanecen asíncronos.
7. `idempotency_key` se limita a proyecto. Mismo key y mismo hash devuelve batch existente; mismo key con solicitud diferente devuelve conflicto.
8. UUID de los jobs secundarios debe ser determinista bajo el batch/key y task/item, para que reintentos no creen jobs duplicados.
9. Cancelación solo cambia jobs `QUEUED`; registrar `finished_at`; no tocar outputs completados, decisiones o historial.
10. Ningún endpoint del lote acepta resultados/cambios del cliente ni permite aceptación masiva.

## 5. Modelos y agregado

`AIGenerationBatch` debe almacenar solo metadatos comunes y solicitud idempotente. No duplicar el contenido de cada job. `AIGenerationBatchItem` relaciona cada posición con un job y clave de tarea. Las reglas SQL/Django deben impedir orden/item duplicado y que un job se vincule más de una vez. Mantener `AIGenerationJob` como fuente de verdad del estado de ejecución, output y decisión.

Las tablas son trazabilidad de orquestación, no un nuevo proveedor ni sistema de aceptación. No modificar migraciones `0021`–`0022` ni rehacer contratos B5.1.

## 6. Pruebas de aceptación

- creación HTTP válida: crea un batch y un job por task; versiones/hash iguales;
- idempotencia exacta devuelve batch y jobs existentes; reuso con payload distinto da conflicto;
- tarea repetida, lista vacía, exceso del límite, ID inexistente/inactivo, versión vieja y actor no titular no crean filas;
- una arista bloqueante interna rechaza el batch; una dependencia externa pendiente falla por regla unitario y revierte todo;
- salida por job valida separadamente; estado agregado sigue `SUCCEEDED` mientras aceptación individual permanece pendiente;
- mezcla `SUCCEEDED`/`FAILED`, todos `FAILED`, todos `CANCELLED`, `RUNNING` y combinación terminal se resumen correctamente;
- cancelación cambia solo jobs `QUEUED`, deja `RUNNING` visible y reintentar no altera jobs terminales;
- lectura y cancelación de UUID ajeno devuelve `NOT_FOUND`;
- PostgreSQL confirma constraints de lote/item y rollback completo;
- ejecución real paralela no se afirma ni prueba en B6.1; es criterio de B6.2.

Después de implementar, actualizar conteos en `AGENTS.md` y `scripts/verify_project.py`, contratos API, README backend, estado del producto, guía de continuidad, este paquete y lista de pendientes. Cerrar con la puerta de `AGENTS.md`; un mock verifica el contrato de software, no que el proveedor LLM esté configurado en vivo.

## 7. Implementación registrada en el código

- `backend/thesis/models/ai_batches.py`: `AIGenerationBatch` y `AIGenerationBatchItem`; solicitudes y asociaciones append-only en PostgreSQL.
- `backend/thesis/migrations/0036_aigenerationbatch_and_items.py`: tablas, unicidad de clave/item/orden, índice por proyecto/fecha y triggers append-only.
- `backend/thesis/services/ai_batches.py`: validación, hash canónico, idempotencia, lock de estado, verificación de tareas/dependencias, fan-out atómico vía `request_task_generation`, estados agregados derivados y cancelación exclusiva de jobs en cola.
- `backend/thesis/api/projects.py`: creación, listado, consulta y cancelación autenticados bajo el router de proyectos.
- `backend/thesis/tests/test_ai_batches.py`: creación/API, idempotencia, límites, dependencia interna, permiso owner, rollback por prerrequisito y cancelación/estado mixto.

**Decisión explícita:** B6.1 no proporciona ejecución paralela ni síntesis. Las propuestas exitosas permanecen pendientes de aceptación una por una a través de B5.1. La puerta completa del repositorio aprobó este corte: 7/7, 288.97 s, exit code 0.
