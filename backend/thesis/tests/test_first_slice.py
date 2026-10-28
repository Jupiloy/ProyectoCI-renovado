import json
import asyncio
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from thesis.integrations.openalex import search_works
from thesis.services.errors import DomainError
from thesis.services.exploration import explore_idea
from thesis.services.mcp_auth import actor_from_token, issue_token
from thesis.services.projects import create_project, get_project_state, register_idea


@pytest.fixture
def users(db):
    model = get_user_model()
    return (
        model.objects.create_user(email="ana@example.org", password="strong-pass", display_name="Ana"),
        model.objects.create_user(email="otra@example.org", password="strong-pass", display_name="Otra"),
    )


def test_project_isolation_and_version_conflict(users):
    ana, other = users
    project = create_project(ana, "Tesis de Ana", "Título provisional")
    state = register_idea(ana, project.id, "Dificultades para usar herramientas digitales", 0)
    assert state["idea_provisional"] == "Dificultades para usar herramientas digitales"
    assert state["state_version"] == 1
    with pytest.raises(DomainError, match="Proyecto no encontrado"):
        get_project_state(other, project.id)
    with pytest.raises(DomainError) as conflict:
        register_idea(ana, project.id, "Otra idea", 0)
    assert conflict.value.code == "VERSION_CONFLICT"
    assert get_project_state(ana, project.id)["idea_provisional"] == state["idea_provisional"]


def test_exploration_marks_metadata_and_handles_missing_idea(users):
    ana, _ = users
    project = create_project(ana, "Tesis de Ana")
    assert project.title == "Título por definir"
    assert explore_idea(ana, project.id)["search_status"] == "NEEDS_IDEA"
    register_idea(ana, project.id, "Uso de herramientas digitales en colegios", 0)
    observed = []

    def fake_search(query):
        observed.append(query)
        return [{"title": "Trabajo registrado", "verification_level": "METADATA_ONLY", "full_text_inspected": False}]

    result = explore_idea(ana, project.id, search_provider=fake_search)
    assert observed == ["Uso de herramientas digitales en colegios"]
    assert result["works"][0]["full_text_inspected"] is False


def test_mcp_token_is_bound_to_user_and_revocable(users):
    ana, _ = users
    token = issue_token(ana)
    assert actor_from_token(token) == ana
    with pytest.raises(DomainError) as error:
        actor_from_token("wrong-token")
    assert error.value.code == "UNAUTHENTICATED"
    from thesis.models import McpAccessToken
    from django.utils import timezone

    McpAccessToken.objects.update(revoked_at=timezone.now())
    with pytest.raises(DomainError):
        actor_from_token(token)


def test_openalex_results_do_not_claim_full_text():
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return json.dumps({"results": [{
                "id": "https://openalex.org/Wexample",
                "title": "Ejemplo de metadatos",
                "authorships": [{"author": {"display_name": "Persona"}}],
                "publication_year": None,
                "best_oa_location": {"pdf_url": "https://example.org/file.pdf"},
            }]}).encode()

    with patch("thesis.integrations.openalex.urlopen", return_value=Response()):
        works = search_works("idea provisional")
    assert works[0]["verification_level"] == "METADATA_ONLY"
    assert works[0]["full_text_inspected"] is False
    assert works[0]["pdf_url"] == "https://example.org/file.pdf"


def test_api_requires_session_and_csrf(users):
    ana, _ = users
    client = Client(enforce_csrf_checks=True)
    unauthenticated = client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert unauthenticated.status_code == 401
    client.force_login(ana)
    missing_csrf = client.post("/api/v1/projects", data=json.dumps({"name": "Tesis", "title": "Provisional"}), content_type="application/json")
    assert missing_csrf.status_code == 403
    docs_response = client.get("/api/v1/docs")
    assert docs_response.status_code == 200
    csrf_token = client.cookies["csrftoken"].value
    created = client.post(
        "/api/v1/projects",
        data=json.dumps({"name": "Tesis", "title": "Provisional"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert created.status_code == 200
    assert created.json()["name"] == "Tesis"


@pytest.mark.django_db(transaction=True)
def test_mcp_uses_token_identity_and_shared_services(monkeypatch):
    from mcp_server.server import app

    ana = get_user_model().objects.create_user(
        email="mcp-ana@example.org", password="strong-pass", display_name="Ana MCP",
    )
    monkeypatch.setenv("TESISMCP_MCP_TOKEN", issue_token(ana))

    async def journey():
        created = await app.call_tool("crear_proyecto", {"name": "Proyecto MCP", "title": "Título provisional"})
        project_id = created.structured_content["project_id"]
        saved = await app.call_tool("registrar_idea", {
            "project_id": project_id,
            "description": "Dificultades de acceso a herramientas digitales",
            "expected_version": 0,
        })
        state = await app.call_tool("obtener_estado", {"project_id": project_id})
        return saved.structured_content, state.structured_content

    saved, state = asyncio.run(journey())
    assert saved["state_version"] == 1
    assert state["idea_provisional"] == "Dificultades de acceso a herramientas digitales"
