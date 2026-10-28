"""Invitaciones de apoyo limitadas a tareas y recursos explícitos."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class ProjectSupportInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente de aceptación"
        ACCEPTED = "ACCEPTED", "Aceptada"
        REVOKED = "REVOKED", "Revocada"
        EXPIRED = "EXPIRED", "Expirada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("thesis.Project", on_delete=models.PROTECT, related_name="support_invitations")
    workflow = models.ForeignKey("thesis.ProjectWorkflow", on_delete=models.PROTECT, related_name="support_invitations")
    task = models.ForeignKey("thesis.WorkflowTask", on_delete=models.PROTECT, related_name="support_invitations")
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sent_support_invitations")
    invited_email = models.EmailField(max_length=254)
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="accepted_support_invitations")
    task_instructions = models.TextField()
    token_sha256 = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="revoked_support_invitations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "thesis_project_support_invitation"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(status="PENDING", accepted_by__isnull=True, accepted_at__isnull=True, revoked_at__isnull=True)
                           | Q(status="ACCEPTED", accepted_by__isnull=False, accepted_at__isnull=False, revoked_at__isnull=True)
                           | Q(status="REVOKED", revoked_at__isnull=False, revoked_by__isnull=False)
                           | Q(status="EXPIRED", accepted_by__isnull=True, accepted_at__isnull=True, revoked_at__isnull=True)),
                name="support_invite_state_fields_ck",
            ),
        ]
        indexes = [models.Index(fields=["project", "status", "expires_at"], name="support_invite_proj_state_idx")]


class SupportInvitationSource(models.Model):
    """Grant inmutable de acceso a un SourceDocument concreto."""

    invitation = models.ForeignKey(ProjectSupportInvitation, on_delete=models.PROTECT, related_name="resource_grants")
    source = models.ForeignKey("thesis.SourceDocument", on_delete=models.PROTECT, related_name="support_grants")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "thesis_support_invitation_source"
        constraints = [models.UniqueConstraint(fields=["invitation", "source"], name="support_invite_source_unique")]


class SupportContribution(models.Model):
    """Aporte append-only de una persona invitada; no altera el manuscrito."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.ForeignKey(ProjectSupportInvitation, on_delete=models.PROTECT, related_name="contributions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="support_contributions")
    idempotency_key = models.UUIDField()
    response_text = models.TextField()
    source_excerpt_ids = models.JSONField(default=list)
    response_sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "thesis_support_contribution"
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["invitation", "idempotency_key"], name="support_contribution_key_unique"),
            models.CheckConstraint(condition=~Q(response_text=""), name="support_contribution_nonempty_ck"),
        ]
