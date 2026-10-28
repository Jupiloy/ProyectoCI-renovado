"""Integración agnóstica de modelos de lenguaje para TesisMCP."""

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
from .development import DevelopmentMockProviderAdapter
from .factory import get_llm_adapter, set_test_adapter_override
from .gemini import GeminiProviderAdapter

__all__ = [
    "LLMError",
    "LLMMessage",
    "LLMResult",
    "LLMProviderAdapter",
    "LLMProviderUnavailableError",
    "LLMProviderTimeoutError",
    "LLMProviderRateLimitError",
    "LLMOutputInvalidError",
    "DevelopmentMockProviderAdapter",
    "GeminiProviderAdapter",
    "get_llm_adapter",
    "set_test_adapter_override",
]
