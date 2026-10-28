"""Adaptadores para runtimes de agentes conectados por BYOA."""

from .registry import get_runtime_adapter

__all__ = ["get_runtime_adapter"]
