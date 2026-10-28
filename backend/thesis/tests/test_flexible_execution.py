import hashlib
from uuid import uuid4
import pytest
from django.contrib.auth import get_user_model
from thesis.models import Chapter, ChapterRevision, ResearchProfile, StepProgress, SourceDocument, SourceExcerpt
from thesis.services.projects import create_project
from thesis.services.steps import save_step, submit_chapter, get_chapter
from thesis.services.workflows import get_workflow_state, create_or_update_draft, publish_workflow_draft
from thesis.services.errors import DomainError


@pytest.fixture
def flex_context(db):
    User = get_user_model()
    owner = User.objects.create_user(email="flex-owner@example.org", password="pass")
    advisor = User.objects.create_user(email="flex-advisor@example.org", password="pass")
    project = create_project(owner, "Tesis Flexible")
    from thesis.services.reviews import assign_advisor
    assign_advisor(owner, project.id, advisor.email)
    return owner, advisor, project


def get_p01_data():
    candidates = [
        {"id": i, "titulo_tentativo": f"Tema candidato número {i}", "pros": ["Acceso"],
         "contras": ["Tiempo"], "viabilidad_preliminar": "MEDIA"} for i in range(1, 6)
    ]
    return {"temas_propuestos": candidates, "tema_preseleccionado_id": 1}


def get_p04_data():
    return {
        "titulo_oficial": "Uso de herramientas digitales en estudiantes de Piura durante 2026",
        "conteo_palabras": 10,
        "variables_confirmadas": ["herramientas digitales"],
        "unidad_analisis_confirmada": "estudiantes",
        "lugar_confirmado": "Piura",
        "periodo_confirmado": 2026,
    }


def get_p14_data():
    return {
        "criterios_inclusion": ["Artículos empíricos indexados", "Publicaciones con revisión por pares"],
        "criterios_exclusion": ["Ensayos de opinión no contrastados", "Resúmenes de congresos sin datos"],
        "anio_inicio": 2020,
        "anio_fin": 2026,
        "idiomas_admitidos": ["Español", "Inglés"],
    }


def test_legacy_mode_enforces_strict_sequence(flex_context):
    owner, _, project = flex_context
    profile = ResearchProfile.objects.get(project=project)
    assert profile.workflow_mode == "LEGACY_SEQUENTIAL"

    # Step P01 succeeds
    save_step(owner, project.id, "P01", "Contenido P01", get_p01_data(), 0, str(uuid4()))

    # Attempting P03 without P02 fails with PREREQUISITE_LOCKED
    p03_data = {
        "ods_principal_numero": 4, "ods_principal_nombre": "Educación de calidad",
        "meta_ods_especifica": "4.4",
        "argumento_alineacion": "Texto de alineación con longitud suficiente de más de cincuenta caracteres para validar el contrato Pydantic.",
        "linea_utp_vinculada": "Tecnología educativa",
    }
    with pytest.raises(DomainError) as exc:
        save_step(owner, project.id, "P03", "Contenido P03", p03_data, 1, str(uuid4()))
    assert exc.value.code == "PREREQUISITE_LOCKED"
    assert "Completa P02 antes de P03" in exc.value.message


def test_progress_from_legacy_mode_is_not_reused_after_workflow_publication(flex_context):
    owner, _, project = flex_context
    save_step(owner, project.id, "P01", "Temas anteriores a configurar el recorrido", get_p01_data(), 0, str(uuid4()))
    get_workflow_state(owner, project.id)
    create_or_update_draft(owner, project.id, {"tasks": []}, expected_version=0)
    publish_workflow_draft(owner, project.id, "Activar ejecución versionada", expected_version=1)

    p02_data = {
        "matriz_comparativa": [
            {"tema_id": i, "titulo": f"Tema candidato número {i}",
             "puntajes": {"acceso_a_datos": 4, "relevancia_profesional": 4,
                          "brecha_conocimiento": 4, "recursos_disponibles": 4},
             "puntaje_total": 16, "justificacion_eleccion": "Se dispone de datos y tiempo suficiente."}
            for i in range(1, 4)
        ],
        "tema_ganador_id": 1,
        "tema_ganador_titulo": "Tema candidato número 1",
    }
    with pytest.raises(DomainError) as exc:
        save_step(owner, project.id, "P02", "No reutilizar salida de versión anterior", p02_data, 1, str(uuid4()))
    assert exc.value.code == "PREREQUISITE_LOCKED"
    assert "P01" in exc.value.message


def test_configurable_mode_allows_independent_advancement_and_blocks_unmet_dependencies(flex_context):
    owner, advisor, project = flex_context

    # Activate configurable graph mode by publishing a workflow
    get_workflow_state(owner, project.id)
    create_or_update_draft(owner, project.id, {"tasks": []}, expected_version=0)
    publish_workflow_draft(owner, project.id, "Activar grafo configurable", expected_version=1)

    profile = ResearchProfile.objects.get(project=project)
    assert profile.workflow_mode == "CONFIGURABLE_GRAPH"
    assert profile.active_workflow is not None

    # Step 1: Execute P01 (no prerequisites)
    res_p01 = save_step(owner, project.id, "P01", "Contenido P01", get_p01_data(), 0, str(uuid4()))
    assert res_p01["revision_no"] == 1
    rev1 = ChapterRevision.objects.get(pk=res_p01["revision_id"])
    assert rev1.workflow_version_no == profile.active_workflow.version_no
    assert "temas" in rev1.prompt_text_used.lower() or "p01" in rev1.prompt_text_used.lower()
    assert rev1.context_snapshot is not None

    # Step 2: Attempt P06 without P04 (P06 depends on P04) -> BLOCKED
    p06_data = {
        "problema_central": "Limitada adopción de herramientas digitales en la enseñanza universitaria",
        "causas_directas": ["Falta de capacitación técnica", "Infraestructura tecnológica insuficiente"],
        "efectos_directos": ["Bajo rendimiento académico", "Desmotivación estudiantil temprana"],
        "pregunta_general": "¿Cómo influyen las herramientas digitales en el rendimiento estudiantil?",
        "preguntas_especificas": ["¿Cuál es el nivel inicial?", "¿Cuál es el impacto final?"],
    }
    with pytest.raises(DomainError) as blocked:
        save_step(owner, project.id, "P06", "Contenido P06", p06_data, 1, str(uuid4()))
    assert blocked.value.code == "PREREQUISITE_LOCKED"
    assert "P04" in blocked.value.message

    # Step 3: Complete P04 by satisfying dependencies P01 -> P02 -> P03 -> P04
    p02_data = {
        "matriz_comparativa": [
            {"tema_id": i, "titulo": f"Tema candidato número {i}",
             "puntajes": {"acceso_a_datos": 4, "relevancia_profesional": 4, "brecha_conocimiento": 4, "recursos_disponibles": 4},
             "puntaje_total": 16, "justificacion_eleccion": "Se dispone de datos y tiempo suficiente."}
            for i in range(1, 4)
        ],
        "tema_ganador_id": 1,
        "tema_ganador_titulo": "Tema candidato número 1",
    }
    save_step(owner, project.id, "P02", "Contenido P02", p02_data, 1, str(uuid4()))

    p03_data = {
        "ods_principal_numero": 4, "ods_principal_nombre": "Educación de calidad",
        "meta_ods_especifica": "4.4",
        "argumento_alineacion": "Texto de alineación con longitud suficiente de más de cincuenta caracteres para validar el contrato Pydantic.",
        "linea_utp_vinculada": "Tecnología educativa",
    }
    save_step(owner, project.id, "P03", "Contenido P03", p03_data, 2, str(uuid4()))

    save_step(owner, project.id, "P04", "Contenido P04", get_p04_data(), 3, str(uuid4()))

    # Step 4: Advance P14 (Capítulo 4) BEFORE completing P05 (Capítulo 1)!
    # In legacy mode, P14 requires P13, P12, P11, ... P05 sequentially.
    # In configurable mode, P14 only requires P04 (delimitación confirmada).
    # Thus, P14 can be advanced independently!
    res_p14 = save_step(owner, project.id, "P14", "Criterios de inclusión", get_p14_data(), 4, str(uuid4()))
    assert res_p14["step_code"] == "P14"
    assert StepProgress.objects.filter(project=project, step_code="P14", status="COMPLETED").exists()


def test_submit_chapter_with_deactivated_optional_task(flex_context):
    owner, _, project = flex_context

    # Create draft where P05 is marked optional and deactivated
    get_workflow_state(owner, project.id)
    create_or_update_draft(owner, project.id, {
        "tasks": [
            {"task_id": "P05", "is_active": False, "is_optional": True}
        ]
    }, expected_version=0)
    publish_workflow_draft(owner, project.id, "Publicar sin P05", expected_version=1)

    # Complete P01, P02, P03
    save_step(owner, project.id, "P01", "Contenido P01", get_p01_data(), 0, str(uuid4()))

    p02_data = {
        "matriz_comparativa": [
            {"tema_id": i, "titulo": f"Tema candidato número {i}",
             "puntajes": {"acceso_a_datos": 4, "relevancia_profesional": 4, "brecha_conocimiento": 4, "recursos_disponibles": 4},
             "puntaje_total": 16, "justificacion_eleccion": "Se dispone de datos y tiempo suficiente."}
            for i in range(1, 4)
        ],
        "tema_ganador_id": 1,
        "tema_ganador_titulo": "Tema candidato número 1",
    }
    save_step(owner, project.id, "P02", "Contenido P02", p02_data, 1, str(uuid4()))

    p03_data = {
        "ods_principal_numero": 4, "ods_principal_nombre": "Educación de calidad",
        "meta_ods_especifica": "4.4",
        "argumento_alineacion": "Texto de alineación con longitud suficiente de más de cincuenta caracteres para validar el contrato Pydantic.",
        "linea_utp_vinculada": "Tecnología educativa",
    }
    save_step(owner, project.id, "P03", "Contenido P03", p03_data, 2, str(uuid4()))

    # Submitting Chapter 1 should block because P04 (protected and required) is missing!
    with pytest.raises(DomainError) as blocked:
        submit_chapter(owner, project.id, 1)
    assert blocked.value.code == "PREREQUISITE_LOCKED"
    assert "P04" in blocked.value.message

    # Complete P04
    save_step(owner, project.id, "P04", "Contenido P04", get_p04_data(), 3, str(uuid4()))

    # Now Chapter 1 has all active required tasks complete (P01, P02, P03, P04).
    # P05 is deactivated and optional, so submit_chapter succeeds!
    res = submit_chapter(owner, project.id, 1)
    assert res["status"] == Chapter.Status.READY
