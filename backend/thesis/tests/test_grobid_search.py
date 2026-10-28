import hashlib
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from thesis.integrations.grobid import parse_tei
from thesis.models import SourceDocument, SourceExcerpt, SourceGrobidAnalysis, SourcePassage
from thesis.services.errors import DomainError
from thesis.services.grobid import analyze_source_grobid, get_source_grobid
from thesis.services.projects import create_project
from thesis.services.search import index_source_passages, search_passages


TEI = b'''<TEI xmlns="http://www.tei-c.org/ns/1.0">
<teiHeader><fileDesc><titleStmt><title>Extracted study</title>
 </titleStmt><sourceDesc><biblStruct><analytic>
<author><persName><forename>Ana</forename><surname>Test</surname></persName></author>
</analytic></biblStruct></sourceDesc></fileDesc></teiHeader>
<text><back><listBibl><biblStruct xml:id="b1"><analytic><title>Reference title</title>
<author><persName><forename>Juan</forename><surname>Sample</surname></persName></author>
</analytic><idno type="DOI">10.1234/example</idno></biblStruct></listBibl></back></text>
</TEI>'''


@pytest.fixture
def context(db, tmp_path):
    user = get_user_model().objects.create_user(email="analysis@example.org", password="pass", display_name="Ana")
    other = get_user_model().objects.create_user(email="other-analysis@example.org", password="pass", display_name="Otra")
    project = create_project(user, "Análisis")
    content = b"%PDF-synthetic-source"
    folder = tmp_path / "sources" / str(project.id)
    folder.mkdir(parents=True)
    (folder / "source.pdf").write_bytes(content)
    source = SourceDocument.objects.create(
        project=project, kind=SourceDocument.Kind.UPLOAD, title="Etiqueta de prueba",
        authors_json=[], storage_key=f"sources/{project.id}/source.pdf",
        sha256=hashlib.sha256(content).hexdigest(), mime_type="application/pdf",
        page_count=2, verification_status=SourceDocument.Status.TEXT_CHECKED,
        extraction_method=SourceDocument.ExtractionMethod.POPPLER,
    )
    text = "La investigación usa evidencias documentales sobre educación. " * 18
    SourceExcerpt.objects.create(source=source, chunk_no=1, page_no=2,
                                 text=text, text_sha256=hashlib.sha256(text.encode()).hexdigest())
    return user, other, project, source, tmp_path


def test_grobid_keeps_machine_metadata_separate(context):
    user, other, project, source, root = context
    with override_settings(MEDIA_ROOT=root), patch("thesis.services.grobid.process_fulltext", return_value=TEI) as client:
        result = analyze_source_grobid(user, project.id, source.id)
        again = analyze_source_grobid(user, project.id, source.id)
    assert result["analysis_status"] == "ANALYZED"
    assert again["analysis_status"] == "ALREADY_ANALYZED"
    client.assert_called_once()
    assert result["extracted_title"] == "Extracted study"
    assert result["extracted_authors"] == ["Ana Test"]
    assert result["references"][0]["doi"] == "10.1234/example"
    assert result["cover_metadata_verified"] is False
    assert SourceDocument.objects.get(pk=source.pk).title == "Etiqueta de prueba"
    assert SourceGrobidAnalysis.objects.get(source=source).tei_sha256 == hashlib.sha256(TEI).hexdigest()
    with pytest.raises(DomainError) as denied:
        get_source_grobid(other, project.id, source.id)
    assert denied.value.code == "NOT_FOUND"


def test_pgvector_search_keeps_physical_page_and_project_scope(context):
    user, other, project, source, _ = context
    def vectors(texts):
        return [[1.0 if "educación" in text else 0.0, 0.0 if "educación" in text else 1.0] + [0.0] * 382 for text in texts]

    with patch("thesis.services.search.embed_texts", side_effect=vectors):
        indexed = index_source_passages(user, project.id, source.id)
        result = search_passages(user, project.id, "educación", limit=2)
        again = index_source_passages(user, project.id, source.id)
    assert indexed["indexed_passages"] >= 1
    assert indexed["indexed_passages"] == again["indexed_passages"]
    assert SourcePassage.objects.filter(excerpt__source=source).count() == indexed["indexed_passages"]
    assert result["results"][0]["physical_page"] == 2
    assert result["results"][0]["supports_claim_verified"] is False
    with pytest.raises(DomainError) as denied:
        search_passages(other, project.id, "educación")
    assert denied.value.code == "NOT_FOUND"


def test_tei_parser_rejects_non_tei():
    with pytest.raises(DomainError) as error:
        parse_tei(b"<html><title>Not TEI</title></html>")
    assert error.value.code == "GROBID_FAILED"
