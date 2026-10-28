import hashlib
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from thesis.models import DocumentJob, SourceDocument, SourceExcerpt
from thesis.services.document_jobs import (
    enqueue_document_job, get_document_job, recover_interrupted_jobs, run_next_document_job,
)
from thesis.services.errors import DomainError
from thesis.services.projects import create_project


@pytest.fixture
def context(db):
    user = get_user_model().objects.create_user(email="job-owner@example.org", password="pass", display_name="Ana")
    other = get_user_model().objects.create_user(email="job-other@example.org", password="pass", display_name="Otra")
    project = create_project(user, "Trabajos")
    source = SourceDocument.objects.create(
        project=project, kind=SourceDocument.Kind.UPLOAD, title="Archivo",
        authors_json=[], storage_key="source.pdf", sha256="a" * 64,
        verification_status=SourceDocument.Status.TEXT_CHECKED,
    )
    SourceExcerpt.objects.create(source=source, chunk_no=1, page_no=1,
                                 text="Evidencia", text_sha256=hashlib.sha256(b"Evidencia").hexdigest())
    return user, other, project, source


def test_enqueue_is_idempotent_and_project_scoped(context):
    user, other, project, source = context
    first = enqueue_document_job(user, project.id, source.id, DocumentJob.Kind.GROBID)
    second = enqueue_document_job(user, project.id, source.id, DocumentJob.Kind.GROBID)
    assert first["job_id"] == second["job_id"]
    assert first["status"] == "QUEUED"
    assert DocumentJob.objects.count() == 1
    with pytest.raises(DomainError) as denied:
        get_document_job(other, project.id, first["job_id"])
    assert denied.value.code == "NOT_FOUND"


def test_http_enqueues_without_running_heavy_work(context):
    user, other, project, source = context
    client = Client()
    client.force_login(user)
    with patch("thesis.services.grobid.analyze_source_grobid") as heavy:
        response = client.post(f"/api/v1/projects/{project.id}/sources/{source.id}/grobid")
    assert response.status_code == 202
    heavy.assert_not_called()
    job_id = response.json()["job_id"]
    assert client.get(f"/api/v1/projects/{project.id}/jobs/{job_id}").json()["status"] == "QUEUED"
    client.force_login(other)
    assert client.get(f"/api/v1/projects/{project.id}/jobs/{job_id}").status_code == 404


def test_worker_saves_result_and_failure(context):
    user, _, project, source = context
    first = enqueue_document_job(user, project.id, source.id, DocumentJob.Kind.INDEX)
    with patch("thesis.services.search.index_source_passages", return_value={"indexed_passages": 2}) as work:
        assert run_next_document_job() is True
    work.assert_called_once_with(user, project.id, source.id)
    done = get_document_job(user, project.id, first["job_id"])
    assert done["status"] == "SUCCEEDED"
    assert done["result"] == {"indexed_passages": 2}
    assert done["attempts"] == 1
    assert run_next_document_job() is False

    second = enqueue_document_job(user, project.id, source.id, DocumentJob.Kind.GROBID)
    with patch("thesis.services.grobid.analyze_source_grobid", side_effect=DomainError("GROBID_UNAVAILABLE", "Servicio apagado")):
        assert run_next_document_job() is True
    failed = get_document_job(user, project.id, second["job_id"])
    assert failed["status"] == "FAILED"
    assert failed["error_code"] == "GROBID_UNAVAILABLE"
    assert failed["result"] is None


def test_worker_recovers_interrupted_job(context):
    user, _, project, source = context
    queued = enqueue_document_job(user, project.id, source.id, DocumentJob.Kind.INDEX)
    DocumentJob.objects.filter(pk=queued["job_id"]).update(status=DocumentJob.Status.RUNNING, attempts=1)
    recover_interrupted_jobs()
    assert get_document_job(user, project.id, queued["job_id"])["status"] == "QUEUED"


def test_doi_check_runs_in_worker(context):
    user, _, project, source = context
    source.doi = "10.1234/example"
    source.save(update_fields=["doi"])
    queued = enqueue_document_job(user, project.id, source.id, DocumentJob.Kind.DOI_CHECK)
    with patch("thesis.services.evidence.check_source_doi", return_value={"registry_record_found": True}) as check:
        assert run_next_document_job() is True
    check.assert_called_once_with(user, project.id, source.id)
    assert get_document_job(user, project.id, queued["job_id"])["result"]["registry_record_found"] is True
