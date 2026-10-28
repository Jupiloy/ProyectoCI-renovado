"""Pruebas automatizadas para el Motor de Prompts y Roles Multi-Agente del Servidor MCP."""

import asyncio
from unittest.mock import patch
import pytest
from uuid import uuid4

from mcp_server.server import app
from thesis.models import Project, ProjectParticipant, ResearchProfile, User
from thesis.services.errors import DomainError


def test_list_prompts_contains_all_32_steps_and_roles():
    """Verifica que el catálogo de MCP exponga los 32 pasos metodológicos y los 3 roles de agente."""
    async def run():
        prompts = await app.list_prompts()
        prompt_names = {p.name for p in prompts}

        assert len(prompts) == 35, f"Se esperaban 35 prompts registrados, se encontraron {len(prompts)}"

        # Verificar presencia de los 32 pasos (P01 a P32)
        for num in range(1, 33):
            code_str = f"p{num:02d}"
            matching = [name for name in prompt_names if f"paso_{code_str}" in name]
            assert len(matching) == 1, f"Falta el prompt del paso P{num:02d} en el catálogo MCP"

        # Verificar presencia de los 3 roles dedicados
        assert "rol_asesor_metodologico" in prompt_names
        assert "rol_investigador_grounded" in prompt_names
        assert "rol_revisor_contratos" in prompt_names

    asyncio.run(run())


def test_prompt_examples_validate_against_step_contracts():
    from mcp_server.prompts.templates import TEMPLATES_POR_PASO
    from thesis.services.step_contracts import CONTRACTS

    assert set(TEMPLATES_POR_PASO) == set(CONTRACTS)
    for code, template in TEMPLATES_POR_PASO.items():
        CONTRACTS[code].model_validate(template["esquema_json_ejemplo"])


def test_project_prompt_requires_authenticated_actor():
    from mcp_server.prompts.hydration import hydrate_project_context

    with patch("mcp_server.prompts.hydration.current_actor", side_effect=DomainError(
        "UNAUTHENTICATED", "Token MCP inválido"
    )):
        with pytest.raises(DomainError) as exc:
            hydrate_project_context(str(uuid4()))
    assert exc.value.code == "UNAUTHENTICATED"


def test_get_prompt_without_project_id():
    """Verifica la generación de un prompt en modo preliminar sin ID de proyecto."""
    async def run():
        res = await app.get_prompt("paso_p01_mapa_temas", {})
        assert res is not None
        assert len(res.messages) == 1
        text = res.messages[0].content.text

        assert "P01: Mapa de Temas Viables" in text
        assert "Protocolo de Tres Roles Secuenciales" in text
        assert "Fase 1: Asesor Metodológico" in text
        assert "Fase 2: Investigador Grounded" in text
        assert "Fase 3: Revisor de Contratos" in text
        assert "No se especificó `project_id`" in text
        assert "temas_propuestos" in text

    asyncio.run(run())


@pytest.mark.django_db(transaction=True)
def test_get_prompt_with_hydrated_project(monkeypatch):
    """Verifica que el prompt hidrate automáticamente los datos consolidados desde PostgreSQL."""
    from thesis.services.projects import create_project
    from thesis.services.mcp_auth import issue_token

    student = User.objects.create_user(
        email="tesista.prompts@utp.edu.pe",
        password="test-password-123",
        display_name="Tesista MCP Prompts",
    )
    monkeypatch.setenv("TESISMCP_MCP_TOKEN", issue_token(student))
    project = create_project(student, "Proyecto MCP Test Prompts", "Sistema de Prueba para el Motor de Prompts")

    # Enriquecer el perfil para la prueba de hidratación
    profile = project.profile
    profile.topic = "Arquitecturas Multi-Agente en Educación Superior"
    profile.ods_code = "ODS-04:4.4"
    profile.lock_version = 5
    profile.save()

    async def run():
        res = await app.get_prompt(
            "paso_p04_delimitacion_titulo",
            {"project_id": str(project.id), "detalle_estudiante": "Deseo enfocarlo en la UTP Sede Piura"}
        )
        assert res is not None
        text = res.messages[0].content.text

        # Comprobar hidratación desde PostgreSQL
        assert str(project.id) in text
        assert "Sistema de Prueba para el Motor de Prompts" in text
        assert "Arquitecturas Multi-Agente en Educación Superior" in text
        assert "ODS-04:4.4" in text
        assert "lock_version" in text
        assert "`5`" in text
        assert "Deseo enfocarlo en la UTP Sede Piura" in text
        assert "titulo_oficial" in text

    asyncio.run(run())


def test_all_32_step_prompts_load_successfully():
    """Comprueba que los 32 prompts de paso retornen contenido válido sin excepciones."""
    async def run():
        prompts = await app.list_prompts()
        step_prompts = [p for p in prompts if p.name.startswith("paso_p")]

        assert len(step_prompts) == 32

        for p in step_prompts:
            res = await app.get_prompt(p.name, {})
            assert res is not None
            assert len(res.messages) == 1
            content = res.messages[0].content.text
            assert len(content) > 200
            assert "Protocolo de Tres Roles Secuenciales" in content
            assert "guardar_paso" in content

    asyncio.run(run())


def test_dedicated_role_prompts():
    """Comprueba el funcionamiento de los 3 prompts de rol multi-agente."""
    async def run():
        # 1. Asesor metodológico
        res_adv = await app.get_prompt("rol_asesor_metodologico", {"consulta": "¿Cómo redacto mis hipótesis?"})
        text_adv = res_adv.messages[0].content.text
        assert "Modo Asesor Metodológico Principal" in text_adv
        assert "Taxonomía de Bloom" in text_adv
        assert "¿Cómo redacto mis hipótesis?" in text_adv

        # 2. Investigador Grounded
        res_inv = await app.get_prompt("rol_investigador_grounded", {"tema_o_criterio": "Model Context Protocol"})
        text_inv = res_inv.messages[0].content.text
        assert "Modo Investigador Grounded" in text_inv
        assert "buscar_antecedentes_peru" in text_inv
        assert "Model Context Protocol" in text_inv

        # 3. Revisor de contratos
        res_rev = await app.get_prompt("rol_revisor_contratos", {"paso_a_auditar": "P06"})
        text_rev = res_rev.messages[0].content.text
        assert "Modo Revisor de Contratos (Paso P06)" in text_rev
        assert "problema_central" in text_rev
        assert "pregunta_general" in text_rev

    asyncio.run(run())
