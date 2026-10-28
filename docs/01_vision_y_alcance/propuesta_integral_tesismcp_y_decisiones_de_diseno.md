# Propuesta integral de TesisMCP y decisiones de diseño

**Documento de trabajo consolidado. Actualizado: 25 de octubre de 2026.**

Reúne la visión conversada, las precisiones del equipo y una revisión técnica de integraciones. No reemplaza las transcripciones, normas UTP ni validación del asesor. “Existe” describe algo registrado en documentación/código que debe comprobarse antes de atribuirlo a una entrega; “propuesta” no es capacidad implementada; “pendiente de permiso” depende de licencia o autorización externa.

## 1. Visión consolidada

TesisMCP aspira a ser una **plataforma web de acompañamiento metodológico, búsqueda documentada y producción asistida de borradores de tesis**. MCP es una conexión adicional para que un cliente de IA compatible invoque funciones del proyecto de forma controlada.

La plataforma web es el espacio principal para cargar contexto, explorar alternativas, consultar fuentes, redactar, revisar y seguir el avance. Incluye como objetivo un **editor enriquecido propio en el frontend**, con una experiencia familiar parecida a Word y conectado al estado, las citas, las revisiones y los comentarios de TesisMCP. No requiere que el estudiante salga a otro editor para el flujo habitual. Word, LibreOffice y PDF son opciones de exportación o continuidad externa. **Collabora Online queda fuera de la propuesta.**

La plataforma combina:

1. Una ruta metodológica configurable y versionada, que conserva dependencias académicas, pero permite ajustar pasos, orden, instrucciones y plantillas.
2. Búsqueda y biblioteca de evidencia, con historial de consultas, metadatos contrastados, archivos originales y enlaces entre afirmaciones y páginas/pasajes.
3. Redacción asistida de capítulos y entregables definidos para el proyecto, revisión de consistencia, referencias rastreables y revisión del tesista y su asesor.
4. Un espacio colaborativo con versiones, observaciones, decisiones y aprobaciones; una persona puede cubrir más de una función de asesoría.
5. Herramientas/conectores optativos —bases científicas, Zotero, OCR, conversores, exportación, analítica y agentes— que cada usuario activa según permisos y necesidad.

La automatización debe ayudar con tareas repetitivas: organizar, estructurar, redactar borradores, manejar citas y elaborar tablas/figuras. No debe presentar como evidencia resultados de campo inexistentes ni convertir una sugerencia de IA en decisión académica del tesista o asesor.

> TesisMCP es una plataforma web configurable que ayuda a estudiantes y asesores a planificar y desarrollar investigaciones, localizar y organizar evidencia, producir borradores académicos estructurados y revisar su coherencia mediante IA, reglas deterministas, conectores optativos y trazabilidad de fuentes. El tesista conserva sus decisiones de investigación y el asesor conserva la evaluación académica.

## 2. Precisiones que guían el diseño

- WhatsApp queda excluido porque pertenece a otro proyecto. n8n puede evaluarse como herramienta opcional para automatizar flujos o conectar servicios, pero no es requisito del producto ni sustituye la lógica del backend.
- Se desea desarrollar la idea general bien recibida por el profesor: generación organizada, estructurada, citada y revisable de partes de tesis, junto con tablas y figuras.
- La web es el producto principal; MCP es una integración.
- IEEE es el estilo previsto para el trabajo/piloto UTP, con verificación de la guía vigente al codificar reglas.
- La interfaz puede destacar cinco temas viables, pero cinco no es límite. Debe conservar todos los candidatos, los “descartados por ahora”, razones, versiones y nuevas ideas que surjan de ellos.
- Revisar pronto título, variables cuando apliquen, unidad de análisis, lugar y periodo. No imponer variables a estudios cualitativos que no las requieran.
- Se requieren funciones de asesoría metodológica y temática, no dos personas obligatorias: un asesor puede hacer ambas.
- Administradores institucionales, bibliotecarios y expertos externos son herramientas, invitaciones o extensiones opcionales; no roles humanos obligatorios.
- Se desea un perfil de escritura personal que reduzca el tono uniforme de los borradores sin sacrificar rigor, normas, citas o autoría.
- Scopus, Web of Science, Zotero, LaTeX, agentes y una experiencia tipo NotebookLM son opciones a investigar; no todas están implementadas hoy.
- Zotero debe conectarse como gestor bibliográfico existente; no se busca copiar su aplicación ni reproducir toda su funcionalidad.
- P01–P32 y capítulos 1–7 son la base implementada; el alcance objetivo acompaña también recolección autorizada, análisis de datos reales, resultados, discusión, conclusiones y entrega. No se limita al MVP histórico P01–P08. El recorrido y los prompts son configurables por proyecto; la [propuesta de orden](../03_metodologia_y_prompts/propuesta_orden_metodologico_revisado.md) es una plantilla inicial editable. Cada agente debe inspeccionar el código vigente y completar brechas sin reconstruir funciones existentes.

Las transcripciones contienen propuestas sobre orden de pasos, delimitación temprana, búsqueda, gestores bibliográficos, Word y evaluación experta. Son insumos, no decisiones aprobadas por sí solos. La herramienta mostrada en la reunión no fue auditada técnicamente.

## 3. Flujo de producto

~~~mermaid
flowchart TD
  A[Configurar proyecto, institución y guía] --> B[Explorar problemas y temas]
  B --> C[Revisar viabilidad y delimitación]
  C --> D[Estudiante confirma dirección]
  D --> E[Planear preguntas, objetivos y método]
  E --> F[Buscar en web y conectores autorizados]
  F --> G[Verificar fuentes y documentos]
  G --> H[Analizar evidencia y redactar borradores]
  H --> I[Actualizar tablas, figuras y documento vivo]
  I --> J[Revisión de tesista y asesor]
  J --> K[Exportar revisión congelada]
  J -->|observaciones| H
~~~

La interfaz puede agrupar los subpasos en fases; el backend conserva granularidad, condiciones e historial. Las decisiones dependientes mantienen puertas de aprobación; las búsquedas independientes se pueden paralelizar. Cinco temas destacados son una vista priorizada, con criterios visibles, nunca una restricción. Se preservan también opciones en observación, descartadas provisionalmente o fusionadas.

## 4. Edición protegida de metodología y prompts

El sistema puede ayudar a editar el orden y contenido de prompts, pero no reescribir silenciosamente sus límites:

1. **Núcleo protegido:** permisos, privacidad, procedencia, validaciones, aprobación humana y reglas contra datos/resultados inventados.
2. **Metodología versionada:** fases, pasos, prerrequisitos, resultados esperados, prompts y reglas institucionales con fuente y fecha.
3. **Configuración por proyecto:** preferencias, guía, enfoque, estilo y conectores.
4. **Propuesta de cambio:** la IA propone añadir, retirar, reordenar, fusionar o aclarar pasos y muestra el diff/impacto.
5. **Validador determinista:** revisa dependencias, ciclos, campos requeridos y proyectos afectados.
6. **Aprobación y publicación:** un usuario autorizado publica una versión nueva e inmutable; los proyectos existentes conservan su versión o migran con comparación.
7. **Historial y reversión:** motivo, autor, fecha, antes/después y posibilidad de restaurar.

Una preferencia individual no debe cambiar la metodología de otras personas.

El usuario puede editar el contenido de prompts, añadirlos, desactivarlos y reordenar prompts **y tareas** del recorrido. El orden visible se distingue de los prerrequisitos de ejecución; el sistema explica los bloqueos reales y conserva los borradores que aún no tienen entradas. El [contrato para el backend](../02_arquitectura_y_sistema/contrato_recorrido_y_prompts_configurables.md) detalla versiones, API, permisos, compatibilidad y criterios de aceptación. Esta función es objetivo priorizado, no capacidad actual.

## 5. Scopus, Web of Science y búsqueda asistida

**Decisión de producto:** la búsqueda asistida en Scopus y Web of Science debe ser útil sin API. La ruta base genera una ecuación editable, explica conceptos y filtros, abre el sitio oficial para que el usuario ejecute la consulta con su propio acceso y permite importar los resultados que exporte. Los conectores API son una opción futura; no son requisito para explorar temas, registrar búsquedas, importar resultados ni leer archivos aportados por el usuario. La especificación del recorrido y sus límites está en [búsqueda, lectura documental y revisión de afirmaciones](../02_arquitectura_y_sistema/especificacion_busqueda_y_revision_de_evidencia.md).

### OAuth, suscripción y acceso desde navegador no son lo mismo

Una suscripción web, API key u OAuth no otorgan automáticamente acceso programático completo. OAuth autoriza identidad/permisos; el proveedor decide APIs, campos y usos según licencias. Para el producto base, el usuario busca en el sitio del proveedor y exporta/importa resultados. Las APIs solo se consideran si luego aportan valor, el entitlement y uso están comprobados y hay autorización aplicable. No guardar contraseñas institucionales, evadir CAPTCHA, límites o controles de acceso. Automatización de interfaz no forma parte del flujo base.

### Scopus / Elsevier

Las APIs permiten consultar metadatos, resúmenes y datos de citas de Scopus. La documentación oficial describe API key, autenticación institucional por IP, tokens institucionales habilitados por Elsevier y OAuth para algunos casos de integración de nivel usuario. Elsevier advierte que API key por sí sola no concede acceso: se necesita entitlement o aprobación aplicable. Algunas APIs, campos y vistas requieren permisos adicionales.

| Vía | Qué hace | Qué no garantiza |
| :--- | :--- | :--- |
| API key | Identifica aplicación/desarrollador. | No concede licencia ni acceso completo por sí sola. |
| IP institucional | Usa el entitlement reconocido desde una red autorizada. | No permite cualquier uso o redistribución. |
| Token institucional | Alternativa que Elsevier debe habilitar para el cliente/proyecto. | No puede emitirlo el equipo por cuenta propia. |
| OAuth Elsevier | Autoriza ciertos accesos de usuario para integración, sujeto a habilitación. | No transforma una suscripción web en permiso general de API ni abre todo PDF. |
| Exportación del usuario | Importa resultados que el usuario consultó y eligió exportar. | No da necesariamente texto completo ni derechos de redistribución. |

**Solo si se implementa posteriormente un conector API:** backend con secretos cifrados, scopes mínimos, revocación y borrado; separación por institución/cuenta; límites, caché y registro de uso. Guardar proveedor, consulta, fecha, filtros, identificadores, estado de acceso y limitaciones. Scopus Search/Abstract Retrieval no debe prometer descargar artículos de cualquier editorial. Obtener el texto mediante DOI, resolvedor institucional, repositorio abierto/Unpaywall o PDF aportado legítimamente. Ser indexado no demuestra calidad ni pertinencia. Ninguno de estos trabajos bloquea el modo manual asistido.

### Web of Science / Clarivate

Clarivate documenta Web of Science API Expanded y API Starter. Expanded ofrece búsqueda y registros detallados/citas y requiere licencia de pago. Starter ofrece planes distintos: la documentación consultada describe una prueba gratuita limitada, un plan de miembro institucional y un plan de integración institucional sujeto a aprobación. El mecanismo publicado es API key; no asumir OAuth de usuario equivalente al de Elsevier.

El modo base genera ecuaciones reproducibles, abre la búsqueda en WoS y acepta archivos exportados por el usuario; no requiere API. Un eventual conector API se evalúa por separado tras verificar permisos. La automatización de interfaz no se usa para saltar controles ni extraer datos fuera de lo permitido.

### Fuentes complementarias

| Fuente | Uso | Precaución |
| :--- | :--- | :--- |
| OpenAlex | Descubrimiento abierto y relaciones entre obras/autores. | Cobertura variable; acceso abierto no valida calidad. |
| Crossref | Resolver/contrastar DOI y metadatos depositados. | Metadatos incompletos; no sustituye lectura. |
| Semantic Scholar | Descubrimiento y relaciones de citas. | Cuotas/cobertura variables; no prueba calidad automáticamente. |
| ALICIA/CONCYTEC y repositorios peruanos | Tesis y producción nacional/local. | Verificar portada, institución, año y texto físico. |
| OpenAIRE, CORE, DOAJ, Europe PMC | Descubrir contenido abierto según cobertura/API. | Aplican reglas y cuotas propias. |
| Unpaywall | Encontrar ubicaciones de versiones abiertas por DOI. | No siempre habrá PDF; verificar versión. |
| RIS/BibTeX/CSV | Importar búsquedas hechas por el usuario. | Deduplicar, comprobar y respetar términos. |

El proyecto ya documenta adaptadores como OpenAlex, Semantic Scholar, ALICIA y Crossref; confirmar estado real de cada uno antes de afirmar cobertura. No llamar “resultado Scopus” a un registro de OpenAlex sin cotejarlo.

Cada conector debe normalizar proveedor/ID, fecha y consulta; título, autores, año, revista, DOI, resumen, afiliación y tipo; estado de acceso (metadatos, abstract, texto abierto, texto institucional o archivo del usuario); procedencia, confianza por campo y huella de respuesta. Deduplicar sin perder el origen de cada dato.

**Secuencia recomendada:** (1) exploración de idea y fuentes abiertas; (2) ecuaciones editables, enlace a búsqueda manual y registro de protocolo; (3) importación de exportaciones de Scopus/WoS y deduplicación revisable; (4) lectura de resúmenes o documentos accesibles/aportados con localizadores; (5) evaluar APIs licenciadas solo si existe necesidad adicional y permiso probado. La suscripción web de un individuo no implica API para todo el equipo. La ruta manual es una capacidad de producto, no una solución temporal que espere al conector.

Fuentes oficiales: [Elsevier autenticación/OAuth](https://dev.elsevier.com/tecdoc_api_authentication.html), [portal de APIs Elsevier y entitlements](https://dev.elsevier.com/), [APIs Scopus](https://dev.elsevier.com/sc_apis.html), [guía técnica Scopus](https://dev.elsevier.com/guides/Scopus%20API%20Guide_V1_20230907.pdf), [WoS API Expanded](https://developer.clarivate.com/apis/wos), [WoS API Starter y planes](https://developer.clarivate.com/apis/wos-starter).

## 6. Multiagentes: capacidades candidatas

Los agentes son funciones internas invocables, no personas obligatorias. Se ejecutan como procesos separados cuando agregan beneficio; otras tareas pueden ser deterministas.

| Tarea/agente | Aporte |
| :--- | :--- |
| Explorador de temas | Propone variantes y conserva las descartadas. |
| Evaluador de viabilidad | Señala recursos, datos, restricciones y supuestos pendientes. |
| Revisor de coherencia | Comprueba pregunta–objetivos–hipótesis–variables–población–método; no fuerza variables si no aplican. |
| Diseñador de búsqueda | Sinónimos, ecuaciones por base, filtros y protocolo reproducible. |
| Recolectores por fuente o región | Búsquedas paralelas en fuentes abiertas autorizadas; para bases licenciadas, preparación de ecuaciones y procesamiento de exportaciones aportadas por el usuario. |
| Deduplicador/conciliador | Compara registros, conserva desacuerdos y procedencia. |
| Verificador bibliográfico | Contrasta DOI, URL, autores, año, tipo y metadatos. |
| Extractor documental | Texto, citas candidatas, tablas e imágenes con página/hoja. |
| Síntesis por región/variable/método | Procesa ramas paralelas cuando el corpus/criterios están fijados. |
| Analista de evidencia opuesta | Busca trabajos que contradicen una afirmación y vacíos de cobertura. |
| Mapeador del estado del arte | Organiza diseños, contextos, poblaciones y hallazgos enlazados a fuentes. |
| Extractor de métodos/limitaciones | Extrae diseño, muestra, instrumentos y límites con página física. |
| Asistente de instrumentos | Mapea constructo/variable→dimensión→indicador→ítem→fuente y marca vacíos. |
| Redactor + perfilador de estilo | Genera borradores desde fuentes admitidas y rasgos consentidos/editables. |
| Auditor de citas/consistencia | Revisa cada afirmación frente a su fuente y pasaje; busca citas irrelevantes, apoyo parcial, contradicción, falta de acceso, cambios de alcance y referencias huérfanas. |
| Asistente de observaciones | Agrupa comentarios, muestra diffs y propone respuestas para decisión del tesista. |
| Generador y auditor de figuras | Genera desde datos estructurados; comprueba unidades, leyendas, denominadores y fuente. |
| Auditor institucional | Comprueba formato contra guía versionada. |
| Auditor de reproducibilidad | Revisa consultas, filtros, archivos y transformaciones. |
| Triage de avance | Recomienda bloqueos y próximos pasos, sin saltar aprobaciones. |

Una vez definida pregunta y criterios, búsquedas internacionales, nacionales, locales y por base pueden correr al mismo tiempo: no hay que esperar una región para redactar otra si son ramas independientes. Un cambio de pregunta sí puede invalidar consultas. Usar patrón **fan-out/fan-in** para tareas independientes y **puertas metodológicas** para decisiones que cambian pasos posteriores. Cada resultado tipado guarda alcance, versión de contexto, citas, incertidumbre, costo y estado. Los agentes proponen revisiones; no mutan una versión aprobada. Los desacuerdos se muestran, no se ocultan.

## 7. Actores y extensiones opcionales

Los actores centrales son el **tesista** y el/los **asesor(es)**. Las funciones temática y metodológica se asignan por separado, pero pueden pertenecer a la misma persona. Si una norma exige dos firmas, se configura a partir del documento aplicable.

Los apoyos deben tener un uso concreto en la web, aunque su participación sea optativa. El experto invitado puede revisar un problema, instrumento o afirmación delimitados y devolver comentarios anclados; el bibliotecario puede revisar ecuaciones, filtros y resultados importados; un responsable institucional autorizado puede mantener guías y plantillas versionadas. La invitación comparte solo los documentos, versiones y preguntas requeridos. Sus respuestas son aportes; el tesista decide qué incorporar y el asesor asignado conserva la aprobación académica. Administración institucional no implica acceso automático a tesis privadas.

Zotero, bases científicas, OCR, exportación, R y modelos externos/locales se tratan como conectores/capacidades optativas con permisos y costos visibles. Invitados y servicios externos no son roles obligatorios para cada tesis. Cada apoyo debe reducir pasos repetidos: preparar paquetes de revisión, reutilizar búsquedas/ecuaciones, comparar versiones, agrupar comentarios, deduplicar importaciones y registrar decisiones. Los detalles de tareas, permisos, invitación y aceptación están en la [especificación funcional de búsqueda y evidencia](../02_arquitectura_y_sistema/especificacion_busqueda_y_revision_de_evidencia.md).

Los roles del producto no son lo mismo que el juicio de expertos. La validación del prototipo es un procedimiento: seleccionar evaluadores, aplicar una ficha/rúbrica, identificar versión del sistema y analizar resultados. Pruebas técnicas miden funcionamiento; expertos revisan pertinencia metodológica; usuarios aportan usabilidad. Una ficha ordena observaciones, no las convierte por sí sola en evidencia estadística.

## 8. Escritura personalizada

Perfil opcional construido desde muestras propias que el estudiante elige y autoriza. El sistema propone rasgos generales (formalidad, longitud, conectores, voz, nivel explicativo, vocabulario); el usuario corrige el perfil, elige ajustes y compara versiones. Adaptar preferencias no significa copiar frases ni imitar a otra persona. Mantener consentimiento, retención/borrado, separación por proyecto y control de envío a proveedores. No usarlo para ocultar IA o evadir detectores. Objetivo: preservar la voz legítima del estudiante sin que todos los documentos tengan un tono idéntico.

## 9. Zotero, citas vivas, Word y LaTeX

**“Referencias IEEE verificadas”** significa metadatos y citas vinculados a fuentes conocidas y, cuando se inspeccionó, a pasajes. **“Campos activos Zotero comprobados”** significa que el plugin puede editar/refrescar la cita y bibliografía. No son la misma garantía: un PDF LaTeX puede tener citas IEEE correctas sin campos editables, y “[12]” en DOCX no demuestra integración Zotero.

No solo Word: Zotero ofrece plugins para Microsoft Word, LibreOffice y Google Docs. La verificación real debe abrir/refrescar el documento con el plugin conectado en uno de esos procesadores.

TesisMCP debe mantener el editor enriquecido y las citas del flujo habitual dentro de su propio frontend. Puede conectar bibliotecas Zotero mediante autorización para buscar/importar referencias y, si se habilita, sincronizar cambios. Las citas dentro del editor de TesisMCP se enlazan a registros de fuente y se formatean en la plataforma; esto es distinto de campos activos del complemento Zotero en un DOCX externo. Word/LibreOffice se usan cuando el usuario decide continuar fuera o necesita verificar campos activos. La API de Zotero no inserta por sí sola campos vivos dentro de un DOCX. Pedir permisos mínimos, proteger/revocar credenciales y probar cualquier exportación compatible de extremo a extremo; revisar el XML en busca de `CSL_CITATION` no basta para afirmar que funciona.

Dentro del editor, una función central de revisión de afirmaciones y citas debe cotejar la afirmación concreta con pasajes de la fuente, de forma semejante a la interacción visible de Jenny AI. Separar verificación de metadatos y respaldo de contenido; presentar estados como apoyo, apoyo parcial, contradicción, fuente no relacionada o acceso insuficiente. Una fuente alternativa debe mostrar pasaje y localizador, no solo título o similitud. Toda sustitución o reescritura es una propuesta con diff y requiere aceptación explícita; el flujo detallado está en la [especificación de revisión de evidencia](../02_arquitectura_y_sistema/especificacion_busqueda_y_revision_de_evidencia.md).

No se recomienda copiar o replicar la aplicación Zotero. Su código se ofrece principalmente bajo AGPLv3 salvo componentes con licencia distinta, y el nombre/marca Zotero tiene restricciones propias. Se puede evaluar reutilizar componentes puntuales (por ejemplo, un procesador CSL) tras revisar su licencia individual; la decisión de arquitectura es integrar Zotero y construir la experiencia metodológica de TesisMCP.

LaTeX **sí ayuda** con ecuaciones, referencias cruzadas, bibliografía, plantillas y compilación reproducible. Exige aprendizaje y puede ser menos cómodo para asesoría visual en Word. No es Word con otra interfaz: LaTeX es marcado/compilación y Word es un editor visual OOXML. Recomendación: contenido académico canónico estructurado y versionado; generar editor web, DOCX, PDF, LaTeX, BibTeX/CSL JSON/RIS y eventualmente ODT.

Fuentes Zotero: [OAuth](https://www.zotero.org/support/dev/web_api/v3/oauth), [API escritura](https://www.zotero.org/support/dev/web_api/v3/write_requests), [procesadores compatibles](https://www.zotero.org/support/word_processor_integration), [uso del plugin Word](https://www.zotero.org/support/word_processor_plugin_usage), [campos activos](https://www.zotero.org/support/kb/existing_citations_not_detected).

## 10. Tablas y figuras en tiempo real

Separar (a) datos canónicos con procedencia, fórmulas y versión; (b) visualizaciones dinámicas recalculadas por la plataforma; (c) explicaciones/representaciones sugeridas por IA y validadas contra los datos. Circuito: cambio → validación → recálculo determinista → actualización visual → revisión si cambia interpretación → evento registrado.

La vista web puede actualizarse en vivo. La exportación congela una revisión con fecha, datos, fuentes y cálculos; si algo cambia después, se ofrece regenerarla, no se altera silenciosamente. Un ícono/tooltip puede mostrar “cómo se generó” y abrir la procedencia. Citar adaptaciones/reproducciones. Antes de recolectar datos, generar matrices y mapas de literatura, no resultados empíricos ficticios.

## 11. Documentos, OCR y experiencia tipo NotebookLM

Por la descripción de conversión multiformato, incluido Excel, quizá recuerdas [Microsoft MarkItDown](https://github.com/microsoft/markitdown), aunque sin el enlace no se puede asegurar. MarkItDown convierte varios formatos a Markdown y ofrece un complemento OCR/visión para imágenes en PDF/Office. Docling también acepta archivos Office, PDF y exporta Markdown/JSON, y aparece en el stack documentado del proyecto.

| Opción | Uso | Riesgo/límite |
| :--- | :--- | :--- |
| Docling | Representación estructurada multiformato, PDF/Office, tablas y OCR según pipeline. | Confirmar OCR/extracción de imágenes para cada formato. |
| MarkItDown | Conversión ligera de PDF, Word, PowerPoint, Excel y otros a Markdown. | Puede simplificar hojas/tablas; el OCR con visión puede enviar imágenes a un servicio externo. |
| Marker | PDF científico/libros, OCR, orden, tablas, imágenes y ecuaciones. | Revisar licencia tanto de código como de pesos/modelos. |
| PyMuPDF/Poppler/OCRmyPDF/Tesseract | Extracción PDF y OCR local controlable. | OCR recupera texto; no entiende el significado del gráfico. |

OCR sirve para letras y números en píxeles: páginas escaneadas, capturas, fotografías e imágenes incrustadas. No interpreta por sí solo ejes, tendencias o causalidad; para eso conservar figura y cotejar con datos/tablas. Si el PDF ya tiene buena capa de texto, usar extracción nativa y OCR selectivo.

Pipeline: conservar original con hash/permisos; detectar formato/páginas/hojas; extraer estructura nativa; OCR solo donde haga falta; guardar texto OCR aparte con confianza; extraer figuras y anotar visión en campo separado; preservar JSON con página/hoja/celda/posición; producir Markdown para el modelo con referencias al original; recuperar pasajes enlazables; permitir corrección manual con historial. Markdown es intermedio, no fuente canónica: aplanar Excel puede perder fórmulas, hojas y relaciones.

Se puede reproducir la experiencia visible de NotebookLM —cargar fuentes, hacer preguntas ancladas y abrir citas— con almacenamiento de originales, extracción estructurada, chunks por estructura, búsqueda léxica+vectorial, RAG que cite IDs, validador de citas e interfaz que salta a página/pasaje. Google describe fuentes y citas, pero no publica la totalidad de su implementación interna; no afirmar que se replica su algoritmo.

Fuentes: [formatos Docling](https://docling-project.github.io/docling/usage/supported_formats/), [Docling Serve/OCR](https://github.com/docling-project/docling-serve/blob/main/docs/usage.md), [MarkItDown](https://github.com/microsoft/markitdown), [MarkItDown OCR](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-ocr), [Marker](https://github.com/VikParuchuri/marker), [fuentes NotebookLM](https://support.google.com/gemininotebook/answer/16215270?hl=en), [Google sobre grounding/citas](https://blog.google/innovation-and-ai/technology/ai/notebooklm-google-ai/).

No elegir una herramienta por popularidad: comparar Docling, MarkItDown y alternativas con PDF digital/escaneado, dos columnas, ecuaciones, tablas anchas, gráficos, XLSX multhoja/fórmulas y DOCX/PPTX con imágenes. Medir omisiones, orden, página, tablas, recursos, estabilidad y licencia.

## 12. Libros

Sí, alguien del equipo debe localizarlos y consultarlos; puede usar biblioteca universitaria, préstamo interbibliotecario o compra legal. No es necesario que tú compres todos. Verificar portada, edición e ISBN antes de citar. Los libros complementan; no reemplazan normas y guías UTP.

| Obra | Uso | Enlace editorial |
| :--- | :--- | :--- |
| Hernández-Sampieri y Mendoza, *Metodología de la investigación: las rutas cuantitativa, cualitativa y mixta* | Enfoques, planteamiento, diseño, variables/constructos e instrumentos; el profesor mencionó Sampieri, verificar edición. | [McGraw Hill](https://info.mheducation.com/rs/128-SJW-347/images/CATALOGO%20HED%202023.pdf) |
| Creswell y Creswell, *Research Design* | Alinear pregunta, enfoque y diseño. | [SAGE](https://us.sagepub.com/en-us/nam/research-design/book270550) |
| Booth et al., *The Craft of Research* | Preguntas, argumentos y evidencia. | [University of Chicago Press](https://press.uchicago.edu/ucp/books/book/chicago/C/bo215874008.html) |
| DeVellis y Thorpe, *Scale Development* | Escalas cuando el estudio las requiere. | [SAGE](https://us.sagepub.com/en-us/nam/scale-development/book269114) |
| Zobel, *Writing for Computer Science* | Escritura académica en computación. | [Springer](https://link.springer.com/book/10.1007/978-1-4471-6639-9) |
| Wohlin et al., *Experimentation in Software Engineering* | Evaluación experimental en software, si aplica. | [Springer](https://link.springer.com/book/10.1007/978-3-662-69306-3) |
| Dumas et al., *Fundamentals of Business Process Management* | Procesos, si aplica. | [Springer](https://link.springer.com/book/10.1007/978-3-662-56509-4) |
| Yin, *Case Study Research and Applications* | Estudios de caso, si corresponde. | [SAGE](https://us.sagepub.com/) |
| Day y Gastel, *How to Write and Publish a Scientific Paper* | Comunicación científica. | [Cambridge](https://www.cambridge.org/) |

No hace falta leer todos enteros. Elegir capítulos según método y consultar al asesor. Verificar ediciones; estos enlaces no afirman disponibilidad gratuita.

## 13. Principios de arquitectura y evidencia

- Web, MCP y conectores usan los mismos servicios/contratos; el LLM no escribe directamente el estado canónico.
- Enlazar afirmaciones a referencia, versión de archivo, página/pasaje y nivel de verificación.
- Diferenciar metadatos, abstract, texto extraído, lectura humana y evidencia confirmada.
- Datos canónicos estructurados; editor y exportaciones son vistas versionadas.
- Versionar capítulos, metodología, prompts, perfil de estilo, búsquedas, figuras y exportaciones.
- Resolver identidad/permisos en servidor; detectar conflictos y no sobrescribir.
- Conectores con scopes mínimos, consentimiento, cifrado, revocación, cuotas y registro.
- La IA propone; validadores y aprobaciones se exponen por separado.
- “No encontrado” siempre se limita a fuentes, consulta, filtros y fecha.

## 14. Evaluación

Separar funcionamiento técnico, calidad documental/extracción, pertinencia metodológica revisada por expertos, usabilidad y eventual comparación de tiempo/esfuerzo. Definir antes los criterios, muestra, instrumento y análisis. Para medir reducción de trabajo, comparar tareas equivalentes con y sin TesisMCP y registrar tiempos, pasos repetidos, correcciones y errores; reportar condiciones y limitaciones. La ficha de observación ordena juicios; no convierte automáticamente opiniones en prueba estadística. No afirmar ahorro o eficacia sin medición válida.

## 15. Ruta de trabajo

La secuencia es orden de construcción, no reducción permanente del producto. **P01–P32 y capítulos 1–7 son punto de partida compatible; la versión objetivo acompaña hasta el cierre de la tesis.** Antes de programar, contrastar cada requisito con el backend actual y marcarlo como implementado, parcial, pendiente o descartado. Para desarrollo del backend, el [plan B0–B10](../02_arquitectura_y_sistema/plan_entregas_backend.md) es la secuencia vigente y prioriza configuración de recorrido/prompts tras B0. La lista siguiente es un mapa de dominios, no otro orden de entregas:

1. Reconciliar visión web con estado/código; auditar el backend P01–P32 para evitar duplicación; definir modelo canónico de método/evidencia y salida UTP/IEEE desde guía vigente.
2. Consolidar fuentes abiertas, ecuaciones e importación; registrar consultas y comparar extracción documental con muestra real.
3. Añadir asesor único/múltiple, tareas multiagente, perfil de escritura consentido y cambios metodológicos versionados.
4. Crear el editor enriquecido propio en el frontend y figuras desde datos; conectar Zotero; exportar DOCX/PDF; verificar campos Zotero en Word/LibreOffice solo si se ofrece esa compatibilidad; ofrecer LaTeX según necesidad.
5. Construir búsqueda asistida manual e importación desde bases licenciadas; evaluar APIs como extensión solo si se demuestra necesidad y permiso. Añadir revisión afirmación–cita con evidencia antes de proponer reemplazos; validar técnica, expertos y usuarios por separado.

## 16. Decisiones por confirmar

1. Qué ruta empírica demostrará el piloto después de P32 y qué datos reales, permisos y revisión se requieren para ella; no asumir resultados antes de recolectarlos.
2. Qué guía/reglamento UTP vigente determina estructura y formato IEEE.
3. Si, después de demostrar la ruta manual, una API de Scopus/WoS aporta valor adicional y UTP/proveedor autoriza ese uso, usuarios, cuotas, datos y red. Esta decisión no bloquea la búsqueda asistida base.
4. Nivel Zotero esperado: exportar referencias, sincronizar biblioteca o campos vivos en DOCX.
5. Salida inicial: DOCX/PDF, LaTeX o ambos.
6. Consentimiento y proveedor para analizar muestras de escritura.
7. Tratamiento de fórmulas, gráficas y hojas en Excel.
8. Criterios/validadores de priorización de temas.
9. Agentes que se construirán y evidencia requerida para demostrar beneficio.
10. Ficha de expertos/usuarios y su validación previa.

## 17. Respuestas breves a tus dudas

- **Búsqueda en Scopus/WoS:** la ruta prevista del producto no necesita API: preparar ecuación, abrir la búsqueda oficial e importar la exportación del usuario. Una integración API es opcional y requiere demostrar permisos/valor. OAuth autentica/autoriza, no concede licencia por sí solo.
- **Asesor temático/metodológico:** son funciones separables y pueden asignarse a la misma persona.
- **Validación experta vs roles:** son conceptos distintos; uno describe usuarios, el otro un protocolo para evaluar prototipo.
- **Zotero:** la app puede conectar biblioteca y crear documentos; campos activos requieren probar refresco del plugin en Word, LibreOffice o Docs. No basta API o XML.
- **Figuras dinámicas:** cálculo determinista desde datos canónicos, actualización inmediata en plataforma; IA puede sugerir explicaciones. Exportación congela la versión.
- **OCR:** extrae texto de imágenes; no interpreta por sí solo el sentido de un gráfico.
- **Docling/MarkItDown:** no hay ganador universal. MarkItDown parece coincidir con la herramienta recordada, sin certeza al faltar enlace; Docling ya figura en el proyecto; Marker merece revisar licencia y calidad PDF.
- **Libros:** sí, el equipo debe buscarlos en biblioteca/catálogo; no tienes que comprar todos.

## 18. Documentos del proyecto relacionados

- [Síntesis consolidada de reuniones](../dudas_y_consultas/general/2026-10-22_sintesis_consolidada_reuniones_tesismcp.md)
- [Profesor invitado y ruta metodológica](../dudas_y_consultas/general/2026-10-22_analisis_profesor_invitado_y_ruta_metodologica.md)
- [Análisis del producto mostrado](../dudas_y_consultas/general/2026-10-22_analisis_demostracion_producto_esperado.md)
- [Análisis de reunión con asesor](../dudas_y_consultas/general/2026-10-22_analisis_reunion_asesor_a.md)
- [Ecosistema y roles previos](ecosistema_y_roles.md)
- [Arquitectura global](../02_arquitectura_y_sistema/arquitectura_global.md)
- [Estado verificable del producto](../07_desarrollo_prototipo/estado_version_producto.md)
- [Estrategia actual de búsqueda](../04_modulo_investigacion_y_busqueda/estrategia_busqueda_antecedentes.md)

> **Mantenimiento:** cuando una decisión se apruebe o una capacidad se implemente, actualizar su estado y enlazar evidencia/código. Guardar esta propuesta no significa que esté implementada.
