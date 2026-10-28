# Síntesis consolidada y neutral de las reuniones sobre TesisMCP

- **Fecha asociada a los audios:** 2026-10-22.
- **Corpus recibido:** tres transcripciones Markdown completas.
- **Cobertura declarada por las transcripciones:** 17:28, 14:10 y 26:32.
- **Limitación:** originalmente se mencionaron cuatro audios, pero en esta entrega solo se recibieron tres transcripciones. No se puede determinar de forma segura cuál audio falta ni asociar cada transcripción con una hora de grabación concreta.
- **Nivel de verificación:** texto completo de las tres transcripciones, sin cotejo auditivo ni diarización.
- **Aclaración posterior del usuario:** uno de los profesores propuso que el sistema genere el borrador hasta el capítulo 7 para ahorrar trabajo monótono y repetitivo al tesista y al asesor, con contenido citado, organizado, mostrado y estructurado.
- **Estado:** análisis consolidado; decisiones de alcance pendientes.

## 1. Hallazgo principal

La evidencia textual respalda esta formulación neutral:

> La idea general de TesisMCP fue valorada favorablemente, pero se recomendó delimitar mejor el primer alcance y ampliar su valor académico mediante contexto institucional, trazabilidad científica, redacción metodológica, documento estructurado y validación humana.

La aclaración posterior del usuario permite precisar el objetivo: uno de los profesores sí planteó automatizar la construcción del borrador hasta el capítulo 7 para ahorrar tareas monótonas y repetitivas al tesista y al asesor. La expectativa incluye que el material quede citado, organizado y estructurado. Esto no equivale a inventar trabajo de campo, resultados o conclusiones ni a entregar una tesis final sin revisión humana.

## 2. Evidencia directa sobre la valoración del proyecto

| Fuente | Tiempo | Evidencia | Lectura permitida |
| :--- | :---: | :--- | :--- |
| Demostración del producto esperado | 10:45 | “En pocas palabras, el proyecto está bien, pero hay que explotarlo un poquito más. Hay que encaminarlo bien.” | Evaluación favorable con solicitud de fortalecimiento. |
| Demostración del producto esperado | 14:10 | “el proyecto está... está bien ejecutado” y “hay que explotarlo un poco más”. | No se solicita abandonar la idea actual. |
| Profesor invitado | 00:43 | El equipo dice que busca llegar hasta la primera parte de la tesis, sin ejecutar el instrumento. | Límite inicial declarado por el equipo. |
| Profesor invitado | 09:18 | Se espera “un producto académico”, no una interacción equivalente a sentarse con ChatGPT. | El valor diferencial debe ser metodológico y verificable. |
| Profesor invitado | 14:17 | Se explica que varias fases son repetitivas y que por ello fueron estructuradas para obtener consistentemente el resultado deseado. | Sustenta el ahorro de tiempo como necesidad del usuario. |
| Profesor invitado | 21:35–22:58 | Se discute que agentes podrían llenar progresivamente una estructura y producir el documento completo. | Posible mecanismo técnico; no demuestra que la arquitectura multiagente sea obligatoria. |

## 3. Clasificación consolidada

### A. Orientaciones reiteradas y de alta confianza

1. **Resolver el problema metodológico, no construir solo una aplicación.**
2. **Diferenciar TesisMCP de un chat genérico** mediante flujo, contratos, contexto y trazabilidad.
3. **Incorporar normativa institucional y líneas de investigación.**
4. **Mantener al tesista como decisor**, especialmente al elegir el tema.
5. **Relacionar fuentes con variables, preguntas, objetivos e hipótesis.**
6. **Entregar un borrador académico estructurado**, preferentemente Word.
7. **Validar con investigadores humanos** y no solo con pruebas técnicas.
8. **Comenzar con un alcance manejable** antes de generalizar.

### B. Recomendaciones fuertes, pero no decisiones registradas

- Limitar el piloto a Informática UTP.
- Reducir a cinco los temas visibles.
- Reordenar o fusionar los primeros prompts.
- Agrupar los treinta y dos pasos en fases grandes en la interfaz.
- Añadir conexión o interoperabilidad con buscadores y gestores bibliográficos.
- Incorporar parámetros de redacción por institución.

### C. Ideas exploratorias

- Multiuniversidad desde la primera versión.
- Agentes independientes trabajando en paralelo.
- Analítica estadística con R.
- Preparación comercial o para ferias.
- Generación integral de la tesis.

### D. Elementos que no deben convertirse en requisitos

- Preferencias personales por proveedores de IA.
- Afirmaciones sobre herramientas privadas no auditadas.
- Especulaciones sobre LaTeX.
- Código descargado de GitHub sin auditoría.
- Ejemplos anecdóticos, cifras personales o casos ajenos al proyecto.

La conversación sobre n8n/WhatsApp (25:19–26:32 de la transcripción del profesor invitado) pertenece a un proyecto aparte del profesor, según aclaración posterior del usuario. Se excluye del alcance, del backlog y de las ideas exploratorias de TesisMCP.

## 4. Qué parece necesitar el usuario académico

El conjunto de reuniones describe al usuario como un tesista que necesita:

1. declarar universidad, carrera, guía y línea de investigación;
2. explorar temas, pero conservar la decisión final;
3. comprobar pronto variables, unidad de análisis, lugar y ODS;
4. avanzar por una ruta metodológica comprensible;
5. buscar y registrar evidencia científica de manera reproducible;
6. entender la relación de cada fuente con su investigación;
7. redactar conforme a criterios académicos explícitos;
8. recibir un documento editable y estructurado;
9. someter el resultado a revisión de un investigador o asesor.
10. obtener automáticamente tablas y figuras numeradas, tituladas, vinculadas con el texto y acompañadas por su nota y fuente.

Esto describe **generación asistida de un borrador metodológico estructurado hasta el capítulo 7**, con fuentes y revisión humana. El sistema automatiza producción documental repetitiva, pero no sustituye las decisiones del tesista, la evaluación del asesor ni la ejecución empírica.

## 5. Comparación con el producto actual verificado en código

| Tema de las reuniones | Estado actual comprobado | Evaluación |
| :--- | :--- | :--- |
| Ruta metodológica | Existen contratos y guardado secuencial P01–P32. | Cubierto en el núcleo. |
| Alcance hasta instrumentos | P01–P32 llegan al diseño y piloto del instrumento; no abarcan ejecución de campo, resultados, discusión o conclusiones. | Alineado con el límite declarado. |
| Decisión humana del tema | P01 permite preselección opcional, pero P02 exige un `tema_ganador` con el mayor puntaje. | Riesgo de desalineación semántica; debe registrarse confirmación humana. |
| Cinco temas | P01 acepta entre cinco y diez; la documentación/prompts aún describen diez. | Parcial; falta una decisión uniforme. |
| Línea institucional | P03 registra `linea_utp_vinculada` como texto. No existe un perfil institucional general que gobierne todas las reglas. | Parcial y acoplado a UTP. |
| Búsqueda científica | El código consulta OpenAlex, Semantic Scholar y ALICIA y coteja DOI con Crossref. P13 genera ecuaciones para Scopus e IEEE Xplore. | No hay conexión directa con Scopus o Web of Science. |
| Trazabilidad de evidencia | P16 exige PDF registrado, extractos localizados y páginas físicas. | Cubierto con límites explícitos. |
| Zotero/Mendeley | El sistema inspecciona campos Word y Zotero en DOCX aportados. | No crea ni sincroniza bibliotecas Zotero/Mendeley. |
| Documento Word | Existe exportación de borrador DOCX con texto guardado y formato base. | No hay carátula institucional completa, índices automáticos, tablas/figuras académicas completas ni citas activas generadas. |
| Parámetros de redacción | Hay límites, taxonomía de Bloom, signos y contratos estrictos. | Parcial; falta parametrización institucional completa. |
| Validación humana | Existe revisión del asesor con observaciones y aprobación. | No equivale aún a un protocolo experimental con ficha de observación de expertos. |
| Multiagentes | Hay tres prompts de rol secuenciales. | No existen agentes independientes ni ejecución paralela. |
| Modelo independiente del LLM | El cliente del usuario aporta el LLM y el servidor MCP conserva el flujo. | Alineado. |
| Interfaz del tesista | El estado canónico indica que no se desarrollará una web propia del tesista. | Tensión directa con las conversaciones sobre mejorar la interfaz; requiere decisión. |

Fuentes de estado: [estado verificable del producto](../../07_desarrollo_prototipo/estado_version_producto.md), [contratos metodológicos](../../03_metodologia_y_prompts/contratos_pydantic_y_validadores_mvp.md), [arquitectura global](../../02_arquitectura_y_sistema/arquitectura_global.md) y código bajo `backend/thesis/` y `mcp_server/`.

## 6. Decisiones que el equipo debe cerrar

| Decisión | Alternativas observadas | Recomendación analítica, no atribuida a los profesores |
| :--- | :--- | :--- |
| Alcance institucional | Solo Informática UTP / multiuniversidad inmediata / piloto UTP extensible | Piloto UTP con un modelo de configuración extensible. |
| Frontera académica | Formulación hasta instrumentos / manuscrito completo / ejecución empírica | Mantener P01–P32 y excluir ejecución de campo y resultados no observados. |
| Elección del tema | Ganador automático / recomendación explicable con confirmación humana | Recomendación explicable y confirmación obligatoria del tesista. |
| Integración científica | Generar ecuaciones / importar exportaciones / API directa | Priorizar trazabilidad e importación legal; evaluar APIs según licencia y acceso. |
| Documento final | Borrador genérico / plantilla UTP / motor multiuniversidad | Completar primero una plantilla UTP verificable. |
| Interfaz | Solo cliente MCP y Admin / interfaz propia del tesista | Resolver explícitamente la contradicción con el estado canónico antes de implementar. |
| Orquestación | Secuencial / roles secuenciales / agentes independientes | Conservar secuencia validada hasta demostrar beneficio de otra arquitectura. |
| Validación | Pruebas técnicas / asesor / juicio de expertos con instrumento | Mantener las tres capas y no confundirlas. |

## 7. Propuesta de priorización

Esta priorización es resultado del análisis y **no** una decisión registrada en los audios.

### Posición recomendada

No cambiar el núcleo de TesisMCP por un generador autónomo sin controles. Sí convertirlo explícitamente en un **generador asistido de borradores de los capítulos 1–7**, porque esa automatización es el ahorro de tiempo señalado por el profesor. El diferenciador defendible es que la generación ocurre dentro del circuito P01–P32, con evidencia trazable, contratos deterministas, confirmación del tesista y revisión del asesor.

“Completar el proyecto” debería significar que un estudiante puede iniciar con su guía institucional, recorrer una ruta comprensible, tomar las decisiones académicas y generar los capítulos 1–7 en un Word revisable, organizado y citado con fuentes verificables. No debería significar que el sistema invente decisiones, ejecute el trabajo de campo o entregue una tesis lista para sustentar sin intervención humana.

### Camino de producto recomendado

1. **Fijar el piloto:** Informática UTP como caso validable, manteniendo una arquitectura extensible pero sin prometer soporte inmediato para todas las universidades.
2. **Corregir la experiencia inicial:** solicitar guía y línea de investigación; presentar cinco temas; dejar la elección al estudiante; validar temprano variables, unidad de análisis, lugar, periodo y ODS. Los contratos internos pueden conservar P01–P04 aunque la interfaz los agrupe.
3. **Mostrar el valor central:** generar progresivamente los capítulos 1–7 a partir de P01–P32, fundamentar las afirmaciones con fuentes registradas y explicar por qué cada antecedente se relaciona con la investigación.
4. **Cerrar el entregable visible:** generar un borrador Word conforme al piloto UTP, con estructura, tablas, figuras, índices, citas y referencias vinculadas y advertencias de revisión. Debe seguir llamándose borrador académico, no tesis terminada.
5. **Integrar la revisión humana:** hacer visible el ciclo tesista–asesor y ejecutar una validación formal con investigadores mediante un instrumento definido antes de recoger resultados.
6. **Generalizar solo después de validar:** perfiles de otras universidades, gestores bibliográficos, accesos licenciados y arquitecturas multiagente quedan condicionados a evidencia del piloto.

### Papel recomendado para Scopus, Zotero, Mendeley y LaTeX

- **Scopus:** usarlo como fuente de descubrimiento y como destino de ecuaciones de búsqueda reproducibles. Para el piloto es más prudente importar resultados exportados por el usuario que depender de una integración directa no comprobada.
- **Zotero:** priorizarlo como gestor de la biblioteca del proyecto y de las citas, porque el código ya reconoce campos Zotero presentes en documentos DOCX. Reconocer campos no equivale todavía a crear o sincronizar una biblioteca.
- **Mendeley:** tratarlo como segunda opción de interoperabilidad, después de completar y validar un flujo con un único gestor.
- **LaTeX:** considerarlo como exportador alternativo para usuarios o instituciones que lo requieran. No es necesario para producir un DOCX estructurado y no fue confirmado en la reunión como tecnología interna de la herramienta mostrada.

La cadena de valor propuesta es: **buscar y documentar la estrategia → registrar fuentes verificables → redactar con vínculos de evidencia → insertar citas gestionables → exportar Word y, eventualmente, LaTeX**.

### Citas activas, tablas y figuras automáticas

Las referencias trazables y verificadas son el requisito de integridad: cada afirmación debe poder regresar a una fuente, un pasaje y una página. Sin esta capa, una cita activa solo automatizaría una referencia potencialmente incorrecta. Sin embargo, para materializar el ahorro de tiempo mostrado en la reunión, el piloto final también debería producir citas editables o actualizables y una bibliografía sincronizada en el documento.

Se recomienda implementarlo por etapas:

1. **Primera etapa:** vínculos internos `afirmación → fuente → extracto → página`, citas visibles consistentes y bibliografía regenerable desde los registros del proyecto.
2. **Segunda etapa:** campos de cita activos en DOCX o interoperabilidad comprobada con Zotero; Mendeley puede añadirse después de validar un gestor completo.

Las tablas y figuras generadas automáticamente deben incluir número, título, contenido verificable, nota y procedencia. Si adaptan o reproducen una fuente, deben citarla; si son elaboración propia, deben identificar los datos y reglas usados para construirlas. Los índices de tablas y figuras y las referencias cruzadas del texto deberían actualizarse automáticamente.

Antes del trabajo de campo solo pueden generarse recursos sustentados por información disponible: matrices metodológicas, tablas de literatura, diagramas conceptuales, flujos y gráficos derivados de datos reales ya registrados. El sistema no debe fabricar gráficos de resultados, estadísticas ni muestras inexistentes.

### Prioridad inmediata: coherencia del alcance

1. Formalizar el piloto como UTP Informática o rechazar explícitamente esa delimitación.
2. Definir en qué paso termina el producto y qué significa “primera parte”.
3. Preservar la elección humana del tema.
4. Resolver si habrá interfaz propia del tesista.

### Prioridad alta: valor diferencial

1. Registrar guía y línea de investigación como fuentes versionadas.
2. Hacer reproducible la estrategia de búsqueda y la relación fuente–tesis.
3. Completar la plantilla Word UTP sin presentarla como tesis lista para sustentar.
4. Diseñar y ejecutar validación con investigadores.

### Extensión posterior

1. Perfil institucional multiuniversidad.
2. Interoperabilidad con gestores bibliográficos.
3. Integraciones licenciadas con bases científicas.
4. Evaluación comparativa de orquestación multiagente.
5. Analítica estadística, solo si entra en el alcance ético y funcional.

## 8. Formulación recomendada del proyecto tras las reuniones

> TesisMCP es un generador asistido de borradores metodológicos que construye progresivamente los capítulos 1–7 mediante pasos verificables, fuentes trazables, reglas institucionales y revisión humana. Automatiza la organización, redacción, citación y exportación del documento para ahorrar trabajo repetitivo al tesista y al asesor, pero no ejecuta el trabajo de campo, no inventa resultados y no sustituye sus decisiones ni la aprobación académica.

Esta formulación conserva el circuito actual y reconoce expresamente la generación documental solicitada, distinguiendo el borrador asistido de una tesis final validada.

## 9. Pendientes de evidencia

- Obtener la cuarta transcripción o confirmar que uno de los audios no contenía material relevante.
- Mapear cada transcripción al nombre y hora exacta de su audio.
- Revisar manualmente los pasajes con hablantes ambiguos.
- Conseguir los reglamentos y guías institucionales exactos antes de codificar reglas.
- Validar técnicamente cualquier herramienta o integración mostrada en la reunión.

