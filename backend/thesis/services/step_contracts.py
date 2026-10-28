"""Contratos de salida de P01-P08; validan forma, no veracidad científica."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TemaCandidato(StrictOutput):
    id: int = Field(ge=1, le=10)
    titulo_tentativo: str = Field(min_length=10, max_length=200)
    pros: list[str] = Field(min_length=1)
    contras: list[str] = Field(min_length=1)
    viabilidad_preliminar: str = Field(pattern="^(ALTA|MEDIA|BAJA)$")


class P01Output(StrictOutput):
    temas_propuestos: list[TemaCandidato] = Field(min_length=5, max_length=10)
    tema_preseleccionado_id: int | None = Field(default=None, ge=1, le=10)

    @model_validator(mode="after")
    def check_ids(self):
        ids = [tema.id for tema in self.temas_propuestos]
        if len(set(ids)) != len(ids) or (self.tema_preseleccionado_id is not None and self.tema_preseleccionado_id not in ids):
            raise ValueError("Los identificadores de temas deben ser únicos y la preselección debe existir")
        return self


class CriterioEvaluacion(StrictOutput):
    acceso_a_datos: int = Field(ge=1, le=5)
    relevancia_profesional: int = Field(ge=1, le=5)
    brecha_conocimiento: int = Field(ge=1, le=5)
    recursos_disponibles: int = Field(ge=1, le=5)


class EvaluacionTema(StrictOutput):
    tema_id: int = Field(ge=1, le=10)
    titulo: str = Field(min_length=10)
    puntajes: CriterioEvaluacion
    puntaje_total: int = Field(ge=4, le=20)
    justificacion_eleccion: str = Field(min_length=20, max_length=500)

    @model_validator(mode="after")
    def check_total(self):
        if self.puntaje_total != sum(self.puntajes.model_dump().values()):
            raise ValueError("El puntaje total no coincide con sus criterios")
        return self


class P02Output(StrictOutput):
    matriz_comparativa: list[EvaluacionTema] = Field(min_length=3, max_length=3)
    tema_ganador_id: int
    tema_ganador_titulo: str

    @model_validator(mode="after")
    def check_winner(self):
        ids = [item.tema_id for item in self.matriz_comparativa]
        winners = [item for item in self.matriz_comparativa if item.tema_id == self.tema_ganador_id]
        if (len(set(ids)) != 3 or len(winners) != 1 or winners[0].titulo != self.tema_ganador_titulo
                or winners[0].puntaje_total < max(item.puntaje_total for item in self.matriz_comparativa)):
            raise ValueError("El tema ganador debe existir exactamente en la matriz")
        return self


class P03Output(StrictOutput):
    ods_principal_numero: int = Field(ge=1, le=17)
    ods_principal_nombre: str = Field(min_length=5, max_length=100)
    meta_ods_especifica: str = Field(min_length=3, max_length=20)
    argumento_alineacion: str = Field(min_length=50, max_length=600)
    linea_utp_vinculada: str = Field(min_length=5, max_length=150)


class P04Output(StrictOutput):
    titulo_oficial: str = Field(min_length=15, max_length=250)
    conteo_palabras: int = Field(ge=1, le=20)
    variables_confirmadas: list[str] = Field(min_length=1, max_length=2)
    unidad_analisis_confirmada: str = Field(min_length=3)
    lugar_confirmado: str = Field(min_length=3)
    periodo_confirmado: int = Field(ge=2024, le=2030)

    @model_validator(mode="after")
    def check_count(self):
        if self.conteo_palabras != len(self.titulo_oficial.split()):
            raise ValueError("El conteo de palabras declarado no coincide con el título")
        title = self.titulo_oficial.casefold()
        components = [*self.variables_confirmadas, self.unidad_analisis_confirmada,
                      self.lugar_confirmado, str(self.periodo_confirmado)]
        if any(value.casefold() not in title for value in components):
            raise ValueError("El título debe mencionar variables, unidad, lugar y periodo confirmados")
        return self


class P05Output(StrictOutput):
    contenido_markdown: str = Field(min_length=500)
    num_parrafos: int = Field(ge=3)
    palabras_totales: int = Field(ge=250, le=1200)

    @model_validator(mode="after")
    def check_counts(self):
        paragraphs = [value for value in self.contenido_markdown.split("\n\n") if value.strip()]
        if len(paragraphs) != self.num_parrafos or len(self.contenido_markdown.split()) != self.palabras_totales:
            raise ValueError("Los recuentos declarados no coinciden con el contenido")
        return self


class P06Output(StrictOutput):
    problema_central: str = Field(min_length=15, max_length=250)
    causas_directas: list[str] = Field(min_length=2, max_length=5)
    efectos_directos: list[str] = Field(min_length=2, max_length=5)
    pregunta_general: str = Field(min_length=20, max_length=250)
    preguntas_especificas: list[str] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def check_questions(self):
        if not self.pregunta_general.startswith("¿") or not self.pregunta_general.endswith("?"):
            raise ValueError("La pregunta general requiere signos de interrogación")
        return self


class DimensionJustificacion(StrictOutput):
    dimension: str = Field(pattern="^(TEORICA|PRACTICA|METODOLOGICA|SOCIAL)$")
    argumento: str = Field(min_length=60, max_length=800)


class P07Output(StrictOutput):
    justificaciones: list[DimensionJustificacion] = Field(min_length=4, max_length=4)
    resumen_ejecutivo: str = Field(min_length=80, max_length=600)

    @model_validator(mode="after")
    def check_dimensions(self):
        if {item.dimension for item in self.justificaciones} != {"TEORICA", "PRACTICA", "METODOLOGICA", "SOCIAL"}:
            raise ValueError("Se requieren las cuatro dimensiones sin duplicados")
        return self


class P08Output(StrictOutput):
    brecha_detectada: str = Field(min_length=30, max_length=400)
    aporte_propuesto: str = Field(min_length=30, max_length=400)
    estado_evidencia: str = Field(default="PENDING_EVIDENCE", pattern="^PENDING_EVIDENCE$")


VERBOS_BLOOM_PERMITIDOS = {
    "DETERMINAR", "ANALIZAR", "EVALUAR", "DISEÑAR", "IMPLEMENTAR",
    "PROPONER", "IDENTIFICAR", "COMPARAR", "ESTABLECER", "EXAMINAR",
    "MEDIR", "DEMOSTRAR", "OPTIMIZAR", "DESARROLLAR", "MODELAR",
}


# --- Capítulo 3: Objetivos, Preguntas e Hipótesis ---

class P09Output(StrictOutput):
    objetivo_general: str = Field(min_length=15, max_length=250)
    objetivos_especificos: list[str] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def check_bloom(self):
        first_word = self.objetivo_general.split()[0].upper().rstrip(":,;.")
        if first_word not in VERBOS_BLOOM_PERMITIDOS:
            raise ValueError(f"El objetivo general debe iniciar con un verbo de Bloom válido ('{first_word}')")
        for obj in self.objetivos_especificos:
            word = obj.split()[0].upper().rstrip(":,;.")
            if word not in VERBOS_BLOOM_PERMITIDOS:
                raise ValueError(f"Cada objetivo específico debe iniciar con un verbo de Bloom válido ('{word}')")
        return self


class P10Output(StrictOutput):
    pregunta_general: str = Field(min_length=15, max_length=250)
    preguntas_especificas: list[str] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def check_question_marks(self):
        for q in [self.pregunta_general, *self.preguntas_especificas]:
            q_clean = q.strip()
            if not q_clean.startswith("¿") or not q_clean.endswith("?"):
                raise ValueError(f"La pregunta '{q}' debe iniciar con '¿' y terminar con '?'")
        return self


class P11Output(StrictOutput):
    tipo_investigacion: str = Field(pattern="^(APLICADA|BASICA|DESCRIPTIVA|CORRELACIONAL|EXPLICATIVA)$")
    hipotesis_general: str = Field(min_length=15, max_length=300)
    hipotesis_especificas: list[str] = Field(min_length=2, max_length=4)
    variable_independiente: str = Field(min_length=3, max_length=120)
    variable_dependiente: str = Field(min_length=3, max_length=120)


class FilaOperacionalizacion(StrictOutput):
    variable: str = Field(min_length=3, max_length=120)
    definicion_conceptual: str = Field(min_length=20, max_length=400)
    definicion_operacional: str = Field(min_length=20, max_length=400)
    dimensiones: list[str] = Field(min_length=1, max_length=6)
    indicadores: list[str] = Field(min_length=1, max_length=10)
    escala_medicion: str = Field(pattern="^(NOMINAL|ORDINAL|INTERVALO|RAZON)$")


class P12Output(StrictOutput):
    matriz_operacionalizacion: list[FilaOperacionalizacion] = Field(min_length=1, max_length=4)


# --- Capítulo 4: Revisión de Literatura (Antecedentes) ---

class P13Output(StrictOutput):
    ecuacion_scopus: str = Field(min_length=10, max_length=500)
    ecuacion_ieee: str = Field(min_length=10, max_length=500)
    palabras_clave_es: list[str] = Field(min_length=2, max_length=10)
    palabras_clave_en: list[str] = Field(min_length=2, max_length=10)


class P14Output(StrictOutput):
    criterios_inclusion: list[str] = Field(min_length=2, max_length=6)
    criterios_exclusion: list[str] = Field(min_length=2, max_length=6)
    anio_inicio: int = Field(ge=2018, le=2026)
    anio_fin: int = Field(ge=2024, le=2026)
    idiomas_admitidos: list[str] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def check_years(self):
        if self.anio_inicio > self.anio_fin:
            raise ValueError("El año de inicio no puede ser mayor al año de fin")
        return self


class P15Output(StrictOutput):
    registros_identificados: int = Field(ge=1)
    registros_duplicados_removidos: int = Field(ge=0)
    registros_cribados: int = Field(ge=1)
    articulos_evaluados_texto_completo: int = Field(ge=1)
    estudios_incluidos: int = Field(ge=1)

    @model_validator(mode="after")
    def check_funnel(self):
        if not (self.registros_identificados >= self.registros_cribados >= self.articulos_evaluados_texto_completo >= self.estudios_incluidos):
            raise ValueError("El embudo PRISMA debe ser decreciente o igual en cada etapa de cribado")
        return self


class PasajeLiteratura(StrictOutput):
    excerpt_id: int = Field(gt=0)
    cita_textual: str = Field(min_length=10, max_length=600)


class FichaLiteratura(StrictOutput):
    source_id: str | None = Field(default=None, max_length=64)
    autores: str = Field(min_length=3, max_length=150)
    anio: int = Field(ge=2018, le=2026)
    titulo: str = Field(min_length=10, max_length=300)
    metodologia: str = Field(min_length=5, max_length=200)
    muestra: str = Field(min_length=3, max_length=100)
    hallazgo_principal: str = Field(min_length=15, max_length=400)
    doi: str | None = Field(default=None, max_length=100)
    verification_level: str | None = Field(default=None, max_length=50)
    paginas_reales: int | None = Field(default=None, ge=1)
    metodologia_evidencia: PasajeLiteratura
    muestra_evidencia: PasajeLiteratura
    hallazgo_evidencia: PasajeLiteratura


class P16Output(StrictOutput):
    estudios: list[FichaLiteratura] = Field(min_length=1, max_length=20)


class P17Output(StrictOutput):
    ejes_tematicos: list[str] = Field(min_length=2, max_length=6)
    consensos_literatura: list[str] = Field(min_length=1, max_length=6)
    discrepancias_o_debates: list[str] = Field(min_length=1, max_length=6)


class P18Output(StrictOutput):
    vacio_conocimiento_identificado: str = Field(min_length=30, max_length=500)
    justificacion_necesidad_estudio: str = Field(min_length=30, max_length=500)


class P19Output(StrictOutput):
    antecedentes_internacionales: str = Field(min_length=100)
    antecedentes_nacionales: str = Field(min_length=100)
    sintesis_comparativa: str = Field(min_length=50)


class P20Output(StrictOutput):
    estilo_citacion: str = Field(pattern="^(IEEE|APA_7)$")
    referencias_formateadas: list[str] = Field(min_length=1, max_length=50)


# --- Capítulo 5: Marco Teórico y Conceptual ---

class TeoriaBase(StrictOutput):
    nombre_teoria: str = Field(min_length=5, max_length=150)
    autores_principales: str = Field(min_length=3, max_length=120)
    anio_origen: int | None = Field(default=None, ge=1800, le=2026)
    postulado_central: str = Field(min_length=20, max_length=400)
    aplicabilidad_al_proyecto: str = Field(min_length=20, max_length=400)


class P21Output(StrictOutput):
    teorias: list[TeoriaBase] = Field(min_length=1, max_length=4)


class DefinicionConstructo(StrictOutput):
    termino: str = Field(min_length=2, max_length=100)
    definicion: str = Field(min_length=20, max_length=350)
    cita_fuente: str = Field(min_length=3, max_length=100)


class P22Output(StrictOutput):
    constructos: list[DefinicionConstructo] = Field(min_length=3, max_length=15)


class P23Output(StrictOutput):
    descripcion_relaciones: str = Field(min_length=40, max_length=800)
    diagrama_mermaid: str = Field(min_length=10)


class P24Output(StrictOutput):
    proposiciones_teoricas: list[str] = Field(min_length=2, max_length=8)


# --- Capítulo 6: Metodología ---

class P25Output(StrictOutput):
    enfoque: str = Field(pattern="^(CUANTITATIVO|CUALITATIVO|MIXTO)$")
    diseno: str = Field(pattern="^(EXPERIMENTAL|PREEXPERIMENTAL|CUASIEXPERIMENTAL|NO_EXPERIMENTAL)$")
    nivel_alcance: str = Field(pattern="^(EXPLORATORIO|DESCRIPTIVO|CORRELACIONAL|EXPLICATIVO)$")
    corte_temporal: str = Field(pattern="^(TRANSVERSAL|LONGITUDINAL)$")
    justificacion_diseno: str = Field(min_length=30, max_length=600)


class P26Output(StrictOutput):
    tecnicas_seleccionadas: list[str] = Field(min_length=1, max_length=5)
    instrumentos_previstos: list[str] = Field(min_length=1, max_length=5)
    procedimiento_recoleccion: str = Field(min_length=40, max_length=800)


class P27Output(StrictOutput):
    validez_instrumento: str = Field(pattern="^(JUICIO_EXPERTOS_AIKEN|ANALISIS_FACTORIAL|VALIDEZ_CONTENIDO)$")
    confiabilidad_metodo: str = Field(pattern="^(ALFA_CRONBACH|OMEGA_MCDONALD|KR_20|TEST_RETEST)$")
    criterio_aceptabilidad: str = Field(min_length=10, max_length=300)


class P28Output(StrictOutput):
    consentimiento_informado_requerido: bool
    principios_eticos_aplicados: list[str] = Field(min_length=2, max_length=6)
    politica_confidencialidad_datos: str = Field(min_length=30, max_length=500)


class P29Output(StrictOutput):
    contenido_markdown: str = Field(min_length=200)
    palabras_totales: int = Field(ge=100)

    @model_validator(mode="after")
    def check_words(self):
        actual = len(self.contenido_markdown.split())
        if actual != self.palabras_totales:
            raise ValueError("El recuento de palabras declarado no coincide con el contenido")
        return self


# --- Capítulo 7: Instrumentos de Recolección de Datos ---

class ItemCuestionario(StrictOutput):
    numero: int = Field(ge=1, le=60)
    dimension_asociada: str = Field(min_length=3, max_length=100)
    indicador: str = Field(min_length=3, max_length=100)
    enunciado_reactivo: str = Field(min_length=10, max_length=300)
    tipo_escala: str = Field(default="LIKERT_5", pattern="^(LIKERT_5|LIKERT_7|DICOTOMICA)$")


class P30Output(StrictOutput):
    nombre_instrumento: str = Field(min_length=5, max_length=150)
    poblacion_objetivo: str = Field(min_length=5, max_length=150)
    banco_items: list[ItemCuestionario] = Field(min_length=5, max_length=60)


class PreguntaGuia(StrictOutput):
    numero: int = Field(ge=1, le=30)
    eje_tematico: str = Field(min_length=3, max_length=100)
    pregunta_principal: str = Field(min_length=10, max_length=300)
    repregunta_profundizacion: str = Field(min_length=10, max_length=300)


class P31Output(StrictOutput):
    nombre_guia: str = Field(min_length=5, max_length=150)
    perfil_informante_clave: str = Field(min_length=10, max_length=200)
    preguntas: list[PreguntaGuia] = Field(min_length=3, max_length=25)


class P32Output(StrictOutput):
    tamanio_muestra_piloto: int = Field(ge=5, le=100)
    coeficiente_confiabilidad_obtenido: float = Field(ge=0.0, le=1.0)
    ajustes_redaccion_items: list[str] = Field(min_length=1, max_length=15)
    estado_instrumento: str = Field(pattern="^(CALIBRADO|REQUIERE_REVISION)$")


ALL_STEP_CONTRACTS = [
    P01Output, P02Output, P03Output, P04Output, P05Output, P06Output, P07Output, P08Output,
    P09Output, P10Output, P11Output, P12Output,
    P13Output, P14Output, P15Output, P16Output, P17Output, P18Output, P19Output, P20Output,
    P21Output, P22Output, P23Output, P24Output,
    P25Output, P26Output, P27Output, P28Output, P29Output,
    P30Output, P31Output, P32Output,
]

CONTRACTS = {f"P{number:02d}": contract for number, contract in enumerate(ALL_STEP_CONTRACTS, start=1)}
