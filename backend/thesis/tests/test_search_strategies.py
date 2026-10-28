from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.test import Client
from django.utils import timezone

from thesis.models import SearchExecution, SearchStrategy
from thesis.services.errors import DomainError
from thesis.services.projects import create_project
from thesis.services.search_strategies import (
    create_search_strategy,
    get_search_strategy_history,
    list_manual_search_executions,
    list_search_strategies,
    record_manual_search_execution,
    revise_search_strategy,
)


@pytest.fixture
def search_context(db):
    users = get_user_model().objects
    owner = users.create_user(email="search-strategy-owner@example.org", password="pass")
    outsider = users.create_user(email="search-strategy-outsider@example.org", password="pass")
    project = create_project(owner, "Búsqueda reproducible")
    return owner, outsider, project


def strategy_payload(**overrides):
    payload = {
        "provider": "SCOPUS",
        "title": "Sistemas de apoyo a tesis",
        "topic": "Asistentes digitales para metodología de investigación",
        "query_text": "thesis assistant research methodology",
        "search_equation": '("thesis" OR "research project") AND ("assistant" OR "methodology")',
        "concepts": ["thesis", "research assistant", "metodología"],
        "filters": {"year_from": 2020, "document_type": ["article", "conference paper"]},
        "search_url": "https://www.scopus.com/",
        "idempotency_key": str(uuid4()),
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_strategy_create_revise_history_and_stale_version_conflict(search_context):
    owner, _, project = search_context
    first_payload = strategy_payload()
    first = create_search_strategy(owner, project.id, first_payload)
    repeated = create_search_strategy(owner, project.id, first_payload)
    assert repeated["strategy_id"] == first["strategy_id"]
    assert first["version_no"] == 1

    edited = strategy_payload(
        title="Revisión de sistemas de apoyo a tesis",
        topic="Asistentes digitales y metodología académica",
        idempotency_key=str(uuid4()),
    )
    second = revise_search_strategy(owner, project.id, first["strategy_id"], 1, edited)
    assert second["version_no"] == 2
    assert second["supersedes_strategy_id"] == first["strategy_id"]
    assert len(get_search_strategy_history(owner, project.id, first["strategy_id"])) == 2
    assert len(list_search_strategies(owner, project.id)) == 1
    assert list_search_strategies(owner, project.id)[0]["version_no"] == 2

    with pytest.raises(DomainError) as stale:
        revise_search_strategy(owner, project.id, first["strategy_id"], 1,
                               strategy_payload(idempotency_key=str(uuid4())))
    assert stale.value.code == "VERSION_CONFLICT"


@pytest.mark.django_db
def test_manual_execution_is_user_declared_idempotent_and_bound_to_exact_version(search_context):
    owner, _, project = search_context
    strategy = create_search_strategy(owner, project.id, strategy_payload())
    key = uuid4()
    execution_date = timezone.localdate() - timedelta(days=2)
    result = record_manual_search_execution(owner, project.id, strategy["strategy_id"],
                                            execution_date, 42, "Exporté RIS", key)
    repeated = record_manual_search_execution(owner, project.id, strategy["strategy_id"],
                                              execution_date, 42, "Exporté RIS", key)
    assert repeated["execution_id"] == result["execution_id"]
    assert result["execution_mode"] == "MANUAL_USER_DECLARED"
    assert result["strategy_version_no"] == 1
    assert result["reported_result_count"] == 42
    assert len(list_manual_search_executions(owner, project.id, strategy["strategy_id"])) == 1
    assert SearchExecution.objects.get(pk=result["execution_id"]).executed_by_id == owner.id


@pytest.mark.django_db
def test_strategy_access_url_validation_and_immutable_history(search_context):
    owner, outsider, project = search_context
    with pytest.raises(DomainError) as bad_url:
        create_search_strategy(owner, project.id, strategy_payload(search_url="https://evil.example/login"))
    assert bad_url.value.code == "VALIDATION_ERROR"

    strategy = create_search_strategy(owner, project.id, strategy_payload())
    with pytest.raises(DomainError) as denied:
        get_search_strategy_history(outsider, project.id, strategy["strategy_id"])
    assert denied.value.code == "NOT_FOUND"

    with pytest.raises(DatabaseError):
        with transaction.atomic():
            SearchStrategy.objects.filter(pk=strategy["strategy_id"]).update(title="alterado directamente")
    execution = record_manual_search_execution(owner, project.id, strategy["strategy_id"],
                                               timezone.localdate(), None, "", uuid4())
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            SearchExecution.objects.filter(pk=execution["execution_id"]).delete()


@pytest.mark.django_db
def test_search_strategy_http_contract_and_permissions(search_context):
    owner, outsider, project = search_context
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)
    client.get("/api/v1/docs")
    csrf = client.cookies["csrftoken"].value
    payload = strategy_payload()
    response = client.post(f"/api/v1/projects/{project.id}/search-strategies", payload,
                          content_type="application/json", HTTP_X_CSRFTOKEN=csrf)
    assert response.status_code == 201, response.content
    strategy_id = response.json()["strategy_id"]
    execution_response = client.post(
        f"/api/v1/projects/{project.id}/search-strategies/{strategy_id}/executions/manual",
        {"execution_date": timezone.localdate().isoformat(), "reported_result_count": 12,
         "notes": "Consulta realizada por el tesista", "idempotency_key": str(uuid4())},
        content_type="application/json", HTTP_X_CSRFTOKEN=csrf,
    )
    assert execution_response.status_code == 201, execution_response.content
    assert execution_response.json()["execution_mode"] == "MANUAL_USER_DECLARED"
    client.force_login(outsider)
    assert client.get(f"/api/v1/projects/{project.id}/search-strategies").status_code == 404
