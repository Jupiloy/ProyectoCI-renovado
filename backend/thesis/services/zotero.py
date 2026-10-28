"""Integración Zotero Web API v3: OAuth 1.0a, lectura personal y copia bibliográfica por proyecto."""

import os
import re
import time
from urllib.parse import quote, urlparse

import requests
from cryptography.fernet import Fernet, InvalidToken
from django.db import transaction
from django.http import HttpResponseRedirect
from django.utils import timezone
from requests_oauthlib import OAuth1Session

from thesis.models import SourceDocument, ZoteroConnection
from thesis.services.access import require_project
from thesis.services.errors import DomainError


ZOTERO_API = "https://api.zotero.org"
OAUTH_REQUEST = "https://www.zotero.org/oauth/request"
OAUTH_AUTHORIZE = "https://www.zotero.org/oauth/authorize"
OAUTH_ACCESS = "https://www.zotero.org/oauth/access"
OAUTH_SESSION_KEY = "zotero_oauth_pending"


def _oauth_settings() -> tuple[str, str, str]:
    values = (
        os.getenv("ZOTERO_OAUTH_CLIENT_KEY", "").strip(),
        os.getenv("ZOTERO_OAUTH_CLIENT_SECRET", "").strip(),
        os.getenv("ZOTERO_OAUTH_CALLBACK_URL", "").strip(),
    )
    if not all(values):
        raise DomainError("CONFIG_ERROR", "Zotero OAuth no está configurado para esta instalación")
    parsed_callback = urlparse(values[2])
    local_callback = parsed_callback.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed_callback.scheme != "https" and not (parsed_callback.scheme == "http" and local_callback):
        raise DomainError("CONFIG_ERROR", "El callback OAuth debe usar HTTPS fuera de localhost")
    if not parsed_callback.hostname or parsed_callback.username or parsed_callback.password:
        raise DomainError("CONFIG_ERROR", "El callback OAuth debe ser una URL válida sin credenciales")
    return values


def _fernet() -> Fernet:
    raw_key = os.getenv("ZOTERO_CREDENTIAL_ENCRYPTION_KEY", "").strip().encode("ascii")
    if not raw_key:
        raise DomainError("CONFIG_ERROR", "Falta ZOTERO_CREDENTIAL_ENCRYPTION_KEY")
    try:
        return Fernet(raw_key)
    except (ValueError, TypeError) as exc:
        raise DomainError("CONFIG_ERROR", "ZOTERO_CREDENTIAL_ENCRYPTION_KEY no es una clave Fernet válida") from exc


def _connection_status(connection: ZoteroConnection | None) -> dict:
    return {
        "provider": "ZOTERO",
        "connected": bool(connection and connection.is_connected),
        "zotero_user_id": connection.zotero_user_id if connection and connection.is_connected else None,
        "granted_scopes": connection.granted_scopes if connection and connection.is_connected else [],
        "connected_at": connection.connected_at.isoformat() if connection and connection.is_connected else None,
    }


def get_zotero_connection_status(actor) -> dict:
    connection = ZoteroConnection.objects.filter(user=actor).first()
    return _connection_status(connection)


def start_zotero_oauth(actor, request):
    client_key, client_secret, callback_url = _oauth_settings()
    _fernet()  # Fail before asking Zotero to grant a key that cannot be stored securely.
    oauth = OAuth1Session(client_key, client_secret=client_secret, callback_uri=callback_url)
    try:
        credentials = oauth.fetch_request_token(OAUTH_REQUEST)
    except requests.RequestException as exc:
        raise DomainError("PROVIDER_UNAVAILABLE", "No se pudo iniciar la autorización de Zotero") from exc
    if not credentials.get("oauth_token") or not credentials.get("oauth_token_secret"):
        raise DomainError("AUTHORIZATION_ERROR", "Zotero no devolvió una solicitud temporal válida")
    request.session[OAUTH_SESSION_KEY] = {
        "oauth_token": credentials.get("oauth_token", ""),
        "oauth_token_secret": credentials.get("oauth_token_secret", ""),
        "user_id": str(actor.pk),
        "started_at": time.time(),
    }
    request.session.modified = True
    authorization_url = oauth.authorization_url(
        OAUTH_AUTHORIZE,
        name="TesisMCP",
        library_access=1,
        notes_access=0,
        write_access=0,
        all_groups="none",
    )
    return HttpResponseRedirect(authorization_url)


def complete_zotero_oauth(actor, request) -> dict:
    pending = request.session.get(OAUTH_SESSION_KEY)
    if not isinstance(pending, dict) or pending.get("user_id") != str(actor.pk):
        raise DomainError("AUTHORIZATION_ERROR", "No existe una autorización Zotero pendiente para esta sesión")
    try:
        started_at = float(pending.get("started_at", 0))
    except (TypeError, ValueError):
        started_at = 0
    if started_at <= 0 or time.time() - started_at > 600:
        request.session.pop(OAUTH_SESSION_KEY, None)
        raise DomainError("AUTHORIZATION_ERROR", "La autorización Zotero expiró; inicia una nueva conexión")
    token = request.GET.get("oauth_token", "")
    verifier = request.GET.get("oauth_verifier", "")
    request_token_secret = pending.get("oauth_token_secret")
    if (not token or token != pending.get("oauth_token") or not verifier
            or not isinstance(request_token_secret, str) or not request_token_secret):
        request.session.pop(OAUTH_SESSION_KEY, None)
        raise DomainError("AUTHORIZATION_ERROR", "La respuesta OAuth no coincide con la solicitud iniciada")
    client_key, client_secret, _ = _oauth_settings()
    oauth = OAuth1Session(
        client_key,
        client_secret=client_secret,
        resource_owner_key=token,
        resource_owner_secret=request_token_secret,
        verifier=verifier,
    )
    try:
        credentials = oauth.fetch_access_token(OAUTH_ACCESS)
    except requests.RequestException as exc:
        request.session.pop(OAUTH_SESSION_KEY, None)
        raise DomainError("PROVIDER_UNAVAILABLE", "Zotero no completó el intercambio OAuth") from exc
    api_key = credentials.get("oauth_token", "")
    zotero_user_id = str(credentials.get("userID", "")).strip()
    if not api_key or not zotero_user_id.isdigit():
        request.session.pop(OAUTH_SESSION_KEY, None)
        raise DomainError("AUTHORIZATION_ERROR", "Zotero no devolvió una identidad y clave utilizables")
    encrypted = _fernet().encrypt(api_key.encode("utf-8")).decode("ascii")
    connection, _ = ZoteroConnection.objects.update_or_create(
        user=actor,
        defaults={
            "zotero_user_id": zotero_user_id,
            "api_key_ciphertext": encrypted,
            "granted_scopes": ["personal_library:read"],
            "connected_at": timezone.now(),
            "disconnected_at": None,
        },
    )
    request.session.pop(OAUTH_SESSION_KEY, None)
    return _connection_status(connection)


def _api_key(connection: ZoteroConnection) -> str:
    if not connection.is_connected:
        raise DomainError("NOT_FOUND", "La cuenta Zotero no está conectada")
    try:
        return _fernet().decrypt(connection.api_key_ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise DomainError("CONFIG_ERROR", "No se puede descifrar la credencial Zotero almacenada") from exc


def _zotero_get(connection: ZoteroConnection, path: str, *, params: dict | None = None):
    response = requests.get(
        f"{ZOTERO_API}{path}",
        headers={"Zotero-API-Key": _api_key(connection), "Zotero-API-Version": "3"},
        params=params or {}, timeout=(3.05, 20),
    )
    if response.status_code == 403:
        raise DomainError("AUTHORIZATION_ERROR", "Zotero rechazó el acceso; revisa o revoca la conexión")
    if response.status_code == 429:
        raise DomainError("RATE_LIMITED", "Zotero limitó temporalmente las consultas; inténtalo más tarde")
    if response.status_code >= 500:
        raise DomainError("PROVIDER_UNAVAILABLE", "Zotero no está disponible temporalmente")
    if not response.ok:
        raise DomainError("PROVIDER_ERROR", f"Zotero respondió con HTTP {response.status_code}")
    return response


def _personal_library_path(connection: ZoteroConnection) -> str:
    return f"/users/{quote(connection.zotero_user_id, safe='')}/items"


def list_zotero_items(actor, project_id, *, query: str = "", start: int = 0, limit: int = 25) -> dict:
    require_project(actor, project_id)
    if type(start) is not int or start < 0 or type(limit) is not int or not 1 <= limit <= 100:
        raise DomainError("VALIDATION_ERROR", "Paginación Zotero inválida")
    if len(query) > 200:
        raise DomainError("VALIDATION_ERROR", "query supera 200 caracteres")
    connection = ZoteroConnection.objects.filter(user=actor).first()
    if not connection or not connection.is_connected:
        raise DomainError("NOT_FOUND", "La cuenta Zotero no está conectada")
    response = _zotero_get(connection, _personal_library_path(connection), params={
        "format": "json", "limit": limit, "start": start, "q": query,
        "itemType": "-attachment -note -annotation",
    })
    try:
        payload = response.json()
    except ValueError as exc:
        raise DomainError("PROVIDER_ERROR", "Zotero devolvió JSON inválido") from exc
    items = []
    for item in payload if isinstance(payload, list) else []:
        if not isinstance(item, dict):
            continue
        data = item.get("data", {})
        title = str(data.get("title") or "").strip()
        if not item.get("key") or not title:
            continue
        items.append({
            "item_key": str(item["key"]), "item_type": data.get("itemType"), "title": title,
            "authors": _authors(data.get("creators", [])), "date": data.get("date", ""),
            "doi": data.get("DOI", ""), "publication_venue": data.get("publicationTitle", ""),
            "url": data.get("url", ""), "abstract": data.get("abstractNote", ""),
        })
    return {
        "items": items,
        "start": start,
        "limit": limit,
        "total_results": _header_int(response.headers, "Total-Results"),
        "last_modified_version": _header_int(response.headers, "Last-Modified-Version"),
    }


def _header_int(headers, name: str) -> int | None:
    try:
        return int(headers[name]) if name in headers else None
    except (TypeError, ValueError):
        return None


def _authors(creators) -> list[str]:
    if not isinstance(creators, list):
        return []
    authors = []
    for creator in creators:
        if not isinstance(creator, dict) or creator.get("creatorType") != "author":
            continue
        name = str(creator.get("name") or "").strip()
        if not name:
            name = " ".join(part for part in (
                str(creator.get("firstName") or "").strip(),
                str(creator.get("lastName") or "").strip(),
            ) if part)
        if name:
            authors.append(name)
    return authors


def _publication_year(raw_date) -> int | None:
    match = re.search(r"\b(1[5-9]\d{2}|20\d{2}|21\d{2})\b", str(raw_date or ""))
    return int(match.group(1)) if match else None


def import_zotero_item(actor, project_id, item_key: str) -> dict:
    project = require_project(actor, project_id, owner_only=True)
    if not isinstance(item_key, str) or not re.fullmatch(r"[A-Z0-9]{8}", item_key):
        raise DomainError("VALIDATION_ERROR", "item_key Zotero debe tener 8 caracteres alfanuméricos")
    connection = ZoteroConnection.objects.filter(user=actor).first()
    if not connection or not connection.is_connected:
        raise DomainError("NOT_FOUND", "La cuenta Zotero no está conectada")
    response = _zotero_get(
        connection, f"{_personal_library_path(connection)}/{quote(item_key, safe='')}",
        params={"format": "json"},
    )
    try:
        item = response.json()
        data = item["data"]
        title = str(data.get("title") or "").strip()
    except (ValueError, KeyError, TypeError) as exc:
        raise DomainError("PROVIDER_ERROR", "Zotero devolvió un registro incompleto") from exc
    if item.get("key") != item_key or not title:
        raise DomainError("NOT_FOUND", "El registro Zotero no existe en la biblioteca autorizada")
    if data.get("itemType") in {"attachment", "note", "annotation"}:
        raise DomainError("VALIDATION_ERROR", "Solo se importan registros bibliográficos, no notas o adjuntos")

    provider_record_id = f"{connection.zotero_user_id}:{item_key}"
    with transaction.atomic():
        source, created = SourceDocument.objects.get_or_create(
            project=project, record_provider=SourceDocument.RecordProvider.ZOTERO,
            provider_record_id=provider_record_id,
            defaults={
                "kind": SourceDocument.Kind.EXTERNAL,
                "title": title,
                "authors_json": _authors(data.get("creators", [])),
                "publication_year": _publication_year(data.get("date")),
                "doi": str(data.get("DOI") or "")[:255] or None,
                "abstract": str(data.get("abstractNote") or ""),
                "publication_venue": str(data.get("publicationTitle") or ""),
                "url": str(data.get("url") or "") or None,
                "metadata_origin": SourceDocument.MetadataOrigin.PROVIDER_API,
                "verification_status": SourceDocument.Status.UNVERIFIED_METADATA,
            },
        )
    return {
        "source_id": str(source.id), "created": created,
        "metadata_origin": source.metadata_origin,
        "verification_status": source.verification_status,
        "provider_record_id": source.provider_record_id,
        "title": source.title, "authors": source.authors_json, "publication_year": source.publication_year,
        "doi": source.doi, "url": source.url,
    }


def disconnect_zotero(actor) -> dict:
    connection = ZoteroConnection.objects.filter(user=actor).first()
    if connection is None or not connection.is_connected:
        return {"provider": "ZOTERO", "connected": False, "remote_revocation": "NOT_CONNECTED"}
    api_key = _api_key(connection)
    remote_status = "REVOKED"
    response_status = None
    try:
        response = requests.delete(
            f"{ZOTERO_API}/keys/{quote(api_key, safe='')}",
            headers={"Zotero-API-Key": api_key, "Zotero-API-Version": "3"}, timeout=(3.05, 20),
        )
        response_status = response.status_code
        if response.status_code not in (200, 204, 404):
            remote_status = "MANUAL_REVOCATION_REQUIRED"
    except requests.RequestException:
        remote_status = "MANUAL_REVOCATION_REQUIRED"
    connection.api_key_ciphertext = ""
    connection.disconnected_at = timezone.now()
    connection.save(update_fields=["api_key_ciphertext", "disconnected_at", "updated_at"])
    return {
        "provider": "ZOTERO", "connected": False,
        "remote_revocation": remote_status, "remote_http_status": response_status,
        "manual_revocation_path": "https://www.zotero.org/settings/keys"
        if remote_status == "MANUAL_REVOCATION_REQUIRED" else None,
    }
