"""Presentación de datos de dominio; sin cambios de persistencia."""

from uuid import UUID
from thesis.models import ChapterRevision, ChapterSnapshot, EvidenceLink
from thesis.services.citation_occurrences import list_citation_marks


def _revision_data(revision: ChapterRevision) -> dict:
    return {"revision_id": revision.pk, "revision_no": revision.revision_no,
            "chapter_no": revision.chapter.number, "step_code": revision.step_code,
            "content_md": revision.content_md, "content_sha256": revision.content_sha256,
            "workflow_version_no": revision.workflow_version_no,
            "prompt_version_used": revision.prompt_version_used,
            "created_at": revision.created_at.isoformat()}

def _snapshot_summary(snapshot: ChapterSnapshot) -> dict:
    return {
        "id": str(snapshot.id),
        "snapshot_no": snapshot.snapshot_no,
        "format_version": snapshot.format_version,
        "payload_sha256": snapshot.payload_sha256,
        "state_version": snapshot.state_version,
        "workflow_version_no": snapshot.workflow_version_no,
        "document_revision_id": str(snapshot.document_revision_id) if snapshot.document_revision_id else None,
        "created_at": snapshot.created_at.isoformat(),
    }

def _snapshot_detail(snapshot: ChapterSnapshot) -> dict:
    return {
        "id": str(snapshot.id),
        "chapter_no": snapshot.chapter.number,
        "snapshot_no": snapshot.snapshot_no,
        "format_version": snapshot.format_version,
        "project_title": snapshot.project_title,
        "state_version": snapshot.state_version,
        "workflow_version_no": snapshot.workflow_version_no,
        "document_revision_id": str(snapshot.document_revision_id) if snapshot.document_revision_id else None,
        "content_tree": snapshot.document_revision.content_tree if snapshot.document_revision_id else None,
        "citations": list_citation_marks(snapshot.document_revision) if snapshot.document_revision_id else [],
        "content_md": snapshot.content_md,
        "sections_manifest": snapshot.sections_manifest,
        "document_artifacts_manifest": snapshot.document_artifacts_manifest,
        "payload_sha256": snapshot.payload_sha256,
        "created_by_id": snapshot.created_by_id,
        "created_at": snapshot.created_at.isoformat(),
    }

def _snapshot_evidence_links(revision: ChapterRevision) -> list[dict]:
    links = list(
        EvidenceLink.objects.filter(revision=revision).order_by("pk").values(
            "id",
            "claim_text",
            "start_char",
            "end_char",
            "matched_text",
            "excerpt_id",
            "excerpt_sha256",
            "excerpt__page_no",
            "excerpt__source_id",
            "excerpt__source__sha256",
            "excerpt__source__title",
            "status",
        )
    )
    for link in links:
        for field, value in link.items():
            if isinstance(value, UUID):
                link[field] = str(value)
    return links
