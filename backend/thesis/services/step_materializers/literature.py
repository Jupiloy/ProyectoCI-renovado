"""Reglas de literatura, referencias y constructos."""

from thesis.models import ResearchVariable, SourceDocument, SourceExcerpt
from thesis.services.errors import DomainError

from .registry import StepExecutionContext, _get_completed_step_output, register_step_handler


def _match_source_document(valid_sources: list[SourceDocument], estudio: dict) -> SourceDocument | None:
    sid = estudio.get("source_id")
    doi = (estudio.get("doi") or "").strip().casefold()
    title = estudio["titulo"].strip().casefold()
    for src in valid_sources:
        if sid:
            if str(src.id) == sid:
                return src
            continue
        if doi and src.doi and src.doi.strip().casefold() == doi:
            return src
        if src.title.strip().casefold() == title:
            return src
    return None


@register_step_handler("P16")
def handle_p16_literature_matrix(ctx: StepExecutionContext) -> None:
    p15_data = _get_completed_step_output(ctx.project, "P15")
    incluidos_p15 = p15_data.get("estudios_incluidos")
    if incluidos_p15 is not None and len(ctx.validated["estudios"]) != incluidos_p15:
        raise DomainError(
            "RULE_CONSISTENCY_MISMATCH",
            f"El número de estudios en P16 ({len(ctx.validated['estudios'])}) debe coincidir "
            f"exactamente con los estudios incluidos del embudo PRISMA en P15 ({incluidos_p15})",
        )
    p14_data = _get_completed_step_output(ctx.project, "P14")
    anio_ini = p14_data.get("anio_inicio", 2018)
    anio_fin = p14_data.get("anio_fin", 2026)
    valid_sources = list(SourceDocument.objects.filter(
        project=ctx.project,
        verification_status=SourceDocument.Status.TEXT_CHECKED,
        page_count__gt=0,
        storage_key__isnull=False,
        sha256__isnull=False,
    ).exclude(storage_key="").filter(excerpts__isnull=False).distinct())
    for estudio in ctx.validated["estudios"]:
        if not (anio_ini <= estudio["anio"] <= anio_fin):
            raise DomainError(
                "RULE_CONSISTENCY_MISMATCH",
                f"El estudio '{estudio['titulo']}' ({estudio['anio']}) está fuera del "
                f"rango temporal definido en P14 ({anio_ini}-{anio_fin})",
            )
        matched = _match_source_document(valid_sources, estudio)
        if matched is None:
            raise DomainError(
                "UNVERIFIED_SOURCE",
                f"El estudio '{estudio['titulo']}' requiere un PDF extraído con páginas físicas "
                "y extractos en este proyecto antes de incluirlo en P16",
            )
        if matched.title.strip().casefold() != estudio["titulo"].strip().casefold():
            raise DomainError("SOURCE_METADATA_MISMATCH", "El título de P16 no coincide con la ficha registrada")
        if matched.publication_year is not None and matched.publication_year != estudio["anio"]:
            raise DomainError("SOURCE_METADATA_MISMATCH", "El año de P16 no coincide con la ficha registrada")
        if matched.doi and estudio.get("doi") and matched.doi.strip().casefold() != estudio["doi"].strip().casefold():
            raise DomainError("SOURCE_METADATA_MISMATCH", "El DOI de P16 no coincide con la ficha registrada")
        for field in ("metodologia_evidencia", "muestra_evidencia", "hallazgo_evidencia"):
            evidence = estudio[field]
            excerpt = SourceExcerpt.objects.filter(pk=evidence["excerpt_id"], source=matched).first()
            if excerpt is None or evidence["cita_textual"] not in excerpt.text:
                raise DomainError(
                    "UNVERIFIED_SOURCE",
                    f"La cita textual de {field} para '{estudio['titulo']}' no aparece en "
                    "un extracto de la fuente seleccionada",
                )
            evidence["pagina_fisica"] = excerpt.page_no
            evidence["excerpt_sha256"] = excerpt.text_sha256
        if estudio.get("verification_level") is not None and estudio["verification_level"] != "TEXT_EXTRACTED_WITH_QUOTES":
            raise DomainError(
                "UNVERIFIED_SOURCE",
                f"El nivel de verificación de '{estudio['titulo']}' debe ser 'TEXT_EXTRACTED_WITH_QUOTES'",
            )
        if estudio.get("paginas_reales") is not None and estudio["paginas_reales"] != matched.page_count:
            raise DomainError(
                "SOURCE_METADATA_MISMATCH",
                f"El número de páginas afirmado ({estudio['paginas_reales']}) no coincide con el conteo físico del PDF ({matched.page_count})",
            )
        estudio["source_id"] = str(matched.id)
        estudio["source_sha256"] = matched.sha256
        estudio["verification_level"] = "TEXT_EXTRACTED_WITH_QUOTES"
        estudio["paginas_reales"] = matched.page_count


@register_step_handler("P20")
def handle_p20_references(ctx: StepExecutionContext) -> None:
    p16_data = _get_completed_step_output(ctx.project, "P16")
    estudios_p16 = p16_data.get("estudios", [])
    if len(ctx.validated["referencias_formateadas"]) < len(estudios_p16):
        raise DomainError(
            "RULE_CONSISTENCY_MISMATCH",
            f"El número de referencias en P20 ({len(ctx.validated['referencias_formateadas'])}) "
            f"no puede ser menor a los estudios incluidos en P16 ({len(estudios_p16)})",
        )


@register_step_handler("P22")
def handle_p22_constructs(ctx: StepExecutionContext) -> None:
    project_vars = list(ResearchVariable.objects.filter(project=ctx.project))
    terminos_definidos = [c["termino"].casefold() for c in ctx.validated["constructos"]]
    for var in project_vars:
        var_key = var.name.casefold()
        if not any(var_key in term or term in var_key for term in terminos_definidos):
            raise DomainError(
                "RULE_CONSISTENCY_MISMATCH",
                f"La variable '{var.name}' definida en P11 debe estar definida dentro de los constructos de P22",
            )
