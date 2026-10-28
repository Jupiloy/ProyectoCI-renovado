# B6.2 — concurrencia segura del worker de generación IA

**Estado:** implementado y verificado por puerta integral: 7/7 comprobaciones, 313.67 s, exit code 0 (26/10/2026). Suite completa `pytest`: aprobada en 293.13 s; pruebas focalizadas `test_ai_generation.py`: 19 pasaron.  
**Alcance:** hacer que trabajos independientes de `AIGenerationJob` puedan ejecutarse en paralelo con un límite explícito, sin duplicar su reclamo, reintentar silenciosamente llamadas externas ni cambiar el contrato HTTP de B5.1/B6.1.  
**No incluye:** síntesis de resultados (B6.3), invitaciones (B6.4), selección de modelo por proyecto, cambio de proveedor, un límite monetario real ni paralelismo entre procesos worker.

## 1. Hechos de partida comprobados en el código

- `run_ai_worker` ya adquiría el advisory lock PostgreSQL `7721503202`, por lo que solo un proceso podía ejecutar esa cola; admitía `--once` y `--poll-interval`.
- `run_next_ai_job()` elegía un registro `QUEUED` con `select_for_update(skip_locked=True)`, pero salía de la transacción antes de cambiar su estado. El job seguía visible como `QUEUED` y el bloqueo de fila ya se había liberado. Con consumidores concurrentes, varios podían seleccionar el mismo job. `process_ai_generation_job()` lo volvía a bloquear y solo uno invocaba el proveedor; los demás podían desperdiciar consultas y competencia por la cola.
- `process_ai_generation_job()` fijaba `RUNNING`, `started_at` e incrementaba `attempts` antes de invocar el adaptador; la llamada Gemini recibe `timeout=30.0`. Una caída abrupta podía dejar el job permanentemente `RUNNING`.
- Los jobs tienen estados persistidos `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED`, campo `attempts` y tiempos `started_at`/`finished_at`. No requieren nuevos campos para este bloque.
- B6.1 crea `AIGenerationBatch` y `AIGenerationBatchItem`, pero cada elemento sigue siendo un `AIGenerationJob`; el estado agregado del lote se deriva de esos jobs.

## 2. Comportamiento implementado

### 2.1 Reclamo atómico

`run_next_ai_job()` ahora, en una única transacción PostgreSQL:

1. Selecciona el job `QUEUED` más antiguo con `select_for_update(skip_locked=True)`.
2. Cambia inmediatamente su estado a `RUNNING`, fija `started_at` e incrementa `attempts`.
3. Confirma la transacción y solo entonces llama a `process_ai_generation_job(..., already_claimed=True)`.

El procesamiento interno reconoce el job ya reclamado y no repite el cambio de estado ni el incremento. La ruta directa existente `process_ai_generation_job(job_id)` todavía admite jobs `QUEUED` y conserva su contrato de B5.1, incluido el modo síncrono de desarrollo. Un consumidor que no encuentre trabajos retorna `False`.

La transacción que reclama el job es breve y no abarca la llamada a Gemini. `skip_locked` junto con el cambio de estado dentro de la transacción permite que consumidores concurrentes reclamen filas diferentes. La aceptación humana continúa separada: `RUNNING` solo significa que el proveedor está siendo consultado, nunca que la salida esté aprobada.

### 2.2 Límite de concurrencia y vida del proceso

- El comando admite `--concurrency N`; su valor predeterminado es `1` para mantener el comportamiento anterior hasta que el despliegue habilite más capacidad.
- `TESISMCP_AI_WORKER_MAX_CONCURRENCY` limita el máximo permitido y, si no se configura, es `4`. Valores menores que uno o un `N` superior al máximo se rechazan al arrancar.
- La concurrencia se implementa con un grupo acotado de hilos dentro de un único proceso. El advisory lock global permanece: no hay varios procesos ni réplicas independientes consumiendo la cola a la vez.
- Cada hilo cierra conexiones Django obsoletas antes/después de las consultas y del procesamiento para no compartir una conexión DB entre hilos.
- `--once` conserva el significado de procesar a lo sumo un job y terminar; por claridad se rechaza `--once --concurrency N` si N no es 1.
- `--poll-interval` debe ser positivo. Al recibir Ctrl+C, el worker deja de reclamar jobs y espera a que terminen los que ya están en curso antes de liberar el advisory lock.
- Compose añade `ai_worker` separado del worker documental. `TESISMCP_AI_WORKER_CONCURRENCY` controla su valor ejecutado (por defecto 1); proveedor, modelo y clave Gemini se inyectan por variables de entorno, sin guardarlos en el repositorio. El proveedor sigue deshabilitado por defecto.

Este límite regula cuántas llamadas simultáneas puede iniciar esta instalación, pero **no es un presupuesto monetario**: no se calculan precios ni se impone un tope USD. Los límites de cuotas del proveedor y un eventual presupuesto son decisiones/configuraciones externas. Los lotes B6.1 continúan limitados por sus contratos existentes.

### 2.3 Recuperación tras caída

Después de adquirir el advisory lock, el comando transforma los jobs que aún figuran `RUNNING` en `FAILED` con `error_code=WORKER_INTERRUPTED` y un mensaje que solicita una nueva generación explícita si se desea volver a intentar. El procedimiento bloquea las filas y no toca otros estados.

No se reencola ni se reintenta automáticamente. Si el proceso cae después de que el proveedor generó una respuesta, pero antes de persistirla, no se sabe si la llamada fue facturada; reintentar de forma automática podría cobrar una segunda vez. El job fallido conserva `attempts` y el usuario puede pedir otra generación, que creará un job nuevo conforme al contrato actual.

La recuperación es segura al inicio porque el advisory lock global garantiza que el worker anterior ya no consume la cola. No existe heartbeat ni lease temporal: en este diseño no se ejecuta recuperación periódica mientras el worker vivo mantiene el lock.

## 3. Compatibilidad y límites

- No se añade migración, entidad ni endpoint. No cambia el esquema ni el payload HTTP.
- B6.1 continúa usando los mismos jobs para cada miembro de lote; los jobs elegibles de cualquier lote o solicitud individual comparten la cola y el límite global configurado.
- `cancel_ai_job` sigue cancelando únicamente `QUEUED`. Una vez reclamado como `RUNNING`, la cancelación se rechaza; B6.2 no interrumpe una petición HTTP ya enviada al proveedor.
- La validación local, la comprobación del contexto antes y después de la llamada, el hash y la aceptación explícita siguen en `ai_jobs.py`.
- La concurrencia afecta solo trabajos que ya son elegibles y no dependen de otros pasos. El sistema no ignora dependencias del workflow para llenar los slots.
- B6.3 queda a cargo de resumir/sintetizar varias salidas mediante referencias y hashes, con preview/diff y aceptación humana. B6.2 no combina salidas ni escribe en el documento.

## 4. Verificaciones focalizadas esperadas

Las pruebas de B6.2 cubren:

1. Dos consumidores PostgreSQL reclaman jobs distintos; cada fila cambia a `RUNNING` una vez y suma un único intento.
2. Jobs `RUNNING` abandonados pasan una sola vez a `FAILED/WORKER_INTERRUPTED`, conservan el número de intentos y nunca se reencolan automáticamente.
3. `--once` rechaza concurrencia mayor a uno.
4. El comando rechaza concurrencia no positiva o mayor al máximo configurado.
5. Se conservan las pruebas existentes de validación, contexto obsoleto, aceptación/rechazo, permisos y contratos de B5.1/B6.1.

La puerta integral del proyecto es el criterio final; esta especificación no afirma que la concurrencia del proveedor real se haya ejercitado sin credenciales Gemini.

## 5. Archivos modificados

- `backend/thesis/services/ai_jobs.py`: reclamo y recuperación de jobs.
- `backend/thesis/management/commands/run_ai_worker.py`: límite configurable, hilos, lock y ciclo de vida.
- `backend/config/settings.py`: máximo de concurrencia de despliegue.
- `backend/thesis/tests/test_ai_generation.py`: regresiones de reclamo, recuperación y `--once`.
- `compose.yaml`: servicio de worker IA separado.

No se espera modificación de modelos o migraciones. Si `makemigrations --check` indica lo contrario, detenerse y explicar el delta antes de aceptar una migración no contemplada.
