"""Guardado de pasos y revisiones académicas del MVP."""

import hashlib
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from pydantic import ValidationError

from thesis.models import (
    Chapter,
    ChapterRevision,
    EvidenceLink,
    ResearchProfile,
    StepProgress,
)
from thesis.services.access import require_project
from thesis.services.chapter_serialization import _revision_data
from thesis.services.errors import DomainError
from thesis.services.step_contracts import CONTRACTS
from thesis.services.step_materializers import execute_step_materializer


from thesis.services.chapter_queries import CHAPTER_STEPS, get_chapter, list_chapter_snapshots, get_chapter_snapshot
from thesis.services.chapter_submission import submit_chapter












def save_step(actor, project_id, step_code: str, content_md: str, output_data: dict,
              expected_version: int, idempotency_key: str) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    if step_code not in CONTRACTS:
        raise DomainError("VALIDATION_ERROR", f"Paso {step_code} no disponible en el catálogo de pasos")
    chapter_no = next((ch for ch, steps in CHAPTER_STEPS.items() if step_code in steps), None)
    if chapter_no is None:
        raise DomainError("VALIDATION_ERROR", f"Capítulo no encontrado para {step_code}")
    try:
        key = UUID(str(idempotency_key))
    except (ValueError, TypeError) as exc:
        raise DomainError("VALIDATION_ERROR", "idempotency_key debe ser UUID") from exc
    content_md = content_md.strip()
    if not content_md or len(content_md) > 200000:
        raise DomainError("VALIDATION_ERROR", "El contenido de la revisión debe tener entre 1 y 200000 caracteres")
    if step_code == "P04" and len(str(output_data.get("titulo_oficial", "")).split()) > 20:
        raise DomainError("RULE_WORD_COUNT_EXCEEDED", "El título supera el máximo de 20 palabras")
    if step_code == "P06":
        question = str(output_data.get("pregunta_general", "")).strip()
        if not question.startswith("¿") or not question.endswith("?"):
            raise DomainError("RULE_QUESTION_FORMAT", "La pregunta general requiere signos ¿?")
    try:
        validated = CONTRACTS[step_code].model_validate(output_data).model_dump()
    except ValidationError as exc:
        raise DomainError("VALIDATION_SCHEMA_ERROR", str(exc)[:1000]) from exc
    with transaction.atomic():
        profile = ResearchProfile.objects.select_for_update().get(project=project)
        chapter, _ = Chapter.objects.get_or_create(project=project, number=chapter_no)
        chapter = Chapter.objects.select_for_update().get(pk=chapter.pk)
        existing = ChapterRevision.objects.filter(chapter=chapter, idempotency_key=key).first()
        if existing:
            if (
                existing.step_code != step_code
                or existing.content_md != content_md
                or existing.workflow_id != profile.active_workflow_id
                or existing.workflow_version_no != (
                    profile.active_workflow.version_no if profile.active_workflow_id else None
                )
            ):
                raise DomainError("VERSION_CONFLICT", "La clave de idempotencia ya corresponde a otra revisión")
            return {**_revision_data(existing), "state_version": profile.lock_version, "idempotent": True}
        if profile.lock_version != expected_version:
            raise DomainError("VERSION_CONFLICT", "El perfil cambió; consulta la versión actual")
        if chapter.status not in (Chapter.Status.DRAFT, Chapter.Status.CHANGES_REQUESTED):
            raise DomainError("VERSION_CONFLICT", "El capítulo debe volver a borrador antes de editarse")

        active_wf = None
        prompt_text_used = ""
        prompt_version_used = None
        context_snapshot = {
            "approach": profile.approach,
            "ods_code": profile.ods_code,
            "unit_of_analysis": profile.unit_of_analysis,
            "place": profile.place,
            "period_text": profile.period_text,
        }

        if profile.workflow_mode == ResearchProfile.WorkflowMode.CONFIGURABLE_GRAPH:
            active_wf = profile.active_workflow
            if not active_wf:
                raise DomainError("CONFIG_ERROR", "No hay un recorrido activo publicado para el proyecto")
            wf_task = active_wf.tasks.filter(task_id=step_code).first()
            if not wf_task:
                raise DomainError("NOT_FOUND", f"La tarea {step_code} no existe en el recorrido publicado")
            if not wf_task.is_active:
                raise DomainError("PREREQUISITE_LOCKED", f"La tarea {step_code} no está activa en el recorrido publicado")

            unmet = []
            for dep in wf_task.prerequisite_dependencies.filter(is_blocking=True).select_related("target_task"):
                target = dep.target_task
                target_id = target.task_id
                if target.is_active:
                    if target.legacy_step_code:
                        progress = StepProgress.objects.filter(
                            project=project, step_code=target.legacy_step_code,
                            workflow=active_wf, workflow_version_no=active_wf.version_no,
                            status=StepProgress.Status.COMPLETED,
                        ).first()
                        target_output = progress.output_json if progress else None
                    else:
                        previous_execution = target.executions.filter(workflow=active_wf).order_by("-revision_no").first()
                        target_output = previous_execution.output_json if previous_execution else None
                    if target_output is None:
                        reason = f" ({dep.reason})" if dep.reason else ""
                        unmet.append(f"{target_id}{reason}")
                    elif dep.required_field:
                        value = target_output
                        for part in dep.required_field.split("."):
                            if not isinstance(value, dict) or part not in value:
                                value = None
                                break
                            value = value[part]
                        if value in (None, "", [], {}):
                            unmet.append(f"{target_id}.{dep.required_field}")
            if unmet:
                raise DomainError(
                    "PREREQUISITE_LOCKED",
                    f"Dependencias no satisfechas para {step_code}: completa {', '.join(unmet)} antes de continuar"
                )

            prompt_obj = getattr(wf_task, "prompt", None)
            prompt_text_used = prompt_obj.prompt_text if prompt_obj else ""
            prompt_version_used = prompt_obj.prompt_version if prompt_obj else None
            context_snapshot = {
                "approach": profile.approach,
                "ods_code": profile.ods_code,
                "unit_of_analysis": profile.unit_of_analysis,
                "place": profile.place,
                "period_text": profile.period_text,
            }
        else:
            sequence = [step for steps in CHAPTER_STEPS.values() for step in steps]
            if step_code != "P01":
                previous = sequence[sequence.index(step_code) - 1]
                if not StepProgress.objects.filter(project=project, step_code=previous, status=StepProgress.Status.COMPLETED).exists():
                    raise DomainError("PREREQUISITE_LOCKED", f"Completa {previous} antes de {step_code}")

        execute_step_materializer(project, profile, step_code, validated)
        if chapter.status == Chapter.Status.CHANGES_REQUESTED:
            chapter.resume_editing()
            chapter.save(update_fields=["status", "updated_at"])
        previous_revision = chapter.revisions.order_by("-revision_no").first()
        revision = ChapterRevision.objects.create(
            chapter=chapter,
            revision_no=(previous_revision.revision_no + 1 if previous_revision else 1),
            step_code=step_code,
            idempotency_key=key,
            content_md=content_md,
            content_sha256=hashlib.sha256(content_md.encode("utf-8")).hexdigest(),
            created_by=actor,
            workflow=active_wf,
            workflow_version_no=(active_wf.version_no if active_wf else None),
            prompt_text_used=prompt_text_used,
            prompt_version_used=prompt_version_used,
            context_snapshot=context_snapshot,
        )
        StepProgress.objects.update_or_create(
            project=project,
            step_code=step_code,
            defaults={
                "status": StepProgress.Status.COMPLETED,
                "output_json": validated,
                "completed_at": timezone.now(),
                "task_id": step_code,
                "workflow": active_wf,
                "workflow_version_no": (active_wf.version_no if active_wf else None),
            },
        )
        profile.lock_version += 1
        profile.save(update_fields=[
            "lock_version", "problem_statement", "ods_code",
            "unit_of_analysis", "place", "period_text", "approach", "updated_at",
        ])
        return {**_revision_data(revision), "state_version": profile.lock_version, "idempotent": False}






