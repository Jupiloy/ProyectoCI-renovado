# Diagramas editables del informe IEEE

Cada archivo `.mmd` contiene el código Mermaid de un diagrama de la metodología. Se puede editar como texto y abrir en un editor compatible con Mermaid. Los ocho archivos reproducen los bloques del [informe fuente](../../06_informe_final_curso/informe_academico_curso_integrador_IEEE.md) sin alterar sus entidades ni relaciones.

Los archivos `figura_*_word.dot` contienen el código Graphviz exacto que genera las figuras del [informe Word](../../06_informe_final_curso/informe_academico_curso_integrador_IEEE.docx). También son editables como texto. El informe divide el cuarto diagrama en `figura_4a_word.dot` y `figura_4b_word.dot` para que sus entidades sean legibles.

| Archivo | Apartado del informe | Contenido |
| --- | --- | --- |
| `01_flujo_tesista_asesor.mmd` | 6.4.1 | Flujo operativo del tesista y asesor |
| `02_secuencia_preparar_guardar.mmd` | 6.4.2 | Secuencia para preparar y guardar un paso |
| `03_estados_revision_capitulo.mmd` | 6.5.1 | Estados de revisión de un capítulo |
| `04_er_identidad_proyecto.mmd` | 6.5.2 | Identidad y avance del proyecto |
| `05_er_versiones_revision.mmd` | 6.5.2 | Versiones y revisión |
| `06_er_matriz_variables.mmd` | 6.5.2 | Matriz de consistencia y variables |
| `07_er_instrumentos_indicadores.mmd` | 6.5.2 | Instrumentos e indicadores |
| `08_er_fuentes_evidencia.mmd` | 6.5.2 | Fuentes y evidencia |

Para mantener consistente el informe, los bloques Mermaid de los archivos Markdown ([`modelo_datos_fisico.md`](../modelo_datos_fisico.md), [`informe_academico_curso_integrador.md`](../../06_informe_final_curso/informe_academico_curso_integrador.md) e [`informe_academico_curso_integrador_IEEE.md`](../../06_informe_final_curso/informe_academico_curso_integrador_IEEE.md)) reproducen de forma idéntica las anotaciones de estos `.mmd` (nulabilidad `!`/`?`, longitudes, valores por defecto, choices y metadatos de CHECKs e índices en comentarios `%%`). La especificación tabular completa se encuentra en la [referencia técnica de restricciones e índices](../restricciones_indices_referencia.md). En las figuras 4a–8, el generador crea los archivos `.dot` a partir del Mermaid y reemplaza cualquier edición directa anterior del `.dot`. En las figuras 1–3, el generador crea el `.dot` desde el código Graphviz dentro del script; si se modifica solo el `.dot`, el próximo Word seguirá usando la versión del script.
