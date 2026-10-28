# Paso 1: acceso web y selección de proyecto

Fecha: 27/10/2026. Proyecto vigente: `ProyectoCI-renovado`. Frontend vigente para esta integración: `TesisMCP/`; `TesisMCP_Frontend/` conserva el prototipo anterior y no es el destino de esta tarea.

## Estado y siguiente modelo

**1A, backend y contrato:** implementado y comprobado mediante las pruebas focalizadas descritas al final. **1B, frontend de acceso/proyectos:** implementado, revisado por Sol High y corregido; tipos y compilación en verde. La prueba con sesión real en navegador sigue pendiente. La puerta integral se reserva para el cierre de las correcciones, según la indicación del usuario; la compilación no acredita todo el backend ni el recorrido interactivo.

## Contrato existente de sesión

Las rutas de sesión terminan en `/` y usan cookies Django; no crear JWT ni almacenar credenciales en localStorage.

| Acción | Ruta | Entrada | Respuesta y conducta |
| --- | --- | --- | --- |
| Consultar sesión y obtener CSRF | `GET /api/v1/auth/session/` | Sin cuerpo | `200` con `authenticated: bool`, `user: null` o `{id,email,display_name}`, `csrf_token: string`. Un usuario sin sesión también recibe 200; interpretar `authenticated`. |
| Iniciar sesión | `POST /api/v1/auth/login/` | JSON **solo** `{email,password}`; cabecera `X-CSRFToken` y cookies | `200` con la misma estructura y un nuevo `csrf_token`. Reemplazar el token en memoria porque el login rota CSRF. `401` credenciales inválidas, `400` JSON inválido, `413` cuerpo excesivo, `403` CSRF. |
| Cerrar sesión | `POST /api/v1/auth/logout/` | Cookies y `X-CSRFToken` | `200 {authenticated:false}`. Limpiar datos del usuario/proyecto tras confirmación; en caso de fallo de red no fingir cierre del servidor. |

`user.id` es string. No hay rol académico global en `user`. El rol pertenece a la membresía de cada proyecto. Las cuentas se crean mediante Django Admin o administración local; registro abierto y recuperación de contraseña siguen pendientes. No simular esas funciones.

## Nuevo listado autorizado

`GET /api/v1/projects?offset=0&limit=50` devuelve:

```ts
type ProjectPermissions = {
  can_read_project: boolean;
  can_edit_document: boolean;
  can_manage_workflow: boolean;
  can_review_chapters: boolean;
};
type ProjectSummary = {
  project_id: string; // UUID
  name: string;
  title: string;
  status: "ACTIVE";
  role: "OWNER" | "ADVISOR";
  permissions: ProjectPermissions;
};
type ProjectPage = {
  projects: ProjectSummary[];
  offset: number;
  limit: number;
  has_more: boolean;
};
```

- Solo aparecen proyectos activos con membresía activa del usuario autenticado. Los apoyos invitados no adquieren membresía por recibir una invitación y no se agregan artificialmente a este listado.
- Orden estable por nombre del proyecto y UUID. `offset` debe ser no negativo, `limit` está entre 1 y 100, valor predeterminado 50. Límites inválidos devuelven 400; valores de consulta que no se pueden interpretar como enteros pueden devolver 422.
- Si no hay proyectos, `projects` es una lista vacía. Si `has_more` es verdadero, cargar la siguiente página con `offset + limit` sin repetir ni descartar filas.
- `OWNER`: lectura, edición del documento y gestión del recorrido; no revisión como asesor. `ADVISOR`: lectura y revisión de capítulos; no edición del documento ni gestión del recorrido.
- Estas capacidades describen el rol en ese momento. El estado del capítulo, el snapshot vigente y las validaciones de cada operación siguen aplicándose en servidor. Una capacidad almacenada en el navegador no conserva acceso tras revocar la membresía.
- Sin sesión: 401. El listado no expone proyectos ajenos, archivados o de membresía inactiva.

Creación ya existente: `POST /api/v1/projects`, JSON `{name,title?}`, cookies y CSRF. Devuelve **200** con estado de proyecto, no con `ProjectSummary`; después recargar el listado autorizado para obtener rol y permisos. No inventar soporte de idempotencia en esta operación.

Consulta ya existente: `GET /api/v1/projects/{project_id}` devuelve el estado de investigación (`project_id`, `name`, `title`, `status`, `state_version` y otros campos); no equivale al listado ni incluye actualmente el rol por sí solo. Obtener rol/permisos de la selección autorizada. Una URL o un ID guardado nunca autorizan el acceso por sí mismos.

## Encargo concreto para Luna: 1B

1. Leer este documento y la [matriz de integración](matriz_integracion_frontend_backend.md); inspeccionar `TesisMCP/src/App.tsx`, `src/api/client.ts`, `src/index.css`, `vite.config.ts`, `package.json` y `tsconfig.json`. Conservar el diseño del primer prototipo.
2. Crear tipos y funciones de sesión/proyectos en módulos pequeños bajo `TesisMCP/src/api/`. Mantener todas las peticiones dentro del cliente, con `credentials: "include"`. No mezclar funciones HTTP dentro de componentes de presentación.
3. Adaptar `apiRequest` para conservar el estado HTTP y un mensaje legible. Un error CSRF puede ser HTML; no asumir que todo error tiene JSON. Construir cabeceras de forma compatible con `HeadersInit`. No forzar JSON sobre `FormData`. No añadir reintentos automáticos de operaciones que escriben.
4. Conectar el arranque a `GET /auth/session/`: mostrar carga; si `authenticated` es falso, formulario real de correo y contraseña. Añadir errores y bloqueo de doble envío. No enviar rol en el login.
5. Al autenticar, actualizar CSRF en memoria y mostrar los proyectos autorizados. Permitir seleccionar proyecto y cargar otra página. Mostrar un estado vacío con opción de crear proyecto mediante el POST existente; conservar entradas del formulario si falla. No mostrar un total global contando solo la primera página.
6. Usar la selección del proyecto para obtener rol y permisos. Una misma cuenta puede ser tesista en un proyecto y asesora en otro. Ocultar acciones incompatibles en la interfaz, manteniendo siempre la autorización del backend. No cambiar roles mediante un selector local.
7. Al elegir proyecto, mostrar su nombre/título reales y el estado de conexión. Las secciones aún no integradas deben indicar que están pendientes; no mostrar cifras, actividad, citas o avances de la demostración como si pertenecieran al proyecto real. Mantener el modo demostración como entrada explícita y aislada del modo real.
8. Conectar cierre de sesión y cambio de proyecto. Al cerrar, limpiar usuario, proyecto y datos de su contexto. No almacenar contraseña ni token CSRF en localStorage. Ante 401 en modo real volver al acceso; ante 403 distinguir falta de permiso/CSRF; ante 404 de un proyecto recargar selección sin revelar datos ajenos. No repetir automáticamente una escritura tras refrescar CSRF.
9. Preparar ejecución local: `vite.config.ts` importa `./.figma/make/site.json`, que no existe en esta copia. Eliminar esa dependencia ausente o hacer que la configuración local funcione sin ella, conservando React/Tailwind y el diseño. Configurar un proxy de desarrollo de `/api` a Django (destino local configurable, inicialmente `http://127.0.0.1:8000`), conservando el Host del navegador (`changeOrigin: false`) y sin reescribir el prefijo. Django debe estar en desarrollo para cookies HTTP locales. No habilitar CORS indiscriminadamente ni desactivar CSRF. El puerto o base API no demuestra despliegue cloud.
10. Extraer solo los componentes necesarios de acceso y selección de proyectos. La división completa del editor, su árbol v2, citas, guardado, snapshots, Zotero y agente pertenecen a pasos posteriores. No reconstruir backend, roles ni autenticación.
11. Ejecutar una comprobación de tipos y una compilación del frontend cuando las dependencias estén disponibles (`pnpm exec tsc --noEmit`, `pnpm build`); no confundir compilación con inicio de sesión probado en navegador. Si falta una cuenta real configurada, declarar esa comprobación pendiente; no crear credenciales ficticias en el producto.
12. Actualizar este mismo MD con archivos cambiados, comprobaciones y pendientes, e indicar al usuario: **«Recuerda cambiar a Sol High para revisar el paso 1B antes de continuar con el editor»**.

## Cierre de 1B: acceso y selección en frontend

Estado: implementación frontend compilada. No se ha ejecutado una sesión desde navegador contra un Django activo ni se ha comprobado una cuenta institucional real.

### Archivos añadidos o adaptados

- `TesisMCP/src/api/types.ts`: contratos TypeScript para sesión, permisos, resumen/página de proyectos y estado del proyecto.
- `TesisMCP/src/api/auth.ts`: consulta de sesión, login y logout.
- `TesisMCP/src/api/projects.ts`: listado paginado, creación y lectura de proyectos.
- `TesisMCP/src/api/client.ts`: transporte same-origin con cookies, `X-CSRFToken`, errores que conservan HTTP status, respuestas HTML CSRF no expuestas como texto, cabeceras `Headers` y manejo que no fuerza JSON sobre `FormData`.
- `TesisMCP/src/App.tsx`: arranque consultando sesión; estados de acceso, lista, espacio conectado y demo aislada; carga de estado real del proyecto; logout y recuperación de sesión ante 401.
- `TesisMCP/src/features/auth/AccessScreen.tsx`: acceso institucional por correo/contraseña, CSRF, bloqueo de doble envío y errores; modo demo explícito.
- `TesisMCP/src/features/projects/ProjectSelectionScreen.tsx`: lista autorizada paginada, estados de carga/vacío/error, creación y apertura de proyecto, cambio de proyecto y cierre de sesión.
- `TesisMCP/src/features/projects/ConnectedProjectScreen.tsx`: muestra el nombre, título, rol y permisos obtenidos del backend, sin métricas inventadas; deja claro qué integraciones de documentos siguen pendientes.
- `TesisMCP/src/DemoApp.tsx`: antiguo prototipo aislado como modo de demostración, con acciones visibles para volver al acceso real o salir de la demo.
- `TesisMCP/src/index.css`: estilos de las nuevas pantallas y adaptación móvil, conservando React/Tailwind y el estilo del prototipo.
- `TesisMCP/vite.config.ts`: reemplaza la importación inexistente `./.figma/make/site.json` por metadatos locales y configura proxy `/api` hacia `TESISMCP_API_TARGET` o `http://127.0.0.1:8000`, con `changeOrigin: false` y sin reescritura de ruta.

### Comprobaciones ejecutadas

| Comando | Resultado | Tiempo | Código |
| --- | --- | --- | --- |
| `pnpm exec tsc --noEmit` | Tipos correctos; pnpm enlazó 43 paquetes ya presentes en su almacén local, sin descargas | 17.82 s | 0 |
| `pnpm build` | Vite compiló 23 módulos y produjo `dist/index.html`, CSS y JS | 2.92 s | 0 |
| Contraste de rutas/tipos contra `backend/config/auth_views.py`, `backend/config/urls.py` y `backend/thesis/api/routes_overview.py` | Rutas, claves y formas de respuesta concordantes por inspección de código | No cronometrada | Inspección estática |
| `python3 scripts/verify_project.py` | Diferida hasta la revisión/cierre global, según el plan acordado | No ejecutada | Sin veredicto |

### Correcciones tras la revisión Sol High

La revisión detectó tres fallos funcionales y una matriz desfasada. Se corrigieron sin añadir endpoints ni pruebas nuevas:

- `ProjectSelectionScreen.tsx` separa el error de carga inicial del error de una acción. Si falla el listado, muestra un estado de error con **Reintentar carga**; no afirma que la cuenta carezca de proyectos.
- Tras un `POST /projects` confirmado, valida y conserva el `project_id` durante la búsqueda y apertura. **Buscar proyecto creado** repite solo las consultas GET. Si la respuesta del POST se pierde o hay un error del servidor, bloquea un reenvío casual y pide revisar la lista antes de permitir otro intento explícito. Sin idempotencia del backend no se puede descartar toda duplicación ante pérdida de respuesta.
- `api/client.ts` identifica un rechazo CSRF conocido en la respuesta HTML de Django y `PERMISSION_DENIED` cuando viene en JSON. Los errores 403 de origen indeterminado se mantienen como tales; no se inventa su causa. El login, la creación y el logout pueden actualizar CSRF y pedir un nuevo clic, sin repetir automáticamente la escritura.
- `matriz_integracion_frontend_backend.md` ahora refleja la conexión real de sesión/proyectos y conserva pendientes de navegador, editor y fuentes.

| Comprobación tras las correcciones | Resultado | Tiempo observado | Código |
| --- | --- | --- | --- |
| `pnpm exec tsc --noEmit` | Sin errores de tipos tras la última guarda del ID | 6.30 s | 0 |
| `pnpm build` | Vite compiló 23 módulos tras la última guarda del ID | 2.72 s | 0 |
| Prueba de acceso real en navegador | Pendiente, requiere Django activo y cuenta configurada | No ejecutada | Sin veredicto |
| `python3 scripts/verify_project.py` | Reservada para el cierre global acordado | No ejecutada | Sin veredicto |

### Límites expresos antes del paso siguiente

- No se probó login/logout real con un navegador, cookies de una cuenta configurada ni backend Django encendido; la comprobación real de sesión queda pendiente.
- No se verificó visualmente el prototipo en navegador. La compilación confirma que Vite pudo construir el frontend, no la experiencia interactiva en runtime.
- No se añadió registro público ni recuperación de contraseña.
- El modo demo sigue usando datos de demostración dentro de `DemoApp`; su entrada es explícita y no se mezclan con el estado conectado.
- El espacio conectado solo muestra datos y permisos del proyecto. Editor, documentos, guardado/versiones, snapshots, citas, Zotero, asistente y revisión siguen siendo pasos posteriores.
- La creación usa el POST existente y vuelve a consultar el listado autorizado; no se añadió idempotencia ni lógica de autenticación nueva en backend.
- No se ejecutó la puerta global, la suite backend ni pruebas nuevas en esta subetapa.

**Siguiente acción:** comprobar el acceso con Django y una cuenta real en navegador cuando estén disponibles. Para diseñar el contrato del editor y el documento v2 del paso siguiente, continuar con Sol High; la implementación visual delimitada puede pasar después a Luna.

## Archivos backend de 1A

- [Servicio de proyectos](../../backend/thesis/services/projects.py): `list_user_projects`, filtro de membresía/estado, paginación y capacidades por rol.
- [Esquemas API](../../backend/thesis/api/schemas.py): `ProjectPermissionsOut`, `ProjectSummaryOut`, `ProjectListOut`.
- [Rutas](../../backend/thesis/api/routes_overview.py): `list_projects`, `GET /projects` con esquema tipado y operation_id propio.
- [Fachada compatible](../../backend/thesis/api/projects.py): exporta los nuevos símbolos siguiendo la estructura existente.
- [Pruebas focalizadas](../../backend/thesis/tests/test_web_access.py): sesión, CSRF, aislamiento, roles por proyecto, paginación, acceso revocado y creación/listado tras login.

No se modificaron modelos ni se añadieron migraciones. Los endpoints de sesión existentes se conservaron y se comprobaron mediante Django Client con CSRF real.

## Evidencia de 1A

Se usó la imagen local existente de verificación y PostgreSQL. Se montó el código de la copia renovada en solo lectura; no se reconstruyó la imagen ni se ejecutó la puerta integral. Django/pytest usa su base de pruebas; no se aplicaron migraciones ni escrituras de aplicación a la base activa desde este encargo.

| Comprobación | Resultado | Tiempo informado | Salida |
| --- | --- | --- | --- |
| `python -m pytest --reuse-db -q backend/thesis/tests/test_web_access.py` dentro de `localhost/tesismcp-verify:local`, con PostgreSQL local y `DJANGO_DEBUG=1` | 9 pruebas aprobadas; advertencia de deprecación de dependencia Google en Python 3.14 | 11.09 s | 0 |
| Revisión del diff contra originales temporales | Cambio acotado al contrato de selección; aislamiento comprobado | No cronometrada | Inspección estática |
| Puerta integral `scripts/verify_project.py` | Reservada para el cierre acordado | No ejecutada | Sin veredicto integral |

La comprobación de 1A no demuestra aún acceso desde el frontend real, experiencia visual ni funcionamiento de los servicios externos.
