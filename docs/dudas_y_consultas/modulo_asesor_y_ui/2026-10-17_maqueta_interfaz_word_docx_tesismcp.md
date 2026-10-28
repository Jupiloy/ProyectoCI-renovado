# Maqueta de Interfaz DOCX / Word para TesisMCP (Layout de 3 Paneles)

> **Estado respecto del producto actual (18/10/2026):** esta es una consulta histórica y puede describir alternativas descartadas. El alcance vigente usa `MCPServer` por `stdio`, API Django Ninja y panel Django Admin/Unfold para el asesor; no incluye frontend propio del tesista ni infraestructura pública seleccionada. Consulte [Estado verificable del producto](../../07_desarrollo_prototipo/estado_version_producto.md).


- **Fecha:** 2026-10-17
- **Categoría:** `modulo_asesor_y_ui`
- **Estado:** Resuelta / Maqueta Interactiva Generada
- **Participante / Rol:** Estudiante / Equipo TesisMCP (Rol 4: Frontend y UI / Rol 1: Arquitectura)

---

## ❓ 1. Pregunta o Duda Planteada

> **"Eso de la vista de árbol no me gusta, se sale un poco de la vista 'Word' o 'DOCX' que queríamos. ¿Puedes hacerme más o menos una maqueta de cómo quedaría? No capto la idea del frontend, el cómo se vería."**

El estudiante aclara que no desea vistas abstractas de grafos o diagramas de árbol (tipo Miro o canvas nodal) que rompan la familiaridad de los usuarios con Microsoft Word, Google Docs o documentos `.docx`. En su lugar, solicita una maqueta visual concreta de la interfaz centrada en la experiencia de redacción en hoja A4 tradicional, manteniendo la interacción con materiales a la izquierda y el asesor/IA a la derecha.

---

## 🖥️ 2. Maqueta Interactiva Generada

Se desarrolló una maqueta interactiva funcional completa en HTML5 y Tailwind CSS disponible como artefacto:
* **Archivo de la Maqueta:** [maqueta_frontend_word_tesismcp.html](maqueta_frontend_word_tesismcp.html)

---

## 📐 3. Arquitectura de los Tres Paneles

La maqueta elimina por completo lienzos nodales o esquemas abstractos y se enfoca 100% en el paradigma de un procesador de textos académico:

### 1. Barra Superior y Ribbon (Estilo Word / Google Docs)
* Icono azul de documento, título editable (`Informe_Final_Tesis_Sistemas_2026.docx`), etiqueta de estado "Guardado en la nube" y menú tradicional (`Archivo`, `Editar`, `Ver`, `Insertar`, `Formato`, `Herramientas`, `Asesor Metodológico`, `Conector MCP`).
* Cinta de herramientas (*Ribbon*): selector tipográfico (`Times New Roman 12pt` para APA 7), negrita, cursiva, subrayado, alineación justificada, estilos rápidos de títulos (Título 1, Título 2, Normal) y botones científicos directos:
  - 📖 **Insertar Cita APA (@):** Despliega las fuentes bibliográficas verificadas.
  - 🛡️ **Auditar Anti-Alucinación:** Comprueba que no existan cifras inventadas sin respaldo en los PDFs locales.

### 2. Panel Izquierdo: Materiales y Estructura (Estilo NotebookLM)
* **Pestaña 1 (Estructura DOCX):** Árbol de capítulos del informe final (Cap. 1 Planteamiento, Cap. 2 Marco Teórico, Cap. 3 Metodología, etc.) con sus páginas estimadas.
* **Pestaña 2 (Fuentes y Papers):** Lista de PDFs descargados con metadatos rigurosos (ej. *Chauca 2024, 132 págs, Pág. 103 validada*) y enlaces directos para abrir el PDF original.
* **Ficha de Variables Rápidas:** Tarjeta fija con la Variable Independiente, Variable Dependiente y tamaño de muestra ($n=103$).

### 3. Panel Central: La Hoja DOCX A4 (Procesador de Textos)
* **Hoja blanca realista (A4):** Centrada sobre fondo gris neutro, con márgenes estándar, encabezados institucionales de la universidad y número de página al pie.
* **Texto con formato formal APA 7:** Tipografía serifada, sangría en primera línea, espaciado e interlineado académico.
* **Citas interactivas:** Citas como `Chauca (2024, p. 103)` destacadas sutilmente que al hacer clic muestran el fragmento original del PDF.
* **Control de Cambios con Diff (Tipo Word):** Cuando la IA o el asesor sugieren una corrección, se muestra dentro del documento con **texto tachado en rojo** (original) y **texto nuevo en verde** (propuesta), con botones de `[✓ Aceptar Cambio]` y `[✕ Descartar]`.
* **Menú Flotante Contextual (Novel / TipTap):** Al seleccionar cualquier fragmento de texto con el cursor, aparece una pequeña barra flotante oscura con opciones rápidas: *Formalizar APA 7*, *Sintetizar*, *Citar Fuente*.

### 4. Panel Derecho: Asesor Humano y Conector FastMCP (BYOA)
* **Selector de Modo en el Encabezado:**
  - 🎓 **Asesor Metodológico (Humano):** Muestra las observaciones marginales oficiales enviadas por el docente revisor asignado (ej. *"Asegúrate de que la muestra de 103 egresados figure en el Cap. 2"*).
  - ⚡ **Agente FastMCP (BYOA):** Conecta con el servidor local FastMCP (`http://localhost:8000/sse`) para permitir que el estudiante use su propio agente (Antigravity, Claude Desktop o Cursor) directamente sobre el documento.
* **Historial de Consultas:** Chat interactivo para hacer preguntas metodológicas sin salir de la vista del Word.
* **Acciones de Auditoría Rápida:** Botones para validar la Matriz de Consistencia y comprobar citas bibliográficas en un clic.

---

## 🚀 4. Actualización V2: Incorporación del Paradigma Híbrido (Jenni AI + NotebookLM)

En la última actualización de la maqueta (`maqueta_frontend_word_tesismcp.html`), se integraron las siguientes capacidades clave derivadas del análisis de UX:

1. **Autocompletado Predictivo con `Tab` (Estilo Jenni AI):** Sugerencia en texto fantasma (*ghost text* en gris) que se acepta presionando la tecla `Tab` o haciendo clic en el pill contextual.
2. **Selector de Citación Rápida con `@`:** Popover interactivo con filtrado de fuentes bibliográficas verificadas.
3. **Visor de Fragmento Físico al Clic (Estilo NotebookLM):** Al hacer clic en un chip de cita como `Chauca (2024, p. 103) [1]`, se abre el diálogo modal que resalta el párrafo textual idéntico del PDF original con su número de página física auditada.
4. **Modal de Exportación DOCX Especializada:** Selector de exportación con citas nativas de Word (`<w:fldSimple>`) vs. hipervínculos, con bibliografía completa libre de paywalls.
5. **Checkboxes de Fuentes Activas en el Panel Izquierdo:** Control estricto de qué fuentes primarias alimentan el contexto en cada momento.

Para una explicación exhaustiva de este diseño conceptual, consultar el informe complementario:
* [`2026-10-17_paradigma_hibrido_jenni_ai_notebooklm_word.md`](./2026-10-17_paradigma_hibrido_jenni_ai_notebooklm_word.md)

