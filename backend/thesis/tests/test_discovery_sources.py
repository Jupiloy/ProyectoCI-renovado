from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.test import Client
from django.utils import timezone

from thesis.models import SearchExecutionSource, SourceDocument
from thesis.services.discovery_sources import select_discovery_candidate
from thesis.services.errors import DomainError
from thesis.services.projects import create_project
from thesis.services.search_strategies import create_search_strategy, record_manual_search_execution


@pytest.fixture
def candidate_context(db):
    users = get_user_model().objects
    owner = users.create_user(email="candidate-owner@example.org", password="pass")
    outsider = users.create_user(email="candidate-outsider@example.org", password="pass")
    project = create_project(owner, "Fuentes seleccionadas")
    return owner, outsider, project


def candidate_payload(**overrides):
    payload = {
        "provider": "SEMANTIC_SCHOLAR",
        "provider_record_id": "paper_123456",
        "title": "A study of research writing",
        "authors": ["Researcher, A."],
        "publication_year": 2024,
        "doi": "10.1234/research-writing",
        "abstract": "Abstract supplied from a discovery result.",
        "publication_venue": "Example Journal",
        "record_url": "https://www.semanticscholar.org/paper/paper_123456",
        "pdf_url": "https://example.org/open-paper.pdf",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_select_candidate_is_idempotent_unverified_and_reports_possible_duplicates(candidate_context):
    owner, _, project = candidate_context
    SourceDocument.objects.create(
        project=project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.ALICIA, provider_record_id="alicia_456",
        title="A study of research writing", doi="10.1234/research-writing", authors_json=[],
        metadata_origin=SourceDocument.MetadataOrigin.USER_FILE_IMPORT,
    )
    first = select_discovery_candidate(owner, project.id, candidate_payload())
    second = select_discovery_candidate(owner, project.id, candidate_payload())
    assert first["created"] is True
    assert second["created"] is False
    assert first["metadata_origin"] == SourceDocument.MetadataOrigin.USER_SELECTED_CANDIDATE
    assert first["verification_level"] == "USER_SUPPLIED_METADATA_UNVERIFIED"
    assert SourceDocument.objects.get(pk=first["source_id"]).verification_status == SourceDocument.Status.UNVERIFIED_METADATA
    assert first["full_text_inspected"] is False
    assert first["possible_duplicates"][0]["match"] == "DOI_AND_TITLE"
    assert SourceDocument.objects.filter(project=project).count() == 2


@pytest.mark.django_db
def test_candidate_link_to_execution_is_project_scoped_and_append_only(candidate_context):
    owner, outsider, project = candidate_context
    strategy = create_search_strategy(owner, project.id, {
        "provider": "OPEN_WEB", "title": "Web abierta", "topic": "Tema", "query_text": "tema de tesis",
        "idempotency_key": str(uuid4()),
    })
    execution = record_manual_search_execution(
        owner, project.id, strategy["strategy_id"], timezone.localdate(),
        None, "", uuid4(),
    )
    payload = candidate_payload(search_execution_id=execution["execution_id"])
    selected = select_discovery_candidate(owner, project.id, payload)
    assert selected["linked_to_execution"] is True
    [link] = SearchExecutionSource.objects.filter(execution_id=execution["execution_id"])
    assert link.link_kind == SearchExecutionSource.LinkKind.DISCOVERY_SELECTION
    assert link.imported_file_sha256 == ""
    with pytest.raises(DomainError) as denied:
        select_discovery_candidate(outsider, project.id, candidate_payload(provider_record_id="paper_other"))
    assert denied.value.code == "NOT_FOUND"
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            SearchExecutionSource.objects.filter(pk=link.pk).delete()


@pytest.mark.django_db
def test_database_rejects_cross_project_execution_source_link(candidate_context):
    owner, _, project = candidate_context
    other_project = create_project(owner, "Otro proyecto")
    strategy = create_search_strategy(owner, project.id, {
        "provider": "OPEN_WEB", "title": "Web abierta", "topic": "Tema", "query_text": "tema de tesis",
        "idempotency_key": str(uuid4()),
    })
    execution = record_manual_search_execution(
        owner, project.id, strategy["strategy_id"], timezone.localdate(), None, "", uuid4(),
    )
    source = SourceDocument.objects.create(
        project=other_project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.ALICIA, provider_record_id="alicia_987",
        title="Fuente de otro proyecto", authors_json=[],
    )
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            SearchExecutionSource.objects.create(
                execution_id=execution["execution_id"], source=source,
                link_kind=SearchExecutionSource.LinkKind.DISCOVERY_SELECTION,
                imported_file_sha256="", created_by=owner,
            )


@pytest.mark.django_db
def test_candidate_rejects_invalid_provider_ids_and_non_https_urls(candidate_context):
    owner, _, project = candidate_context
    with pytest.raises(DomainError) as openalex_id:
        select_discovery_candidate(owner, project.id, candidate_payload(provider="OPENALEX", provider_record_id="evil"))
    assert openalex_id.value.code == "VALIDATION_ERROR"
    with pytest.raises(DomainError) as insecure_url:
        select_discovery_candidate(owner, project.id, candidate_payload(record_url="http://example.org/paper"))
    assert insecure_url.value.code == "VALIDATION_ERROR"


@pytest.mark.django_db
def test_select_discovery_candidate_http_requires_owner(candidate_context):
    owner, outsider, project = candidate_context
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)
    client.get("/api/v1/docs")
    csrf = client.cookies["csrftoken"].value
    strategy = create_search_strategy(owner, project.id, {
        "provider": "OPEN_WEB", "title": "Búsqueda web", "topic": "Tema de prueba",
        "query_text": "research assistant", "idempotency_key": str(uuid4()),
    })
    execution = record_manual_search_execution(
        owner, project.id, strategy["strategy_id"], timezone.localdate(), None, "", uuid4(),
    )
    payload = candidate_payload(search_execution_id=execution["execution_id"])
    response = client.post(
        f"/api/v1/projects/{project.id}/sources/select-discovery", payload,
        content_type="application/json", HTTP_X_CSRFTOKEN=csrf,
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["verification_level"] == "USER_SUPPLIED_METADATA_UNVERIFIED"
    assert body["record_provider"] == "SEMANTIC_SCHOLAR"
    links = client.get(
        f"/api/v1/projects/{project.id}/search-strategies/{strategy['strategy_id']}"
        f"/executions/{execution['execution_id']}/sources"
    )
    assert links.status_code == 200, links.content
    assert links.json()["sources"][0]["link_kind"] == "DISCOVERY_SELECTION"
    client.force_login(outsider)
    denied = client.post(
        f"/api/v1/projects/{project.id}/sources/select-discovery", candidate_payload(provider_record_id="paper_other"),
        content_type="application/json", HTTP_X_CSRFTOKEN=csrf,
    )
    assert denied.status_code == 404
    denied_links = client.get(
        f"/api/v1/projects/{project.id}/search-strategies/{strategy['strategy_id']}"
        f"/executions/{execution['execution_id']}/sources"
    )
    assert denied_links.status_code == 404
