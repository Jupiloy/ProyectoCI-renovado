"""Invitaciones de apoyo por tarea y recurso, sin membresía global del proyecto."""

import hashlib
import hmac
import json
import secrets
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone

from thesis.models import (
    ProjectParticipant, ProjectSupportInvitation, ResearchProfile, SourceDocument,
    SourceExcerpt, SupportContribution, SupportInvitationSource, WorkflowTask,
)
from thesis.services.access import require_project
from thesis.services.errors import DomainError


MAX_INVITATION_SOURCES = 25
MAX_CONTRIBUTION_EXCERPTS = 30
MAX_INVITATION_TTL_HOURS = 24 * 30
DEFAULT_INVITATION_TTL_HOURS = 24 * 7


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _can_manage_support(actor: Any, project_id: UUID):
    project = require_project(actor, project_id)
    allowed = ProjectParticipant.objects.filter(
        project=project, user=actor, active=True,
        role__in=[ProjectParticipant.Role.OWNER, ProjectParticipant.Role.ADVISOR],
    ).exists()
    if not allowed:
        raise DomainError("NOT_FOUND", "Proyecto no encontrado")
    return project


def _effective_status(invitation: ProjectSupportInvitation) -> str:
    if (invitation.status in {
            ProjectSupportInvitation.Status.PENDING,
            ProjectSupportInvitation.Status.ACCEPTED,
        } and invitation.expires_at <= timezone.now()):
        return ProjectSupportInvitation.Status.EXPIRED
    return invitation.status


def _present_invitation(invitation: ProjectSupportInvitation, *, token: str | None = None) -> dict:
    data = {
        "invitation_id": str(invitation.id),
        "project_id": str(invitation.project_id),
        "workflow_version_no": invitation.workflow.version_no,
        "task_id": invitation.task.task_id,
        "task_title": invitation.task.title,
        "invited_email": invitation.invited_email,
        "invited_by_id": invitation.invited_by_id,
        "accepted_by_id": invitation.accepted_by_id,
        "task_instructions": invitation.task_instructions,
        "status": _effective_status(invitation),
        "resource_count": invitation.resource_grants.count(),
        "expires_at": invitation.expires_at.isoformat(),
        "accepted_at": invitation.accepted_at.isoformat() if invitation.accepted_at else None,
        "revoked_at": invitation.revoked_at.isoformat() if invitation.revoked_at else None,
        "created_at": invitation.created_at.isoformat(),
    }
    if token is not None:
        # El token plano solo se devuelve una vez al crear; nunca se persiste ni se serializa después.
        data["invite_token_once"] = token
    return data


def create_support_invitation(
    actor: Any,
    project_id: UUID,
    invited_email: str,
    task_id: str,
    task_instructions: str,
    source_ids: list[UUID],
    ttl_hours: int = DEFAULT_INVITATION_TTL_HOURS,
) -> dict:
    project = _can_manage_support(actor, project_id)
    invited_email = invited_email.strip().lower()
    try:
        validate_email(invited_email)
    except ValidationError as exc:
        raise DomainError("VALIDATION_ERROR", "invited_email no es una dirección válida") from exc
    if invited_email == actor.email.strip().lower():
        raise DomainError("VALIDATION_ERROR", "No puedes invitar tu propia cuenta")
    if ProjectParticipant.objects.filter(project=project, user__email=invited_email, active=True).exists():
        raise DomainError("VERSION_CONFLICT", "La cuenta ya participa en este proyecto con acceso propio")
    if not get_user_model().objects.filter(email=invited_email, is_active=True).exists():
        raise DomainError("NOT_FOUND", "No se encontró una cuenta activa para el correo invitado")
    if not isinstance(task_instructions, str) or not task_instructions.strip() or len(task_instructions.strip()) > 5000:
        raise DomainError("VALIDATION_ERROR", "task_instructions debe tener entre 1 y 5000 caracteres")
    if not isinstance(source_ids, list) or len(source_ids) > MAX_INVITATION_SOURCES or len(set(source_ids)) != len(source_ids):
        raise DomainError("VALIDATION_ERROR", f"source_ids debe contener hasta {MAX_INVITATION_SOURCES} IDs distintos")
    if not isinstance(ttl_hours, int) or not 1 <= ttl_hours <= MAX_INVITATION_TTL_HOURS:
        raise DomainError("VALIDATION_ERROR", f"ttl_hours debe estar entre 1 y {MAX_INVITATION_TTL_HOURS}")

    profile = ResearchProfile.objects.filter(project=project).first()
    workflow = profile.active_workflow if profile else None
    if workflow is None:
        workflow = project.workflows.filter(status="PUBLISHED").order_by("-version_no").first()
    if workflow is None:
        raise DomainError("NOT_FOUND", "No existe un recorrido publicado para este proyecto")
    task = WorkflowTask.objects.filter(workflow=workflow, task_id=task_id, is_active=True).first()
    if task is None:
        raise DomainError("NOT_FOUND", "Tarea activa no encontrada en el recorrido publicado")

    sources = list(SourceDocument.objects.filter(project=project, pk__in=source_ids).order_by("pk"))
    if len(sources) != len(source_ids):
        raise DomainError("NOT_FOUND", "Una o más fuentes no pertenecen al proyecto")
    token = secrets.token_urlsafe(32)
    with transaction.atomic():
        duplicate = ProjectSupportInvitation.objects.select_for_update().filter(
            project=project, task=task, invited_email=invited_email,
            status__in=[ProjectSupportInvitation.Status.PENDING, ProjectSupportInvitation.Status.ACCEPTED],
            expires_at__gt=timezone.now(),
        ).first()
        if duplicate and _effective_status(duplicate) != ProjectSupportInvitation.Status.EXPIRED:
            raise DomainError("VERSION_CONFLICT", "Ya existe una invitación vigente para este correo y tarea")
        invitation = ProjectSupportInvitation.objects.create(
            project=project,
            workflow=workflow,
            task=task,
            invited_by=actor,
            invited_email=invited_email,
            task_instructions=task_instructions.strip(),
            token_sha256=_hash(token),
            status=ProjectSupportInvitation.Status.PENDING,
            expires_at=timezone.now() + timedelta(hours=ttl_hours),
        )
        SupportInvitationSource.objects.bulk_create([
            SupportInvitationSource(invitation=invitation, source=source) for source in sources
        ])
    return _present_invitation(invitation, token=token)


def list_support_invitations(actor: Any, project_id: UUID) -> list[dict]:
    project = _can_manage_support(actor, project_id)
    return [
        _present_invitation(item)
        for item in ProjectSupportInvitation.objects.filter(project=project).select_related("workflow", "task")[:100]
    ]


def accept_support_invitation(actor: Any, invitation_id: UUID, invite_token: str) -> dict:
    if not actor.is_authenticated or not actor.is_active:
        raise DomainError("NOT_FOUND", "Invitación no encontrada")
    if not isinstance(invite_token, str) or not 20 <= len(invite_token) <= 200:
        raise DomainError("NOT_FOUND", "Invitación no encontrada")
    token_hash = _hash(invite_token)
    with transaction.atomic():
        invitation = ProjectSupportInvitation.objects.select_for_update().select_related(
            "workflow", "task",
        ).filter(pk=invitation_id).first()
        if invitation is None or not hmac.compare_digest(invitation.token_sha256, token_hash):
            raise DomainError("NOT_FOUND", "Invitación no encontrada")
        if invitation.status == ProjectSupportInvitation.Status.ACCEPTED:
            if invitation.expires_at <= timezone.now():
                raise DomainError("INVITATION_EXPIRED", "La invitación expiró")
            if invitation.accepted_by_id == actor.pk and actor.email.strip().lower() == invitation.invited_email:
                return _present_invitation(invitation)
            raise DomainError("NOT_FOUND", "Invitación no encontrada")
        if invitation.status != ProjectSupportInvitation.Status.PENDING:
            raise DomainError("INVITATION_UNAVAILABLE", "La invitación ya no está disponible")
        if invitation.expires_at <= timezone.now():
            invitation.status = ProjectSupportInvitation.Status.EXPIRED
            invitation.save(update_fields=["status"])
            expired = True
        else:
            expired = False
        if not expired and actor.email.strip().lower() != invitation.invited_email:
            raise DomainError("NOT_FOUND", "Invitación no encontrada")
        if expired:
            result = None
        else:
            invitation.status = ProjectSupportInvitation.Status.ACCEPTED
            invitation.accepted_by = actor
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=["status", "accepted_by", "accepted_at"])
            result = _present_invitation(invitation)
    if expired:
        raise DomainError("INVITATION_EXPIRED", "La invitación expiró")
    return result


def revoke_support_invitation(actor: Any, project_id: UUID, invitation_id: UUID) -> dict:
    project = _can_manage_support(actor, project_id)
    with transaction.atomic():
        invitation = ProjectSupportInvitation.objects.select_for_update().select_related("workflow", "task").filter(
            project=project, pk=invitation_id,
        ).first()
        if invitation is None:
            raise DomainError("NOT_FOUND", "Invitación no encontrada")
        if invitation.status == ProjectSupportInvitation.Status.REVOKED:
            return _present_invitation(invitation)
        if _effective_status(invitation) == ProjectSupportInvitation.Status.EXPIRED:
            if invitation.status == ProjectSupportInvitation.Status.PENDING:
                invitation.status = ProjectSupportInvitation.Status.EXPIRED
                invitation.save(update_fields=["status"])
            raise_expired = True
        else:
            raise_expired = False
            invitation.status = ProjectSupportInvitation.Status.REVOKED
            invitation.revoked_by = actor
            invitation.revoked_at = timezone.now()
            invitation.save(update_fields=["status", "revoked_by", "revoked_at"])
    if raise_expired:
        raise DomainError("INVITATION_EXPIRED", "La invitación ya expiró")
    return _present_invitation(invitation)


def _active_accepted_invitation(
    actor: Any, invitation_id: UUID, *, lock: bool = False,
) -> ProjectSupportInvitation:
    query = ProjectSupportInvitation.objects.select_related("project", "workflow", "task")
    if lock:
        query = query.select_for_update()
    invitation = query.filter(
        pk=invitation_id, status=ProjectSupportInvitation.Status.ACCEPTED, accepted_by=actor,
    ).first()
    if invitation is None or not actor.is_active or invitation.expires_at <= timezone.now():
        raise DomainError("NOT_FOUND", "Invitación aceptada no encontrada")
    if invitation.project.status != invitation.project.Status.ACTIVE:
        raise DomainError("NOT_FOUND", "Invitación aceptada no encontrada")
    return invitation


def get_support_invitation_context(actor: Any, invitation_id: UUID) -> dict:
    invitation = _active_accepted_invitation(actor, invitation_id)
    grants = list(
        SupportInvitationSource.objects.filter(invitation=invitation)
        .select_related("source").order_by("source__title", "source_id")
    )
    resources = []
    for grant in grants:
        source = grant.source
        remaining_excerpt_slots = max(0, 200 - sum(len(item["excerpts"]) for item in resources))
        excerpts = list(source.excerpts.order_by("page_no", "chunk_no")[:min(50, remaining_excerpt_slots)])
        resources.append({
            "source_id": str(source.id),
            "title": source.title,
            "record_provider": source.record_provider,
            "publication_year": source.publication_year,
            "doi": source.doi,
            "verification_status": source.verification_status,
            "sha256": source.sha256,
            "page_count": source.page_count,
            "download_available": bool(source.storage_key),
            "excerpts": [{
                "excerpt_id": str(excerpt.id),
                "physical_page": excerpt.page_no,
                "text": excerpt.text,
                "text_sha256": excerpt.text_sha256,
            } for excerpt in excerpts],
            "excerpts_truncated": source.excerpts.count() > len(excerpts),
        })
    return {
        "invitation_id": str(invitation.id),
        "project_id": str(invitation.project_id),
        "task_id": invitation.task.task_id,
        "task_title": invitation.task.title,
        "task_description": invitation.task.description,
        "task_instructions": invitation.task_instructions,
        "workflow_version_no": invitation.workflow.version_no,
        "expires_at": invitation.expires_at.isoformat(),
        "resources": resources,
    }


def get_support_source_file(actor: Any, invitation_id: UUID, source_id: UUID) -> tuple[Path, str]:
    invitation = _active_accepted_invitation(actor, invitation_id)
    grant = SupportInvitationSource.objects.select_related("source").filter(
        invitation=invitation, source_id=source_id,
    ).first()
    if grant is None or not grant.source.storage_key:
        raise DomainError("NOT_FOUND", "Archivo no disponible en los recursos compartidos")
    source = grant.source
    root = Path(settings.MEDIA_ROOT).resolve()
    path = (root / source.storage_key).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise DomainError("PDF_UNREADABLE", "El archivo no está disponible o su integridad cambió")
    digest = hashlib.sha256()
    with path.open("rb") as stored_pdf:
        for chunk in iter(lambda: stored_pdf.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != source.sha256:
        raise DomainError("PDF_UNREADABLE", "El archivo no está disponible o su integridad cambió")
    return path, f"fuente-{source.id}.pdf"


def submit_support_contribution(
    actor: Any, invitation_id: UUID, response_text: str,
    source_excerpt_ids: list[int], idempotency_key: UUID,
) -> dict:
    response_text = response_text.strip() if isinstance(response_text, str) else ""
    if not response_text or len(response_text) > 10000:
        raise DomainError("VALIDATION_ERROR", "response_text debe tener entre 1 y 10000 caracteres")
    if (not isinstance(source_excerpt_ids, list)
            or len(source_excerpt_ids) > MAX_CONTRIBUTION_EXCERPTS
            or len(set(source_excerpt_ids)) != len(source_excerpt_ids)):
        raise DomainError("VALIDATION_ERROR", f"source_excerpt_ids debe contener hasta {MAX_CONTRIBUTION_EXCERPTS} IDs distintos")
    excerpt_ids = [str(value) for value in source_excerpt_ids]
    payload_hash = _hash(json.dumps({
        "response_text": response_text, "source_excerpt_ids": excerpt_ids,
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    with transaction.atomic():
        invitation = _active_accepted_invitation(actor, invitation_id, lock=True)
        allowed_ids = set(SupportInvitationSource.objects.filter(
            invitation=invitation,
        ).values_list("source_id", flat=True))
        excerpts = list(SourceExcerpt.objects.filter(
            pk__in=source_excerpt_ids, source_id__in=allowed_ids,
        ))
        if len(excerpts) != len(source_excerpt_ids):
            raise DomainError("NOT_FOUND", "Uno o más extractos no pertenecen a recursos compartidos")
        existing = SupportContribution.objects.filter(
            invitation=invitation, idempotency_key=idempotency_key,
        ).first()
        if existing:
            if existing.response_sha256 != payload_hash:
                raise DomainError("IDEMPOTENCY_CONFLICT", "La clave ya fue usada para otro aporte")
            return _present_contribution(existing)
        contribution = SupportContribution.objects.create(
            invitation=invitation, author=actor, idempotency_key=idempotency_key,
            response_text=response_text, source_excerpt_ids=excerpt_ids,
            response_sha256=payload_hash,
        )
    return _present_contribution(contribution)


def _present_contribution(item: SupportContribution) -> dict:
    return {
        "contribution_id": str(item.id),
        "invitation_id": str(item.invitation_id),
        "author_id": item.author_id,
        "response_text": item.response_text,
        "source_excerpt_ids": item.source_excerpt_ids,
        "response_sha256": item.response_sha256,
        "created_at": item.created_at.isoformat(),
    }


def list_support_contributions(actor: Any, project_id: UUID, invitation_id: UUID) -> list[dict]:
    project = _can_manage_support(actor, project_id)
    invitation = ProjectSupportInvitation.objects.filter(project=project, pk=invitation_id).first()
    if invitation is None:
        raise DomainError("NOT_FOUND", "Invitación no encontrada")
    return [
        _present_contribution(item)
        for item in SupportContribution.objects.filter(invitation=invitation).select_related("author")
    ]
