"""Consultas autorizadas de capítulos e instantáneas."""
from uuid import UUID
from thesis.models import Chapter, ChapterSnapshot, ResearchProfile, StepProgress
from thesis.services.access import require_project
from thesis.services.chapter_serialization import _revision_data, _snapshot_summary, _snapshot_detail
from thesis.services.errors import DomainError
from thesis.step_catalogue import CATALOGO_PASOS

CHAPTER_STEPS = {
    chapter: [code for code, info in CATALOGO_PASOS.items() if info["capitulo"] == chapter]
    for chapter in sorted({info["capitulo"] for info in CATALOGO_PASOS.values()})
}


def get_chapter(actor, project_id, chapter_no: int) -> dict:
    project = require_project(actor, project_id)
    if chapter_no not in CHAPTER_STEPS:
        raise DomainError("NOT_FOUND", "Capítulo no disponible en la plataforma")
    chapter = Chapter.objects.filter(project=project, number=chapter_no).first()
    latest = chapter.revisions.order_by("-revision_no").first() if chapter else None
    progress_query = StepProgress.objects.filter(project=project, step_code__in=CHAPTER_STEPS[chapter_no])
    profile = ResearchProfile.objects.filter(project=project).first()
    if profile and profile.workflow_mode == ResearchProfile.WorkflowMode.CONFIGURABLE_GRAPH:
        if profile.active_workflow:
            progress_query = progress_query.filter(
                workflow=profile.active_workflow,
                workflow_version_no=profile.active_workflow.version_no,
            )
        else:
            progress_query = progress_query.none()
    return {
        "chapter_no": chapter_no,
        "status": chapter.status if chapter else Chapter.Status.DRAFT,
        "latest_revision": _revision_data(latest) if latest else None,
        "approved_revision_id": chapter.approved_revision_id if chapter else None,
        "approved_snapshot_id": str(chapter.approved_snapshot_id) if (chapter and chapter.approved_snapshot_id) else None,
        "submitted_snapshot_id": str(chapter.submitted_snapshot_id) if (chapter and chapter.submitted_snapshot_id) else None,
        "steps": list(progress_query.order_by("step_code").values("step_code", "status", "output_json")),
    }

def list_chapter_snapshots(actor, project_id, chapter_no: int) -> list[dict]:
    """Lista metadatos de las instantáneas históricas y vigentes de un capítulo."""
    project = require_project(actor, project_id)
    if chapter_no not in CHAPTER_STEPS:
        raise DomainError("NOT_FOUND", "Capítulo no disponible en la plataforma")
    chapter = Chapter.objects.filter(project=project, number=chapter_no).first()
    if not chapter:
        return []
    return [_snapshot_summary(s) for s in chapter.snapshots.order_by("-snapshot_no")]

def get_chapter_snapshot(actor, project_id, chapter_no: int, snapshot_id: UUID) -> dict:
    """Devuelve el detalle completo de una instantánea con su manifest y texto."""
    project = require_project(actor, project_id)
    if chapter_no not in CHAPTER_STEPS:
        raise DomainError("NOT_FOUND", "Capítulo no disponible en la plataforma")
    snapshot = ChapterSnapshot.objects.filter(
        chapter__project=project,
        chapter__number=chapter_no,
        pk=snapshot_id,
    ).select_related("chapter", "document_revision").first()
    if not snapshot:
        raise DomainError("NOT_FOUND", "Instantánea de capítulo no encontrada")
    return _snapshot_detail(snapshot)
