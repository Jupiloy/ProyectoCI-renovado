"""Adaptador oficial de Google Gemini usando el SDK google-genai."""

import json
import logging
from typing import Any

import httpx
from google import genai
from google.genai import errors, types

from .base import (
    LLMMessage,
    LLMOutputInvalidError,
    LLMProviderAdapter,
    LLMProviderRateLimitError,
    LLMProviderTimeoutError,
    LLMProviderUnavailableError,
    LLMResult,
)

logger = logging.getLogger(__name__)


class GeminiProviderAdapter(LLMProviderAdapter):
    """Adaptador de proveedor LLM para Google Gemini utilizando google-genai."""

    def __init__(self, api_key: str, model: str = "gemini-3.8-flash"):
        if not api_key or not api_key.strip():
            raise LLMProviderUnavailableError(
                "Falta la clave API de Gemini en el servidor; no se puede inicializar el proveedor"
            )
        if not model or not model.strip():
            raise LLMProviderUnavailableError(
                "Falta TESISMCP_GEMINI_MODEL en la configuración del servidor"
            )
        self._api_key = api_key.strip()
        self.model = model.strip()

    def generate_structured(
        self,
        messages: list[LLMMessage],
        output_schema: dict[str, Any],
        model_config: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> LLMResult:
        """Invoca a Gemini solicitando salida estructurada mediante JSON Schema."""
        if model_config and "model" in model_config:
            raise LLMProviderUnavailableError(
                "Gemini no acepta selección de modelo en model_config; configure TESISMCP_GEMINI_MODEL en el servidor"
            )
        effective_model = self.model

        system_parts: list[str] = []
        contents: list[types.Content] = []

        for msg in messages:
            if msg.role == "system":
                system_parts.append(msg.content)
            elif msg.role in {"user", "human"}:
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=msg.content)],
                    )
                )
            elif msg.role in {"assistant", "model"}:
                contents.append(
                    types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=msg.content)],
                    )
                )
            else:
                raise LLMOutputInvalidError(
                    f"Rol de mensaje no compatible con Gemini: {msg.role!r}"
                )

        system_instruction = "\n\n".join(system_parts) if system_parts else None

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=output_schema,
            system_instruction=system_instruction,
        )

        timeout_ms = int(max(timeout, 1.0) * 1000)

        try:
            client = genai.Client(
                api_key=self._api_key,
                http_options=types.HttpOptions(timeout=timeout_ms),
            )
            response = client.models.generate_content(
                model=effective_model,
                contents=contents,
                config=config,
            )
        except (httpx.TimeoutException, TimeoutError) as exc:
            raise LLMProviderTimeoutError(
                f"Tiempo de espera agotado al consultar Gemini ({timeout}s)"
            ) from exc
        except errors.ClientError as exc:
            code = getattr(exc, "code", None)
            msg_str = str(exc).upper()
            if code == 429 or "RESOURCE_EXHAUSTED" in msg_str:
                raise LLMProviderRateLimitError("Límite de tasa de Gemini alcanzado (HTTP 429)") from exc
            if code in {401, 403}:
                raise LLMProviderUnavailableError(
                    "Credenciales o permisos de Gemini inválidos en el servidor (HTTP 401/403)"
                ) from exc
            if code == 400:
                raise LLMOutputInvalidError(
                    "La solicitud o esquema estructurado fue rechazado por Gemini (HTTP 400)"
                ) from exc
            if code in {408, 504}:
                raise LLMProviderTimeoutError(
                    f"Tiempo de espera agotado en la API de Gemini (HTTP {code})"
                ) from exc
            raise LLMProviderUnavailableError(f"Error de cliente en Gemini (HTTP {code})") from exc
        except errors.ServerError as exc:
            code = getattr(exc, "code", 500)
            if code in {408, 504}:
                raise LLMProviderTimeoutError(
                    f"Tiempo de espera agotado en servidor de Gemini (HTTP {code})"
                ) from exc
            raise LLMProviderUnavailableError(
                f"El servicio de Gemini no está disponible temporalmente (HTTP {code})"
            ) from exc
        except errors.APIError as exc:
            code = getattr(exc, "code", None)
            if code in {408, 504}:
                raise LLMProviderTimeoutError(f"Tiempo de espera agotado en API Gemini (HTTP {code})") from exc
            raise LLMProviderUnavailableError(f"Falla de API en Gemini (HTTP {code})") from exc
        except Exception as exc:
            logger.error(
                "Falla inesperada de transporte al consultar Gemini (tipo=%s)",
                type(exc).__name__,
            )
            raise LLMProviderUnavailableError("Falla de transporte inesperada al consultar Gemini") from exc

        raw_text = getattr(response, "text", None) or ""
        if not raw_text.strip():
            raise LLMOutputInvalidError("Gemini devolvió una respuesta vacía sin texto JSON")

        try:
            parsed_json = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise LLMOutputInvalidError(
                f"La respuesta de Gemini no es un JSON válido: {exc}"
            ) from exc

        if not isinstance(parsed_json, dict):
            raise LLMOutputInvalidError(
                f"La respuesta de Gemini debe ser un objeto JSON (dict), se recibió {type(parsed_json).__name__}"
            )

        usage: dict[str, Any] = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            if getattr(meta, "prompt_token_count", None) is not None:
                usage["prompt_token_count"] = meta.prompt_token_count
            if getattr(meta, "candidates_token_count", None) is not None:
                usage["candidates_token_count"] = meta.candidates_token_count
            if getattr(meta, "total_token_count", None) is not None:
                usage["total_token_count"] = meta.total_token_count

        return LLMResult(
            content_json=parsed_json,
            raw_text=raw_text,
            provider="GEMINI",
            model=effective_model,
            usage=usage,
        )
