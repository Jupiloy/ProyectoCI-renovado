"""Validación acotada de esquemas y outputs JSON de tareas personalizadas."""

import json
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError

from thesis.services.errors import DomainError

MAX_OUTPUT_SCHEMA_BYTES = 64_000
MAX_OUTPUT_SCHEMA_DEPTH = 24
MAX_OUTPUT_BYTES = 500_000


def validate_output_schema_definition(schema: Any) -> dict[str, Any]:
    """Valida esquema JSON Schema local y acotado, sin referencias externas/recursivas."""
    if not isinstance(schema, dict) or schema.get("type") != "object":
        raise DomainError("VALIDATION_ERROR", "output_schema debe definir un objeto JSON Schema con type='object'")
    if not isinstance(schema.get("properties"), dict):
        raise DomainError("VALIDATION_ERROR", "output_schema debe incluir un mapa 'properties'")
    if schema.get("additionalProperties") is not False:
        raise DomainError("VALIDATION_ERROR", "output_schema debe declarar additionalProperties=false")
    try:
        encoded = json.dumps(schema, sort_keys=True, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DomainError("VALIDATION_ERROR", "output_schema debe contener JSON válido") from exc
    if len(encoded) > MAX_OUTPUT_SCHEMA_BYTES:
        raise DomainError("VALIDATION_ERROR", "output_schema excede el tamaño máximo permitido")

    def inspect(node: Any, depth: int = 0) -> None:
        if depth > MAX_OUTPUT_SCHEMA_DEPTH:
            raise DomainError("VALIDATION_ERROR", "output_schema excede la profundidad máxima permitida")
        if isinstance(node, dict):
            if any(key in node for key in ("$ref", "$dynamicRef", "$recursiveRef")):
                raise DomainError("VALIDATION_ERROR", "output_schema no permite referencias JSON Schema")
            for value in node.values():
                inspect(value, depth + 1)
        elif isinstance(node, list):
            for value in node:
                inspect(value, depth + 1)

    inspect(schema)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise DomainError("VALIDATION_ERROR", "output_schema no es un JSON Schema Draft 2020-12 válido") from exc
    return schema


def validate_output_data(data: Any, schema: dict[str, Any]) -> dict[str, Any]:
    """Valida recursivamente un output custom y devuelve el objeto sin transformarlo."""
    schema = validate_output_schema_definition(schema)
    if not isinstance(data, dict):
        raise DomainError("OUTPUT_INVALID", "La salida generada debe ser un objeto JSON")
    try:
        encoded = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DomainError("OUTPUT_INVALID", "La salida generada no es JSON serializable") from exc
    if len(encoded) > MAX_OUTPUT_BYTES:
        raise DomainError("OUTPUT_INVALID", "La salida generada supera el tamaño máximo permitido")

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    error = next(iter(validator.iter_errors(data)), None)
    if error is not None:
        location = ".".join(str(part) for part in error.absolute_path)
        field = f" en '{location}'" if location else ""
        raise DomainError("OUTPUT_INVALID", f"La salida no cumple output_schema{field}: {error.message[:300]}")
    return data
