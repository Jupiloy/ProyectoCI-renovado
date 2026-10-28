# Paradigma Híbrido: Jenni AI + NotebookLM + Word/Docs en TesisMCP

> **Estado respecto del producto actual (18/10/2026):** esta es una consulta histórica y puede describir alternativas descartadas. El alcance vigente usa `MCPServer` por `stdio`, API Django Ninja y panel Django Admin/Unfold para el asesor; no incluye frontend propio del tesista ni infraestructura pública seleccionada. Consulte [Estado verificable del producto](../../07_desarrollo_prototipo/estado_version_producto.md).


- **Fecha:** 2026-10-17
- **Categoría:** `modulo_asesor_y_ui`
- **Estado:** Resuelta
- **Participante / Rol:** Estudiante / Tesista & Asesor de Arquitectura de Software

---

## ❓ 1. Pregunta o Duda Planteada

> *"Me gusta cómo queda, pero siendo sincero dudo que la gente use lo nuestro para tipear, la mayoría optaría por hacerlo en Word. Tal vez lo nuestro nos permitiría hacer las ediciones básicas o tener la tecnología necesaria que se usaría para las tesis, pero dejar las herramientas para lo que están hechas. No sé cómo explicarme, lo que yo quiero hacer es como una mezcla de Jenni AI, Docs de Google (o Word) y NotebookLM."*

### Dimensiones de la consulta:
1. **Validación de la hipótesis de producto:** ¿Por qué un estudiante no escribiría una tesis de 150 páginas en un editor web desde cero?
2. **Deconstrucción del trinomio funcional:** ¿Qué aporta exactamente **Jenni AI**, qué aporta **Google NotebookLM** y qué aporta **Microsoft Word / Google Docs**?
3. **Definición del producto final:** ¿Cómo se estructura la experiencia de usuario (UX) e interoperabilidad técnica de TesisMCP para actuar como un *Estudio de Redacción Científica y Verificación Grounded* sin pretender ser un sustituto forzado de Word?

---

## 💡 2. Respuesta Fundamentada y Diagnóstico Crítico

### 2.1. Validación de la Observación: La Falacia del "Reemplazo de Word"

La intuición planteada es **100% acertada y estratégica**. En el ámbito académico y de posgrado, obligar al usuario a abandonar Microsoft Word para redactar la totalidad de su tesis es una de las causas principales de abandono de herramientas de software:

1. **La tiranía del formato universitario:** Las universidades imponen directivas de grados y títulos sumamente rígidas: márgenes disimétricos (3 cm superior/izquierdo, 2.5 cm inferior/derecho), numeración romana en páginas preliminares (i, ii, iii) y arábiga en el cuerpo, encabezados diferenciados por sección, tablas apaisadas (*landscape*) para matrices operacionales y sangría francesa estricta. Ningún editor web de tipo Markdown o WYSIWYG ligero puede competir con décadas de especificación OpenXML de Microsoft Word sin un esfuerzo de desarrollo desmedido.
2. **El ciclo de revisión del Asesor Humano:** Los asesores y jurados universitarios revisan borradores en archivos `.docx` utilizando el **Control de Cambios** (*Track Changes*) y comentarios al margen. Un asesor no se conectará a una plataforma web desconocida a aprender una interfaz nueva; exigirá que el estudiante le envíe el archivo `.docx`.
3. **La fatiga de la página en blanco vs. el taller de redacción:** El estudiante no necesita "otro procesador de texto". Lo que necesita desesperadamente es **asistencia de redacción científica anti-alucinación** para superar los bloqueos en secciones críticas (Planteamiento del Problema, Estado del Arte, Justificación y Discusión de Resultados), contrastando en tiempo real contra sus antecedentes descargados.

---

### 2.2. Deconstrucción Empírica del Trinomio Funcional

A continuación se detalla la investigación empírica realizada directamente sobre cada una de las tres herramientas de referencia:

```
                  ┌──────────────────────────────────────────────┐
                  │                 TesisMCP                     │
                  │   Estudio de Redacción y Grounding Académico │
                  └──────────────────────┬───────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
┌──────────────────┐           ┌──────────────────┐           ┌──────────────────┐
│   NotebookLM     │           │     Jenni AI     │           │   Word / Docs    │
│ (Grounding Base) │           │ (Drafting Flow)  │           │ (Ecosistema Doc) │
├──────────────────┤           ├──────────────────┤           ├──────────────────┤
│• Fuentes fijas   │           │• Autocomplete Tab│           │• Formato maestro │
│• Citas con pág.  │           │• Citación con @  │           │• Export .docx    │
│• Cero alucinación│           │• Parafraseo/Tono │           │• Citas de Word   │
│• Chat con PDFs   │           │• Chat contextual │           │• Control cambios │
└──────────────────┘           └──────────────────┘           └──────────────────┘
```

#### A. Google NotebookLM (El Núcleo Grounded / Anti-Alucinación)
- **Filosofía de diseño:** Sistema cerrado a fuentes específicas (*Source-grounded AI*).
- **Estructura de interfaz (3 columnas):**
  1. *Panel Izquierdo (Fuentes):* Permite subir PDFs de antecedentes, pegar directivas o enlazar URLs. Cada fuente puede activarse/desactivarse mediante casillas de verificación.
  2. *Panel Central (Chat & Consulta):* Respuestas restringidas rigurosamente al contenido de las fuentes activas.
  3. *Panel Derecho (Studio):* Generación de resúmenes de audio, mapas conceptuales, tablas de datos e informes estructurados a partir del corpus.
- **Mecánica clave de interacción:** Al generar un texto o respuesta, NotebookLM inserta **chips de cita numerados** (ej. `[1]`, `[10]`). Al pulsar sobre el chip, se despliega un modal interactivo que muestra el fragmento textual exacto y conduce a la página del documento fuente, eliminando toda posibilidad de citas falsas.

#### B. Jenni AI (El Estudio de Fluidez y Asistencia en Redacción)
- **Filosofía de diseño:** Editor enfocado en destrabar la escritura académica mediante microasistencias predictivas y citación embebida.
- **Mecánicas clave de interacción inspeccionadas en vivo:**
  1. **Autocompletado predictivo con `Tab`:** Conforme el usuario escribe, el sistema sugiere en texto fantasma (*ghost text*) el conector lógico o la continuación del argumento.
     - `Right Arrow` o `Tab`: Acepta la frase completa propuesta.
     - `Alt + →`: Acepta palabra por palabra para control fino del argumento.
     - `Ctrl + /`: Invoca explícitamente una sugerencia de redacción.
  2. **Citación rápida en línea con `@`:** Escribir `@` en cualquier parte del lienzo abre el selector de referencias bibliográficas, permitiendo buscar en los PDFs de la biblioteca o en repositorios académicos (Semantic Scholar) con filtros de año, Factor de Impacto (*Impact Factor 0.25+, 3+, 10+*) y recuento de citas (*Cited by 5+, 20+, 50+*).
  3. **Edición y transformación de tono (`Ctrl + J`):** Al seleccionar un párrafo, el menú contextual permite parafrasear, resumir, expandir o ajustar el tono hacia un registro académico formal.
  4. **Chat lateral con fuentes (`Ctrl + Y`):** Permite chatear con los documentos adjuntos utilizando menciones `@PDF` (ej. *"Compara la metodología de Huamán con la de Salas-Acuña"*).
  5. **Exportación e Interoperabilidad DOCX:** Dispone de dos modelos de exportación de citas:
     - *MS Word native citations:* Genera campos nativos de Word (`<w:fldSimple w:instr="CITATION ...">`), permitiendo que el Administrador de Referencias de Word y la bibliografía se mantengan sincronizados nativamente.
     - *Hyperlink citations:* Citas hipervinculadas con URL/DOI, ideal para trabajar en Google Docs.
     - *Layout presets:* Opciones de formateo preconfiguradas (*Jenni default*, *Double-spaced manuscript*, *Two-column paper*, y *Thesis or report* con interlineado 1.5, portada y tabla de contenido).
  6. **Fricción comercial detectada:** Jenni AI bloquea la exportación de bibliografías en su plan gratuito (*"References are a paid feature... Bibliography with 21 citations will be missing from exports"*). En TesisMCP, el grounding y las citas verificadas constituyen el núcleo abierto del sistema.

#### C. Microsoft Word & Google Docs (El Contenedor Maestro y Entregable Oficial)
- **Filosofía de diseño:** El estándar indiscutible de entrega de documentos oficiales, formateo de impresión y revisión por jurados.
- **Rol en el flujo:** TesisMCP no compite con el documento maestro de Word; se conecta a él mediante un flujo de **ida y vuelta (*Roundtrip DOCX*)**.

---

### 2.3. La Experiencia de Usuario (UX) de TesisMCP: El Estudio Híbrido

En lugar de pretender que el tesista escriba 150 páginas en un navegador, TesisMCP se posiciona como el **Taller de Redacción y Contrastación Científica (Academic Drafting & Grounding Studio)**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ BARRA SUPERIOR: [Archivo] [Importar .docx] [Exportar .docx] [Estilo: APA 7] [Páginas] │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ FUENTES & GROUNDING      │ ÁREA DE REDACCIÓN ASISTIDA  │ COPILOT & REVISIÓN ASESOR     │
│ (Estilo NotebookLM)      │ (Estilo Jenni AI / Word)    │ (Chat Contextual & Auditoría) │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 📁 Fuentes Primarias (9) │ 📄 Página Física (A4 / Word)│ 🤖 Asesor Metodológico / MCP  │
│ [x] Huamán 2024 (p.74)   │                             │                               │
│ [x] Salas 2023 (p.15)    │ 1.1 Formulación del Problema│ "He verificado que la cita de │
│ [x] Regalado 2024 (p.81) │                             │ Huamán (2024) coincide con la │
│                          │ En las universidades peruanas│ página 74 del PDF original."  │
│ ➕ Añadir Fuente (PDF)   │ la formulación de tesis pre-│                               │
│ 🔍 Buscar en ALICIA/IEEE │ senta demoras críticas [1]. │ 🔘 [Insertar en el texto]     │
│                          │                             │                               │
│ 📌 Notas Guardadas       │ Conector sugerido:          │ 💬 Observaciones del Asesor   │
│ • Hallazgos SOA Piura    │ "Esto coincide con lo de-   │ • "Falta contrastar con el    │
│ • Cifras de URP          │ mostrado por Salas (2023)..."│    estudio de Regalado."      │
│                          │ [Tab para aceptar]          │                               │
│                          │                             │ 📊 Auditoría Zero-LLM         │
│                          │ Presiona @ para citar       │ [✔ Citas 100% verificadas]    │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

#### Flujo de Trabajo Real del Estudiante:
1. **Fase 1: Carga y Grounding (NotebookLM):** El tesista arrastra los PDFs de sus antecedentes y la guía de tesis de su universidad. El motor `core.grounding` extrae el texto y numera físicamente las páginas.
2. **Fase 2: Redacción Asistida y Desbloqueo (Jenni AI):** El tesista no redacta todo el documento a la vez; redacta secciones complejas (ej. *Capítulo I: Planteamiento del Problema* o *Capítulo IV: Discusión*).
   - Escribe con autocompletado semántico (`Tab` para conectores formales).
   - Inserta antecedentes comprobados tipeando `@` (filtrando por sus PDFs locales).
   - Cada afirmación genera un chip de verificación `[pág. X]`.
3. **Fase 3: Exportación Sincronizada a Word (MS Word / Google Docs):**
   - El tesista hace clic en **"Exportar a Word (.docx)"**.
   - TesisMCP emite un archivo `.docx` con las citas formateadas como campos nativos de Word (`MS Word native citations`).
   - El tesista abre el `.docx` en su Microsoft Word habitual, pulsa "Actualizar Campos" en Referencias y obtiene la bibliografía oficial generada automáticamente.
   - El estudiante envía el `.docx` a su asesor para recibir comentarios y observaciones con control de cambios tradicional.

---

### 2.4. Decisión de Diseño: "Mantenerlo Básico" (Minimalismo Radical y Cero Sobrecarga Cognitiva)

Tras evaluar iteraciones visuales con múltiples paneles e indicadores, se establece como principio rector permanente para el frontend de TesisMCP: **Mantener la interfaz básica, sobria y libre de distracciones**.

1. **Evitar la "cabina de avión" (Feature Creep):** Si una herramienta de tesis se satura con decenas de botones, métricas flotantes, modales encadenados y paneles ruidosos, el estudiante experimenta sobrecarga cognitiva y rechaza el entorno. La familiaridad de un procesador limpio (tipo Google Docs o Word en modo lectura/redacción simple) es insustituible.
2. **Poder técnico invisible en el Backend FastMCP:** La complejidad de TesisMCP (grounding a texto completo, numeración de páginas físicas con `pdfinfo`/`pdftotext`, validadores Zero-LLM y contratos Pydantic P01–P08) debe operar **de forma silenciosa y eficiente en el backend**, sin obligar al usuario a manipular configuraciones técnicas avanzadas en la interfaz.
3. **El Trinomio Simplificado en la Práctica:**
   - **Lienzo central:** Una hoja A4 despejada y fluida para redactar o pegar el borrador del capítulo.
   - **Panel lateral único:** Un espacio integrado y colapsable para consultar dudas al asesor o a las fuentes subidas.
   - **Acción final evidente:** Un botón visible y directo de exportación a `.docx` con citas compatibles.

---

## 🛠️ 3. Especificación Técnica de Implementación

### 3.1. Arquitectura de Componentes Frontend (TipTap + Extensions)

Para lograr esta experiencia híbrida sin construir un procesador de textos desde cero, se utilizan las siguientes extensiones sobre el editor TipTap/Novel:

```typescript
// Configuración de Extensiones de TipTap para TesisMCP
import StarterKit from '@tiptap/starter-kit';
import { InlineGhostTextExtension } from './extensions/ghost-text';
import { MentionCitationExtension } from './extensions/mention-citation';
import { GroundedTooltipExtension } from './extensions/grounded-tooltip';

export const editorExtensions = [
  StarterKit.configure({
    history: true,
  }),
  // 1. Jenni AI Flow: Autocompletado predictivo con Tab
  InlineGhostTextExtension.configure({
    triggerKey: 'Tab',
    wordAcceptKey: 'Alt-ArrowRight',
    apiEndpoint: '/api/mcp/autocomplete',
  }),
  // 2. Jenni AI Flow: Citación en línea con @
  MentionCitationExtension.configure({
    suggestionChar: '@',
    apiEndpoint: '/api/grounding/sources',
  }),
  // 3. NotebookLM Flow: Chips de cita con tooltip y modal de página física
  GroundedTooltipExtension.configure({
    onChipClick: (sourceId, pageNumber) => {
      openPdfViewerModal(sourceId, pageNumber);
    },
  }),
];
```

### 3.2. Modelo de Exportación e Interoperabilidad DOCX (`python-docx`)

Para garantizar que el archivo `.docx` generado contenga citas compatibles nativamente con Microsoft Word:

```python
# Exportador de Citas Nativas para Microsoft Word (TesisMCP)
import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def agregar_cita_nativa_word(paragraph, autor, anio, titulo):
    """
    Inserta un campo nativo w:fldSimple con instrucción CITATION
    para que Microsoft Word lo reconozca en su Administrador de Fuentes.
    """
    run = paragraph.add_run()
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), f'CITATION {autor}{anio} \\l 10250 ')
    
    # Texto visible por defecto si los campos no se actualizan de inmediato
    r = OxmlElement('w:r')
    t = OxmlElement('w:t')
    t.text = f"({autor}, {anio})"
    r.append(t)
    fldSimple.append(r)
    
    run._r.append(fldSimple)
```

---

## 🔗 4. Referencias y Archivos Vinculados

- **Maqueta HTML de la Interfaz:** [maqueta_frontend_word_tesismcp.html](maqueta_frontend_word_tesismcp.html)
- **Selección Tecnológica del Frontend:** [`2026-10-17_seleccion_tecnologica_y_diseno_frontend_tesismcp.md`](2026-10-17_seleccion_tecnologica_y_diseno_frontend_tesismcp.md)
- **Análisis de storytold/wordcraft y MCP:** [`2026-10-17_storytold_wordcraft_integracion_mcp.md`](../servidor_mcp_e_ia/2026-10-17_storytold_wordcraft_integracion_mcp.md)
- **Módulo de Grounding y Auditoría:** [`core/grounding/audit_cli.py`](../../../core/grounding/audit_cli.py)
