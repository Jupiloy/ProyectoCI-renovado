from django.db import transaction
from django.db.models import F
from django.utils import timezone

from thesis.models import Project, ProjectParticipant, ResearchProfile
from thesis.services.access import require_project
from thesis.services.errors import DomainError


def _clean_text(value: str, name: str, max_length: int) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > max_length:
        raise DomainError("VALIDATION_ERROR", f"{name} debe tener entre 1 y {max_length} caracteres")
    return cleaned


@transaction.atomic
def create_project(actor, name: str, title: str | None = None) -> Project:
    if getattr(actor, "_tesismcp_agent_connection_id", None) is not None:
        raise DomainError("PERMISSION_DENIED", "Una conexión BYOA limitada a un proyecto no puede crear proyectos")
    project = Project.objects.create(
        name=_clean_text(name, "name", 160),
        title=_clean_text(title, "title", 300) if title else "Título por definir",
    )
    ProjectParticipant.objects.create(project=project, user=actor, role=ProjectParticipant.Role.OWNER)
    ResearchProfile.objects.create(project=project)
    return project


def list_user_projects(actor, *, offset: int = 0, limit: int = 50) -> dict:
    """Lista solo proyectos activos con membresía vigente del usuario autenticado."""
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
        raise DomainError("VALIDATION_ERROR", "offset debe ser no negativo y limit debe estar entre 1 y 100")
    memberships = list(
        ProjectParticipant.objects.select_related("project")
        .filter(user=actor, active=True, project__status=Project.Status.ACTIVE)
        .order_by("project__name", "project_id")[offset:offset + limit + 1]
    )
    projects = []
    for membership in memberships[:limit]:
        owner = membership.role == ProjectParticipant.Role.OWNER
        projects.append({
            "project_id": str(membership.project_id),
            "name": membership.project.name,
            "title": membership.project.title,
            "status": membership.project.status,
            "role": membership.role,
            "permissions": {
                "can_read_project": True,
                "can_edit_document": owner,
                "can_manage_workflow": owner,
                "can_review_chapters": membership.role == ProjectParticipant.Role.ADVISOR,
            },
        })
    return {"projects": projects, "offset": offset, "limit": limit, "has_more": len(memberships) > limit}


def get_project_state(actor, project_id) -> dict:
    project = require_project(actor, project_id)
    profile = project.profile
    consistency_rows = [
        {
            "ordinal": row.ordinal,
            "objective_text": row.objective_text,
            "question_text": row.question_text,
            "hypothesis_text": row.hypothesis_text,
        }
        for row in project.consistency_rows.order_by("ordinal")
    ]
    variables = [
        {
            "ordinal": var.ordinal,
            "role": var.role,
            "name": var.name,
            "conceptual_definition": var.conceptual_definition,
            "operational_definition": var.operational_definition,
            "dimensions": [
                {
                    "ordinal": dim.ordinal,
                    "name": dim.name,
                    "indicators": [
                        {
                            "ordinal": ind.ordinal,
                            "name": ind.name,
                            "measurement_scale": ind.measurement_scale,
                        }
                        for ind in dim.indicators.order_by("ordinal")
                    ],
                }
                for dim in var.dimensions.order_by("ordinal")
            ],
        }
        for var in project.variables.order_by("ordinal")
    ]
    instruments = [
        {
            "id": str(inst.id),
            "name": inst.name,
            "kind": inst.kind,
            "version_no": inst.version_no,
            "status": inst.status,
            "items_count": inst.items.count(),
        }
        for inst in project.instruments.order_by("created_at")
    ]
    return {
        "project_id": str(project.id),
        "name": project.name,
        "title": project.title,
        "status": project.status,
        "idea_provisional": profile.topic,
        "problem_statement": profile.problem_statement,
        "ods_code": profile.ods_code,
        "unit_of_analysis": profile.unit_of_analysis,
        "place": profile.place,
        "period_text": profile.period_text,
        "approach": profile.approach,
        "consistency_matrix": consistency_rows,
        "variables": variables,
        "instruments": instruments,
        "state_version": profile.lock_version,
    }


@transaction.atomic
def register_idea(actor, project_id, description: str, expected_version: int) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    idea = _clean_text(description, "description", 2000)
    updated = ResearchProfile.objects.filter(
        project=project, lock_version=expected_version,
    ).update(topic=idea, lock_version=F("lock_version") + 1, updated_at=timezone.now())
    if not updated:
        raise DomainError("VERSION_CONFLICT", "La idea cambió; consulta el estado actual antes de guardar")
    return get_project_state(actor, project.id)
