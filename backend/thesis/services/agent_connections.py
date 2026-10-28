"""Registro, autenticación y revocación de conectores BYOA locales."""

import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from ninja.security import HttpBearer

from thesis.models import AgentConnection, AIGenerationJob, ProjectParticipant
from thesis.services.access import require_project
from thesis.services.errors import DomainError
from thesis.services.mcp_auth import issue_token

CONNECTION_LIFETIME_HOURS = 720


def _digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def present_connection(connection: AgentConnection) -> dict:
    return {
        "id": str(connection.pk),
        "project_id": str(connection.project_id),
        "name": connection.name,
        "runtime": connection.runtime,
        "created_at": connection.created_at.isoformat(),
        "expires_at": connection.expires_at.isoformat(),
        "last_seen_at": connection.last_seen_at.isoformat() if connection.last_seen_at else None,
        "revoked_at": connection.revoked_at.isoformat() if connection.revoked_at else None,
        "active": connection.is_active,
    }


@transaction.atomic
def create_agent_connection(actor, project_id, *, name: str, runtime: str) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    clean_name = name.strip() if isinstance(name, str) else ""
    if not clean_name or len(clean_name) > 100:
        raise DomainError("VALIDATION_ERROR", "name debe tener entre 1 y 100 caracteres")
    if runtime != AgentConnection.Runtime.ANTIGRAVITY_CLI:
        raise DomainError("VALIDATION_ERROR", "runtime no soportado; por ahora usa ANTIGRAVITY_CLI")
    raw_connector_token = secrets.token_urlsafe(48)
    connection = AgentConnection.objects.create(
        user=actor,
        project=project,
        name=clean_name,
        runtime=runtime,
        connector_token_hash=_digest(raw_connector_token),
        expires_at=timezone.now() + timedelta(hours=CONNECTION_LIFETIME_HOURS),
    )
    raw_mcp_token = issue_token(
        actor,
        lifetime_hours=CONNECTION_LIFETIME_HOURS,
        agent_connection=connection,
    )
    return {
        **present_connection(connection),
        "connector_token": raw_connector_token,
        "mcp_token": raw_mcp_token,
        "credentials_shown_once": True,
    }


def list_agent_connections(actor, project_id) -> list[dict]:
    project = require_project(actor, project_id, owner_only=True)
    return [present_connection(c) for c in AgentConnection.objects.filter(user=actor, project=project)]


@transaction.atomic
def revoke_agent_connection(actor, connection_id) -> dict:
    connection = AgentConnection.objects.select_for_update().filter(user=actor, pk=connection_id).first()
    if connection is None:
        raise DomainError("NOT_FOUND", "Conexión BYOA no encontrada")
    if connection.revoked_at is None:
        connection.revoked_at = timezone.now()
        connection.save(update_fields=["revoked_at"])
        connection.mcp_tokens.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())
        AIGenerationJob.objects.filter(
            agent_connection=connection,
            status__in=[AIGenerationJob.Status.QUEUED, AIGenerationJob.Status.RUNNING],
        ).update(
            status=AIGenerationJob.Status.CANCELLED,
            finished_at=timezone.now(),
            lease_expires_at=None,
            error_code="CONNECTION_REVOKED",
            error_message="La conexión del agente fue revocada",
        )
    return present_connection(connection)


class AgentConnectionBearer(HttpBearer):
    def authenticate(self, request, token):
        if not token:
            return None
        connection = AgentConnection.objects.select_related("user", "project").filter(
            connector_token_hash=_digest(token),
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
            user__is_active=True,
            project__status="ACTIVE",
        ).first()
        if connection is None or not ProjectParticipant.objects.filter(
            project=connection.project, user=connection.user,
            role=ProjectParticipant.Role.OWNER, active=True,
        ).exists():
            return None
        AgentConnection.objects.filter(pk=connection.pk).update(last_seen_at=timezone.now())
        connection.last_seen_at = timezone.now()
        return connection


agent_connection_bearer = AgentConnectionBearer()
