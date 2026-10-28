"""Adaptador de proveedor de desarrollo y pruebas locales."""

import json
from typing import Any, Callable

from .base import (
    LLMError,
    LLMMessage,
    LLMOutputInvalidError,
    LLMProviderAdapter,
    LLMProviderRateLimitError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
    LLMResult,
)


class DevelopmentMockProviderAdapter(LLMProviderAdapter):
    """Adaptador de desarrollo que simula respuestas estructuradas o errores."""

    def __init__(
        self,
        default_response: dict[str, Any] | None = None,
        simulate_error: str | None = None,
        custom_responder: Callable[[list[LLMMessage], dict[str, Any]], dict[str, Any]] | None = None,
        provider_name: str = "DEVELOPMENT_MOCK",
        model_name: str = "mock-thesis-v1",
    ):
        self.default_response = default_response or {}
        self.simulate_error = simulate_error
        self.custom_responder = custom_responder
        self.provider_name = provider_name
        self.model_name = model_name

    def generate_structured(
        self,
        messages: list[LLMMessage],
        output_schema: dict[str, Any],
        model_config: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> LLMResult:
        if self.simulate_error == "timeout":
            raise LLMProviderTimeoutError("El proveedor no respondió en el tiempo límite asignado")
        if self.simulate_error == "rate_limit":
            raise LLMProviderRateLimitError("Límite de tasa de solicitudes excedido en el proveedor")
        if self.simulate_error == "unavailable":
            raise LLMProviderUnavailableError("El servicio de inferencia no se encuentra disponible")
        if self.simulate_error == "invalid_json":
            raise LLMOutputInvalidError("La salida del proveedor no tiene formato JSON válido")

        if self.custom_responder is not None:
            data = self.custom_responder(messages, output_schema)
        elif self.default_response:
            data = self.default_response
        else:
            data = {}

        raw_text = json.dumps(data, ensure_ascii=False)
        return LLMResult(
            content_json=data,
            raw_text=raw_text,
            provider=self.provider_name,
            model=self.model_name,
            usage={},
        )
