import json
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from thesis.services.projects import create_project


@pytest.fixture
def api_setup(db):
    User = get_user_model()
    owner = User.objects.create_user(email="api-owner@example.org", password="pass")
    advisor = User.objects.create_user(email="api-advisor@example.org", password="pass")
    outsider = User.objects.create_user(email="api-outsider@example.org", password="pass")
    project = create_project(owner, "Proyecto API Workflow")
    from thesis.services.reviews import assign_advisor
    assign_advisor(owner, project.id, advisor.email)
    return owner, advisor, outsider, project


def test_workflow_api_crud_flow(api_setup):
    owner, advisor, outsider, project = api_setup
    client = Client()

    # 1. Outsider gets 404 (NOT_FOUND)
    client.force_login(outsider)
    res = client.get(f"/api/v1/projects/{project.id}/workflow")
    assert res.status_code == 404

    # 2. Owner gets 200 and initialized workflow
    client.force_login(owner)
    res = client.get(f"/api/v1/projects/{project.id}/workflow")
    assert res.status_code == 200
    data = res.json()
    assert data["published"]["version_no"] == 1
    assert data["draft"] is None

    # 3. Advisor can also view workflow (200)
    client.force_login(advisor)
    adv_res = client.get(f"/api/v1/projects/{project.id}/workflow")
    assert adv_res.status_code == 200

    # 4. Advisor cannot edit draft (404/denied)
    res_adv_edit = client.put(
        f"/api/v1/projects/{project.id}/workflow/draft",
        data=json.dumps({"tasks": [], "expected_version": 0}),
        content_type="application/json",
    )
    assert res_adv_edit.status_code == 404

    # 5. Owner creates/edits draft
    client.force_login(owner)
    draft_payload = {
        "tasks": [
            {
                "task_id": "P01",
                "prompt_text": "Nuevo prompt vía API REST",
            }
        ],
        "expected_version": 0,
    }
    res_draft = client.put(
        f"/api/v1/projects/{project.id}/workflow/draft",
        data=json.dumps(draft_payload),
        content_type="application/json",
    )
    assert res_draft.status_code == 200
    draft_data = res_draft.json()["draft"]
    assert draft_data["version_no"] == 2
    assert draft_data["lock_version"] == 1

    # 6. Concurrency conflict on draft (VERSION_CONFLICT -> 409)
    res_conflict = client.put(
        f"/api/v1/projects/{project.id}/workflow/draft",
        data=json.dumps(draft_payload),
        content_type="application/json",
    )
    assert res_conflict.status_code == 409

    # 7. Validate draft
    res_val = client.post(f"/api/v1/projects/{project.id}/workflow/validate")
    assert res_val.status_code == 200
    assert res_val.json()["valid"] is True

    # 8. Publish draft
    pub_payload = {
        "change_summary": "Versión 2 personalizada publicada vía API",
        "expected_version": 1,
    }
    res_pub = client.post(
        f"/api/v1/projects/{project.id}/workflow/publish",
        data=json.dumps(pub_payload),
        content_type="application/json",
    )
    assert res_pub.status_code == 200
    pub_data = res_pub.json()
    assert pub_data["published"]["version_no"] == 2
    assert pub_data["draft"] is None

    # 9. Get effective prompt
    res_prompt = client.get(f"/api/v1/projects/{project.id}/workflow/tasks/P01/prompt")
    assert res_prompt.status_code == 200
    assert res_prompt.json()["prompt_text"] == "Nuevo prompt vía API REST"

    # 10. Restore past version 1
    restore_payload = {
        "target_version_no": 1,
        "change_summary": "Restaurando a v1 inicial",
    }
    res_restore = client.post(
        f"/api/v1/projects/{project.id}/workflow/restore",
        data=json.dumps(restore_payload),
        content_type="application/json",
    )
    assert res_restore.status_code == 200
    assert res_restore.json()["published"]["version_no"] == 3
