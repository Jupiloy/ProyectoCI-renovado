# MEMORIA PERMANENTE Y REGLA DE ORO DEL PROYECTO: VERIFICACIÓN EN PROFUNDIDAD (GROUNDED TRUTH)

> 📌 **¿Eres un asistente o agente de IA que recién entra al proyecto?**  
> Para entender de qué va el sistema, el stack tecnológico, los roles de los 5 integrantes, el flujo "con manzanitas" y el mapa de código, consulta la **[Guía Maestra para Agentes (GUIA_AGENTE.md)](./GUIA_AGENTE.md)**.

> **DIRECTRIZ FUNDAMENTAL Y OBLIGATORIA DEL USUARIO:**
> El agente tiene terminantemente prohibido asumir, estimar, inventar o deducir datos sin verificación previa a texto completo. La exactitud, el rigor empírico y la imparcialidad técnica son la máxima prioridad; **no importa cuántos tokens o llamadas a herramientas consuma el proceso de verificación**.

---

## 1. Principio de Cero Tolerancia a Alucinaciones e Imparcialidad Estricta
* **Imparcialidad y objetividad técnica:** Prohibido el sesgo complaciente o dar respuestas complacientes por cortesía. Si una tecnología, enfoque, arquitectura o documento presenta limitaciones, riesgos, contradicciones, fallas críticas o falta de sustento empírico, el agente debe declararlo de forma directa, neutral e imparcial, evaluando pros y contras objetivos sin maquillar la realidad.
* **Nunca inventar cifras ni métricas:** Si un porcentaje, muestra ($n$), valor estadístico ($p$, $t$), año o título no aparece de forma **literal y textual** en la fuente primaria (PDF, base de datos o código fuente), **NO se puede escribir como número**. Si no está explícito, debe reportarse cualitativamente o admitir explícitamente que la fuente no proporciona esa métrica.
* **Distinción matemática estricta: Puntos Porcentuales vs. Variación Porcentual Relativa (%):**
  * Si un indicador pasa de 44.80% a 63.80%, la diferencia absoluta es de **19.00 puntos porcentuales**, NUNCA un incremento relativo del 19.00% (el incremento relativo matemático sería del 42.41%). Prohibido confundir puntos porcentuales con porcentajes relativos o tasas de crecimiento.
* **Conteo físico real de páginas:**
  * Prohibido estimar o inferir el número de páginas por el índice o la última sección numerada. El número de páginas DEBE ser verificado físicamente mediante herramientas del sistema (`pdfinfo`, `pdftotext`, capa `core.grounding`).
* **Inspección real de documentos:** Antes de citar o resumir un archivo PDF o documento descargado, es obligatorio haber inspeccionado su texto físico mediante herramientas de extracción directa (`pdftotext`, `view_file` o la capa `core.grounding`). Está prohibido guiarse únicamente por el nombre del archivo o por inferencias previas.
* **Títulos y autorías exactas:** Todo título de artículo, tesis o autor debe verificarse contra la carátula o portada oficial del documento, distinguiendo rigurosamente entre autores, asesores y jurados.

---

## 2. Protocolo Estricto de Fichas de Antecedentes (Filtro Anti-Alucinación)

Para cada candidato, estudio o antecedente evaluado, es obligatorio separar formalmente los siguientes campos:
1. **Metadatos Oficiales Comprobados en Portada/DOI:** Título exacto, autores oficiales (separados de asesores), tipo de grado/trabajo, institución, año, revista y enlace oficial.
2. **Nivel de Verificación Declarado:**
   * Indicar explícitamente si se inspeccionó el **PDF físico a texto completo** o si solo se consultaron **metadatos y resumen**.
   * Si solo se consultó resumen/metadatos, está terminantemente prohibido emitir juicios sobre el cuerpo metodológico interno (p. ej., prohibido afirmar que carece de grupo control o de pruebas inferenciales sin haber leído la tesis completa).
3. **Evidencia Localizada y Resultados Demostrados (con número de página física exacta):**
   * Toda afirmación de resultados o metodología debe indicar la página física o tabla exacta donde figura en el documento.
   * **No convertir capacidades propuestas en resultados demostrados:** Si un autor propone un sistema o repositorio (p. ej. lecciones aprendidas de UDEP) y declara que el impacto a largo plazo será evaluado posteriormente, debe reportarse como propuesta cualitativa, sin inventar mejoras temporales ni porcentajes.
4. **Pertinencia Funcional Específica para TesisMCP:**
   * Responder explícitamente qué función concreta de TesisMCP respalda:
     1. Búsqueda científica con fuentes comprobables.
     2. Redacción metodológica en etapas desacopladas.
     3. Seguimiento de tesis y métricas de avance (Dashboard).
     4. Revisión y observaciones del asesor.
5. **Clasificación:** Clasificar objetivamente como *Antecedente Directo*, *Apoyo Técnico* o *Contexto Local*.
6. **Control de Duplicados e Independencia:**
   * Comprobar siempre contra la selección base existente antes de presentar alternativas como "independientes" (no duplicar estudios ya seleccionados como URP).
7. **Limitaciones Objetivas y Reporte de Fallas Críticas:**
   * Reportar con total franqueza limitaciones de diseño (p. ej. preexperimental sin grupo control), restricciones de muestra y fallas empíricas reportadas por los propios autores (p. ej. la tasa de alucinación del 68% en referencias BibTeX de PaperOrchestrator).

---

## 3. Protocolo de Ejecución y Auditoría Obligatorio

Antes de generar o modificar documentación técnica, académica o código:
1. **Auditoría Previa Automatizada:**
   * Todo PDF incorporado debe registrarse en `core/grounding/audit_cli.py` con sus `paginas_esperadas`, título exacto y cifras textuales.
   * Ejecutar y verificar que pase con 100% de éxito:
     ```bash
     python3 -m core.grounding.audit_cli
     ```
2. **Consistencia Cruzada Universal:**
   * Comprobar que lo expresado en el informe principal (`docs/06_informe_final_curso/informe_academico_curso_integrador.md`) coincida de manera idéntica con la matriz de antecedentes (`docs/04_modulo_investigacion_y_busqueda/analisis_profundo_antecedentes.md`) y el repositorio de archivos (`docs/antecedentes_descargados/README.md`).
3. **Verificación de Enlaces y Recursos:** Todo enlace local en Markdown debe apuntar a un archivo que exista físicamente dentro de la carpeta del proyecto.
4. **Estilo de Citación Unificado:** El proyecto admite **APA 7ª edición e IEEE**. Cada documento académico debe usar de forma consistente el estilo que le corresponda, sin mezclar formatos dentro del mismo documento. Toda cita en el texto debe tener su referencia y toda referencia debe corresponder a una cita; los corchetes numéricos son válidos cuando el documento usa IEEE.

---

## 4. Prioridad de Calidad sobre Eficiencia de Tokens
* El agente debe tomarse todos los pasos necesarios, ejecutar comandos de terminal y leer archivos línea por línea las veces que sea necesario para estar 100% seguro de la veracidad de la información.
* Ante cualquier discrepancia entre la memoria de conversación y el contenido real de un archivo, **el archivo real en disco siempre prevalece sobre cualquier resumen previo**.

---

## 5. Barrera Automática de Finalización y Puerta de Verificación (Definition of Done Gate)
* **Prohibición Estricta de Cierre sin Ejecución:** El agente tiene terminantemente prohibido declarar una tarea como "terminada", "lista" o "resuelta" basándose en inspección visual, memoria o auto-evaluación abstracta.
* **Comando Determinista Obligatorio:** Antes de dar por concluido cualquier cambio o responder que un hito está completado, debe ejecutarse en consola:
  ```bash
  python3 scripts/verify_project.py
  ```
  Este comando ejecuta de forma unificada:
  1. **Auditoría Grounded:** 9/9 PDFs físicos verificados al 100% con títulos y citas literales.
  2. **Integridad Django:** `python backend/manage.py check` con 0 errores del sistema.
  3. **Archivos de migración:** `python backend/manage.py makemigrations --check --dry-run` asegura correspondencia entre modelos y archivos; no comprueba que la base activa esté actualizada.
     **Migraciones aplicadas (control separado):** `python backend/manage.py migrate --check --database default` debe pasar sobre la base configurada por `DATABASE_URL`. No aplica migraciones automáticamente. Las migraciones del entorno local se ensayan primero en una restauración aislada con backup DB+media probado; no confundir la base de pytest con la base activa.
  4. **Suite de Pruebas Automatizadas:** `pytest --reuse-db -q` con 100% de tests en verde.
  5. **Higiene de Repositorio (`repository-hygiene-auditor`):** Prevención de archivos masivos accidentales (problema de 1,730 Markdowns), verificación de `.gitignore`, ausencia de cachés (`__pycache__`) y archivos sobredimensionados no autorizados.
  6. **Consistencia Doc-Código:** Verificación de correspondencia exacta en modelos (59 tras BYOA local; B8 histórico tenía 58), migraciones (47, hasta 0047), pasos metodológicos (32), herramientas MCP (34), prompts (35) y ausencia de enlaces Markdown rotos. Si se añaden entidades o contratos, actualizar el verificador según el código real sin desactivar el control.
* **Condición Inviolable de Salida:** El comando **DEBE** retornar Código de Salida 0 (`exit code: 0`). Si falla, el agente debe auto-reparar el código antes de comunicarse con el usuario.
* **Reporte Obligatorio:** Toda entrega debe presentar la tabla de evidencia con comandos ejecutados, tiempos, códigos de salida y el veredicto explícito `[APROBADO_CON_EVIDENCIA / EXIT_CODE_0]`.
