"""Construcción y verificación del contexto congelado de trabajos de IA."""
import hashlib
import json
from typing import Any
from thesis.models import ProjectWorkflow, ResearchProfile, SourceExcerpt, StepProgress, WorkflowTaskExecution
from thesis.services.errors import DomainError
from thesis.services.step_contracts import CONTRACTS
from thesis.services.workflow_template import calculate_workflow_hash, workflow_content_dump


def _build_context_snapshot(project, profile, workflow, task, context_refs):
    """Reconstruye el contexto actual desde registros autorizados del proyecto."""
    snapshot: dict[str, Any] = {
        "approach": profile.approach,
        "ods_code": profile.ods_code,
        "unit_of_analysis": profile.unit_of_analysis,
        "place": profile.place,
        "period_text": profile.period_text,
        "problem_statement": profile.problem_statement,
        "dependency_outputs": {},
    }
    for dep in task.prerequisite_dependencies.all().select_related("target_task"):
        target = dep.target_task
        if target.task_id.startswith("USR_"):
            execution = WorkflowTaskExecution.objects.filter(
                task=target, workflow=workflow
            ).order_by("-revision_no").first()
            if execution:
                snapshot["dependency_outputs"][target.task_id] = execution.output_json
        else:
            progress = StepProgress.objects.filter(
                project=project, step_code=target.task_id,
                workflow=workflow, workflow_version_no=workflow.version_no,
            ).first()
            if progress and progress.output_json:
                snapshot["dependency_outputs"][target.task_id] = progress.output_json

    resolved_refs = []
    for ref in context_refs or []:
        if not isinstance(ref, dict) or set(ref) - {"kind", "id"}:
            raise DomainError("VALIDATION_ERROR", "Cada context_ref debe contener únicamente kind e id")
        if ref.get("kind") != "source_excerpt" or not ref.get("id"):
            raise DomainError("VALIDATION_ERROR", "Tipo de context_ref no admitido; se requiere source_excerpt")
        excerpt = SourceExcerpt.objects.filter(source__project=project, pk=ref["id"]).first()
        if not excerpt:
            raise DomainError("NOT_FOUND", f"Extracto de evidencia '{ref['id']}' no encontrado en el proyecto")
        resolved_refs.append({
            "kind": "source_excerpt",
            "id": str(excerpt.id),
            "page_no": excerpt.page_no,
            "text": excerpt.text,
            "text_sha256": excerpt.text_sha256,
        })
    snapshot["context_refs"] = resolved_refs
    return snapshot

def _job_context_is_current(job: AIGenerationJob, profile: ResearchProfile) -> bool:
    """Comprueba que perfil, workflow, prompt, esquema y referencias aún coinciden."""
    if job.state_version_at_request is None or profile.lock_version != job.state_version_at_request:
        return False
    active_workflow = profile.active_workflow
    if active_workflow is None:
        active_workflow = (
            ProjectWorkflow.objects.filter(project=profile.project, status=ProjectWorkflow.Status.PUBLISHED)
            .order_by("-version_no")
            .first()
        )
    if not active_workflow or active_workflow.pk != job.workflow_id:
        return False
    tasks_dump, deps_dump, prompts_dump = workflow_content_dump(job.workflow)
    if not job.workflow.content_sha256 or calculate_workflow_hash(tasks_dump, deps_dump, prompts_dump) != job.workflow.content_sha256:
        return False
    prompt = getattr(job.task, "prompt", None)
    if (prompt.prompt_text if prompt else "") != job.prompt_text_used:
        return False
    if (prompt.prompt_version if prompt else 1) != job.prompt_version_used:
        return False
    current_schema = CONTRACTS[job.workflow_task_id].model_json_schema() if job.workflow_task_id in CONTRACTS else job.task.output_schema
    if current_schema != job.output_schema_used:
        return False
    refs = [
        {"kind": ref.get("kind"), "id": ref.get("id")}
        for ref in job.context_snapshot.get("context_refs", [])
    ]
    try:
        current_snapshot = _build_context_snapshot(job.project, profile, job.workflow, job.task, refs)
    except DomainError:
        return False
    current_hash = hashlib.sha256(
        json.dumps(current_snapshot, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return current_hash == job.context_sha256
