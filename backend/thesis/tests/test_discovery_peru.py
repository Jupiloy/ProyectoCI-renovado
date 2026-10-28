from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from thesis.integrations.alicia import search_alicia_theses
from thesis.services.discovery_peru import _classify_locality, search_peru_antecedents
from thesis.services.errors import DomainError
from thesis.services.geography import resolve_geographic_scope
from thesis.services.projects import create_project


def test_geography_resolution_dynamic():
    # Caso 1: Región directa
    scope_piura = resolve_geographic_scope("Piura, Perú")
    assert scope_piura.region == "Piura"
    assert "UDEP" in scope_piura.local_institutions
    assert "sullana" in scope_piura.match_keywords

    # Caso 2: Provincia/Distrito perteneciente a la región
    scope_sullana = resolve_geographic_scope("Provincia de Sullana")
    assert scope_sullana.region == "Piura"

    # Caso 3: Otra región peruana
    scope_aqp = resolve_geographic_scope("Arequipa")
    assert scope_aqp.region == "Arequipa"
    assert "UNSA" in scope_aqp.local_institutions

    # Caso 4: Lugar no indexado previamente (fallback dinámico sin fallos)
    scope_custom = resolve_geographic_scope("Chachapoyas")
    assert scope_custom.region == "Chachapoyas"
    assert "chachapoyas" in scope_custom.match_keywords

    # Caso 5: Lugar vacío
    scope_empty = resolve_geographic_scope(None)
    assert scope_empty.region == "Perú"
    assert scope_empty.match_keywords == []


def test_locality_requires_complete_geographic_terms():
    lima = resolve_geographic_scope("Lima")
    piura_record = {"title": "Gestión académica en Piura", "institution": "Universidad Nacional de Piura"}
    assert _classify_locality(piura_record, lima)[0] is False
    assert _classify_locality({"title": "Estudio realizado en Perú", "institution": "Universidad de Piura"},
                             resolve_geographic_scope(None))[0] is False


def test_alicia_normalization_is_metadata_only():
    mock_payload = {
        "status": "OK",
        "resultCount": 1,
        "records": [{
            "id": "alicia-101",
            "title": "Sistema web para la gestión de proyectos de tesis en Piura",
            "authors": {"primary": {"García, Juan": {"role": ["author"]}}, "secondary": []},
            "publicationDates": ["2024"],
            "thesisDegreeGrantor": ["Universidad Nacional de Piura"],
            "urls": [{"url": "https://hdl.handle.net/11042/1234", "desc": "Repositorio"}],
            "dcDescriptionAbstract": ["Resumen de la tesis en la ciudad de Piura."],
        }],
    }
    response_mock = MagicMock()
    response_mock.__enter__.return_value = response_mock
    with patch("thesis.integrations.alicia.urlopen", return_value=response_mock), \
         patch("thesis.integrations.alicia.json.load", return_value=mock_payload):
        results = search_alicia_theses("sistema web tesis")

    assert len(results) == 1
    doc = results[0]
    assert doc["title"] == "Sistema web para la gestión de proyectos de tesis en Piura"
    assert doc["authors"] == ["García, Juan"]
    assert doc["publication_year"] == 2024
    assert doc["handle_url"] == "https://hdl.handle.net/11042/1234"
    assert doc["verification_level"] == "METADATA_ONLY"
    assert doc["full_text_inspected"] is False


def test_alicia_does_not_invent_institution_or_merge_advisors_with_authors():
    from thesis.integrations.alicia import _normalize_alicia_record

    result = _normalize_alicia_record({
        "id": "registro-1",
        "title": "Tesis de ejemplo",
        "authors": {"primary": {"Autora Real": {}}, "secondary": {"Asesor": {}}},
        "dcDateIssued": ["2024-05-10"],
    })
    assert result["authors"] == ["Autora Real"]
    assert result["publication_year"] == 2024
    assert result["institution"] is None


@pytest.mark.django_db
def test_search_peru_antecedents_classification_and_filters():
    users = get_user_model().objects
    owner = users.create_user(email="tesista-peru@example.org", password="pass")
    other = users.create_user(email="intruso@example.org", password="pass")
    project = create_project(owner, "Tesis Piura")

    # Configurar el lugar del perfil como Piura
    profile = project.profile
    profile.place = "Piura, Perú"
    profile.save(update_fields=["place"])

    fake_alicia_records = [
        {
            "source_origin": "ALICIA_CONCYTEC",
            "record_id": "1",
            "title": "Repositorio de lecciones de ingeniería",
            "authors": ["Cáceres, D."],
            "publication_year": 2025,
            "institution": "Universidad de Piura",
            "handle_url": "https://hdl.handle.net/11042/7457",
            "abstract": "Estudio desarrollado en el Campus Piura.",
            "verification_level": "METADATA_ONLY",
            "full_text_inspected": False,
        },
        {
            "source_origin": "ALICIA_CONCYTEC",
            "record_id": "2",
            "title": "Control de inventario en planta pesquera de Paita",
            "authors": ["López, M."],
            "publication_year": 2024,
            "institution": "Universidad Tecnológica del Perú",
            "handle_url": "https://repositorio.utp.edu.pe/handle/20.500.12867/999",
            "abstract": "Aplicado a una empresa de la provincia de Paita.",
            "verification_level": "METADATA_ONLY",
            "full_text_inspected": False,
        },
        {
            "source_origin": "ALICIA_CONCYTEC",
            "record_id": "3",
            "title": "Arquitectura de microservicios bancarios en Lima",
            "authors": ["Rojas, E."],
            "publication_year": 2023,
            "institution": "Pontificia Universidad Católica del Perú",
            "handle_url": "https://tesis.pucp.edu.pe/repositorio/handle/20.500.12404/555",
            "abstract": "Caso de estudio en San Isidro, Lima.",
            "verification_level": "METADATA_ONLY",
            "full_text_inspected": False,
        },
    ]

    with patch("thesis.services.discovery_peru.search_alicia_theses", return_value=fake_alicia_records), \
         patch("thesis.services.discovery_peru.search_peru_affiliated_articles", return_value=[]):

        # 1. Búsqueda con scope_filter="todos": debe incluir ambos y priorizar locales
        data_all = search_peru_antecedents(owner, project.id, "ingeniería de sistemas", scope_filter="todos")
        res_all = data_all["resultados"]
        assert len(res_all) == 3
        assert res_all[0]["es_local"] is True
        assert "LOCAL_POR_INSTITUCION" in res_all[0]["justificacion_local"]
        assert res_all[1]["es_local"] is True
        assert "LOCAL_POR_OBJETO_ESTUDIO" in res_all[1]["justificacion_local"]
        assert res_all[2]["es_local"] is False
        assert "NACIONAL" in res_all[2]["justificacion_local"]

        # 2. Búsqueda con scope_filter="locales": solo los 2 de Piura
        data_loc = search_peru_antecedents(owner, project.id, "ingeniería de sistemas", scope_filter="locales")
        res_loc = data_loc["resultados"]
        assert len(res_loc) == 2
        assert all(item["es_local"] is True for item in res_loc)

        # 3. Búsqueda con scope_filter="nacionales": solo el de Lima (no local)
        data_nac = search_peru_antecedents(owner, project.id, "ingeniería de sistemas", scope_filter="nacionales")
        res_nac = data_nac["resultados"]
        assert len(res_nac) == 1
        assert res_nac[0]["es_local"] is False

    # 4. Control de acceso: intruso rechazado con NOT_FOUND
    with pytest.raises(DomainError) as denied:
        search_peru_antecedents(other, project.id, "ingeniería de sistemas")
    assert denied.value.code == "NOT_FOUND"


@pytest.mark.django_db
def test_search_reports_provider_outages():
    owner = get_user_model().objects.create_user(email="busqueda@example.org", password="pass")
    project = create_project(owner, "Búsqueda Piura")
    project.profile.place = "Piura"
    project.profile.save(update_fields=["place"])
    unavailable = DomainError("SEARCH_UNAVAILABLE", "Proveedor caído")
    with patch("thesis.services.discovery_peru.search_alicia_theses", side_effect=unavailable), \
         patch("thesis.services.discovery_peru.search_peru_affiliated_articles", side_effect=unavailable):
        with pytest.raises(DomainError) as exc:
            search_peru_antecedents(owner, project.id, "tesis")
    assert exc.value.code == "SEARCH_UNAVAILABLE"


def test_openalex_articles_do_not_claim_peer_review():
    from thesis.integrations.peru_articles import search_peru_affiliated_articles

    payload = {"results": [
        {"id": "W1", "title": "Artículo", "type": "article", "authorships": []},
        {"id": "W2", "title": "Libro", "type": "book", "authorships": []},
    ]}
    response_mock = MagicMock()
    response_mock.__enter__.return_value = response_mock
    with patch("thesis.integrations.peru_articles.urlopen", return_value=response_mock), \
         patch("thesis.integrations.peru_articles.json.load", return_value=payload):
        result = search_peru_affiliated_articles("tesis")
    assert len(result) == 1
    assert result[0]["source_origin"] == "ARTICULO_CON_FILIACION_PERUANA"
    assert result[0]["peer_review_verified"] is False
