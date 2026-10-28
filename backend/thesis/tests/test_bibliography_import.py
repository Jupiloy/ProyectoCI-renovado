import hashlib

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone

from thesis.integrations.bibliography_import import parse_bibliography
from thesis.models import SearchExecutionSource, SourceDocument
from thesis.services.bibliography import import_bibliography
from thesis.services.errors import DomainError
from thesis.services.projects import create_project
from thesis.services.search_strategies import create_search_strategy, record_manual_search_execution


RIS = b"""TY  - JOUR
TI  - A review of academic writing
AU  - Maria Garcia
AU  - Li, Wei
PY  - 2023
DO  - https://doi.org/10.1234/review
JO  - Journal of Examples
AB  - A useful abstract.
ER  -
"""

BIBTEX = b"""@article{garcia2024,
  title = {A {Nested} Title},
  author = {Maria Garcia and Li, Wei},
  year = {2024},
  doi = {10.1234/nested},
  journal = {Example Journal}
}
"""

CSV = b"titulo,autores,a\xc3\xb1o,doi,link\nA title,Garcia; Wei,2022,10.1234/csv,https://example.org/item\n"


@pytest.mark.parametrize(("content", "file_format", "expected_title", "expected_authors", "expected_year"), [
    (RIS, "ris", "A review of academic writing", ["Maria Garcia", "Li, Wei"], 2023),
    (BIBTEX, "bib", "A Nested Title", ["Maria Garcia", "Li, Wei"], 2024),
    (CSV, "csv", "A title", ["Garcia", "Wei"], 2022),
])
def test_supported_bibliography_formats_normalize_metadata(content, file_format, expected_title, expected_authors, expected_year):
    [record] = parse_bibliography(content, file_format)
    assert record["title"] == expected_title
    assert record["authors"] == expected_authors
    assert record["year"] == expected_year
    assert record["doi"]


def test_parser_rejects_invalid_encoding_format_and_oversized_file():
    for content, file_format in [(b"\xff", "ris"), (b"anything", "pdf"), (b"x" * (5 * 1024 * 1024 + 1), "csv")]:
        with pytest.raises(DomainError) as error:
            parse_bibliography(content, file_format)
        assert error.value.code == "VALIDATION_ERROR"


@pytest.mark.django_db
def test_import_persists_provenance_and_reports_possible_duplicates():
    owner = get_user_model().objects.create_user(email="bib-owner@example.org", password="pass")
    project = create_project(owner, "Importación bibliográfica")
    first = SimpleUploadedFile("export.ris", RIS, content_type="application/x-research-info-systems")
    imported = import_bibliography(owner, project.id, first, "SCOPUS")
    assert imported["records_created"] == 1
    assert imported["provider"] == SourceDocument.RecordProvider.SCOPUS
    source = SourceDocument.objects.get(pk=imported["results"][0]["source_id"])
    assert source.imported_by_id == owner.id
    assert source.imported_file_sha256 == hashlib.sha256(RIS).hexdigest()
    assert source.metadata_origin == SourceDocument.MetadataOrigin.USER_FILE_IMPORT
    assert source.provider_record_id == f"{imported['file_sha256']}:1"
    assert source.verification_status == SourceDocument.Status.UNVERIFIED_METADATA

    second = SimpleUploadedFile("again.ris", RIS, content_type="application/x-research-info-systems")
    repeated = import_bibliography(owner, project.id, second, "SCOPUS")
    assert repeated["records_already_imported"] == 1
    assert repeated["results"][0]["possible_duplicates"] == []
    assert SourceDocument.objects.filter(project=project).count() == 1


@pytest.mark.django_db
def test_import_is_project_scoped_and_returns_cross_provider_duplicate_candidate():
    owner = get_user_model().objects.create_user(email="bib-owner2@example.org", password="pass")
    outsider = get_user_model().objects.create_user(email="bib-outsider@example.org", password="pass")
    project = create_project(owner, "Bibliografía")
    SourceDocument.objects.create(
        project=project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.ALICIA, provider_record_id="alicia-44",
        title="A review of academic writing", doi="10.1234/review", authors_json=[],
    )
    result = import_bibliography(owner, project.id, SimpleUploadedFile("export.ris", RIS), "WOS")
    imported = result["results"][0]
    assert imported["created"] is True
    assert imported["possible_duplicates"][0]["match"] == "DOI_AND_TITLE"
    with pytest.raises(DomainError) as denied:
        import_bibliography(outsider, project.id, SimpleUploadedFile("export.ris", RIS), "WOS")
    assert denied.value.code == "NOT_FOUND"


@pytest.mark.django_db
def test_bibliography_and_peru_discovery_http_contracts():
    owner = get_user_model().objects.create_user(email="bib-http@example.org", password="pass")
    project = create_project(owner, "Búsqueda web")
    project.profile.place = "Piura"
    project.profile.save(update_fields=["place"])
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)
    client.get("/api/v1/docs")
    csrf = client.cookies["csrftoken"].value
    response = client.post(
        f"/api/v1/projects/{project.id}/sources/import-bibliography",
        {"provider": "SCOPUS", "file": SimpleUploadedFile("export.ris", RIS)},
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert response.status_code == 200, response.content
    assert response.json()["records_created"] == 1
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr("thesis.services.discovery_peru.search_alicia_theses", lambda *args, **kwargs: [])
        monkeypatch.setattr("thesis.services.discovery_peru.search_peru_affiliated_articles", lambda *args, **kwargs: [])
        result = client.get(f"/api/v1/projects/{project.id}/discovery/peru?query=tesis")
    assert result.status_code == 200, result.content
    assert result.json()["verification_level"] == "METADATA_ONLY"


@pytest.mark.django_db
def test_import_can_link_each_record_to_exact_manual_search_execution_idempotently():
    owner = get_user_model().objects.create_user(email="bib-execution@example.org", password="pass")
    project = create_project(owner, "Importación vinculada")
    strategy = create_search_strategy(owner, project.id, {
        "provider": "SCOPUS", "title": "Estrategia de prueba", "topic": "Búsqueda de trabajos", 
        "query_text": "academic writing", "idempotency_key": "123e4567-e89b-42d3-a456-426614174000",
    })
    execution = record_manual_search_execution(
        owner, project.id, strategy["strategy_id"], timezone.localdate(), 1, "Consulta manual",
        "123e4567-e89b-42d3-a456-426614174001",
    )
    uploaded = SimpleUploadedFile("export.ris", RIS)
    result = import_bibliography(owner, project.id, uploaded, "SCOPUS", execution["execution_id"])
    assert result["search_execution_id"] == execution["execution_id"]
    assert result["sources_linked_to_execution"] == 1
    link = SearchExecutionSource.objects.get(execution_id=execution["execution_id"])
    assert str(link.source_id) == result["results"][0]["source_id"]
    assert link.link_kind == SearchExecutionSource.LinkKind.BIBLIOGRAPHY_IMPORT
    assert link.imported_file_sha256 == hashlib.sha256(RIS).hexdigest()

    repeat = import_bibliography(owner, project.id, SimpleUploadedFile("again.ris", RIS), "SCOPUS",
                                 execution["execution_id"])
    assert repeat["records_created"] == 0
    assert repeat["records_already_imported"] == 1
    assert repeat["sources_linked_to_execution"] == 0
    assert SearchExecutionSource.objects.filter(execution_id=execution["execution_id"]).count() == 1


@pytest.mark.django_db
def test_import_rejects_execution_from_another_project():
    owner = get_user_model().objects.create_user(email="bib-other-project@example.org", password="pass")
    project_a = create_project(owner, "Proyecto A")
    project_b = create_project(owner, "Proyecto B")
    strategy = create_search_strategy(owner, project_a.id, {
        "provider": "SCOPUS", "title": "Estrategia", "topic": "Tema de búsqueda", 
        "query_text": "research methods", "idempotency_key": "123e4567-e89b-42d3-a456-426614174002",
    })
    execution = record_manual_search_execution(
        owner, project_a.id, strategy["strategy_id"], timezone.localdate(), None, "",
        "123e4567-e89b-42d3-a456-426614174003",
    )
    with pytest.raises(DomainError) as not_found:
        import_bibliography(owner, project_b.id, SimpleUploadedFile("export.ris", RIS), "SCOPUS",
                            execution["execution_id"])
    assert not_found.value.code == "NOT_FOUND"


@pytest.mark.django_db
def test_bibliography_http_form_can_link_import_to_execution():
    owner = get_user_model().objects.create_user(email="bib-execution-http@example.org", password="pass")
    project = create_project(owner, "Importación enlazada por API")
    strategy = create_search_strategy(owner, project.id, {
        "provider": "WEB_OF_SCIENCE", "title": "Consulta WoS", "topic": "Tema de investigación",
        "query_text": "academic writing", "idempotency_key": "123e4567-e89b-42d3-a456-426614174004",
    })
    execution = record_manual_search_execution(
        owner, project.id, strategy["strategy_id"], timezone.localdate(), 1, "",
        "123e4567-e89b-42d3-a456-426614174005",
    )
    client = Client(enforce_csrf_checks=True)
    client.force_login(owner)
    client.get("/api/v1/docs")
    csrf = client.cookies["csrftoken"].value
    response = client.post(
        f"/api/v1/projects/{project.id}/sources/import-bibliography",
        {"provider": "WOS", "execution_id": execution["execution_id"],
         "file": SimpleUploadedFile("export.ris", RIS)},
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert response.status_code == 200, response.content
    assert response.json()["search_execution_id"] == execution["execution_id"]
    assert response.json()["sources_linked_to_execution"] == 1
