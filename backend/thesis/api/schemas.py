"""Contratos de entrada de la API; comportamiento conservado del módulo original."""

from datetime import date
from uuid import UUID
from typing import Literal

from ninja import Schema
from pydantic import ConfigDict


class ProjectPermissionsOut(Schema):
    can_read_project: bool
    can_edit_document: bool
    can_manage_workflow: bool
    can_review_chapters: bool


class ProjectSummaryOut(Schema):
    project_id: UUID
    name: str
    title: str
    status: Literal["ACTIVE"]
    role: Literal["OWNER", "ADVISOR"]
    permissions: ProjectPermissionsOut


class ProjectListOut(Schema):
    projects: list[ProjectSummaryOut]
    offset: int
    limit: int
    has_more: bool


class CreateProjectIn(Schema):
    name: str
    title: str | None = None

class RegisterIdeaIn(Schema):
    description: str
    expected_version: int

class ImportSourceIn(Schema):
    openalex_id: str

class SearchStrategyIn(Schema):
    provider: str
    title: str
    topic: str
    query_text: str
    search_equation: str = ""
    concepts: list[str] = []
    filters: dict = {}
    search_url: str = ""
    idempotency_key: UUID

class SearchStrategyRevisionIn(SearchStrategyIn):
    expected_version: int

class ManualSearchExecutionIn(Schema):
    execution_date: date
    reported_result_count: int | None = None
    notes: str = ""
    idempotency_key: UUID

class SelectDiscoveryCandidateIn(Schema):
    provider: str
    provider_record_id: str
    title: str
    authors: list[str] = []
    publication_year: int | None = None
    doi: str | None = None
    abstract: str = ""
    publication_venue: str = ""
    record_url: str = ""
    pdf_url: str = ""
    search_execution_id: UUID | None = None

class TableRecipeIn(Schema):
    name: str
    spec: dict
    idempotency_key: UUID
    expected_version: int | None = None

class ResearchFigureIn(Schema):
    name: str
    spec: dict
    idempotency_key: UUID
    expected_version: int | None = None
    accept_truncated_input: bool = False

class SourceDuplicateDecisionIn(Schema):
    source_id: UUID
    other_source_id: UUID
    decision: str
    primary_source_id: UUID | None = None
    note: str = ""
    idempotency_key: UUID

class SearchPassagesIn(Schema):
    query: str
    limit: int = 5
    source_ids: list[UUID] | None = None

class SaveStepIn(Schema):
    content_md: str
    output_data: dict
    expected_version: int
    idempotency_key: UUID

class CitationSourceIn(Schema):
    source_id: UUID
    locator: str = ""

class CitationMarkIn(Schema):
    group_id: UUID
    block_id: UUID
    position: int
    sources: list[CitationSourceIn]

class CitationEvidenceCandidateIn(Schema):
    excerpt_id: int
    claim_start: int
    claim_end: int
    excerpt_start: int
    excerpt_end: int
    idempotency_key: UUID

class CitationEvidenceDecisionIn(Schema):
    status: str
    expected_version: int
    idempotency_key: UUID
    note: str = ""

class CitationReplacementProposalIn(Schema):
    replacement_source_id: UUID
    rationale: str
    idempotency_key: UUID

class CitationReplacementDecisionIn(Schema):
    action: str
    expected_document_version: int
    idempotency_key: UUID
    reason: str = ""

class ZoteroImportIn(Schema):
    item_key: str

class SaveChapterDocumentIn(Schema):
    content_tree: dict
    citations: list[CitationMarkIn] = []
    expected_version: int
    idempotency_key: UUID

class AssignAdvisorIn(Schema):
    email: str

class CommentIn(Schema):
    snapshot_id: UUID | None = None
    start_cp: int
    end_cp: int
    selected_text: str
    body: str

class DecisionIn(Schema):
    action: str
    reason: str = ""

class QuoteIn(Schema):
    quote: str
    limit: int = 5

class EvidenceLinkIn(Schema):
    excerpt_id: int
    claim_text: str
    start_char: int
    end_char: int
    matched_text: str
    revision_id: int | None = None

class EvidenceDecisionIn(Schema):
    decision: str
    note: str = ""

class WorkflowTaskUpdateIn(Schema):
    task_id: str
    title: str | None = None
    description: str = ""
    chapter_no: int | None = None
    order_index: int | None = None
    is_active: bool | None = None
    is_optional: bool | None = None
    prompt_text: str | None = None
    output_schema: dict | None = None

class WorkflowDependencyIn(Schema):
    source: str
    target: str
    type: str = "DATA_REQUIRED"
    field: str = ""
    blocking: bool = True
    reason: str = ""

class WorkflowDraftIn(Schema):
    tasks: list[WorkflowTaskUpdateIn] = []
    dependencies: list[WorkflowDependencyIn] | None = None
    expected_version: int = 0

class PublishWorkflowIn(Schema):
    change_summary: str = ""
    expected_version: int

class RestoreWorkflowIn(Schema):
    target_version_no: int
    change_summary: str = ""

class WorkflowTaskExecuteIn(Schema):
    input_data: dict = {}
    output_data: dict
    idempotency_key: UUID

class GenerateTaskProposalIn(Schema):
    expected_state_version: int | None = None
    workflow_version_no: int | None = None
    input_data: dict = {}
    context_refs: list[dict] = []
    idempotency_key: UUID

class AIBatchTaskIn(Schema):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    input_data: dict = {}
    context_refs: list[dict] = []

class CreateAIBatchIn(Schema):
    model_config = ConfigDict(extra="forbid")

    tasks: list[AIBatchTaskIn]
    expected_state_version: int
    workflow_version_no: int
    idempotency_key: UUID

class CreateBatchSynthesisIn(Schema):
    model_config = ConfigDict(extra="forbid")

    job_ids: list[UUID]
    idempotency_key: UUID

class DecideBatchSynthesisIn(Schema):
    model_config = ConfigDict(extra="forbid")

    decision: str
    decision_key: UUID
    reason: str = ""

class CreateSupportInvitationIn(Schema):
    model_config = ConfigDict(extra="forbid")

    invited_email: str
    task_id: str
    task_instructions: str
    source_ids: list[UUID] = []
    ttl_hours: int = 168

class AcceptSupportInvitationIn(Schema):
    model_config = ConfigDict(extra="forbid")

    invite_token: str

class SupportContributionIn(Schema):
    model_config = ConfigDict(extra="forbid")

    response_text: str
    source_excerpt_ids: list[int] = []
    idempotency_key: UUID

class AcceptAIProposalIn(Schema):
    expected_state_version: int
    decision_key: UUID
    expected_document_version: int | None = None
    proposal_sha256: str | None = None

class RejectAIProposalIn(Schema):
    decision_key: UUID
    reason: str = ""
