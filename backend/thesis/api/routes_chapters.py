"""Rutas de chapters; registradas en el router compartido."""

from uuid import UUID
from ninja import Status
from thesis.services.steps import get_chapter, get_chapter_snapshot, list_chapter_snapshots, save_step, submit_chapter
from thesis.services.reviews import add_comment, advisor_dashboard, assign_advisor, decide_chapter, list_comments, resolve_comment
from thesis.services.chapter_documents import get_chapter_document, save_chapter_document
from thesis.services.ieee_citations import get_current_ieee_citation_view
from thesis.services.citation_evidence import create_citation_evidence_candidate, list_citation_evidence, review_citation_evidence
from thesis.services.citation_replacements import create_citation_replacement_proposal, decide_citation_replacement, preview_citation_replacement
from .schemas import AssignAdvisorIn, CitationEvidenceCandidateIn, CitationEvidenceDecisionIn, CitationReplacementDecisionIn, CitationReplacementProposalIn, CommentIn, DecisionIn, SaveChapterDocumentIn, SaveStepIn
from .routers import router


@router.post("/{project_id}/advisor", operation_id="thesis_api_projects_set_advisor")
def set_advisor(request, project_id: UUID, payload: AssignAdvisorIn):
    return assign_advisor(request.user, project_id, payload.email)


@router.get("/advisor/dashboard", operation_id="thesis_api_projects_advisor_projects")
def advisor_projects(request):
    return advisor_dashboard(request.user)


@router.put("/{project_id}/steps/{step_code}", operation_id="thesis_api_projects_save_project_step")
def save_project_step(request, project_id: UUID, step_code: str, payload: SaveStepIn):
    return save_step(request.user, project_id, step_code, payload.content_md,
                     payload.output_data, payload.expected_version, str(payload.idempotency_key))


@router.get("/{project_id}/chapters/{chapter_no}", operation_id="thesis_api_projects_chapter_state")
def chapter_state(request, project_id: UUID, chapter_no: int):
    return get_chapter(request.user, project_id, chapter_no)


@router.get("/{project_id}/chapters/{chapter_no}/document", operation_id="thesis_api_projects_chapter_document")
def chapter_document(request, project_id: UUID, chapter_no: int):
    return get_chapter_document(request.user, project_id, chapter_no)


@router.put("/{project_id}/chapters/{chapter_no}/document", operation_id="thesis_api_projects_save_project_chapter_document")
def save_project_chapter_document(request, project_id: UUID, chapter_no: int, payload: SaveChapterDocumentIn):
    return save_chapter_document(
        request.user,
        project_id,
        chapter_no,
        payload.content_tree,
        payload.expected_version,
        str(payload.idempotency_key),
        citations=[item.dict() for item in payload.citations],
    )


@router.get("/{project_id}/chapters/{chapter_no}/citations/ieee", operation_id="thesis_api_projects_chapter_ieee_citations")
def chapter_ieee_citations(request, project_id: UUID, chapter_no: int):
    return get_current_ieee_citation_view(request.user, project_id, chapter_no)


@router.post("/{project_id}/chapters/{chapter_no}/citations/{occurrence_id}/evidence", response={200: dict, 201: dict}, operation_id="thesis_api_projects_add_citation_evidence")
def add_citation_evidence(request, project_id: UUID, chapter_no: int,
                          occurrence_id: UUID, payload: CitationEvidenceCandidateIn):
    result = create_citation_evidence_candidate(
        request.user, project_id, chapter_no, occurrence_id, payload.excerpt_id,
        payload.claim_start, payload.claim_end, payload.excerpt_start, payload.excerpt_end,
        payload.idempotency_key,
    )
    return Status(200 if result["idempotent"] else 201, result)


@router.get("/{project_id}/chapters/{chapter_no}/citations/{occurrence_id}/evidence", operation_id="thesis_api_projects_citation_evidence_history")
def citation_evidence_history(request, project_id: UUID, chapter_no: int, occurrence_id: UUID):
    return {"reviews": list_citation_evidence(request.user, project_id, chapter_no, occurrence_id)}


@router.post("/{project_id}/chapters/{chapter_no}/citation-evidence/{review_id}/decision", operation_id="thesis_api_projects_decide_citation_evidence")
def decide_citation_evidence(request, project_id: UUID, chapter_no: int,
                              review_id: UUID, payload: CitationEvidenceDecisionIn):
    return review_citation_evidence(
        request.user, project_id, chapter_no, review_id, payload.status, payload.expected_version,
        payload.idempotency_key, payload.note,
    )


@router.post("/{project_id}/chapters/{chapter_no}/citations/{occurrence_id}/replacement-proposals", response={200: dict, 201: dict}, operation_id="thesis_api_projects_propose_citation_replacement")
def propose_citation_replacement(request, project_id: UUID, chapter_no: int,
                                 occurrence_id: UUID, payload: CitationReplacementProposalIn):
    result = create_citation_replacement_proposal(
        request.user, project_id, chapter_no, occurrence_id, payload.replacement_source_id,
        payload.rationale, payload.idempotency_key,
    )
    return Status(200 if result["idempotent"] else 201, result)


@router.get("/{project_id}/chapters/{chapter_no}/citation-replacement-proposals/{proposal_id}", operation_id="thesis_api_projects_citation_replacement_proposal")
def citation_replacement_proposal(request, project_id: UUID, chapter_no: int, proposal_id: UUID):
    return preview_citation_replacement(request.user, project_id, chapter_no, proposal_id)


@router.post("/{project_id}/chapters/{chapter_no}/citation-replacement-proposals/{proposal_id}/decision", operation_id="thesis_api_projects_decide_citation_replacement_proposal")
def decide_citation_replacement_proposal(request, project_id: UUID, chapter_no: int,
                                          proposal_id: UUID, payload: CitationReplacementDecisionIn):
    return decide_citation_replacement(
        request.user, project_id, chapter_no, proposal_id, payload.action,
        payload.expected_document_version, payload.idempotency_key, payload.reason,
    )


@router.post("/{project_id}/chapters/{chapter_no}/submit", operation_id="thesis_api_projects_submit_project_chapter")
def submit_project_chapter(request, project_id: UUID, chapter_no: int):
    return submit_chapter(request.user, project_id, chapter_no)


@router.get("/{project_id}/chapters/{chapter_no}/snapshots", operation_id="thesis_api_projects_list_snapshots")
def list_snapshots(request, project_id: UUID, chapter_no: int):
    return list_chapter_snapshots(request.user, project_id, chapter_no)


@router.get("/{project_id}/chapters/{chapter_no}/snapshots/{snapshot_id}", operation_id="thesis_api_projects_get_snapshot")
def get_snapshot(request, project_id: UUID, chapter_no: int, snapshot_id: UUID):
    return get_chapter_snapshot(request.user, project_id, chapter_no, snapshot_id)


@router.post("/{project_id}/chapters/{chapter_no}/comments", operation_id="thesis_api_projects_add_review_comment")
def add_review_comment(request, project_id: UUID, chapter_no: int, payload: CommentIn):
    return add_comment(request.user, project_id, chapter_no, payload.start_cp,
                       payload.end_cp, payload.selected_text, payload.body, payload.snapshot_id)


@router.get("/{project_id}/chapters/{chapter_no}/comments", operation_id="thesis_api_projects_review_comments")
def review_comments(request, project_id: UUID, chapter_no: int, snapshot_id: UUID | None = None):
    return list_comments(request.user, project_id, chapter_no, snapshot_id)


@router.post("/{project_id}/comments/{comment_id}/resolve", operation_id="thesis_api_projects_resolve_review_comment")
def resolve_review_comment(request, project_id: UUID, comment_id: int):
    return resolve_comment(request.user, project_id, comment_id)


@router.post("/{project_id}/chapters/{chapter_no}/decision", operation_id="thesis_api_projects_review_decision")
def review_decision(request, project_id: UUID, chapter_no: int, payload: DecisionIn):
    return decide_chapter(request.user, project_id, chapter_no, payload.action, payload.reason)
