# Contrato del conector BYOA y adaptador Antigravity

**Estado (28/10/2026):** contrato y primer adaptador local implementados en backend. `AgentConnection`, los jobs BYOA, los endpoints de conector y `run_byoa_connector` cubren la conexión Antigravity CLI. La interfaz de adaptadores permite añadir runtimes, pero solo Antigravity está registrado. No se ha probado una ejecución real en una instalación Antigravity autenticada ni se ha integrado la gestión BYOA en la interfaz web.

## Objetivo

Permitir que la web de TesisMCP solicite una tarea al agente que el usuario ya utiliza, reciba progreso y presente una salida estructurada para revisión. La interfaz web no habla con el modelo directamente. El backend conserva identidad, autorización del proyecto, versiones, estado e historial. El agente aporta el razonamiento y utiliza herramientas de TesisMCP mediante MCP.

La frontera común debe permitir integrar distintos runtimes sin hacer que cada runtime cambie la API académica, el modelo de permisos o el frontend. No existe un adaptador que vuelva compatibles automáticamente todas las aplicaciones comerciales: cada runtime requiere un mecanismo concreto para iniciar una tarea y devolver su resultado.

## Responsabilidades y protocolos

| Frontera | Mecanismo | Responsabilidad |
| --- | --- | --- |
| Navegador → TesisMCP | API HTTP autenticada con sesión Django y CSRF | Crear/cancelar tareas y consultar estado y propuestas. |
| Conector → TesisMCP | API HTTP con credencial propia, revocable y ligada a una cuenta | Recibir tareas asignadas, reportar progreso y devolver resultado. |
| Agente → herramientas TesisMCP | MCP | Descubrir y ejecutar herramientas autorizadas. MCP no inicia por sí mismo una tarea web. |
| Conector → runtime de IA | Adaptador por runtime | Iniciar la tarea, traducir eventos y normalizar errores/salidas. |
| Runtime ↔ otro agente, si aplica | A2A cuando ambos extremos lo soportan | Delegación entre agentes. No reemplaza MCP para herramientas ni es requisito de la primera integración. |

La API de TesisMCP debe mantener un contrato de tarea independiente del adaptador. El adaptador no contiene reglas de tesis ni decide permisos.

## Modelo común de tarea

La primera versión delegada debe aprovechar el ciclo de propuesta/aceptación existente de `AIGenerationJob` cuando sea compatible con el código actual. Antes de reutilizarlo, la implementación debe separar explícitamente ejecución `SERVER` de ejecución `BYOA`: el worker server-side no debe reclamar jobs BYOA y el conector no debe reclamar jobs server-side. No se debe crear una segunda máquina de aceptación ni duplicar validadores de outputs.

Cada tarea BYOA debe conservar como mínimo:

- `job_id`, proyecto, usuario solicitante, tarea metodológica y clave de idempotencia.
- Recorrido, prompt, esquema de salida, contexto autorizado y sus versiones/hash al momento de encolar.
- Conexión/runtime de destino, estado, timestamps, intentos y correlation id.
- Eventos acotados de progreso, código de error normalizado y procedencia declarada por el runtime.
- Resultado validado contra el esquema del backend y estado `PENDING_ACCEPTANCE` hasta decisión humana.

Estados mínimos: `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED`. La propuesta aceptada/rechazada es un estado independiente de la ejecución. Un mensaje de progreso del runtime nunca equivale a resultado validado ni a aceptación.

El conector reclama una sola tarea con lease de 300 segundos, lo renueva mediante heartbeat y completa/falla usando el `job_id` autenticado por la conexión. El backend persiste `RUNNING` en el claim; los jobs con lease vencido pasan a `FAILED/LEASE_EXPIRED` y requieren una nueva solicitud explícita, sin reintento automático para evitar duplicar costos. La cancelación de un job BYOA en ejecución se observa en el siguiente heartbeat.

### Envelopes del protocolo común (versión 1)

La API del conector usa JSON versionado; los nombres de runtime no alteran la forma del job.

**Job reclamado** — el backend devuelve solo la tarea asignada a la conexión autenticada:

```json
{
  "protocol_version": "1",
  "runtime": "ANTIGRAVITY_CLI",
  "job_id": "uuid",
  "correlation_id": "uuid",
  "lease_expires_at": "RFC3339 timestamp",
  "task": {
    "project_id": "uuid",
    "task_id": "P01 o USR_...",
    "prompt_text": "texto fijado por el backend",
    "prompt_version": 1,
    "input_data": {},
    "context_snapshot": {},
    "context_sha256": "sha256",
    "output_schema": {}
  }
}
```

El conector obtiene el sobre desde un endpoint autenticado de claim; no puede enviar un `project_id` para escoger un job ajeno. Los identificadores de ejemplo no son valores persistidos. La implementación debe limitar el tamaño del sobre y considerar la sensibilidad del contexto antes de transmitirlo al runtime.

**Evento de progreso** — una conexión solo puede emitir eventos para un job que tenga reclamado:

```json
{
  "protocol_version": "1",
  "event_id": "uuid",
  "job_id": "uuid",
  "correlation_id": "uuid",
  "sequence": 1,
  "type": "started | progress | tool_activity | completed | failed | cancelled",
  "created_at": "RFC3339 timestamp",
  "payload": {}
}
```

El backend limita cantidad, tamaño y campos de eventos permitidos. La secuencia se asigna al persistir; el conector no elige su número. `tool_activity` puede identificar el nombre de una herramienta y referencias de fuente, pero no debe exponer razonamiento interno ni secretos. El progreso es informativo, no una escritura del proyecto.

**Resultado final** — solo `completed` incluye una propuesta y procedencia declarada:

```json
{
  "protocol_version": "1",
  "runtime": "ANTIGRAVITY_CLI",
  "job_id": "uuid",
  "correlation_id": "uuid",
  "output_data": {},
  "provenance": {
    "runtime": "ANTIGRAVITY_CLI",
    "model": "identificador declarado o null",
    "tool_calls": []
  },
  "warnings": []
}
```

El backend comprueba `output_data` con el esquema guardado al encolar y computa el hash de lo que persiste. Los campos de procedencia declarados no son evidencia criptográfica de que el modelo o herramientas indicados se hayan usado; se guardan como metadatos reportados por el runtime. El backend no acepta que el runtime envíe estados de aceptación.

Códigos de error estables para el canal del conector incluyen `UNAUTHENTICATED`, `CONNECTION_REVOKED`, `JOB_NOT_ASSIGNED`, `LEASE_EXPIRED`, `JOB_NOT_CANCELLABLE`, `INVALID_EVENT`, `OUTPUT_INVALID`, `RUNTIME_UNAVAILABLE`, `RUNTIME_TIMEOUT` y `RUNTIME_FAILED`. La implementación puede añadir códigos sin cambiar el significado de los existentes. Los mensajes visibles al usuario no incluyen stack traces ni datos de credenciales.

## Identidad y seguridad

Son credenciales distintas y no se deben intercambiar:

1. Cookie de sesión web: identifica a la persona en el navegador.
2. Secreto del conector: identifica una instalación/runtime vinculado a esa cuenta; se muestra una sola vez, se guarda hasheado, vence y puede revocarse.
3. Token MCP: autentica las llamadas del agente a herramientas MCP; debe quedar ligado al usuario/conexión y no autoriza proyectos automáticamente.
4. Credenciales del proveedor o suscripción del runtime: permanecen bajo el control de Antigravity/runtime; TesisMCP no pide la contraseña personal ni copia credenciales al navegador.

Cada operación web verifica sesión, CSRF cuando corresponde, rol y acceso al proyecto mediante servicios actuales. Cada operación del conector deriva identidad de su secreto autenticado, verifica que el job esté asignado a esa conexión y vuelve a comprobar pertenencia/permisos del usuario. Nunca acepta `user_id`, rol o permisos como autoridad desde el payload o prompt.

No registrar secretos, prompts con material sensible ni documentos completos en logs. Limitar tamaño y frecuencia de mensajes/eventos. Restringir progreso a campos tipados, sanear texto y evitar que una salida de agente actualice directamente datos canónicos.

## Adaptador Antigravity inicial

La primera implementación apunta a Antigravity CLI en modo local. Su documentación oficial describe ejecución headless, eventos `stream-json` y salida estructurada mediante `--json-schema`; también documenta integración MCP para herramientas. La SDK de Python es otra vía, pero su inicio requiere una credencial Gemini API o Vertex y no debe confundirse con reutilizar automáticamente la cuenta de la aplicación Antigravity. Por eso se elige primero la CLI ligada al runtime local del usuario. Antes de invocar, la implementación debe confirmar el binario, autenticación, cuota y opciones disponibles en esa máquina; si la CLI no está instalada o autenticada, informar `RUNTIME_UNAVAILABLE` sin cambiar a una API de modelo del servidor.

El registro de runtimes vive en `backend/thesis/agent_runtimes/`; `AgentRuntimeAdapter` define resolución de ejecutable, construcción de comando, configuración MCP, parseo de eventos y detección de permisos denegados. `AntigravityCliAdapter` es el único adaptador registrado hoy. Añadir otro runtime requiere implementar esta interfaz, registrar el código de runtime y completar su mecanismo de configuración MCP; el formato común de jobs no cambia. La interfaz vigente expone:

- `start(task_envelope) -> runtime_handle`
- `read_events(runtime_handle) -> iterable[progress | result | error]`
- `cancel(runtime_handle)`
- `normalize_result(raw_result, output_schema) -> structured_result`

El adaptador pasa a Antigravity la instrucción del trabajo y el esquema de respuesta; no le entrega un token con acceso general. La configuración MCP de Antigravity usa credenciales generadas para la conexión del usuario, con alcance mínimo. No escribir tokens en archivos versionados, salida de consola ni mensajes de error.

Si la interfaz oficial de Antigravity no permite invocación/seguimiento desde el conector como se espera, documentar la limitación y detener ese adaptador en el punto de integración. No simular que se ejecutó el agente ni sustituirlo sin avisar por Gemini API, Claude API u otro proveedor.

## Interfaz intercambiable para otros runtimes

La capa común expone operaciones de plataforma, no nombres de proveedores:

- `register_connection`, `revoke_connection`, `health`.
- `claim_job`, `report_progress`, `complete_job`, `fail_job`, `cancel_job`.
- `start`, `events`, `cancel` en el adaptador local del runtime.

Cada runtime implementa ese adaptador usando el mecanismo disponible: CLI, SDK, proceso sidecar, webhook o A2A si está soportado en ambos extremos. MCP se configura aparte como acceso del agente a herramientas TesisMCP. El contrato de jobs, los esquemas y la presentación del frontend no cambian al añadir un runtime.

## Alcance de la primera entrega

1. Registrar y revocar conexiones por proyecto mediante sesión autenticada.
2. Elegir conexión al crear un job BYOA y mantenerlo separado del modo `SERVER`.
3. Reclamar jobs, renovar leases, reportar eventos y devolver resultados con credencial propia.
4. Ejecutar Antigravity CLI mediante su adaptador registrado cuando esté instalado y autenticado.
5. Validar la respuesta con contratos backend y dejarla pendiente de aceptación humana.
6. Serializar progreso, resultado, error y procedencia para su lectura desde la API de jobs.
7. Mantener la generación server-side sin fallback implícito.

La interfaz web aún no expone el alta/selección/revocación de conexiones BYOA ni el control del conector local. La ruta real de Antigravity tampoco se ha ejecutado aquí.

Fuera de esta primera entrega: nube, A2A obligatorio, soporte universal ya instalado para todos los agentes, OAuth de todos los proveedores, sincronización en tiempo real avanzada, envío de secretos del proveedor a TesisMCP y aprobación automática.

## Criterios de aceptación

- El backend puede distinguir de forma persistente un job `SERVER` de uno `BYOA` y cada worker consume únicamente su modo.
- Una cuenta puede ver y revocar solo sus propias conexiones; el secreto crudo no vuelve a aparecer después de emitirse.
- Un conector no puede reclamar un job ajeno, de otra conexión o de otro proyecto.
- Las operaciones del agente MCP se autorizan con la identidad vinculada y las reglas de proyecto existentes.
- La idempotencia evita jobs duplicados; el lease evita dobles reclamos concurrentes.
- Los eventos no permiten escribir contenido canónico y el resultado pasa validación del backend antes de mostrarse como propuesta.
- Si Antigravity CLI no está disponible, se informa el bloqueo real sin fingir una ejecución.
- La ejecución server-side no se activa como fallback y conserva su comportamiento opt-in.

## Referencias de protocolo

- [Antigravity CLI headless](https://www.antigravity.google/docs/cli/headless/)
- [MCP transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
- [A2A specification](https://a2a-protocol.org/dev/specification/agent-card/)
