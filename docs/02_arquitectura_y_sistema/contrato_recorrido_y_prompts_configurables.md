# Contrato de backend: recorrido y prompts configurables por proyecto

> **Actualización:** las referencias históricas a P20 solo APA describen un corte anterior. P20 ahora admite IEEE y APA_7; no se reescribieron recorridos publicados y falta comprobación completa del formato.

**Estado:** contrato de producto; B5 tiene implementación parcial y B5.1 implementa el ciclo de jobs, worker, validación, aceptación/rechazo y adaptador Gemini. Las tareas `USR_...` pueden guardar resultados enviados por el cliente y validar `output_schema`. El proveedor está deshabilitado por defecto y la llamada real requiere credenciales; el mock solo funciona en `DEBUG`. Consultar el [paquete de implementación Gemini B5.1](./implementacion_adaptador_gemini_b5_1.md) y [generación IA y resultados](./especificacion_generacion_ia_y_resultados.md). Complementa la [propuesta de orden metodológico](../03_metodologia_y_prompts/propuesta_orden_metodologico_revisado.md); no la convierte en una secuencia obligatoria.

## 1. Resultado que debe poder mostrar el equipo

En un proyecto de prueba, el tesista autenticado obtiene una copia de la plantilla inicial, edita el texto de un prompt, agrega otro, desactiva uno y cambia el orden visible de tareas. La plataforma muestra antes de publicar las dependencias y los efectos; conserva la versión anterior y permite comparar/restaurar. Un asesor del mismo proyecto puede consultar y comentar el recorrido propuesto sin adquirir permiso implícito para alterar datos o aprobar una tesis. Una ejecución o revisión futura señala la versión de recorrido/prompt usada. Una regla protegida sigue activa aunque el usuario borre del texto del prompt su recordatorio.

**No dar por demostrado el objetivo solo por almacenar un JSON o cambiar el orden de una lista.** La API que guarda P01–P32 debe respetar el recorrido publicado y los prerrequisitos reales cuando se anuncie como configurable. Hasta entonces la interfaz debe decir que el cambio es de planificación/prompt, no de ejecución del paso.

## 2. Hechos del código actual que gobiernan la migración

- `backend/thesis/step_catalogue.py` contiene P01–P32 con capítulo, nombre, objetivo y entradas declaradas; no contiene un grafo de dependencias explícito.
- `backend/thesis/services/steps.py::save_step` valida el contrato Pydantic y exige que el P inmediatamente anterior esté `COMPLETED`. `submit_chapter` exige todos los P del capítulo, incluso los que debieran ser condicionales.
- `backend/thesis/models/chapters.py::StepProgress` guarda un `step_code` de longitud 3 y un único `output_json` por proyecto/paso. `ChapterRevision` ya registra workflow/versión, texto de prompt y versión de prompt; todavía no conserva un snapshot estructurado de su `output_json`. `ResearchProfile.lock_version` y `idempotency_key` protegen guardados actuales.
- `WorkflowTaskExecution` guarda resultados de tareas personalizadas `USR_...` y `ChapterRevision` registra prompt/recorrido usados; el endpoint `/workflow/tasks/{task_id}/execute` recibe `output_data` desde el cliente. Esto es persistencia de una salida externa, no generación hecha por el backend.
- Los materializadores contienen dependencias ocultas: P06 y P09 leen P04; P10/P11 leen P09; P16 lee P15 y compara la cuenta PRISMA; P20 lee P16; P25 lee P11. Antes de adelantar alguno, el agente debe localizar todas las lecturas de otras salidas, no solo cambiar la comprobación de `save_step`.
- El router `backend/thesis/api/projects.py` expone `PUT /projects/{project_id}/steps/{step_code}` con `content_md`, `output_data`, `expected_version` e `idempotency_key`. Los prompts MCP actuales son plantillas de código, no datos editables por proyecto. Las pruebas actuales demuestran la secuencia legada; no demuestran el nuevo recorrido.

## 3. Tres capas separadas

| Capa | Puede configurar el usuario | Quién la ejecuta/valida | Ejemplo |
|---|---|---|---|
| Presentación y prompts | Texto, ejemplos, tono, orden visible, nombre de tarea, alternativas, activación de tareas opcionales. | Servicio de configuración con versión y permisos. | Mover una búsqueda exploratoria antes del título o agregar un prompt de entrevista. |
| Dependencias académicas del proyecto | Proponer conexiones entre tareas, elegir enfoque/rama, declarar entradas y revisión deseada; publicar solo si pasa validación. | Servicio de grafo y contratos por tarea. | Poner antecedentes en paralelo, con contexto provisional versionado. |
| Núcleo protegido | No editable por prompt ni por reordenamiento. | Servicios de dominio, permisos, base de datos y reglas institucionales versionadas. | Identidad, evidencia, datos reales, consentimiento aplicable, aprobación humana, historial inmutable. |

Un prompt es una instrucción para producir una **propuesta**; no equivale al contrato estructurado de salida ni a una norma UTP. Cambiar el orden visual tampoco cambia las dependencias de ejecución por sí mismo.

## 4. Política de publicación y ejecución

1. Cada proyecto parte de una plantilla base versionada. El usuario crea una **versión borrador** separada de la versión publicada. Debe poder ver diff y restaurar una versión histórica sin mutarla.
2. La versión publicada identifica tareas estables, posición visible, prompt versionado, estado activo/opcional, condiciones de rama, dependencias tipadas y fuente de cada regla. La implementación actual reserva IDs `USR_...` para tareas personalizadas y conserva P01–P32 como pasos con contrato fijo.
3. Validación antes de publicar: referencias a tareas existentes, IDs únicos, grafo sin ciclos, rama/condición consistente, ausencia de dependencias imposibles, permisos, límites de texto, ausencia de control protegido editado. Una lista con orden diferente pero grafo igual es válida.
4. Si se mueve una tarea antes de obtener sus entradas, se puede guardar como planificación o borrador de prompt. La ejecución estructurada retorna un bloqueo explícito con los prerrequisitos faltantes; no fabrica entradas. Tareas independientes pueden ejecutarse en paralelo con una versión de contexto fijada.
5. La desactivación no borra salidas, revisiones, comentarios ni aprobaciones anteriores. Una tarea obligatoria para un trámite concreto no se desactiva por modificar su prompt. Desactivar una tarea opcional no debe impedir enviar el capítulo por una regla legada de “todos los P”.
6. Un cambio de título, método, población, fuente o instrumento puede dejar salidas **potencialmente obsoletas**. El sistema conserva cada revisión, señala las tareas afectadas y pide revalidación según la dependencia; no invalida silenciosamente una aprobación ni vuelve a ejecutar IA sin aceptación.
7. La IA puede **proponer** cambios de prompt, orden o ramas con motivo y diff. Solo la acción del usuario autorizado publica la nueva versión. El asesor puede observar/sugerir; las firmas y aprobación institucional se rigen por permisos separados.

## 5. Contrato de datos mínimo propuesto

El agente debe elegir modelos/tablas concretos tras comparar los existentes. Lo siguiente es **información que debe persistir**, no nombres de clases impuestos:

- `project_id`, `base_template_version`, `workflow_version_id`, estado `DRAFT/PUBLISHED/RETIRED`, autor, fecha, versión anterior, hash del contenido y motivo de cambio.
- Tarea estable con `task_id`, `legacy_step_code?`, capítulo/sección de salida opcional, orden de presentación, rama/condición, estado opcional/activo y contrato de salida referenciado. Las tareas personalizadas no se guardan en `StepProgress.step_code` de tres caracteres sin migración explícita.
- Dependencia dirigida con tipo (dato requerido, revisión humana, condición institucional), origen, destino, condición y fuente/justificación. Diferenciar **recomendación de orden** de **prerrequisito bloqueante**.
- Plantilla de prompt con texto, versión, procedencia (base, usuario o sugerencia IA), autor, fecha, parámetros permitidos y referencia a tarea. Guardar exactamente el texto usado al ejecutar; no depender de la versión actual para reconstruir el pasado.
- Ejecución/salida/revisión con vínculo a `workflow_version_id`, `prompt_version_id`, entradas/contexto versionados, contrato de salida y estado de aceptación. Para operaciones existentes, definir estrategia de compatibilidad antes de cambiar esquema.

El historial es append-only para versiones publicadas y aprobaciones. La configuración borrador puede editarse con control de versión optimista. No copiar íntegramente el manuscrito a cada tabla de configuración.

## 6. API y permisos mínimos de la primera entrega

Mantener `/api/v1/` y aislar todas las operaciones por proyecto autenticado. El agente define rutas Ninja exactas tras revisar el router. Deben existir operaciones equivalentes a:

| Operación | Actor | Resultado o error necesario |
|---|---|---|
| Leer recorrido publicado y borrador propio | Tesista, asesor asignado en modo lectura | IDs/versiones, tareas ordenadas, dependencias y origen de reglas; nunca contenido de otro proyecto. |
| Crear/editar borrador de recorrido | Tesista titular | `expected_version`, conflicto recuperable, diff; texto y grafo validados. |
| Validar sin publicar | Tesista | Errores tipados por tarea/dependencia; advertencias separadas de bloqueos. |
| Publicar o restaurar mediante nueva versión | Tesista titular | Versión inmutable nueva y auditoría; no sustituye aprobación del asesor. |
| Consultar prompt efectivo para una tarea | Participante autorizado | Texto exacto/versionado, parámetros y capa protegida aplicable; no revelar secretos. |
| Guardar/ejecutar tarea estructurada | Tesista o agente bajo su identidad | Evalúa la versión publicada, contrato y dependencias; rechazo estable cuando falte una entrada; idempotencia y bloqueo concurrente. |
| Solicitar generación con IA | Tesista titular, sujeto a proveedor configurado | Crear job en servidor con contexto fijado, prompt y versión; devolver propuesta tipada, no aceptada. Véase la [especificación de generación](./especificacion_generacion_ia_y_resultados.md). |
| Aceptar/rechazar propuesta IA | Tesista titular; asesor conserva revisión académica | Revalidar versión/contexto y crear revisión canónica solo con aceptación explícita; rechazo no cambia manuscrito. |

El asesor puede sugerir cambios por un canal de observaciones versionadas; no muta el borrador del tesista sin una concesión explícita futura. MCP reutiliza los servicios del backend; sus 35 prompts estáticos pueden seguir como compatibilidad, pero no son el almacén canónico de los prompts nuevos.

## 7. Entrega vertical y orden de trabajo para Antigravity

**A. Auditoría focalizada:** enumerar modelos, migraciones, rutas, consumidores y tests que hacen supuestos de secuencia P01–P32, incluidos materializadores y `submit_chapter`. Registrar hallazgos con archivo/símbolo real. No reescribir el dominio desde cero.

**B. Configuración persistente:** crear versiones de recorrido/prompts por proyecto, servicio de validación/publicación y API de lectura/escritura segura. Usar una plantilla base derivada del catálogo actual. Mantener proyectos existentes en modo legado si no se migran aún. Demostrar edición, reordenamiento visual, restauración, aislamiento y conflictos.

**C. Ejecución realmente flexible:** cambiar `save_step` para consultar un grafo publicado cuando el proyecto esté en modo configurable; refactorizar las dependencias ocultas de cada materializador afectado. Demostrar al menos una tarea de literatura adelantada sin fabricar P previos y un caso bloqueado por dependencia real. Adaptar `submit_chapter` a las tareas activas y exigibles de la versión publicada, sin rebajar controles de revisión.

**D. Ampliación metodológica:** resolver ramas cuantitativa/cualitativa/mixta, P15 opcional, P20 IEEE, P05 borrador/definitiva y posteriores a P32 por contratos y datos reales. No declarar esta fase implementada por completar B/C.

**E. Generación IA desde el backend:** B5.1 implementa el job, contexto/prompt versionados, validación, worker, aceptación/rechazo y adaptador Gemini. El proveedor está deshabilitado por defecto y la llamada real queda pendiente de credenciales. El endpoint `execute` es distinto: guarda `output_data` ya producido por el cliente.

**B, C y D son hitos distintos.** La demo al profesor puede mostrar B si se etiqueta honestamente “configuración del recorrido”; para afirmar “ejecución flexible” debe pasar C. Nada de esto exige esperar a la reunión para comenzar.

## 8. Pruebas de aceptación que no son opcionales

1. El titular modifica y reordena prompts, publica, obtiene una versión nueva y recupera exactamente la anterior. Dos ediciones concurrentes producen conflicto, no pérdida de datos.
2. Usuario ajeno y asesor sin permiso de edición no pueden publicar, alterar ni leer borradores ajenos; la API/MCP usan identidad del servidor.
3. Un grafo cíclico, referencias inexistentes o intento de desactivar control protegido se rechazan con error localizable. Reordenar nodos independientes sí funciona.
4. Una tarea sin entradas requeridas permanece en borrador/pendiente; no se guarda como completada. Las tareas paralelas usan la versión de contexto fijada.
5. Una revisión antigua conserva la versión del prompt y del recorrido con la que se creó, incluso tras restaurar/publicar otra.
6. Proyectos legados conservan P01–P32 y las pruebas previas; ninguna migración borra `StepProgress`, `ChapterRevision` ni eventos.
7. La publicación/ejecución no permite al prompt conceder permisos, inventar evidencia, publicar resultados empíricos sin datos ni aprobar una revisión.
8. Al completar C, `save_step` y `submit_chapter` usan los requisitos efectivos de la versión publicada; una prueba muestra un paso independiente adelantado y otra un bloqueo por dependencia real.

## 9. Lo que aún debe decidir el equipo sin frenar A/B

- Política exacta de quién puede **publicar** un recorrido académico que el asesor ya observó: tesista solo, o tesista con visto bueno del asesor para cambios que afectan un plan aprobado. Hasta decidirlo, ningún cambio modifica una aprobación pasada y el asesor ve un aviso de versión nueva.
- Estructura final del documento enriquecido y del snapshot completo de capítulo; B1 sigue necesario para garantizar que la aprobación/exportación corresponden al contenido íntegro.
- Matriz exhaustiva de dependencias P01–P32 por enfoque y modalidad. La [propuesta metodológica](../03_metodologia_y_prompts/propuesta_orden_metodologico_revisado.md) orienta; los prerrequisitos de ejecución se confirman leyendo contratos, materializadores y normas aplicables, no por copiar el orden F0–F10.

Esta especificación autoriza una implementación incremental y honesta. La tesis completa más allá de P32 permanece como alcance de producto, pero requiere modelos de datos empíricos, revisión y exportación propios; no se simula con prompts añadidos.
