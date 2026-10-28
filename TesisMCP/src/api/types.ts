export type SessionUser = {
  id: string
  email: string
  display_name: string
}

export type SessionResponse = {
  authenticated: boolean
  user: SessionUser | null
  csrf_token: string
}

export type ProjectPermissions = {
  can_read_project: boolean
  can_edit_document: boolean
  can_manage_workflow: boolean
  can_review_chapters: boolean
}

export type ProjectSummary = {
  project_id: string
  name: string
  title: string
  status: "ACTIVE"
  role: "OWNER" | "ADVISOR"
  permissions: ProjectPermissions
}

export type ProjectPage = {
  projects: ProjectSummary[]
  offset: number
  limit: number
  has_more: boolean
}

export type ProjectState = {
  project_id: string
  name: string
  title: string
  status: "ACTIVE" | "ARCHIVED"
  idea_provisional: string
  state_version: number
}

export type ChapterState = {
  chapter_no: number
  status: "DRAFT" | "READY" | "CHANGES_REQUESTED" | "APPROVED"
  latest_revision: { id: string; revision_no: number } | null
  approved_revision_id: string | null
  approved_snapshot_id: string | null
  submitted_snapshot_id: string | null
  steps: Array<{ step_code: string; status: string; output_json: Record<string, unknown> }>
}

export type ChapterTextBlock =
  | { type: "heading"; id: string; level: number; text: string }
  | { type: "paragraph" | "blockquote" | "code_block"; id: string; text: string }
  | { type: "bullet_list" | "ordered_list"; id: string; items: string[] }
export type ChapterArtifactBlock =
  | { type: "data_table"; id: string; table_version_id: string; result_sha256: string; caption: string }
  | { type: "figure"; id: string; figure_version_id: string; output_sha256: string; caption: string }
export type ChapterBlock = ChapterTextBlock | ChapterArtifactBlock
export type ChapterContentTree = { schema_version: 1 | 2; blocks: ChapterBlock[] }
export type ChapterCitation = {
  group_id: string
  block_id: string
  position: number
  sources: Array<{
    source_id: string
    locator: string
    source_order?: number
    reference?: Record<string, unknown>
    reference_sha256?: string
  }>
}
export type ChapterDocument = {
  chapter_no: number
  document_version: number
  revision_id: string | null
  revision_no: number | null
  schema_version: 1 | 2
  content_tree: ChapterContentTree
  content_md: string
  content_sha256: string
  citation_manifest_sha256?: string
  citations?: ChapterCitation[]
  state_version: number | null
  source?: string | null
  is_legacy_projection: boolean
  is_stale: boolean
  idempotent?: boolean
  current_document_version?: number
  is_current?: boolean
}

export type WorkflowTaskPrompt = {
  prompt_text: string
  prompt_version: number
  provenance: string
  parameters_schema: Record<string, unknown>
}

export type WorkflowTask = {
  task_id: string
  legacy_step_code: string
  title: string
  description: string
  chapter_no: number | null
  order_index: number
  is_active: boolean
  is_optional: boolean
  is_protected: boolean
  contract_name: string
  branch_condition: string
  prompt: WorkflowTaskPrompt | null
}

export type WorkflowDependency = {
  source: string
  target: string
  type: string
  field: string
  blocking: boolean
  reason: string
}

export type WorkflowVersion = {
  workflow_id: number
  version_no: number
  status: "DRAFT" | "PUBLISHED" | "RETIRED"
  base_template_version: string
  change_summary: string
  content_sha256: string
  lock_version: number
  created_at: string
  tasks: WorkflowTask[]
  dependencies: WorkflowDependency[]
}

export type WorkflowHistoryItem = {
  version_no: number
  status: "DRAFT" | "PUBLISHED" | "RETIRED"
  change_summary: string
  content_sha256: string
  created_at: string
}

export type WorkflowState = {
  project_id: string
  published: WorkflowVersion | null
  draft: WorkflowVersion | null
  history: WorkflowHistoryItem[]
}

export type WorkflowTaskUpdateInput = {
  task_id: string
  title?: string
  description?: string
  chapter_no?: number | null
  order_index?: number
  is_active?: boolean
  is_optional?: boolean
  prompt_text?: string
  output_schema?: Record<string, unknown> | null
}

export type WorkflowDraftInput = {
  tasks?: WorkflowTaskUpdateInput[]
  dependencies?: WorkflowDependency[] | null
  expected_version: number
}

export type WorkflowValidationResult = {
  valid: boolean
  errors: string[]
  warnings: string[]
}

export type PublishWorkflowInput = {
  change_summary: string
  expected_version: number
}

export type RestoreWorkflowInput = {
  target_version_no: number
  change_summary: string
}

export type EffectivePrompt = {
  task_id: string
  title: string
  workflow_version_no: number
  is_protected: boolean
  is_optional: boolean
  is_active: boolean
  prompt_text: string
  prompt_version: number
  provenance: string
  parameters_schema: Record<string, unknown>
}

export type WorkflowTaskExecuteInput = {
  input_data?: Record<string, unknown>
  output_data: Record<string, unknown>
  idempotency_key: string
}

export type WorkflowTaskExecutionItem = {
  execution_id: number
  revision_no: number
  input_data: Record<string, unknown>
  output_data: Record<string, unknown>
  prompt_text_used: string
  prompt_version_used: number
  output_sha256: string
  created_at: string
}

export type CustomWorkflowTaskExecutions = {
  task_id: string
  workflow_version_no: number
  executions: WorkflowTaskExecutionItem[]
}

export type SaveStepPayload = {
  content_md: string
  output_data: Record<string, unknown>
  expected_version: number
  idempotency_key: string
}

export type SourceDocument = {
  source_id: string
  project_id: string
  kind: "UPLOAD" | "EXTERNAL"
  record_provider: string
  provider_record_id: string
  imported_file_sha256?: string | null
  title: string | null
  abstract: string | null
  publication_venue: string | null
  display_label: string
  original_filename: string | null
  metadata_origin: string
  title_verified_against_cover: boolean
  authors: string[] | null
  publication_year: number | null
  doi: string | null
  record_url: string
  landing_page_url: string
  pdf_url: string
  openalex_retracted: boolean | null
  verification_status: "PENDING_EXTRACTION" | "TEXT_CHECKED" | "OCR_REQUIRED" | "REJECTED" | "METADATA_CHECKED" | "UNVERIFIED_METADATA"
  physical_page_count: number | null
  text_extraction_method: string | null
  extraction_state: string
  extraction_details: Record<string, unknown>
  ocr_derived_sha256?: string | null
  full_text_extracted: boolean
  verification_level: string
  cover_metadata_verified: boolean
  scientific_claims_verified: boolean
  excerpt_count: number
  segment_count: number
  download_status?: string
}

export type SourceExcerpt = {
  excerpt_id: number
  physical_page: number
  text: string
  text_sha256: string
}

export type SourceSegment = {
  segment_id: number
  sequence_no: number
  kind: string
  locator: Record<string, unknown>
  heading: string
  text: string
}

export type DocumentJob = {
  job_id: string
  project_id: string
  source_id: string | null
  manuscript_id?: string | null
  kind: string
  status: "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "CANCELLED"
  attempts: number
  created_at: string
  started_at: string | null
  finished_at: string | null
  result: Record<string, unknown> | null
  error_code: string | null
  error_message: string | null
}

export type PassageItem = {
  source_id: string
  passage_id: number
  excerpt_id?: number | null
  segment_id?: number | null
  physical_page?: number | null
  locator: Record<string, unknown>
  locator_kind: string
  start_char: number
  text: string
  text_sha256: string
  cosine_distance: number
  embedding_model: string
  supports_claim_verified: boolean
}

export type PassageSearchResult = {
  query: string
  search_status: string
  results: PassageItem[]
}

export type DiscoveryCandidate = {
  provider: string
  provider_record_id: string
  title: string
  authors: string[]
  publication_year: number | null
  doi: string | null
  abstract: string
  publication_venue: string
  record_url: string
  pdf_url: string
  search_execution_id?: string | null
}

export type SearchStrategy = {
  strategy_id: string
  provider: string
  title: string
  topic: string
  query_text: string
  search_equation: string
  concepts: string[]
  filters: Record<string, unknown>
  search_url: string
  created_at?: string
  executions_count?: number
}

export type ZoteroConnectionStatus = {
  provider: "ZOTERO"
  connected: boolean
  zotero_user_id: string | null
  granted_scopes: string[]
  connected_at: string | null
}

export type AdvisorDashboardProject = {
  project_id: string
  project_name: string
  chapters: Array<{ chapter_no: number; status: string }>
}

export type ChapterSnapshotSummary = {
  snapshot_id: string
  snapshot_no: number
  chapter_no: number
  status: string
  content_sha256: string
  manifest_sha256: string
  created_at: string
}

export type ChapterSnapshotDetail = {
  snapshot_id: string
  snapshot_no: number
  chapter_no: number
  status: string
  content_md: string
  content_sha256: string
  manifest_sha256: string
  created_at: string
  sections_manifest?: Record<string, unknown>[]
  evidence_links?: Record<string, unknown>[]
}

/**
 * Contrato real del backend para instantáneas (backend/thesis/services/chapter_serialization.py,
 * _snapshot_summary y _snapshot_detail). Los tipos sin sufijo «Api» conservan el contrato del
 * módulo de demostración (src/features/) y no se tocan en R6.
 */
export type ChapterSnapshotSummaryApi = {
  id: string
  snapshot_no: number
  format_version: number
  payload_sha256: string
  state_version: number
  workflow_version_no: number | null
  document_revision_id: string | null
  created_at: string
}

export type ChapterSnapshotDetailApi = {
  id: string
  chapter_no: number
  snapshot_no: number
  format_version: number
  project_title: string
  state_version: number
  workflow_version_no: number | null
  document_revision_id: string | null
  content_tree: Record<string, unknown> | null
  citations: Record<string, unknown>[]
  content_md: string
  sections_manifest: Record<string, unknown>[] | null
  document_artifacts_manifest: Record<string, unknown>[] | null
  payload_sha256: string
  created_by_id: number | null
  created_at: string
}

export type ReviewComment = {
  comment_id: number
  snapshot_id: string | null
  start_cp: number
  end_cp: number
  selected_text: string
  body: string
  status: "OPEN" | "RESOLVED"
  author: string
  created_at: string
  resolved_at?: string | null
}

export type SupportInvitation = {
  invitation_id: string
  invited_email: string
  task_id: string
  task_title?: string
  task_instructions: string
  status: "PENDING" | "ACCEPTED" | "REVOKED" | "EXPIRED"
  ttl_hours: number
  expires_at: string
  created_at: string
  accepted_at?: string | null
  revoked_at?: string | null
  invite_token?: string
}

export type SupportContribution = {
  contribution_id: number
  response_text: string
  source_excerpt_ids: number[]
  created_at: string
}

// --- Bloque 6: Generación con IA, Propuestas, Diffs y Batches ---

export type AIGenerationJob = {
  job_id: string
  project_id: string
  task_id: string
  workflow_version_no: number
  prompt_version_used: number
  status: "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "CANCELLED"
  acceptance_status: "PENDING_ACCEPTANCE" | "ACCEPTED" | "REJECTED"
  idempotency_key: string
  input_data: Record<string, unknown>
  output_data: Record<string, unknown> | null
  output_sha256: string
  provider: string
  model: string
  usage: Record<string, unknown>
  error_code: string | null
  error_message: string | null
  decision_reason: string | null
  result_revision_id: number | null
  result_execution_id: number | null
  result_document_revision_id: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export type DocumentDiffOperation = {
  op: string
  before_block_ids: string[]
  after_blocks: ChapterBlock[]
}

export type DocumentDiff = {
  job_id: string
  task_id: string
  chapter_no: number
  operation: "REPLACE_DOCUMENT"
  expected_state_version: number
  expected_document_version: number
  before_content_sha256: string
  before_tree: ChapterContentTree
  before_content_md: string
  after_tree: ChapterContentTree
  after_content_md: string
  operations: DocumentDiffOperation[]
  source_output_sha256: string
  proposal_sha256: string
}

export type AcceptProposalPayload = {
  expected_state_version: number
  decision_key: string
  expected_document_version?: number
  proposal_sha256?: string
}

export type RejectProposalPayload = {
  decision_key: string
  reason?: string
}

export type AIBatchItem = AIGenerationJob & {
  item_order: number
  input_sha256: string
}

export type AIBatch = {
  batch_id: string
  project_id: string
  status: "QUEUED" | "RUNNING" | "SUCCEEDED" | "PARTIAL" | "FAILED" | "CANCELLED"
  workflow_version_no: number
  item_count: number
  completed_count: number
  items: AIBatchItem[]
  created_at: string
}

export type BatchSynthesis = {
  synthesis_id: string
  batch_id: string
  status: "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "CANCELLED"
  decision_status: "PENDING_REVIEW" | "ACCEPTED" | "REJECTED"
  output_data: Record<string, unknown> | null
  output_sha256: string
  error_code: string | null
  error_message: string | null
  created_at: string
  finished_at: string | null
}

// --- Bloque 7: Datasets, Tablas, Figuras, Citas IEEE y Exportación ---

export type ResearchDataset = {
  dataset_id: string
  name: string
  description: string
  current_version_no: number
  created_at: string
}

export type ResearchDatasetVersion = {
  version_id: string
  dataset_id: string
  version_no: number
  original_filename: string
  sheet_name: string | null
  file_sha256: string
  row_count: number
  column_names: string[]
  created_at: string
}

export type TableRecipe = {
  recipe_id: string
  dataset_id: string
  name: string
  current_version_no: number
  created_at: string
}

export type TableRecipeVersion = {
  version_id: string
  recipe_id: string
  dataset_id: string
  dataset_version_no: number
  version_no: number
  name: string
  spec: Record<string, unknown>
  spec_sha256: string
  result_sha256: string
  result_columns: string[]
  row_count: number
  matched_row_count: number
  truncated: boolean
  rows: Record<string, unknown>[]
  created_at: string
}

export type ResearchFigure = {
  figure_id: string
  dataset_id: string
  recipe_id: string
  name: string
  current_version_no: number
  created_at: string
}

export type ResearchFigureVersion = {
  version_id: string
  figure_id: string
  dataset_id: string
  recipe_id: string
  table_recipe_version_no: number
  version_no: number
  name: string
  spec: Record<string, unknown>
  output_sha256: string
  image_mime_type: string
  image_width_px: number
  image_height_px: number
  created_at: string
}

export type IeeeCitationReference = {
  number: number
  source_id: string
  reference: Record<string, unknown>
  reference_sha256: string
  ieee_text: string
  status: "METADATA_COMPLETE" | "INCOMPLETE_METADATA"
  missing_fields: string[]
}

export type IeeeCitationMark = {
  group_id: string
  block_id: string
  position: number
  source_ids: string[]
  occurrence_ids: string[]
  numbers: number[]
  citation_text: string
}

export type IeeeCitationView = {
  style: "IEEE"
  rendering_status: string
  document_revision_id: string
  document_revision_sha256: string
  citation_manifest_sha256: string
  marks: IeeeCitationMark[]
  references: IeeeCitationReference[]
  notice: string
}

export type CitationEvidenceReview = {
  review_id: string
  occurrence_id: string
  source_id: string
  source_identity: string
  source_text_status: string
  automated_semantic_assessment: string
  chapter_document_revision_id: string
  claim_text: string
  claim_sha256: string
  claim_range: { start: number; end: number }
  excerpt_id: number
  physical_page: number
  matched_text: string
  excerpt_range: { start: number; end: number }
  excerpt_sha256: string
  status: "CANDIDATE" | "SUPPORTS" | "CONTRADICTS" | "UNRELATED" | "INSUFFICIENT"
  review_version: number
  previous_review_id: string | null
  review_note: string
  created_by_id: number | string
  created_at: string
}

export type CitationReplacementProposal = {
  proposal_id: string
  occurrence_id: string
  document_revision_id: string
  expected_document_version: number
  replacement_source_id: string
  previous_reference: Record<string, unknown>
  replacement_reference: Record<string, unknown>
  previous_reference_sha256: string
  replacement_reference_sha256: string
  rationale: string
  decision: {
    status: "ACCEPTED" | "REJECTED"
    resulting_document_revision_id: string | null
    decided_by_id: number | string
    decided_at: string
    reason: string
  } | null
  preview?: {
    from: Record<string, unknown>
    to: Record<string, unknown>
    current_ieee_view: IeeeCitationView
    requires_explicit_acceptance: boolean
  }
}




