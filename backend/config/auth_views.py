"""Endpoints de sesión para clientes web same-origin con cookies Django y CSRF."""

import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST


MAX_LOGIN_BODY_BYTES = 16 * 1024


def _user_payload(user):
    return {
        "id": str(user.pk),
        "email": user.email,
        "display_name": user.display_name,
    }


@ensure_csrf_cookie
@require_GET
def session_status(request):
    """Devuelve la sesión actual y entrega un token CSRF para el siguiente POST."""
    user = request.user
    return JsonResponse({
        "authenticated": bool(user.is_authenticated),
        "user": _user_payload(user) if user.is_authenticated else None,
        "csrf_token": get_token(request),
    })


@require_POST
def session_login(request):
    """Autentica por correo y crea una sesión Django; errores no revelan la cuenta."""
    if len(request.body) > MAX_LOGIN_BODY_BYTES:
        return JsonResponse({"detail": "Solicitud demasiado grande"}, status=413)
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "Se requiere JSON válido"}, status=400)
    if not isinstance(payload, dict) or set(payload) != {"email", "password"}:
        return JsonResponse({"detail": "Se requieren email y password"}, status=400)
    email = payload["email"]
    password = payload["password"]
    if not isinstance(email, str) or not isinstance(password, str):
        return JsonResponse({"detail": "Credenciales inválidas"}, status=400)
    user = authenticate(request, username=email.strip().lower(), password=password)
    if user is None or not user.is_active:
        return JsonResponse({"detail": "Correo o contraseña incorrectos"}, status=401)
    login(request, user)
    return JsonResponse({
        "authenticated": True,
        "user": _user_payload(user),
        "csrf_token": get_token(request),
    })


@require_POST
def session_logout(request):
    """Invalida la sesión actual; Django CSRF protege este POST mediante middleware."""
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=200)
    logout(request)
    return JsonResponse({"authenticated": False}, status=200)
