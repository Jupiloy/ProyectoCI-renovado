import pytest
from pydantic import ValidationError

from thesis.services.step_contracts import CONTRACTS, P09Output, P10Output, P15Output, P30Output
from thesis.services.steps import CHAPTER_STEPS
from thesis.step_catalogue import CATALOGO_PASOS


def test_catalogo_completo_32_pasos_y_7_capitulos():
    assert len(CONTRACTS) == 32
    assert set(CHAPTER_STEPS.keys()) == {1, 2, 3, 4, 5, 6, 7}
    total_steps_in_chapters = sum(len(steps) for steps in CHAPTER_STEPS.values())
    assert total_steps_in_chapters == 32
    assert set(CATALOGO_PASOS) == set(CONTRACTS)
    assert {code: chapter for chapter, codes in CHAPTER_STEPS.items() for code in codes} == {
        code: info["capitulo"] for code, info in CATALOGO_PASOS.items()
    }
    for number in range(1, 33):
        code = f"P{number:02d}"
        assert code in CONTRACTS

def test_validador_bloom_p09_exitoso_y_fallido():
    valido = {
        "objetivo_general": "Determinar el impacto de la herramienta digital en el rendimiento académico",
        "objetivos_especificos": [
            "Analizar el nivel inicial de competencias de los estudiantes",
            "Evaluar la percepción de los docentes sobre la plataforma",
        ],
    }
    obj = P09Output.model_validate(valido)
    assert obj.objetivo_general.startswith("Determinar")

    invalido = {
        "objetivo_general": "El presente estudio busca conocer el impacto de la herramienta",
        "objetivos_especificos": [
            "Analizar el nivel inicial",
            "Evaluar la percepción",
        ],
    }
    with pytest.raises(ValidationError) as exc:
        P09Output.model_validate(invalido)
    assert "verbo de Bloom válido" in str(exc.value)

def test_validador_preguntas_p10_con_signos():
    valido = {
        "pregunta_general": "¿De qué manera influye la arquitectura MCP en la trazabilidad de tesis?",
        "preguntas_especificas": [
            "¿Cuál es el nivel de adopción del protocolo en el equipo?",
            "¿Cómo se relacionan los contratos de validación con la reducción de alucinaciones?",
        ],
    }
    res = P10Output.model_validate(valido)
    assert res.pregunta_general.startswith("¿")

    sin_signos = {
        "pregunta_general": "De qué manera influye la arquitectura MCP",
        "preguntas_especificas": ["¿Cuál es el nivel de adopción?", "¿Cómo se relacionan?"],
    }
    with pytest.raises(ValidationError):
        P10Output.model_validate(sin_signos)

def test_validador_embudo_prisma_p15():
    valido = {
        "registros_identificados": 120,
        "registros_duplicados_removidos": 20,
        "registros_cribados": 100,
        "articulos_evaluados_texto_completo": 35,
        "estudios_incluidos": 12,
    }
    p15 = P15Output.model_validate(valido)
    assert p15.estudios_incluidos == 12

    invalido = {
        "registros_identificados": 50,
        "registros_duplicados_removidos": 0,
        "registros_cribados": 80,  # Imposible cribar más de los identificados
        "articulos_evaluados_texto_completo": 30,
        "estudios_incluidos": 10,
    }
    with pytest.raises(ValidationError) as exc:
        P15Output.model_validate(invalido)
    assert "embudo PRISMA" in str(exc.value)

def test_validador_cuestionario_likert_p30():
    valido = {
        "nombre_instrumento": "Cuestionario de Usabilidad y Trazabilidad Metodológica",
        "poblacion_objetivo": "Estudiantes y asesores de ingeniería UTP Sede Piura",
        "banco_items": [
            {
                "numero": i,
                "dimension_asociada": "Usabilidad Técnica",
                "indicador": "Facilidad de uso percibida",
                "enunciado_reactivo": f"El sistema responde de manera predecible en el paso {i}",
                "tipo_escala": "LIKERT_5",
            }
            for i in range(1, 6)
        ],
    }
    p30 = P30Output.model_validate(valido)
    assert len(p30.banco_items) == 5
