"""Fábrica para resolver el adaptador LLM activo en el entorno."""

import os
from django.conf import settings
from .base import LLMProviderAdapter, LLMProviderUnavailableError
from .development import DevelopmentMockProviderAdapter

_TEST_ADAPTER_OVERRIDE: LLMProviderAdapter | None = None


def set_test_adapter_override(adapter: LLMProviderAdapter | None) -> None:
    """Permite fijar un adaptador en memoria para pruebas automatizadas."""
    global _TEST_ADAPTER_OVERRIDE
    _TEST_ADAPTER_OVERRIDE = adapter


def get_llm_adapter(provider_name: str | None = None) -> LLMProviderAdapter:
    """Devuelve la instancia del adaptador LLM desacoplado según configuración."""
    if _TEST_ADAPTER_OVERRIDE is not None:
        return _TEST_ADAPTER_OVERRIDE

    name = provider_name or getattr(settings, "TESISMCP_LLM_PROVIDER", "DISABLED")

    if name == "DEVELOPMENT_MOCK":
        if not settings.DEBUG:
            raise LLMProviderUnavailableError(
                "DEVELOPMENT_MOCK solo está permitido en modo DEBUG; configure un proveedor real en el servidor"
            )
        return DevelopmentMockProviderAdapter()

    if name == "GEMINI":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise LLMProviderUnavailableError(
                "El proveedor Gemini está configurado pero falta la variable de entorno GEMINI_API_KEY en el servidor"
            )
        model = (
            getattr(settings, "TESISMCP_GEMINI_MODEL", None)
            or os.environ.get("TESISMCP_GEMINI_MODEL", "gemini-3.8-flash")
        )
        from .gemini import GeminiProviderAdapter
        return GeminiProviderAdapter(api_key=api_key, model=model)

    if name == "DISABLED":
        raise LLMProviderUnavailableError(
            "El servicio de generación IA se encuentra deshabilitado por política del sistema"
        )

    raise LLMProviderUnavailableError(f"Proveedor LLM desconocido o no configurado: '{name}'")
