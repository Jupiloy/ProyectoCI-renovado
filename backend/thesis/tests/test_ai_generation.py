import io
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, override_settings
from django.core.management.base import CommandError

from thesis.integrations.llm import DevelopmentMockProviderAdapter, set_test_adapter_override
from thesis.models import (
    AIGenerationJob,
    Chapter,
    ChapterDocumentRevision,
    ChapterRevision,
    ProjectWorkflow,
    ResearchProfile,
    StepProgress,
    WorkflowTask,
    WorkflowTaskExecution,
)
from thesis.services.ai_jobs import (
    _accepted_proposal_content_md,
    accept_ai_proposal,
    cancel_ai_job,
    get_ai_job,
    reject_ai_proposal,
    request_task_generation,
    process_ai_generation_job,
    run_next_ai_job,
    fail_interrupted_ai_jobs,
)
from thesis.services.output_schemas import validate_output_data
from thesis.services.errors import DomainError
from thesis.services.exports import export_draft_docx
from thesis.services.chapter_documents import save_chapter_document
from thesis.services.projects import create_project
from thesis.services.reviews import assign_advisor
from thesis.services.workflows import create_or_update_draft, get_workflow_state, publish_workflow_draft


@pytest.fixture(autouse=True)
def reset_llm_adapter_override():
    set_test_adapter_override(None)
    yield
    set_test_adapter_override(None)


@pytest.fixture
def ai_context(db, settings):
    settings.TESISMCP_SYNC_AI_GENERATION = True
    User = get_user_model()
    owner = User.objects.create_user(email="ai-owner@example.org", password="pass")
    advisor = User.objects.create_user(email="ai-advisor@example.org", password="pass")
    stranger = User.objects.create_user(email="ai-stranger@example.org", password="pass")
    project = create_project(owner, "Tesis IA Asistida")
    assign_advisor(owner, project.id, advisor.email)

    # Activar recorrido configurable
    get_workflow_state(owner, project.id)
    create_or_update_draft(owner, project.id, {"tasks": []}, expected_version=0)
    publish_workflow_draft(owner, project.id, "Activar recorrido base", expected_version=1)

    return owner, advisor, stranger, project


def get_p01_sample_data():
    candidates = [
        {
            "id": i,
            "titulo_tentativo": f"Tema candidato automatizado número {i}",
            "pros": ["Acceso a datos primarios"],
            "contras": ["Tiempo limitado"],
            "viabilidad_preliminar": "ALTA" if i == 1 else "MEDIA",
        }
        for i in range(1, 6)
    ]
    return {"temas_propuestos": candidates, "tema_preseleccionado_id": 1}


def test_accepted_proposal_projects_only_explicit_chapter_text():
    chapter_text = "## Introducción\n\nTexto académico de la propuesta."
    assert _accepted_proposal_content_md("P05", {"contenido_markdown": chapter_text}) == chapter_text
    assert _accepted_proposal_content_md("P29", {"contenido_markdown": chapter_text}) == chapter_text

    structured = {"preguntas": ["¿Qué ocurre?"], "conteo": 1}
    rendered_structured = _accepted_proposal_content_md("P01", structured)
    assert rendered_structured.startswith("```json\n")
    assert json.loads(rendered_structured.removeprefix("```json\n").removesuffix("\n```")) == structured

    with pytest.raises(DomainError) as invalid_text:
        _accepted_proposal_content_md("P05", {"contenido_markdown": "   "})
    assert invalid_text.value.code == "OUTPUT_INVALID"


@pytest.mark.django_db(transaction=True)
def test_concurrent_ai_workers_claim_distinct_jobs_once(ai_context, monkeypatch):
    owner, _, _, project = ai_context
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=get_p01_sample_data()))
    profile = ResearchProfile.objects.get(project=project)
    with override_settings(TESISMCP_SYNC_AI_GENERATION=False):
        jobs = [
            request_task_generation(
                owner, project.id, "P01", idempotency_key=uuid4(),
                expected_state_version=profile.lock_version,
            )
            for _ in range(2)
        ]

    claimed_ids = []
    claimed_lock = threading.Lock()
    both_claimed = threading.Barrier(2)

    def hold_claimed_job(job_id, *, already_claimed=False):
        assert already_claimed is True
        with claimed_lock:
            claimed_ids.append(str(job_id))
        both_claimed.wait(timeout=10)

    monkeypatch.setattr("thesis.services.ai_jobs.process_ai_generation_job", hold_claimed_job)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_next_ai_job) for _ in range(2)]
        assert [future.result(timeout=15) for future in futures] == [True, True]

    assert len(set(claimed_ids)) == 2
    persisted = list(AIGenerationJob.objects.filter(pk__in=[item["job_id"] for item in jobs]))
    assert {job.status for job in persisted} == {AIGenerationJob.Status.RUNNING}
    assert {job.attempts for job in persisted} == {1}


def test_interrupted_ai_jobs_fail_without_automatic_retry(ai_context):
    owner, _, _, project = ai_context
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=get_p01_sample_data()))
    profile = ResearchProfile.objects.get(project=project)
    with override_settings(TESISMCP_SYNC_AI_GENERATION=False):
        queued = request_task_generation(
            owner, project.id, "P01", idempotency_key=uuid4(),
            expected_state_version=profile.lock_version,
        )
    AIGenerationJob.objects.filter(pk=queued["job_id"]).update(
        status=AIGenerationJob.Status.RUNNING, attempts=1,
    )

    assert fail_interrupted_ai_jobs() == 1
    job = AIGenerationJob.objects.get(pk=queued["job_id"])
    assert job.status == AIGenerationJob.Status.FAILED
    assert job.error_code == "WORKER_INTERRUPTED"
    assert job.finished_at is not None
    assert job.attempts == 1
    assert fail_interrupted_ai_jobs() == 0


def test_ai_worker_once_rejects_more_than_one_consumer(settings):
    settings.TESISMCP_AI_WORKER_MAX_CONCURRENCY = 4
    with pytest.raises(CommandError, match="--once admite solo --concurrency 1"):
        call_command("run_ai_worker", "--once", "--concurrency", "2")


@pytest.mark.parametrize("concurrency", [0, 5])
def test_ai_worker_rejects_concurrency_outside_configured_range(settings, concurrency):
    settings.TESISMCP_AI_WORKER_MAX_CONCURRENCY = 4
    with pytest.raises(CommandError, match="--concurrency debe estar entre 1 y 4"):
        call_command("run_ai_worker", "--concurrency", str(concurrency))


def test_p05_proposal_preview_and_acceptance_replace_canonical_document(ai_context):
    owner, _, stranger, project = ai_context
    client = Client()
    client.force_login(owner)
    profile = ResearchProfile.objects.get(project=project)
    original_tree = {
        "schema_version": 1,
        "blocks": [{"type": "paragraph", "id": str(uuid4()), "text": "Borrador previo del tesista."}],
    }
    original = save_chapter_document(
        owner, project.id, 1, original_tree, expected_version=0, idempotency_key=uuid4(),
    )
    profile.refresh_from_db()
    p04_output = {
        "titulo_oficial": "Uso de herramientas digitales en estudiantes de Piura durante 2026",
        "conteo_palabras": 10,
        "variables_confirmadas": ["herramientas digitales"],
        "unidad_analisis_confirmada": "estudiantes",
        "lugar_confirmado": "Piura",
        "periodo_confirmado": 2026,
    }
    StepProgress.objects.create(
        project=project,
        step_code="P04",
        status=StepProgress.Status.COMPLETED,
        output_json=p04_output,
        workflow=profile.active_workflow,
        workflow_version_no=profile.active_workflow.version_no,
    )
    paragraph = " ".join(["palabra"] * 90)
    p05_output = {
        "contenido_markdown": "\n\n".join([paragraph, paragraph + " uno", paragraph + " dos"]),
        "num_parrafos": 3,
        "palabras_totales": 272,
    }
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=p05_output))
    generated = request_task_generation(
        owner, project.id, "P05", input_data={}, idempotency_key=uuid4(),
        expected_state_version=profile.lock_version,
    )
    job_id = generated["job_id"]
    assert generated["status"] == AIGenerationJob.Status.SUCCEEDED

    preview_response = client.get(f"/api/v1/projects/{project.id}/ai-jobs/{job_id}/document-diff")
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["operation"] == "REPLACE_DOCUMENT"
    assert preview["expected_document_version"] == original["document_version"]
    assert preview["before_tree"] == original_tree
    assert len(preview["after_tree"]["blocks"]) == 3
    assert preview["source_output_sha256"] == generated["output_sha256"]
    assert client.get(f"/api/v1/projects/{project.id}/chapters/1/document").json()["content_tree"] == original_tree

    client.force_login(stranger)
    assert client.get(f"/api/v1/projects/{project.id}/ai-jobs/{job_id}/document-diff").status_code == 404
    client.force_login(owner)

    with pytest.raises(DomainError) as tampered_diff:
        accept_ai_proposal(
            owner, project.id, job_id, expected_state_version=profile.lock_version,
            decision_key=uuid4(), expected_document_version=preview["expected_document_version"],
            proposal_sha256="0" * 64,
        )
    assert tampered_diff.value.code == "VERSION_CONFLICT"
    assert client.get(f"/api/v1/projects/{project.id}/chapters/1/document").json()["content_tree"] == original_tree

    decision_key = uuid4()
    accepted = client.post(
        f"/api/v1/projects/{project.id}/ai-jobs/{job_id}/accept",
        data=json.dumps({
            "expected_state_version": profile.lock_version,
            "decision_key": str(decision_key),
            "expected_document_version": preview["expected_document_version"],
            "proposal_sha256": preview["proposal_sha256"],
        }),
        content_type="application/json",
    )
    assert accepted.status_code == 200
    accepted_data = accepted.json()
    assert accepted_data["result_document_revision_id"]

    current_document = client.get(f"/api/v1/projects/{project.id}/chapters/1/document").json()
    assert current_document["document_version"] == original["document_version"] + 1
    assert current_document["content_md"] == p05_output["contenido_markdown"]
    assert current_document["source"] == ChapterDocumentRevision.Source.AI_PROPOSAL
    assert current_document["content_tree"] == preview["after_tree"]
    assert str(AIGenerationJob.objects.get(pk=job_id).result_document_revision_id) == accepted_data["result_document_revision_id"]

    repeated = accept_ai_proposal(
        owner, project.id, job_id, expected_state_version=profile.lock_version,
        decision_key=decision_key,
    )
    assert repeated["idempotent"] is True
    assert repeated["result_document_revision_id"] == accepted_data["result_document_revision_id"]


def test_ai_generation_p01_success_and_acceptance(ai_context):
    owner, _, _, project = ai_context
    p01_data = get_p01_sample_data()

    # Inyectar adaptador de desarrollo con respuesta válida para P01
    mock_adapter = DevelopmentMockProviderAdapter(default_response=p01_data)
    set_test_adapter_override(mock_adapter)

    req_key = uuid4()
    profile = ResearchProfile.objects.get(project=project)
    start_lock_version = profile.lock_version

    # Solicitar generación de P01
    res = request_task_generation(
        actor=owner,
        project_id=project.id,
        task_id="P01",
        input_data={"enfoque_interes": "cuantitativo"},
        idempotency_key=req_key,
        expected_state_version=start_lock_version,
    )

    job_id = res["job_id"]
    job = AIGenerationJob.objects.get(pk=job_id)
    assert job.status == AIGenerationJob.Status.SUCCEEDED
    assert job.acceptance_status == AIGenerationJob.AcceptanceStatus.PENDING_ACCEPTANCE
    assert job.output_data == p01_data
    assert job.output_sha256 != ""
    assert job.provider == "DEVELOPMENT_MOCK"

    # Demostrar que el manuscrito canónico NO ha sido alterado aún
    assert not ChapterRevision.objects.filter(step_code="P01", chapter__project=project).exists()
    assert not StepProgress.objects.filter(project=project, step_code="P01", status="COMPLETED").exists()

    # Aceptar explícitamente la propuesta
    dec_key = uuid4()
    acc_res = accept_ai_proposal(
        actor=owner,
        project_id=project.id,
        job_id=job_id,
        expected_state_version=start_lock_version,
        decision_key=dec_key,
    )

    assert acc_res["acceptance_status"] == "ACCEPTED"
    assert acc_res["idempotent"] is False
    assert acc_res["result_revision_id"] is not None

    # Demostrar que AHORA sí existe la revisión canónica inmutable
    rev = ChapterRevision.objects.get(pk=acc_res["result_revision_id"])
    assert rev.step_code == "P01"
    assert rev.content_md == "```json\n" + json.dumps(job.output_data, ensure_ascii=False, indent=2) + "\n```"
    assert rev.workflow_version_no == profile.active_workflow.version_no

    prog = StepProgress.objects.get(project=project, step_code="P01")
    assert prog.status == StepProgress.Status.COMPLETED
    assert prog.output_json == p01_data

    # Repetir la aceptación es idempotente
    repeat_acc = accept_ai_proposal(
        actor=owner,
        project_id=project.id,
        job_id=job_id,
        expected_state_version=acc_res["state_version"],
        decision_key=dec_key,
    )
    assert repeat_acc["idempotent"] is True
    assert repeat_acc["result_revision_id"] == rev.pk
    with pytest.raises(DomainError) as wrong_decision_key:
        accept_ai_proposal(
            owner, project.id, job_id,
            expected_state_version=acc_res["state_version"], decision_key=uuid4(),
        )
    assert wrong_decision_key.value.code == "IDEMPOTENCY_CONFLICT"


def test_ai_generation_usr_custom_task_success_and_reject(ai_context):
    owner, _, _, project = ai_context

    # Crear tarea personalizada USR_INTERVIEW con output_schema seguro
    schema = {
        "type": "object",
        "required": ["preguntas", "categoria"],
        "properties": {
            "preguntas": {"type": "array"},
            "categoria": {"type": "string"},
        },
        "additionalProperties": False,
    }
    create_or_update_draft(
        owner,
        project.id,
        {
            "tasks": [
                {
                    "task_id": "USR_INTERVIEW",
                    "title": "Diseño de Guía de Entrevista",
                    "chapter_no": 3,
                    "order_index": 50,
                    "is_active": True,
                    "is_optional": True,
                    "prompt_text": "Genera preguntas abiertas para actores clave.",
                    "output_schema": schema,
                }
            ]
        },
        expected_version=0,
    )
    publish_workflow_draft(owner, project.id, "Publicar tarea personalizada", expected_version=1)

    custom_output = {
        "preguntas": ["¿Cómo evalúa la adopción tecnológica?", "¿Cuáles son los desafíos?"],
        "categoria": "Infraestructura y Procesos",
    }
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=custom_output))

    profile = ResearchProfile.objects.get(project=project)
    res = request_task_generation(
        actor=owner,
        project_id=project.id,
        task_id="USR_INTERVIEW",
        input_data={"poblacion": "Docentes universitarios"},
        idempotency_key=uuid4(),
        expected_state_version=profile.lock_version,
    )
    job_id = res["job_id"]
    job = AIGenerationJob.objects.get(pk=job_id)
    assert job.status == "SUCCEEDED"

    # Rechazar explícitamente la propuesta
    dec_key = uuid4()
    rej_res = reject_ai_proposal(
        actor=owner,
        project_id=project.id,
        job_id=job_id,
        decision_key=dec_key,
        reason="Las preguntas son demasiado genéricas; se requiere mayor profundidad.",
    )
    assert rej_res["acceptance_status"] == "REJECTED"
    assert rej_res["idempotent"] is False

    # Demostrar que NO se alteró ninguna ejecución ni capítulo
    assert not WorkflowTaskExecution.objects.filter(task__task_id="USR_INTERVIEW").exists()
    assert not ChapterRevision.objects.filter(chapter__project=project, step_code="USR_INTERVIEW").exists()

    # Intentar aceptar una propuesta rechazada debe fallar
    with pytest.raises(DomainError) as err:
        accept_ai_proposal(
            actor=owner,
            project_id=project.id,
            job_id=job_id,
            expected_state_version=profile.lock_version,
            decision_key=uuid4(),
        )
    assert err.value.code == "VERSION_CONFLICT"


def test_ai_generation_strict_validation_and_extra_fields(ai_context):
    owner, _, _, project = ai_context

    # Proveedor devuelve campo extra en P01
    invalid_p01_data = get_p01_sample_data()
    invalid_p01_data["campo_no_permitido"] = "alucinación residual"

    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=invalid_p01_data))

    profile = ResearchProfile.objects.get(project=project)
    res = request_task_generation(
        actor=owner,
        project_id=project.id,
        task_id="P01",
        idempotency_key=uuid4(),
        expected_state_version=profile.lock_version,
    )
    job = AIGenerationJob.objects.get(pk=res["job_id"])
    assert job.status == AIGenerationJob.Status.FAILED
    assert job.error_code == "OUTPUT_INVALID"
    assert "extra_forbidden" in job.error_message or "campo_no_permitido" in job.error_message


def test_custom_json_schema_validates_nested_items_and_constraints():
    schema = {
        "type": "object",
        "required": ["preguntas"],
        "properties": {
            "preguntas": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        },
        "additionalProperties": False,
    }
    assert validate_output_data({"preguntas": ["Pregunta"]}, schema) == {"preguntas": ["Pregunta"]}
    with pytest.raises(DomainError) as nested_error:
        validate_output_data({"preguntas": [123]}, schema)
    assert nested_error.value.code == "OUTPUT_INVALID"
    with pytest.raises(DomainError) as constraint_error:
        validate_output_data({"preguntas": []}, schema)
    assert constraint_error.value.code == "OUTPUT_INVALID"


def test_generation_is_queued_by_default_and_processed_by_worker(ai_context):
    owner, _, _, project = ai_context
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=get_p01_sample_data()))
    profile = ResearchProfile.objects.get(project=project)
    with override_settings(TESISMCP_SYNC_AI_GENERATION=False):
        result = request_task_generation(
            owner, project.id, "P01", idempotency_key=uuid4(),
            expected_state_version=profile.lock_version,
        )
        job = AIGenerationJob.objects.get(pk=result["job_id"])
        assert job.status == AIGenerationJob.Status.QUEUED
        assert process_ai_generation_job(job.id).status == AIGenerationJob.Status.SUCCEEDED


def test_generation_fails_closed_without_configured_provider(ai_context):
    owner, _, _, project = ai_context
    set_test_adapter_override(None)
    profile = ResearchProfile.objects.get(project=project)
    with override_settings(TESISMCP_LLM_PROVIDER="DISABLED", TESISMCP_SYNC_AI_GENERATION=False):
        with pytest.raises(DomainError) as error:
            request_task_generation(
                owner, project.id, "P01", idempotency_key=uuid4(),
                expected_state_version=profile.lock_version,
            )
    assert error.value.code == "PROVIDER_UNAVAILABLE"
    assert not AIGenerationJob.objects.filter(project=project).exists()


def test_ai_generation_provider_error_handling(ai_context):
    owner, _, _, project = ai_context
    profile = ResearchProfile.objects.get(project=project)

    # 1. Simular Timeout
    set_test_adapter_override(DevelopmentMockProviderAdapter(simulate_error="timeout"))
    res_t = request_task_generation(owner, project.id, "P01", idempotency_key=uuid4(), expected_state_version=profile.lock_version)
    job_t = AIGenerationJob.objects.get(pk=res_t["job_id"])
    assert job_t.status == "FAILED"
    assert job_t.error_code == "PROVIDER_TIMEOUT"

    # 2. Simular Rate Limit
    set_test_adapter_override(DevelopmentMockProviderAdapter(simulate_error="rate_limit"))
    res_r = request_task_generation(owner, project.id, "P01", idempotency_key=uuid4(), expected_state_version=profile.lock_version)
    job_r = AIGenerationJob.objects.get(pk=res_r["job_id"])
    assert job_r.status == "FAILED"
    assert job_r.error_code == "PROVIDER_RATE_LIMITED"

    # 3. Simular Unavailable
    set_test_adapter_override(DevelopmentMockProviderAdapter(simulate_error="unavailable"))
    res_u = request_task_generation(owner, project.id, "P01", idempotency_key=uuid4(), expected_state_version=profile.lock_version)
    job_u = AIGenerationJob.objects.get(pk=res_u["job_id"])
    assert job_u.status == "FAILED"
    assert job_u.error_code == "PROVIDER_UNAVAILABLE"


def test_ai_generation_blocks_unmet_dependencies_and_stale_context(ai_context):
    owner, _, _, project = ai_context
    profile = ResearchProfile.objects.get(project=project)

    # P06 depende de P04. Como P04 no está completo, debe bloquearse
    with pytest.raises(DomainError) as dep_err:
        request_task_generation(owner, project.id, "P06", idempotency_key=uuid4(), expected_state_version=profile.lock_version)
    assert dep_err.value.code == "PREREQUISITE_LOCKED"
    assert "P04" in dep_err.value.message

    # Generar propuesta para P01
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=get_p01_sample_data()))
    res = request_task_generation(owner, project.id, "P01", idempotency_key=uuid4(), expected_state_version=profile.lock_version)
    job_id = res["job_id"]

    # Simular cambio concurrente de contexto en el perfil
    profile.lock_version += 1
    profile.save(update_fields=["lock_version"])

    # El job queda ligado al estado existente al solicitarse. Enviar la nueva
    # versión del perfil no debe permitir aceptar una propuesta obsoleta.
    with pytest.raises(DomainError) as stale_err:
        accept_ai_proposal(owner, project.id, job_id, expected_state_version=profile.lock_version, decision_key=uuid4())
    assert stale_err.value.code == "CONTEXT_STALE"


def test_ai_generation_permissions_and_cross_project_isolation(ai_context):
    owner, advisor, stranger, project = ai_context
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=get_p01_sample_data()))
    profile = ResearchProfile.objects.get(project=project)

    # 1. Usuario ajeno no puede solicitar generación
    with pytest.raises(DomainError) as p_err:
        request_task_generation(stranger, project.id, "P01", idempotency_key=uuid4(), expected_state_version=profile.lock_version)
    assert p_err.value.code in ("NOT_FOUND", "PERMISSION_DENIED")

    # 2. Asesor no puede solicitar generación (solo el tesista titular)
    with pytest.raises(DomainError) as adv_err:
        request_task_generation(advisor, project.id, "P01", idempotency_key=uuid4(), expected_state_version=profile.lock_version)
    assert adv_err.value.code in ("PERMISSION_DENIED", "NOT_FOUND")

    # Generar con el titular
    job_res = request_task_generation(owner, project.id, "P01", idempotency_key=uuid4(), expected_state_version=profile.lock_version)
    job_id = job_res["job_id"]

    # 3. Asesor puede consultar el job
    job_view = get_ai_job(advisor, project.id, job_id)
    assert job_view["job_id"] == job_id

    # 4. Asesor NO puede aceptar la propuesta
    with pytest.raises(DomainError) as adv_acc_err:
        accept_ai_proposal(advisor, project.id, job_id, expected_state_version=profile.lock_version, decision_key=uuid4())
    assert adv_acc_err.value.code in ("PERMISSION_DENIED", "NOT_FOUND")

    # 5. Usuario ajeno no puede consultar el job
    with pytest.raises(DomainError) as str_err:
        get_ai_job(stranger, project.id, job_id)
    assert str_err.value.code == "NOT_FOUND"


def test_ai_generation_idempotency_rules(ai_context):
    owner, _, _, project = ai_context
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=get_p01_sample_data()))
    profile = ResearchProfile.objects.get(project=project)

    key = uuid4()
    # Primera solicitud
    res1 = request_task_generation(
        owner, project.id, "P01", input_data={"filtro": "A"}, idempotency_key=key, expected_state_version=profile.lock_version
    )

    # Segunda solicitud idéntica
    res2 = request_task_generation(
        owner, project.id, "P01", input_data={"filtro": "A"}, idempotency_key=key, expected_state_version=profile.lock_version
    )
    assert res1["job_id"] == res2["job_id"]

    # Solicitud con misma clave pero datos diferentes -> VERSION_CONFLICT
    with pytest.raises(DomainError) as conf_err:
        request_task_generation(
            owner, project.id, "P01", input_data={"filtro": "DIFERENTE"}, idempotency_key=key, expected_state_version=profile.lock_version
        )
    assert conf_err.value.code == "VERSION_CONFLICT"


def test_usr_outputs_are_not_automatically_in_docx(ai_context):
    owner, _, _, project = ai_context

    # Guardar P01 canónico
    p01_data = get_p01_sample_data()
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=p01_data))
    profile = ResearchProfile.objects.get(project=project)
    res_p01 = request_task_generation(owner, project.id, "P01", idempotency_key=uuid4(), expected_state_version=profile.lock_version)
    accept_ai_proposal(owner, project.id, res_p01["job_id"], expected_state_version=profile.lock_version, decision_key=uuid4())

    # Crear y aceptar tarea USR_NOTES
    schema = {
        "type": "object",
        "properties": {"nota": {"type": "string"}},
        "additionalProperties": False,
    }
    create_or_update_draft(
        owner,
        project.id,
        {
            "tasks": [
                {
                    "task_id": "USR_NOTES",
                    "title": "Notas de campo",
                    "chapter_no": 1,
                    "is_active": True,
                    "is_optional": True,
                    "prompt_text": "Generar notas de campo.",
                    "output_schema": schema,
                }
            ]
        },
        expected_version=0,
    )
    publish_workflow_draft(owner, project.id, "Publicar USR_NOTES", expected_version=1)

    profile.refresh_from_db()
    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response={"nota": "Secreto de campo no exportable"}))
    res_usr = request_task_generation(owner, project.id, "USR_NOTES", idempotency_key=uuid4(), expected_state_version=profile.lock_version)
    accept_ai_proposal(owner, project.id, res_usr["job_id"], expected_state_version=profile.lock_version, decision_key=uuid4())

    # Generar exportación DOCX
    docx_io = export_draft_docx(owner, project.id)
    docx_bytes = docx_io.getvalue()
    assert len(docx_bytes) > 0

    # Demostrar que el output de USR_NOTES no fue insertado en el texto exportado
    assert b"Secreto de campo no exportable" not in docx_bytes


def test_ai_api_rest_endpoints(ai_context):
    owner, _, _, project = ai_context
    client = Client()
    client.force_login(owner)

    set_test_adapter_override(DevelopmentMockProviderAdapter(default_response=get_p01_sample_data()))
    profile = ResearchProfile.objects.get(project=project)

    # 1. POST generate
    gen_payload = {
        "expected_state_version": profile.lock_version,
        "input_data": {"test": True},
        "idempotency_key": str(uuid4()),
    }
    resp = client.post(
        f"/api/v1/projects/{project.id}/workflow/tasks/P01/generate",
        data=json.dumps(gen_payload),
        content_type="application/json",
    )
    assert resp.status_code in (200, 202)
    job_data = resp.json()
    job_id = job_data["job_id"]
    assert job_data["task_id"] == "P01"

    # 2. GET ai-job
    resp_get = client.get(f"/api/v1/projects/{project.id}/ai-jobs/{job_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["job_id"] == job_id

    # 3. POST accept
    acc_payload = {
        "expected_state_version": profile.lock_version,
        "decision_key": str(uuid4()),
    }
    resp_acc = client.post(
        f"/api/v1/projects/{project.id}/ai-jobs/{job_id}/accept",
        data=json.dumps(acc_payload),
        content_type="application/json",
    )
    assert resp_acc.status_code == 200
    assert resp_acc.json()["acceptance_status"] == "ACCEPTED"
