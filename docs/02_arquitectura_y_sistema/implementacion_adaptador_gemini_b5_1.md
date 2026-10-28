# Paquete de implementación: adaptador Gemini para B5.1

**Estado:** bloque ejecutado; conservar como registro y referencia, no como instrucción para repetir B5.1. Implementado con SDK oficial `google-genai`, con modelo predeterminado `gemini-3.8-flash` (26/10/2026); pruebas simuladas y ciclo integrado pasan. La llamada real queda pendiente de credenciales `GEMINI_API_KEY`. **Fecha:** 26/10/2026. El código actual define los contratos y símbolos existentes.

## 1. Resultado que se busca

Habilitar generación real en el servidor Django usando Gemini, a través del contrato LLM que ya existe. La petición web debe seguir el recorrido ya implementado: API → `AIGenerationJob` → worker → adaptador → validación local → propuesta pendiente de aceptación. El proveedor nunca se invoca desde el navegador.

El alcance original consistió en completar el adaptador y su configuración; ese trabajo ya está hecho. No se debe reconstruir la generación, el worker, los modelos, las rutas ni la aceptación. Una llamada real con credenciales es una verificación operativa separada, no una razón para volver a implementar el adaptador.

## 2. Estado real que se debe comprobar antes de editar

Volver a leer los archivos en el checkout actual; no confiar solo en este inventario.

| Símbolo | Estado observado en el corte de esta especificación | Reutilización requerida |
|---|---|---|
| `backend/thesis/integrations/llm/base.py::LLMProviderAdapter` | Define `generate_structured(messages, output_schema, model_config=None, timeout=30.0)` y los tipos `LLMMessage`, `LLMResult` y errores normalizados. | Implementar esta interfaz sin cambiarla salvo incompatibilidad concreta demostrada por el SDK. |
| `backend/thesis/integrations/llm/factory.py::get_llm_adapter` | Estado histórico previo a B5.1: `GEMINI` verificaba la clave e informaba que faltaba el adaptador. Estado actual: construye el adaptador real; `DISABLED` sigue como default y el mock solo se permite con `DEBUG`. | No volver a editar la rama Gemini salvo que una falla reproducible o un cambio de requisito lo justifique. |
| `backend/thesis/services/ai_jobs.py` | Crea/recupera jobs, forma mensajes desde contexto autorizado, llama al adaptador, valida localmente y normaliza fallas. | No mover llamadas de proveedor a la API, modelos o frontend. No duplicar validación/aceptación. |
| `backend/thesis/api/projects.py` | Las rutas de generar, consultar, cancelar, aceptar y rechazar ya están declaradas. | No crear endpoints paralelos ni cambiar sus esquemas para integrar Gemini. |
| `AIGenerationJob`, migraciones `0021` y `0022` | Persisten el ciclo de trabajo, el contexto, la respuesta y la decisión humana. | No añadir migración para una integración que debe resolverse dentro del adaptador/configuración. |
| `backend/thesis/tests/test_ai_generation.py` y pruebas de integración LLM | Cubren el ciclo con adaptadores simulados e inyección de prueba. | Ampliar pruebas focalizadas sin sustituir el test de una llamada real cuando haya credenciales configuradas. |

## 3. Decisiones técnicas para este bloque

1. Usar el SDK oficial Python `google-genai` (`from google import genai`) si las fuentes oficiales y la compatibilidad con el Python/dependencias reales del proyecto lo confirman. No instalar el SDK antiguo `google-generativeai` ni inventar nombres de paquetes, clases, parámetros o modelos.
2. Para salida estructurada, usar el mecanismo oficial de Gemini que acepte un esquema Pydantic/JSON Schema. La documentación oficial indica que Structured Outputs admite un subconjunto de JSON Schema; comprobar compatibilidad con los esquemas reales de P01–P32 y `USR_...`. No asumir que todo JSON Schema es aceptado por el proveedor.
3. Mantener validación local estricta después de la respuesta del SDK. La salida estructurada del proveedor no reemplaza `validate_output_data` ni el esquema congelado en el job.
4. `GEMINI_API_KEY` es secreto exclusivamente del proceso backend/worker. El modelo predeterminado acordado para el proyecto es `gemini-3.8-flash`; puede cambiarse solo desde la configuración del servidor mediante `TESISMCP_GEMINI_MODEL`. No se recibe de petición, prompt, usuario ni base de datos editable. Si el proveedor o el modelo no están disponibles, fallar con un error operativo claro y seguro.
5. `TESISMCP_LLM_PROVIDER` debe seguir `DISABLED` por defecto. Para habilitar Gemini, el entorno tiene que declarar explícitamente `GEMINI` y aportar clave y modelo válidos. Nunca degradar silenciosamente a mock u otro modelo.
6. Configurar timeout usando el valor `timeout` de la interfaz y los mecanismos soportados por la versión fijada del SDK. Respetar la semántica sincrónica actual del worker; no convertir el SDK en una tarea dentro de la petición HTTP.
7. Mapear errores del SDK a las excepciones ya definidas en `base.py` (`LLMProviderUnavailableError`, `LLMProviderTimeoutError`, `LLMProviderRateLimitError`, `LLMOutputInvalidError`) y a códigos existentes en `ai_jobs.py`. No exponer respuestas crudas, cabeceras, claves, prompt privado ni stack traces en la API.
8. Devolver `LLMResult` con `provider="GEMINI"`, el modelo realmente usado, JSON validado preliminarmente y uso solo cuando el SDK lo entregue. No estimar tokens/costos ni reportar metadatos no proporcionados.
9. Serializar mensajes conforme a roles que realmente soporte la API elegida. Preservar el contenido de instrucciones del sistema/tarea y el tratamiento de contexto como dato no confiable; si el SDK exige transformar roles, documentar la equivalencia y probarla. No cambiar el prompt del proyecto para solucionar limitaciones del transporte.
10. No activar búsqueda web, grounding, File Search, function calling, MCP, URL context, agentes ni carga de archivos en este bloque. Son capacidades diferentes y requieren contratos, permisos y evaluación propios.

## 4. Seguridad y límites de datos

- No agregar secretos a `.env`, fixtures, logs, Markdown versionado, capturas ni salida de terminal. Actualizar `.env.example` únicamente con nombres de variables y valores vacíos/no secretos si existe.
- Confirmar qué texto/contexto construye `ai_jobs.py` y qué campos del job llegan al proveedor. No ampliar los datos transmitidos ni subir documentos completos como parte de esta tarea.
- No imprimir prompt, texto de tesis, extractos, clave, respuesta cruda ni objetos SDK completos en logs. Se pueden registrar IDs del job, proveedor, modelo efectivo, estado y error normalizado.
- No garantizar retención, privacidad, residencia regional ni exclusión del entrenamiento sin una fuente contractual vigente. La puesta en producción requiere decisión institucional independiente.
- El adaptador entrega una propuesta. Solo `accept_ai_proposal` puede volverla contenido persistido; Gemini no acepta, aprueba ni edita directamente la tesis.

## 5. Trabajo permitido y fuera de alcance

**Alcance original ya ejecutado:** módulo adaptador Gemini, rama factory, dependencia fijada, settings/configuración de entorno, documentación de configuración sin secretos, mapeo de errores y pruebas de adaptador. Los puntos siguientes registran el criterio de aceptación aplicado; no constituyen una nueva tarea de implementación.

**Fuera de alcance:** modelos/migraciones, rutas/API, permisos, contratos Pydantic de las tareas, catálogo o reordenamiento de prompts, workflow, aceptación/rechazo, editor web, Zotero, búsqueda Scopus/WoS, multiagentes, envío de documentos, generación de capítulos completos y cambios generales de arquitectura.

Si al inspeccionar el SDK surge una incompatibilidad que obligue a alterar `LLMProviderAdapter`, el worker, contratos de salida o política de datos, detener esa alteración, documentar la evidencia y proponer el cambio mínimo. No ampliar el alcance sin registrarlo primero.

## 6. Pruebas y evidencia requeridas

1. Pruebas unitarias del adaptador con el límite SDK simulado: salida estructurada válida, JSON inválido/vacío, respuesta sin texto, timeout, rate limit, autenticación/configuración inválida, error de proveedor y extracción de uso cuando exista.
2. Pruebas factory: provider deshabilitado sigue fallando cerrado; mock sigue restringido a `DEBUG`; Gemini requiere clave y modelo; no hay fallback silencioso.
3. Prueba de integración del ciclo ya existente con el adaptador inyectado: el job guarda propuesta validada como pendiente y no escribe una revisión canónica antes de la aceptación. No dupliques pruebas ya existentes; inspecciónalas y agrega solo cobertura que falte.
4. Una llamada real a Gemini solo se reporta si se ejecutó con credenciales y un modelo configurados en el entorno. Una respuesta simulada nunca cuenta como conexión real. No pedir ni copiar la clave en el chat.
5. Ejecutar las comprobaciones exigidas por `AGENTS.md`, incluida `python3 scripts/verify_project.py`. Reportar comando, código de salida y si la llamada real se hizo o quedó pendiente por credenciales.

## 7. Criterio de cierre de B5.1-Gemini

- La factory puede construir el adaptador Gemini desde configuración exclusivamente del servidor.
- El adaptador implementa la interfaz existente y devuelve JSON estricto; los errores quedan normalizados.
- La salida pasa la validación local real de la tarea; una falla no se convierte en éxito.
- El flujo de job, aceptación humana y almacenamiento canónico conserva su comportamiento existente.
- No hay claves ni contenido sensible en el navegador, respuesta pública, logs o repositorio.
- Las pruebas cubren los casos anteriores y la puerta del proyecto termina con `exit code 0`.
- El informe final separa «adaptador implementado», «pruebas con SDK simulado» y «llamada real verificada», sin confundirlos.

## 8. Fuentes técnicas primarias a consultar

- [Google Gemini API: Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output): revisar el subconjunto JSON Schema admitido y el ejemplo vigente para Python.
- [Google Gemini API: Python SDK / Getting started](https://ai.google.dev/gemini-api/docs/get-started): confirmar paquete, import, configuración, llamada y compatibilidad actuales.

Las páginas oficiales son fuentes técnicas de API, no autorización para transmitir datos personales ni fuente de una política institucional de privacidad.
