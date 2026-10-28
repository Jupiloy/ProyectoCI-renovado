import json
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.test import Client, override_settings

from thesis.integrations.llm import DevelopmentMockProviderAdapter, set_test_adapter_override
from thesis.models import (
    AIGenerationBatch, AIGenerationBatchItem, AIGenerationBatchSynthesis, AIGenerationJob,
    ProjectWorkflow, ResearchProfile, WorkflowDependency, WorkflowTaskExecution,
)
from thesis.services.ai_batches import create_ai_batch, get_ai_batch, cancel_ai_batch, _batch_status
from thesis.services.batch_synthesis import (
    create_batch_synthesis, decide_batch_synthesis, get_batch_synthesis,
)
from thesis.services.ai_jobs import run_next_ai_job
from thesis.services.errors import DomainError
from thesis.services.projects import create_project
from thesis.services.reviews import assign_advisor
from thesis.services.workflows import create_or_update_draft, get_workflow_state, publish_workflow_draft


@pytest.fixture(autouse=True)
def reset_adapter():
    set_test_adapter_override(None)
    yield
    set_test_adapter_override(None)


@pytest.fixture
def batch_context(db):
    User = get_user_model()
    owner = User.objects.create_user(email="batch-owner@example.org", password="pass")
    advisor = User.objects.create_user(email="batch-advisor@example.org", password="pass")
    stranger = User.objects.create_user(email="batch-stranger@example.org", password="pass")
    project = create_project(owner, "Lotes IA")
    assign_advisor(owner, project.id, advisor.email)
    get_workflow_state(owner, project.id)
    create_or_update_draft(owner, project.id, {"tasks": []}, expected_version=0)
    publish_workflow_draft(owner, project.id, "Activar recorrido", expected_version=1)
    create_or_update_draft(
        owner, project.id,
        {"tasks": [
            {"task_id": "USR_BATCH_A", "title": "Tarea A", "chapter_no": 1,
             "order_index": 90, "is_active": True, "is_optional": True,
             "prompt_text": "Devuelve un resultado breve.",
             "output_schema": {"type": "object", "required": ["result"],
                               "properties": {"result": {"type": "string"}},
                               "additionalProperties": False}},
            {"task_id": "USR_BATCH_B", "title": "Tarea B", "chapter_no": 1,
             "order_index": 91, "is_active": True, "is_optional": True,
             "prompt_text": "Devuelve otro resultado breve.",
             "output_schema": {"type": "object", "required": ["result"],
                               "properties": {"result": {"type": "string"}},
                               "additionalProperties": False}},
        ]}, expected_version=0,
    )
    publish_workflow_draft(owner, project.id, "Publicar tareas de prueba", expected_version=1)
    profile = ResearchProfile.objects.get(project=project)
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response={"result": "mock"}))
    return owner, advisor, stranger, project, profile


def payload_for(profile, tasks=None, key=None):
    return {
        "tasks": tasks or [
            {"task_id": "USR_BATCH_A", "input_data": {"x": 1}, "context_refs": []},
            {"task_id": "USR_BATCH_B", "input_data": {"x": 2}, "context_refs": []},
        ],
        "expected_state_version": profile.lock_version,
        "workflow_version_no": profile.active_workflow.version_no,
        "idempotency_key": key or uuid4(),
    }


@pytest.mark.django_db
@override_settings(TESISMCP_SYNC_AI_GENERATION=False)
def test_batch_creation_http_and_same_key_idempotency(batch_context):
    owner, _, _, project, profile = batch_context
    client = Client()
    client.force_login(owner)
    data = payload_for(profile)
    body = {**data, "idempotency_key": str(data["idempotency_key"])}
    response = client.post(
        f"/api/v1/projects/{project.id}/ai-batches", data=json.dumps(body),
        content_type="application/json",
    )
    assert response.status_code == 202, response.content
    result = response.json()
    assert result["status"] == "QUEUED"
    assert result["item_count"] == 2
    assert result["status_counts"] == {
        "queued": 2, "running": 0, "succeeded": 0, "failed": 0, "cancelled": 0,
    }
    assert [item["task_id"] for item in result["items"]] == ["USR_BATCH_A", "USR_BATCH_B"]
    assert AIGenerationJob.objects.filter(project=project).count() == 2
    assert AIGenerationBatchItem.objects.filter(batch_id=result["batch_id"]).count() == 2
    listed = client.get(f"/api/v1/projects/{project.id}/ai-batches")
    assert listed.status_code == 200
    assert listed.json()["items"][0]["batch_id"] == result["batch_id"]
    fetched = client.get(f"/api/v1/projects/{project.id}/ai-batches/{result['batch_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["request_sha256"] == result["request_sha256"]

    repeated = client.post(
        f"/api/v1/projects/{project.id}/ai-batches", data=json.dumps(body),
        content_type="application/json",
    )
    assert repeated.status_code == 202
    assert repeated.json()["batch_id"] == result["batch_id"]
    assert AIGenerationJob.objects.filter(project=project).count() == 2

    body["tasks"][0]["input_data"] = {"x": 999}
    conflict = client.post(
        f"/api/v1/projects/{project.id}/ai-batches", data=json.dumps(body),
        content_type="application/json",
    )
    assert conflict.status_code == 409
    assert AIGenerationJob.objects.filter(project=project).count() == 2


@pytest.mark.django_db
@override_settings(TESISMCP_SYNC_AI_GENERATION=False)
def test_batch_rejects_duplicates_limit_internal_dependencies_and_non_owner(batch_context):
    owner, advisor, _, project, profile = batch_context
    same = [{"task_id": "USR_BATCH_A"}, {"task_id": "USR_BATCH_A"}]
    with pytest.raises(DomainError) as duplicate:
        create_ai_batch(owner, project.id, same, profile.lock_version,
                        profile.active_workflow.version_no, uuid4())
    assert duplicate.value.code == "VALIDATION_ERROR"
    too_many = [{"task_id": f"USR_{i}"} for i in range(9)]
    with pytest.raises(DomainError):
        create_ai_batch(owner, project.id, too_many, profile.lock_version,
                        profile.active_workflow.version_no, uuid4())

    task_a = profile.active_workflow.tasks.get(task_id="USR_BATCH_A")
    task_b = profile.active_workflow.tasks.get(task_id="USR_BATCH_B")
    WorkflowDependency.objects.create(
        workflow=profile.active_workflow, source_task=task_a, target_task=task_b,
        dependency_type=WorkflowDependency.Type.DATA_REQUIRED, is_blocking=True,
    )
    with pytest.raises(DomainError) as dependency:
        create_ai_batch(owner, project.id,
                        [{"task_id": task_a.task_id}, {"task_id": task_b.task_id}],
                        profile.lock_version, profile.active_workflow.version_no, uuid4())
    assert dependency.value.code == "BATCH_DEPENDENCY_CONFLICT"
    assert AIGenerationBatch.objects.filter(project=project).count() == 0

    with pytest.raises(DomainError) as permission:
        create_ai_batch(advisor, project.id, [{"task_id": "USR_BATCH_A"}],
                        profile.lock_version, profile.active_workflow.version_no, uuid4())
    assert permission.value.code == "NOT_FOUND"


@pytest.mark.django_db
@override_settings(TESISMCP_SYNC_AI_GENERATION=False)
def test_batch_cancel_and_aggregate_mixed_statuses(batch_context):
    owner, _, stranger, project, profile = batch_context
    created = create_ai_batch(owner, project.id, payload_for(profile)["tasks"],
                              profile.lock_version, profile.active_workflow.version_no, uuid4())
    batch_id = created["batch_id"]
    jobs = list(AIGenerationJob.objects.filter(project=project).order_by("created_at"))
    jobs[0].status = AIGenerationJob.Status.SUCCEEDED
    jobs[0].output_data = {"result": "ok"}
    jobs[0].save(update_fields=["status", "output_data"])
    mixed = get_ai_batch(owner, project.id, batch_id)
    assert mixed["status"] == "QUEUED"  # hay una tarea en cola y ninguna en RUNNING

    cancelled = cancel_ai_batch(owner, project.id, batch_id)
    assert cancelled["cancellation"] == {"cancelled": 1, "already_terminal": 1, "still_running": 0}
    assert cancelled["status"] == "PARTIAL"
    assert AIGenerationJob.objects.get(pk=jobs[1].pk).status == AIGenerationJob.Status.CANCELLED
    with pytest.raises(DomainError) as hidden:
        get_ai_batch(stranger, project.id, batch_id)
    assert hidden.value.code == "NOT_FOUND"


@pytest.mark.django_db
@override_settings(TESISMCP_SYNC_AI_GENERATION=False)
def test_batch_cancellation_does_not_interrupt_running_job(batch_context):
    owner, _, _, project, profile = batch_context
    created = create_ai_batch(owner, project.id, payload_for(profile)["tasks"],
                              profile.lock_version, profile.active_workflow.version_no, uuid4())
    jobs = list(AIGenerationJob.objects.filter(project=project).order_by("created_at"))
    jobs[0].status = AIGenerationJob.Status.RUNNING
    jobs[0].save(update_fields=["status"])
    client = Client()
    client.force_login(owner)
    response = client.post(f"/api/v1/projects/{project.id}/ai-batches/{created['batch_id']}/cancel")
    assert response.status_code == 200
    result = response.json()
    assert result["cancellation"] == {"cancelled": 1, "already_terminal": 0, "still_running": 1}
    assert AIGenerationJob.objects.get(pk=jobs[0].pk).status == AIGenerationJob.Status.RUNNING


@pytest.mark.django_db
@override_settings(TESISMCP_SYNC_AI_GENERATION=False)
def test_batch_and_item_rows_are_append_only_in_postgresql(batch_context):
    owner, _, _, project, profile = batch_context
    created = create_ai_batch(owner, project.id, payload_for(profile)["tasks"],
                              profile.lock_version, profile.active_workflow.version_no, uuid4())
    batch = AIGenerationBatch.objects.get(pk=created["batch_id"])
    item = AIGenerationBatchItem.objects.filter(batch=batch).first()
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            AIGenerationBatch.objects.filter(pk=batch.pk).update(request_sha256="0" * 64)
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            AIGenerationBatchItem.objects.filter(pk=item.pk).update(input_sha256="0" * 64)


@pytest.mark.django_db
@override_settings(TESISMCP_SYNC_AI_GENERATION=False)
def test_batch_rolls_back_when_later_job_validation_fails(batch_context):
    owner, _, _, project, profile = batch_context
    task_a = profile.active_workflow.tasks.get(task_id="USR_BATCH_A")
    task_b = profile.active_workflow.tasks.get(task_id="USR_BATCH_B")
    external = profile.active_workflow.tasks.get(task_id="P01")
    WorkflowDependency.objects.create(
        workflow=profile.active_workflow, source_task=task_b, target_task=external,
        dependency_type=WorkflowDependency.Type.DATA_REQUIRED, is_blocking=True,
    )
    with pytest.raises(DomainError) as blocked:
        create_ai_batch(owner, project.id,
                        [{"task_id": task_a.task_id}, {"task_id": task_b.task_id}],
                        profile.lock_version, profile.active_workflow.version_no, uuid4())
    assert blocked.value.code == "PREREQUISITE_LOCKED"
    assert AIGenerationBatch.objects.filter(project=project).count() == 0
    assert AIGenerationJob.objects.filter(project=project).count() == 0


@pytest.mark.django_db
@override_settings(TESISMCP_SYNC_AI_GENERATION=True)
def test_batch_rejects_synchronous_provider_mode_without_persisting(batch_context):
    owner, _, _, project, profile = batch_context
    with pytest.raises(DomainError) as sync_mode:
        create_ai_batch(owner, project.id, payload_for(profile)["tasks"],
                        profile.lock_version, profile.active_workflow.version_no, uuid4())
    assert sync_mode.value.code == "ASYNC_GENERATION_REQUIRED"
    assert AIGenerationBatch.objects.filter(project=project).count() == 0
    assert AIGenerationJob.objects.filter(project=project).count() == 0


@pytest.mark.parametrize(("statuses", "expected"), [
    (["QUEUED", "QUEUED"], "QUEUED"),
    (["RUNNING", "QUEUED"], "RUNNING"),
    (["SUCCEEDED", "SUCCEEDED"], "SUCCEEDED"),
    (["FAILED", "FAILED"], "FAILED"),
    (["CANCELLED", "CANCELLED"], "CANCELLED"),
    (["SUCCEEDED", "FAILED"], "PARTIAL"),
    (["SUCCEEDED", "QUEUED"], "QUEUED"),
])
def test_aggregate_status_derives_all_documented_combinations(statuses, expected):
    assert _batch_status([SimpleNamespace(status=status) for status in statuses]) == expected


def _set_job_succeeded_with_output(job, output):
    import hashlib
    job.status = AIGenerationJob.Status.SUCCEEDED
    job.output_data = output
    job.output_sha256 = hashlib.sha256(
        json.dumps(output, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    job.save(update_fields=["status", "output_data", "output_sha256"])


@pytest.mark.django_db
@override_settings(TESISMCP_SYNC_AI_GENERATION=False)
def test_batch_synthesis_snapshots_sources_generates_report_and_never_writes_manuscript(batch_context):
    owner, advisor, stranger, project, profile = batch_context
    created = create_ai_batch(
        owner, project.id, payload_for(profile)["tasks"], profile.lock_version,
        profile.active_workflow.version_no, uuid4(),
    )
    jobs = list(AIGenerationJob.objects.filter(project=project).order_by("created_at"))
    _set_job_succeeded_with_output(jobs[0], {"result": "A"})
    _set_job_succeeded_with_output(jobs[1], {"result": "B"})

    synthesis_output = {
        "summary": "Las dos tareas presentan alternativas sobre el mismo objetivo.",
        "summary_source_task_ids": ["USR_BATCH_A", "USR_BATCH_B"],
        "agreements": [{
            "claim": "Ambas proponen evaluar el mismo fenómeno.",
            "source_task_ids": ["USR_BATCH_A", "USR_BATCH_B"],
        }],
        "differences": [{
            "topic": "Unidad de análisis",
            "observations": [
                {"task_id": "USR_BATCH_A", "observation": "Propone docentes."},
                {"task_id": "USR_BATCH_B", "observation": "Propone estudiantes."},
            ],
        }],
        "gaps": [{"description": "No se proporcionó evidencia de acceso a la población."}],
        "recommendations": [{
            "recommendation": "Confirmar la unidad de análisis con el asesor.",
            "rationale": "Las tareas proponen unidades distintas.",
            "source_task_ids": ["USR_BATCH_A", "USR_BATCH_B"],
        }],
    }
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=synthesis_output))
    synthesis = create_batch_synthesis(
        owner, project.id, UUID(created["batch_id"]),
        [jobs[0].id, jobs[1].id], uuid4(),
    )
    synthesis_row = AIGenerationBatchSynthesis.objects.get(pk=synthesis["synthesis_id"])
    assert synthesis["status"] == "QUEUED"
    assert synthesis["sources"][0]["task_id"] == "USR_BATCH_A"
    assert synthesis_row.source_snapshot[0]["output_data"] == {"result": "A"}

    # La entrada de la síntesis permanece fija incluso si cambia el estado de decisión del job de origen.
    jobs[0].acceptance_status = AIGenerationJob.AcceptanceStatus.REJECTED
    jobs[0].save(update_fields=["acceptance_status"])
    assert run_next_ai_job() is True
    result = get_batch_synthesis(
        advisor, project.id, UUID(created["batch_id"]), UUID(synthesis["synthesis_id"]),
    )
    assert result["status"] == "SUCCEEDED"
    assert result["decision_status"] == "PENDING_REVIEW"
    assert result["output_data"]["summary_source_task_ids"] == ["USR_BATCH_A", "USR_BATCH_B"]
    assert result["sources"][0]["acceptance_status_at_snapshot"] == "PENDING_ACCEPTANCE"
    assert result["output_sha256"]
    assert not WorkflowTaskExecution.objects.filter(workflow=profile.active_workflow).exists()
    assert AIGenerationBatchSynthesis.objects.get(pk=synthesis["synthesis_id"]).source_snapshot[0]["output_data"] == {"result": "A"}
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            AIGenerationBatchSynthesis.objects.filter(pk=synthesis["synthesis_id"]).update(
                output_data={"summary": "alterada"},
            )
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            AIGenerationBatchSynthesis.objects.filter(pk=synthesis["synthesis_id"]).update(
                decision_status=AIGenerationBatchSynthesis.DecisionStatus.ACCEPTED,
            )

    accepted = decide_batch_synthesis(
        owner, project.id, UUID(created["batch_id"]), UUID(synthesis["synthesis_id"]),
        "ACCEPTED", uuid4(), "Informe auxiliar revisado.",
    )
    assert accepted["decision_status"] == "ACCEPTED"
    assert get_batch_synthesis(
        advisor, project.id, UUID(created["batch_id"]), UUID(synthesis["synthesis_id"]),
    )["decision_reason"] == "Informe auxiliar revisado."
    with pytest.raises(DomainError):
        decide_batch_synthesis(
            owner, project.id, UUID(created["batch_id"]), UUID(synthesis["synthesis_id"]),
            "REJECTED", uuid4(), "Cambio de decisión",
        )
    with pytest.raises(DomainError):
        get_batch_synthesis(
            stranger, project.id, UUID(created["batch_id"]), UUID(synthesis["synthesis_id"]),
        )


@pytest.mark.django_db
@override_settings(TESISMCP_SYNC_AI_GENERATION=False)
def test_batch_synthesis_rejects_unselected_task_references_and_preserves_snapshot(batch_context):
    owner, _, _, project, profile = batch_context
    created = create_ai_batch(
        owner, project.id, payload_for(profile)["tasks"], profile.lock_version,
        profile.active_workflow.version_no, uuid4(),
    )
    jobs = list(AIGenerationJob.objects.filter(project=project).order_by("created_at"))
    _set_job_succeeded_with_output(jobs[0], {"result": "A"})
    _set_job_succeeded_with_output(jobs[1], {"result": "B"})
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response={
        "summary": "Resumen con una referencia inexistente.",
        "summary_source_task_ids": ["USR_NOT_SELECTED"],
        "agreements": [], "differences": [], "gaps": [], "recommendations": [],
    }))
    synthesis = create_batch_synthesis(
        owner, project.id, UUID(created["batch_id"]), [jobs[0].id, jobs[1].id], uuid4(),
    )
    assert run_next_ai_job() is True
    failed = AIGenerationBatchSynthesis.objects.get(pk=synthesis["synthesis_id"])
    assert failed.status == AIGenerationBatchSynthesis.Status.FAILED
    assert failed.error_code == "OUTPUT_INVALID"
    assert failed.attempts == 1
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            AIGenerationBatchSynthesis.objects.filter(pk=failed.pk).update(source_snapshot=[])
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            AIGenerationBatchSynthesis.objects.filter(pk=failed.pk).delete()
