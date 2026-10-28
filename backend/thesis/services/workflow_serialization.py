"""Presentación de datos de dominio; sin cambios de persistencia."""

from typing import Any
from thesis.models import ProjectWorkflow, WorkflowTask


def _serialize_task(task: WorkflowTask) -> dict[str, Any]:
    prompt_data = None
    if hasattr(task, "prompt") and task.prompt:
        prompt_data = {
            "prompt_text": task.prompt.prompt_text,
            "prompt_version": task.prompt.prompt_version,
            "provenance": task.prompt.provenance,
            "parameters_schema": task.prompt.parameters_schema,
        }
    return {
        "task_id": task.task_id,
        "legacy_step_code": task.legacy_step_code,
        "title": task.title,
        "description": task.description,
        "chapter_no": task.chapter_no,
        "order_index": task.order_index,
        "is_active": task.is_active,
        "is_optional": task.is_optional,
        "is_protected": task.is_protected,
        "contract_name": task.contract_name,
        "branch_condition": task.branch_condition,
        "prompt": prompt_data,
    }

def _serialize_workflow(wf: ProjectWorkflow) -> dict[str, Any]:
    tasks = list(wf.tasks.select_related("prompt").order_by("order_index", "task_id"))
    deps = list(wf.dependencies.select_related("source_task", "target_task"))
    return {
        "workflow_id": wf.pk,
        "version_no": wf.version_no,
        "status": wf.status,
        "base_template_version": wf.base_template_version,
        "change_summary": wf.change_summary,
        "content_sha256": wf.content_sha256,
        "lock_version": wf.lock_version,
        "created_at": wf.created_at.isoformat(),
        "tasks": [_serialize_task(t) for t in tasks],
        "dependencies": [
            {
                "source": d.source_task.task_id,
                "target": d.target_task.task_id,
                "type": d.dependency_type,
                "field": d.required_field,
                "blocking": d.is_blocking,
                "reason": d.reason,
            }
            for d in deps
        ],
    }
