# Seguridad, datos y operación del backend

**Estado:** requisitos objetivo para desarrollo/despliegue; contrastar con configuración vigente. **Actualizado:** 25/10/2026.

## Seguridad y límites de confianza

1. **Identidad:** sesiones web o token MCP validado en servidor. El modelo no selecciona `user_id`, rol, proyecto ajeno ni permiso.
2. **Autorización:** cada lectura, escritura, job y descarga verifica pertenencia y capacidad dentro del caso de uso. Los identificadores UUID no son control de acceso.
3. **Separación de dominios:** servicios implementan reglas; API/MCP son adaptadores; base de datos agrega restricciones para invariantes que lo permitan.
4. **Entrada hostil:** contenido de PDF, Office, páginas web, campos bibliográficos y salida de LLM se tratan como datos no confiables, nunca como instrucciones del sistema.
5. **Subida/descarga:** límites de tamaño/tipo, validación real del formato, hash, nombres no confiables neutralizados, almacenamiento fuera del webroot, control de acceso y limpieza conforme a política. Descargas URL deben evitar SSRF y destinos internos.
6. **Secretos:** nunca guardar credenciales UTP/Scopus/WoS en claro ni pedirlas en prompts. Tokens OAuth/API se cifran y limitan al scope autorizado; revocación y borrado verificables. No presentar login institucional como permiso programático.
7. **Auditoría:** registrar actor, acción, recurso, versión anterior/nueva, fecha, canal e integración relevante. No incluir tokens, contraseñas ni contenido privado innecesario en logs.
8. **Agentes:** outputs se validan por esquema y pertenencia a IDs permitidos; el agente no puede aprobar, publicar metodología o guardar texto final sin actor/acción autorizada.
9. **Búsqueda web y bibliográfica:** resultados y páginas se tratan como datos no confiables. Registrar origen, consulta y fecha; no atribuir resultados de un proveedor a otro. La ruta manual Scopus/WoS no recopila contraseñas ni presenta como automatizada una consulta que ejecutó el usuario.
10. **Revisión de citas:** el output de IA no se trata como verdad ni como decisión editorial. Guardar texto exacto, fuente/version/hash, pasaje/localizador, método y nivel de acceso. Una sugerencia de sustitución requiere aceptación explícita del tesista y genera una revisión nueva.
11. **Invitados:** limitar el acceso a invitación aceptada, tarea y recursos compartidos; validar autorización en peticiones, workers y descargas. Invitado no obtiene acceso a proyecto completo ni a datos personales por pertenecer a una categoría profesional.

## Datos y versiones

- PostgreSQL/Django actuales son la fuente de verdad; inspeccionar modelos y migraciones antes de agregar entidades.
- Los documentos originales y artefactos derivados deben distinguirse por hash, versión, tipo de extracción y relación con el original.
- Fuente, extracto, pasaje y vínculo de evidencia conservan procedencia y localizador físico. Un índice vectorial/caché puede reconstruirse; no es autoridad documental.
- Evaluación automática de respaldo, estado de acceso, revisión del tesista y revisión del asesor son datos separados y versionados. Si cambia afirmación, documento, extracción o fuente, identificar evaluaciones que quedaron obsoletas; no actualizarlas silenciosamente.
- Invitación de apoyo conserva invitante, invitado, propósito/tarea, recursos, permisos, aceptación, expiración/revocación y respuestas. Una respuesta de invitado no sustituye el texto canónico ni aprobación de capítulo.
- Definir retención, eliminación, exportación y recuperación para proyectos, archivos, conexiones Zotero, muestras de estilo y ejecuciones de IA. Son decisiones pendientes si no están cubiertas por configuración/política existente.
- Separar datos personales del contenido académico cuando sea posible. El perfil de escritura usa muestras propias consentidas; registrar consentimiento, revocación, borrado y propósito.
- Las revisiones presentadas/aprobadas y los eventos son inmutables. Las correcciones crean versiones nuevas; nunca reescribir el objeto evaluado.
- Para tablas/figuras preservar dataset de entrada, unidades, transformación, parámetros y versiones. Las exportaciones refieren a snapshots de texto, cita y figura.

## Migraciones y compatibilidad

Antes de una migración, documentar: esquema actual, filas afectadas, transformación, valores nulos/ilegibles, estrategia de despliegue, reversión y prueba con datos representativos. Evitar migraciones destructivas. Mantener lecturas de datos legados y marcar la incertidumbre; no “arreglar” registros históricos por inferencia.

Áreas que requieren diseño antes de tocar el esquema:

- snapshot completo de capítulo frente a revisiones por paso;
- historial de `output_json` y catálogo de prompts/metodología versionado;
- múltiples procedencias bibliográficas y fuentes sin OpenAlex ID;
- documento estructurado del editor y anclas de selección;
- conexión Zotero y credenciales externas;
- ejecución, contexto, cancelación y aceptación de agentes;
- datos y transformaciones reproducibles de figuras.

No crear una tabla solo porque aparece un concepto en esta especificación: primero buscar modelo o relación existente, justificar normalización e índices, documentar migración y permisos.

## Procesamiento de archivos y trabajos

- Mantener originales inmutables; registrar extractor/versión, hash, paginación física y resultados derivados.
- PDF escaneado activa OCR selectivo y guarda confianza/localización. El OCR no valida semántica ni lectura de gráficos.
- Para XLSX conservar hojas, celdas, fórmulas y valores; Markdown es una vista de trabajo, no fuente canónica.
- Los workers procesan jobs aislados, limitados por tamaño/tiempo/memoria, con estado/error recuperable. Reintento, cancelación e idempotencia se especifican por tipo.
- No ejecutar macros ni contenido activo de Office. Aislar conversores externos y validar sus entradas/salidas.
- No usar embeddings o semejanza para afirmar que una cita demuestra una conclusión.
- Para enlaces o intentos de resolver/descargar un documento, validar esquemas y dominios, bloquear rangos de red interna/localhost, limitar redirecciones, tamaño y tiempo, y ejecutar la extracción en worker aislado. Requerir una fuente legítima/permitida; no automatizar acceso autenticado a Scopus/WoS en el flujo base.
- OCR y evaluación de citas guardan texto/posición/confianza como artefactos; una baja confianza, paginación indeterminada o ausencia de texto debe traducirse en acceso/verificación insuficiente, no en una afirmación completada.

## Operación y observabilidad

### Desarrollo local y preparación del despliegue

La decisión vigente del equipo es mantener el desarrollo local durante el curso y preparar la configuración por entorno para un despliegue futuro. `compose.yaml` ya usa volúmenes persistentes para PostgreSQL/media/modelos y liga sus puertos publicados a loopback; ello da persistencia/aislamiento local, no respaldo ni preparación para producción. Al corte 26/10/2026 el Compose mantiene credenciales locales fijas y `DJANGO_DEBUG=1` como default de desarrollo. `DATABASE_URL` es configurable en Django, pero no afirmar que el despliegue ya sea portable o seguro.

El helper histórico de `V1` permanece en la carpeta original y su antiguo dump no incluye `MEDIA_ROOT`. El proyecto principal incorporó después `scripts/local_recovery.py`, un respaldo manual conjunto de DB y media y un ensayo de restauración aislada. No existe un timer/cron ni copia fuera del mismo host; la copia de proyecto tampoco crea una base de datos independiente. Ver procedimiento, evidencia y limitaciones en el [paquete B10](./paquete_b10_operacion_local_y_despliegue.md).

Para un despliegue no local, verificar y documentar antes de habilitar usuarios:

- HTTPS, configuración segura de sesión/CSRF/CORS, secretos por entorno y permisos de servicio mínimos;
- PostgreSQL respaldado, restauración probada, migraciones controladas y estrategia de recuperación;
- almacenamiento persistente privado para documentos/exportaciones y separación entre original y derivados;
- colas/workers observables, límites, reintentos y capacidad de cancelar;
- logs estructurados, métricas técnicas, alertas y política de retención sin datos secretos;
- health/readiness que comprueba dependencias necesarias sin filtrar configuración sensible;
- cuota y errores de proveedores externos separados del estado general del proyecto;
- monitoreo de costos/latencias del proveedor de IA si se habilita generación desde la web.

No se declara producción lista por pasar `manage.py check`: se requiere revisión de configuración, recuperación de datos, seguridad operacional y prueba del despliegue real.

## Integraciones externas y degradación

OpenAlex, Semantic Scholar, ALICIA, Crossref, resolutores, Scopus, WoS, Zotero, OCR/GROBID y modelos pueden fallar, cambiar cuota o no estar autorizados. El dominio debe registrar proveedor/método, exponer fallas parciales y permitir flujos alternativos. Para Scopus/WoS la ruta de producto base es preparar ecuación/enlace y procesar exportación del usuario; API es opcional y no bloquea esta ruta. No se debe descargar texto cerrado por inferir que la cuenta personal autoriza al sistema. Automatización de navegador no forma parte del flujo base; cualquier experimento se revisa por separado según términos/autorización y nunca evade controles de acceso.

Si una fuente completa no puede obtenerse, permitir al usuario seguir con enlace, metadatos o resumen, marcando explícitamente el nivel. No emitir juicio de respaldo sobre secciones no inspeccionadas. La especificación funcional está en [búsqueda y revisión de evidencia](./especificacion_busqueda_y_revision_de_evidencia.md).

n8n, si se adopta, invoca operaciones autorizadas de TesisMCP; no mantiene una segunda base canónica ni duplica reglas de aprobación. WhatsApp no se integra.
