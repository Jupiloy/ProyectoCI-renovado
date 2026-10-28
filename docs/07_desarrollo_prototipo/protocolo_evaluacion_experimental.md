# Protocolo de Evaluación Experimental del Prototipo TesisMCP

> **Estado:** protocolo propuesto, todavía no ejecutado. No existen en el repositorio respuestas de participantes, resultados SUS, tiempos comparativos ni pruebas inferenciales. Ninguna cifra de esta planificación debe presentarse como resultado observado.

> **Propósito:** Definir el diseño experimental, hipótesis, variables, métricas cuantitativas e instrumentos de evaluación para sustentar la sección de **Resultados y Discusión** del Informe Final de Curso Integrador 1 (`docs/06_informe_final_curso/informe_academico_curso_integrador_IEEE.docx`).

---

## 1. Planteamiento de Hipótesis de Investigación

* **Hipótesis General ($H_1$):**  
  La aplicación de la plataforma **TesisMCP**, basada en una arquitectura modular desacoplada mediante el protocolo MCP y validación estructurada por pasos, **reduce significativamente el tiempo promedio de formulación metodológica** de los Capítulos 1 y 2, y **disminuye la tasa de observaciones emitidas por el asesor** en comparación con el proceso tradicional asistido únicamente por procesadores de texto convencionales.

* **Hipótesis Nula ($H_0$):**  
  No existe diferencia estadísticamente significativa en el tiempo promedio de formulación metodológica ni en la tasa de observaciones entre el uso de TesisMCP y el método tradicional manual ($p \ge 0.05$).

---

## 2. Variables del Estudio y Cuadro de Operacionalización

| Variable | Tipo | Definición Operacional | Indicador | Escala de Medición |
| :--- | :--- | :--- | :--- | :--- |
| **TesisMCP (Arquitectura desacoplada MCP)** | Independiente ($V_I$) | Uso del entorno TesisMCP con servidor MCP, persistencia relacional y control de versiones frente al método tradicional. | Condición experimental: (0 = Tradicional / Word, 1 = Experimental / TesisMCP). | Nominal dicotómica |
| **Tiempo de Formulación Metodológica** | Dependiente ($V_{D1}$) | Tiempo total transcurrido desde el inicio de P01 hasta la aprobación del borrador de Capítulo 1 y 2. | Minutos cronometrados en telemetría del sistema. | Razón (Minutos) |
| **Tasa de Observaciones del Asesor** | Dependiente ($V_{D2}$) | Proporción de borradores que reciben al menos un comentario de observación en primera revisión. | $\text{Tasa} = \frac{\text{Revisiones observadas}}{\text{Total revisiones enviadas}} \times 100$ | Razón (Porcentaje %) |
| **Usabilidad Percibida** | Dependiente ($V_{D3}$) | Calidad de interacción, facilidad de uso y satisfacción reportada por los tesistas. | Puntaje global de la escala estandarizada SUS (System Usability Scale). | Intervalo (0 a 100 puntos) |

---

## 3. Instrumento Estandarizado: Escala de Usabilidad del Sistema (SUS)

Se propone aplicar **System Usability Scale (SUS)** con 10 ítems y escala Likert de 5 puntos. Antes de usar una traducción española, el equipo debe registrar la versión publicada y su fuente primaria.

1. Creo que me gustaría utilizar TesisMCP frecuentemente para la elaboración de mi tesis.
2. Encontré el flujo de trabajo de TesisMCP innecesariamente complejo.
3. Pensé que TesisMCP fue fácil de usar.
4. Creo que necesitaría del apoyo de una persona técnica para poder utilizar TesisMCP.
5. Encontré que las diversas funciones en TesisMCP estaban bien integradas.
6. Pensé que había demasiada inconsistencia en este sistema.
7. Imagino que la mayoría de personas aprenderían a usar TesisMCP muy rápidamente.
8. Encontré el sistema muy engorroso o frustrante de usar.
9. Me sentí muy seguro y confiado al utilizar TesisMCP para formular mi metodología.
10. Necesité aprender muchas cosas antes de poder empezar a trabajar con TesisMCP.

### Algoritmo Matemático de Calificación SUS:
* Para cada ítem impar ($1, 3, 5, 7, 9$): Contribución $x_i = \text{Puntaje} - 1$.
* Para cada ítem par ($2, 4, 6, 8, 10$): Contribución $x_i = 5 - \text{Puntaje}$.
* Puntaje total normalizado sobre 100:
  $$\text{SUS Score} = \left( \sum_{i=1}^{10} x_i \right) \times 2.5$$
* El criterio de interpretación y cualquier meta deben definirse y citarse antes de analizar datos; este documento no registra todavía un umbral aprobado por el proyecto.

---

## 4. Muestra Piloto y Procedimiento de Prueba (Semana 12)

1. **Muestra:** pendiente de aprobación y reclutamiento. El tamaño final debe registrarse a partir de participantes reales y criterios de inclusión explícitos.
2. **Diseño:** Cuasi-experimental o pre-experimental con medición pre-test / post-test sobre tareas idénticas de delimitación de título (P04), problema (P06) y justificación (P07).
3. **Análisis Estadístico:**
   * Prueba de normalidad de Shapiro-Wilk sobre las diferencias temporales y puntajes.
   * Si la distribución es normal ($p > 0.05$): Prueba $t$ de Student para muestras emparejadas.
   * Si la distribución no es normal ($p \le 0.05$): Prueba no paramétrica de rangos con signo de Wilcoxon.
   * Nivel de significancia preestablecido: $\alpha = 0.05$.
