import pytest
from django.contrib.auth import get_user_model
from thesis.models import (
    Project,
    ResearchProfile,
    ProjectWorkflow,
    WorkflowTask,
    WorkflowDependency,
    WorkflowPrompt,
    Chapter,
    ChapterRevision,
    StepProgress,
)
from thesis.services.projects import create_project


@pytest.mark.django_db
def test_create_workflow_models_and_profile_integration():
    User = get_user_model()
    user = User.objects.create_user(email="wf-test@example.org", password="pass")
    project = create_project(user, "Proyecto Configurable")

    # Verify ResearchProfile defaults to LEGACY_SEQUENTIAL
    profile = ResearchProfile.objects.get(project=project)
    assert profile.workflow_mode == "LEGACY_SEQUENTIAL"
    assert profile.active_workflow is None

    # Create a draft workflow
    wf = ProjectWorkflow.objects.create(
        project=project,
        version_no=1,
        status=ProjectWorkflow.Status.DRAFT,
        base_template_version="catalogo_p01_p32_v1",
        change_summary="Versión inicial borrador",
        content_sha256="abc" * 21 + "a",
        created_by=user,
    )
    assert wf.pk is not None
    assert wf.status == "DRAFT"

    # Create tasks
    task1 = WorkflowTask.objects.create(
        workflow=wf,
        task_id="P01",
        legacy_step_code="P01",
        title="Mapa de temas viables",
        chapter_no=1,
        order_index=1,
        is_active=True,
        is_optional=False,
        is_protected=True,
        contract_name="P01Output",
    )
    task2 = WorkflowTask.objects.create(
        workflow=wf,
        task_id="P02",
        legacy_step_code="P02",
        title="Matriz de factibilidad",
        chapter_no=1,
        order_index=2,
        is_active=True,
        is_optional=False,
        contract_name="P02Output",
    )

    # Create dependency: P01 -> P02
    dep = WorkflowDependency.objects.create(
        workflow=wf,
        source_task=task2,
        target_task=task1,
        dependency_type=WorkflowDependency.Type.DATA_REQUIRED,
        is_blocking=True,
        reason="P02 requiere temas preseleccionados de P01",
    )
    assert dep.pk is not None

    # Create prompt
    prompt = WorkflowPrompt.objects.create(
        task=task1,
        prompt_text="Instrucciones para generar temas viables",
        prompt_version=1,
        provenance=WorkflowPrompt.Provenance.BASE_CATALOG,
        created_by=user,
    )
    assert prompt.pk is not None

    # Link workflow to profile and test chapter revision link
    profile.workflow_mode = "CONFIGURABLE_GRAPH"
    profile.active_workflow = wf
    profile.save()

    chapter = Chapter.objects.create(project=project, number=1)
    revision = ChapterRevision.objects.create(
        chapter=chapter,
        revision_no=1,
        step_code="P01",
        idempotency_key="11111111-1111-1111-1111-111111111111",
        content_md="# Borrador",
        content_sha256="def" * 21 + "d",
        created_by=user,
        workflow=wf,
        workflow_version_no=1,
        prompt_text_used=prompt.prompt_text,
    )
    assert revision.workflow == wf
    assert revision.workflow_version_no == 1
    assert revision.prompt_text_used == "Instrucciones para generar temas viables"

    step_prog = StepProgress.objects.create(
        project=project,
        step_code="P01",
        task_id="P01",
        status=StepProgress.Status.COMPLETED,
        output_json={},
        workflow=wf,
        workflow_version_no=1,
    )
    assert step_prog.workflow == wf
    assert step_prog.task_id == "P01"
