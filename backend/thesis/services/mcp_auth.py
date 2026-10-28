import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from thesis.models import McpAccessToken
from thesis.services.errors import DomainError


def issue_token(user, *, lifetime_hours: int = 24, agent_connection=None) -> str:
    if lifetime_hours < 1 or lifetime_hours > 720:
        raise ValueError("lifetime_hours fuera de rango")
    if agent_connection is not None and (agent_connection.user_id != user.pk or not agent_connection.is_active):
        raise ValueError("La conexión BYOA no pertenece al usuario o está inactiva")
    raw = secrets.token_urlsafe(48)
    McpAccessToken.objects.create(
        user=user,
        agent_connection=agent_connection,
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(hours=lifetime_hours),
    )
    return raw


def actor_from_token(raw: str):
    if not raw:
        raise DomainError("UNAUTHENTICATED", "Configura TESISMCP_MCP_TOKEN")
    digest = hashlib.sha256(raw.encode()).hexdigest()
    token = McpAccessToken.objects.select_related("user", "agent_connection").filter(
        token_hash=digest,
        revoked_at__isnull=True,
        expires_at__gt=timezone.now(),
        user__is_active=True,
    ).first()
    if token is None:
        raise DomainError("UNAUTHENTICATED", "Token MCP inválido, vencido o revocado")
    actor = token.user
    connection = token.agent_connection
    if connection is not None:
        if not connection.is_active or connection.project.status != "ACTIVE":
            raise DomainError("UNAUTHENTICATED", "La conexión BYOA está revocada, vencida o inactiva")
        actor._tesismcp_agent_connection_id = connection.pk
        actor._tesismcp_agent_project_id = connection.project_id
    return actor
