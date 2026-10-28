# Análisis neutral de la reunión con el asesor A

- **Fecha del audio:** 2026-10-22, según los nombres de los audios entregados por el usuario.
- **Fuente textual inspeccionada íntegramente:** `transcripci_n_de_reuni_n_y_asesor_a.md`.
- **Huella SHA-256 de la fuente:** `090274f318e6d7f2b2e1fcc592128d95ca7af4550cb93b1e50782825c376bfa1`.
- **Cobertura temporal de la transcripción:** 00:00–17:28.
- **Nivel de verificación:** análisis del texto completo de una transcripción automática; no se verificó esta transcripción contra el audio.
- **Identificación de hablantes:** la fuente no contiene diarización. Las referencias a “docente”, “asesor” o “equipo” son inferencias contextuales y no identificaciones biométricas.
- **Estado:** analizada; requiere revisión humana de pasajes ambiguos.

## 1. Conclusión neutral

La reunión no registra un rechazo ni un reemplazo explícito de TesisMCP. La orientación central es mantener la idea, delimitar primero un caso institucional manejable, validar la ruta con investigadores y asegurar que el producto resuelva el problema metodológico del tesista en lugar de limitarse a ser una interfaz que envía preguntas a un chat.

La frase más cercana a una definición de alcance inicial es “Limítalo a Informática UTP” (03:03). Esto se presenta como recomendación de secuenciación del producto: comenzar con una universidad y carrera, comprobar el funcionamiento y fortalecerlo después. No demuestra por sí sola que el equipo haya aceptado formalmente ese alcance.

## 2. Registro de evidencia clasificada

| Tiempo | Tipo de intervención | Evidencia o paráfrasis fiel | Certeza | Implicación posible para TesisMCP |
| :---: | :--- | :--- | :---: | :--- |
| 01:58–02:04 | Aclaración | Se afirma que ya se explicó “lo que quiere la gente del otro lado” y que se tendrían los requerimientos. | Media | La frase no enumera requisitos; no debe usarse como prueba de que el alcance esté cerrado. |
| 02:09–03:06 | Recomendación fuerte | Descargar el reglamento de grados y títulos y el reglamento de líneas de investigación de UTP; orientar primero el producto a una universidad y limitarlo a Informática UTP. | Alta | Definir un piloto institucional antes de generalizar. |
| 02:19–02:58 | Aclaración metodológica | Las normas de presentación varían por carrera; se mencionan IEEE, APA y Vancouver como ejemplos. | Alta respecto de lo dicho; no verificada normativamente | Modelar el formato por institución/carrera, pero cotejar cada norma con documentos oficiales. |
| 03:24–03:55 | Recomendación y riesgo | Validar el sistema con investigadores y no construirlo empíricamente a partir de la interpretación de un solo libro o un solo flujo docente. | Alta | Incorporar validación experta y admitir variantes metodológicas. |
| 04:26–05:46 | Observación y propuesta | Distintos usuarios emplean distintos LLM; TesisMCP debería proporcionar “el camino” o flujo sin depender de la cuenta elegida. | Alta | Mantener el enfoque BYOA/cliente LLM desacoplado. |
| 06:04–08:24 | Principio de producto | El ingeniero debe resolver un problema; la aplicación es un medio y no el fin. | Alta | Formular el valor del producto desde la reducción de fricción y errores metodológicos. |
| 08:35–09:18 | Consejo | No basta con obtener texto o Word: el tesista debe leer lo realizado por otros autores y reconocer hasta dónde llegaron. | Alta | Mantener revisión humana y trazabilidad de evidencia. |
| 09:18–09:47 | Preferencia académica | Para tesis de pregrado se recomienda trabajar con artículos científicos en lugar de depender solo de tesis previas. | Alta como preferencia del hablante | Priorizar literatura científica sin excluir fuentes válidas por una regla no institucionalmente comprobada. |
| 11:19–11:34 | Observación | Se distingue “usar IA” de simplemente chatear con ella. | Alta | El diferenciador debe ser el flujo, las validaciones y la evidencia, no una caja de chat. |
| 14:15–15:03 | Ejemplo de solución | Se propone simplificar la construcción de fórmulas y la consulta de Scopus mediante una aplicación comprensible. | Alta | Considerar generación trazable de ecuaciones y apoyo a búsqueda; la integración directa con Scopus queda por evaluar. |
| 16:01–16:50 | Aclaración de roles | Se distingue al experto temático del metodólogo. | Alta | La validación no debería descansar en un único perfil experto. |
| 17:00–17:28 | Sugerencia | La IA podría ayudar a revisar ortografía. | Alta | Función auxiliar posible; no constituye el núcleo del producto. |

## 3. Clasificación temática

### Necesidades del usuario expresadas o inferibles con respaldo

1. Recibir una ruta metodológica ordenada, no respuestas aisladas de un chat (05:28–05:46; 11:19–11:34).
2. Trabajar con la normativa y la línea de investigación de su institución/carrera (02:09–03:06).
3. Simplificar tareas difíciles de búsqueda científica (14:15–15:03).
4. Conservar control humano sobre lectura, interpretación y validación (03:24–03:55; 08:35–09:18).

### Consejos y guías

- Empezar por Informática UTP y ampliar después.
- Validar el flujo con investigadores de perfiles metodológicos y temáticos.
- Diseñar el sistema alrededor del problema del usuario.
- Priorizar artículos y evidencia verificable.
- Mantener independencia respecto del proveedor de IA.

### Riesgos advertidos

- Generalizar desde un único libro o una única manera de asesorar.
- Confundir producir una aplicación con resolver el problema.
- Entregar texto generado sin leer las fuentes.
- Replicar una caja de chat sin un flujo académico comprobable.

### Ejemplos, no requisitos

- Las opiniones comparativas sobre Claude, ChatGPT, Gemini, Grok o DeepSeek no constituyen una evaluación técnica controlada.
- Los ejemplos de BUSCARV, ascensores, agentes de venta, publicaciones y semilleros son ilustrativos; no forman parte del alcance de TesisMCP.
- Las cifras personales mencionadas por el hablante no se trasladan como métricas del proyecto.

## 4. Decisiones que no quedaron demostradas

- No consta una aceptación formal del alcance “solo Informática UTP”.
- No se acordó integrar directamente Scopus.
- No se acordó una estrategia comercial.
- No se pidió generar una tesis completa de manera autónoma.
- No se definió qué documento institucional exacto gobernará cada regla.

## 5. Preguntas de seguimiento

1. ¿El equipo acepta Informática UTP como piloto vinculante o solo como demostración?
2. ¿Qué investigadores validarán la ruta y mediante qué instrumento?
3. ¿La búsqueda científica se limitará a generar ecuaciones y registrar evidencia o incluirá acceso directo a bases licenciadas?
4. ¿Qué reglas corresponden a la universidad, cuáles a la carrera y cuáles son preferencias del asesor?

