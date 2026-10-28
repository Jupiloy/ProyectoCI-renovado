"""Servicios de dominio para la gestión y ejecución de recorridos configurables."""

import re
from typing import Any
from uuid import UUID

from django.db import transaction

from thesis.models import (
    Project,
    ProjectWorkflow,
    ResearchProfile,
    StepProgress,
    WorkflowDependency,
    WorkflowPrompt,
    WorkflowTask,
    WorkflowTaskExecution,
)
from thesis.services.access import require_project
from thesis.services.workflow_validation import validate_workflow_draft
from thesis.services.workflow_execution import execute_custom_workflow_task, get_custom_workflow_task_executions
from thesis.services.workflow_serialization import _serialize_task, _serialize_workflow
from thesis.services.errors import DomainError
from thesis.services.output_schemas import validate_output_schema_definition
from thesis.services.workflow_template import (
    calculate_workflow_hash,
    initialize_project_workflow,
    workflow_content_dump,
)






def _ensure_project_has_workflow(project: Project, actor: Any) -> ProjectWorkflow:
    published = (
        ProjectWorkflow.objects.filter(project=project, status=ProjectWorkflow.Status.PUBLISHED)
        .order_by("-version_no")
        .first()
    )
    if not published:
        published = initialize_project_workflow(project, actor)
    return published


def get_workflow_state(actor: Any, project_id: UUID) -> dict[str, Any]:
    """Obtiene el estado completo del recorrido del proyecto: publicado, borrador e historial."""
    project = require_project(actor, project_id)
    _ensure_project_has_workflow(project, actor)

    published = (
        ProjectWorkflow.objects.filter(project=project, status=ProjectWorkflow.Status.PUBLISHED)
        .order_by("-version_no")
        .first()
    )
    draft = (
        ProjectWorkflow.objects.filter(project=project, status=ProjectWorkflow.Status.DRAFT)
        .order_by("-version_no")
        .first()
    )
    history = list(
        ProjectWorkflow.objects.filter(project=project)
        .order_by("-version_no")
        .values("version_no", "status", "change_summary", "content_sha256", "created_at")
    )
    for h in history:
        h["created_at"] = h["created_at"].isoformat()

    return {
        "project_id": str(project.id),
        "published": _serialize_workflow(published) if published else None,
        "draft": _serialize_workflow(draft) if draft else None,
        "history": history,
    }


def create_or_update_draft(
    actor: Any, project_id: UUID, draft_payload: dict[str, Any], expected_version: int
) -> dict[str, Any]:
    """Crea o edita la versión en borrador del recorrido para el titular del proyecto."""
    project = require_project(actor, project_id, owner_only=True)
    with transaction.atomic():
        published = _ensure_project_has_workflow(project, actor)
        draft = (
            ProjectWorkflow.objects.select_for_update()
            .filter(project=project, status=ProjectWorkflow.Status.DRAFT)
            .order_by("-version_no")
            .first()
        )

        if not draft:
            # Create fresh draft cloned from published
            latest_version = (
                ProjectWorkflow.objects.filter(project=project)
                .order_by("-version_no")
                .first()
                .version_no
            )
            draft = ProjectWorkflow.objects.create(
                project=project,
                version_no=latest_version + 1,
                status=ProjectWorkflow.Status.DRAFT,
                base_template_version=published.base_template_version,
                change_summary="Borrador de cambios al recorrido",
                created_by=actor,
                parent_workflow=published,
                lock_version=0,
            )
            # Clone tasks and prompts
            task_map = {}
            for t in published.tasks.select_related("prompt").all():
                new_t = WorkflowTask.objects.create(
                    workflow=draft,
                    task_id=t.task_id,
                    legacy_step_code=t.legacy_step_code,
                    title=t.title,
                    description=t.description,
                    chapter_no=t.chapter_no,
                    order_index=t.order_index,
                    is_active=t.is_active,
                    is_optional=t.is_optional,
                    is_protected=t.is_protected,
                    contract_name=t.contract_name,
                    output_schema=t.output_schema,
                    branch_condition=t.branch_condition,
                )
                task_map[t.task_id] = new_t
                if hasattr(t, "prompt") and t.prompt:
                    WorkflowPrompt.objects.create(
                        task=new_t,
                        prompt_text=t.prompt.prompt_text,
                        prompt_version=t.prompt.prompt_version,
                        provenance=t.prompt.provenance,
                        parameters_schema=t.prompt.parameters_schema,
                        created_by=actor,
                    )
            # Clone dependencies
            for d in published.dependencies.all():
                s_id = d.source_task.task_id
                t_id = d.target_task.task_id
                if s_id in task_map and t_id in task_map:
                    WorkflowDependency.objects.create(
                        workflow=draft,
                        source_task=task_map[s_id],
                        target_task=task_map[t_id],
                        dependency_type=d.dependency_type,
                        required_field=d.required_field,
                        is_blocking=d.is_blocking,
                        reason=d.reason,
                    )

        # Check optimistic concurrency
        if draft.lock_version != expected_version:
            raise DomainError(
                "VERSION_CONFLICT",
                f"El borrador del recorrido cambió (versión actual: {draft.lock_version}, esperada: {expected_version})",
            )

        # Apply updates to draft tasks
        existing_tasks = {t.task_id: t for t in draft.tasks.select_related("prompt").all()}
        for t_update in draft_payload.get("tasks", []):
            task_id = t_update.get("task_id")
            if not task_id:
                continue
            if task_id not in existing_tasks:
                title = (t_update.get("title") or "").strip()
                prompt_text = (t_update.get("prompt_text") or "").strip()
                if not re.fullmatch(r"USR_[A-Z0-9_-]{4,44}", task_id) or not title:
                    raise DomainError(
                        "VALIDATION_ERROR",
                        "Las tareas nuevas requieren un ID USR_ único y un título no vacío",
                    )
                if not prompt_text:
                    raise DomainError("VALIDATION_ERROR", "Una tarea personalizada requiere un prompt no vacío")
                if len(title) > 200 or len(prompt_text) > 50000:
                    raise DomainError("VALIDATION_ERROR", "El título o el prompt supera el límite permitido")
                output_schema = t_update.get("output_schema") or {}
                if output_schema:
                    validate_output_schema_definition(output_schema)
                chapter_no = t_update.get("chapter_no")
                if chapter_no is not None and not 1 <= chapter_no <= 7:
                    raise DomainError("VALIDATION_ERROR", "chapter_no debe estar entre 1 y 7 o ser null")
                if t_update.get("order_index") is not None and int(t_update["order_index"]) < 1:
                    raise DomainError("VALIDATION_ERROR", "order_index debe ser positivo")
                task_obj = WorkflowTask.objects.create(
                    workflow=draft, task_id=task_id, title=title,
                    description=(t_update.get("description") or "").strip(),
                    chapter_no=t_update.get("chapter_no"),
                    order_index=int(t_update.get("order_index") or (len(existing_tasks) + 1)),
                    is_active=True if t_update.get("is_active") is None else bool(t_update["is_active"]),
                    is_optional=True if t_update.get("is_optional") is None else bool(t_update["is_optional"]),
                    is_protected=False, contract_name="",
                    output_schema=output_schema,
                )
                existing_tasks[task_id] = task_obj
                WorkflowPrompt.objects.create(
                    task=task_obj, prompt_text=prompt_text, prompt_version=1,
                    provenance=WorkflowPrompt.Provenance.USER_EDITED, created_by=actor,
                )
                continue
            task_obj = existing_tasks[task_id]

            # Validate protected rules
            if task_obj.is_protected:
                if t_update.get("is_active") is False:
                    raise DomainError(
                        "VALIDATION_ERROR",
                        f"No se puede desactivar la tarea protegida '{task_obj.task_id}' ({task_obj.title})",
                    )
                if t_update.get("is_optional") is True:
                    raise DomainError(
                        "VALIDATION_ERROR",
                        f"No se puede marcar como opcional la tarea protegida '{task_obj.task_id}'",
                    )

            if t_update.get("order_index") is not None:
                task_obj.order_index = int(t_update["order_index"])
            if t_update.get("is_active") is not None:
                task_obj.is_active = bool(t_update["is_active"])
            if t_update.get("is_optional") is not None:
                task_obj.is_optional = bool(t_update["is_optional"])
            if t_update.get("title") is not None and t_update["title"].strip():
                task_obj.title = t_update["title"].strip()
            if t_update.get("output_schema") is not None:
                output_schema = t_update["output_schema"] or {}
                if output_schema:
                    validate_output_schema_definition(output_schema)
                task_obj.output_schema = output_schema
            task_obj.save()

            # Prompt text update
            if t_update.get("prompt_text") is not None:
                p_text = t_update["prompt_text"].strip()
                if hasattr(task_obj, "prompt") and task_obj.prompt:
                    p = task_obj.prompt
                    p.prompt_text = p_text
                    p.prompt_version += 1
                    p.provenance = WorkflowPrompt.Provenance.USER_EDITED
                    p.save(update_fields=["prompt_text", "prompt_version", "provenance"])
                else:
                    WorkflowPrompt.objects.create(
                        task=task_obj,
                        prompt_text=p_text,
                        prompt_version=1,
                        provenance=WorkflowPrompt.Provenance.USER_EDITED,
                        created_by=actor,
                    )

        # Apply updates to dependencies if provided
        if "dependencies" in draft_payload:
            incoming_deps = draft_payload["dependencies"]
            if incoming_deps is None:
                raise DomainError("VALIDATION_ERROR", "dependencies debe ser una lista, no null")
            draft.dependencies.all().delete()
            for dep_in in incoming_deps:
                s_id = dep_in.get("source")
                t_id = dep_in.get("target")
                if s_id not in existing_tasks or t_id not in existing_tasks:
                    raise DomainError("VALIDATION_ERROR", f"Dependencia referencia una tarea inexistente: {s_id} -> {t_id}")
                if s_id == t_id:
                    raise DomainError("VALIDATION_ERROR", "Una tarea no puede depender de sí misma")
                try:
                    dep_type = WorkflowDependency.Type(dep_in.get("type", WorkflowDependency.Type.DATA_REQUIRED))
                except ValueError as exc:
                    raise DomainError("VALIDATION_ERROR", "Tipo de dependencia no reconocido") from exc
                WorkflowDependency.objects.create(
                    workflow=draft, source_task=existing_tasks[s_id], target_task=existing_tasks[t_id],
                    dependency_type=dep_type, required_field=dep_in.get("field", ""),
                    is_blocking=dep_in.get("blocking", True), reason=dep_in.get("reason", ""),
                )

        draft.lock_version += 1
        draft.save(update_fields=["lock_version", "updated_at"])

    return get_workflow_state(actor, project_id)






def publish_workflow_draft(
    actor: Any, project_id: UUID, change_summary: str, expected_version: int
) -> dict[str, Any]:
    """Publica el borrador como nueva versión inmutable activa del proyecto."""
    project = require_project(actor, project_id, owner_only=True)
    with transaction.atomic():
        draft = (
            ProjectWorkflow.objects.select_for_update()
            .filter(project=project, status=ProjectWorkflow.Status.DRAFT)
            .order_by("-version_no")
            .first()
        )
        if not draft:
            raise DomainError("NOT_FOUND", "No existe un borrador de recorrido pendiente de publicar")

        if draft.lock_version != expected_version:
            raise DomainError(
                "VERSION_CONFLICT",
                f"El borrador cambió (versión: {draft.lock_version}, esperada: {expected_version})",
            )

        val = validate_workflow_draft(actor, project_id)
        if not val["valid"]:
            raise DomainError("VALIDATION_ERROR", f"Borrador no válido: {'; '.join(val['errors'])}")

        # Calculate hash
        tasks_dump, deps_dump, prompts_dump = workflow_content_dump(draft)
        draft.content_sha256 = calculate_workflow_hash(tasks_dump, deps_dump, prompts_dump)

        # Retire previously published workflows
        ProjectWorkflow.objects.filter(
            project=project, status=ProjectWorkflow.Status.PUBLISHED
        ).update(status=ProjectWorkflow.Status.RETIRED)

        draft.status = ProjectWorkflow.Status.PUBLISHED
        draft.change_summary = change_summary.strip() or "Recorrido publicado"
        draft.save(update_fields=["status", "change_summary", "content_sha256", "updated_at"])

        # Update profile to activate configurable graph mode
        profile = ResearchProfile.objects.select_for_update().get(project=project)
        profile.workflow_mode = ResearchProfile.WorkflowMode.CONFIGURABLE_GRAPH
        profile.active_workflow = draft
        profile.save(update_fields=["workflow_mode", "active_workflow", "updated_at"])

    return get_workflow_state(actor, project_id)


def restore_workflow_version(
    actor: Any, project_id: UUID, target_version_no: int, change_summary: str
) -> dict[str, Any]:
    """Restaura una versión histórica creando una nueva versión publicada inmutable."""
    project = require_project(actor, project_id, owner_only=True)
    with transaction.atomic():
        historical = ProjectWorkflow.objects.filter(
            project=project, version_no=target_version_no
        ).first()
        if not historical:
            raise DomainError("NOT_FOUND", f"Versión histórica {target_version_no} no encontrada")

        latest_version = (
            ProjectWorkflow.objects.filter(project=project)
            .order_by("-version_no")
            .first()
            .version_no
        )

        new_wf = ProjectWorkflow.objects.create(
            project=project,
            version_no=latest_version + 1,
            status=ProjectWorkflow.Status.PUBLISHED,
            base_template_version=historical.base_template_version,
            change_summary=f"Restaurado desde versión {target_version_no}: {change_summary}".strip(),
            created_by=actor,
            parent_workflow=historical,
            lock_version=0,
        )

        task_map = {}
        tasks_dump = []
        prompts_dump = {}

        for t in historical.tasks.select_related("prompt").all():
            new_t = WorkflowTask.objects.create(
                workflow=new_wf,
                task_id=t.task_id,
                legacy_step_code=t.legacy_step_code,
                title=t.title,
                description=t.description,
                chapter_no=t.chapter_no,
                order_index=t.order_index,
                is_active=t.is_active,
                is_optional=t.is_optional,
                is_protected=t.is_protected,
                contract_name=t.contract_name,
                output_schema=t.output_schema,
                branch_condition=t.branch_condition,
            )
            task_map[t.task_id] = new_t
            if hasattr(t, "prompt") and t.prompt:
                WorkflowPrompt.objects.create(
                    task=new_t,
                    prompt_text=t.prompt.prompt_text,
                    prompt_version=t.prompt.prompt_version,
                    provenance=t.prompt.provenance,
                    parameters_schema=t.prompt.parameters_schema,
                    created_by=actor,
                )
                prompts_dump[t.task_id] = {
                    "text": t.prompt.prompt_text, "version": t.prompt.prompt_version,
                    "provenance": t.prompt.provenance,
                    "parameters_schema": t.prompt.parameters_schema,
                }

        deps_dump = []
        for d in historical.dependencies.all():
            s_id = d.source_task.task_id
            t_id = d.target_task.task_id
            if s_id in task_map and t_id in task_map:
                WorkflowDependency.objects.create(
                    workflow=new_wf,
                    source_task=task_map[s_id],
                    target_task=task_map[t_id],
                    dependency_type=d.dependency_type,
                    required_field=d.required_field,
                    is_blocking=d.is_blocking,
                    reason=d.reason,
                )
                deps_dump.append({
                    "source": s_id, "target": t_id, "type": d.dependency_type,
                    "required_field": d.required_field, "blocking": d.is_blocking,
                    "reason": d.reason,
                })

        tasks_dump, deps_dump, prompts_dump = workflow_content_dump(new_wf)

        new_wf.content_sha256 = calculate_workflow_hash(tasks_dump, deps_dump, prompts_dump)
        new_wf.save(update_fields=["content_sha256", "updated_at"])

        # Retire previously published
        ProjectWorkflow.objects.filter(
            project=project, status=ProjectWorkflow.Status.PUBLISHED
        ).exclude(pk=new_wf.pk).update(status=ProjectWorkflow.Status.RETIRED)

        # Update profile
        profile = ResearchProfile.objects.select_for_update().get(project=project)
        profile.workflow_mode = ResearchProfile.WorkflowMode.CONFIGURABLE_GRAPH
        profile.active_workflow = new_wf
        profile.save(update_fields=["workflow_mode", "active_workflow", "updated_at"])

    return get_workflow_state(actor, project_id)




def get_effective_prompt(actor: Any, project_id: UUID, task_id: str) -> dict[str, Any]:
    """Consulta el texto exacto del prompt y metadatos efectivos para una tarea en la versión activa."""
    project = require_project(actor, project_id)
    _ensure_project_has_workflow(project, actor)

    profile = ResearchProfile.objects.get(project=project)
    active_wf = profile.active_workflow
    if not active_wf:
        active_wf = (
            ProjectWorkflow.objects.filter(project=project, status=ProjectWorkflow.Status.PUBLISHED)
            .order_by("-version_no")
            .first()
        )

    task = WorkflowTask.objects.select_related("prompt").filter(workflow=active_wf, task_id=task_id).first()
    if not task:
        raise DomainError("NOT_FOUND", f"Tarea '{task_id}' no encontrada en el recorrido activo")

    prompt = task.prompt if hasattr(task, "prompt") else None
    return {
        "task_id": task.task_id,
        "title": task.title,
        "workflow_version_no": active_wf.version_no,
        "is_protected": task.is_protected,
        "is_optional": task.is_optional,
        "is_active": task.is_active,
        "prompt_text": prompt.prompt_text if prompt else "",
        "prompt_version": prompt.prompt_version if prompt else 1,
        "provenance": prompt.provenance if prompt else "BASE_CATALOG",
        "parameters_schema": prompt.parameters_schema if prompt else {},
    }
