"""Adaptadores MCP: sus reglas viven en thesis.services."""

from typing import Any
from uuid import UUID

from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.django_bridge import current_actor, setup_django


def _invoke(operation, *args, **kwargs):
    from django.db import connections
    from thesis.services.errors import DomainError

    try:
        return operation(current_actor(), *args, **kwargs)
    except DomainError as exc:
        raise ToolError(f"{exc.code}: {exc.message}") from exc
    finally:
        connections.close_all()


def _project_uuid(project_id: str) -> UUID:
    try:
        return UUID(project_id)
    except ValueError as exc:
        raise ToolError("VALIDATION_ERROR: project_id debe ser UUID") from exc


def register_project_tools(app) -> None:
    setup_django()
    from thesis.models import DocumentJob
    from thesis.services.document_jobs import enqueue_document_job, get_document_job
    from thesis.services.discovery import search_semantic_scholar
    from thesis.services.discovery_peru import search_peru_antecedents
    from thesis.services.evidence import locate_quote
    from thesis.services.evidence_links import create_evidence_link, list_evidence_links, review_evidence_link
    from thesis.services.exploration import explore_idea
    from thesis.services.grobid import get_source_grobid
    from thesis.services.manuscripts import list_manuscript_citations, list_manuscripts, read_manuscript_section
    from thesis.services.projects import create_project, get_project_state, register_idea
    from thesis.services.reviews import add_comment, assign_advisor, decide_chapter, list_comments, resolve_comment
    from thesis.services.search import search_passages
    from thesis.services.sources import enqueue_openalex_source, list_excerpts, list_sources
    from thesis.services.steps import get_chapter, save_step, submit_chapter

    @app.tool()
    def crear_proyecto(name: str, title: str | None = None) -> dict[str, Any]:
        """Crea un proyecto para el usuario autenticado del cliente MCP."""
        def operation(actor):
            project = create_project(actor, name, title)
            return get_project_state(actor, project.id)

        return _invoke(operation)

    @app.tool()
    def obtener_estado(project_id: str) -> dict[str, Any]:
        """Consulta el estado de un proyecto al que pertenece el usuario."""
        return _invoke(get_project_state, _project_uuid(project_id))

    @app.tool()
    def registrar_idea(project_id: str, description: str, expected_version: int) -> dict[str, Any]:
        """Guarda una idea provisional confirmada por el tesista, con control de versión."""
        return _invoke(register_idea, _project_uuid(project_id), description, expected_version)

    @app.tool()
    def explorar_idea(project_id: str) -> dict[str, Any]:
        """Busca literatura sobre la idea guardada; devuelve solo metadatos, no resultados demostrados."""
        return _invoke(explore_idea, _project_uuid(project_id))

    @app.tool()
    def buscar_semantic_scholar(project_id: str, query: str, limit: int = 5) -> dict[str, Any]:
        """Busca metadatos en Semantic Scholar; no inspecciona ni verifica el texto completo."""
        return _invoke(search_semantic_scholar, _project_uuid(project_id), query, limit)

    @app.tool()
    def buscar_antecedentes_peru(
        project_id: str,
        query: str,
        scope_filter: str = "todos",
        include_articles: bool = True,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Busca tesis en ALICIA y artículos con filiación peruana; no acredita revisión por pares ni inspección del PDF."""
        return _invoke(
            search_peru_antecedents,
            _project_uuid(project_id),
            query,
            scope_filter=scope_filter,
            include_articles=include_articles,
            limit=limit,
        )

    @app.tool()
    def incorporar_fuente_openalex(project_id: str, openalex_id: str) -> dict[str, Any]:
        """Consulta un ID OpenAlex y encola la descarga y extracción del PDF abierto, si existe."""
        return _invoke(enqueue_openalex_source, _project_uuid(project_id), openalex_id)

    @app.tool()
    def listar_fuentes(project_id: str) -> list[dict[str, Any]]:
        """Lista fichas y nivel real de inspección de las fuentes de un proyecto."""
        return _invoke(list_sources, _project_uuid(project_id))

    @app.tool()
    def consultar_extractos(project_id: str, source_id: str, page_no: int | None = None, limit: int = 20) -> dict[str, Any]:
        """Devuelve texto extraído y hash con número de página física; no valida afirmaciones científicas."""
        return _invoke(list_excerpts, _project_uuid(project_id), _project_uuid(source_id), page_no=page_no, limit=limit)

    @app.tool()
    def procesar_ocr(project_id: str, source_id: str) -> dict[str, Any]:
        """Encola OCR de un PDF escaneado; consulta el resultado mediante job_id."""
        return _invoke(enqueue_document_job, _project_uuid(project_id), _project_uuid(source_id), DocumentJob.Kind.OCR)

    @app.tool()
    def listar_borradores(project_id: str) -> list[dict[str, Any]]:
        """Lista borradores DOCX aportados; sus citas aún no están verificadas contra fuentes."""
        return _invoke(list_manuscripts, _project_uuid(project_id))

    @app.tool()
    def consultar_borrador(project_id: str, manuscript_id: str, offset: int = 0, limit: int = 5000) -> dict[str, Any]:
        """Devuelve un tramo de Markdown; no infiere páginas físicas ni valida fuentes."""
        return _invoke(read_manuscript_section, _project_uuid(project_id), _project_uuid(manuscript_id), offset=offset, limit=limit)

    @app.tool()
    def consultar_citas_borrador(project_id: str, manuscript_id: str, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        """Lista campos Word/Zotero por tramos; su contenido no comprueba la fuente externa."""
        return _invoke(list_manuscript_citations, _project_uuid(project_id), _project_uuid(manuscript_id), offset=offset, limit=limit)

    @app.tool()
    def analizar_fuente_grobid(project_id: str, source_id: str) -> dict[str, Any]:
        """Encola la extracción GROBID; devuelve job_id para consultar el estado."""
        return _invoke(enqueue_document_job, _project_uuid(project_id), _project_uuid(source_id), DocumentJob.Kind.GROBID)

    @app.tool()
    def consultar_analisis_grobid(project_id: str, source_id: str, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        """Consulta referencias extraídas automáticamente, distinguiéndolas de metadatos comprobados."""
        return _invoke(get_source_grobid, _project_uuid(project_id), _project_uuid(source_id), offset=offset, limit=limit)

    @app.tool()
    def indexar_fuente(project_id: str, source_id: str) -> dict[str, Any]:
        """Encola la generación de embeddings locales; devuelve job_id."""
        return _invoke(enqueue_document_job, _project_uuid(project_id), _project_uuid(source_id), DocumentJob.Kind.INDEX)

    @app.tool()
    def consultar_trabajo(project_id: str, job_id: str) -> dict[str, Any]:
        """Consulta el estado y resultado de un trabajo documental del proyecto."""
        return _invoke(get_document_job, _project_uuid(project_id), _project_uuid(job_id))

    @app.tool()
    def buscar_pasajes(project_id: str, query: str, limit: int = 5) -> dict[str, Any]:
        """Busca candidatos semánticos en pgvector; no afirma que sostengan una conclusión."""
        return _invoke(search_passages, _project_uuid(project_id), query, limit=limit)

    @app.tool()
    def guardar_paso(project_id: str, step_code: str, content_md: str, output_data: dict[str, Any],
                     expected_version: int, idempotency_key: str) -> dict[str, Any]:
        """Valida P01-P32 (Capítulos 1 al 7) y guarda una revisión completa confirmada por el tesista."""
        return _invoke(save_step, _project_uuid(project_id), step_code, content_md, output_data,
                       expected_version, idempotency_key)

    @app.tool()
    def consultar_capitulo(project_id: str, chapter_no: int) -> dict[str, Any]:
        """Lee progreso y revisión vigente de un capítulo autorizado."""
        return _invoke(get_chapter, _project_uuid(project_id), chapter_no)

    @app.tool()
    def enviar_capitulo(project_id: str, chapter_no: int) -> dict[str, Any]:
        """Envía al asesor un capítulo cuyos pasos están completos."""
        return _invoke(submit_chapter, _project_uuid(project_id), chapter_no)

    @app.tool()
    def asignar_asesor(project_id: str, email: str) -> dict[str, Any]:
        """Asigna un usuario existente como asesor activo del proyecto del tesista."""
        return _invoke(assign_advisor, _project_uuid(project_id), email)

    @app.tool()
    def consultar_observaciones(project_id: str, chapter_no: int) -> list[dict[str, Any]]:
        """Lista comentarios anclados a revisiones de un capítulo autorizado."""
        return _invoke(list_comments, _project_uuid(project_id), chapter_no)

    @app.tool()
    def observar_fragmento(project_id: str, chapter_no: int, start_cp: int, end_cp: int,
                           selected_text: str, body: str) -> dict[str, Any]:
        """El asesor comenta un fragmento exacto de la revisión vigente."""
        return _invoke(add_comment, _project_uuid(project_id), chapter_no,
                       start_cp, end_cp, selected_text, body)

    @app.tool()
    def decidir_capitulo(project_id: str, chapter_no: int, action: str, reason: str = "") -> dict[str, Any]:
        """El asesor solicita cambios, aprueba o reabre un capítulo con las guardas del dominio."""
        return _invoke(decide_chapter, _project_uuid(project_id), chapter_no, action, reason)

    @app.tool()
    def resolver_observacion(project_id: str, comment_id: int) -> dict[str, Any]:
        """El asesor marca como resuelta una observación del proyecto."""
        return _invoke(resolve_comment, _project_uuid(project_id), comment_id)

    @app.tool()
    def cotejar_doi(project_id: str, source_id: str) -> dict[str, Any]:
        """Encola el cotejo de metadatos Crossref; no verifica la portada ni las afirmaciones."""
        return _invoke(enqueue_document_job, _project_uuid(project_id), _project_uuid(source_id), DocumentJob.Kind.DOI_CHECK)

    @app.tool()
    def localizar_frase(project_id: str, source_id: str, quote: str, limit: int = 5) -> dict[str, Any]:
        """Localiza una frase en texto extraído y devuelve candidatos con página física."""
        return _invoke(locate_quote, _project_uuid(project_id), _project_uuid(source_id), quote, limit=limit)

    @app.tool()
    def vincular_evidencia(project_id: str, excerpt_id: int, claim_text: str, start_char: int,
                           end_char: int, matched_text: str, revision_id: int | None = None) -> dict[str, Any]:
        """Crea un vínculo candidato con texto físico y página; requiere confirmación del asesor."""
        return _invoke(create_evidence_link, _project_uuid(project_id), excerpt_id, claim_text,
                       start_char, end_char, matched_text, revision_id)

    @app.tool()
    def listar_vinculos_evidencia(project_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Lista vínculos, procedencia, página y decisión del asesor."""
        return _invoke(list_evidence_links, _project_uuid(project_id), limit=limit)

    @app.tool()
    def revisar_vinculo_evidencia(project_id: str, link_id: int, decision: str, note: str = "") -> dict[str, Any]:
        """El asesor confirma o rechaza un vínculo candidato con la fuente."""
        return _invoke(review_evidence_link, _project_uuid(project_id), link_id, decision, note)
