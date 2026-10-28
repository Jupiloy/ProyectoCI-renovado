from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.test import Client

from thesis.models import SourceDocument, SourceDuplicateDecision
from thesis.services.errors import DomainError
from thesis.services.projects import create_project
from thesis.services.source_duplicate_decisions import decide_source_duplicate, list_source_duplicate_decisions


@pytest.fixture
def duplicate_context(db):
    owner = get_user_model().objects.create_user(email="duplicate-owner@example.org", password="pass")
    outsider = get_user_model().objects.create_user(email="duplicate-outsider@example.org", password="pass")
    project = create_project(owner, "Decisiones de duplicados")
    source_a = SourceDocument.objects.create(
        project=project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.ALICIA, provider_record_id="alicia-duplicate-a",
        title="Análisis de sistemas académicos", doi="10.1234/shared", authors_json=[],
    )
    source_b = SourceDocument.objects.create(
        project=project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.OPENALEX, provider_record_id="W1234567890",
        openalex_id="https://openalex.org/W1234567890", title="Analisis de sistemas academicos",
        doi="10.1234/shared", authors_json=[],
    )
    return owner, outsider, project, source_a, source_b


@pytest.mark.django_db
def test_duplicate_decisions_append_history_without_merging_sources(duplicate_context):
    owner, _, project, source_a, source_b = duplicate_context
    first = decide_source_duplicate(owner, project.id, source_a.id, source_b.id,
                                    "MARK_DUPLICATE", "Coinciden DOI y título", uuid4())
    repeated = decide_source_duplicate(owner, project.id, source_b.id, source_a.id,
                                       "MARK_DUPLICATE", "Coinciden DOI y título", first["idempotency_key"])
    latest = decide_source_duplicate(owner, project.id, source_b.id, source_a.id,
                                     "KEEP_SEPARATE", "Revisión manual: son trabajos distintos", uuid4())
    assert first["decision_no"] == 1 and first["created"] is True
    assert repeated["created"] is False and repeated["decision_id"] == first["decision_id"]
    assert latest["decision_no"] == 2 and latest["is_current"] is True
    assert SourceDuplicateDecision.objects.filter(project=project).count() == 2
    assert SourceDocument.objects.filter(project=project).count() == 2
    history = list_source_duplicate_decisions(owner, project.id)["decisions"]
    assert [row["is_current"] for row in history] == [False, True]
    assert {source_a.id, source_b.id} == set(SourceDocument.objects.filter(project=project).values_list("id", flat=True))


@pytest.mark.django_db
def test_duplicate_decision_requires_owner_and_matching_pair(duplicate_context):
    owner, outsider, project, source_a, source_b = duplicate_context
    with pytest.raises(DomainError) as denied:
        decide_source_duplicate(outsider, project.id, source_a.id, source_b.id,
                                "MARK_DUPLICATE", "", uuid4())
    assert denied.value.code == "NOT_FOUND"
    source_c = SourceDocument.objects.create(
        project=project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.ALICIA, provider_record_id="alicia-unrelated",
        title="Otro tema completamente distinto", authors_json=[],
    )
    with pytest.raises(DomainError) as unrelated:
        decide_source_duplicate(owner, project.id, source_a.id, source_c.id,
                                "MARK_DUPLICATE", "", uuid4())
    assert unrelated.value.code == "VALIDATION_ERROR"
    with pytest.raises(DomainError) as idempotency:
        decide_source_duplicate(owner, project.id, source_a.id, source_b.id,
                                "KEEP_SEPARATE", "", "invalid-uuid")
    assert idempotency.value.code == "VALIDATION_ERROR"


@pytest.mark.django_db
def test_duplicate_decision_http_contract_and_history(duplicate_context):
    owner, outsider, project, source_a, source_b = duplicate_context
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)
    client.get("/api/v1/docs")
    csrf = client.cookies["csrftoken"].value
    payload = {
        "source_id": str(source_a.id), "other_source_id": str(source_b.id),
        "decision": "SET_PRIMARY", "primary_source_id": str(source_a.id),
        "note": "Registro preferido por revisión humana",
        "idempotency_key": str(uuid4()),
    }
    response = client.post(f"/api/v1/projects/{project.id}/sources/duplicate-decisions", payload,
                           content_type="application/json", HTTP_X_CSRFTOKEN=csrf)
    assert response.status_code == 201, response.content
    assert response.json()["decision"] == "SET_PRIMARY"
    assert response.json()["primary_source_id"] == str(source_a.id)
    history = client.get(f"/api/v1/projects/{project.id}/sources/duplicate-decisions")
    assert history.status_code == 200
    assert len(history.json()["decisions"]) == 1
    client.force_login(outsider)
    denied = client.get(f"/api/v1/projects/{project.id}/sources/duplicate-decisions")
    assert denied.status_code == 404


@pytest.mark.django_db
def test_duplicate_decision_history_is_append_only_in_postgres(duplicate_context):
    owner, _, project, source_a, source_b = duplicate_context
    result = decide_source_duplicate(owner, project.id, source_a.id, source_b.id,
                                    "MARK_DUPLICATE", "", uuid4())
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            SourceDuplicateDecision.objects.filter(pk=result["decision_id"]).update(note="edited")
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            SourceDuplicateDecision.objects.filter(pk=result["decision_id"]).delete()


@pytest.mark.django_db
def test_database_rejects_cross_project_duplicate_decision(duplicate_context):
    owner, _, project, source_a, _ = duplicate_context
    other_project = create_project(owner, "Proyecto aislado")
    source_other = SourceDocument.objects.create(
        project=other_project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.ALICIA, provider_record_id="alicia-other-project",
        title=source_a.title, doi=source_a.doi, authors_json=[],
    )
    first, second = sorted([source_a, source_other], key=lambda source: str(source.id))
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            SourceDuplicateDecision.objects.create(
                project=project, source_a=first, source_b=second, decision_no=1,
                decision=SourceDuplicateDecision.Decision.MARK_DUPLICATE,
                created_by=owner, idempotency_key=uuid4(),
            )
