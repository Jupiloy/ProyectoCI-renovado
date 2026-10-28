import hashlib
import json
from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.test import Client
from django.test import override_settings
from django.utils import timezone

from thesis.models import (
    ProjectParticipant, ProjectSupportInvitation, SourceDocument, SourceExcerpt,
    SupportContribution,
)
from thesis.services.errors import DomainError
from thesis.services.projects import create_project
from thesis.services.reviews import assign_advisor
from thesis.services.support_invitations import (
    accept_support_invitation, create_support_invitation, get_support_invitation_context,
    get_support_source_file, list_support_contributions, list_support_invitations,
    revoke_support_invitation, submit_support_contribution,
)
from thesis.services.workflows import get_workflow_state
from thesis.services.access import require_project


@pytest.fixture
def support_context(db):
    User = get_user_model()
    owner = User.objects.create_user(email="support-owner@example.org", password="pass")
    advisor = User.objects.create_user(email="support-advisor@example.org", password="pass")
    guest = User.objects.create_user(email="support-guest@example.org", password="pass")
    wrong_guest = User.objects.create_user(email="wrong-guest@example.org", password="pass")
    project = create_project(owner, "Apoyo acotado")
    assign_advisor(owner, project.id, advisor.email)
    get_workflow_state(owner, project.id)
    source = SourceDocument.objects.create(
        project=project,
        record_provider=SourceDocument.RecordProvider.OTHER,
        provider_record_id="support-source-a",
        title="Fuente compartida",
        verification_status=SourceDocument.Status.TEXT_CHECKED,
        metadata_origin=SourceDocument.MetadataOrigin.USER_SELECTED_CANDIDATE,
    )
    excerpt = SourceExcerpt.objects.create(
        source=source, chunk_no=1, page_no=3,
        text="Fragmento localizado en la página tres.",
        text_sha256=hashlib.sha256("Fragmento localizado en la página tres.".encode()).hexdigest(),
    )
    return owner, advisor, guest, wrong_guest, project, source, excerpt


def _create_invitation(owner, project, guest, source_ids):
    return create_support_invitation(
        owner, project.id, guest.email, "P01",
        "Revisa la pertinencia de la fuente para explorar el tema.",
        source_ids, ttl_hours=24,
    )


@pytest.mark.django_db
def test_support_invitation_requires_acceptance_and_never_grants_project_membership(support_context):
    owner, advisor, guest, wrong_guest, project, source, excerpt = support_context
    created = _create_invitation(owner, project, guest, [source.id])
    token = created["invite_token_once"]
    invitation_id = created["invitation_id"]
    row = ProjectSupportInvitation.objects.get(pk=invitation_id)

    assert created["status"] == "PENDING"
    assert token not in row.token_sha256
    assert row.token_sha256 == hashlib.sha256(token.encode()).hexdigest()
    assert not ProjectParticipant.objects.filter(project=project, user=guest).exists()
    with pytest.raises(DomainError):
        get_support_invitation_context(guest, row.id)
    with pytest.raises(DomainError):
        accept_support_invitation(wrong_guest, row.id, token)

    accepted = accept_support_invitation(guest, row.id, token)
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            ProjectSupportInvitation.objects.filter(pk=row.id).update(accepted_by=wrong_guest)
    repeated_accept = accept_support_invitation(guest, row.id, token)
    assert accepted["status"] == "ACCEPTED"
    assert repeated_accept["status"] == "ACCEPTED"
    assert not ProjectParticipant.objects.filter(project=project, user=guest).exists()
    with pytest.raises(DomainError) as hidden_project:
        require_project(guest, project.id)
    assert hidden_project.value.code == "NOT_FOUND"

    workspace = get_support_invitation_context(guest, row.id)
    assert workspace["task_id"] == "P01"
    assert [item["source_id"] for item in workspace["resources"]] == [str(source.id)]
    assert workspace["resources"][0]["excerpts"][0]["excerpt_id"] == str(excerpt.id)
    assert "invite_token_once" not in workspace
    assert list_support_invitations(advisor, project.id)[0]["invitation_id"] == str(row.id)


@pytest.mark.django_db
def test_support_contribution_is_idempotent_scoped_and_survives_revocation(support_context):
    owner, _, guest, _, project, source, excerpt = support_context
    other_source = SourceDocument.objects.create(
        project=project,
        record_provider=SourceDocument.RecordProvider.OTHER,
        provider_record_id="support-source-b",
        title="Fuente no compartida",
    )
    other_excerpt = SourceExcerpt.objects.create(
        source=other_source, chunk_no=1, page_no=1,
        text="No se compartió este extracto.",
        text_sha256=hashlib.sha256("No se compartió este extracto.".encode()).hexdigest(),
    )
    created = _create_invitation(owner, project, guest, [source.id])
    invitation_id = created["invitation_id"]
    accept_support_invitation(guest, invitation_id, created["invite_token_once"])

    with pytest.raises(DomainError) as outside_scope:
        submit_support_contribution(
            guest, invitation_id, "Aporte", [other_excerpt.id], uuid4(),
        )
    assert outside_scope.value.code == "NOT_FOUND"

    key = uuid4()
    contribution = submit_support_contribution(
        guest, invitation_id, "La fuente aborda el tema y su página tres contiene el pasaje pertinente.",
        [excerpt.id], key,
    )
    repeated = submit_support_contribution(
        guest, invitation_id, "La fuente aborda el tema y su página tres contiene el pasaje pertinente.",
        [excerpt.id], key,
    )
    assert repeated["contribution_id"] == contribution["contribution_id"]
    assert contribution["source_excerpt_ids"] == [str(excerpt.id)]
    assert list_support_contributions(owner, project.id, invitation_id)[0]["response_sha256"]
    with pytest.raises(DomainError):
        submit_support_contribution(guest, invitation_id, "Texto distinto", [excerpt.id], key)

    revoked = revoke_support_invitation(owner, project.id, invitation_id)
    assert revoked["status"] == "REVOKED"
    with pytest.raises(DomainError):
        get_support_invitation_context(guest, uuid4())
    with pytest.raises(DomainError):
        get_support_invitation_context(guest, ProjectSupportInvitation.objects.get(pk=invitation_id).id)
    assert len(list_support_contributions(owner, project.id, invitation_id)) == 1
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            SupportContribution.objects.filter(pk=contribution["contribution_id"]).update(response_text="editado")


@pytest.mark.django_db
def test_support_invitation_expiration_and_unshared_file_are_enforced(support_context, tmp_path, monkeypatch):
    owner, _, guest, _, project, source, _ = support_context
    created = _create_invitation(owner, project, guest, [source.id])
    invitation_id = created["invitation_id"]
    invitation = ProjectSupportInvitation.objects.get(pk=invitation_id)
    from thesis.services import support_invitations
    expired_now = invitation.expires_at + timedelta(seconds=1)
    monkeypatch.setattr(support_invitations.timezone, "now", lambda: expired_now)
    with pytest.raises(DomainError) as expired:
        accept_support_invitation(guest, invitation.id, created["invite_token_once"])
    assert expired.value.code == "INVITATION_EXPIRED"
    invitation.refresh_from_db()
    assert invitation.status == ProjectSupportInvitation.Status.EXPIRED

    pdf_bytes = b"%PDF-1.4\nB6.4 isolated test file\n"
    media_root = tmp_path / "media"
    stored = media_root / "sources" / str(project.id) / "shared.pdf"
    stored.parent.mkdir(parents=True)
    stored.write_bytes(pdf_bytes)
    shared_pdf = SourceDocument.objects.create(
        project=project,
        kind=SourceDocument.Kind.UPLOAD,
        title="PDF compartido",
        storage_key=str(stored.relative_to(media_root)),
        sha256=hashlib.sha256(pdf_bytes).hexdigest(),
        mime_type="application/pdf",
        verification_status=SourceDocument.Status.TEXT_CHECKED,
        page_count=1,
    )
    invite = _create_invitation(owner, project, guest, [shared_pdf.id])
    monkeypatch.undo()
    accept_support_invitation(guest, invite["invitation_id"], invite["invite_token_once"])
    with override_settings(MEDIA_ROOT=media_root):
        path, filename = get_support_source_file(guest, invite["invitation_id"], shared_pdf.id)
        assert path.read_bytes() == pdf_bytes
        assert filename == f"fuente-{shared_pdf.id}.pdf"
        with pytest.raises(DomainError):
            get_support_source_file(guest, invite["invitation_id"], source.id)


@pytest.mark.django_db
def test_support_invitation_http_acceptance_workspace_and_contribution(support_context):
    owner, _, guest, _, project, source, excerpt = support_context
    owner_client = Client()
    owner_client.force_login(owner)
    create_response = owner_client.post(
        f"/api/v1/projects/{project.id}/support-invitations",
        data=json.dumps({
            "invited_email": guest.email,
            "task_id": "P01",
            "task_instructions": "Comprueba la pertinencia de esta fuente.",
            "source_ids": [str(source.id)],
            "ttl_hours": 72,
        }),
        content_type="application/json",
    )
    assert create_response.status_code == 200, create_response.content
    invite = create_response.json()
    assert invite["invite_token_once"]

    guest_client = Client()
    guest_client.force_login(guest)
    accepted = guest_client.post(
        f"/api/v1/projects/support-invitations/{invite['invitation_id']}/accept",
        data=json.dumps({"invite_token": invite["invite_token_once"]}),
        content_type="application/json",
    )
    assert accepted.status_code == 200, accepted.content
    workspace = guest_client.get(
        f"/api/v1/projects/support-invitations/{invite['invitation_id']}/workspace",
    )
    assert workspace.status_code == 200
    assert workspace.json()["task_id"] == "P01"
    response = guest_client.post(
        f"/api/v1/projects/support-invitations/{invite['invitation_id']}/contributions",
        data=json.dumps({
            "response_text": "La fuente parece pertinente para el tema indicado.",
            "source_excerpt_ids": [str(excerpt.id)],
            "idempotency_key": str(uuid4()),
        }),
        content_type="application/json",
    )
    assert response.status_code == 200, response.content

    contributions = owner_client.get(
        f"/api/v1/projects/{project.id}/support-invitations/{invite['invitation_id']}/contributions",
    )
    assert contributions.status_code == 200
    assert len(contributions.json()["items"]) == 1
