from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from thesis.models import Project, ProjectWorkflow, WorkflowTask, ResearchProfile
from thesis.services.projects import create_project
from thesis.services.errors import DomainError
from thesis.services.workflows import (
    get_workflow_state,
    create_or_update_draft,
    validate_workflow_draft,
    publish_workflow_draft,
    restore_workflow_version,
    get_effective_prompt,
    execute_custom_workflow_task,
    get_custom_workflow_task_executions,
)


@pytest.fixture
def wf_setup(db):
    User = get_user_model()
    owner = User.objects.create_user(email="wf-owner@example.org", password="pass")
    advisor = User.objects.create_user(email="wf-advisor@example.org", password="pass")
    outsider = User.objects.create_user(email="wf-outsider@example.org", password="pass")
    project = create_project(owner, "Proyecto Workflow Test")
    from thesis.services.reviews import assign_advisor
    assign_advisor(owner, project.id, advisor.email)
    return owner, advisor, outsider, project


def test_get_workflow_state_initializes_and_enforces_permissions(wf_setup):
    owner, advisor, outsider, project = wf_setup

    # Outsider is denied with NOT_FOUND
    with pytest.raises(DomainError) as exc:
        get_workflow_state(outsider, project.id)
    assert exc.value.code == "NOT_FOUND"

    # Owner can get state (lazily initializes base published workflow v1)
    state = get_workflow_state(owner, project.id)
    assert state["project_id"] == str(project.id)
    assert state["published"]["version_no"] == 1
    assert state["published"]["status"] == "PUBLISHED"
    assert len(state["published"]["tasks"]) == 32
    assert state["draft"] is None
    assert len(state["history"]) == 1

    # Advisor can also read state
    adv_state = get_workflow_state(advisor, project.id)
    assert adv_state["published"]["version_no"] == 1


def test_draft_workflow_concurrency_and_diff(wf_setup):
    owner, _, outsider, project = wf_setup

    # Outsider cannot edit draft
    with pytest.raises(DomainError) as exc:
        create_or_update_draft(outsider, project.id, {"tasks": []}, expected_version=0)
    assert exc.value.code == "NOT_FOUND"

    # Create first draft
    draft_payload = {
        "tasks": [
            {
                "task_id": "P01",
                "order_index": 1,
                "prompt_text": "Mi prompt personalizado para generar temas",
            },
            {
                "task_id": "P15",
                "order_index": 15,
                "is_optional": True,
                "is_active": False,  # Deactivate optional PRISMA
            }
        ]
    }
    state = create_or_update_draft(owner, project.id, draft_payload, expected_version=0)
    assert state["draft"] is not None
    assert state["draft"]["version_no"] == 2
    assert state["draft"]["status"] == "DRAFT"
    assert state["draft"]["lock_version"] == 1

    # Check diff: P01 prompt changed, P15 deactivated
    p01_task = next(t for t in state["draft"]["tasks"] if t["task_id"] == "P01")
    assert p01_task["prompt"]["prompt_text"] == "Mi prompt personalizado para generar temas"
    assert p01_task["prompt"]["provenance"] == "USER_EDITED"

    p15_task = next(t for t in state["draft"]["tasks"] if t["task_id"] == "P15")
    assert p15_task["is_active"] is False

    # Second edit with wrong expected_version fails with VERSION_CONFLICT
    with pytest.raises(DomainError) as exc:
        create_or_update_draft(owner, project.id, draft_payload, expected_version=0)
    assert exc.value.code == "VERSION_CONFLICT"

    # Valid edit with expected_version=1 succeeds
    state2 = create_or_update_draft(owner, project.id, {"tasks": []}, expected_version=1)
    assert state2["draft"]["lock_version"] == 2


def test_cannot_deactivate_or_optionalize_protected_task(wf_setup):
    owner, _, _, project = wf_setup
    get_workflow_state(owner, project.id)

    # Attempt to deactivate protected P04
    payload_bad = {
        "tasks": [
            {"task_id": "P04", "is_active": False}
        ]
    }
    with pytest.raises(DomainError) as exc:
        create_or_update_draft(owner, project.id, payload_bad, expected_version=0)
    assert exc.value.code == "VALIDATION_ERROR"
    assert "protegida" in exc.value.message.lower()


def test_validate_and_publish_workflow_and_reject_cycles(wf_setup):
    owner, _, _, project = wf_setup
    initial_state = get_workflow_state(owner, project.id)

    # Create cycle: P01 -> P02 -> P01
    cyclic_payload = {
        "dependencies": [
            {"source": "P01", "target": "P02", "reason": "P01 necesita P02"},
            {"source": "P02", "target": "P01", "reason": "P02 necesita P01"},
        ]
    }
    create_or_update_draft(owner, project.id, cyclic_payload, expected_version=0)

    val = validate_workflow_draft(owner, project.id)
    assert val["valid"] is False
    assert any("cíclica" in err.lower() for err in val["errors"])

    # Attempt to publish fails
    with pytest.raises(DomainError) as exc:
        publish_workflow_draft(owner, project.id, "Publicando ciclo", expected_version=1)
    assert exc.value.code == "VALIDATION_ERROR"

    # Fix the cycle by removing the circular dependency
    clean_payload = {"dependencies": initial_state["published"]["dependencies"]}
    create_or_update_draft(owner, project.id, clean_payload, expected_version=1)
    val2 = validate_workflow_draft(owner, project.id)
    assert val2["valid"] is True

    # Publish succeeds
    pub_state = publish_workflow_draft(owner, project.id, "Publicando versión 2 sin PRISMA", expected_version=2)
    assert pub_state["published"]["version_no"] == 2
    assert pub_state["published"]["status"] == "PUBLISHED"
    assert pub_state["draft"] is None
    assert len(pub_state["history"]) == 2

    # Check ResearchProfile updated
    profile = ResearchProfile.objects.get(project=project)
    assert profile.workflow_mode == "CONFIGURABLE_GRAPH"
    assert profile.active_workflow.version_no == 2

    # Effective prompt returns updated prompt
    eff = get_effective_prompt(owner, project.id, "P01")
    assert eff["task_id"] == "P01"


def test_restore_workflow_version_creates_new_version(wf_setup):
    owner, _, _, project = wf_setup
    get_workflow_state(owner, project.id)

    # Publish version 2
    create_or_update_draft(owner, project.id, {
        "tasks": [{"task_id": "P01", "prompt_text": "Prompt de v2"}]
    }, expected_version=0)
    publish_workflow_draft(owner, project.id, "v2 publicada", expected_version=1)

    # Now restore version 1
    restored = restore_workflow_version(owner, project.id, target_version_no=1, change_summary="Volviendo a base v1")
    assert restored["published"]["version_no"] == 3
    assert "Restaurado desde versión 1" in restored["published"]["change_summary"]

    eff = get_effective_prompt(owner, project.id, "P01")
    # In v1 prompt had base text, not "Prompt de v2"
    assert eff["prompt_text"] != "Prompt de v2"


def test_custom_tasks_are_versioned_executable_and_check_required_fields(wf_setup):
    owner, _, _, project = wf_setup
    initial = get_workflow_state(owner, project.id)
    dependencies = initial["published"]["dependencies"] + [{
        "source": "USR_DOC-001", "target": "USR_SRC-001", "type": "DATA_REQUIRED",
        "field": "claim", "blocking": True, "reason": "El borrador requiere una afirmación de la fuente",
    }]
    draft = create_or_update_draft(owner, project.id, {
        "tasks": [
            {"task_id": "USR_SRC-001", "title": "Ficha de fuente", "prompt_text": "Extrae los datos trazables."},
            {"task_id": "USR_DOC-001", "title": "Nota de síntesis", "prompt_text": "Redacta una síntesis sustentada."},
        ],
        "dependencies": dependencies,
    }, expected_version=0)
    assert any(t["task_id"] == "USR_DOC-001" for t in draft["draft"]["tasks"])
    published = publish_workflow_draft(owner, project.id, "Agregar tareas auxiliares", expected_version=1)
    version = published["published"]["version_no"]

    with pytest.raises(DomainError) as blocked:
        execute_custom_workflow_task(owner, project.id, "USR_DOC-001", {}, {"summary": "..."}, uuid4())
    assert blocked.value.code == "PREREQUISITE_LOCKED"

    execute_custom_workflow_task(owner, project.id, "USR_SRC-001", {}, {"claim": ""}, uuid4())
    with pytest.raises(DomainError) as missing_field:
        execute_custom_workflow_task(owner, project.id, "USR_DOC-001", {}, {"summary": "..."}, uuid4())
    assert missing_field.value.code == "PREREQUISITE_LOCKED"

    execute_custom_workflow_task(owner, project.id, "USR_SRC-001", {}, {"claim": "Resultado citado"}, uuid4())
    result = execute_custom_workflow_task(
        owner, project.id, "USR_DOC-001", {"source": "USR_SRC-001"},
        {"summary": "Síntesis trazable"}, uuid4(),
    )
    history = get_custom_workflow_task_executions(owner, project.id, "USR_DOC-001", version)
    assert result["workflow_version_no"] == version
    assert history["executions"][0]["prompt_text_used"] == "Redacta una síntesis sustentada."
    assert history["executions"][0]["output_data"] == {"summary": "Síntesis trazable"}


def test_core_academic_dependencies_cannot_be_removed(wf_setup):
    owner, _, _, project = wf_setup
    get_workflow_state(owner, project.id)
    create_or_update_draft(owner, project.id, {"dependencies": []}, expected_version=0)
    validation = validate_workflow_draft(owner, project.id)
    assert validation["valid"] is False
    assert any("P06 requiere P04" in error for error in validation["errors"])
