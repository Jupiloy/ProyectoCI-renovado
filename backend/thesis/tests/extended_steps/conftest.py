import pytest
from django.contrib.auth import get_user_model

from thesis.models import ConsistencyRow, StepProgress
from thesis.services.projects import create_project


@pytest.fixture
def base_project_with_p08(db):
    users = get_user_model().objects
    owner = users.create_user(email="extended-owner@example.org", password="pass", display_name="Tesista Extendido")
    project = create_project(owner, "Tesis Completa 32 Pasos")

    # Simular pasos completados P01 a P08 con datos realistas en P04 y P06
    for i in range(1, 9):
        code = f"P{i:02d}"
        output = {}
        if code == "P04":
            output = {
                "variables_confirmadas": ["protocolo MCP", "reducción de observaciones"],
                "unidad_analisis_confirmada": "proyectos de tesis",
                "lugar_confirmado": "UTP Piura",
                "periodo_confirmado": 2026,
            }
        elif code == "P06":
            output = {
                "problema_central": "Falta de trazabilidad metodológica en revisiones de tesis",
                "causas_directas": ["Desconexión entre etapas", "Revisión manual dispersa"],
                "efectos_directos": ["Retrasos en entregas", "Inconsistencias de variables"],
                "pregunta_general": "¿Cómo influye el protocolo MCP en la reducción de observaciones?",
                "preguntas_especificas": [
                    "¿Cuál es la tasa de comentarios resueltos por entrega?",
                    "¿Cuál es el tiempo promedio de respuesta del asesor docente?",
                ],
            }
            ConsistencyRow.objects.create(
                project=project,
                ordinal=0,
                question_text=output["pregunta_general"],
            )
            for idx, q in enumerate(output["preguntas_especificas"], start=1):
                ConsistencyRow.objects.create(
                    project=project,
                    ordinal=idx,
                    question_text=q,
                )
        StepProgress.objects.create(
            project=project,
            step_code=code,
            status=StepProgress.Status.COMPLETED,
            output_json=output,
        )
    return owner, project
