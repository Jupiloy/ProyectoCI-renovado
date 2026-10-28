# Plan de Implementación: Entrega B5 - Recorrido y Prompts Configurables por Proyecto

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar en el backend de TesisMCP la persistencia de versiones de recorrido y plantillas de prompts por proyecto (borrador y publicado, diff, restauración, aislamiento y concurrencia optimista), la ejecución flexible según dependencias reales conservando compatibilidad para proyectos legados P01–P32, la validación protegida en `submit_chapter`, y la trazabilidad inmutable de versiones en cada revisión.

**Architecture:** Capa desacoplada en tres niveles: (1) Modelos de versiones de workflow (`ProjectWorkflow`, `WorkflowTask`, `WorkflowDependency`, `WorkflowPrompt`) con `workflow_mode` en `ResearchProfile`; (2) Servicios de dominio (`thesis.services.workflows`, `workflow_template`) con grafo dirigido acíclico, validación estricta y bloqueo optimista `expected_version`; (3) Adaptación de `save_step`, `submit_chapter` y materializadores para alternar entre modo legado secuencial y modo configurable por dependencias; (4) API REST Django Ninja bajo `/api/v1/projects/{project_id}/workflow/` con sesión y aislamiento estricto por proyecto.

**Tech Stack:** Python 3.12+, Django 5.x, Django Ninja, PostgreSQL 16 + pgvector, Pydantic v2 (StrictOutput), pytest-django.

**Spec:** [docs/02_arquitectura_y_sistema/contrato_recorrido_y_prompts_configurables.md](../../02_arquitectura_y_sistema/contrato_recorrido_y_prompts_configurables.md) y [docs/02_arquitectura_y_sistema/criterio_backend_listo_para_frontend.md](../../02_arquitectura_y_sistema/criterio_backend_listo_para_frontend.md).

## Global Constraints

- Trabajar exclusivamente en `/home/janr/Documentos/Universidad/Apuntes_Obsidian/Estudiando/Ciclo7/Curso Integrador 1/ProyectoCI`.
- Cero tolerancia a alucinaciones (Grounded Truth); nunca inventar métricas, números ni accesos.
- Reglas de autorización en servidor; ningún prompt ni cliente aporta `user_id` ni permisos.
- Control de concurrencia optimista (`expected_version` / `lock_version`) en todas las mutaciones.
- Inmutabilidad de revisiones publicadas, aprobaciones y eventos; borrado protegido (`PROTECT`).
- Compatibilidad absoluta con proyectos legados P01–P32 y los 59 tests actuales.
- Ejecutar `python3 scripts/verify_project.py` al cerrar la entrega con código de salida 0.

## Review Focus

- Intento de acceso cruzado: un usuario autenticado intenta consultar o editar el recorrido de un proyecto ajeno -> debe retornar `DomainError("NOT_FOUND", ...)` / HTTP 404 sin filtrar existencia.
- Conflicto concurrente: dos llamadas simultáneas a editar o publicar borrador con la misma `expected_version` -> la segunda debe fallar con `DomainError("VERSION_CONFLICT", ...)`.
- Grafo con ciclos: el usuario intenta publicar dependencias cíclicas (A -> B -> A) -> debe rechazarse con `DomainError("VALIDATION_ERROR", "El recorrido contiene dependencias cíclicas")`.
- Violación de control protegido: el usuario intenta desactivar una tarea protegida (ej. P04 título, P16 evidencia, P28 ética) -> rechazo estricto sin permitir bypass.
- Adelanto de tarea independiente vs bloqueo por dependencia real: en modo configurable, adelantar una búsqueda (P13) sin P05 debe triunfar; ejecutar P06 sin P04 debe bloquear con `DomainError("PREREQUISITE_LOCKED", ...)`.

---

### Task 1: Modelos de Recorrido Configurable, Prompts y Migración Django 0019

**Files:**
- Create: `backend/thesis/models/workflows.py`
- Modify: `backend/thesis/models/research.py:10-30`
- Modify: `backend/thesis/models/chapters.py:10-50`
- Modify: `backend/thesis/models/__init__.py:1-40`
- Create: `backend/thesis/migrations/0019_configurable_workflows_and_prompts.py`
- Modify: `scripts/verify_project.py:212-228`

**Interfaces:**
- Consumes: `Project`, `User` de `thesis.models`
- Produces: `ProjectWorkflow`, `WorkflowTask`, `WorkflowDependency`, `WorkflowPrompt` exportados en `thesis.models`

- [ ] **Step 1: Escribir prueba fallida para los nuevos modelos de workflow**
Crear `backend/thesis/tests/test_workflow_models.py` verificando que se puedan crear instancias de `ProjectWorkflow`, `WorkflowTask`, `WorkflowDependency`, `WorkflowPrompt`, y que `ResearchProfile` tenga `workflow_mode` y `active_workflow`.

- [ ] **Step 2: Ejecutar test para verificar que falla**
Run: `.venv/bin/pytest backend/thesis/tests/test_workflow_models.py -v`
Expected: FAIL con `ImportError` o `AttributeError`.

- [ ] **Step 3: Implementar modelos en `backend/thesis/models/workflows.py` y actualizar `research.py`, `chapters.py` y `__init__.py`**
- `ProjectWorkflow`: fields `project`, `version_no`, `status` (`DRAFT`, `PUBLISHED`, `RETIRED`), `base_template_version`, `change_summary`, `content_sha256`, `created_by`, `parent_workflow`, `lock_version`, timestamps.
- `WorkflowTask`: fields `workflow`, `task_id`, `legacy_step_code`, `title`, `description`, `chapter_no`, `order_index`, `is_active`, `is_optional`, `is_protected`, `contract_name`, `branch_condition`.
- `WorkflowDependency`: fields `workflow`, `source_task`, `target_task`, `dependency_type`, `required_field`, `is_blocking`, `reason`.
- `WorkflowPrompt`: fields `task`, `prompt_text`, `prompt_version`, `provenance`, `parameters_schema`, `created_by`, `created_at`.
- `ResearchProfile`: agregar `workflow_mode` (`LEGACY_SEQUENTIAL`, `CONFIGURABLE_GRAPH`) con default `LEGACY_SEQUENTIAL`, y `active_workflow` FK null=True.
- `ChapterRevision`: agregar `workflow` FK null=True, `workflow_version_no` null=True, `prompt_text_used` blank=True, `context_snapshot` default=dict.
- `StepProgress`: agregar `workflow` FK null=True, `workflow_version_no` null=True, `task_id` blank=True.

- [ ] **Step 4: Generar migración Django y aplicarla**
Run: `DJANGO_DEBUG=1 .venv/bin/python backend/manage.py makemigrations thesis -n configurable_workflows_and_prompts`
Run: `DJANGO_DEBUG=1 .venv/bin/python backend/manage.py migrate`

- [ ] **Step 5: Actualizar conteos en `scripts/verify_project.py`**
El gate actual debe contar 32 modelos y 20 migraciones tras añadir `WorkflowTaskExecution` y la migración `0020`.

- [ ] **Step 6: Ejecutar test de modelos para verificar que pasa**
Run: `.venv/bin/pytest backend/thesis/tests/test_workflow_models.py -v`
Expected: PASS.

---

### Task 2: Servicio de Catálogo Base e Inicialización de Plantilla de Recorrido

**Files:**
- Create: `backend/thesis/services/workflow_template.py`
- Test: `backend/thesis/tests/test_workflow_template.py`

**Interfaces:**
- Consumes: `CATALOGO_PASOS` de `thesis.step_catalogue`, `TEMPLATES_POR_PASO` de `mcp_server.prompts.templates`, modelos de `workflows.py`
- Produces: `initialize_project_workflow(project, user, base_template_version="catalogo_p01_p32_v1") -> ProjectWorkflow`
- Produces: `detect_workflow_cycles(tasks, dependencies) -> list[str]`

- [ ] **Step 1: Escribir prueba fallida para inicialización de plantilla y detección de ciclos**
Verificar que `initialize_project_workflow` crea 32 tareas correspondientes a P01–P32, asigna prompts predeterminados, crea dependencias lógicas clave (P04 -> P06, P04 -> P09, P09 -> P10, P09 -> P11, P11 -> P12, P11 -> P25, P12 -> P30, P16 -> P20, etc.), marca tareas protegidas (P04, P16, P20, P28), y que `detect_workflow_cycles` detecta ciclos dirigidos.

- [ ] **Step 2: Ejecutar test para verificar que falla**
Run: `.venv/bin/pytest backend/thesis/tests/test_workflow_template.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'thesis.services.workflow_template'`.

- [ ] **Step 3: Implementar `workflow_template.py`**
Implementar la carga inicial de tareas, prompts y dependencias desde `CATALOGO_PASOS` y `mcp_server/prompts/templates/`, con marcado de `is_protected` y algoritmo de detección de ciclos por DFS (búsqueda en profundidad con detección de back-edges).

- [ ] **Step 4: Ejecutar test para verificar que pasa**
Run: `.venv/bin/pytest backend/thesis/tests/test_workflow_template.py -v`
Expected: PASS.

---

### Task 3: Servicio de Dominio para Recorrido y Prompts (`thesis.services.workflows`)

**Files:**
- Create: `backend/thesis/services/workflows.py`
- Test: `backend/thesis/tests/test_workflows_service.py`

**Interfaces:**
- Consumes: `require_project` de `thesis.services.access`, modelos de `thesis.models`
- Produces:
  - `get_workflow_state(actor, project_id) -> dict`
  - `create_or_update_draft(actor, project_id, draft_payload: dict, expected_version: int) -> dict`
  - `validate_workflow_draft(actor, project_id) -> dict`
  - `publish_workflow_draft(actor, project_id, change_summary: str, expected_version: int) -> dict`
  - `restore_workflow_version(actor, project_id, target_version_no: int, change_summary: str) -> dict`
  - `get_effective_prompt(actor, project_id, task_id: str) -> dict`

- [ ] **Step 1: Escribir pruebas unitarias y de integración para el servicio**
Incluir casos de:
- Inicialización perezosa de workflow en proyecto nuevo.
- Consulta de estado por tesista y asesor.
- Rechazo a usuario ajeno (`NOT_FOUND`).
- Edición de borrador (modificar texto de prompt, cambiar orden_index, marcar opcional).
- Conflicto de versión concurrente (`VERSION_CONFLICT`).
- Rechazo de dependencias cíclicas en validación/publicación.
- Rechazo a desactivar control protegido (`is_protected=True`).
- Publicación de versión inmutable con cálculo de hash SHA-256.
- Restauración de versión anterior creando una nueva versión append-only.

- [ ] **Step 2: Ejecutar test para verificar que falla**
Run: `.venv/bin/pytest backend/thesis/tests/test_workflows_service.py -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: Implementar `backend/thesis/services/workflows.py`**
Implementar transacciones atómicas con `select_for_update()`, validación de permisos con `require_project(owner_only=True)` para mutaciones, control de concurrencia optimista, cálculo de diff entre versiones, y trazabilidad inmutable.

- [ ] **Step 4: Ejecutar test para verificar que pasa**
Run: `.venv/bin/pytest backend/thesis/tests/test_workflows_service.py -v`
Expected: PASS.

---

### Task 4: API REST Ninja para Recorrido y Prompts (`/api/v1/projects/{project_id}/workflow/`)

**Files:**
- Modify: `backend/thesis/api/projects.py`
- Test: `backend/thesis/tests/test_workflow_api.py`

**Interfaces:**
- Consumes: funciones de `thesis.services.workflows`
- Produces: Endpoints HTTP autenticados:
  - `GET /projects/{project_id}/workflow`
  - `PUT /projects/{project_id}/workflow/draft`
  - `POST /projects/{project_id}/workflow/validate`
  - `POST /projects/{project_id}/workflow/publish`
  - `POST /projects/{project_id}/workflow/restore`
  - `GET /projects/{project_id}/workflow/tasks/{task_id}/prompt`

- [ ] **Step 1: Escribir pruebas de API**
Pruebas usando `django.test.Client`:
- `GET /projects/{project_id}/workflow`: 200 para titular y asesor, 404 para outsider.
- `PUT /projects/{project_id}/workflow/draft`: 200 con retorno de `state_version` y diff.
- Conflicto concurrente 409 (`VERSION_CONFLICT`).
- `POST /projects/{project_id}/workflow/validate`: 200 con `valid: true/false` y lista de errores tipados.
- `POST /projects/{project_id}/workflow/publish`: 200 creando versión publicada inmutable.
- `POST /projects/{project_id}/workflow/restore`: 200 generando nueva versión publicada.

- [ ] **Step 2: Ejecutar test para verificar que falla**
Run: `.venv/bin/pytest backend/thesis/tests/test_workflow_api.py -v`
Expected: FAIL con 404 o ruta no encontrada.

- [ ] **Step 3: Agregar esquemas Ninja y rutas en `backend/thesis/api/projects.py`**
Implementar los esquemas `WorkflowTaskIn`, `WorkflowDraftIn`, `PublishWorkflowIn`, `RestoreWorkflowIn` y vincular los endpoints con `workflows.py`.

- [ ] **Step 4: Ejecutar test de API para verificar que pasa**
Run: `.venv/bin/pytest backend/thesis/tests/test_workflow_api.py -v`
Expected: PASS.

---

### Task 5: Ejecución Flexible en `save_step`, Materializadores y `submit_chapter`

**Files:**
- Modify: `backend/thesis/services/steps.py:80-125`
- Modify: `backend/thesis/services/step_materializers/literature.py:25-50`
- Modify: `backend/thesis/services/step_materializers/consistency.py:50-80`
- Test: `backend/thesis/tests/test_flexible_execution.py`

**Interfaces:**
- Consumes: `ProjectWorkflow`, `WorkflowDependency`, `WorkflowTask`
- Produces:
  - `save_step` evalúa `profile.workflow_mode`:
    - Si `LEGACY_SEQUENTIAL`: respeta secuencia fija P01–P32.
    - Si `CONFIGURABLE_GRAPH`: evalúa grafo publicado y dependencias activas bloqueantes.
  - `submit_chapter` evalúa tareas activas obligatorias del capítulo en el workflow publicado.
  - Trazabilidad en `ChapterRevision`: vincula `workflow_id`, `workflow_version_no`, `prompt_text_used`, `context_snapshot`.

- [ ] **Step 1: Escribir pruebas de ejecución flexible**
Crear `backend/thesis/tests/test_flexible_execution.py`:
- Un proyecto en modo `LEGACY_SEQUENTIAL` sigue exigiendo el paso inmediatamente anterior (comprobación de no regresión).
- Un proyecto que publica un workflow configurable puede adelantar una tarea independiente (ej. P13/P14 literatura) sin completar P05 ni P12.
- Una tarea con dependencias no satisfechas (ej. P06 sin P04) es bloqueada con `PREREQUISITE_LOCKED` y código de dependencia faltante.
- Guardar una revisión en modo configurable guarda la versión exacta de workflow y prompt en `ChapterRevision`.
- Publicar una nueva versión de workflow después no altera la versión registrada en revisiones anteriores.
- `submit_chapter` en modo configurable: si una tarea opcional fue desactivada, el capítulo puede enviarse con éxito; si una tarea obligatoria o protegida falta, se bloquea con `PREREQUISITE_LOCKED`.

- [ ] **Step 2: Ejecutar test para verificar que falla**
Run: `.venv/bin/pytest backend/thesis/tests/test_flexible_execution.py -v`
Expected: FAIL.

- [ ] **Step 3: Implementar la lógica flexible en `steps.py` y actualizar materializadores**
- En `save_step`: branching según `profile.workflow_mode`. Si es configurable, consultar `profile.active_workflow`, verificar que las dependencias bloqueantes estén `COMPLETED` en `StepProgress`, registrar `workflow_version_no` y `prompt_text_used` en `ChapterRevision` y `StepProgress`.
- En `step_materializers/literature.py`: consultar P15 y P14 de forma segura (`StepProgress.filter(...)`) para tolerar workflows donde P15 sea opcional o P14 use defaults.
- En `submit_chapter`: si el proyecto está en modo configurable, consultar las tareas del capítulo en `profile.active_workflow` que estén activas y no sean opcionales.

- [ ] **Step 4: Ejecutar test de ejecución flexible y la suite de flow académica**
Run: `.venv/bin/pytest backend/thesis/tests/test_flexible_execution.py backend/thesis/tests/test_academic_flow.py -v`
Expected: ALL PASS.

---

### Task 6: Documentación, Integración y Puerta Determinista de Verificación (DoD)

**Files:**
- Modify: `docs/02_arquitectura_y_sistema/criterio_backend_listo_para_frontend.md`
- Modify: `docs/07_desarrollo_prototipo/estado_version_producto.md`
- Modify: `docs/02_arquitectura_y_sistema/inventario_brechas_backend.md`
- Modify: `backend/README.md`
- Verify: `scripts/verify_project.py`

- [ ] **Step 1: Actualizar la documentación con las capacidades verificadas de B5**
Documentar los nuevos modelos (32), migraciones (20), endpoints de `/api/v1/projects/{project_id}/workflow/`, modo dual de ejecución (`LEGACY_SEQUENTIAL` vs `CONFIGURABLE_GRAPH`), y contratos de petición/respuesta reales.

- [ ] **Step 2: Ejecutar la suite completa de pytest**
Run: `DJANGO_DEBUG=1 .venv/bin/pytest --reuse-db -q`
Expected: 100% de tests en verde (59 anteriores + nuevos tests de B5).

- [ ] **Step 3: Ejecutar la barrera determinista DoD**
Run: `python3 scripts/verify_project.py`
Expected: Código de salida 0 `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]`.

- [ ] **Step 4: Generar reporte de cierre de entrega B5**
Presentar la tabla de evidencia ejecutada, archivos modificados, ejemplo de petición/respuesta y la preparación para la siguiente entrega (B1 y B2).
