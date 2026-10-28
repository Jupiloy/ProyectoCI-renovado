"""Conexiones locales BYOA vinculadas a una cuenta y un proyecto."""

import uuid
from django.conf import settings
from django.db import models


class AgentConnection(models.Model):
    class Runtime(models.TextChoices):
        ANTIGRAVITY_CLI = "ANTIGRAVITY_CLI", "Antigravity CLI"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agent_connections",
    )
    project = models.ForeignKey(
        "thesis.Project",
        on_delete=models.PROTECT,
        related_name="agent_connections",
    )
    name = models.CharField(max_length=100)
    runtime = models.CharField(max_length=32, choices=Runtime.choices)
    connector_token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_seen_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "thesis_agent_connection"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "project", "revoked_at"], name="agent_conn_user_proj_idx")]

    @property
    def is_active(self) -> bool:
        from django.utils import timezone
        return self.revoked_at is None and self.expires_at > timezone.now() and self.user.is_active
