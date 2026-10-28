"""Routers compartidos para mantener el orden de registro de operaciones."""

from ninja import Router

router = Router(tags=["Proyectos"])
integrations_router = Router(tags=["Integraciones"])
