from ninja import NinjaAPI
from ninja.security import django_auth

from thesis.services.errors import DomainError
from thesis.api.projects import integrations_router, router as projects_router

api = NinjaAPI(title="TesisMCP", version="1.0.0", auth=django_auth)
api.add_router("/projects", projects_router)
api.add_router("/integrations", integrations_router)


@api.exception_handler(DomainError)
def domain_error_response(request, exc: DomainError):
    status = {
        "VALIDATION_ERROR": 400,
        "INVALID_DATASET": 400,
        "DATASET_TOO_LARGE": 413,
        "OUTPUT_TOO_LARGE": 413,
        "EMPTY_RESULT": 422,
        "NOT_FOUND": 404,
        "PROJECT_ARCHIVED": 409,
        "VERSION_CONFLICT": 409,
        "SEARCH_UNAVAILABLE": 502,
        "PDF_UNREADABLE": 400,
        "OCR_UNAVAILABLE": 503,
        "OCR_FAILED": 422,
        "DOCX_UNREADABLE": 422,
        "DOCX_UNAVAILABLE": 503,
        "GROBID_UNAVAILABLE": 503,
        "GROBID_FAILED": 422,
        "EMBEDDING_UNAVAILABLE": 503,
        "REGISTRY_UNAVAILABLE": 502,
        "VALIDATION_SCHEMA_ERROR": 422,
        "RULE_WORD_COUNT_EXCEEDED": 400,
        "RULE_QUESTION_FORMAT": 400,
        "PREREQUISITE_LOCKED": 422,
        "ADVISOR_UNRESOLVED_COMMENTS": 412,
        "PERMISSION_DENIED": 403,
        "PROMPT_NOT_CONFIGURED": 422,
        "OUTPUT_INVALID": 422,
        "TRUNCATED_INPUT_CONFIRMATION_REQUIRED": 422,
        "FIGURE_TOO_MANY_POINTS": 422,
        "FIGURE_RENDERER_UNAVAILABLE": 503,
        "ARTIFACT_NOT_FOUND": 404,
        "ARTIFACT_HASH_MISMATCH": 422,
        "ARTIFACT_UNAVAILABLE": 422,
        "ARTIFACT_MANIFEST_INVALID": 422,
        "PROVIDER_UNAVAILABLE": 503,
        "PROVIDER_TIMEOUT": 504,
        "PROVIDER_RATE_LIMITED": 429,
        "CONTEXT_STALE": 409,
        "JOB_NOT_CANCELLABLE": 409,
        "IDEMPOTENCY_CONFLICT": 409,
        "BATCH_DEPENDENCY_CONFLICT": 422,
        "ASYNC_GENERATION_REQUIRED": 503,
    }.get(exc.code, 500)
    return api.create_response(request, {"detail": f"{exc.code}: {exc.message}"}, status=status)
