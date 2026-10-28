import copy
import hashlib
from uuid import uuid4

import pytest

from thesis.models import ResearchVariable, StepProgress
from thesis.services.errors import DomainError
from thesis.services.projects import get_project_state
from thesis.services.steps import save_step


def test_flujo_capitulos_4_5_6_grounding_y_metodologia(base_project_with_p08):
    from thesis.models import SourceDocument, SourceExcerpt

    owner, project = base_project_with_p08

    # Simular P09-P12 completados y variables creadas
    for code, out in [
        ("P09", {"objetivos_especificos": ["A", "B"]}),
        ("P10", {"preguntas_especificas": ["¿A?", "¿B?"]}),
        ("P11", {"tipo_investigacion": "CORRELACIONAL", "hipotesis_especificas": ["H1", "H2"]}),
        ("P12", {}),
        ("P13", {}),
        ("P14", {"anio_inicio": 2021, "anio_fin": 2025}),
        ("P15", {"estudios_incluidos": 3}),
    ]:
        StepProgress.objects.create(
            project=project, step_code=code, status=StepProgress.Status.COMPLETED, output_json=out
        )

    ResearchVariable.objects.create(
        project=project, ordinal=1, role=ResearchVariable.Role.INDEPENDENT, name="protocolo MCP"
    )
    ResearchVariable.objects.create(
        project=project, ordinal=2, role=ResearchVariable.Role.DEPENDENT, name="reducción de observaciones"
    )

    # Registrar 3 fuentes reales (SourceDocument) en el proyecto
    sources = []
    excerpts = []
    for idx in range(1, 4):
        src = SourceDocument.objects.create(
            project=project,
            kind=SourceDocument.Kind.EXTERNAL,
            openalex_id=f"https://openalex.org/W202400{idx}",
            title=f"Estudio Empírico sobre Agentes y Validación {idx}",
            publication_year=2024,
            doi=f"10.1234/mcp.2024.{idx}",
            storage_key=f"sources/test-{idx}.pdf",
            sha256=f"{idx}" * 64,
            page_count=2,
            verification_status=SourceDocument.Status.TEXT_CHECKED,
        )
        excerpt_text = f"Texto extraído físicamente para la fuente {idx}."
        excerpt = SourceExcerpt.objects.create(
            source=src, chunk_no=1, page_no=1, text=excerpt_text,
            text_sha256=hashlib.sha256(excerpt_text.encode()).hexdigest(),
        )
        sources.append(src)
        excerpts.append(excerpt)

    def evidence_for(index):
        return {"excerpt_id": excerpts[index - 1].id,
                "cita_textual": excerpts[index - 1].text}

    # Un registro de catálogo con solo metadatos no puede entrar en la matriz.
    sources[0].verification_status = SourceDocument.Status.METADATA_CHECKED
    sources[0].save(update_fields=["verification_status"])
    metadata_only = [
        {
            "autores": f"Autor {i}", "anio": 2024,
            "titulo": f"Estudio Empírico sobre Agentes y Validación {i}",
            "metodologia": "Cuasiexperimental", "muestra": "50 proyectos",
            "hallazgo_principal": "Reducción significativa de errores de formato y consistencia",
            "doi": f"10.1234/mcp.2024.{i}",
            "metodologia_evidencia": evidence_for(i),
            "muestra_evidencia": evidence_for(i),
            "hallazgo_evidencia": evidence_for(i),
        }
        for i in range(1, 4)
    ]
    with pytest.raises(DomainError) as exc_metadata:
        save_step(owner, project.id, "P16", "# Matriz", {"estudios": metadata_only}, 0, str(uuid4()))
    assert exc_metadata.value.code == "UNVERIFIED_SOURCE"
    sources[0].verification_status = SourceDocument.Status.TEXT_CHECKED
    sources[0].save(update_fields=["verification_status"])

    # 1. Intentar guardar P16 con un paper inventado (alucinado) -> debe fallar con UNVERIFIED_SOURCE
    estudios_alucinados = [
        {
            "autores": f"Autor {i}",
            "anio": 2024,
            "titulo": f"Estudio Empírico sobre Agentes y Validación {i}" if i < 3 else "Paper Inventado por el LLM",
            "metodologia": "Cuasiexperimental",
            "muestra": "50 proyectos",
            "hallazgo_principal": "Reducción significativa de errores de formato y consistencia",
            "doi": f"10.1234/mcp.2024.{i}" if i < 3 else "10.9999/fake.doi",
            "metodologia_evidencia": evidence_for(i),
            "muestra_evidencia": evidence_for(i),
            "hallazgo_evidencia": evidence_for(i),
        }
        for i in range(1, 4)
    ]
    with pytest.raises(DomainError) as exc_fake:
        save_step(
            actor=owner,
            project_id=project.id,
            step_code="P16",
            content_md="# Matriz de Literatura con paper falso",
            output_data={"estudios": estudios_alucinados},
            expected_version=0,
            idempotency_key=str(uuid4()),
        )
    assert exc_fake.value.code == "UNVERIFIED_SOURCE"

    # 2. Guardar P16 con las 3 fuentes reales verificadas -> exitoso y vincula source_id
    estudios_reales = [
        {
            "autores": f"Autor {i}",
            "anio": 2024,
            "titulo": f"Estudio Empírico sobre Agentes y Validación {i}",
            "metodologia": "Cuasiexperimental",
            "muestra": "50 proyectos",
            "hallazgo_principal": "Reducción significativa de errores de formato y consistencia",
            "doi": f"10.1234/mcp.2024.{i}",
            "metodologia_evidencia": evidence_for(i),
            "muestra_evidencia": evidence_for(i),
            "hallazgo_evidencia": evidence_for(i),
        }
        for i in range(1, 4)
    ]
    cita_inventada = copy.deepcopy(estudios_reales)
    cita_inventada[0]["hallazgo_evidencia"]["cita_textual"] = "Una cita inventada que no aparece en el PDF."
    with pytest.raises(DomainError) as exc_quote:
        save_step(owner, project.id, "P16", "# Matriz", {"estudios": cita_inventada}, 0, str(uuid4()))
    assert exc_quote.value.code == "UNVERIFIED_SOURCE"
    doi_inventado = copy.deepcopy(estudios_reales)
    doi_inventado[0]["doi"] = "10.9999/incorrecto"
    with pytest.raises(DomainError) as exc_doi:
        save_step(owner, project.id, "P16", "# Matriz", {"estudios": doi_inventado}, 0, str(uuid4()))
    assert exc_doi.value.code == "SOURCE_METADATA_MISMATCH"
    res_p16 = save_step(
        actor=owner,
        project_id=project.id,
        step_code="P16",
        content_md="# Matriz de Literatura Verificada",
        output_data={"estudios": estudios_reales},
        expected_version=0,
        idempotency_key=str(uuid4()),
    )
    assert res_p16["state_version"] == 1
    p16_saved = StepProgress.objects.get(project=project, step_code="P16").output_json
    assert p16_saved["estudios"][0]["source_id"] == str(sources[0].id)
    assert p16_saved["estudios"][0]["source_sha256"] == sources[0].sha256
    assert p16_saved["estudios"][0]["verification_level"] == "TEXT_EXTRACTED_WITH_QUOTES"
    assert p16_saved["estudios"][0]["hallazgo_evidencia"]["pagina_fisica"] == 1

    # Completar P17-P19 y probar validación P20 y P22 y P25
    for code in ["P17", "P18", "P19", "P20", "P21"]:
        StepProgress.objects.create(
            project=project, step_code=code, status=StepProgress.Status.COMPLETED, output_json={}
        )

    # 3. En P22 debe exigir que las variables de P11 figuren en los constructos
    res_p22 = save_step(
        actor=owner,
        project_id=project.id,
        step_code="P22",
        content_md="# Marco Conceptual",
        output_data={
            "constructos": [
                {
                    "termino": "Protocolo MCP",
                    "definicion": "Protocolo estándar de contexto para conectar modelos con herramientas verificadas.",
                    "cita_fuente": "Anthropic (2024)",
                },
                {
                    "termino": "Reducción de observaciones",
                    "definicion": "Disminución de incidencias metodológicas detectadas en revisiones de capítulos.",
                    "cita_fuente": "Elaboración propia (2026)",
                },
                {
                    "termino": "Trazabilidad académica",
                    "definicion": "Capacidad de vincular cada afirmación del manuscrito con su evidencia primaria.",
                    "cita_fuente": "Autor 1 (2024)",
                },
            ]
        },
        expected_version=1,
        idempotency_key=str(uuid4()),
    )
    assert res_p22["state_version"] == 2

    for code in ["P23", "P24"]:
        StepProgress.objects.create(
            project=project, step_code=code, status=StepProgress.Status.COMPLETED, output_json={}
        )

    # 4. En P25 valida coherencia con P11 (CORRELACIONAL) y actualiza ResearchProfile.approach
    res_p25 = save_step(
        actor=owner,
        project_id=project.id,
        step_code="P25",
        content_md="# Diseño Metodológico",
        output_data={
            "enfoque": "CUANTITATIVO",
            "diseno": "NO_EXPERIMENTAL",
            "nivel_alcance": "CORRELACIONAL",
            "corte_temporal": "TRANSVERSAL",
            "justificacion_diseno": "Se miden las variables en un único momento para evaluar su relación estadística.",
        },
        expected_version=2,
        idempotency_key=str(uuid4()),
    )
    assert res_p25["state_version"] == 3
    estado = get_project_state(owner, project.id)
    assert estado["approach"] == "QUANTITATIVE"
