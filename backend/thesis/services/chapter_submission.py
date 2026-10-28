"""Envío transaccional de capítulos e instantáneas inmutables."""
import hashlib
import json
from django.db import transaction
from thesis.models import Chapter, ChapterDocument, ChapterRevision, ChapterSnapshot, ResearchProfile, ReviewEvent, StepProgress, WorkflowTaskExecution
from thesis.services.access import require_project
from thesis.services.chapter_queries import CHAPTER_STEPS, get_chapter
from thesis.services.chapter_serialization import _snapshot_summary, _snapshot_evidence_links
from thesis.services.errors import DomainError


def submit_chapter(actor, project_id, chapter_no: int) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    if chapter_no not in CHAPTER_STEPS:
        raise DomainError("NOT_FOUND", "Capítulo no disponible en la plataforma")
    with transaction.atomic():
        profile = ResearchProfile.objects.select_for_update().get(project=project)
        chapter, _ = Chapter.objects.get_or_create(project=project, number=chapter_no)
        chapter = Chapter.objects.select_for_update().get(pk=chapter.pk)

        # Idempotencia: un reintento mientras el capítulo siga en READY devuelve el snapshot vinculado
        if chapter and chapter.status == Chapter.Status.READY:
            if chapter.submitted_snapshot_id:
                return {
                    **get_chapter(actor, project_id, chapter_no),
                    "snapshot": _snapshot_summary(chapter.submitted_snapshot),
                }
            raise DomainError("VERSION_CONFLICT", "El capítulo ya se encuentra en revisión")

        if chapter is None or chapter.status not in (Chapter.Status.DRAFT, Chapter.Status.CHANGES_REQUESTED):
            raise DomainError("VERSION_CONFLICT", "El capítulo no está listo para enviar")

        sections_manifest = []
        content_parts = []
        document = ChapterDocument.objects.select_related("current_revision").filter(chapter=chapter).first()
        document_revision = document.current_revision if document else None
        if document_revision:
            if document_revision.state_version != profile.lock_version:
                raise DomainError(
                    "CONTEXT_STALE",
                    "El documento cambió respecto del método o las salidas guardadas; actualízalo antes de enviar",
                )
            if not document_revision.content_md.strip():
                raise DomainError("PREREQUISITE_LOCKED", "El documento del capítulo está vacío")
        active_wf = None
        wf_version_no = None

        if profile.workflow_mode == ResearchProfile.WorkflowMode.CONFIGURABLE_GRAPH:
            active_wf = profile.active_workflow
            if active_wf is None:
                raise DomainError("CONFIG_ERROR", "El proyecto está en modo configurable pero no tiene un workflow activo")
            wf_version_no = active_wf.version_no
            chapter_tasks = active_wf.tasks.filter(chapter_no=chapter_no).order_by("order_index", "task_id")
            required_task_ids = set(
                chapter_tasks.filter(is_active=True, is_optional=False).values_list("task_id", flat=True)
            )
            legacy_task_ids = set(
                chapter_tasks.filter(is_active=True, is_optional=False)
                .exclude(legacy_step_code="").values_list("legacy_step_code", flat=True)
            )
            custom_task_ids = required_task_ids - set(
                chapter_tasks.exclude(legacy_step_code="").values_list("task_id", flat=True)
            )
            completed_task_ids = set(
                StepProgress.objects.filter(
                    project=project,
                    step_code__in=legacy_task_ids,
                    workflow=active_wf,
                    workflow_version_no=wf_version_no,
                    status=StepProgress.Status.COMPLETED,
                ).values_list("step_code", flat=True)
            )
            completed_task_ids.update(
                WorkflowTaskExecution.objects.filter(
                    workflow=active_wf,
                    task__task_id__in=custom_task_ids,
                ).values_list("task__task_id", flat=True)
            )
            missing = required_task_ids - completed_task_ids
            if missing:
                raise DomainError(
                    "PREREQUISITE_LOCKED",
                    f"Completa todas las tareas obligatorias del capítulo antes de enviar: {', '.join(sorted(missing))}",
                )

            for task in chapter_tasks:
                if task.legacy_step_code:
                    if task.is_active:
                        rev = chapter.revisions.filter(
                            step_code=task.legacy_step_code,
                            workflow=active_wf,
                            workflow_version_no=wf_version_no,
                        ).order_by("-revision_no").first()
                        progress = StepProgress.objects.filter(
                            project=project,
                            step_code=task.legacy_step_code,
                            workflow=active_wf,
                            workflow_version_no=wf_version_no,
                        ).first()
                        if progress and progress.status == StepProgress.Status.COMPLETED:
                            if rev is None:
                                raise DomainError(
                                    "PREREQUISITE_LOCKED",
                                    f"La tarea {task.task_id} no tiene una revisión textual de la versión activa para congelar",
                                )
                            evidence = _snapshot_evidence_links(rev)
                            sections_manifest.append({
                                "task_id": task.task_id,
                                "legacy_step_code": task.legacy_step_code,
                                "order_index": task.order_index,
                                "is_active": True,
                                "is_optional": task.is_optional,
                                "status": "COMPLETED",
                                "revision_id": rev.pk if rev else None,
                                "revision_no": rev.revision_no if rev else None,
                                "content_md": rev.content_md,
                                "content_sha256": rev.content_sha256 if rev else "",
                                "revision_workflow_id": rev.workflow_id,
                                "revision_workflow_version_no": rev.workflow_version_no,
                                "prompt_text_used": rev.prompt_text_used,
                                "prompt_version_used": rev.prompt_version_used,
                                "context_snapshot": rev.context_snapshot,
                                "created_by_id": rev.created_by_id,
                                "output_json": progress.output_json,
                                "evidence_links": evidence,
                                "rendered_in_text": True,
                            })
                            if rev and rev.content_md.strip():
                                content_parts.append(rev.content_md.strip())
                        else:
                            sections_manifest.append({
                                "task_id": task.task_id,
                                "legacy_step_code": task.legacy_step_code,
                                "order_index": task.order_index,
                                "is_active": True,
                                "is_optional": task.is_optional,
                                "status": "SKIPPED",
                                "rendered_in_text": False,
                            })
                    else:
                        sections_manifest.append({
                            "task_id": task.task_id,
                            "legacy_step_code": task.legacy_step_code,
                            "order_index": task.order_index,
                            "is_active": False,
                            "is_optional": task.is_optional,
                            "status": "SKIPPED",
                            "rendered_in_text": False,
                        })
                elif task.task_id.startswith("USR_"):
                    if task.is_active:
                        exec_obj = task.executions.filter(workflow=active_wf).order_by("-revision_no").first()
                        if exec_obj:
                            sections_manifest.append({
                                "task_id": task.task_id,
                                "order_index": task.order_index,
                                "is_active": True,
                                "is_optional": task.is_optional,
                                "status": "COMPLETED",
                                "execution_id": exec_obj.id,
                                "revision_no": exec_obj.revision_no,
                                "output_sha256": exec_obj.output_sha256,
                                "workflow_id": exec_obj.workflow_id,
                                "workflow_version_no": exec_obj.workflow.version_no,
                                "input_json": exec_obj.input_json,
                                "output_json": exec_obj.output_json,
                                "prompt_text_used": exec_obj.prompt_text_used,
                                "prompt_version_used": exec_obj.prompt_version_used,
                                "created_by_id": exec_obj.created_by_id,
                                "created_at": exec_obj.created_at.isoformat(),
                                "rendered_in_text": False,
                            })
                        else:
                            sections_manifest.append({
                                "task_id": task.task_id,
                                "order_index": task.order_index,
                                "is_active": True,
                                "is_optional": task.is_optional,
                                "status": "SKIPPED",
                                "rendered_in_text": False,
                            })
                    else:
                        sections_manifest.append({
                            "task_id": task.task_id,
                            "order_index": task.order_index,
                            "is_active": False,
                            "is_optional": task.is_optional,
                            "status": "SKIPPED",
                            "rendered_in_text": False,
                        })
        else:
            codes = CHAPTER_STEPS[chapter_no]
            completed = set(StepProgress.objects.filter(
                project=project,
                step_code__in=codes,
                workflow__isnull=True,
                workflow_version_no__isnull=True,
                status=StepProgress.Status.COMPLETED,
            ).values_list("step_code", flat=True))
            if completed != set(codes):
                raise DomainError("PREREQUISITE_LOCKED", "Completa todos los pasos del capítulo")

            for idx, code in enumerate(codes):
                rev = chapter.revisions.filter(
                    step_code=code,
                    workflow__isnull=True,
                    workflow_version_no__isnull=True,
                ).order_by("-revision_no").first()
                progress = StepProgress.objects.filter(
                    project=project,
                    step_code=code,
                    workflow__isnull=True,
                    workflow_version_no__isnull=True,
                ).first()
                if rev is None or progress is None:
                    raise DomainError(
                        "PREREQUISITE_LOCKED",
                        f"La tarea {code} no tiene una revisión y salida estructurada para congelar",
                    )
                evidence = _snapshot_evidence_links(rev)
                sections_manifest.append({
                    "task_id": code,
                    "legacy_step_code": code,
                    "order_index": idx,
                    "is_active": True,
                    "is_optional": False,
                    "status": "COMPLETED",
                    "revision_id": rev.pk,
                    "revision_no": rev.revision_no,
                    "content_md": rev.content_md,
                    "content_sha256": rev.content_sha256,
                    "revision_workflow_id": rev.workflow_id,
                    "revision_workflow_version_no": rev.workflow_version_no,
                    "prompt_text_used": rev.prompt_text_used,
                    "prompt_version_used": rev.prompt_version_used,
                    "context_snapshot": rev.context_snapshot,
                    "created_by_id": rev.created_by_id,
                    "output_json": progress.output_json,
                    "evidence_links": evidence,
                    "rendered_in_text": True,
                })
                if rev and rev.content_md.strip():
                    content_parts.append(rev.content_md.strip())

        if not any(section.get("status") == "COMPLETED" for section in sections_manifest):
            raise DomainError("PREREQUISITE_LOCKED", "Completa al menos una tarea del capítulo antes de enviarlo")

        if document_revision:
            # La revisión del editor es el texto canónico. Las tareas siguen en el manifest como procedencia,
            # pero no se afirman como texto visible si no existe un mapeo explícito de bloques.
            for section in sections_manifest:
                section["rendered_in_text"] = False
            content_parts = [document_revision.content_md]

        document_artifacts_manifest = []
        if document_revision:
            from thesis.services.document_artifacts import validate_document_artifacts
            document_artifacts_manifest = validate_document_artifacts(project, document_revision.content_tree)

        submitted_revision_ids = [
            section["revision_id"] for section in sections_manifest if section.get("revision_id") is not None
        ]
        last_revision = ChapterRevision.objects.filter(
            chapter=chapter, pk__in=submitted_revision_ids
        ).order_by("-revision_no").first()

        last_snapshot = ChapterSnapshot.objects.filter(chapter=chapter).order_by("-snapshot_no").first()
        next_snapshot_no = (last_snapshot.snapshot_no + 1) if last_snapshot else 1

        consolidated_content_md = "\n\n".join(content_parts)

        canonical_payload = {
            "chapter_no": chapter_no,
            "content_md": consolidated_content_md,
            "format_version": (3 if document_revision and document_revision.schema_version >= 2
                               else 2 if document_revision else 1),
            "project_title": project.title or project.name or "",
            "sections_manifest": sections_manifest,
            "state_version": profile.lock_version,
            "workflow_id": active_wf.pk if active_wf else None,
            "workflow_content_sha256": active_wf.content_sha256 if active_wf else "",
            "workflow_version_no": wf_version_no,
            "document_artifacts_manifest": document_artifacts_manifest,
        }
        if document_revision:
            canonical_payload["document_revision_id"] = str(document_revision.id)
            canonical_payload["document_revision_sha256"] = document_revision.content_sha256
            canonical_payload["citation_manifest_sha256"] = document_revision.citation_manifest_sha256
        payload_bytes = json.dumps(canonical_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()

        snapshot = ChapterSnapshot.objects.create(
            chapter=chapter,
            document_revision=document_revision,
            snapshot_no=next_snapshot_no,
            format_version=canonical_payload["format_version"],
            project_title=project.title or project.name or "",
            state_version=profile.lock_version,
            workflow=active_wf,
            workflow_version_no=wf_version_no,
            content_md=consolidated_content_md,
            sections_manifest=sections_manifest,
            document_artifacts_manifest=document_artifacts_manifest,
            payload_sha256=payload_sha256,
            created_by=actor,
        )

        chapter.submitted_snapshot = snapshot
        chapter.submit()
        chapter.save(update_fields=["status", "submitted_snapshot", "updated_at"])
        ReviewEvent.objects.create(
            chapter=chapter,
            revision=last_revision,
            snapshot=snapshot,
            actor=actor,
            action=ReviewEvent.Action.SUBMIT,
        )

    return {
        **get_chapter(actor, project_id, chapter_no),
        "snapshot": _snapshot_summary(snapshot),
    }
