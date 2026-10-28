"""Registro y despacho de reglas relacionales de los pasos."""

from collections.abc import Callable
from dataclasses import dataclass

from thesis.models import Project, ResearchProfile, StepProgress


@dataclass(frozen=True)
class StepExecutionContext:
    """Contexto inmutable inyectado a cada estrategia de materialización."""

    project: Project
    profile: ResearchProfile
    step_code: str
    validated: dict


StepHandler = Callable[[StepExecutionContext], None]
STEP_HANDLERS: dict[str, StepHandler] = {}


def register_step_handler(*step_codes: str):
    """Decorador del Registro de Estrategias (Strategy Registry) por código de paso."""
    def decorator(func: StepHandler) -> StepHandler:
        for code in step_codes:
            STEP_HANDLERS[code] = func
        return func
    return decorator


def _get_completed_step_output(project: Project, step_code: str) -> dict:
    query = StepProgress.objects.filter(
        project=project, step_code=step_code, status=StepProgress.Status.COMPLETED
    )
    profile = ResearchProfile.objects.filter(project=project).first()
    if profile and profile.workflow_mode == ResearchProfile.WorkflowMode.CONFIGURABLE_GRAPH:
        if not profile.active_workflow:
            return {}
        query = query.filter(
            workflow=profile.active_workflow,
            workflow_version_no=profile.active_workflow.version_no,
        )
    progress = query.first()
    return progress.output_json if progress and progress.output_json else {}


def execute_step_materializer(project: Project, profile: ResearchProfile, step_code: str, validated: dict) -> None:
    """Despacha la estrategia registrada para `step_code` sin cadenas `if/elif`."""
    handler = STEP_HANDLERS.get(step_code)
    if handler is not None:
        handler(StepExecutionContext(project=project, profile=profile, step_code=step_code, validated=validated))
