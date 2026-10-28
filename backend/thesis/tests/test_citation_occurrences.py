from uuid import uuid4

import pytest
import hashlib
from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.test import Client

from thesis.models import (
    ChapterCitationOccurrence, ChapterDocumentRevision, CitationEvidenceReview,
    CitationReplacementDecision, SourceDocument, SourceExcerpt,
)
from thesis.services.chapter_documents import get_chapter_document, save_chapter_document
from thesis.services.errors import DomainError
from thesis.services.ieee_citations import build_ieee_citation_view
from thesis.services.citation_evidence import create_citation_evidence_candidate, review_citation_evidence
from thesis.services.reviews import assign_advisor
from thesis.services.citation_replacements import (
    create_citation_replacement_proposal, decide_citation_replacement, preview_citation_replacement,
)
from thesis.services.projects import create_project


@pytest.fixture
def citation_context(db):
    owner = get_user_model().objects.create_user(email="citation-owner@example.org", password="pass")
    project = create_project(owner, "Citas estructuradas")
    source = SourceDocument.objects.create(
        project=project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.ALICIA, provider_record_id="alicia-citation-001",
        title="Título de la fuente de prueba", authors_json=["Autora Uno", "Autor Dos"],
        publication_year=2024, doi="10.1234/citation", publication_venue="Revista de Prueba",
        url="https://example.org/paper", metadata_origin=SourceDocument.MetadataOrigin.USER_FILE_IMPORT,
        verification_status=SourceDocument.Status.UNVERIFIED_METADATA,
    )
    return owner, project, source


def citation_mark(block_id, source_id, *, position=12, locator="p. 4", group_id=None):
    return {
        "group_id": group_id or uuid4(), "block_id": block_id, "position": position,
        "sources": [{"source_id": source_id, "locator": locator}],
    }


@pytest.mark.django_db
def test_citations_are_saved_with_revision_frozen_metadata_and_idempotency(citation_context):
    owner, project, source = citation_context
    block_id = str(uuid4())
    tree = {"schema_version": 1, "blocks": [{
        "type": "paragraph", "id": block_id, "text": "Esta afirmación usa evidencia."}]}
    mark = citation_mark(block_id, source.id)
    key = str(uuid4())
    saved = save_chapter_document(owner, project.id, 1, tree, 0, key, citations=[mark])
    assert saved["citation_manifest_sha256"]
    assert len(saved["citations"]) == 1
    assert saved["citations"][0]["sources"][0]["reference"]["title"] == source.title
    repeated = save_chapter_document(
        owner, project.id, 1, tree, 0, key, citations=[mark],
    )
    assert repeated["idempotent"] is True
    assert repeated["revision_id"] == saved["revision_id"]
    source.title = "Metadato cambiado después de guardar"
    source.save(update_fields=["title"])
    current = get_chapter_document(owner, project.id, 1)
    assert current["citations"][0]["sources"][0]["reference"]["title"] == "Título de la fuente de prueba"
    retried_after_metadata_change = save_chapter_document(owner, project.id, 1, tree, 0, key, citations=[mark])
    assert retried_after_metadata_change["idempotent"] is True
    assert retried_after_metadata_change["citations"][0]["sources"][0]["reference"]["title"] == "Título de la fuente de prueba"
    assert retried_after_metadata_change["document_version"] == 1
    assert retried_after_metadata_change["current_document_version"] == 1
    assert retried_after_metadata_change["is_current"] is True

    newer_tree = {"schema_version": 1, "blocks": [{
        "type": "paragraph", "id": block_id, "text": "Esta afirmación usa evidencia actualizada."}]}
    newer = save_chapter_document(owner, project.id, 1, newer_tree, 1, str(uuid4()), citations=[mark])
    historical_retry = save_chapter_document(owner, project.id, 1, tree, 0, key, citations=[mark])
    assert historical_retry["revision_id"] == saved["revision_id"]
    assert historical_retry["document_version"] == 1
    assert historical_retry["current_document_version"] == 2
    assert historical_retry["is_current"] is False
    assert get_chapter_document(owner, project.id, 1)["revision_id"] == newer["revision_id"]

    with pytest.raises(DomainError) as conflict:
        save_chapter_document(owner, project.id, 1, tree, 0, key,
                              citations=[{**mark, "position": mark["position"] + 1}])
    assert conflict.value.code == "IDEMPOTENCY_CONFLICT"


@pytest.mark.django_db
def test_citation_document_and_ieee_http_contract(citation_context):
    owner, project, source = citation_context
    block_id = str(uuid4())
    client = Client()
    client.force_login(owner)
    response = client.put(
        f"/api/v1/projects/{project.id}/chapters/1/document",
        data={
            "content_tree": {"schema_version": 1, "blocks": [
                {"type": "paragraph", "id": block_id, "text": "Una afirmación con fuente."},
            ]},
            "citations": [{
                "group_id": str(uuid4()), "block_id": block_id, "position": 8,
                "sources": [{"source_id": str(source.id), "locator": "p. 4"}],
            }],
            "expected_version": 0,
            "idempotency_key": str(uuid4()),
        },
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    ieee = client.get(f"/api/v1/projects/{project.id}/chapters/1/citations/ieee")
    assert ieee.status_code == 200, ieee.content
    payload = ieee.json()
    assert payload["marks"][0]["citation_text"] == "[1]"
    assert payload["references"][0]["reference"]["title"] == source.title


@pytest.mark.django_db
def test_citation_validation_rejects_nonparagraph_bad_offset_and_foreign_source(citation_context):
    owner, project, source = citation_context
    paragraph_id, heading_id = str(uuid4()), str(uuid4())
    tree = {"schema_version": 1, "blocks": [
        {"type": "heading", "id": heading_id, "level": 1, "text": "Capítulo"},
        {"type": "paragraph", "id": paragraph_id, "text": "Texto breve."},
    ]}
    with pytest.raises(DomainError) as wrong_block:
        save_chapter_document(owner, project.id, 1, tree, 0, str(uuid4()),
                              citations=[citation_mark(heading_id, source.id)])
    assert wrong_block.value.code == "VALIDATION_ERROR"
    with pytest.raises(DomainError) as bad_offset:
        save_chapter_document(owner, project.id, 1, tree, 0, str(uuid4()),
                              citations=[citation_mark(paragraph_id, source.id, position=99)])
    assert bad_offset.value.code == "VALIDATION_ERROR"
    other_project = create_project(owner, "Proyecto fuente ajeno")
    foreign = SourceDocument.objects.create(
        project=other_project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.ALICIA, provider_record_id="alicia-citation-foreign",
        title="Fuente ajena", authors_json=[],
    )
    with pytest.raises(DomainError) as foreign_source:
        save_chapter_document(owner, project.id, 1, tree, 0, str(uuid4()),
                              citations=[citation_mark(paragraph_id, foreign.id, position=4)])
    assert foreign_source.value.code == "NOT_FOUND"


@pytest.mark.django_db
def test_citation_occurrence_is_append_only_in_postgres(citation_context):
    owner, project, source = citation_context
    block_id = str(uuid4())
    tree = {"schema_version": 1, "blocks": [{
        "type": "paragraph", "id": block_id, "text": "Una frase con cita."}]}
    saved = save_chapter_document(owner, project.id, 1, tree, 0, str(uuid4()),
                                  citations=[citation_mark(block_id, source.id, position=8)])
    occurrence = ChapterCitationOccurrence.objects.get(document_revision_id=saved["revision_id"])
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            ChapterCitationOccurrence.objects.filter(pk=occurrence.pk).update(locator="p. 9")
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            ChapterCitationOccurrence.objects.filter(pk=occurrence.pk).delete()


@pytest.mark.django_db
def test_postgres_guard_rejects_cross_project_source_and_invalid_anchor(citation_context):
    owner, project, source = citation_context
    block_id = str(uuid4())
    tree = {"schema_version": 1, "blocks": [{
        "type": "paragraph", "id": block_id, "text": "Una frase con cita."}]}
    saved = save_chapter_document(owner, project.id, 1, tree, 0, str(uuid4()))
    revision = saved["revision_id"]
    other_project = create_project(owner, "Proyecto de fuente externa")
    foreign_source = SourceDocument.objects.create(
        project=other_project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.ALICIA,
        provider_record_id="alicia-citation-db-guard", title="Fuente externa", authors_json=[],
    )

    for source_id, anchor_id in ((foreign_source.id, block_id), (source.id, str(uuid4()))):
        row = ChapterCitationOccurrence(
            document_revision_id=revision, group_id=uuid4(), group_order=1,
            block_id=anchor_id, char_offset=2, source_id=source_id, source_order=1,
            locator="", reference_snapshot={}, reference_sha256="a" * 64, created_by=owner,
        )
        with pytest.raises(DatabaseError):
            with transaction.atomic():
                row.pk = uuid4()
                row.save(force_insert=True)


@pytest.mark.django_db
def test_ieee_numbers_follow_first_occurrence_and_frozen_metadata(citation_context):
    owner, project, first_source = citation_context
    second_source = SourceDocument.objects.create(
        project=project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.ALICIA, provider_record_id="alicia-ieee-second",
        title="Segunda fuente", authors_json=["B. Autora"], publication_year=2023,
        publication_venue="Revista B", verification_status=SourceDocument.Status.UNVERIFIED_METADATA,
    )
    first_block, second_block = str(uuid4()), str(uuid4())
    tree = {"schema_version": 1, "blocks": [
        {"type": "paragraph", "id": first_block, "text": "Primera afirmación."},
        {"type": "paragraph", "id": second_block, "text": "Segunda afirmación."},
    ]}
    first_group_id = uuid4()
    saved = save_chapter_document(owner, project.id, 1, tree, 0, str(uuid4()), citations=[
        {"group_id": first_group_id, "block_id": first_block, "position": 5,
         "sources": [
             {"source_id": first_source.id, "locator": "p. 4"},
             {"source_id": second_source.id, "locator": "p. 6"},
         ]},
        citation_mark(second_block, second_source.id, position=5),
    ])
    revision = ChapterDocumentRevision.objects.get(pk=saved["revision_id"])
    view = build_ieee_citation_view(revision)
    assert [mark["citation_text"] for mark in view["marks"]] == ["[1], [2]", "[2]"]
    assert [item["reference"]["title"] for item in view["references"]] == [
        "Título de la fuente de prueba", "Segunda fuente",
    ]
    assert view["references"][0]["status"] == "METADATA_COMPLETE"
    assert view["references"][1]["status"] == "METADATA_COMPLETE"

    reordered = {"schema_version": 1, "blocks": [tree["blocks"][1], tree["blocks"][0]]}
    updated = save_chapter_document(owner, project.id, 1, reordered, 1, str(uuid4()), citations=[
        citation_mark(second_block, second_source.id, position=5),
        {"group_id": first_group_id, "block_id": first_block, "position": 5,
         "sources": [
             {"source_id": first_source.id, "locator": "p. 4"},
             {"source_id": second_source.id, "locator": "p. 6"},
         ]},
    ])
    updated_revision = ChapterDocumentRevision.objects.get(pk=updated["revision_id"])
    updated_view = build_ieee_citation_view(updated_revision)
    assert [mark["citation_text"] for mark in updated_view["marks"]] == ["[1]", "[2], [1]"]
    assert [item["reference"]["title"] for item in updated_view["references"]] == [
        "Segunda fuente", "Título de la fuente de prueba",
    ]


@pytest.mark.django_db
def test_claim_evidence_is_separate_from_identity_and_advisor_review(citation_context):
    owner, project, source = citation_context
    advisor = get_user_model().objects.create_user(email="citation-advisor@example.org", password="pass")
    assign_advisor(owner, project.id, advisor.email)
    text = "La evidencia textual permite revisar esta afirmación académica."
    block_id = str(uuid4())
    saved = save_chapter_document(owner, project.id, 1, {
        "schema_version": 1,
        "blocks": [{"type": "paragraph", "id": block_id, "text": text}],
    }, 0, str(uuid4()), citations=[citation_mark(block_id, source.id, position=15)])
    occurrence = ChapterCitationOccurrence.objects.get(document_revision_id=saved["revision_id"])
    source.verification_status = SourceDocument.Status.TEXT_CHECKED
    source.save(update_fields=["verification_status"])
    excerpt_text = "Este pasaje corresponde al texto extraído del documento fuente."
    excerpt = SourceExcerpt.objects.create(
        source=source, chunk_no=1, page_no=4, text=excerpt_text,
        text_sha256=hashlib.sha256(excerpt_text.encode()).hexdigest(),
    )
    candidate = create_citation_evidence_candidate(
        owner, project.id, 1, occurrence.id, excerpt.id, 0, len(text),
        0, len(excerpt_text), str(uuid4()),
    )
    assert candidate["status"] == CitationEvidenceReview.Status.CANDIDATE
    assert candidate["source_identity"] == "NOT_CHECKED"
    assert candidate["source_text_status"] == SourceDocument.Status.TEXT_CHECKED
    assert candidate["automated_semantic_assessment"] == "NOT_PERFORMED"

    decision_key = str(uuid4())
    decision = review_citation_evidence(
        advisor, project.id, 1, candidate["review_id"], CitationEvidenceReview.Status.SUPPORTS,
        expected_version=1, idempotency_key=decision_key, note="Revisión humana del pasaje.",
    )
    assert decision["status"] == CitationEvidenceReview.Status.SUPPORTS
    assert decision["review_version"] == 2
    assert decision["previous_review_id"] == candidate["review_id"]
    assert CitationEvidenceReview.objects.filter(occurrence=occurrence).count() == 2
    with pytest.raises(DomainError) as changed_note:
        review_citation_evidence(
            advisor, project.id, 1, candidate["review_id"], CitationEvidenceReview.Status.SUPPORTS,
            expected_version=1, idempotency_key=decision_key, note="Justificación alterada.",
        )
    assert changed_note.value.code == "IDEMPOTENCY_CONFLICT"


@pytest.mark.django_db
def test_citation_replacement_requires_acceptance_and_creates_new_revision(citation_context):
    owner, project, old_source = citation_context
    new_source = SourceDocument.objects.create(
        project=project, kind=SourceDocument.Kind.EXTERNAL,
        record_provider=SourceDocument.RecordProvider.ALICIA, provider_record_id="alicia-replacement",
        title="Fuente alternativa", authors_json=["C. Autora"], publication_year=2025,
        publication_venue="Revista C", verification_status=SourceDocument.Status.UNVERIFIED_METADATA,
    )
    block_id = str(uuid4())
    saved = save_chapter_document(owner, project.id, 1, {
        "schema_version": 1,
        "blocks": [{"type": "paragraph", "id": block_id, "text": "Una afirmación citada."}],
    }, 0, str(uuid4()), citations=[citation_mark(block_id, old_source.id, position=10)])
    occurrence = ChapterCitationOccurrence.objects.get(document_revision_id=saved["revision_id"])
    proposal = create_citation_replacement_proposal(
        owner, project.id, 1, occurrence.id, new_source.id,
        "La fuente alternativa se propone para revisión académica.", str(uuid4()),
    )
    preview = preview_citation_replacement(owner, project.id, 1, proposal["proposal_id"])
    assert preview["preview"]["requires_explicit_acceptance"] is True
    assert preview["preview"]["from"]["title"] == old_source.title
    assert preview["preview"]["to"]["title"] == new_source.title
    assert ChapterDocumentRevision.objects.count() == 1

    decision_key = str(uuid4())
    decision = decide_citation_replacement(
        owner, project.id, 1, proposal["proposal_id"], CitationReplacementDecision.Status.ACCEPTED,
        expected_document_version=proposal["expected_document_version"], idempotency_key=decision_key,
    )
    assert decision["decision"]["status"] == CitationReplacementDecision.Status.ACCEPTED
    assert decision["decision"]["resulting_document_revision_id"] != saved["revision_id"]
    assert ChapterDocumentRevision.objects.count() == 2
    old_occurrence = ChapterCitationOccurrence.objects.get(pk=occurrence.pk)
    assert old_occurrence.source_id == old_source.id
    new_revision = ChapterDocumentRevision.objects.get(pk=decision["decision"]["resulting_document_revision_id"])
    new_occurrence = ChapterCitationOccurrence.objects.get(document_revision=new_revision)
    assert new_occurrence.source_id == new_source.id
    assert new_occurrence.reference_snapshot["title"] == new_source.title
    with pytest.raises(DomainError) as changed_reason:
        decide_citation_replacement(
            owner, project.id, 1, proposal["proposal_id"], CitationReplacementDecision.Status.ACCEPTED,
            expected_document_version=proposal["expected_document_version"], idempotency_key=decision_key,
            reason="Razón distinta.",
        )
    assert changed_reason.value.code == "VERSION_CONFLICT"
