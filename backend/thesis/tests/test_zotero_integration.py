import pytest
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.test import Client
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils import timezone

from thesis.models import ZoteroConnection
from thesis.services.errors import DomainError
from thesis.services.projects import create_project
from thesis.services.zotero import (
    _api_key, _authors, _oauth_settings, _publication_year,
    get_zotero_connection_status, start_zotero_oauth,
)


@pytest.mark.django_db
def test_zotero_status_is_private_and_unconfigured_oauth_fails_closed(monkeypatch):
    user = get_user_model().objects.create_user(email="zotero-user@example.org", password="pass")
    assert get_zotero_connection_status(user) == {
        "provider": "ZOTERO", "connected": False, "zotero_user_id": None,
        "granted_scopes": [], "connected_at": None,
    }
    request = RequestFactory().get("/api/v1/integrations/zotero/connect")
    request.user = user
    SessionMiddleware(lambda req: None).process_request(request)
    request.session.save()
    client = Client()
    client.force_login(user)
    status_response = client.get("/api/v1/integrations/zotero")
    assert status_response.status_code == 200
    assert status_response.json()["connected"] is False
    monkeypatch.delenv("ZOTERO_OAUTH_CLIENT_KEY", raising=False)
    monkeypatch.delenv("ZOTERO_OAUTH_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("ZOTERO_OAUTH_CALLBACK_URL", raising=False)
    with pytest.raises(DomainError) as error:
        start_zotero_oauth(user, request)
    assert error.value.code == "CONFIG_ERROR"


def test_zotero_callback_url_requires_https_or_exact_localhost(monkeypatch):
    monkeypatch.setenv("ZOTERO_OAUTH_CLIENT_KEY", "client")
    monkeypatch.setenv("ZOTERO_OAUTH_CLIENT_SECRET", "secret")
    monkeypatch.setenv("ZOTERO_OAUTH_CALLBACK_URL", "https://app.example.org/oauth/zotero")
    assert _oauth_settings()[2] == "https://app.example.org/oauth/zotero"
    monkeypatch.setenv("ZOTERO_OAUTH_CALLBACK_URL", "http://localhost:8000/oauth/zotero")
    assert _oauth_settings()[2] == "http://localhost:8000/oauth/zotero"
    monkeypatch.setenv("ZOTERO_OAUTH_CALLBACK_URL", "https://localhost.bad.example/oauth/zotero")
    assert _oauth_settings()[2] == "https://localhost.bad.example/oauth/zotero"
    monkeypatch.setenv("ZOTERO_OAUTH_CALLBACK_URL", "http://attackerlocalhost.example/oauth/zotero")
    with pytest.raises(DomainError) as error:
        _oauth_settings()
    assert error.value.code == "CONFIG_ERROR"


@pytest.mark.django_db
def test_zotero_api_key_is_encrypted_at_rest_and_metadata_helpers_are_conservative(monkeypatch):
    user = get_user_model().objects.create_user(email="zotero-encrypted@example.org", password="pass")
    key = Fernet.generate_key()
    monkeypatch.setenv("ZOTERO_CREDENTIAL_ENCRYPTION_KEY", key.decode("ascii"))
    cipher = Fernet(key).encrypt(b"secret-zotero-api-key").decode("ascii")
    connection = ZoteroConnection.objects.create(
        user=user, zotero_user_id="123456", api_key_ciphertext=cipher,
        granted_scopes=["personal_library:read"], connected_at=timezone.now(),
    )
    assert "secret-zotero-api-key" not in connection.api_key_ciphertext
    assert _api_key(connection) == "secret-zotero-api-key"
    assert _authors([
        {"creatorType": "author", "firstName": "Ada", "lastName": "Lovelace"},
        {"creatorType": "editor", "name": "Editor Uno"},
    ]) == ["Ada Lovelace"]
    assert _publication_year("2021-09-04") == 2021
    assert _publication_year("forthcoming") is None


@pytest.mark.django_db
def test_zotero_library_and_import_require_project_member_and_connected_account():
    from thesis.services.zotero import import_zotero_item, list_zotero_items

    user = get_user_model().objects.create_user(email="zotero-project@example.org", password="pass")
    project = create_project(user, "Zotero")
    with pytest.raises(DomainError) as list_error:
        list_zotero_items(user, project.id)
    assert list_error.value.code == "NOT_FOUND"
    with pytest.raises(DomainError) as import_error:
        import_zotero_item(user, project.id, "ABCD1234")
    assert import_error.value.code == "NOT_FOUND"
