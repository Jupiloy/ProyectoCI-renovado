# B6 — Lotes, worker concurrente, síntesis e invitaciones puntuales

**Objetivo del bloque:** coordinar tareas IA independientes, agilizar su revisión y habilitar contribuciones acotadas de expertos/bibliotecarios. B6 no convierte multiagentes en autoridades: la salida siempre conserva procedencia, permisos y revisión humana.

## Resultado integrado

| Subbloque | Función | Persistencia/API | Estado al cierre de este paquete |
|---|---|---|---|
| B6.1 | Crear lote de 1–8 tareas independientes, reutilizar un `AIGenerationJob` por tarea, consultar progreso, cancelar solo colas. | `AIGenerationBatch`, `AIGenerationBatchItem`; `/ai-batches`. | Implementado/verificado antes de esta entrega. |
| B6.2 | Reclamo atómico, concurrencia limitada dentro de un proceso, worker singleton entre procesos y recuperación conservadora. | Sin modelos nuevos; `run_ai_worker`. | Implementado/verificado antes de esta entrega. |
| B6.3 | Congelar outputs exitosos seleccionados, producir síntesis estructurada, verificar referencias y permitir decisión del titular. | `AIGenerationBatchSynthesis`; `/ai-batches/{id}/syntheses`. | Implementado y verificado; gate B6 7/7. |
| B6.4 | Invitar a usuario existente a revisar una tarea con materiales explícitos y aportar texto sin acceso global. | `ProjectSupportInvitation`, `SupportInvitationSource`, `SupportContribution`; `/support-invitations`. | Implementado y verificado; gate B6 7/7. |

## Límites compartidos

1. El worker usa una cola y un control de concurrencia compartidos. B6.3 no crea un segundo worker; síntesis y generación compiten ordenadas por antigüedad de creación.
2. `SUCCEEDED` significa ejecución completada y salida válida según esquema. No significa que el asesor o tesista haya aprobado el contenido.
3. Síntesis aceptada es un informe auxiliar. No escribe en el editor, no acepta jobs fuente ni cambia estados de tareas o tesis.
4. Una persona invitada no es `ProjectParticipant`. La invitación concede acceso temporal solo a una tarea y fuentes explícitas. Su respuesta es un aporte append-only, no una revisión oficial ni una aprobación.
5. El correo no se envía desde la plataforma en este bloque; se devuelve el token una sola vez para compartir manualmente con la cuenta existente invitada.
6. Proveedor IA real, credenciales, coste, políticas de retención institucional y despliegue público requieren pruebas/decisiones externas. Los tests de contrato no demuestran conexión de producción.

## Corte técnico

- 51 modelos Django esperados y 37 migraciones numeradas hasta `0037`.
- La migración `0037_projectsupportinvitation_supportcontribution_and_more.py` agrega cuatro modelos y controles PostgreSQL de inmutabilidad/alcance.
- Archivos principales: `backend/thesis/models/ai_batches.py`, `backend/thesis/models/support.py`, `backend/thesis/services/batch_synthesis.py`, `backend/thesis/services/support_invitations.py`, `backend/thesis/services/ai_jobs.py`, `backend/thesis/api/projects.py`.
- Pruebas focalizadas: `backend/thesis/tests/test_ai_batches.py` y `backend/thesis/tests/test_support_invitations.py`.
- Evidencia de cierre integral: `TESISMCP_DB_CONTAINER=tesismcp-local-pg ./scripts/verify_podman.sh` pasó 7/7, total 395.34 s y pytest 374.20 s, exit code 0. El resultado también está registrado en [guía de continuidad](./guia_continuidad_backend.md), [pendientes backend](./pendientes_backend_despues_b4.md), [estado de producto](../07_desarrollo_prototipo/estado_version_producto.md) y READMEs.

## Siguiente ruta de desarrollo

Cerrar B6 no equivale a terminar todo el backend. El trabajo posterior sigue el [plan de entregas](./plan_entregas_backend.md) y el [criterio backend listo para frontend](./criterio_backend_listo_para_frontend.md): integrar el editor frontend con B1/B2, resolver anclas por bloque y round-trip, hacer prueba con proveedor IA real al disponer de credenciales, y abordar B7 documentos, B8 figuras/datos y operación/despliegue según prioridad. La búsqueda de Scopus/WoS manual sigue disponible sin API; APIs licenciadas son opcionales.
