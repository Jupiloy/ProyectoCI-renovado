# Protocolo de Ingeniería Agéntica en Bucle Cerrado y Optimización Flash

trigger: always_on

## 1. Filosofía de Ejecución: Bucle Cerrado (Closed-Loop)
El agente nunca debe operar en "bucle abierto" (escribir código y asumir que funciona). Gemini 3.8 Flash alcanza precisión de nivel frontier cuando está gobernado por mecanismos deterministas:

1. **TDD / Especificación por Pruebas (Test-First):**
   * Antes de implementar nueva lógica de negocio o resolver bugs no triviales, identificar o crear la prueba unitaria o de integración correspondiente (`pytest`, `vitest`, etc.).
   * El fallo de la prueba actúa como especificación ejecutable sin ambigüedad.
2. **Compilador y Linter como Árbitros Inmediatos:**
   * Prohibido dar una tarea por finalizada sin haber ejecutado la verificación sintáctica, de tipos o de tests en terminal (`python3 -m py_compile`, `pytest`, `mypy`, `ruff`, `tsc --noEmit`).
   * Si la herramienta arroja un error (`stderr`), el agente debe capturarlo, diagnosticar la causa raíz y auto-corregir inmediatamente antes de responder al usuario.
3. **Descomposición en Micro-Pasos Atómicos:**
   * Prohibido intentar refactorizar o reescribir archivos masivos (>150 líneas modificadas) en una sola pasada ciega.
   * Dividir siempre la ejecución en pasos incrementales y verificables: Contrato/Firma -> Test -> Implementación -> Verificación.

## 2. Higiene de Contexto y Prevención de "Context Rot"
Aunque la ventana de contexto sea de 1M+ tokens, la atención del modelo se degrada ante volcados innecesarios de archivos completos:

1. **Uso de Grafos y Símbolos en vez de Grep Ciego:**
   * Consultar primero `graphify` (`query_graph`, `shortest_path`, `get_node` o `~/.local/bin/graphify query`) para obtener el subgrafo relevante en lugar de volcar carpetas completas al contexto.
2. **Delegación a Subagentes de Solo Lectura:**
   * Para lecturas extensas de documentación, exploración masiva de directorios o búsqueda bibliográfica, invocar subagentes `research` (read-only). Esto preserva el hilo principal limpio para diseño y codificación.
3. **Mantenimiento Proactivo de Contexto:**
   * Cuando una sesión supere los 30 turnos de conversación o tras cerrar un hito de refactorización importante, sugerir o invocar `/compact` para podar el historial y mantener la precisión de razonamiento.

## 3. Especificación y Modelado Visual Previo (Spec-First)
1. **Clarificación Previa:** Ante tareas complejas con ambigüedad en los requisitos, usar `/grill-me` o formular preguntas directas para cerrar decisiones arquitectónicas antes de escribir código.
2. **Artefactos y Diagramas Mermaid:**
   * Antes de realizar cambios estructurales en backend, APIs o flujos de datos, plasmar el diseño en un artefacto Markdown con diagramas Mermaid (`flowchart`, `sequenceDiagram`, `stateDiagram`) y una lista de verificación (`[ ]`).
