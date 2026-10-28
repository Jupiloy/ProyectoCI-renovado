# Arquitectura BYOA: web, API, agente del usuario y MCP

**Estado (28/10/2026):** arquitectura objetivo y primer slice BYOA local implementado en backend. Antigravity CLI es el primer runtime. La UI BYOA y ejecución real de CLI no están verificadas; el soporte no es automáticamente universal.

## 1. Decisión en una frase

La web de TesisMCP inicia y presenta el trabajo; el backend autentica, autoriza, coordina y guarda; el agente que conecta el usuario analiza usando el modelo que tenga disponible; MCP le permite llamar herramientas y consultar datos de TesisMCP.

```text
Tesista
  │ pide una tarea y revisa el resultado
  ▼
Web TesisMCP ── API de TesisMCP ── Backend / cola de tareas
                                      │ asigna trabajo y recibe avances
                                      ▼
                              Conector del agente
                                      │ entrega tarea y resultado
                                      ▼
                              Agente del usuario
                                │             ▲
                                │ MCP         │ herramientas / resultados
                                ▼             │
                         Servidor MCP TesisMCP
                                      │
                                      ▼
                         Servicios y datos autorizados
```

La API de TesisMCP y MCP pueden terminar usando los mismos servicios internos. Son interfaces distintas para consumidores y propósitos distintos; no se debe duplicar autorización ni lógica académica.

## 2. No confundir estas tres cosas

| Concepto | Quién lo usa en este diseño | Para qué sirve | Ejemplo |
|---|---|---|---|
| **API de TesisMCP** | La web, el conector y otros clientes de la plataforma | Iniciar una tarea, consultar su estado, recibir eventos y guardar una decisión o resultado | `POST /api/v1/.../tasks` |
| **API del proveedor de IA** | Un programa que invoca directamente un modelo alojado por un proveedor | Enviar mensajes al modelo y recibir una respuesta | Gemini API o Anthropic API con credenciales propias |
| **MCP** | El agente como cliente MCP | Descubrir y llamar herramientas que TesisMCP ofrece, con identidad y permisos | `buscar_documentos`, `leer_fuente`, `consultar_estado` |

Una **API** es una interfaz de programación general. La API del producto y la API del modelo son servicios diferentes aunque ambas se llamen API. MCP también define una interfaz y un protocolo, especializado en cómo los clientes de IA descubren y usan herramientas, recursos y prompts.

El usuario aporta un agente/runtime compatible. Esto no garantiza que toda suscripción comercial de consumo pueda usarse desde TesisMCP. Si el agente depende de una API de proveedor, su acceso, credenciales y posibles costos siguen las condiciones de ese proveedor. TesisMCP no debe pedir la contraseña del usuario para una aplicación de IA.

## 3. Recorrido concreto de una tarea

Ejemplo: el tesista pulsa **“Analizar mis antecedentes”** en un proyecto.

1. **La web crea la solicitud mediante la API de TesisMCP.** Envía el identificador del proyecto, el tipo de tarea, las entradas seleccionadas, versiones esperadas e idempotency key. No envía una identidad elegida por el modelo.
2. **El backend valida y registra.** Identifica la sesión, comprueba la membresía y los permisos, fija las versiones/contexto que se analizarán y crea un job. Devuelve un `job_id` y su estado inicial.
3. **El coordinador asigna la tarea al agente conectado.** El conector recibe instrucciones y datos mínimos. El canal de despacho es una capacidad de TesisMCP; no se debe asumir que aparece automáticamente por instalar un servidor MCP.
4. **El agente razona con su modelo.** Durante el análisis, el agente llama al servidor MCP de TesisMCP para buscar documentos o pasajes que el usuario puede consultar.
5. **El servidor MCP aplica permisos.** Resuelve la identidad del token autenticado y llama los servicios compartidos del backend. El modelo no puede elegir otro `user_id` ni acceder a proyectos ajenos.
6. **El conector devuelve avances y el resultado.** El backend valida el esquema, registra procedencia, advertencias, agente/runtime declarado, versiones de entrada y resultado. Un resultado se guarda como propuesta, no como texto aprobado.
7. **La web muestra el progreso y la propuesta.** La interfaz consulta estado/eventos con la API. El tesista puede revisar, aceptar, rechazar o cancelar según la operación. La aprobación del asesor sigue siendo un estado distinto.

```text
Web ──(API: crear job)──> Backend/cola ──(despacho)──> Conector ──> Agente
Web <──(API: estado/eventos)── Backend <──(resultado)── Conector <── Agente
                                                          │
                                  Agente ──(MCP: herramientas)──> MCP TesisMCP
```

## 4. Responsabilidad de cada componente

### Web

- Presenta proyectos, documentos, prompts, tareas y permisos.
- Inicia, cancela y consulta trabajos por la API del producto.
- Muestra estados, eventos, fuentes y resultados estructurados.
- Presenta cambios propuestos para revisión humana antes de escribir en contenido canónico.

### Backend y API de TesisMCP

- Es la fuente de verdad para identidad, permisos, versiones, jobs y resultados.
- Valida que el usuario pueda usar el proyecto y los recursos.
- Crea jobs idempotentes, registra estado y controla timeout/cancelación/reintentos.
- Despacha el job a un conector compatible y valida su respuesta.
- Publica cambios de estado para la web (por ejemplo, SSE o WebSocket) o permite consultarlos mediante polling.
- Comparte los servicios de dominio con el adaptador MCP.

### Conector o gateway del agente

- Vincula un runtime/agente concreto con una cuenta TesisMCP.
- Recibe trabajos, inicia su ejecución, entrega eventos y retorna resultados.
- Mantiene una conexión saliente autenticada hacia TesisMCP en instalaciones locales o redes con NAT/firewall; no exige exponer un puerto entrante del usuario.
- Limita y valida mensajes, conserva `job_id`/correlation id y no toma decisiones de permisos de proyecto.
- Es un adaptador por runtime/proveedor; no existe una integración universal automática con todos los agentes comerciales.

### Agente del usuario

- Interpreta la tarea, planifica y llama al modelo disponible en su runtime.
- Decide cuándo necesita herramientas y llama al servidor MCP de TesisMCP.
- Devuelve salida estructurada, referencias a herramientas/fuentes utilizadas y advertencias.
- No escribe directamente en la base de datos ni puede aprobar su propia salida.

### Servidor MCP de TesisMCP

- Expone herramientas tipadas sobre servicios de dominio existentes.
- Autoriza cada llamada usando la identidad del token/conexión, además del acceso al proyecto.
- Devuelve solo los datos permitidos y mantiene procedencia/errores de dominio.
- No es el modelo, no es el agente, no es una API de Gemini/Claude y no gestiona por sí solo la cola de trabajos de la interfaz.

## 5. ¿Qué hace MCP y qué no hace aquí?

MCP es el puente **desde el agente hacia las capacidades de TesisMCP**. Por ejemplo, permite que el agente busque fuentes, lea extractos, consulte una tarea o use una operación expresamente autorizada.

La web necesita además una operación **desde la interfaz hacia el trabajo del agente**: crear un job, asignarlo a una conexión, recibir progreso y recuperar el resultado. Esa coordinación pertenece a la API/orquestador de TesisMCP y al conector del runtime.

MCP puede transportar mensajes cliente-servidor y Streamable HTTP ofrece respuestas/eventos. Aun así, eso no significa que cualquier agente exponga una interfaz genérica para aceptar una tarea arbitraria iniciada por nuestra web. El conector adapta el ciclo de trabajo al runtime concreto. No asumir que MCP por sí solo inicia o aloja al agente.

## 6. Arquitectura local y migración a nube

### Prototipo local

- Django/PostgreSQL y el servidor MCP corren localmente.
- La web llama a la API de TesisMCP usando la sesión Django.
- Un conector local enlaza el job con un agente/runtime compatible. Puede ejecutarse como proceso separado y conectarse al backend local.
- El agente llama al servidor MCP local usando las credenciales asociadas a la identidad autorizada.
- La identidad web y la identidad MCP deben quedar vinculadas explícitamente. No pasar `user_id` desde el prompt.

El backend local ahora dispone de `AgentConnection`, credenciales distintas con hashes y revocación, alcance a un proyecto, modo `BYOA` en `AIGenerationJob`, endpoints autenticados de claim/heartbeat/evento/completado/fallo y el comando `run_byoa_connector` para invocar Antigravity CLI. La salida vuelve a validarse en Django y queda pendiente de aceptación humana. La UI de conexión/generación no está integrada al frontend y no se ha probado una llamada real con `agy` instalado y autenticado. El servidor MCP permanece en stdio local; el camino server-side Gemini sigue opcional y separado.

### Despliegue en nube (recomendado)

- Publicar la API de la aplicación y el endpoint MCP remoto bajo HTTPS.
- Para MCP remoto, priorizar Streamable HTTP y autorización OAuth siguiendo el protocolo MCP; validar audiencia, permisos/scopes, expiración, revocación y origen.
- Implementar un gateway/orquestador de jobs persistente. Los conectores de usuario mantienen una conexión saliente autenticada para recibir jobs y reportar avances/resultados. Una integración con agente alojado puede usar un adaptador de API/webhook del proveedor si su plataforma lo permite.
- Usar OAuth de TesisMCP para vincular una cuenta y conceder acceso limitado al proyecto. Ese OAuth no autoriza automáticamente el uso de Gemini, Claude u otro modelo.
- Si el runtime requiere credenciales de proveedor, guardarlas en el runtime del usuario cuando sea posible. Si TesisMCP debe almacenarlas para una integración concreta, cifrarlas, limitar su uso y permitir revocarlas; nunca enviarlas al navegador, a logs ni al modelo como parte del prompt.
- Separar credenciales de API de TesisMCP, credenciales MCP y credenciales del proveedor/modelo. Tienen audiencias y propósitos distintos.
- Incorporar timeout, cancelación, recuperación de desconexión, límites de tamaño, reintentos idempotentes, control de cuotas y auditoría antes de exponerlo públicamente.

No abrir el puerto de la computadora del usuario al internet como solución general. El conector debe iniciar la conexión saliente o usar una integración alojada autorizada.

## 7. Vía opcional server-side existente

B5.1 dispone de jobs y un adaptador Gemini que llama a un proveedor configurado por el servidor. Es una vía distinta: en ella TesisMCP, no el agente del usuario, llama al modelo. Se conserva como opción explícita para desarrollo o para un servicio institucional futuro; no es el significado de BYOA ni es requisito de la arquitectura principal.

En esa vía, la clave del proveedor debe estar en el entorno protegido del backend/worker. No se expone en frontend. Mantenerla deshabilitada por defecto mientras no exista una decisión de producto y configuración validada.

## 8. Reglas de seguridad y consistencia

- La sesión de la web autentica al usuario ante TesisMCP; la autorización del agente a TesisMCP es una credencial distinta, revocable y vinculada a ese usuario.
- Cada petición y herramienta comprueba membresía y permiso sobre proyecto/recurso. Una credencial identifica; no concede automáticamente acceso a todos los proyectos.
- No confiar en `user_id`, rol, `project_id`, citas ni estado de aprobación declarados por el modelo sin cotejarlos con contexto autorizado y servicios.
- Versionar el contexto usado por el job. Si cambian documentos o contenido durante su ejecución, marcar el resultado como potencialmente obsoleto y requerir revisión/rebase.
- Una salida del agente es una propuesta. La aceptación del tesista, revisión del asesor y aprobación institucional, si aplica, son estados independientes.
- Registrar qué runtime/proveedor/modelo se declaró, cuándo se ejecutó, entradas referenciadas, herramientas llamadas, salida y errores. Si el cliente no informa un dato, marcarlo desconocido; no inferirlo.

## 9. Etapas de implementación y estado

1. **Contrato y vínculo local — implementados:** `AIGenerationJob` separa `SERVER` y `BYOA`; `AgentConnection` es revocable y acotada por proyecto.
2. **Despacho y autenticación — implementados en código:** claim, heartbeat, eventos, cierre del job y token MCP ligado a la conexión.
3. **Primer adaptador local — implementado, no ejecutado en vivo:** Antigravity CLI vía `run_byoa_connector`; requiere instalación, autenticación y permiso MCP en la máquina.
4. **Adaptadores adicionales — extensión prevista:** registrar una implementación de `AgentRuntimeAdapter` por runtime; no hay compatibilidad universal automática.
5. **Integración web — pendiente:** conexión/listado/revocación, selección de modo BYOA, progreso, cancelación y salida.
6. **Cloud — pendiente:** API HTTPS, MCP remoto autorizado, cola durable, gateway seguro de conectores, control de cuotas, desconexiones y pruebas de seguridad/privacidad.

El backend ya tiene contrato independiente del runtime, registry de adaptadores y primer adaptador local Antigravity. La integración visual y la ejecución real siguen pendientes. La vía de proveedor server-side puede conservarse como modo opcional, claramente identificado.

## 10. Estado de implementación local y primer runtime

El código implementa el contrato de conexión, seguridad y ciclo de job descrito en [Contrato del conector BYOA](contrato_conector_byoa.md), con Antigravity CLI local como primer runtime. La interfaz del frontend, una ejecución real autenticada, permisos MCP de la máquina usuaria y una integración de segundo runtime siguen sin comprobarse. Otros runtimes implementarán adaptadores pequeños contra el mismo contrato; MCP proporciona las herramientas de TesisMCP.

## 11. Criterios de aceptación de esta arquitectura

- La web puede crear un job autenticado y ver sus estados/resultados usando la API de TesisMCP.
- Un conector registrado recibe jobs solo para la identidad/proyectos autorizados y puede revocarse.
- El agente puede llamar herramientas MCP para consultar recursos permitidos con la misma autorización de dominio.
- Dos usuarios no pueden leer tareas, resultados, documentos ni eventos del otro.
- Una desconexión no duplica silenciosamente una operación ni convierte un trabajo perdido en exitoso.
- Los resultados quedan como propuestas trazables; la web nunca presenta generación como aprobación.
- Puede cambiarse el runtime/agente sin cambiar reglas de permisos ni modelo de dominio.
- La documentación distingue BYOA del adaptador Gemini server-side y de las APIs comerciales de modelos.

## Fuentes del protocolo

- [MCP: transportes](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP: autorización](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
