"""Observaciones y decisiones del asesor sobre revisiones concretas."""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from thesis.models import Chapter, ChapterSnapshot, ProjectParticipant, ReviewComment, ReviewEvent
from thesis.services.access import require_project
from thesis.services.errors import DomainError
from thesis.services.steps import CHAPTER_STEPS, get_chapter


def _advisor(actor, project_id):
    project = require_project(actor, project_id)
    if not ProjectParticipant.objects.filter(project=project, user=actor, active=True,
                                             role=ProjectParticipant.Role.ADVISOR).exists():
        raise DomainError("NOT_FOUND", "Proyecto no encontrado")
    return project


def assign_advisor(actor, project_id, email: str) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    email = email.strip().lower()
    advisor = get_user_model().objects.filter(email=email, is_active=True).first()
    if advisor is None or advisor == actor:
        raise DomainError("NOT_FOUND", "Asesor activo no encontrado")
    with transaction.atomic():
        existing = ProjectParticipant.objects.select_for_update().filter(
            project=project, role=ProjectParticipant.Role.ADVISOR, active=True,
        ).first()
        if existing and existing.user_id != advisor.pk:
            raise DomainError("VERSION_CONFLICT", "El proyecto ya tiene un asesor activo")
        if not existing:
            membership, created = ProjectParticipant.objects.get_or_create(project=project, user=advisor, defaults={
                "role": ProjectParticipant.Role.ADVISOR,
            })
            if not created:
                if membership.role != ProjectParticipant.Role.ADVISOR:
                    raise DomainError("VERSION_CONFLICT", "La persona ya tiene otro rol en el proyecto")
                membership.active = True
                membership.left_at = None
                membership.save(update_fields=["active", "left_at"])
    return {"project_id": str(project.id), "advisor_id": advisor.pk, "advisor_email": advisor.email}


def _current_chapter(project, chapter_no: int):
    if chapter_no not in CHAPTER_STEPS:
        raise DomainError("NOT_FOUND", "Capítulo no disponible en el MVP")
    chapter = Chapter.objects.select_for_update().filter(project=project, number=chapter_no).first()
    if chapter is None:
        raise DomainError("NOT_FOUND", "Capítulo no encontrado")
    return chapter


def add_comment(actor, project_id, chapter_no: int, start_cp: int, end_cp: int,
                selected_text: str, body: str, snapshot_id=None) -> dict:
    project = _advisor(actor, project_id)
    body = body.strip()
    if not body or len(body) > 5000:
        raise DomainError("VALIDATION_ERROR", "La observación debe tener entre 1 y 5000 caracteres")
    with transaction.atomic():
        chapter = _current_chapter(project, chapter_no)
        if chapter.status != Chapter.Status.READY:
            raise DomainError("VERSION_CONFLICT", "El capítulo no está en revisión")
        snapshot = chapter.submitted_snapshot
        revision = None
        if snapshot is not None:
            if snapshot_id is None:
                raise DomainError("VALIDATION_ERROR", "snapshot_id es obligatorio para comentar la versión enviada")
            if str(snapshot.id) != str(snapshot_id):
                raise DomainError("VERSION_CONFLICT", "El capítulo cambió; vuelve a cargar el snapshot vigente")
            anchor_text = snapshot.content_md
        else:
            if snapshot_id is not None:
                raise DomainError("VERSION_CONFLICT", "El capítulo no tiene un snapshot vigente para ese comentario")
            revision = chapter.revisions.order_by("-revision_no").first()
            anchor_text = revision.content_md if revision else ""
        if revision is None and snapshot is None:
            raise DomainError("NOT_FOUND", "No hay una versión textual que pueda recibir observaciones")
        if start_cp < 0 or end_cp <= start_cp or anchor_text[start_cp:end_cp] != selected_text:
            raise DomainError("VALIDATION_ERROR", "El fragmento no coincide con la revisión vigente")
        comment = ReviewComment.objects.create(
            revision=revision,
            snapshot=snapshot,
            author=actor,
            start_cp=start_cp,
            end_cp=end_cp,
            selected_text=selected_text,
            body=body,
        )
    return _serialize_comment(comment)


def _serialize_comment(item: ReviewComment) -> dict:
    snapshot = item.snapshot
    return {
        "comment_id": item.pk,
        "revision_id": item.revision_id,
        "snapshot_id": str(snapshot.id) if snapshot else None,
        "snapshot_no": snapshot.snapshot_no if snapshot else None,
        "snapshot_sha256": snapshot.payload_sha256 if snapshot else None,
        "start_cp": item.start_cp,
        "end_cp": item.end_cp,
        "selected_text": item.selected_text,
        "body": item.body,
        "status": item.status,
        "author_id": item.author_id,
        "author": item.author.email,
        "created_at": item.created_at.isoformat(),
        "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
    }


def list_comments(actor, project_id, chapter_no: int, snapshot_id=None) -> list[dict]:
    project = require_project(actor, project_id)
    chapter = Chapter.objects.filter(project=project, number=chapter_no).first()
    if chapter is None:
        return []
    comments = ReviewComment.objects.filter(
        Q(revision__chapter=chapter) | Q(snapshot__chapter=chapter)
    ).select_related("snapshot", "revision", "author")
    if snapshot_id is not None:
        snapshot = ChapterSnapshot.objects.filter(chapter=chapter, pk=snapshot_id).first()
        if snapshot is None:
            raise DomainError("NOT_FOUND", "Snapshot no encontrado en este capítulo")
        comments = comments.filter(snapshot=snapshot)
    return [_serialize_comment(item) for item in comments.order_by("created_at", "pk")]


def resolve_comment(actor, project_id, comment_id: int) -> dict:
    project = _advisor(actor, project_id)
    with transaction.atomic():
        item = ReviewComment.objects.select_for_update().filter(pk=comment_id).first()
        belongs_to_project = bool(
            item
            and (
                (item.revision_id and item.revision.chapter.project_id == project.pk)
                or (item.snapshot_id and item.snapshot.chapter.project_id == project.pk)
            )
        )
        if not belongs_to_project:
            raise DomainError("NOT_FOUND", "Observación no encontrada")
        if item.status == ReviewComment.Status.OPEN:
            item.status = ReviewComment.Status.RESOLVED
            item.resolved_by = actor
            item.resolved_at = timezone.now()
            item.save(update_fields=["status", "resolved_by", "resolved_at"])
    return {"comment_id": item.pk, "status": item.status}


def decide_chapter(actor, project_id, chapter_no: int, action: str, reason: str = "") -> dict:
    project = _advisor(actor, project_id)
    with transaction.atomic():
        chapter = _current_chapter(project, chapter_no)
        snapshot = chapter.submitted_snapshot
        revision = None if snapshot else chapter.revisions.order_by("-revision_no").first()
        if action == ReviewEvent.Action.REQUEST_CHANGES:
            if chapter.status != Chapter.Status.READY or (snapshot is None and revision is None):
                raise DomainError("VERSION_CONFLICT", "El capítulo no está en revisión")
            target = {"snapshot": snapshot} if snapshot else {"revision": revision}
            if not ReviewComment.objects.filter(**target, status=ReviewComment.Status.OPEN).exists():
                raise DomainError("VALIDATION_ERROR", "Registra al menos una observación abierta")
            chapter.request_changes()
        elif action == ReviewEvent.Action.APPROVE:
            if chapter.status != Chapter.Status.READY or (snapshot is None and revision is None):
                raise DomainError("VERSION_CONFLICT", "El capítulo no está en revisión")
            target = {"snapshot": snapshot} if snapshot else {"revision": revision}
            if ReviewComment.objects.filter(**target, status=ReviewComment.Status.OPEN).exists():
                raise DomainError("ADVISOR_UNRESOLVED_COMMENTS", "Resuelve las observaciones abiertas antes de aprobar")
            chapter.approve()
            chapter.approved_snapshot = snapshot
            chapter.approved_revision = revision
            chapter.approved_at = timezone.now()
        elif action == ReviewEvent.Action.REOPEN:
            if chapter.status != Chapter.Status.APPROVED or not reason.strip():
                raise DomainError("VERSION_CONFLICT", "Reabrir exige un capítulo aprobado y un motivo")
            snapshot = chapter.approved_snapshot
            revision = None if snapshot else chapter.approved_revision
            chapter.reopen()
            chapter.approved_revision = None
            chapter.approved_snapshot = None
            chapter.approved_at = None
        else:
            raise DomainError("VALIDATION_ERROR", "Decisión inválida")
        chapter.save(update_fields=[
            "status", "approved_revision", "approved_snapshot", "approved_at", "updated_at",
        ])
        ReviewEvent.objects.create(
            chapter=chapter,
            revision=revision,
            snapshot=snapshot,
            actor=actor,
            action=action,
            reason=reason.strip(),
        )
    return get_chapter(actor, project_id, chapter_no)


def advisor_dashboard(actor) -> list[dict]:
    projects = (ProjectParticipant.objects.filter(user=actor, active=True, role=ProjectParticipant.Role.ADVISOR)
                .select_related("project").order_by("project__name"))
    return [{"project_id": str(row.project_id), "project_name": row.project.name,
             "chapters": [{"chapter_no": no, "status": Chapter.objects.filter(
                 project=row.project, number=no).values_list("status", flat=True).first() or Chapter.Status.DRAFT}
                 for no in CHAPTER_STEPS]} for row in projects]
