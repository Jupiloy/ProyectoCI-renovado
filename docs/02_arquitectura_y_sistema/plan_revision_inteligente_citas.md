# Primera versión de revisión inteligente de citas

**Estado:** especificación de implementación; la evaluación semántica automática no está implementada. La revisión humana y el historial de evidencia sí existen. Este diseño sigue BYOA: el agente conectado aporta el análisis; TesisMCP fija datos/contexto, valida y presenta la propuesta.

## 1. Capacidad acotada

Para una ocurrencia de cita seleccionada en una revisión de capítulo, generar una propuesta que compare la afirmación con pasajes de la fuente citada. Debe señalar si el pasaje parece respaldar, respaldar parcialmente, contradecir, no tratar o no permitir evaluar la afirmación. Debe incluir razonamiento breve, extractos exactos, páginas/localizadores y límites de acceso. La propuesta ayuda a revisar; no certifica la verdad científica.

La primera versión no reemplaza citas automáticamente, no edita el documento, no inventa metadatos ni afirma haber leído un texto completo si solo recibió metadatos/resumen. La búsqueda de fuentes alternativas es una operación separada: cada candidata requiere registro real y un pasaje accesible antes de sugerirse como respaldo.

## 2. Lo que ya existe y debe reutilizarse

- `ChapterCitationOccurrence` identifica una cita del documento canónico y la revisión/bloque donde aparece.
- `SourceExcerpt` conserva texto y página física; `SourceDocument.verification_status` señala el nivel de acceso.
- `CitationEvidenceReview` conserva historial append-only del vínculo afirmación–pasaje y decisiones humanas versionadas.
- `POST .../citations/{occurrence_id}/evidence` registra un candidato textual validado; `GET .../evidence` consulta historial; `POST .../citation-evidence/{review_id}/decision` registra la decisión explícita del asesor.
- La respuesta actual declara `automated_semantic_assessment: NOT_PERFORMED`. No cambiar ese valor hasta integrar y probar un evaluador real.

No reutilizar el estado de decisión humana para almacenar la conclusión del agente. La recomendación técnica es un registro separado e inmutable de propuesta IA (o un job enlazado con payload de evaluación validado), con versión de entrada, hash de afirmación/pasaje, runtime declarado, referencias MCP usadas, fecha, salida y advertencias. La propuesta no debe confundirse con `SUPPORTS`/`CONTRADICTS` decidido por el asesor.

## 3. Contrato de entrada

El backend obtiene de IDs autorizados, no del texto libre del modelo:

- proyecto, capítulo, revisión del documento y ocurrencia de cita;
- afirmación exacta y rango/hash de esa revisión;
- fuente vinculada a la cita, estado de extracción/acceso y metadatos existentes;
- uno o más `excerpt_id` de esa fuente (o de una fuente candidata permitida), con texto, página/localizador y hash;
- versiones esperadas e idempotency key.

Rechazar IDs cruzados entre proyectos, extractos de otra fuente, fuente sin texto suficiente, hash obsoleto y una afirmación que no coincida con la revisión escogida. Si hay metadatos sin texto accesible, la salida debe ser `INSUFFICIENT_ACCESS`, no un dictamen semántico.

## 4. Contrato de salida de la propuesta

Usar un esquema estricto con, al menos:

- `assessment`: `SUPPORTS`, `PARTIAL_SUPPORT`, `CONTRADICTS`, `UNRELATED`, `INSUFFICIENT_ACCESS` o `NOT_ASSESSED`;
- `claim_text` y hash de entrada;
- lista de `evidence` con `source_id`, `excerpt_id`, pasaje literal o rango exacto, hash y localizador físico/estructural;
- `reasoning_summary` breve, redactado como evaluación provisional;
- `limitations` y `missing_information` explícitos;
- runtime/modelo si el agente lo declara; usar `UNKNOWN` cuando no haya dato verificable;
- `context_version`, `created_at` y estado separado `PENDING_HUMAN_REVIEW`.

El servidor debe comprobar por sí mismo que cada extracto pertenece al proyecto/fuente autorizados, que el hash coincide y que el pasaje citado aparece en el texto almacenado. No confiar en que el modelo haya devuelto un `excerpt_id` válido.

## 5. Flujo de usuario y permisos

1. Tesista solicita análisis desde una versión de documento concreta.
2. Backend autoriza y crea job/entrada congelada.
3. El agente BYOA recibe la tarea; consulta extractos mediante MCP si necesita obtenerlos.
4. Backend valida y guarda propuesta; devuelve progreso/resultado por API.
5. La web muestra afirmación, texto de evidencia, página, nivel de acceso, razonamiento y limitaciones.
6. Tesista puede descartar o enviar a revisión. El asesor conserva su decisión explícita y versionada.
7. Para cambiar una cita, reutilizar el flujo actual de `replacement-proposals`, mostrar diff y exigir aceptación del titular. Nunca aceptar por la mera propuesta IA.

El asesor puede confirmar, rechazar o pedir más evidencia según las decisiones actuales. La respuesta automatizada no cuenta como aprobación de capítulo ni como evaluación metodológica.

## 6. Errores y resultados no concluyentes

Exponer estados diferenciados: job fallido/desconectado, `INSUFFICIENT_ACCESS`, `NOT_ASSESSED`, evidencia obsoleta (`STALE`/conflicto de versión), esquema inválido, fuente no disponible y propuesta lista para revisión. No convertir falta de acceso en `UNRELATED`; no ocultar errores del runtime.

## 7. Evaluación antes de presentarlo como fiable

Preparar ejemplos autorizados y revisados por personas con pares afirmación–pasaje: apoyo claro, apoyo parcial, contradicción, irrelevancia y acceso insuficiente. Registrar criterio de oro y desacuerdos entre revisores. Medir por clase precisión/recall cuando haya etiquetas suficientes, cobertura de citas localizables, pasajes inválidos, tasa de respuestas no concluyentes, latencia y costo real si el runtime lo informa. Publicar composición del conjunto y método; no inventar cifras ni extrapolar desde mocks.

Los casos simulados prueban contratos, no calidad semántica. Antes de una conclusión de rendimiento se necesita ejecución con un agente/modelo real y revisión independiente.

## 8. Orden de implementación

1. Definir schema, modelo/almacenamiento separado, estados y referencias de evidencia.
2. Conectar un job BYOA a una tarea MCP concreta, respetando el [contrato de agentes](./arquitectura_byoa_api_mcp.md).
3. Implementar autorización, validación de extractos/hashes, idempotencia y salida no concluyente.
4. Añadir la vista web de propuesta e historial; conservar la decisión humana existente.
5. Evaluar con un conjunto etiquetado y documentar límites.

No duplicar revisión humana ni reimplementar B5.1 Gemini. No declarar esta capacidad implementada por añadir solo un prompt o una herramienta MCP.
