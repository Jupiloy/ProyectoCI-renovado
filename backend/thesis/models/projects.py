"""Proyectos de tesis y participantes."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Project(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activo"
        ARCHIVED = "ARCHIVED", "Archivado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    title = models.CharField(max_length=300)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project"
        indexes = [models.Index(fields=["status", "-updated_at"], name="project_status_updated_idx")]

    def __str__(self):
        return self.name


class ProjectParticipant(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Tesista"
        ADVISOR = "ADVISOR", "Asesor"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    role = models.CharField(max_length=10, choices=Role.choices)
    active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "project_participant"
        constraints = [
            models.UniqueConstraint(fields=["project", "user"], name="participant_project_user_unique"),
            models.UniqueConstraint(fields=["project"], condition=Q(role="OWNER", active=True), name="participant_one_active_owner"),
            models.UniqueConstraint(fields=["project"], condition=Q(role="ADVISOR", active=True), name="participant_one_active_advisor"),
            models.CheckConstraint(condition=Q(active=True, left_at__isnull=True) | Q(active=False, left_at__isnull=False), name="participant_active_dates_match"),
        ]
        indexes = [models.Index(fields=["user", "active", "role"], name="participant_user_role_idx")]
