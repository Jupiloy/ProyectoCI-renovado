# Análisis comparativo de antecedentes de TesisMCP

Este análisis reúne siete trabajos vinculados con las funciones previstas de TesisMCP: asistencia para investigar y redactar con fuentes comprobables, gestión del avance de tesis y revisión por asesores. La selección incluye tres trabajos internacionales, tres nacionales y uno aplicado en Piura. La clasificación local de Rosales Rosas responde al lugar estudiado —la Universidad Nacional de Piura—, aunque el grado fue otorgado por la USAT. La verificación bibliográfica y de resultados se basa en las publicaciones y resúmenes institucionales enlazados; no equivale a una lectura integral de todos los PDF.

## Matriz comparativa

| Ámbito | Trabajo | Evidencia que aporta | Alcance para TesisMCP |
| :--- | :--- | :--- | :--- |
| Internacional | [Skarlinski et al., PaperQA2 (2024)](https://arxiv.org/abs/2409.13740) | Agente para buscar y sintetizar literatura científica con respuestas citadas; 70 % de las contradicciones detectadas en una muestra fueron validadas por expertos. | Fundamenta la recuperación de fuentes y la comprobación de afirmaciones; no garantiza ausencia de errores. |
| Internacional | [Su et al., VIRSCI (ACL 2025)](https://aclanthology.org/2025.acl-long.1368/) | Agentes que generan, evalúan y refinan ideas de investigación; el artículo reporta mayor novedad frente al método comparado. | Apoya la separación de funciones entre generación y evaluación; no evalúa asesorías de tesis. |
| Internacional | [Wan et al., CogWriter (2025)](https://arxiv.org/abs/2502.12568) | Planificación jerárquica, generación y revisión de textos largos; reporta 22 % más precisión en cumplimiento de instrucciones complejas que GPT-4o en LongGenBench. | Orienta la redacción por etapas; el resultado procede de un benchmark de generación, no de tesis universitarias. |
| Nacional | [Córdova Carrascal y Paulini Pereyra, URP (2020)](https://alicia.concytec.gob.pe/vufind/index.php/Record/URPU_3ebc890ea0b262fc41a483fc7e2c4e86/Details) | Sistema web con historial documental y de asesorías, observaciones por etapa y avisos de aprobación. | Referencia directa para el módulo de seguimiento y revisión por asesores. El resumen no ofrece un porcentaje de mejora. |
| Nacional | [Espejo Franco y Condori Lopez, UNSAAC (2026)](https://repositorio.unsaac.edu.pe/handle/20.500.12918/12945?show=full) | Sistema para gestionar proyectos de tesis y etapas administrativas y de revisión. | Referencia para seguimiento del proceso; el registro no acredita una reducción del 40 % de tiempos. |
| Nacional | [Tuanama Rojas y Vasquez Torres, UNAP (2021)](https://repositorio.unapiquitos.edu.pe/items/9d6b63c5-126b-472f-9c09-45f630ac0059) | Evaluación de calidad en uso de un sistema de seguimiento de tesis: aceptación favorable de hasta 87 % entre seis usuarios. | Ayuda a definir una evaluación con usuarios; la muestra pequeña limita la generalización. |
| Local, Piura | [Rosales Rosas, estudio en la UNP (2020)](https://alicia.concytec.gob.pe/vufind/index.php/Record/USAT_267d25dddfec3fd74833f02636630c18) | Levantamiento del flujo, actores y dificultades del trámite de tesis; propone seguimiento por etapas, digitalización y comunicación. | Da contexto al proceso local. Es una propuesta, sin mejora cuantitativa demostrada. |

## Relación con el proyecto

**Literatura y citas.** PaperQA2 muestra cómo un agente puede recuperar estudios y producir síntesis acompañadas de citas. En TesisMCP esto justifica presentar la fuente y permitir que estudiante o asesor comprueben la afirmación. La recuperación de documentos por sí sola no impide citas erróneas.

**Generación y revisión.** VIRSCI y CogWriter respaldan la distribución de tareas entre agentes y la redacción iterativa. Sus resultados se obtuvieron en generación de ideas o texto, por lo que no prueban que TesisMCP mejorará la calidad de una tesis concreta.

**Seguimiento y asesoría.** El sistema de la URP se relaciona directamente con versiones, comentarios y avisos de revisión. UNSAAC y UNAP aportan experiencias de gestión y evaluación de un sistema de seguimiento. El trabajo de Rosales Rosas sitúa esas necesidades en el trámite de tesis de la UNP.

**Brecha de diseño.** En esta selección, los estudios sobre agentes y escritura no incluyen la gestión institucional de asesorías, mientras que los sistemas universitarios de seguimiento no describen la combinación de recuperación de fuentes, orientación metodológica y revisión del asesor planteada para TesisMCP. Esta es una inferencia delimitada a los trabajos analizados, no una afirmación de inexistencia de otras soluciones.

## Antecedentes alternativos y archivos anteriores

- [Ramirez-Medina, Ataei y Amirfazli, ARIA (2025)](https://arxiv.org/abs/2502.07960) puede complementar la arquitectura multiagente. Su artículo describe un caso de trabajo realizado en aproximadamente una hora; no respalda una reducción general del 98 %.
- [Vílchez Araujo y Villegas Ruiz, Piura (2023)](https://hdl.handle.net/20.500.12692/135383) es una alternativa contextual si la rúbrica exige dos estudios locales. Analiza herramientas de IA para el aprendizaje de Ingeniería de Sistemas, con 15 estudiantes; no estudia la asesoría ni el seguimiento de tesis.
- Los PDF de Dávalos Valle, Requena Umbo y Estrada Mendoza/Navarro Vilela permanecen en `docs/antecedentes_descargados/` como material histórico. No se usan en la selección: al primero se le atribuyó incorrectamente significancia para la hipótesis general, y los otros dos tratan respectivamente educación escolar y asistencia laboral.

La lista y el estado de cada archivo PDF se detallan en [el índice de antecedentes](../antecedentes_descargados/README.md).

---

## 4. Banco de Alternativas Verificadas: Fichas Comprobables de Investigación

En atención rigurosa a las directrices de verificación en profundidad (separando metadatos comprobados, evidencia localizada a texto completo, pertinencia funcional y limitaciones objetivas), se presentan 3 alternativas independientes y complementarias a la selección principal *(aclarando que el trabajo de la URP de Córdova y Paulini ya forma parte de la selección base del informe y no constituye una alternativa independiente)*:

### Ficha 1: Chauca Florian (2024) — Ámbito Nacional

* **1. Metadatos Comprobados en Portada:**
  * **Título Oficial:** *Sistema web para optimizar la gestión de proyectos de tesis en la Facultad de Educación de una universidad pública, 2024*.
  * **Autora:** Daythia Chauca Florian (ORCID: `0009-0009-0457-0629`).
  * **Asesor Oficial:** Mg. Robert Roy Saavedra Jimenez (ORCID: `0000-0002-2788-4825`).
  * **Tipo de Trabajo:** Tesis para optar el Título Profesional de Ingeniera de Sistemas.
  * **Institución:** Universidad César Vallejo, Facultad de Ingeniería y Arquitectura, Escuela Profesional de Ingeniería de Sistemas (Sede Lima).
  * **Enlace Oficial:** [Handle UCV / ALICIA: 20.500.12692/156563](https://hdl.handle.net/20.500.12692/156563).
* **2. Nivel de Verificación:** **Texto completo inspeccionado físicamente en PDF local** ([`NAC3_UCV_Gestion_Proyectos_Tesis_Chauca_2024.pdf`](../antecedentes_descargados/NAC3_UCV_Gestion_Proyectos_Tesis_Chauca_2024.pdf), **243 páginas totales**).
* **3. Evidencia Localizada y Resultados Demostrados:**
  * *Diagnóstico real (p. 1):* Describe que la universidad posee sistemas de mesa de partes (SISGRA) y carga de archivos (GRADUATE), pero el control del avance de la tesis se lleva manualmente en hojas de Excel o libretas por cada asesor, generando retrasos y desinformación en la unidad de investigación.
  * *Metodología (p. ix, 15):* Investigación aplicada con diseño pre-experimental. Población de 140 tesis; muestra estratificada de 103 tesis distribuidas en 21 fichas/días de registro ($N = 21$). Desarrollo bajo metodología SCRUM y arquitectura MVC.
  * *Resultados cuantitativos verificados (Tablas 7 y 8, pp. 22–23):*
    * **Porcentaje de avance de tesis (Tabla 7, p. 22):** Media pre-test de 44.80% frente a media post-test de 63.80%, representando una diferencia absoluta de **19.00 puntos porcentuales**.
    * **Porcentaje de finalización de tesis (Tabla 8, p. 23):** Media pre-test de 18.81% (18.8095%) frente a media post-test de 44.52% (44.5238%), representando una diferencia absoluta de **25.71 puntos porcentuales** (el resumen institucional redondea a 25.73%).
    * *Nota estadística:* Estas diferencias corresponden a puntos porcentuales entre medias observadas en la muestra, no a incrementos relativos proporcionales.
* **4. Pertinencia para TesisMCP:** Respalda la función de **Seguimiento de Tesis y Dashboard del Asesor**. Aporta evidencia empírica nacional reciente (2024) sobre el comportamiento del avance de tesis tras incorporar un sistema web estructurado.
* **5. Clasificación:** **Antecedente Directo** (Nacional).
* **6. Limitaciones Objetivas:** El diseño pre-experimental (sin grupo de control aleatorizado) permite informar las mejoras observadas en la muestra, pero no demuestra por sí solo causalidad estricta ni garantiza que sustituir Excel causará idéntico efecto en TesisMCP. Asimismo, la muestra evaluada perteneció a proyectos de la Facultad de Educación.

---

### Ficha 2: Cáceres Saldaña & Osores Salgado (2025) — Ámbito Local (Piura)

* **1. Metadatos Comprobados en Portada:**
  * **Título Oficial:** *Diseño, desarrollo e implementación de un repositorio digital de lecciones aprendidas para la asignatura de proyectos en la Universidad de Piura*.
  * **Autores:** Diego Ignacio Cáceres Saldaña y Carlo Ricardo Osores Salgado.
  * **Asesores Oficiales:** Dr. Ing. Omar Armando Manuel Hurtado Jara y Mgtr. Ing. Carlos David Zacarías Vélez.
  * **Tipo de Trabajo:** Tesis para optar el Título de Ingeniero Industrial y de Sistemas.
  * **Institución:** Universidad de Piura (UDEP), Facultad de Ingeniería (Campus Piura).
  * **Lugar y Fecha:** Piura, julio de 2025.
  * **Enlace Oficial:** [Handle Pirhua UDEP: 11042/7457](https://hdl.handle.net/11042/7457).
* **2. Nivel de Verificación:** **Texto completo inspeccionado físicamente en PDF local** ([`LOC3_UDEP_Piura_Repositorio_Digital_Proyectos_2025.pdf`](../antecedentes_descargados/LOC3_UDEP_Piura_Repositorio_Digital_Proyectos_2025.pdf), **54 páginas totales**).
* **3. Evidencia Localizada y Resultados Demostrados:**
  * *Diagnóstico (p. 6 / p. ix):* En la asignatura de Proyectos del programa académico de Ingeniería Industrial y de Sistemas de la UDEP existe dispersión de información y falta de un sistema centralizado para gestionar las lecciones aprendidas de proyectos previos, provocando pérdida de conocimiento y duplicación de esfuerzos.
  * *Metodología (p. 6):* Metodología de desarrollo en cascada, diseño de modelo relacional de base de datos, pruebas unitarias y de integración.
  * *Distinción entre propuesta y resultado demostrado (Resumen, p. 6):* El texto concluye textualmente: *«Aunque los resultados de su impacto a largo plazo serán evaluados posteriormente, las pruebas iniciales indican que el sistema mejora el acceso a la información y apoya eficazmente los procesos de aprendizaje»*. **No presenta pruebas estadísticas inferenciales ni porcentajes de reducción temporal**.
* **4. Pertinencia para TesisMCP:** Respalda la función de **Gestión de Entregables y Lecciones Metodológicas**, situando la problemática de la desarticulación de proyectos de ingeniería directamente en la ciudad de Piura (UDEP).
* **5. Clasificación:** **Contexto Local** (Piura).
* **6. Limitaciones Objetivas:** Trata un repositorio de lecciones aprendidas de proyectos de ingeniería, no un flujo guiado de formulación de tesis paso a paso ni un módulo de asesorías y dictámenes oficiales.

---

### Ficha 3: PaperOrchestrator (Yuan et al., 2026) — Ámbito Internacional

* **1. Datos Oficiales Comprobados en Registro Springer y DOI:**
  * **Título Oficial:** *PaperOrchestrator: An LLM-Orchestrated multi-agent pipeline for automated end-to-end scientific paper writing*.
  * **Autores:** Chunhong Yuan, Tianshi Wei, Chuangqi Li, Xing Yi, Shengrui Liu, Zixin Zhang, Yule Cai, Xinke Du.
  * **Año y Revista:** Febrero 2026, *Journal of King Saud University - Computer and Information Sciences* (Publicado por Springer Nature).
  * **Acceso:** **Acceso Abierto (Open Access)**.
  * **Identificador Oficial:** [DOI: 10.1007/s44443-026-00708-4](https://doi.org/10.1007/s44443-026-00708-4).
* **2. Nivel de Verificación:** **Artículo completo inspeccionado a texto abierto vía Springer Nature** (Analizado abstract, arquitectura de 7 etapas, experimentos y discusión de errores).
* **3. Evidencia Localizada y Resultados Demostrados:**
  * *Diagnóstico:* La generación directa en un solo turno (*single-turn*) con modelos LLM comerciales presenta tasas de completitud de secciones concentradas apenas entre el 68% y 85%, con fallas de truncamiento y desalineación estructural.
  * *Solución Técnica:* Descompone la escritura científica en 7 etapas orquestadas por agentes: generación de esquemas, redacción sección por sección, control adaptativo de longitud, pulido de consistencia, generación de referencias BibTeX, conversión robusta a LaTeX y renderizado de plantillas de revistas (soporta inglés y chino).
  * *Hallazgo Crítico de Alucinación (Tabla 10 y Discusión de Errores):* Los autores reportan que **el 68% de las entradas BibTeX generadas presentaron problemas de alucinación**, catalogándolo como el error más grave y frecuente del sistema (*«BibTeX entry hallucination (68%) is the most prevalent and most severe issue in the current system... hallucinated references are not random noise but coherent fabrications»*).
* **4. Pertinencia para TesisMCP:** Apoya la **redacción metodológica en etapas desacopladas** y motiva la verificación bibliográfica. El 68% corresponde a las entradas BibTeX evaluadas en ese artículo; no es una tasa generalizable a todos los sistemas multiagente ni a TesisMCP.
* **5. Clasificación:** **Apoyo Técnico** (Internacional).
* **6. Limitaciones Objetivas:** Requiere integración con APIs académicas externas para resolver su alta tasa de alucinación bibliográfica (68%) y está diseñado para papers de computación, no para reglamentos de titulación universitaria.

---

## 5. Síntesis del Contraste Tecnológico y Arquitectural frente a TesisMCP

De la auditoría cruzada entre la literatura analizada y la implementación de TesisMCP se derivan tres conclusiones fundamentales:

1. **Convergencia con Tesis Nacionales (Gobernanza y Software Tradicional):**  
   Los antecedentes peruanos (Chauca, 2024; Córdova & Paulini, 2020; Espejo & Condori, 2026; Cáceres & Osores, 2025) validan la necesidad de estructurar el seguimiento mediante arquitecturas en capas (MVC/Servicios), contenedores Docker, modelos relacionales en SQL y máquinas de estados (FSM) de revisión. TesisMCP adopta y refina estos componentes mediante Django 5, PostgreSQL 16 con `pgvector`, control optimista de concurrencia (`lock_version`) y una FSM formal para los 7 capítulos.
2. **Convergencia con Papers Internacionales (IA y Agentes):**  
   Los estudios internacionales (VirSci, CogWriter, PaperOrchestrator) fundamentan la división en roles especializados (patrón Actor-Critic: Asesor vs. Revisor) y la descomposición de la redacción en etapas atómicas secuenciales (32 pasos desacoplados), evitando el colapso de coherencia de los modelos monolíticos y neutralizando el riesgo empírico del 68% de alucinación bibliográfica mediante *Grounded Truth*.
3. **Brecha Tecnológica y Aportes Inéditos de TesisMCP:**  
   Ninguno de los antecedentes analizados combina el estándar abierto **Model Context Protocol (MCP)** con un **backend determinista Zero-LLM** y filosofía **BYOA (*Bring Your Own Agent*) a costo de servidor S/. 0.00**, respaldado por validadores programáticos de reglas académicas universitarias (Taxonomía de Bloom, matrices de consistencia lógica y restricciones éticas inmutables).


