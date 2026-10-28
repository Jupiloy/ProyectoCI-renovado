"""Pruebas unitarias y de integración para GeminiProviderAdapter y la fábrica LLM."""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from google.genai import errors

from thesis.integrations.llm.base import (
    LLMMessage,
    LLMOutputInvalidError,
    LLMProviderRateLimitError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
)
from thesis.integrations.llm.factory import get_llm_adapter, set_test_adapter_override
from thesis.integrations.llm.gemini import GeminiProviderAdapter
from thesis.models import AIGenerationJob, ChapterRevision, ResearchProfile, StepProgress, User
from thesis.services.ai_jobs import accept_ai_proposal, process_ai_generation_job, request_task_generation
from thesis.services.projects import create_project
from thesis.services.workflows import create_or_update_draft, get_workflow_state, publish_workflow_draft


def _make_dummy_usage(prompt: int = 120, candidates: int = 85, total: int = 205):
    usage = MagicMock()
    usage.prompt_token_count = prompt
    usage.candidates_token_count = candidates
    usage.total_token_count = total
    return usage


# ==============================================================================
# 1. Pruebas unitarias de GeminiProviderAdapter con SDK simulado
# ==============================================================================


def test_gemini_adapter_init_requires_api_key():
    with pytest.raises(LLMProviderUnavailableError, match="Falta la clave API"):
        GeminiProviderAdapter(api_key="")

    with pytest.raises(LLMProviderUnavailableError, match="Falta la clave API"):
        GeminiProviderAdapter(api_key="   ")


def test_gemini_adapter_init_requires_model():
    with pytest.raises(LLMProviderUnavailableError, match="Falta TESISMCP_GEMINI_MODEL"):
        GeminiProviderAdapter(api_key="fake-secret-key", model=" ")


@patch("thesis.integrations.llm.gemini.genai.Client")
def test_gemini_adapter_generate_structured_success_with_usage(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    sample_output = {"tema_ganador_id": 1, "tema_ganador_titulo": "Tema A"}
    mock_response = MagicMock()
    mock_response.text = json.dumps(sample_output)
    mock_response.usage_metadata = _make_dummy_usage(100, 50, 150)
    mock_client.models.generate_content.return_value = mock_response

    adapter = GeminiProviderAdapter(api_key="fake-secret-key", model="gemini-3.8-flash")
    messages = [
        LLMMessage(role="system", content="Instrucción de sistema"),
        LLMMessage(role="user", content="Pregunta de usuario"),
    ]
    schema = {"type": "object", "properties": {"tema_ganador_id": {"type": "integer"}}}

    result = adapter.generate_structured(messages=messages, output_schema=schema, timeout=25.0)

    assert result.provider == "GEMINI"
    assert result.model == "gemini-3.8-flash"
    assert result.content_json == sample_output
    assert result.usage == {
        "prompt_token_count": 100,
        "candidates_token_count": 50,
        "total_token_count": 150,
    }
    mock_client_cls.assert_called_once()
    mock_client.models.generate_content.assert_called_once()


@patch("thesis.integrations.llm.gemini.genai.Client")
def test_gemini_adapter_generate_structured_without_usage_metadata(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.text = json.dumps({"status": "ok"})
    mock_response.usage_metadata = None
    mock_client.models.generate_content.return_value = mock_response

    adapter = GeminiProviderAdapter(api_key="fake-secret-key")
    result = adapter.generate_structured(
        messages=[LLMMessage(role="user", content="Hola")],
        output_schema={"type": "object"},
    )
    assert result.usage == {}
    assert result.content_json == {"status": "ok"}


def test_model_cannot_be_overridden_through_model_config():
    adapter = GeminiProviderAdapter(api_key="fake-secret-key", model="gemini-3.8-flash")
    with pytest.raises(LLMProviderUnavailableError, match="configure TESISMCP_GEMINI_MODEL"):
        adapter.generate_structured(
            [LLMMessage(role="user", content="Hola")],
            {"type": "object"},
            model_config={"model": "arbitrary-model"},
        )


def test_unknown_message_role_is_rejected_before_provider_call():
    adapter = GeminiProviderAdapter(api_key="fake-secret-key")
    with pytest.raises(LLMOutputInvalidError, match="Rol de mensaje no compatible"):
        adapter.generate_structured(
            [LLMMessage(role="tool", content="untrusted payload")],
            {"type": "object"},
        )


@patch("thesis.integrations.llm.gemini.genai.Client")
def test_gemini_adapter_empty_or_non_json_output(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    adapter = GeminiProviderAdapter(api_key="fake-secret-key")

    # Caso texto vacío
    mock_response_empty = MagicMock()
    mock_response_empty.text = ""
    mock_client.models.generate_content.return_value = mock_response_empty
    with pytest.raises(LLMOutputInvalidError, match="respuesta vacía"):
        adapter.generate_structured([LLMMessage(role="user", content="test")], {})

    # Caso JSON malformado
    mock_response_bad = MagicMock()
    mock_response_bad.text = "{malformed json:"
    mock_client.models.generate_content.return_value = mock_response_bad
    with pytest.raises(LLMOutputInvalidError, match="no es un JSON válido"):
        adapter.generate_structured([LLMMessage(role="user", content="test")], {})

    # Caso JSON que no es un objeto/dict
    mock_response_list = MagicMock()
    mock_response_list.text = "[1, 2, 3]"
    mock_client.models.generate_content.return_value = mock_response_list
    with pytest.raises(LLMOutputInvalidError, match="debe ser un objeto JSON"):
        adapter.generate_structured([LLMMessage(role="user", content="test")], {})


@patch("thesis.integrations.llm.gemini.genai.Client")
def test_gemini_adapter_timeout_mapping(mock_client_cls):
    import httpx
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.models.generate_content.side_effect = httpx.ReadTimeout("Timeout from httpx")

    adapter = GeminiProviderAdapter(api_key="fake-secret-key")
    with pytest.raises(LLMProviderTimeoutError, match="Tiempo de espera agotado"):
        adapter.generate_structured([LLMMessage(role="user", content="test")], {})


@patch("thesis.integrations.llm.gemini.genai.Client")
def test_gemini_adapter_rate_limit_mapping(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    err = errors.ClientError(429, {"error": {"message": "Resource exhausted"}})
    mock_client.models.generate_content.side_effect = err

    adapter = GeminiProviderAdapter(api_key="fake-secret-key")
    with pytest.raises(LLMProviderRateLimitError, match="Límite de tasa de Gemini alcanzado"):
        adapter.generate_structured([LLMMessage(role="user", content="test")], {})


@patch("thesis.integrations.llm.gemini.genai.Client")
def test_gemini_adapter_auth_error_mapping(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    err = errors.ClientError(403, {"error": {"message": "Permission denied: invalid API key"}})
    mock_client.models.generate_content.side_effect = err

    adapter = GeminiProviderAdapter(api_key="fake-secret-key")
    with pytest.raises(LLMProviderUnavailableError, match="Credenciales o permisos de Gemini inválidos"):
        adapter.generate_structured([LLMMessage(role="user", content="test")], {})


@patch("thesis.integrations.llm.gemini.genai.Client")
def test_gemini_adapter_server_error_mapping(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    err = errors.ServerError(503, {"error": {"message": "Backend service unavailable"}})
    mock_client.models.generate_content.side_effect = err

    adapter = GeminiProviderAdapter(api_key="fake-secret-key")
    with pytest.raises(LLMProviderUnavailableError, match="no está disponible temporalmente"):
        adapter.generate_structured([LLMMessage(role="user", content="test")], {})


# ==============================================================================
# 2. Pruebas de la Fábrica (Factory) y Guardarraíles de Configuración
# ==============================================================================


def test_factory_default_disabled():
    set_test_adapter_override(None)
    with override_settings(TESISMCP_LLM_PROVIDER="DISABLED"):
        with pytest.raises(LLMProviderUnavailableError, match="deshabilitado por política"):
            get_llm_adapter()


def test_factory_development_mock_restricted_to_debug():
    set_test_adapter_override(None)
    with override_settings(TESISMCP_LLM_PROVIDER="DEVELOPMENT_MOCK", DEBUG=False):
        with pytest.raises(LLMProviderUnavailableError, match="solo está permitido en modo DEBUG"):
            get_llm_adapter()


def test_factory_gemini_requires_api_key(monkeypatch):
    set_test_adapter_override(None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with override_settings(TESISMCP_LLM_PROVIDER="GEMINI"):
        with pytest.raises(LLMProviderUnavailableError, match="falta la variable de entorno GEMINI_API_KEY"):
            get_llm_adapter()


def test_factory_gemini_success(monkeypatch):
    set_test_adapter_override(None)
    monkeypatch.setenv("GEMINI_API_KEY", "real-or-test-secret-key")
    with override_settings(TESISMCP_LLM_PROVIDER="GEMINI", TESISMCP_GEMINI_MODEL="gemini-3.8-flash"):
        adapter = get_llm_adapter()
        assert isinstance(adapter, GeminiProviderAdapter)
        assert adapter.model == "gemini-3.8-flash"


# ==============================================================================
# 3. Flujo Integrado con AIGenerationJob y Aceptación Canónica
# ==============================================================================


@pytest.mark.django_db
@patch("thesis.integrations.llm.gemini.genai.Client")
def test_gemini_job_flow_creates_pending_proposal_without_modifying_canonical_content(
    mock_client_cls, monkeypatch
):
    set_test_adapter_override(None)
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-api-key")

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    # Salida válida para P01
    p01_payload = {
        "temas_propuestos": [
            {
                "id": i,
                "titulo_tentativo": f"Implementación de arquitectura de software para análisis de datos {i}",
                "pros": ["Alto impacto"],
                "contras": ["Complejidad"],
                "viabilidad_preliminar": "ALTA",
            }
            for i in range(1, 6)
        ],
        "tema_preseleccionado_id": 1,
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(p01_payload)
    mock_response.usage_metadata = _make_dummy_usage(150, 90, 240)
    mock_client.models.generate_content.return_value = mock_response

    user = User.objects.create(email="gemini_tesista@example.com", is_active=True)
    project = create_project(user, "Proyecto Gemini B5.1")

    # Activar recorrido publicado en el proyecto
    get_workflow_state(user, project.id)
    create_or_update_draft(user, project.id, {"tasks": []}, expected_version=0)
    publish_workflow_draft(user, project.id, "Activar recorrido inicial", expected_version=1)

    profile = ResearchProfile.objects.get(project=project)
    start_lock_version = profile.lock_version

    # Iniciar generación configurando GEMINI
    with override_settings(TESISMCP_LLM_PROVIDER="GEMINI", TESISMCP_GEMINI_MODEL="gemini-3.8-flash"):
        job_data = request_task_generation(
            actor=user,
            project_id=project.id,
            task_id="P01",
            idempotency_key=str(uuid.uuid4()),
            expected_state_version=start_lock_version,
        )
        assert job_data["status"] == "QUEUED"
        assert job_data["acceptance_status"] == "PENDING_ACCEPTANCE"

        # Procesar con el worker
        job = process_ai_generation_job(job_data["job_id"])
        assert job.status == AIGenerationJob.Status.SUCCEEDED
        assert job.acceptance_status == AIGenerationJob.AcceptanceStatus.PENDING_ACCEPTANCE
        assert job.provider == "GEMINI"
        assert job.model == "gemini-3.8-flash"
        assert job.usage_data == {
            "prompt_token_count": 150,
            "candidates_token_count": 90,
            "total_token_count": 240,
        }

        # Comprobar que NO ha modificado el manuscrito ni creado revisiones canónicas antes de aceptación
        assert ChapterRevision.objects.filter(chapter__project=project).count() == 0
        progress = StepProgress.objects.filter(project=project, step_code="P01").first()
        assert progress is None or progress.status != StepProgress.Status.COMPLETED

        # Aceptar explícitamente la propuesta
        accept_res = accept_ai_proposal(
            actor=user,
            project_id=project.id,
            job_id=job.id,
            expected_state_version=start_lock_version,
            decision_key=str(uuid.uuid4()),
        )
        assert accept_res["acceptance_status"] == "ACCEPTED"
        assert accept_res["result_revision_id"] is not None

        # Ahora sí existe la revisión canónica
        assert ChapterRevision.objects.filter(chapter__project=project).count() == 1
        rev = ChapterRevision.objects.filter(chapter__project=project).first()
        assert rev.step_code == "P01"
