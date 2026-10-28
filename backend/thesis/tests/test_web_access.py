"""Contrato web de sesión y selección de proyectos, con permisos reales."""

import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from thesis.models import Project, ProjectParticipant
from thesis.services.projects import create_project
from thesis.services.reviews import assign_advisor


pytestmark = pytest.mark.django_db


@pytest.fixture
def accounts():
    model = get_user_model()
    owner = model.objects.create_user(
        email="web-owner@example.org", password="local-test-password", display_name="Tesista",
    )
    other = model.objects.create_user(email="web-other@example.org", display_name="Otro tesista")
    empty = model.objects.create_user(email="web-empty@example.org", display_name="Sin proyectos")
    return owner, other, empty


def test_project_list_requires_a_session():
    assert Client().get("/api/v1/projects").status_code == 401


def test_project_list_filters_membership_and_returns_role_per_project(accounts):
    owner, other, _ = accounts
    owned = create_project(owner, "A - propio")
    advised = create_project(other, "B - asesorado")
    assign_advisor(other, advised.id, owner.email)
    hidden = create_project(other, "C - ajeno")
    archived = create_project(owner, "D - archivado")
    Project.objects.filter(pk=archived.pk).update(status=Project.Status.ARCHIVED)
    revoked = create_project(owner, "E - membresía inactiva")
    ProjectParticipant.objects.filter(project=revoked, user=owner).update(
        active=False, left_at=timezone.now(),
    )
    client = Client()
    client.force_login(owner)

    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["offset"] == 0 and data["limit"] == 50 and data["has_more"] is False
    assert [item["project_id"] for item in data["projects"]] == [str(owned.id), str(advised.id)]
    assert data["projects"][0]["role"] == "OWNER"
    assert data["projects"][0]["permissions"] == {
        "can_read_project": True, "can_edit_document": True,
        "can_manage_workflow": True, "can_review_chapters": False,
    }
    assert data["projects"][1]["role"] == "ADVISOR"
    assert data["projects"][1]["permissions"] == {
        "can_read_project": True, "can_edit_document": False,
        "can_manage_workflow": False, "can_review_chapters": True,
    }
    for excluded in (hidden, archived, revoked):
        assert str(excluded.id) not in response.content.decode()
        assert excluded.name not in response.content.decode()
    assert client.get(f"/api/v1/projects/{hidden.id}").status_code == 404
    assert client.put(
        f"/api/v1/projects/{advised.id}/workflow/draft",
        data=json.dumps({"tasks": [], "expected_version": 0}), content_type="application/json",
    ).status_code == 404


def test_project_list_is_empty_without_memberships(accounts):
    _, other, empty = accounts
    create_project(other, "Proyecto ajeno")
    client = Client()
    client.force_login(empty)
    assert client.get("/api/v1/projects").json() == {
        "projects": [], "offset": 0, "limit": 50, "has_more": False,
    }


def test_project_list_pagination_is_stable(accounts):
    owner, _, _ = accounts
    created = [create_project(owner, name) for name in ("C", "A", "B")]
    client = Client()
    client.force_login(owner)
    observed = []
    for offset in range(3):
        response = client.get("/api/v1/projects", {"offset": offset, "limit": 1})
        assert response.status_code == 200
        page = response.json()
        assert page["offset"] == offset and page["limit"] == 1
        assert page["has_more"] is (offset < 2)
        observed.extend(page["projects"])
    assert [item["name"] for item in observed] == ["A", "B", "C"]
    assert {item["project_id"] for item in observed} == {str(item.id) for item in created}
    assert client.get("/api/v1/projects", {"offset": 3, "limit": 1}).json()["projects"] == []


@pytest.mark.parametrize("params", [{"offset": -1}, {"limit": 0}, {"limit": 101}])
def test_project_list_rejects_invalid_pagination(accounts, params):
    client = Client()
    client.force_login(accounts[0])
    response = client.get("/api/v1/projects", params)
    assert response.status_code == 400
    assert "VALIDATION_ERROR" in response.json()["detail"]


def test_revoked_membership_cannot_use_previously_advertised_permissions(accounts):
    owner, _, _ = accounts
    project = create_project(owner, "Proyecto a revocar")
    client = Client()
    client.force_login(owner)
    assert client.get("/api/v1/projects").json()["projects"][0]["permissions"]["can_read_project"] is True
    ProjectParticipant.objects.filter(project=project, user=owner).update(active=False, left_at=timezone.now())
    assert client.get("/api/v1/projects").json()["projects"] == []
    assert client.get(f"/api/v1/projects/{project.id}").status_code == 404


def test_real_web_session_login_create_and_logout_with_csrf(accounts):
    owner, _, _ = accounts
    client = Client(enforce_csrf_checks=True)
    session = client.get("/api/v1/auth/session/")
    assert session.status_code == 200
    assert session.json()["authenticated"] is False and session.json()["user"] is None
    initial_token = session.json()["csrf_token"]
    initial_cookie = client.cookies["csrftoken"].value
    payload = {"email": owner.email.upper(), "password": "local-test-password"}
    assert client.post("/api/v1/auth/login/", data=json.dumps(payload), content_type="application/json").status_code == 403
    wrong = client.post(
        "/api/v1/auth/login/", data=json.dumps({**payload, "password": "incorrecta"}),
        content_type="application/json", HTTP_X_CSRFTOKEN=initial_token,
    )
    assert wrong.status_code == 401
    login = client.post(
        "/api/v1/auth/login/", data=json.dumps(payload), content_type="application/json",
        HTTP_X_CSRFTOKEN=initial_token,
    )
    assert login.status_code == 200
    assert login.json()["authenticated"] is True
    assert login.json()["user"] == {"id": str(owner.pk), "email": owner.email, "display_name": owner.display_name}
    assert client.cookies["csrftoken"].value != initial_cookie
    token = login.json()["csrf_token"]
    assert client.get("/api/v1/auth/session/").json()["authenticated"] is True
    created = client.post(
        "/api/v1/projects", data=json.dumps({"name": "Creado desde la web", "title": "Título provisional"}),
        content_type="application/json", HTTP_X_CSRFTOKEN=token,
    )
    assert created.status_code == 200
    listed = client.get("/api/v1/projects").json()["projects"]
    assert listed[0]["project_id"] == created.json()["project_id"] and listed[0]["role"] == "OWNER"
    assert client.post("/api/v1/auth/logout/").status_code == 403
    assert client.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=token).status_code == 200
    assert client.get("/api/v1/projects").status_code == 401
    assert client.get("/api/v1/auth/session/").json()["user"] is None
