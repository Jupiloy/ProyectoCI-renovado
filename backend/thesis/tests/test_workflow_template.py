import pytest
from django.contrib.auth import get_user_model
from thesis.models import Project, ProjectWorkflow, WorkflowTask, WorkflowDependency, WorkflowPrompt
from thesis.services.projects import create_project
from thesis.services.workflow_template import (
    calculate_workflow_hash,
    detect_workflow_cycles,
    initialize_project_workflow,
    workflow_content_dump,
)


def test_detect_workflow_cycles():
    # Linear graph: P01 -> P02 -> P03 (no cycles)
    tasks = ["P01", "P02", "P03"]
    deps = [
        {"source": "P02", "target": "P01"},
        {"source": "P03", "target": "P02"},
    ]
    cycles = detect_workflow_cycles(tasks, deps)
    assert cycles == []

    # Cyclic graph: P01 -> P02 -> P03 -> P01
    deps_cyclic = [
        {"source": "P02", "target": "P01"},
        {"source": "P03", "target": "P02"},
        {"source": "P01", "target": "P03"},
    ]
    cycles = detect_workflow_cycles(tasks, deps_cyclic)
    assert len(cycles) > 0
    assert "P01" in cycles or "P02" in cycles


@pytest.mark.django_db
def test_initialize_project_workflow():
    User = get_user_model()
    user = User.objects.create_user(email="tpl-test@example.org", password="pass")
    project = create_project(user, "Tesis Template Test")

    wf = initialize_project_workflow(project, user)
    assert wf.project == project
    assert wf.status == ProjectWorkflow.Status.PUBLISHED
    assert wf.version_no == 1
    assert len(wf.content_sha256) == 64

    # El esquema de salida forma parte del contenido íntegro versionado.
    original_hash = wf.content_sha256
    task = WorkflowTask.objects.get(workflow=wf, task_id="P01")
    task.output_schema = {"type": "object", "properties": {"x": {"type": "string"}}}
    task.save(update_fields=["output_schema"])
    tasks_dump, deps_dump, prompts_dump = workflow_content_dump(wf)
    assert calculate_workflow_hash(tasks_dump, deps_dump, prompts_dump) != original_hash

    # 32 tasks
    tasks = WorkflowTask.objects.filter(workflow=wf)
    assert tasks.count() == 32

    # Check protected tasks
    protected_ids = set(tasks.filter(is_protected=True).values_list("task_id", flat=True))
    assert {"P04", "P16", "P20", "P28"} <= protected_ids

    # Check prompts
    prompts = WorkflowPrompt.objects.filter(task__workflow=wf)
    assert prompts.count() == 32
    p01_prompt = prompts.get(task__task_id="P01")
    assert "P01" in p01_prompt.prompt_text or "temas" in p01_prompt.prompt_text.lower()
    p20_prompt = prompts.get(task__task_id="P20")
    assert "IEEE" in p20_prompt.prompt_text

    # Check dependencies exist
    deps = WorkflowDependency.objects.filter(workflow=wf)
    assert deps.count() >= 25
    p06_deps = deps.filter(source_task__task_id="P06")
    assert any(d.target_task.task_id == "P04" for d in p06_deps)
