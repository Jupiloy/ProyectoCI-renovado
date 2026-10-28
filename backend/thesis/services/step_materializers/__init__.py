"""Materializadores organizados por dominio; importa handlers para registrarlos."""

from .registry import STEP_HANDLERS, StepExecutionContext, execute_step_materializer, register_step_handler
from . import consistency, literature, instruments

__all__ = ["STEP_HANDLERS", "StepExecutionContext", "execute_step_materializer", "register_step_handler"]
