# B6.4 — Invitaciones de apoyo con acceso acotado

**Estado:** implementado y verificado; B6 completo pasó puerta integral 7/7, 395.34 s, exit code 0.  
**Propósito:** permitir que el tesista o asesor asignado solicite una revisión puntual de una persona experta o bibliotecaria y reducir la tarea manual sin incorporar esa persona como miembro general del proyecto.

## Política de acceso

- La persona invitada debe tener una cuenta activa existente y aceptar explícitamente una invitación vigente usando un token aleatorio. El sistema persiste solo SHA-256; el token plano se devuelve una sola vez al crear.
- La invitación queda ligada a proyecto, versión/recorrido, tarea activa publicada y una lista explícita de hasta 25 fuentes del mismo proyecto. Incluye instrucciones y vencimiento entre 1 hora y 30 días (por defecto 7 días).
- Titular y asesor asignado pueden crear/listar/revocar invitaciones y consultar aportes. Las cuentas invitadas no se agregan a `ProjectParticipant` ni adquieren roles globales.
- La persona invitada ve la descripción/instrucción de esa tarea, los metadatos y extractos de las fuentes compartidas (máximo 50 por fuente y 200 por invitación), y puede descargar solo el PDF concedido si existe, está dentro de `MEDIA_ROOT` y su SHA-256 coincide.
- Puede enviar una respuesta textual (1–10 000 caracteres), con referencias opcionales a extractos concedidos. Se guarda de manera append-only, idempotente y con hash. La respuesta no edita el manuscrito, pasos, fuentes, jobs, invitaciones, decisiones ni aprobaciones.
- Revocar impide nuevas consultas, descargas y aportes; no elimina el historial. Expirar también bloquea acceso aunque el registro de aceptación conserve el estado histórico. Token inválido, cuenta/email distintos, proyecto no activo o recurso fuera del grant no revela información y se rechaza.
- El envío del enlace/token se comparte manualmente en esta versión: no se afirma que exista integración de correo. No se permite adjuntar o subir archivos por parte del invitado en B6.4.

## API

Las rutas de administración están bajo `/api/v1/projects/{project_id}`; las rutas del invitado se resuelven por invitación y requieren sesión autenticada:

| Método y ruta | Permiso/efecto |
|---|---|
| `POST /support-invitations` | Titular o asesor asignado; correo de cuenta activa, `task_id`, `task_instructions`, `source_ids` (opcional) y `ttl_hours` (default 168). Devuelve token de un solo uso. |
| `GET /support-invitations` | Titular o asesor asignado; lista hasta 100 invitaciones. |
| `POST /support-invitations/{invitation_id}/revoke` | Titular o asesor asignado; revoca una invitación vigente. |
| `GET /support-invitations/{invitation_id}/contributions` | Titular o asesor asignado; consulta respuestas preservadas. |
| `POST /support-invitations/{invitation_id}/accept` | Cuenta autenticada con correo normalizado igual al invitado; requiere `invite_token`. |
| `GET /support-invitations/{invitation_id}/workspace` | Invitado aceptado y vigente; devuelve solo tarea e insumos concedidos. |
| `GET /support-invitations/{invitation_id}/sources/{source_id}/file` | Invitado aceptado; solo archivo concedido con hash válido. |
| `POST /support-invitations/{invitation_id}/contributions` | Invitado aceptado; requiere texto, UUID idempotente y `source_excerpt_ids` como IDs enteros de extractos dentro del grant. |

## Persistencia y defensa

- `ProjectSupportInvitation`: estado, task/workflow, correo, expiración, token hash, aceptación y revocación.
- `SupportInvitationSource`: grant inmutable a cada `SourceDocument`.
- `SupportContribution`: respuesta append-only y sus extractos asociados.
- La migración `0037` instala restricciones/índices y triggers PostgreSQL para proteger alcance, grants y respuestas. El servicio vuelve a comprobar actor, pertenencia y vigencia en cada operación; las comprobaciones de frontend no son autoridad.
- La invitación no se puede ampliar con IDs enviados en llamadas posteriores. Cada lectura/descarga deriva los permisos de los grants persistidos.

## Limitaciones y trabajo posterior

- No hay alta de cuenta, verificación de correo, envío de correo, carga de documentos, chat, edición canónica ni aprobación académica en este bloque.
- El invitado aporta texto y referencias a extractos existentes; el titular decide si lo incorpora y el asesor conserva sus funciones de revisión/aprobación.
- La política institucional de retención, consentimiento y operación fuera del prototipo debe definirse antes de invitar usuarios reales con datos sensibles.
- Los endpoints API tienen autenticación de sesión del producto. La entrega manual del token debe hacerse por un canal elegido por el usuario; el sistema no registra que ese canal sea seguro.

## Archivos principales

- `backend/thesis/models/support.py`: modelos de invitación, grant y aporte.
- `backend/thesis/services/support_invitations.py`: autorización, aceptación, expiración, revocación, workspace, descarga validada y aporte.
- `backend/thesis/api/projects.py`: endpoints REST.
- `backend/thesis/migrations/0037_projectsupportinvitation_supportcontribution_and_more.py`: tablas, constraints y triggers junto con B6.3.
- `backend/thesis/tests/test_support_invitations.py`: aceptación, no membresía, alcance de recursos, expiración, idempotencia, revocación, descarga y append-only sobre PostgreSQL.

El cierre integrado y el siguiente paso están en [B6 completo](./paquete_b6_completo.md) y [pendientes backend](./pendientes_backend_despues_b4.md).
