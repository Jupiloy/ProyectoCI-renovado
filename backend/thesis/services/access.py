from thesis.models import Project, ProjectParticipant
from thesis.services.errors import DomainError


def require_project(actor, project_id, *, owner_only=False) -> Project:
    membership = ProjectParticipant.objects.select_related("project").filter(
        project_id=project_id, user=actor, active=True,
    )
    if owner_only:
        membership = membership.filter(role=ProjectParticipant.Role.OWNER)
    participant = membership.first()
    if participant is None:
        # No revela si existe un proyecto ajeno.
        raise DomainError("NOT_FOUND", "Proyecto no encontrado")
    if participant.project.status != Project.Status.ACTIVE:
        raise DomainError("PROJECT_ARCHIVED", "El proyecto está archivado")
    return participant.project
