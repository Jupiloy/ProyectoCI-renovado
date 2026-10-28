"""Reglas de diseño metodológico e instrumentos."""

from uuid import UUID

from thesis.models import Indicator, Instrument, InstrumentItem, InstrumentItemIndicator, Project, ResearchProfile, VariableDimension
from thesis.services.errors import DomainError

from .registry import StepExecutionContext, _get_completed_step_output, register_step_handler


APPROACH_MAP = {
    "CUANTITATIVO": ResearchProfile.Approach.QUANTITATIVE,
    "CUALITATIVO": ResearchProfile.Approach.QUALITATIVE,
    "MIXTO": ResearchProfile.Approach.MIXED,
}

SCOPE_EQUIVALENCE = {
    "DESCRIPTIVA": "DESCRIPTIVO",
    "CORRELACIONAL": "CORRELACIONAL",
    "EXPLICATIVA": "EXPLICATIVO",
}



@register_step_handler("P25")
def handle_p25_methodology_design(ctx: StepExecutionContext) -> None:
    p11_data = _get_completed_step_output(ctx.project, "P11")
    tipo_p11 = p11_data.get("tipo_investigacion")
    expected_scope = SCOPE_EQUIVALENCE.get(tipo_p11)
    if expected_scope and ctx.validated["nivel_alcance"] != expected_scope:
        raise DomainError(
            "RULE_CONSISTENCY_MISMATCH",
            f"El nivel de alcance en P25 ({ctx.validated['nivel_alcance']}) no coincide con "
            f"el tipo de investigación declarado en P11 ({tipo_p11})",
        )
    ctx.profile.approach = APPROACH_MAP[ctx.validated["enfoque"]]


def _create_versioned_instrument(project: Project, kind: str, name: str, population: str, seed_xor: int) -> Instrument:
    prev_inst = Instrument.objects.filter(project=project, kind=kind).order_by("-version_no").first()
    return Instrument.objects.create(
        project=project,
        lineage_key=prev_inst.lineage_key if prev_inst else UUID(int=project.id.int ^ seed_xor),
        version_no=(prev_inst.version_no + 1) if prev_inst else 1,
        name=name,
        kind=kind,
        target_population=population,
    )


@register_step_handler("P30")
def handle_p30_questionnaire(ctx: StepExecutionContext) -> None:
    dims_by_name = {
        d.name.casefold(): d
        for d in VariableDimension.objects.filter(variable__project=ctx.project)
    }
    inds_by_key = {
        (ind.dimension_id, ind.name.casefold()): ind
        for ind in Indicator.objects.filter(dimension__variable__project=ctx.project)
    }
    validated_pairs = []
    seen_numbers = set()
    for item in ctx.validated["banco_items"]:
        if item["numero"] in seen_numbers:
            raise DomainError(
                "VALIDATION_ERROR",
                f"Número de ítem duplicado ({item['numero']}) en el cuestionario de P30",
            )
        seen_numbers.add(item["numero"])
        dim_obj = dims_by_name.get(item["dimension_asociada"].casefold())
        if dim_obj is None:
            raise DomainError(
                "RULE_CONSISTENCY_MISMATCH",
                f"La dimensión '{item['dimension_asociada']}' del ítem {item['numero']} en P30 "
                "no existe en la matriz de operacionalización (P12)",
            )
        ind_obj = inds_by_key.get((dim_obj.id, item["indicador"].casefold()))
        if ind_obj is None:
            raise DomainError(
                "RULE_CONSISTENCY_MISMATCH",
                f"El indicador '{item['indicador']}' del ítem {item['numero']} en P30 "
                f"no pertenece a la dimensión '{item['dimension_asociada']}' definida en P12",
            )
        validated_pairs.append((item, dim_obj, ind_obj))

    inst = _create_versioned_instrument(
        project=ctx.project,
        kind=Instrument.Kind.QUESTIONNAIRE,
        name=ctx.validated["nombre_instrumento"],
        population=ctx.validated["poblacion_objetivo"],
        seed_xor=30,
    )
    for item, dim_obj, ind_obj in validated_pairs:
        inst_item = InstrumentItem.objects.create(
            instrument=inst,
            dimension=dim_obj,
            ordinal=item["numero"],
            prompt_text=item["enunciado_reactivo"],
            response_scale=item["tipo_escala"],
        )
        InstrumentItemIndicator.objects.create(instrument_item=inst_item, indicator=ind_obj)


@register_step_handler("P31")
def handle_p31_interview_guide(ctx: StepExecutionContext) -> None:
    dims_by_name = {
        d.name.casefold(): d
        for d in VariableDimension.objects.filter(variable__project=ctx.project)
    }
    inst = _create_versioned_instrument(
        project=ctx.project,
        kind=Instrument.Kind.INTERVIEW,
        name=ctx.validated["nombre_guia"],
        population=ctx.validated["perfil_informante_clave"],
        seed_xor=31,
    )
    for q in ctx.validated["preguntas"]:
        dim_obj = dims_by_name.get(q["eje_tematico"].casefold())
        InstrumentItem.objects.create(
            instrument=inst,
            dimension=dim_obj,
            ordinal=q["numero"],
            prompt_text=q["pregunta_principal"],
            probe_text=q["repregunta_profundizacion"],
        )


@register_step_handler("P32")
def handle_p32_pilot_calibration(ctx: StepExecutionContext) -> None:
    if (
        ctx.validated["estado_instrumento"] == "CALIBRADO"
        and ctx.validated["coeficiente_confiabilidad_obtenido"] < 0.70
    ):
        raise DomainError(
            "RULE_CONSISTENCY_MISMATCH",
            "Un instrumento con coeficiente de confiabilidad menor a 0.70 no puede declararse CALIBRADO en P32",
        )
