from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import path

from config.auth_views import session_login, session_logout, session_status

from config.api import api


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("health/", health),
    path("api/v1/auth/session/", session_status),
    path("api/v1/auth/login/", session_login),
    path("api/v1/auth/logout/", session_logout),
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
]
