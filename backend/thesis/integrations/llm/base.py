"""Definición agnóstica de la interfaz interna de proveedores LLM."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class LLMError(Exception):
    """Excepción base para fallas en el adaptador de proveedor LLM."""
    code = "PROVIDER_ERROR"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class LLMProviderUnavailableError(LLMError):
    code = "PROVIDER_UNAVAILABLE"


class LLMProviderTimeoutError(LLMError):
    code = "PROVIDER_TIMEOUT"


class LLMProviderRateLimitError(LLMError):
    code = "PROVIDER_RATE_LIMITED"


class LLMOutputInvalidError(LLMError):
    code = "OUTPUT_INVALID"


@dataclass(frozen=True)
class LLMMessage:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass(frozen=True)
class LLMResult:
    content_json: dict[str, Any]
    raw_text: str
    provider: str
    model: str
    usage: dict[str, Any] = field(default_factory=dict)


class LLMProviderAdapter(ABC):
    """Interfaz interna obligatoria para cualquier proveedor de IA en TesisMCP."""

    @abstractmethod
    def generate_structured(
        self,
        messages: list[LLMMessage],
        output_schema: dict[str, Any],
        model_config: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> LLMResult:
        """Genera una salida estructurada validada preliminarmente."""
        pass
