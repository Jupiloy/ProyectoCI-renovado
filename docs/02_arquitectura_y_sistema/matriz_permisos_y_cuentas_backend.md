# Cuentas, autenticación y matriz de permisos del backend

**Estado:** describe permisos observados y comportamientos implementados a 26/10/2026. **Actualizado:** 26/10/2026.

## Estado comprobado

- Django usa el modelo `User` con correo como `USERNAME_FIELD`; la contraseña se procesa con el mecanismo Django.
- La API Django Ninja usa `django_auth`; existen `GET /api/v1/auth/session/`, `POST /api/v1/auth/login/` y `POST /api/v1/auth/logout/`. Las escrituras de sesión requieren CSRF y cookies Django.
- No hay auto-registro público, invitación de cuentas, recuperación de contraseña ni verificación de correo. La cuenta se provisiona por Django Admin/superusuario; esto es distinto de `/admin/` como experiencia final de tesista.
- `ProjectParticipant.Role` solo define `OWNER` (tesista) y `ADVISOR`.
- `assign_advisor` solo permite al titular asignar una cuenta activa ya existente, no permite asignarse a sí mismo y mantiene un asesor activo.
- B6.4 implementa invitaciones de apoyo temporales a cuentas activas existentes, ligadas a una tarea y fuentes explícitamente concedidas. El invitado acepta con token de un solo uso (solo su hash se persiste) y no se agrega a `ProjectParticipant`.
- `require_project` permite lectura a cualquier participante activo y oculta proyectos ajenos como `NOT_FOUND`; `owner_only=True` restringe mutaciones del titular.
- MCP usa tokens separados, almacenados como hash, con expiración/revocación. El modelo no selecciona la identidad.

Verificar estas observaciones contra el código vigente en cada implementación. La guía describe el corte inspeccionado, no garantiza que una rama posterior no haya cambiado.

## Defaults recomendados para el piloto web

1. **Acceso cerrado por invitación** para tesistas y asesores mientras se evalúa el prototipo. No lanzar auto-registro público sin una necesidad institucional clara.
2. **Sesión Django segura** para el frontend first-party, HTTPS fuera de local, cookies `Secure`/`HttpOnly`/`SameSite` según topología, CSRF en escrituras y cierre de sesión invalidante.
3. **Invitación de un asesor existente** mediante correo verificado y token de un solo uso, con expiración y aceptación explícita. Si el asesor no tiene cuenta, crear invitación pendiente; no activar una cuenta con contraseña enviada por correo.
4. **Recuperación de contraseña** mediante flujo Django de un solo uso con expiración y backend de correo configurado; respuestas que no revelen si el correo existe.
5. **Sin rol institucional obligatorio.** Superusuario/staff es administración técnica restringida; no participa automáticamente en evaluación académica.
6. **Un asesor activo en el piloto actual.** Si se requiere separar asesoría temática y metodológica, representarlas como capacidades asignadas a esa persona, no dos cuentas/roles obligatorios. Varios asesores requieren decisión y migración propia.
7. **Apoyo invitado por tarea, no rol institucional nuevo.** Implementado en B6.4: el tesista o asesor asignado invita una cuenta activa a una tarea y fuentes explícitas, con aceptación, vencimiento, revocación y auditoría append-only. No se añade `EXPERT` o `LIBRARIAN` como acceso global. El invitado entrega texto con referencias a extractos; no edita el borrador ni aprueba capítulos.

Los endpoints de sesión y la asignación de asesor a una cuenta existente están implementados; no equivalen a una experiencia completa de cuentas. Siguen pendientes el frontend integrado, alta/invitación de cuentas, recuperación/verificación de correo, limitación de intentos y el envío de correo. Los puntos anteriores sobre cuentas cerradas son recomendaciones para el piloto, no funciones ya construidas.

## Matriz actual y objetivo de permisos

`Sí (actual)` se basa en servicios inspeccionados y debe volver a verificarse al tocar esa operación. `Objetivo` es contrato de diseño.

| Acción | Titular/tesista actual | Asesor actual | Objetivo |
|---|---|---|---|
| Crear proyecto y quedar OWNER | Sí, requiere sesión | No como asesor de otro proyecto | Titular autenticado crea; servicio crea la membresía en transacción. |
| Consultar estado/capítulos/comentarios | Participante activo | Participante activo | Ambos ven el mismo proyecto con permisos de lectura; no se revela existencia de proyectos ajenos. |
| Guardar idea/P01–P32 | Sí, `owner_only` | No | Titular edita. Asesor comenta/revisa, no sustituye al tesista en su borrador. |
| Editar y publicar recorrido/prompts del propio proyecto | No existe en el corte observado | No existe en el corte observado | Titular crea borrador, valida y publica una nueva versión con control de conflictos. Asesor asignado consulta y propone observaciones; una política futura puede requerir su visto bueno para cambios que afecten un plan aprobado. Ninguno altera aprobaciones pasadas. No equivale a cambiar la plantilla global. |
| Cargar PDF/DOCX y pedir incorporación OpenAlex | Sí, `owner_only` en servicios inspeccionados | No | Titular solicita. A futuro el asesor puede proponer una fuente, pero no subirla en nombre del tesista salvo permiso explícito y auditado. |
| Consultar fuentes/extractos/pasajes | Participante activo | Participante activo | Lectura limitada al proyecto; exportaciones/descargas autorizadas igual. |
| Crear vínculo candidato afirmación–extracto | Titular (`owner_only=True`) | No | Tesista propone; estado inicial `CANDIDATE`; asesor decide el vínculo concreto. |
| Confirmar/rechazar vínculo de evidencia | No es decisión del titular en el flujo actual | Asesor del proyecto | Asesor revisa solo el vínculo concreto; no se interpreta como validación general de la fuente. |
| Enviar capítulo | Sí, titular | No | Titular presenta snapshot vigente completo. |
| Añadir/comentar observaciones | No | Sí, asesor asignado | Comentario debe apuntar al snapshot/revisión exacto. |
| Resolver comentario | No en flujo documentado | Sí, asesor | Registrar actor/fecha; definir si el tesista puede marcar “respondido” aparte de resolverlo. |
| Solicitar cambios/aprobar/reabrir | No | Sí, asesor asignado | Decisión ligada a versión exacta; aprobar sin observaciones abiertas; reapertura requiere motivo. |
| Invitar/reasignar asesor | Sí asigna cuenta existente hoy | No | Titular inicia invitación; aceptar y reasignar producen eventos. Cambio de asesor no reescribe decisiones pasadas. |
| Invitar experto/bibliotecario a tarea | Implementado B6.4; titular o asesor asignado | Implementado B6.4; titular o asesor asignado | Cuenta activa acepta token; recibe solo tarea y recursos concedidos; puede descargar un PDF compartido vigente; no obtiene membresía ni aprobación. El token plano se devuelve una vez y debe compartirse manualmente. |
| Administrar respuesta del invitado | Implementado B6.4; puede listar aportes | Implementado B6.4; puede listar aportes | Invitado guarda respuesta textual append-only e idempotente ligada a extractos concedidos. Titular/asesor la consulta; el tesista decide si incorpora por su flujo normal. Revocar bloquea lecturas nuevas, conserva aportes. |
| Mantener normativa/plantillas institucionales | No como participante de proyecto | No | Capacidad de administración institucional separada, con versiones y fuente oficial; no concede acceso a contenido de tesis privadas. En el piloto puede permanecer como operación técnica manual del equipo. |
| Cambiar metodología global | No existe superficie de usuario confirmada | No | Solo mantenedor autorizado de metodología; cambios son propuesta versionada y publicados explícitamente. Una edición del tesista afecta únicamente su proyecto. |
| Administrar proveedor/token/integración personal | No en web propia aún | No | Cada usuario autoriza su conexión; secretos aislados por usuario/institución y revocables. |
| Administrar plataforma | `is_staff`/superuser fuera del rol académico | Igual | Necesidad técnica mínima, auditoría y sin aprobación académica implícita. |

## Reglas de aislamiento obligatorias

- Toda operación recibe actor de sesión/token ya autenticado y busca el recurso bajo el proyecto autorizado.
- No confiar en `project_id` como permiso; validar membresía en servicio, también en jobs y descargas.
- Responder `NOT_FOUND` a actor no participante cuando revelar existencia del proyecto sea una filtración.
- Validar propietario/asesor en cada transición, no confiar en botones deshabilitados del frontend.
- Los cambios de membresía quedan auditados. Desactivar una cuenta no borra autoría/revisiones anteriores.
- MCP tiene scopes efectivos por membresía y proyecto. Revocar token detiene llamadas futuras sin borrar historial producido.
- Invitaciones de apoyo deben validar actor invitante, proyecto, tarea, recurso, expiración, aceptación y capacidad en cada request y job. No permitir ampliar el paquete por cambiar IDs desde cliente.
- No utilizar el rol `is_staff`/administrador de plataforma como atajo para revisar tesis. Cualquier acceso de soporte excepcional requiere motivo, alcance, registro y controles separados.

## Criterios de aceptación de cuentas y permisos

1. Usuario anónimo no consulta API protegida ni usa CSRF inválido para mutar.
2. Tesista A no lee ni muta proyecto B incluso con UUID válido obtenido por otro canal.
3. Asesor A no revisa un proyecto que no tiene asignado.
4. Asesor no guarda el paso como titular ni cambia el rol desde payload.
5. Proyecto tiene como máximo un titular y un asesor activo bajo el esquema actual; una invitación puntual no altera esa cardinalidad académica.
6. Invitación expirada/reutilizada/para otro correo no asigna membresía.
7. El cambio/revocación de membresía/token no modifica snapshots ni eventos históricos.
8. B6.4: invitado acepta una invitación vigente y solo consulta la tarea y recursos enumerados; no obtiene acceso a capítulos, proyectos, jobs o funciones de aprobación.
9. B6.4: invitado no puede guardar contenido canónico, aceptar propuestas, aprobar capítulos o crear invitaciones.
10. B6.4: revocar/caducar bloquea lecturas/descargas/aportes nuevos sin borrar las respuestas previas.

El alcance ejecutable de invitaciones está en [B6.4](./paquete_b6_4_invitaciones_apoyo.md); la [especificación de búsqueda y revisión de evidencia](./especificacion_busqueda_y_revision_de_evidencia.md) describe el contexto funcional más amplio.
