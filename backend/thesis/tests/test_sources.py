import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from thesis.integrations.pdf import extract_pages
from thesis.models import SourceDocument
from thesis.services.errors import DomainError
from thesis.services.projects import create_project
from thesis.services.sources import enqueue_openalex_source, import_openalex_source, list_excerpts, process_source_ocr, upload_pdf_pending
from thesis.services.document_jobs import get_document_job, run_next_document_job


@pytest.fixture
def context(db):
    user = get_user_model().objects.create_user(email="fuentes@example.org", password="test-pass", display_name="Ana")
    other = get_user_model().objects.create_user(email="otra-fuente@example.org", password="test-pass", display_name="Otra")
    return user, other, create_project(user, "Investigación")


def work(pdf_url):
    return {
        "openalex_id": "https://openalex.org/W123", "title": "Ficha sintética de prueba",
        "authors": ["Autora de prueba"], "publication_year": None,
        "doi": None, "landing_page_url": None, "pdf_url": pdf_url,
    }


def test_metadata_only_when_no_pdf_link(context):
    user, other, project = context
    with patch("thesis.services.sources.get_work", return_value=work(None)):
        result = import_openalex_source(user, project.id, "W123")
    assert result["download_status"] == "NO_PDF_LINK"
    assert result["full_text_extracted"] is False
    assert result["physical_page_count"] is None
    with pytest.raises(DomainError) as exc:
        list_excerpts(other, project.id, result["source_id"])
    assert exc.value.code == "NOT_FOUND"


def test_openalex_retracted_work_is_kept_but_not_downloaded(context):
    user, _, project = context
    record = work("https://example.org/file.pdf") | {"openalex_retracted": True}
    with patch("thesis.services.sources.get_work", return_value=record), \
         patch("thesis.services.sources.download_pdf") as download:
        result = import_openalex_source(user, project.id, "W123")
    download.assert_not_called()
    assert result["verification_status"] == "REJECTED"
    assert result["download_status"] == "RETRACTED_IN_OPENALEX"
    assert list_excerpts(user, project.id, result["source_id"])["excerpts"] == []


def test_import_preserves_physical_page_and_hash(context, tmp_path):
    user, _, project = context

    def fake_download(_url, destination):
        destination.write_bytes(b"%PDF-test")
        return hashlib.sha256(destination.read_bytes()).hexdigest()

    with override_settings(MEDIA_ROOT=tmp_path), \
         patch("thesis.services.sources.get_work", return_value=work("https://example.org/file.pdf")), \
         patch("thesis.services.sources.download_pdf", side_effect=fake_download), \
         patch("thesis.services.sources.extract_pages", return_value=(3, [(1, "Portada"), (3, "Resultado textual")])):
        result = import_openalex_source(user, project.id, "W123")
    assert result["download_status"] == "OCR_REQUIRED"
    assert result["physical_page_count"] == 3
    assert result["cover_metadata_verified"] is False
    excerpts = list_excerpts(user, project.id, result["source_id"])["excerpts"]
    assert [item["physical_page"] for item in excerpts] == [1, 3]
    assert excerpts[1]["text_sha256"] == hashlib.sha256(b"Resultado textual").hexdigest()
    source = SourceDocument.objects.get(pk=result["source_id"])
    assert source.verification_status == "OCR_REQUIRED"
    assert source.extraction_details_json["ocr_required_pages"] == 1


def test_openalex_pdf_download_runs_in_worker(context, tmp_path):
    user, _, project = context

    def fake_download(_url, destination):
        destination.write_bytes(b"%PDF-test")
        return hashlib.sha256(destination.read_bytes()).hexdigest()

    with override_settings(MEDIA_ROOT=tmp_path), \
         patch("thesis.services.sources.get_work", return_value=work("https://example.org/file.pdf")), \
         patch("thesis.services.sources.download_pdf", side_effect=fake_download) as download, \
         patch("thesis.services.sources.extract_pages", return_value=(3, [(1, "Uno"), (2, "Dos"), (3, "Pasaje verificado en PDF")])):
        pending = enqueue_openalex_source(user, project.id, "W123")
        assert pending["job"]["status"] == "QUEUED"
        assert pending["full_text_extracted"] is False
        download.assert_not_called()
        assert run_next_document_job() is True
        assert download.call_count == 1
    source = SourceDocument.objects.get(pk=pending["source_id"])
    assert source.page_count == 3
    assert source.verification_status == "TEXT_CHECKED"
    assert list_excerpts(user, project.id, source.id)["excerpts"][2]["physical_page"] == 3


def test_pdf_extractor_uses_physical_page_count_from_audited_document():
    path = Path(__file__).resolve().parents[3] / "docs/antecedentes_descargados/INT1_ARIA_Multi_LLM_Framework_2025.pdf"
    count, pages = extract_pages(path)
    assert count == 34  # Registrado y comprobado por core.grounding.audit_cli.
    assert pages and pages[0][0] == 1


def test_source_api_routes_use_session_and_project_access(context):
    import json
    from django.test import Client

    user, other, project = context
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    client.get("/api/v1/docs")
    csrf = client.cookies["csrftoken"].value
    with patch("thesis.services.sources.get_work", return_value=work(None)):
        response = client.post(
            f"/api/v1/projects/{project.id}/sources",
            data=json.dumps({"openalex_id": "W123"}), content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf,
        )
    assert response.status_code == 200
    source_id = response.json()["source_id"]
    assert client.get(f"/api/v1/projects/{project.id}/sources/{source_id}/excerpts").json()["excerpts"] == []
    client.force_login(other)
    assert client.get(f"/api/v1/projects/{project.id}/sources").status_code == 404


def test_upload_audited_pdf_and_reject_cross_project_access(context, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.test import Client

    user, other, project = context
    path = Path(__file__).resolve().parents[3] / "docs/antecedentes_descargados/INT1_ARIA_Multi_LLM_Framework_2025.pdf"
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    client.get("/api/v1/docs")
    csrf = client.cookies["csrftoken"].value
    with override_settings(MEDIA_ROOT=tmp_path):
        response = client.post(
            f"/api/v1/projects/{project.id}/sources/upload",
            data={"label": "PDF aportado por Ana", "file": SimpleUploadedFile("source.pdf", path.read_bytes(), content_type="application/pdf")},
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert response.status_code == 202, response.content
        source = response.json()
        assert source["kind"] == "UPLOAD"
        assert source["physical_page_count"] is None
        assert source["title_verified_against_cover"] is False
        assert source["full_text_extracted"] is False
        assert source["verification_status"] == "PENDING_EXTRACTION"
        assert source["job"]["status"] == "QUEUED"
        assert run_next_document_job() is True
        stored = SourceDocument.objects.get(pk=source["source_id"])
        assert stored.page_count == 34
        assert stored.verification_status == "TEXT_CHECKED"
        assert list_excerpts(user, project.id, source["source_id"])["excerpts"]
        client.force_login(other)
        forbidden = client.post(
            f"/api/v1/projects/{project.id}/sources/upload",
            data={"label": "Intento", "file": SimpleUploadedFile("x.pdf", path.read_bytes(), content_type="application/pdf")},
            HTTP_X_CSRFTOKEN=csrf,
        )
        assert forbidden.status_code == 404


def test_upload_marks_scanned_pdf_for_ocr(context, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile

    user, _, project = context
    with override_settings(MEDIA_ROOT=tmp_path), patch("thesis.services.sources.extract_pages", return_value=(2, [])):
        queued = upload_pdf_pending(user, project.id, "Escaneo", SimpleUploadedFile("scan.pdf", b"%PDF-synthetic"))
        assert queued["upload_status"] == "PDF_QUEUED"
        assert run_next_document_job() is True
    result = get_document_job(user, project.id, queued["job"]["job_id"])["result"]
    source = SourceDocument.objects.get(pk=queued["source_id"])
    assert result["upload_status"] == "OCR_REQUIRED"
    assert result["physical_page_count"] == 2
    assert result["full_text_extracted"] is False
    assert result["excerpt_count"] == 0
    assert source.verification_status == "OCR_REQUIRED"
    assert source.page_count == 2
    assert source.excerpts.count() == 0


def test_mixed_pdf_marks_missing_pages_for_selective_ocr(context, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile

    user, _, project = context
    original = b"%PDF-mixed-pages"
    with override_settings(MEDIA_ROOT=tmp_path), \
         patch("thesis.services.sources.extract_pages", return_value=(3, [(1, "Texto digital uno"), (3, "Texto digital tres")])):
        uploaded = upload_pdf_pending(user, project.id, "PDF mixto", SimpleUploadedFile("mixed.pdf", original))
        assert run_next_document_job() is True
    source = SourceDocument.objects.get(pk=uploaded["source_id"])
    assert source.verification_status == "OCR_REQUIRED"
    assert source.extraction_state == "OCR_REQUIRED"
    assert source.extraction_details_json["ocr_required_pages"] == 1
    assert source.extraction_details_json["pages_with_digital_text"] == [1, 3]
    assert source.excerpts.count() == 2

    def searchable_copy(_original, output):
        output.write_bytes(original + b"-ocr-copy")

    with override_settings(MEDIA_ROOT=tmp_path), \
         patch("thesis.services.sources.create_searchable_pdf", side_effect=searchable_copy), \
         patch("thesis.services.sources.extract_pages", return_value=(3, [(1, "Texto uno"), (2, "Texto OCR dos"), (3, "Texto tres")])):
        result = process_source_ocr(user, project.id, source.id)
    source.refresh_from_db()
    assert result["download_status"] == "OCR_EXTRACTED"
    assert source.verification_status == "TEXT_CHECKED"
    assert source.extraction_details_json["selective_ocr"] is True
    assert source.extraction_details_json["pages_with_text_after_ocr_count"] == 3
    assert [row.page_no for row in source.excerpts.order_by("page_no")] == [1, 2, 3]


def test_upload_rejects_non_pdf(context, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile

    user, _, project = context
    with override_settings(MEDIA_ROOT=tmp_path), pytest.raises(DomainError) as error:
        upload_pdf_pending(user, project.id, "Falso PDF", SimpleUploadedFile("fake.pdf", b"not a pdf"))
    assert error.value.code == "VALIDATION_ERROR"
    assert not SourceDocument.objects.filter(project=project, kind="UPLOAD").exists()


def test_ocr_keeps_original_and_records_derived_evidence(context, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile

    user, other, project = context
    path = Path(__file__).resolve().parents[3] / "docs/antecedentes_descargados/INT1_ARIA_Multi_LLM_Framework_2025.pdf"
    original_bytes = path.read_bytes()

    def verified_copy(_original, output):
        output.write_bytes(original_bytes)

    with override_settings(MEDIA_ROOT=tmp_path), \
         patch("thesis.services.sources.extract_pages", return_value=(34, [])):
        uploaded = upload_pdf_pending(user, project.id, "Escaneo pendiente", SimpleUploadedFile("source.pdf", original_bytes))
        assert run_next_document_job() is True

    source_id = uploaded["source_id"]
    with override_settings(MEDIA_ROOT=tmp_path), \
         patch("thesis.services.sources.create_searchable_pdf", side_effect=verified_copy):
        with pytest.raises(DomainError) as denied:
            process_source_ocr(other, project.id, source_id)
        assert denied.value.code == "NOT_FOUND"
        result = process_source_ocr(user, project.id, source_id)

    source = SourceDocument.objects.get(pk=source_id)
    assert result["download_status"] == "OCR_EXTRACTED"
    assert result["text_extraction_method"] == "OCR"
    assert result["physical_page_count"] == 34
    assert source.sha256 == hashlib.sha256(original_bytes).hexdigest()
    assert (tmp_path / source.storage_key).read_bytes() == original_bytes
    assert source.derived_sha256 == hashlib.sha256((tmp_path / source.derived_storage_key).read_bytes()).hexdigest()
    assert list_excerpts(user, project.id, source_id)["excerpts"]


def test_ocr_rejects_missing_engine_without_changing_source(context, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile

    user, _, project = context
    with override_settings(MEDIA_ROOT=tmp_path), \
         patch("thesis.services.sources.extract_pages", return_value=(2, [])):
        uploaded = upload_pdf_pending(user, project.id, "Escaneo", SimpleUploadedFile("source.pdf", b"%PDF-synthetic"))
        assert run_next_document_job() is True
    with override_settings(MEDIA_ROOT=tmp_path), \
         patch("thesis.integrations.ocr.importlib.util.find_spec", return_value=None), \
         pytest.raises(DomainError) as error:
        process_source_ocr(user, project.id, uploaded["source_id"])
    assert error.value.code == "OCR_UNAVAILABLE"
    source = SourceDocument.objects.get(pk=uploaded["source_id"])
    assert source.verification_status == "OCR_REQUIRED"
    assert source.derived_storage_key is None


def test_ocrmy_pdf_is_configured_to_skip_pages_that_already_have_text(tmp_path):
    from thesis.integrations.ocr import create_searchable_pdf

    command = {}
    def run(args, **kwargs):
        command["args"] = args
        Path(args[-1]).write_bytes(b"derived")
        return None

    with patch("thesis.integrations.ocr.importlib.util.find_spec", return_value=object()), \
         patch("thesis.integrations.ocr.subprocess.run", side_effect=run):
        create_searchable_pdf(Path("input.pdf"), tmp_path / "output.pdf")
    assert "--skip-text" in command["args"]


def test_ocr_http_route_requires_owner_and_enqueues(context, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.test import Client

    user, other, project = context
    with override_settings(MEDIA_ROOT=tmp_path), \
         patch("thesis.services.sources.extract_pages", return_value=(2, [])):
        uploaded = upload_pdf_pending(user, project.id, "Escaneo", SimpleUploadedFile("scan.pdf", b"%PDF-synthetic"))
        assert run_next_document_job() is True
    url = f"/api/v1/projects/{project.id}/sources/{uploaded['source_id']}/ocr"
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    client.get("/api/v1/docs")
    csrf = client.cookies["csrftoken"].value
    with override_settings(MEDIA_ROOT=tmp_path), \
         patch("thesis.services.sources.process_source_ocr") as heavy:
        response = client.post(url, HTTP_X_CSRFTOKEN=csrf)
    assert response.status_code == 202
    assert response.json()["status"] == "QUEUED"
    heavy.assert_not_called()
    client.force_login(other)
    client.get("/api/v1/docs")
    csrf = client.cookies["csrftoken"].value
    with override_settings(MEDIA_ROOT=tmp_path):
        forbidden = client.post(url, HTTP_X_CSRFTOKEN=csrf)
    assert forbidden.status_code == 404
