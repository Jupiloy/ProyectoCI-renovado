from django.apps import AppConfig


class ThesisConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "thesis"
    verbose_name = "TesisMCP"

    def ready(self):
        nombres_modelos = {
            "User": ("Usuario", "Usuarios"),
            "Project": ("Proyecto", "Proyectos"),
            "ProjectParticipant": ("Participante de proyecto", "Participantes de proyectos"),
            "ResearchProfile": ("Perfil de investigación", "Perfiles de investigación"),
            "ConsistencyRow": ("Fila de matriz de consistencia", "Filas de matriz de consistencia"),
            "ResearchVariable": ("Variable de investigación", "Variables de investigación"),
            "ConsistencyRowVariable": ("Variable de fila de consistencia", "Variables de fila de consistencia"),
            "VariableDimension": ("Dimensión de variable", "Dimensiones de variables"),
            "Indicator": ("Indicador", "Indicadores"),
            "StepProgress": ("Avance de paso", "Avances de pasos"),
            "Chapter": ("Capítulo", "Capítulos"),
            "ChapterRevision": ("Revisión de capítulo", "Revisiones de capítulos"),
            "ReviewComment": ("Comentario de revisión", "Comentarios de revisión"),
            "ReviewEvent": ("Evento de revisión", "Eventos de revisión"),
            "McpAccessToken": ("Token de acceso MCP", "Tokens de acceso MCP"),
            "Instrument": ("Instrumento", "Instrumentos"),
            "InstrumentItem": ("Ítem de instrumento", "Ítems de instrumentos"),
            "InstrumentItemIndicator": ("Indicador de ítem", "Indicadores de ítems"),
            "SourceDocument": ("Documento fuente", "Documentos fuentes"),
            "SourceExcerpt": ("Extracto de fuente", "Extractos de fuentes"),
            "SourcePassage": ("Pasaje de fuente", "Pasajes de fuentes"),
            "SourceGrobidAnalysis": ("Análisis GROBID de fuente", "Análisis GROBID de fuentes"),
            "SourceMetadataCheck": ("Verificación de metadatos de fuente", "Verificaciones de metadatos de fuentes"),
            "EvidenceLink": ("Enlace de evidencia", "Enlaces de evidencias"),
            "DocumentJob": ("Trabajo de documento", "Trabajos de documentos"),
            "ManuscriptDocument": ("Documento de manuscrito", "Documentos de manuscritos"),
            "ManuscriptCitation": ("Cita de manuscrito", "Citas de manuscritos"),
        }
        for nombre_modelo, (singular, plural) in nombres_modelos.items():
            try:
                modelo = self.get_model(nombre_modelo)
                modelo._meta.verbose_name = singular
                modelo._meta.verbose_name_plural = plural
            except LookupError:
                pass
