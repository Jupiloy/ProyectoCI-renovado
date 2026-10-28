"""Reglas de delimitación, consistencia y operacionalización."""

from thesis.models import ConsistencyRow, ConsistencyRowVariable, Indicator, ResearchVariable, VariableDimension
from thesis.services.errors import DomainError

from .registry import StepExecutionContext, _get_completed_step_output, register_step_handler


def _sync_consistency_rows(project: Project, field_name: str, general_value: str, specific_values: list[str],
                           truncate_extra: bool = False) -> None:
    """Template Helper para sincronizar la fila general (0) y las específicas (1..n) de la Matriz de Consistencia."""
    ConsistencyRow.objects.update_or_create(
        project=project,
        ordinal=0,
        defaults={field_name: general_value},
    )
    for idx, text_val in enumerate(specific_values, start=1):
        ConsistencyRow.objects.update_or_create(
            project=project,
            ordinal=idx,
            defaults={field_name: text_val},
        )
    if truncate_extra:
        ConsistencyRowVariable.objects.filter(
            consistency_row__project=project,
            consistency_row__ordinal__gt=len(specific_values),
        ).delete()
        ConsistencyRow.objects.filter(
            project=project,
            ordinal__gt=len(specific_values),
        ).delete()


@register_step_handler("P03")
def handle_p03_ods(ctx: StepExecutionContext) -> None:
    ctx.profile.ods_code = (
        f"ODS-{ctx.validated['ods_principal_numero']:02d}:{ctx.validated['meta_ods_especifica']}"
    )[:20]


@register_step_handler("P04")
def handle_p04_title(ctx: StepExecutionContext) -> None:
    ctx.project.title = ctx.validated["titulo_oficial"]
    ctx.project.save(update_fields=["title", "updated_at"])
    ctx.profile.unit_of_analysis = ctx.validated["unidad_analisis_confirmada"]
    ctx.profile.place = ctx.validated["lugar_confirmado"]
    ctx.profile.period_text = str(ctx.validated["periodo_confirmado"])


@register_step_handler("P06")
def handle_p06_problem(ctx: StepExecutionContext) -> None:
    p04_data = _get_completed_step_output(ctx.project, "P04")
    if any(
        value.casefold() not in ctx.validated["pregunta_general"].casefold()
        for value in p04_data.get("variables_confirmadas", [])
    ):
        raise DomainError("RULE_QUESTION_FORMAT", "La pregunta general debe mencionar las variables confirmadas")
    ctx.profile.problem_statement = ctx.validated["pregunta_general"]
    _sync_consistency_rows(
        project=ctx.project,
        field_name="question_text",
        general_value=ctx.validated["pregunta_general"],
        specific_values=ctx.validated.get("preguntas_especificas", []),
        truncate_extra=True,
    )


@register_step_handler("P09")
def handle_p09_objectives(ctx: StepExecutionContext) -> None:
    p04_data = _get_completed_step_output(ctx.project, "P04")
    if any(
        value.casefold() not in ctx.validated["objetivo_general"].casefold()
        for value in p04_data.get("variables_confirmadas", [])
    ):
        raise DomainError(
            "RULE_CONSISTENCY_MISMATCH",
            "El objetivo general debe mencionar las variables confirmadas en P04",
        )
    p06_data = _get_completed_step_output(ctx.project, "P06")
    preguntas_p06 = p06_data.get("preguntas_especificas", [])
    objetivos_esp = ctx.validated["objetivos_especificos"]
    if preguntas_p06 and len(objetivos_esp) != len(preguntas_p06):
        raise DomainError(
            "RULE_CONSISTENCY_MISMATCH",
            f"El número de objetivos específicos ({len(objetivos_esp)}) "
            f"debe coincidir con las preguntas específicas de P06 ({len(preguntas_p06)})",
        )
    _sync_consistency_rows(
        project=ctx.project,
        field_name="objective_text",
        general_value=ctx.validated["objetivo_general"],
        specific_values=objetivos_esp,
        truncate_extra=True,
    )


@register_step_handler("P10")
def handle_p10_questions(ctx: StepExecutionContext) -> None:
    p09_data = _get_completed_step_output(ctx.project, "P09")
    objetivos_p09 = p09_data.get("objetivos_especificos", [])
    preguntas_esp = ctx.validated["preguntas_especificas"]
    if len(preguntas_esp) != len(objetivos_p09):
        raise DomainError(
            "RULE_CONSISTENCY_MISMATCH",
            f"El número de preguntas específicas en P10 ({len(preguntas_esp)}) "
            f"debe coincidir con los objetivos específicos de P09 ({len(objetivos_p09)})",
        )
    _sync_consistency_rows(
        project=ctx.project,
        field_name="question_text",
        general_value=ctx.validated["pregunta_general"],
        specific_values=preguntas_esp,
        truncate_extra=False,
    )


@register_step_handler("P11")
def handle_p11_hypotheses_and_variables(ctx: StepExecutionContext) -> None:
    p09_data = _get_completed_step_output(ctx.project, "P09")
    objetivos_p09 = p09_data.get("objetivos_especificos", [])
    hipotesis_esp = ctx.validated["hipotesis_especificas"]
    if len(hipotesis_esp) != len(objetivos_p09):
        raise DomainError(
            "RULE_CONSISTENCY_MISMATCH",
            f"El número de hipótesis específicas en P11 ({len(hipotesis_esp)}) "
            f"debe coincidir con los objetivos específicos de P09 ({len(objetivos_p09)})",
        )
    p04_data = _get_completed_step_output(ctx.project, "P04")
    declared_vars = {
        ctx.validated["variable_independiente"].casefold(),
        ctx.validated["variable_dependiente"].casefold(),
    }
    for confirmed_var in p04_data.get("variables_confirmadas", []):
        if confirmed_var.casefold() not in declared_vars:
            raise DomainError(
                "RULE_CONSISTENCY_MISMATCH",
                f"La variable confirmada '{confirmed_var}' en P04 debe figurar como variable en P11",
            )
    _sync_consistency_rows(
        project=ctx.project,
        field_name="hypothesis_text",
        general_value=ctx.validated["hipotesis_general"],
        specific_values=hipotesis_esp,
        truncate_extra=False,
    )
    var_ind, _ = ResearchVariable.objects.update_or_create(
        project=ctx.project,
        ordinal=1,
        defaults={
            "role": ResearchVariable.Role.INDEPENDENT,
            "name": ctx.validated["variable_independiente"],
        },
    )
    var_dep, _ = ResearchVariable.objects.update_or_create(
        project=ctx.project,
        ordinal=2,
        defaults={
            "role": ResearchVariable.Role.DEPENDENT,
            "name": ctx.validated["variable_dependiente"],
        },
    )
    ConsistencyRowVariable.objects.filter(variable__project=ctx.project, variable__ordinal__gt=2).delete()
    ResearchVariable.objects.filter(project=ctx.project, ordinal__gt=2).delete()
    for row in ConsistencyRow.objects.filter(project=ctx.project):
        ConsistencyRowVariable.objects.get_or_create(consistency_row=row, variable=var_ind)
        ConsistencyRowVariable.objects.get_or_create(consistency_row=row, variable=var_dep)


@register_step_handler("P12")
def handle_p12_operationalization(ctx: StepExecutionContext) -> None:
    project_vars = list(ResearchVariable.objects.filter(project=ctx.project).order_by("ordinal"))
    vars_by_name = {v.name.casefold(): v for v in project_vars}
    incoming_names = {fila["variable"].casefold() for fila in ctx.validated["matriz_operacionalizacion"]}
    if not project_vars or incoming_names != set(vars_by_name.keys()):
        raise DomainError(
            "RULE_CONSISTENCY_MISMATCH",
            "Las variables en la matriz de operacionalización (P12) deben coincidir "
            "exactamente con las variables definidas en P11",
        )
    for fila in ctx.validated["matriz_operacionalizacion"]:
        var_obj = vars_by_name[fila["variable"].casefold()]
        var_obj.conceptual_definition = fila["definicion_conceptual"]
        var_obj.operational_definition = fila["definicion_operacional"]
        var_obj.save(update_fields=["conceptual_definition", "operational_definition"])
        Indicator.objects.filter(dimension__variable=var_obj).delete()
        dims = []
        for d_idx, dim_name in enumerate(fila["dimensiones"], start=1):
            dim_obj, _ = VariableDimension.objects.update_or_create(
                variable=var_obj,
                ordinal=d_idx,
                defaults={"name": dim_name},
            )
            dims.append(dim_obj)
        VariableDimension.objects.filter(variable=var_obj, ordinal__gt=len(dims)).delete()
        for i_idx, ind_name in enumerate(fila["indicadores"]):
            target_dim = dims[i_idx % len(dims)]
            dim_ordinal = (i_idx // len(dims)) + 1
            Indicator.objects.create(
                dimension=target_dim,
                ordinal=dim_ordinal,
                name=ind_name,
                measurement_scale=fila["escala_medicion"],
            )
