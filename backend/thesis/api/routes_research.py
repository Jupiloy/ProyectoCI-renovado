"""Rutas de research; registradas en el router compartido."""

from uuid import UUID
from django.http import FileResponse
from ninja import File, Form, Status, UploadedFile
from thesis.services.research_data import add_dataset_version, create_dataset, get_dataset_file, get_dataset_version, list_dataset_versions, list_datasets
from thesis.services.research_tables import create_table_recipe, get_table_recipe_version, list_table_recipe_versions, list_table_recipes
from thesis.services.research_figures import create_figure, get_figure_preview, get_figure_version, list_figure_versions, list_figures
from .schemas import ResearchFigureIn, TableRecipeIn
from .routers import router


@router.post("/{project_id}/datasets", response={201: dict}, operation_id="thesis_api_projects_create_research_dataset")
def create_research_dataset(request, project_id: UUID, name: Form[str], file: File[UploadedFile],
                            idempotency_key: Form[str], description: Form[str] = "",
                            sheet_name: Form[str] = ""):
    result = create_dataset(request.user, project_id, name, file, idempotency_key,
                            description=description, sheet_name=sheet_name or None)
    return Status(201 if result["created"] else 200, result)


@router.get("/{project_id}/datasets", operation_id="thesis_api_projects_research_datasets")
def research_datasets(request, project_id: UUID):
    return list_datasets(request.user, project_id)


@router.post("/{project_id}/datasets/{dataset_id}/versions", response={201: dict}, operation_id="thesis_api_projects_add_research_dataset_version")
def add_research_dataset_version(request, project_id: UUID, dataset_id: UUID,
                                 expected_version: Form[int], idempotency_key: Form[str],
                                 file: File[UploadedFile], sheet_name: Form[str] = ""):
    result = add_dataset_version(request.user, project_id, dataset_id, file, idempotency_key,
                                 expected_version, sheet_name=sheet_name or None)
    return Status(201 if result["created"] else 200, result)


@router.get("/{project_id}/datasets/{dataset_id}/versions", operation_id="thesis_api_projects_research_dataset_versions")
def research_dataset_versions(request, project_id: UUID, dataset_id: UUID):
    return list_dataset_versions(request.user, project_id, dataset_id)


@router.get("/{project_id}/datasets/{dataset_id}/versions/{version_no}", operation_id="thesis_api_projects_research_dataset_version")
def research_dataset_version(request, project_id: UUID, dataset_id: UUID, version_no: int):
    return get_dataset_version(request.user, project_id, dataset_id, version_no)


@router.get("/{project_id}/datasets/{dataset_id}/versions/{version_no}/download", operation_id="thesis_api_projects_download_research_dataset_version")
def download_research_dataset_version(request, project_id: UUID, dataset_id: UUID, version_no: int):
    version, path = get_dataset_file(request.user, project_id, dataset_id, version_no)
    return FileResponse(path.open("rb"), as_attachment=True, filename=version.original_filename)


@router.post("/{project_id}/datasets/{dataset_id}/versions/{version_no}/table-recipes",
             response={201: dict, 200: dict}, operation_id="thesis_api_projects_create_research_table_recipe")
def create_research_table_recipe(request, project_id: UUID, dataset_id: UUID, version_no: int,
                                 payload: TableRecipeIn):
    result = create_table_recipe(
        request.user, project_id, dataset_id, version_no, payload.name, payload.spec,
        payload.idempotency_key, payload.expected_version,
    )
    return Status(201 if result["created"] else 200, result)


@router.get("/{project_id}/datasets/{dataset_id}/versions/{version_no}/table-recipes", operation_id="thesis_api_projects_research_table_recipes")
def research_table_recipes(request, project_id: UUID, dataset_id: UUID, version_no: int):
    return list_table_recipes(request.user, project_id, dataset_id, version_no)


@router.get("/{project_id}/datasets/{dataset_id}/table-recipes/{recipe_id}/versions", operation_id="thesis_api_projects_research_table_recipe_versions")
def research_table_recipe_versions(request, project_id: UUID, dataset_id: UUID, recipe_id: UUID):
    return list_table_recipe_versions(request.user, project_id, dataset_id, recipe_id)


@router.get("/{project_id}/datasets/{dataset_id}/table-recipes/{recipe_id}/versions/{version_no}", operation_id="thesis_api_projects_research_table_recipe_version")
def research_table_recipe_version(request, project_id: UUID, dataset_id: UUID, recipe_id: UUID,
                                  version_no: int):
    return get_table_recipe_version(request.user, project_id, dataset_id, recipe_id, version_no)


@router.post("/{project_id}/datasets/{dataset_id}/table-recipes/{recipe_id}/versions/{table_version_no}/figures",
             response={201: dict, 200: dict}, operation_id="thesis_api_projects_create_research_figure")
def create_research_figure(request, project_id: UUID, dataset_id: UUID, recipe_id: UUID,
                           table_version_no: int, payload: ResearchFigureIn):
    result = create_figure(
        request.user, project_id, dataset_id, recipe_id, table_version_no, payload.name,
        payload.spec, payload.idempotency_key, payload.expected_version, payload.accept_truncated_input,
    )
    return Status(201 if result["created"] else 200, result)


@router.get("/{project_id}/datasets/{dataset_id}/table-recipes/{recipe_id}/versions/{table_version_no}/figures", operation_id="thesis_api_projects_research_figures")
def research_figures(request, project_id: UUID, dataset_id: UUID, recipe_id: UUID, table_version_no: int):
    return list_figures(request.user, project_id, dataset_id, recipe_id, table_version_no)


@router.get("/{project_id}/datasets/{dataset_id}/figures/{figure_id}/versions", operation_id="thesis_api_projects_research_figure_versions")
def research_figure_versions(request, project_id: UUID, dataset_id: UUID, figure_id: UUID):
    return list_figure_versions(request.user, project_id, dataset_id, figure_id)


@router.get("/{project_id}/datasets/{dataset_id}/figures/{figure_id}/versions/{version_no}", operation_id="thesis_api_projects_research_figure_version")
def research_figure_version(request, project_id: UUID, dataset_id: UUID, figure_id: UUID, version_no: int):
    return get_figure_version(request.user, project_id, dataset_id, figure_id, version_no)


@router.get("/{project_id}/datasets/{dataset_id}/figures/{figure_id}/versions/{version_no}/preview.png", operation_id="thesis_api_projects_research_figure_preview")
def research_figure_preview(request, project_id: UUID, dataset_id: UUID, figure_id: UUID, version_no: int):
    path = get_figure_preview(request.user, project_id, dataset_id, figure_id, version_no)
    return FileResponse(path.open("rb"), content_type="image/png", filename=path.name)
