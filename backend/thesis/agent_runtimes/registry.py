"""Registro explícito de runtimes soportados por el conector."""

from .antigravity_cli import AntigravityCliAdapter

_ADAPTERS = {AntigravityCliAdapter.runtime_code: AntigravityCliAdapter}


def get_runtime_adapter(runtime_code: str):
    adapter_class = _ADAPTERS.get(runtime_code)
    if adapter_class is None:
        raise ValueError(f"Runtime BYOA no soportado: {runtime_code}")
    return adapter_class()
