# Referencia técnica de restricciones, índices y campos

> **Estado verificado al 18/10/2026.** Refleja los 27 modelos de `backend/thesis/models/`. Para SQL histórico y operaciones exactas, consulte las 18 migraciones.

## Convenciones

- **Nulo:** corresponde a `null=True` en Django.
- **Único:** indica unicidad directa. Las unicidades compuestas o condicionales aparecen en restricciones.
- **Borrado FK:** política `on_delete` de cada relación.

## Identidad y acceso MCP

### `user`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `password` | CharField (max=128) | No | No | `—` | — |
| `last_login` | DateTimeField | Sí | No | `—` | — |
| `is_superuser` | BooleanField | No | No | `False` | — |
| `first_name` | CharField (max=150) | No | No | `—` | — |
| `last_name` | CharField (max=150) | No | No | `—` | — |
| `is_staff` | BooleanField | No | No | `False` | — |
| `is_active` | BooleanField | No | No | `True` | — |
| `date_joined` | DateTimeField | No | No | `now` | — |
| `email` | CharField (max=254) | No | Sí | `—` | — |
| `display_name` | CharField (max=150) | No | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

**Restricciones:**

- `user_email_lower_unique` · UniqueConstraint

### `mcp_access_token`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `token_hash` | CharField (max=64) | No | Sí | `—` | — |
| `user_id` | FK → user | No | No | `—` | CASCADE |
| `expires_at` | DateTimeField | No | No | `—` | — |
| `revoked_at` | DateTimeField | Sí | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

**Índices:**

- `mcp_token_user_expiry_idx`: `user`, `expires_at`

## Proyectos y participantes

### `project`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | UUIDField (max=32) | No | Sí | `uuid4` | — |
| `name` | CharField (max=160) | No | No | `—` | — |
| `title` | CharField (max=300) | No | No | `—` | — |
| `status` | CharField (max=12) | No | No | `Project.Status.ACTIVE` | — |
| `created_at` | DateTimeField | No | No | `—` | — |
| `updated_at` | DateTimeField | No | No | `—` | — |

**Enumeraciones:**

- `status`: `ACTIVE`, `ARCHIVED`.

**Índices:**

- `project_status_updated_idx`: `status`, `-updated_at`

### `project_participant`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `project_id` | FK → project | No | No | `—` | PROTECT |
| `user_id` | FK → user | No | No | `—` | PROTECT |
| `role` | CharField (max=10) | No | No | `—` | — |
| `active` | BooleanField | No | No | `True` | — |
| `joined_at` | DateTimeField | No | No | `—` | — |
| `left_at` | DateTimeField | Sí | No | `—` | — |

**Enumeraciones:**

- `role`: `OWNER`, `ADVISOR`.

**Restricciones:**

- `participant_project_user_unique` · UniqueConstraint · campos: `project`, `user`
- `participant_one_active_owner` · UniqueConstraint · campos: `project` · condición: `(AND: ('active', True), ('role', 'OWNER'))`
- `participant_one_active_advisor` · UniqueConstraint · campos: `project` · condición: `(AND: ('active', True), ('role', 'ADVISOR'))`
- `participant_active_dates_match` · CheckConstraint · condición: `(OR: (AND: ('active', True), ('left_at__isnull', True)), (AND: ('active', False), ('left_at__isnull', False)))`

**Índices:**

- `participant_user_role_idx`: `user`, `active`, `role`

## Perfil, consistencia y variables

### `research_profile`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `project_id` | OneToOne → project | No | Sí | `—` | PROTECT |
| `approach` | CharField (max=16) | Sí | No | `—` | — |
| `topic` | TextField | Sí | No | `—` | — |
| `ods_code` | CharField (max=20) | Sí | No | `—` | — |
| `unit_of_analysis` | TextField | Sí | No | `—` | — |
| `place` | TextField | Sí | No | `—` | — |
| `period_text` | CharField (max=120) | Sí | No | `—` | — |
| `problem_statement` | TextField | Sí | No | `—` | — |
| `schema_version` | PositiveSmallIntegerField | No | No | `1` | — |
| `lock_version` | PositiveIntegerField | No | No | `0` | — |
| `updated_at` | DateTimeField | No | No | `—` | — |

**Enumeraciones:**

- `approach`: `QUANTITATIVE`, `QUALITATIVE`, `MIXED`.

**Restricciones:**

- `research_profile_schema_version_positive` · CheckConstraint · condición: `(AND: ('schema_version__gte', 1))`
- `research_profile_valid_approach` · CheckConstraint · condición: `(OR: ('approach__isnull', True), ('approach__in', ['QUANTITATIVE', 'QUALITATIVE', 'MIXED']))`

### `consistency_row`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `project_id` | FK → project | No | No | `—` | PROTECT |
| `ordinal` | PositiveSmallIntegerField | No | No | `—` | — |
| `question_text` | TextField | Sí | No | `—` | — |
| `objective_text` | TextField | Sí | No | `—` | — |
| `hypothesis_text` | TextField | Sí | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |
| `updated_at` | DateTimeField | No | No | `—` | — |

**Restricciones:**

- `consistency_row_project_ordinal_unique` · UniqueConstraint · campos: `project`, `ordinal`

### `research_variable`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `project_id` | FK → project | No | No | `—` | PROTECT |
| `role` | CharField (max=16) | No | No | `—` | — |
| `name` | CharField (max=200) | No | No | `—` | — |
| `conceptual_definition` | TextField | Sí | No | `—` | — |
| `operational_definition` | TextField | Sí | No | `—` | — |
| `ordinal` | PositiveSmallIntegerField | No | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |
| `updated_at` | DateTimeField | No | No | `—` | — |

**Enumeraciones:**

- `role`: `INDEPENDENT`, `DEPENDENT`, `OTHER`.

**Restricciones:**

- `research_variable_project_ordinal_unique` · UniqueConstraint · campos: `project`, `ordinal`
- `research_variable_ordinal_positive` · CheckConstraint · condición: `(AND: ('ordinal__gte', 1))`
- `research_variable_valid_role` · CheckConstraint · condición: `(AND: ('role__in', ['INDEPENDENT', 'DEPENDENT', 'OTHER']))`

**Índices:**

- `research_var_project_role_idx`: `project`, `role`

### `consistency_row_variable`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `consistency_row_id` | FK → consistency_row | No | No | `—` | PROTECT |
| `variable_id` | FK → research_variable | No | No | `—` | PROTECT |
| `created_at` | DateTimeField | No | No | `—` | — |

**Restricciones:**

- `consistency_row_variable_unique` · UniqueConstraint · campos: `consistency_row`, `variable`

### `variable_dimension`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `variable_id` | FK → research_variable | No | No | `—` | PROTECT |
| `ordinal` | PositiveSmallIntegerField | No | No | `—` | — |
| `name` | CharField (max=200) | No | No | `—` | — |
| `definition` | TextField | Sí | No | `—` | — |

**Restricciones:**

- `variable_dimension_var_ordinal_unique` · UniqueConstraint · campos: `variable`, `ordinal`
- `variable_dimension_ordinal_positive` · CheckConstraint · condición: `(AND: ('ordinal__gte', 1))`

### `indicator`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `dimension_id` | FK → variable_dimension | No | No | `—` | PROTECT |
| `ordinal` | PositiveSmallIntegerField | No | No | `—` | — |
| `name` | CharField (max=200) | No | No | `—` | — |
| `measurement_scale` | CharField (max=30) | Sí | No | `—` | — |
| `technique` | CharField (max=120) | Sí | No | `—` | — |
| `operational_rule` | TextField | Sí | No | `—` | — |

**Restricciones:**

- `indicator_dim_ordinal_unique` · UniqueConstraint · campos: `dimension`, `ordinal`
- `indicator_ordinal_positive` · CheckConstraint · condición: `(AND: ('ordinal__gte', 1))`

## Instrumentos

### `instrument`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | UUIDField (max=32) | No | Sí | `uuid4` | — |
| `project_id` | FK → project | No | No | `—` | PROTECT |
| `lineage_key` | UUIDField (max=32) | No | No | `uuid4` | — |
| `version_no` | PositiveIntegerField | No | No | `1` | — |
| `name` | CharField (max=200) | No | No | `—` | — |
| `kind` | CharField (max=16) | No | No | `—` | — |
| `target_population` | TextField | Sí | No | `—` | — |
| `status` | CharField (max=12) | No | No | `Instrument.Status.DRAFT` | — |
| `approved_by_id` | FK → user | Sí | No | `—` | PROTECT |
| `approved_at` | DateTimeField | Sí | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

**Enumeraciones:**

- `kind`: `QUESTIONNAIRE`, `INTERVIEW`, `FOCUS_GROUP`.
- `status`: `DRAFT`, `APPROVED`.

**Restricciones:**

- `instrument_proj_lineage_ver_uk` · UniqueConstraint · campos: `project`, `lineage_key`, `version_no`
- `instrument_version_positive` · CheckConstraint · condición: `(AND: ('version_no__gt', 0))`
- `instrument_valid_kind` · CheckConstraint · condición: `(AND: ('kind__in', ['QUESTIONNAIRE', 'INTERVIEW', 'FOCUS_GROUP']))`
- `instrument_approval_fields` · CheckConstraint · condición: `(OR: (AND: ('approved_at__isnull', True), ('approved_by__isnull', True), ('status', 'DRAFT')), (AND: ('approved_at__isnull', False), ('approved_by__isnull', False), ('status', 'APPROVED')))`

### `instrument_item`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `instrument_id` | FK → instrument | No | No | `—` | PROTECT |
| `dimension_id` | FK → variable_dimension | Sí | No | `—` | PROTECT |
| `ordinal` | PositiveSmallIntegerField | No | No | `—` | — |
| `prompt_text` | TextField | No | No | `—` | — |
| `response_scale` | CharField (max=120) | Sí | No | `—` | — |
| `probe_text` | TextField | Sí | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

**Restricciones:**

- `instrument_item_inst_ord_uk` · UniqueConstraint · campos: `instrument`, `ordinal`
- `instrument_item_valid` · CheckConstraint · condición: `(AND: ('ordinal__gte', 1), (NOT (AND: ('prompt_text', ''))))`

### `instrument_item_indicator`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `instrument_item_id` | FK → instrument_item | No | No | `—` | PROTECT |
| `indicator_id` | FK → indicator | No | No | `—` | PROTECT |
| `created_at` | DateTimeField | No | No | `—` | — |

**Restricciones:**

- `inst_item_indicator_unique` · UniqueConstraint · campos: `instrument_item`, `indicator`

## Pasos, capítulos y revisión

### `step_progress`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `project_id` | FK → project | No | No | `—` | PROTECT |
| `step_code` | CharField (max=3) | No | No | `—` | — |
| `status` | CharField (max=16) | No | No | `StepProgress.Status.IN_PROGRESS` | — |
| `output_json` | JSONField | No | No | `dict` | — |
| `completed_at` | DateTimeField | Sí | No | `—` | — |
| `updated_at` | DateTimeField | No | No | `—` | — |

**Enumeraciones:**

- `status`: `IN_PROGRESS`, `COMPLETED`.

**Restricciones:**

- `step_project_code_unique` · UniqueConstraint · campos: `project`, `step_code`

### `chapter`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `project_id` | FK → project | No | No | `—` | PROTECT |
| `number` | PositiveSmallIntegerField | No | No | `—` | — |
| `status` | CharField (max=50) | No | No | `Chapter.Status.DRAFT` | — |
| `approved_revision_id` | FK → chapter_revision | Sí | No | `—` | PROTECT |
| `approved_at` | DateTimeField | Sí | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |
| `updated_at` | DateTimeField | No | No | `—` | — |

**Enumeraciones:**

- `status`: `DRAFT`, `READY`, `CHANGES_REQUESTED`, `APPROVED`.

**Restricciones:**

- `chapter_project_number_unique` · UniqueConstraint · campos: `project`, `number`
- `chapter_number_range` · CheckConstraint · condición: `(AND: ('number__gte', 1), ('number__lte', 7))`

### `chapter_revision`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `chapter_id` | FK → chapter | No | No | `—` | PROTECT |
| `revision_no` | PositiveIntegerField | No | No | `—` | — |
| `step_code` | CharField (max=3) | No | No | `—` | — |
| `idempotency_key` | UUIDField (max=32) | No | No | `—` | — |
| `content_md` | TextField | No | No | `—` | — |
| `content_sha256` | CharField (max=64) | No | No | `—` | — |
| `created_by_id` | FK → user | No | No | `—` | PROTECT |
| `created_at` | DateTimeField | No | No | `—` | — |

**Restricciones:**

- `revision_chapter_number_unique` · UniqueConstraint · campos: `chapter`, `revision_no`
- `revision_chapter_key_unique` · UniqueConstraint · campos: `chapter`, `idempotency_key`
- `revision_positive_number` · CheckConstraint · condición: `(AND: ('revision_no__gt', 0))`
- `revision_nonempty_content` · CheckConstraint · condición: `(NOT (AND: ('content_md', '')))`

### `review_comment`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `revision_id` | FK → chapter_revision | No | No | `—` | PROTECT |
| `author_id` | FK → user | No | No | `—` | PROTECT |
| `start_cp` | PositiveIntegerField | No | No | `—` | — |
| `end_cp` | PositiveIntegerField | No | No | `—` | — |
| `selected_text` | TextField | No | No | `—` | — |
| `body` | TextField | No | No | `—` | — |
| `status` | CharField (max=10) | No | No | `ReviewComment.Status.OPEN` | — |
| `resolved_by_id` | FK → user | Sí | No | `—` | PROTECT |
| `resolved_at` | DateTimeField | Sí | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

**Enumeraciones:**

- `status`: `OPEN`, `RESOLVED`.

**Restricciones:**

- `comment_positive_range` · CheckConstraint · condición: `(AND: ('end_cp__gt', F(start_cp)))`

**Índices:**

- `review_comment_status_idx`: `revision`, `status`, `created_at`

### `review_event`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `chapter_id` | FK → chapter | No | No | `—` | PROTECT |
| `revision_id` | FK → chapter_revision | Sí | No | `—` | PROTECT |
| `actor_id` | FK → user | No | No | `—` | PROTECT |
| `action` | CharField (max=20) | No | No | `—` | — |
| `reason` | TextField | No | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

**Enumeraciones:**

- `action`: `SUBMIT`, `REQUEST_CHANGES`, `APPROVE`, `REOPEN`.

**Índices:**

- `review_event_chapter_idx`: `chapter`, `created_at`

## Fuentes y evidencia

### `source_document`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | UUIDField (max=32) | No | Sí | `uuid4` | — |
| `project_id` | FK → project | No | No | `—` | PROTECT |
| `kind` | CharField (max=10) | No | No | `SourceDocument.Kind.EXTERNAL` | — |
| `openalex_id` | CharField (max=255) | Sí | No | `—` | — |
| `title` | TextField | No | No | `—` | — |
| `authors_json` | JSONField | No | No | `list` | — |
| `publication_year` | PositiveSmallIntegerField | Sí | No | `—` | — |
| `doi` | CharField (max=255) | Sí | No | `—` | — |
| `url` | CharField (max=2048) | Sí | No | `—` | — |
| `pdf_url` | CharField (max=2048) | Sí | No | `—` | — |
| `openalex_retracted` | BooleanField | Sí | No | `—` | — |
| `storage_key` | CharField (max=500) | Sí | No | `—` | — |
| `sha256` | CharField (max=64) | Sí | No | `—` | — |
| `derived_storage_key` | CharField (max=500) | Sí | No | `—` | — |
| `derived_sha256` | CharField (max=64) | Sí | No | `—` | — |
| `extraction_method` | CharField (max=10) | Sí | No | `—` | — |
| `mime_type` | CharField (max=100) | Sí | No | `—` | — |
| `page_count` | PositiveIntegerField | Sí | No | `—` | — |
| `verification_status` | CharField (max=20) | No | No | `SourceDocument.Status.METADATA_CHECKED` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

**Enumeraciones:**

- `kind`: `EXTERNAL`, `UPLOAD`.
- `extraction_method`: `POPPLER`, `OCR`.
- `verification_status`: `PENDING_EXTRACTION`, `METADATA_CHECKED`, `UNVERIFIED_METADATA`, `TEXT_CHECKED`, `OCR_REQUIRED`, `REJECTED`. `UNVERIFIED_METADATA` se usa para importaciones/selecciones remitidas por usuario sin cotejo con el proveedor.

**Restricciones:**

- `source_project_openalex_unique` · UniqueConstraint · campos: `project`, `openalex_id` · condición: `(AND: ('openalex_id__isnull', False))`
- `source_project_sha_unique` · UniqueConstraint · campos: `project`, `sha256` · condición: `(AND: ('sha256__isnull', False))`
- `source_positive_pages` · CheckConstraint · condición: `(OR: ('page_count__isnull', True), ('page_count__gt', 0))`
- `source_kind_payload` · CheckConstraint · condición: `(OR: (AND: ('kind', 'EXTERNAL'), ('openalex_id__isnull', False)), (AND: ('kind', 'UPLOAD'), ('sha256__isnull', False), ('storage_key__isnull', False)))`

**Índices:**

- `source_project_status_idx`: `project`, `verification_status`

### `source_excerpt`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `source_id` | FK → source_document | No | No | `—` | CASCADE |
| `chunk_no` | PositiveIntegerField | No | No | `—` | — |
| `page_no` | PositiveIntegerField | No | No | `—` | — |
| `text` | TextField | No | No | `—` | — |
| `text_sha256` | CharField (max=64) | No | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

**Restricciones:**

- `excerpt_source_chunk_unique` · UniqueConstraint · campos: `source`, `chunk_no`
- `excerpt_positive_location` · CheckConstraint · condición: `(AND: ('chunk_no__gt', 0), ('page_no__gt', 0))`
- `excerpt_nonempty_text` · CheckConstraint · condición: `(NOT (AND: ('text', '')))`

**Índices:**

- `excerpt_source_page_idx`: `source`, `page_no`, `chunk_no`

### `source_passage`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `excerpt_id` | FK → source_excerpt | No | No | `—` | CASCADE |
| `start_char` | PositiveIntegerField | No | No | `—` | — |
| `text` | TextField | No | No | `—` | — |
| `text_sha256` | CharField (max=64) | No | No | `—` | — |
| `embedding` | VectorField (dim=384) | No | No | `—` | — |
| `embedding_model` | CharField (max=160) | No | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

**Restricciones:**

- `passage_excerpt_start_unique` · UniqueConstraint · campos: `excerpt`, `start_char`

### `source_grobid_analysis`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `source_id` | OneToOne → source_document | No | Sí | `—` | CASCADE |
| `input_sha256` | CharField (max=64) | No | No | `—` | — |
| `tei_sha256` | CharField (max=64) | No | No | `—` | — |
| `tei_xml` | TextField | No | No | `—` | — |
| `extracted_title` | TextField | No | No | `—` | — |
| `extracted_authors_json` | JSONField | No | No | `list` | — |
| `references_json` | JSONField | No | No | `list` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

### `source_metadata_check`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `source_id` | OneToOne → source_document | No | Sí | `—` | PROTECT |
| `doi` | CharField (max=255) | No | No | `—` | — |
| `registry` | CharField (max=20) | No | No | `'CROSSREF'` | — |
| `registered_title` | TextField | No | No | `—` | — |
| `registered_authors_json` | JSONField | No | No | `list` | — |
| `title_similarity` | FloatField | Sí | No | `—` | — |
| `registry_record_json` | JSONField | No | No | `dict` | — |
| `checked_at` | DateTimeField | No | No | `—` | — |

### `evidence_link`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `project_id` | FK → project | No | No | `—` | PROTECT |
| `revision_id` | FK → chapter_revision | Sí | No | `—` | PROTECT |
| `excerpt_id` | FK → source_excerpt | No | No | `—` | PROTECT |
| `claim_text` | TextField | No | No | `—` | — |
| `start_char` | PositiveIntegerField | No | No | `—` | — |
| `end_char` | PositiveIntegerField | No | No | `—` | — |
| `matched_text` | TextField | No | No | `—` | — |
| `excerpt_sha256` | CharField (max=64) | No | No | `—` | — |
| `status` | CharField (max=10) | No | No | `EvidenceLink.Status.CANDIDATE` | — |
| `created_by_id` | FK → user | No | No | `—` | PROTECT |
| `reviewed_by_id` | FK → user | Sí | No | `—` | PROTECT |
| `review_note` | TextField | No | No | `—` | — |
| `reviewed_at` | DateTimeField | Sí | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

**Enumeraciones:**

- `status`: `CANDIDATE`, `CONFIRMED`, `REJECTED`.

**Restricciones:**

- `evidence_positive_range` · CheckConstraint · condición: `(AND: ('end_char__gt', F(start_char)))`

**Índices:**

- `evidence_project_status_idx`: `project`, `status`

## Trabajos documentales y manuscritos

### `document_job`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | UUIDField (max=32) | No | Sí | `uuid4` | — |
| `project_id` | FK → project | No | No | `—` | PROTECT |
| `source_id` | FK → source_document | Sí | No | `—` | PROTECT |
| `manuscript_id` | FK → manuscript_document | Sí | No | `—` | PROTECT |
| `requested_by_id` | FK → user | No | No | `—` | PROTECT |
| `kind` | CharField (max=16) | No | No | `—` | — |
| `status` | CharField (max=10) | No | No | `DocumentJob.Status.QUEUED` | — |
| `attempts` | PositiveSmallIntegerField | No | No | `0` | — |
| `result_json` | JSONField | Sí | No | `—` | — |
| `error_code` | CharField (max=40) | No | No | `—` | — |
| `error_message` | TextField | No | No | `—` | — |
| `created_at` | DateTimeField | No | No | `—` | — |
| `started_at` | DateTimeField | Sí | No | `—` | — |
| `finished_at` | DateTimeField | Sí | No | `—` | — |

**Enumeraciones:**

- `kind`: `GROBID`, `INDEX`, `OCR`, `DOI_CHECK`, `DOCX`, `PDF_EXTRACT`, `OPENALEX_PDF`.
- `status`: `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`.

**Restricciones:**

- `document_job_one_active_source_kind` · UniqueConstraint · campos: `source`, `kind` · condición: `(AND: ('source__isnull', False), ('status__in', ['QUEUED', 'RUNNING']))`
- `document_job_one_active_manuscript` · UniqueConstraint · campos: `manuscript`, `kind` · condición: `(AND: ('manuscript__isnull', False), ('status__in', ['QUEUED', 'RUNNING']))`
- `document_job_single_target` · CheckConstraint · condición: `(OR: (AND: ('manuscript__isnull', True), ('source__isnull', False)), (AND: ('manuscript__isnull', False), ('source__isnull', True)))`

**Índices:**

- `document_job_queue_idx`: `status`, `created_at`

### `manuscript_document`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | UUIDField (max=32) | No | Sí | `uuid4` | — |
| `project_id` | FK → project | No | No | `—` | PROTECT |
| `label` | CharField (max=300) | No | No | `—` | — |
| `storage_key` | CharField (max=500) | No | No | `—` | — |
| `sha256` | CharField (max=64) | No | No | `—` | — |
| `markdown` | TextField | No | No | `—` | — |
| `processing_status` | CharField (max=10) | No | No | `ManuscriptDocument.ProcessingStatus.READY` | — |
| `created_at` | DateTimeField | No | No | `—` | — |

**Enumeraciones:**

- `processing_status`: `QUEUED`, `READY`, `FAILED`.

**Restricciones:**

- `manuscript_project_sha_unique` · UniqueConstraint · campos: `project`, `sha256`

### `manuscript_citation`

| Campo | Tipo / relación | Nulo | Único | Default | Borrado FK |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `id` | BigAutoField | No | Sí | `—` | — |
| `manuscript_id` | FK → manuscript_document | No | No | `—` | CASCADE |
| `kind` | CharField (max=10) | No | No | `—` | — |
| `part_name` | CharField (max=100) | No | No | `—` | — |
| `paragraph_index` | PositiveIntegerField | No | No | `—` | — |
| `display_text` | TextField | No | No | `—` | — |
| `field_code` | TextField | No | No | `—` | — |
| `citation_items` | JSONField | No | No | `list` | — |

**Enumeraciones:**

- `kind`: `WORD`, `ZOTERO`.

**Índices:**

- `citation_manuscript_loc_idx`: `manuscript`, `part_name`, `paragraph_index`

## Reglas fuera del esquema SQL

| Operación | Garantía aplicada por el servicio |
| :--- | :--- |
| Guardar paso | Permiso por proyecto, prerrequisitos P01–P32, contrato Pydantic estricto, transacción, bloqueo y `lock_version`. |
| Crear revisión | Número secuencial, hash del contenido e idempotencia por capítulo. |
| Enviar capítulo | Revisión vigente y pasos requeridos completos. |
| Aprobar | Actor asesor, revisión vigente y ausencia de comentarios `OPEN`. |
| P16 | Fuente del proyecto con texto extraído, conteo físico, archivo/hash y tres citas literales localizadas. |
| P20 | `estilo_citacion` es `IEEE` o `APA_7` y cantidad de referencias no menor que los estudios de P16. |
| P32 | Rango contractual del coeficiente; no hay recálculo desde observaciones crudas. |

## Orden de migraciones

Las migraciones propias se aplican en orden `0001`–`0018`.

```bash
DJANGO_DEBUG=1 .venv/bin/python backend/manage.py makemigrations --check --dry-run
```
