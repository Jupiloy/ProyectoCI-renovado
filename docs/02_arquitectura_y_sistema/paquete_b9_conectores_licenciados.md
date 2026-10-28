# B9 — Conectores licenciados opcionales

**Estado operativo local tras la reparación:** la base `tesismcp` de `tesismcp-local-pg` recibió las migraciones `0024`–`0044`, después de un respaldo conjunto DB+media y un ensayo de restauración/migración aislado. El desfase hasta `0023` fue el hallazgo inicial; las puertas históricas 7/7 no verificaban migraciones aplicadas. El verificador incorpora ahora ese control separado. Consultar el [registro B10](./paquete_b10_operacion_local_y_despliegue.md) para evidencia, comandos y límites; no confundir esta reparación local con el cierre de B10 o del producto.

**Estado al 26/10/2026:** evaluación técnica y de dependencias terminada; ningún conector API Scopus/WoS se habilita ni se declara implementado. La ruta manual asistida existente permanece disponible. La implementación de conectores queda condicionada a evidencia de acceso, permiso de uso y caso operativo aprobado. n8n no se incorpora porque aún no hay un flujo que lo justifique. WhatsApp permanece excluido.

## 1. Propósito y decisión de alcance

B9 evaluaba si TesisMCP debe consultar directamente fuentes licenciadas como Scopus o Web of Science. La revisión del código, los contratos y las fuentes oficiales confirma que añadir llamadas HTTP sin habilitación institucional sería prematuro: tener una cuenta estudiantil, acceso al sitio web o una API key no demuestra por sí solo que el proyecto pueda consultar esos datos desde una aplicación, bajo qué plan, cuotas o condiciones.

La decisión para el prototipo actual es:

1. Mantener como flujo funcional principal la búsqueda asistida: preparar y versionar la consulta, abrir el sitio oficial, registrar la ejecución que declara el usuario e importar los resultados exportados por este.
2. Usar los proveedores abiertos ya integrados para descubrimiento donde aporten cobertura y permitan ese uso; no presentarlos como resultados de Scopus/WoS.
3. No automatizar login institucional, reutilizar cookies, raspar interfaces ni sortear límites de acceso.
4. Implementar un conector licenciado únicamente después de comprobar el entitlement específico de la API y de aprobar el uso de los datos para TesisMCP.
5. Mantener n8n como opción futura de orquestación, no como requisito del sistema ni como sustituto de servicios, permisos o transacciones de Django.

Esto deja B9 **evaluado y condicionado**, no “implementado”. La falta de API no bloquea búsqueda, importación, lectura del corpus ni continuidad del trabajo del frontend.

## 2. Estado comprobado en el repositorio

La inspección del código actual encontró lo siguiente:

| Capacidad | Evidencia de implementación | Límite preciso |
|---|---|---|
| Estrategias Scopus/WoS | `SearchStrategy` permite esos proveedores, guarda consulta/ecuación/filtros/URL y crea versiones append-only. | No ejecuta la consulta en esos proveedores. |
| Registro de búsqueda | `SearchExecution` persiste una declaración manual del usuario ligada a una estrategia/version. | Es manual; no verifica que el usuario entrara en la base. No es registro de llamada API. |
| Importación | `/sources/import-bibliography` lee RIS, BibTeX y CSV y puede registrar `SCOPUS`/`WOS` como origen del archivo. | Metadatos no se autentican contra el proveedor y no se descargan PDFs. |
| Procedencia | `SourceDocument` distingue `PROVIDER_API`, `USER_FILE_IMPORT`, `USER_SELECTED_CANDIDATE` y `USER_UPLOADED_FILE`. | El estado de procedencia no acredita por sí solo una autorización externa ni una búsqueda API específica. |
| Descubrimiento abierto | OpenAlex, Semantic Scholar y ALICIA tienen consultas de búsqueda; Crossref consulta metadatos de un DOI concreto. | La cobertura, disponibilidad, campos y políticas varían por proveedor; no se atribuyen a Scopus/WoS. |
| Conectores licenciados | No se encontraron módulos de integración Scopus/Elsevier ni Web of Science/Clarivate en `backend/thesis/integrations/`, ni contrato de ejecución API específico. | No hay implementación activa que probar ni credenciales/entitlements verificados en el proyecto. |

Las rutas y modelos pertinentes están descritos en [B3: búsqueda y fuentes](./guia_continuidad_backend.md) y en [contratos API](./contratos_api_backend.md). No se añadieron endpoints, modelos, migraciones ni dependencias en B9.

## 3. Qué significa “tener acceso” para este proyecto

El permiso debe verificarse para **la aplicación TesisMCP, el proveedor/API, el uso y el entorno concretos**. No se debe inferir de una credencial personal ni de la posibilidad de abrir una página web.

### Scopus / Elsevier

La documentación oficial indica que una API key identifica la aplicación, pero no concede automáticamente acceso a los datos; los permisos de API dependen del entitlement confirmado. Para acceso de suscriptor pueden intervenir la suscripción institucional y el método de autenticación aceptado por Elsevier. Algunos permisos, vistas o datos son restringidos. La disponibilidad académica no elimina las políticas ni los límites aplicables.

Antes de programar se debe obtener confirmación del bibliotecario/especialista UTP o del contacto de cuenta/soporte de Elsevier sobre: Scopus API aplicable; uso académico/no comercial del prototipo; acceso para una aplicación web de terceros desarrollada por estudiantes; autenticación permitida desde el servidor de TesisMCP; campos/vistas y cuotas; almacenamiento, visualización, exportación y retención de datos; y requisitos para pruebas y posterior despliegue.

### Web of Science / Clarivate

La ficha oficial de Web of Science API Expanded declara que requiere licencia pagada y que la disponibilidad del plan depende de la suscripción institucional; se solicitan credenciales/API key desde el portal de desarrolladores según el plan contratado. Por ello, se debe confirmar con UTP qué producto y plan existen, si incluyen API y si cubren esta aplicación y el uso propuesto. La cuenta personal de estudiante no demuestra que TesisMCP tenga ese plan.

### Consecuencia para una cuenta estudiantil UTP

La cuenta estudiantil puede servir para consultar recursos conforme al acceso que la universidad ofrezca a esa persona. No permite concluir que el proyecto tenga derecho programático a crear una integración ni que las credenciales se puedan almacenar en un servidor compartido. No pedir, guardar ni usar la contraseña UTP del estudiante en TesisMCP. La validación debe venir de la biblioteca/UTP y de las condiciones oficiales del proveedor.

## 4. Puerta de habilitación de un conector

No iniciar implementación específica hasta completar y registrar estos elementos:

| Control previo | Evidencia mínima aceptable |
|---|---|
| Responsable institucional | Respuesta de biblioteca/especialista UTP, administrador de suscripción o representante autorizado; indicar quién confirma. |
| Producto/API | Nombre exacto del producto, endpoint/API plan y funciones/vistas permitidas. Una suscripción web genérica no basta. |
| Caso de uso | Una tarea concreta que no resuelva ya el flujo manual o un proveedor abierto; actor beneficiado y por qué la automatización aporta valor. |
| Aplicación y entorno | Confirmación de que el acceso permite una aplicación servidor/web para prototipo académico; separar desarrollo, demostración y cualquier uso externo. |
| Autenticación | Método autorizado (por ejemplo, clave de aplicación más acceso institucional admitido) y custodia de secretos de servidor. Nunca contraseña personal en frontend, prompt o base de datos sin protección. |
| Límites y manejo | Cuotas, concurrencia, paginación, errores 401/403/429/5xx, timeout, retry/backoff permitido y mecanismo de revocación. No inventar cuotas. |
| Datos y derechos | Campos consultables, usos permitidos, límites de caché/retención, presentación de resultados, redistribución y borrado. |
| Criterio de prueba | Credenciales de prueba/autorizadas y un ejemplo real reproducible cuyo resultado se pueda cotejar con la respuesta del proveedor, sin exponer claves. |
| Seguridad y operación | Secretos fuera del código y del navegador; logs sin tokens ni consultas sensibles; límites de tamaño/tiempo; desactivación inmediata del conector. |

Si algún punto no se confirma, conservar el modo manual y registrar qué evidencia falta. No afirmar que “UTP tiene API” basándose solo en acceso al portal del proveedor o en una cuenta individual.

## 5. Diseño futuro cuando exista autorización

La futura implementación debe ser pequeña y vertical, empezando por **un proveedor y un único caso de uso**, no por una abstracción multiproveedor anticipada.

1. **Contrato de dominio:** separar una consulta ejecutada por el servidor de una declaración manual. `SearchExecution` actual es específicamente manual; no reutilizarla sin cambiar explícitamente su contrato. Diseñar la persistencia/API para que proveedor, estrategia y versión, actor solicitante, fecha, identificador de solicitud, estado, conteo real, origen `PROVIDER_API` y fallas sean distinguibles. Guardar solo el payload o campos cuya retención esté permitida.
2. **Adaptador del proveedor:** encapsular autenticación, endpoint, paginación, filtros admitidos, normalización y errores. No permitir que el frontend elija URL arbitraria ni envíe secretos. Evitar que una falla de un proveedor rompa búsqueda/importación manual u otros conectores.
3. **Procedencia:** cada registro normalizado debe mantener proveedor real, ID del proveedor, consulta/versión y vínculo con la ejecución. No rotular una fila como API cuando vino de RIS/BibTeX/CSV del usuario.
4. **Límites:** aplicar timeout, tamaño/paginación acotados y cuotas indicadas por la licencia. Reintentar únicamente los errores y con el comportamiento autorizado. No escribir una política de rate limit con cifras inventadas.
5. **Seguridad:** claves solo en secretos de servidor; rotación y revocación; excluir tokens de respuestas, logs, trazas y prompts; proteger SSRF al fijar hosts permitidos; validar permisos del proyecto antes de ejecutar.
6. **Prueba real:** verificar una consulta con credencial autorizada en el entorno permitido y comparar IDs/campos con la respuesta oficial. Las pruebas con transporte sustituido verifican lógica, pero no cuentan como conexión real ni como evidencia de entitlement.
7. **Documentación/UI:** distinguir “búsqueda manual declarada”, “metadatos importados por usuario” y “consulta API ejecutada”. Mostrar proveedor, fecha, alcance, estado y límites; permitir exportar resultados solo si los términos lo admiten.

No se define hoy una migración ni un esquema final de corrida API: primero debe conocerse qué datos y retención autoriza cada licencia. El diseño existente de B3 debe inspeccionarse al iniciar ese incremento para reutilizar procedencia/importación donde corresponda.

## 6. n8n y automatización adicional

n8n no añade por sí solo acceso a Scopus/WoS. Solo tendría sentido ante un flujo concreto de integración externo (por ejemplo, notificación de una tarea o sincronización aprobada) cuyo disparador, propietario, credenciales, reintentos y auditoría estén acordados. Para el prototipo actual no se ha identificado ese caso ni un requisito que justifique un servicio de n8n.

Si se introduce en el futuro, Django conserva autorización, reglas de dominio, transacciones y estado canónico; n8n recibe únicamente el mínimo necesario, usa credenciales separadas y no puede aprobar capítulos ni modificar manuscritos sin una ruta autorizada. WhatsApp no forma parte de esta decisión ni del producto.

## 7. Criterios para reabrir B9 como implementación

B9 pasa de “condicionado” a “en implementación” solo si se adjunta evidencia autorizante y se aprueba un caso de uso. El bloque de ese proveedor se cierra únicamente cuando:

- el adaptador utiliza el producto/API y autenticación autorizados;
- la consulta queda distinguida de la ejecución manual en modelo, respuesta y UI;
- los resultados conservan procedencia e identificadores verificables;
- permisos, límites, errores, paginación, idempotencia y revocación tienen cobertura;
- una prueba con credenciales reales autorizadas pasó en el entorno indicado;
- no se guardan contraseñas personales ni se sortean controles;
- plan, continuidad, contratos, estado del producto y pruebas describen el alcance real;
- la puerta integral de `AGENTS.md` termina con código 0.

Si no existe interés funcional suficiente o permiso programático, la decisión correcta es mantener búsqueda manual asistida e importación; no es una brecha que bloquee el producto base.

## 8. Fuentes primarias consultadas

Consultadas el 26/10/2026. Las condiciones de API pueden cambiar; volver a confirmar en el portal y con UTP justo antes de implementar.

- Elsevier, [API Authentication](https://dev.elsevier.com/tecdoc_api_authentication.html): la API key identifica la aplicación y los accesos específicos requieren entitlement verificado; documenta formas de autenticación institucional.
- Elsevier, [Scopus APIs](https://dev.elsevier.com/sc_apis.html): categorías de acceso académico/no comercial y comercial, sujetos a políticas y uso permitido.
- Elsevier, [Support / API access FAQ](https://dev.elsevier.com/support.html): API key por sí sola no da acceso a datos; acceso y permisos dependen de elegibilidad/entitlement y suscripción aplicable.
- Clarivate, [Web of Science API Expanded](https://developer.dev-stable.clarivate.com/apis/wos): describe la API y declara que requiere licencia pagada cuyo plan depende de la suscripción Web of Science.
- Clarivate, [Developer Portal: cómo comenzar](https://developer.clarivate.com/): registro de portal, registro de aplicación, suscripción a API y obtención de credenciales según plan/aprobación.

La evidencia consultada explica requisitos generales del proveedor; **no acredita el contrato ni el entitlement específico de UTP**.
