"""Conexiones privadas con servicios externos por cuenta autenticada."""

from django.conf import settings
from django.db import models


class ZoteroConnection(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="zotero_connection")
    zotero_user_id = models.CharField(max_length=32)
    api_key_ciphertext = models.TextField(blank=True, default="")
    granted_scopes = models.JSONField(default=list)
    connected_at = models.DateTimeField()
    disconnected_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "zotero_connection"

    @property
    def is_connected(self) -> bool:
        return bool(self.api_key_ciphertext and self.disconnected_at is None)
