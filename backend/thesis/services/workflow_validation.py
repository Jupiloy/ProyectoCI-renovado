"""Servicios de recorridos configurables."""

from typing import Any
from uuid import UUID

from thesis.models import ProjectWorkflow, WorkflowDependency
from thesis.services.access import require_project
from thesis.services.workflow_template import BASE_DEPENDENCIES, detect_workflow_cycles


def validate_workflow_draft(actor: Any, project_id: UUID) -> dict[str, Any]:
    """Valida la consistencia estructural del borrador (ciclos, tareas protegidas, referencias)."""
    project = require_project(actor, project_id)
    draft = (
        ProjectWorkflow.objects.filter(project=project, status=ProjectWorkflow.Status.DRAFT)
        .order_by("-version_no")
        .first()
    )
    if not draft:
        return {"valid": True, "errors": [], "warnings": []}

    errors: list[str] = []
    warnings: list[str] = []

    tasks = list(draft.tasks.all())
    task_ids = [t.task_id for t in tasks]
    active_tasks = {t.task_id: t for t in tasks if t.is_active}

    # 1. Unicidad de task_ids
    if len(set(task_ids)) != len(task_ids):
        errors.append("Existen identificadores de tareas duplicados en el recorrido")

    # 2. Protección de controles núcleo
    for t in tasks:
        if t.is_protected:
            if not t.is_active:
                errors.append(f"La tarea protegida '{t.task_id}' no puede estar desactivada")
            if t.is_optional:
                errors.append(f"La tarea protegida '{t.task_id}' no puede ser opcional")

    # 3. Detección de ciclos
    deps = list(draft.dependencies.select_related("source_task", "target_task"))
    dependency_keys = {
        (d.source_task.task_id, d.target_task.task_id, d.dependency_type, d.is_blocking)
        for d in deps
    }
    for required in BASE_DEPENDENCIES:
        source, target = required["source"], required["target"]
        if source in active_tasks and target in active_tasks and (
            source, target, WorkflowDependency.Type.DATA_REQUIRED, True
        ) not in dependency_keys:
            errors.append(f"Dependencia académica obligatoria ausente o no bloqueante: {source} requiere {target}")
    for dep in deps:
        if (
            dep.workflow_id != draft.pk
            or dep.source_task.workflow_id != draft.pk
            or dep.target_task.workflow_id != draft.pk
            or dep.source_task_id == dep.target_task_id
        ):
            errors.append("Dependencia inválida: las tareas deben pertenecer al mismo recorrido y ser distintas")
        if dep.dependency_type != WorkflowDependency.Type.DATA_REQUIRED:
            errors.append(
                f"La dependencia {dep.dependency_type} aún no tiene compuerta de ejecución y no se puede publicar"
            )
    dep_dicts = [
        {"source": d.source_task.task_id, "target": d.target_task.task_id}
        for d in deps
    ]
    cycles = detect_workflow_cycles(list(active_tasks.keys()), dep_dicts)
    if cycles:
        errors.append(f"Dependencia cíclica detectada en: {' -> '.join(cycles)}")

    # 4. Dependencias que apuntan a tareas inactivas
    for d in deps:
        if d.source_task.task_id in active_tasks and d.target_task.task_id not in active_tasks:
            errors.append(
                f"La tarea activa '{d.source_task.task_id}' depende de '{d.target_task.task_id}', que está desactivada"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
