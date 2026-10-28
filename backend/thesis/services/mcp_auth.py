import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from thesis.models import McpAccessToken
from thesis.services.errors import DomainError


def issue_token(user, *, lifetime_hours: int = 24) -> str:
    if lifetime_hours < 1 or lifetime_hours > 720:
        raise ValueError("lifetime_hours fuera de rango")
    raw = secrets.token_urlsafe(48)
    McpAccessToken.objects.create(
        user=user,
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(hours=lifetime_hours),
    )
    return raw


def actor_from_token(raw: str):
    if not raw:
        raise DomainError("UNAUTHENTICATED", "Configura TESISMCP_MCP_TOKEN")
    digest = hashlib.sha256(raw.encode()).hexdigest()
    token = McpAccessToken.objects.select_related("user").filter(
        token_hash=digest, revoked_at__isnull=True, expires_at__gt=timezone.now(),
        user__is_active=True,
    ).first()
    if token is None:
        raise DomainError("UNAUTHENTICATED", "Token MCP inválido, vencido o revocado")
    return token.user
