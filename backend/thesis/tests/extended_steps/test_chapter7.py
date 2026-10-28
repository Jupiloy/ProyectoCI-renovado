from uuid import uuid4

import pytest

from thesis.models import Chapter, Indicator, ResearchVariable, StepProgress, VariableDimension
from thesis.services.errors import DomainError
from thesis.services.projects import get_project_state
from thesis.services.steps import save_step, submit_chapter


def test_flujo_capitulo_7_instrumentos_y_trazabilidad_indicadores(base_project_with_p08):
    from thesis.models import Instrument, InstrumentItem, InstrumentItemIndicator

    owner, project = base_project_with_p08

    # Crear variables, dimensiones e indicadores (como si P11 y P12 ya hubieran corrido)
    var = ResearchVariable.objects.create(
        project=project, ordinal=1, role=ResearchVariable.Role.INDEPENDENT, name="protocolo MCP"
    )
    dim = VariableDimension.objects.create(variable=var, ordinal=1, name="Validación de Esquemas")
    ind = Indicator.objects.create(
        dimension=dim, ordinal=1, name="Tasa de contratos válidos", measurement_scale="RAZON"
    )

    for i in range(9, 30):
        StepProgress.objects.create(
            project=project, step_code=f"P{i:02d}", status=StepProgress.Status.COMPLETED, output_json={}
        )

    # 1. Fallo en P30 si un ítem apunta a una dimensión o indicador inexistente ("huérfano")
    with pytest.raises(DomainError) as exc_orphan:
        save_step(
            actor=owner,
            project_id=project.id,
            step_code="P30",
            content_md="# Cuestionario con indicador inventado",
            output_data={
                "nombre_instrumento": "Cuestionario de Validación MCP",
                "poblacion_objetivo": "Tesistas de Ingeniería",
                "banco_items": [
                    {
                        "numero": idx,
                        "dimension_asociada": "Validación de Esquemas",
                        "indicador": "Indicador Huérfano No Registrado",
                        "enunciado_reactivo": f"El ítem {idx} evalúa una métrica inexistente en P12",
                        "tipo_escala": "LIKERT_5",
                    }
                    for idx in range(1, 6)
                ],
            },
            expected_version=0,
            idempotency_key=str(uuid4()),
        )
    assert exc_orphan.value.code == "RULE_CONSISTENCY_MISMATCH"

    # 2. Guardado exitoso de P30 con trazabilidad exacta a VariableDimension e Indicator
    res_p30 = save_step(
        actor=owner,
        project_id=project.id,
        step_code="P30",
        content_md="# Cuestionario Validado",
        output_data={
            "nombre_instrumento": "Cuestionario de Validación MCP",
            "poblacion_objetivo": "Tesistas de Ingeniería",
            "banco_items": [
                {
                    "numero": idx,
                    "dimension_asociada": "Validación de Esquemas",
                    "indicador": "Tasa de contratos válidos",
                    "enunciado_reactivo": f"El contrato del paso {idx} previene errores estructurales",
                    "tipo_escala": "LIKERT_5",
                }
                for idx in range(1, 6)
            ],
        },
        expected_version=0,
        idempotency_key=str(uuid4()),
    )
    assert res_p30["state_version"] == 1
    assert Instrument.objects.filter(project=project, kind=Instrument.Kind.QUESTIONNAIRE).count() == 1
    assert InstrumentItem.objects.filter(instrument__project=project, dimension=dim).count() == 5
    assert InstrumentItemIndicator.objects.filter(indicator=ind).count() == 5

    # 3. Guardado exitoso de P31 (Guía de Entrevista)
    res_p31 = save_step(
        actor=owner,
        project_id=project.id,
        step_code="P31",
        content_md="# Guía de Entrevista a Asesores",
        output_data={
            "nombre_guia": "Guía de Entrevista Semiestructurada para Asesores",
            "perfil_informante_clave": "Docentes asesores de tesis con más de 3 años de experiencia",
            "preguntas": [
                {
                    "numero": idx,
                    "eje_tematico": "Validación de Esquemas",
                    "pregunta_principal": f"¿Cómo evalúa la precisión del paso metodológico {idx}?",
                    "repregunta_profundizacion": "¿Qué casos de inconsistencia detectó con mayor frecuencia?",
                }
                for idx in range(1, 4)
            ],
        },
        expected_version=1,
        idempotency_key=str(uuid4()),
    )
    assert res_p31["state_version"] == 2
    assert Instrument.objects.filter(project=project, kind=Instrument.Kind.INTERVIEW).count() == 1

    # 4. Fallo en P32 si declara CALIBRADO con confiabilidad < 0.70, y éxito con >= 0.70
    with pytest.raises(DomainError) as exc_pilot:
        save_step(
            actor=owner,
            project_id=project.id,
            step_code="P32",
            content_md="# Piloto con baja confiabilidad",
            output_data={
                "tamanio_muestra_piloto": 15,
                "coeficiente_confiabilidad_obtenido": 0.55,
                "ajustes_redaccion_items": ["Se simplificó el ítem 2"],
                "estado_instrumento": "CALIBRADO",
            },
            expected_version=2,
            idempotency_key=str(uuid4()),
        )
    assert exc_pilot.value.code == "RULE_CONSISTENCY_MISMATCH"

    res_p32 = save_step(
        actor=owner,
        project_id=project.id,
        step_code="P32",
        content_md="# Piloto Calibrado Exitosamente",
        output_data={
            "tamanio_muestra_piloto": 20,
            "coeficiente_confiabilidad_obtenido": 0.86,
            "ajustes_redaccion_items": ["Se precisó la redacción técnica del ítem 3"],
            "estado_instrumento": "CALIBRADO",
        },
        expected_version=2,
        idempotency_key=str(uuid4()),
    )
    assert res_p32["state_version"] == 3
    cap7 = submit_chapter(owner, project.id, 7)
    assert cap7["status"] == Chapter.Status.READY
    estado_final = get_project_state(owner, project.id)
    assert len(estado_final["instruments"]) == 2
