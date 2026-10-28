# Estructura de Diapositivas y Guión de Sustentación Oral - APF2 (Semana 8)

> **Estado histórico actualizado al 18/10/2026:** este guion conserva la propuesta presentada en APF2. Para una exposición nueva deben usarse las cifras actuales: 27 modelos, 18 migraciones y 59 pruebas; MCP/API para el tesista, Admin/Unfold para el asesor, sin despliegue público ni validación con usuarios.

**Curso:** Curso Integrador I: Sistemas - Software (Ciclo 7)  
**Institución:** Universidad Tecnológica del Perú (UTP) - Sede Piura  
**Estudiante / Líder:** Josué Carrasco García  
**Proyecto:** Plataforma Colaborativa TesisMCP  
**Tiempo estimado de exposición:** 18 a 22 minutos (Límite máximo según rúbrica: 25 minutos)  

---

## 🎯 Alineación con la Rúbrica Oficial de Evaluación (APF2)

| Criterio de la Rúbrica | Diapositivas Asignadas | Elementos Clave Demostrados |
| :--- | :---: | :--- |
| **Criterio 1: Análisis del Contexto** | Diapositivas 2, 3 y 4 | 5 aspectos de la empresa/entorno, descripción clara del problema, delimitación ética y Lean Canvas (9 bloques). |
| **Criterio 2: Alternativas de Solución** | Diapositivas 5, 6 y 7 | 3 alternativas comparadas, cada una con descripción de 5 pantallas completas, justificando la selección de la Alternativa 3. |
| **Criterio 3: Análisis de la Solución** | Diapositiva 8 | Requerimientos funcionales (RF) y no funcionales (RNF) bajo estándar formal SRS / IEEE 830. |
| **Criterio 4: Diseño de la Solución** | Diapositivas 9, 10, 11 y 12 | Flujo de procesos BPMN, diagrama de clases UML, diseño de base de datos relacional (DER), Project Charter y Gantt. |
| **Criterio 5: Sustentación Oral y Prototipo** | Diapositivas 13 y 14 + Demo | Demostración del prototipo funcional interactivo (`prototipo_interactivo.html`), dominio técnico y defensa ante preguntas. |

---

## 📑 Estructura Detallada Diapositiva por Diapositiva

### Diapositiva 1: Portada Oficial
* **Título Oficial:** Desarrollo de una Plataforma Colaborativa basada en Protocolo MCP, Roles Secuenciales y Validación Determinista para la Asistencia Metodológica y Supervisión de Tesis Universitarias
* **Subtítulo:** Avance de Proyecto Final 2 (APF2) - Diseño de la Solución Informática
* **Datos del Expositor:** Josué Carrasco García - Escuela Profesional de Ingeniería de Sistemas e Informática, UTP Piura.
* **Fecha:** Octubre 2026.
* **Guión Verbal (1 min):**  
  > *"Buenas tardes, profesor y miembros del jurado. El día de hoy presento el Avance de Proyecto Final 2 de la plataforma TesisMCP. La elaboración de los primeros capítulos de una tesis exige mantener una estricta correspondencia entre el problema, los objetivos y las variables. Cuando los estudiantes recurren a asistentes de inteligencia artificial comerciales o intercambian archivos por canales dispersos, surgen tres problemas críticos: pérdida de continuidad metodológica entre sesiones, riesgo de referencias sin comprobación documental, y una revisión docente fragmentada. TesisMCP resuelve esta problemática mediante una arquitectura asistida bajo el protocolo abierto MCP, persistencia relacional inmutable y un dashboard colaborativo de revisión con visor tipo Google Docs para el docente asesor."*

---

### Diapositiva 2: Análisis del Contexto Organizacional y Problema Central (Criterio 1)
* **Contenido Visual:**
  * **Organización:** Escuela Profesional de Ingeniería de Sistemas e Informática - Universidad Tecnológica del Perú (UTP), Sede Piura.
  * **Los 5 Aspectos Institucionales (Grounded & Verificados):**
    1. *Visión:* La UTP declara buscar ser la primera opción para estudiantes con afán de superación que contribuyan a un Perú mejor [9].
    2. *Misión:* Dar acceso a educación superior de calidad que permita a los peruanos alcanzar una vida mejor [9].
    3. *Entorno:* Regulación de procedimientos de grado y titulación mediante el Reglamento de Grados y Títulos de la UTP [10]; apoyo digital al avance y asesoría.
    4. *Estrategias:* Guiar el trabajo metodológico desde asignaturas integradoras mediante pasos verificables, registrar versiones y observaciones en un solo proyecto, e incorporar verificación de fuentes con revisión humana.
    5. *Planes de la Organización:* Propuesta académica compatible con la investigación aplicada formativa, sin atribuir metas cuantitativas no documentadas.
  * **Los 3 Dolores del Problema:**
    1. *Pérdida de continuidad metodológica:* Los chats aislados no garantizan que el título, variables o ámbito aprobados se reutilicen consistentemente.
    2. *Referencias sin comprobación:* Los asistentes comerciales inventan datos bibliográficos o citan fuentes sin respaldo textual concreto.
    3. *Revisión dispersa:* Borradores y observaciones intercambiados por correo o mensajería impiden saber qué versión revisó el asesor y cuáles observaciones siguen pendientes.
* **Guión Verbal (2 min):**  
  > *"Analizamos el contexto de la UTP sede Piura bajo cinco aspectos institucionales estrictamente fundamentados en su marco regulatorio oficial. En este entorno, la elaboración de tesis enfrenta tres riesgos concretos que nuestro proyecto atiende: primero, la pérdida de continuidad metodológica en conversaciones de chat independientes; segundo, la generación de referencias bibliográficas sin comprobación de evidencia física; y tercero, la dispersión de borradores y observaciones entre múltiples canales. TesisMCP aborda estos riesgos unificando el ciclo de formulación y revisión docente con trazabilidad completa."*

---

### Diapositiva 3: Modelo de Negocio - Lienzo Lean Canvas (Criterio 1)
* **Contenido Visual:** Matriz visual de 9 bloques (Ash Maurya):
  1. *Problema:* Citas falsas de IA, asesor desbordado, desarticulación lógica entre variables.
  2. *Segmento:* Tesistas de ciclos 7 al 10 y docentes asesores de ingeniería.
  3. *Propuesta Única de Valor:* "Plataforma web que guía paso a paso los Capítulos 1 al 7 de tu tesis con fuentes científicas reales y supervisión en tiempo real de tu asesor."
  4. *Solución:* Máquina de 32 estados metodológicos, servidor MCP y dashboard del asesor.
  5. *Canales:* Portal universitario, Canvas institucional, talleres de investigación.
  6. *Flujo de Ingresos:* Licenciamiento institucional por facultad; modelo base gratuito para alumnos.
  7. *Estructura de Costos:* El backend no contrata una API LLM central; cada cliente aporta su modelo. El costo de cuentas del cliente y de una futura infraestructura pública queda fuera de la medición actual.
  8. *Métricas propuestas:* proporción de citas con documento y localizador comprobables; tiempo entre envío y decisión del asesor. Todavía no existen resultados con usuarios.
  9. *Ventaja Especial:* Protocolo MCP estándar que conecta agentes locales con la base de datos sin costes por tokens.
* **Guión Verbal (2 min):**  
  > *"Diseñamos el modelo de solución a través de un Lean Canvas de 9 bloques. Nuestra propuesta de valor se diferencia de cualquier chat genérico: no es un generador de texto al azar, sino un flujo guiado y fiscalizado. Un punto clave de ingeniería económica es nuestra ventaja especial y estructura de costos: adoptamos la arquitectura BYOA ('Bring Your Own Agent'), donde el servidor universitario expone herramientas mediante protocolo MCP y no gasta ni un solo sol en consumo de APIs de IA centralizadas, ya que cada usuario conecta su cliente habitual."*

---

### Diapositiva 4: Alcance del Proyecto y Delimitación Ética (Criterio 1)
* **Contenido Visual:**
  * **Límite Funcional:** Capítulos 1 al 7 del esquema oficial de titulación de ingeniería (Delimitación del tema hasta el diseño de instrumentos metodológicos).
  * **Bloqueo Ético (*Guardrails*):** El sistema prohíbe expresamente la simulación de datos de campo, fabricación de respuestas a encuestas o invención de análisis estadísticos posteriores (Capítulos 8 en adelante).
  * **Plan de Contingencia (MVP Semana 12):** Enfoque en los Capítulos 1 y 2 con conexión funcional a servidor MCP y panel web para asegurar una demostración sólida y libre de fallos.
* **Guión Verbal (1.5 min):**  
  > *"El alcance del proyecto cubre estrictamente desde el Capítulo 1, que es la delimitación del tema y la formulación del título, hasta el Capítulo 7, correspondiente al diseño técnico de instrumentos como encuestas y entrevistas. Es crucial enfatizar nuestro principio ético de desarrollo de software: el sistema cuenta con bloqueos intencionales para no inventar datos de campo. Toda recolección de datos debe ser ejecutada de manera auténtica por el estudiante."*

---

### Diapositivas 5, 6 y 7: Planteamiento de 3 Alternativas de Solución (Criterio 2)

#### Diapositiva 5: Alternativa 1 - Chatbot Web Monolítico Tradicional
* **Enfoque:** Asistente web simple conectado a una API comercial con chat lineal.
* **Recorrido de 5 Pantallas:**
  1. Login de usuario.
  2. Ventana de chat libre continuo.
  3. Caja de subida de PDFs desordenada.
  4. Historial plano de conversaciones.
  5. Botón de exportación en texto sin formato.
* **Dictamen:** **Descartada.** Sufre degradación de contexto, no persiste variables y no incluye interfaz para el asesor.

#### Diapositiva 6: Alternativa 2 - Sistema Web Documental Clásico
* **Enfoque:** Gestor de archivos web tradicional (tipo intranet administrativa) sin asistencia inteligente.
* **Recorrido de 5 Pantallas:**
  1. Portal de inicio y resumen de cuenta.
  2. Formulario estático de datos de tesis.
  3. Bandeja de subida de archivos Word por entregable.
  4. Mensajería interna para observaciones del docente.
  5. Listado de estados administrativos de aprobación.
* **Dictamen:** **Descartada.** Resuelve el orden burocrático pero no asiste al alumno en la redacción metodológica ni evita citas falsas fuera del sistema.

#### Diapositiva 7: Alternativa 3 - Plataforma Colaborativa MCP con Roles Secuenciales (Seleccionada)
* **Enfoque:** Arquitectura desacoplada en Python con `MCPServer`, tres roles secuenciales ejecutados por un mismo cliente LLM y panel del asesor.
* **Recorrido de 5 Pantallas Oficiales:**
  1. *Dashboard del Tesista:* Árbol de navegación metodológica de los Capítulos 1 al 7 con semáforo de aprobación.
  2. *Editor Metodológico Guiado:* Asistente que redacta paso a paso alimentado exclusivamente de variables y fuentes auditadas.
  3. *Biblioteca de Fuentes y Buscador Científico:* Conexión directa a OpenAlex y repositorios peruanos con extracción de DOIs reales.
  4. *Dashboard de Supervisión del Asesor:* Panel para el profesor con lista de alumnos, porcentaje de avance y alertas de revisión.
  5. *Visor de Revisión y Visto Bueno (Lienzo tipo Google Docs):* Vista central de lectura estilo documento (lienzo A4 en TipTap) con notas al margen ancladas a revisiones inmutables y descarga oficial a Word (`.docx`).
* **Dictamen:** **Seleccionada.** Reúne asistencia metodológica, reglas de evidencia, persistencia versionada y supervisión docente. Estas medidas reducen errores concretos, pero no eliminan todas las alucinaciones.
* **Guión Verbal (3 min):**  
  > *"Para cumplir con el Criterio 2 de la rúbrica, evaluamos 3 alternativas de solución completas, cada una estructurada con un recorrido de 5 pantallas. La Alternativa 1, un chatbot convencional, fue descartada porque pierde el hilo de la conversación y carece de control docente. La Alternativa 2, un gestor documental tradicional, ordena los trámites pero deja solo al alumno ante la hoja en blanco. La Alternativa 3 es la ganadora: combina el servidor MCP en Python, validación determinista, Django Admin/Unfold para la revisión del asesor y exportación de un borrador Word."*

---

### Diapositiva 8: Análisis de la Solución - Requerimientos de Software (Criterio 3)
* **Contenido Visual:**
  * **Requerimientos Funcionales Clave (SRS / IEEE 830):**
    * *RF01:* Persistencia por proyecto de `research_profile` y `step_progress` para los pasos `P01`–`P32`, con revisiones de capítulo inmutables.
    * *RF02:* Servidor `MCPServer` con herramientas de consulta y actualización metodológica vía JSON-RPC.
    * *RF03:* Búsqueda científica y filtro anti-alucinaciones contra repositorios (OpenAlex / OAI-PMH ALICIA).
    * *RF04:* Agente Auditor (Critic) que valida congruencia entre problema, objetivos y variables antes de guardar.
    * *RF05:* Módulo docente con marcado de párrafos observados y estados de aprobación.
    * *RF06:* Exportador estructurado de la tesis a formato Word (`.docx`) según la plantilla oficial UTP.
  * **Requerimientos No Funcionales (RNF):**
    * *RNF01 (Rendimiento):* Respuestas de herramientas de base de datos en menos de 1 segundo.
    * *RNF02 (Seguridad):* Cifrado en reposo, variables sensibles en `.env` y control de acceso basado en roles (Tesista / Asesor).
    * *RNF03 (Escalabilidad):* Arquitectura sin estado (*stateless*) lista para despliegue serverless.
* **Guión Verbal (2 min):**  
  > *"Definimos requerimientos funcionales y no funcionales verificables. El sistema aplica prerrequisitos entre pasos, contratos estrictos y autenticación por sesión o token. La latencia y el aislamiento operativo deben medirse en el entorno de despliegue; no se afirma un tiempo subsegundo sin benchmark."*

---

### Diapositivas 9 y 10: Diseño de Procesos BPMN y Arquitectura de Software (Criterio 4)
* **Contenido Visual:**
  * **Diagrama de Procesos BPMN:** Tres carriles (*swimlanes*):
    1. *Carril del Tesista:* Selecciona etapa -> Redacta con apoyo de IA -> Envía a revisión.
    2. *Carril del Sistema (MCPServer + validadores):* Recupera variables -> Audita citas y coherencia -> Persiste en PostgreSQL.
    3. *Carril del Docente Asesor:* Recibe notificación -> Revisa texto -> Inserta comentarios al margen -> Aprueba o rechaza con observaciones.
  * **Pila Tecnológica Seleccionada:**
    * *Backend:* Python con **Django + Django Ninja** (seguridad nativa, ORM relacional y panel administrativo inmediato).
    * *Capa de integración:* protocolo **MCP** con el SDK oficial (comunicación abierta por herramientas JSON-RPC).
    * *Base de datos verificada:* **PostgreSQL 16** en el entorno local.
    * *Alojamiento público:* pendiente de selección y validación.
    * *Frontend del tesista:* fuera del alcance actual. El asesor utiliza Django Admin/Unfold.
* **Guión Verbal (2.5 min):**  
  > *"El flujo de trabajo se modeló formalmente en BPMN, definiendo las responsabilidades del tesista, el motor de auditoría y el profesor asesor. En la arquitectura tomamos una decisión de ingeniería estratégica: utilizar Django Ninja con `MCPServer`. Django nos entrega de inmediato autenticación robusta, seguridad contra ataques web y el ORM relacional, mientras que Django Ninja provee endpoints asíncronos de alta velocidad con documentación automática en Swagger. La validación actual se ejecuta localmente; el despliegue público y su disponibilidad todavía no se han medido."*

---

### Diapositiva 11: Diseño Lógico y Físico de Base de Datos y Diagrama de Clases (Criterio 4)
* **Contenido Visual:** Los tres niveles formales de modelado de datos, con diagramas en alta resolución disponibles en el repositorio ([`diagrama_er_conceptual.png`](../02_arquitectura_y_sistema/diagrama_er_conceptual.png), [`diagrama_modelo_logico.png`](../02_arquitectura_y_sistema/diagrama_modelo_logico.png) y [`diagrama_modelo_fisico_completo.png`](../02_arquitectura_y_sistema/diagrama_modelo_fisico_completo.png)), complementados por el [visor interactivo de base de datos](../02_arquitectura_y_sistema/visor_diagramas_bd.html). El código actual implementa 27 modelos de dominio organizados en 7 módulos:
  * **Identidad y avance:** `user`, `project`, `project_participant`, `research_profile`, `step_progress` y `chapter`. La pertenencia al proyecto determina el rol de titular o asesor.
  * **Consistencia e instrumentos:** `consistency_row` alinea preguntas, objetivos e hipótesis; `research_variable`, `variable_dimension` e `indicator` estructuran la operacionalización; `instrument` e `instrument_item` versionan cuestionarios y guías.
  * **Redacción y supervisión:** `chapter_revision` conserva borradores inmutables; `review_comment` ancla observaciones a una revisión; `review_event` conserva envíos, aprobaciones y reaperturas.
  * **Fuentes y evidencia:** `source_document` registra metadatos y procedencia; `source_excerpt` guarda un fragmento localizado; `evidence_link` vincula ese fragmento con una afirmación de una revisión.
* **Restricciones destacadas:** claves foráneas, unicidad de `(project_id,step_code)` en `step_progress` y `(project_id,number)` en `chapter`, una persona titular y hasta un asesor activos por proyecto, numeración única de revisiones, `approved_revision_id` y verificación transaccional de pertenencia.
* **Diagrama de Clases:** `AccessPolicy`, `StepService`, `ReviewService` y `SourceService` comparten las reglas de negocio para web y MCP; la arquitectura detallada define sus operaciones.
* **Guión Verbal (2 min):**
  > *"El diseño parte de un proyecto de tesis con un titular y un asesor asignados. Modelamos la base de datos en tres niveles de abstracción: un Diagrama Entidad-Relación Conceptual de 5 dominios, un Modelo Lógico Relacional normalizado y el Esquema Físico Completo en PostgreSQL. Para garantizar el éxito en los plazos del curso, adoptamos una estrategia de ingeniería en dos fases: la implementación actual contiene 27 modelos de dominio. El diccionario físico detalla esos modelos y separa las restricciones de integridad física de las validaciones transaccionales del servicio."*

---

### Diapositiva 12: Planificación, Project Charter y Diagrama de Gantt (Criterio 4)
* **Contenido Visual:**
  * **Project Charter:** Objetivos SMART, riesgos de alto nivel y presupuesto real (S/. 0.00 en consumo cloud/IA; S/. 60.00 PEN en papelería física).
  * **Diagrama de Gantt (Semanas 1 a 18):**
    * *S1-S8:* Fase de ideación, levantamiento de requerimientos y entrega de APF2.
    * *S9 (Arranque Técnico):* Configuración de Django Ninja, modelos de base de datos y `MCPServer`.
    * *S10-S11:* Lógica de validación de Capítulos 1 y 2 y panel del asesor.
    * *S12 (Hito APF3):* Demostración en vivo del prototipo funcional MVP.
    * *S13-S17:* Integración de búsqueda científica (OpenAlex), exportador a Word y pruebas de usabilidad.
    * *S18:* Sustentación final del proyecto ante jurado.
* **Guión Verbal (1.5 min):**  
  > *"En la planificación del proyecto establecimos un cronograma realista en nuestro Diagrama de Gantt. Tras consolidar el diseño formal de la solución en esta Semana 8 con el APF2, el arranque técnico del desarrollo comienza en la Semana 9. Tenemos 3 semanas de ejecución focalizada para llegar a la Semana 12 con el prototipo funcional operativo de los Capítulos 1 y 2, asegurando la demostración en vivo exigida por la asignatura."*

---

### Diapositivas 13 y 14: Demostración del Prototipo Funcional y Defensa Oral (Criterio 5)
* **Contenido Visual:**
  * **Enlace y captura del prototipo:** [`prototipo_interactivo.html`](../02_arquitectura_y_sistema/prototipo_interactivo.html).
  * **Simulación interactiva en 4 pasos:**
    1. Formulación guiada de variables y problema.
    2. Validación lógica por agente auditor (detección de discordancia de variables).
    3. Búsqueda y auditoría de citas grounded (verificación contra PDFs descargados).
    4. Panel de supervisión docente con comentarios al margen y visto bueno.
  * **Capa de Auditoría Grounded:** Demostración del script que comprobó 9 de 9 PDF registrados según título, páginas físicas y expresiones configuradas. Ese resultado no certifica toda afirmación de cada documento.
* **Guión Verbal (3 a 4 min de Demostración en Vivo):**  
  > *"A continuación, procederé a realizar la demostración interactiva de nuestro prototipo funcional, el cual está disponible y autocontenido en nuestro repositorio. En esta pantalla podemos observar el flujo completo: cuando el alumno intenta cambiar una variable en el problema, el agente auditor bloquea el guardado hasta que exista correspondencia lógica. Asimismo, en el módulo de investigación, cada antecedente es contrastado contra su PDF original mediante nuestra capa de verificación grounded, eliminando toda posibilidad de citas falsas. Por último, en el panel del docente, el asesor puede señalar un párrafo específico, escribir su observación y autorizar el avance al siguiente capítulo."*

---

## 🛡️ Banco de Preguntas y Respuestas Técnicas para el Jurado

| Pregunta Probable del Jurado | Respuesta Técnica y Fundamentada |
| :--- | :--- |
| **¿Por qué eligieron Django Ninja en lugar de seguir solo con FastAPI?** | *"FastAPI es un excelente microframework para APIs simples, pero carece de sistema de autenticación de usuarios, panel de administración y ORM relacional nativo. En un proyecto universitario de 14 a 16 semanas, implementar auth y admin desde cero toma entre 3 y 4 semanas que restan tiempo a la lógica de IA. Django Ninja nos da la velocidad asíncrona de FastAPI junto con el ecosistema maduro y seguro de Django."* |
| **¿Cómo aseguran que el sistema no colapse si 50 tesistas lo usan a la vez?** | *"Nuestra arquitectura es stateless (sin estado) y adopta el modelo BYOA (Bring Your Own Agent). El trabajo pesado de generación de lenguaje ocurre en el cliente del usuario (Claude Desktop, Cursor, Antigravity). El backend en Django solo procesa peticiones livianas de lectura y escritura en la base de datos PostgreSQL, la cual soporta cientos de conexiones concurrentes sin saturación de CPU ni memoria."* |
| **¿Por qué afirman que el costo de IA es S/. 0.00?** | *"Porque el servidor universitario no contrata ni paga tokens de OpenAI ni Anthropic de forma centralizada. El servidor expone las herramientas mediante el protocolo MCP mediante `MCPServer`. Es el estudiante o el docente quien conecta su propia cuenta o cliente habitual de IA, eliminando el riesgo de facturas impagas o límites de consumo compartidos."* |
| **¿Cómo reducen el riesgo de fuentes inventadas?** | *"Las búsquedas se etiquetan como metadatos. Para P16 se exige un PDF del proyecto, conteo físico, hash, texto extraído y tres citas literales localizadas. OpenAlex, Semantic Scholar y la API REST de ALICIA aportan candidatos; la existencia de un registro no demuestra revisión por pares ni que el texto respalde una afirmación."* |
| **¿Qué pasará con los Capítulos 8 en adelante de la tesis?** | *"Por diseño ético y delimitación del software, el sistema solo abarca los Capítulos 1 al 7. El Capítulo 8 corresponde a la recolección de datos de campo y pruebas estadísticas empíricas. La plataforma bloquea deliberadamente la fabricación de datos simulados para asegurar la autenticidad del trabajo de grado del futuro ingeniero."* |
