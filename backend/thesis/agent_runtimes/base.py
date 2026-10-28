"""Contrato mínimo que cada runtime BYOA implementa."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class RuntimeEvent:
    """Evento normalizado emitido durante la ejecución de un runtime."""

    kind: str
    payload: dict[str, Any] | None = None


class AgentRuntimeAdapter(Protocol):
    runtime_code: str

    def resolve_executable(self, configured_path: str = "") -> str: ...

    def build_command(
        self, executable: str, schema_path: Path, *, model: str = "", effort: str = "medium"
    ) -> list[str]: ...

    def configure_mcp(self, workspace: Path, server_overrides: dict) -> Path: ...

    def parse_event(self, raw_line: str) -> RuntimeEvent | None: ...

    def permission_denied(self, stderr_text: str) -> bool: ...
