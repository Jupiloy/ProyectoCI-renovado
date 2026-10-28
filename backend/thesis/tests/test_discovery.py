from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from thesis.integrations.semantic_scholar import search_papers
from thesis.services.discovery import search_semantic_scholar
from thesis.services.errors import DomainError
from thesis.services.projects import create_project


def test_semantic_scholar_results_are_metadata_only():
    payload = {"data": [{
        "paperId": "paper-1", "title": "Artículo de prueba", "year": 2024,
        "authors": [{"name": "Autora"}], "url": "https://example.org/record",
        "externalIds": {"DOI": "10.1234/test"},
        "openAccessPdf": {"url": "https://example.org/test.pdf"},
    }]}
    from unittest.mock import MagicMock
    response = MagicMock()
    response.__enter__.return_value = response
    with patch("thesis.integrations.semantic_scholar.urlopen", return_value=response), \
         patch("thesis.integrations.semantic_scholar.json.load", return_value=payload):
        papers = search_papers("consulta de prueba")
    assert papers[0]["title"] == "Artículo de prueba"
    assert papers[0]["verification_level"] == "METADATA_ONLY"
    assert papers[0]["full_text_inspected"] is False


@pytest.mark.django_db
def test_semantic_scholar_search_requires_project_access():
    users = get_user_model().objects
    owner = users.create_user(email="discovery-owner@example.org", password="pass")
    other = users.create_user(email="discovery-other@example.org", password="pass")
    project = create_project(owner, "Prueba")
    with patch("thesis.services.discovery.search_papers", return_value=[]) as provider:
        result = search_semantic_scholar(owner, project.id, "investigación educativa")
    provider.assert_called_once()
    assert result["full_text_inspected"] is False
    with pytest.raises(DomainError) as denied:
        search_semantic_scholar(other, project.id, "investigación educativa")
    assert denied.value.code == "NOT_FOUND"
