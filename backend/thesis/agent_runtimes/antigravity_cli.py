"""Adaptador del protocolo headless de Antigravity CLI."""

import json
import shutil
from pathlib import Path
from typing import Any

from .base import RuntimeEvent


class AntigravityCliAdapter:
    runtime_code = "ANTIGRAVITY_CLI"

    def resolve_executable(self, configured_path: str = "") -> str:
        if configured_path and Path(configured_path).is_file():
            return configured_path
        discovered = shutil.which("agy")
        if discovered:
            return discovered
        fallback = Path.home() / ".local" / "bin" / "agy"
        return str(fallback) if fallback.is_file() else ""

    def build_command(
        self, executable: str, schema_path: Path, *, model: str = "", effort: str = "medium"
    ) -> list[str]:
        args = [
            executable, "--input-format", "stream-json", "--output-format", "stream-json",
            "--json-schema", str(schema_path), "--print-timeout", "15m", "--effort", effort,
        ]
        if model:
            args.extend(["--model", model])
        return args

    def configure_mcp(self, workspace: Path, server_overrides: dict) -> Path:
        agents_dir = workspace / ".agents"
        agents_dir.mkdir(mode=0o700, exist_ok=True)
        config_path = agents_dir / "mcp_config.json"
        config_path.write_text(json.dumps({"mcpServers": server_overrides}), encoding="utf-8")
        config_path.chmod(0o600)
        return config_path

    def parse_event(self, raw_line: str) -> RuntimeEvent | None:
        try:
            event: dict[str, Any] = json.loads(raw_line)
        except (json.JSONDecodeError, TypeError):
            return None
        if event.get("event") == "step_update":
            step = event.get("step_update") or {}
            tool_name = step.get("tool_name") or (step.get("tool_info") or {}).get("name")
            if isinstance(tool_name, str):
                return RuntimeEvent("tool_activity", {"tool_name": tool_name})
            return RuntimeEvent("progress", {"message": "El agente está procesando la tarea"})
        if event.get("event") == "result":
            result = event.get("result") or {}
            return RuntimeEvent("result", {
                "status": result.get("status"),
                "structured_output": result.get("structured_output"),
                "conversation_id": result.get("conversation_id"),
                "usage": result.get("usage") or {},
            })
        return None

    def permission_denied(self, stderr_text: str) -> bool:
        return "soft-denied" in stderr_text.lower()
