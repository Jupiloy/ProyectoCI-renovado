# Plan de entregas y definición de terminado del backend

**Estado operativo local tras la reparación:** la base `tesismcp` de `tesismcp-local-pg` recibió las migraciones `0024`–`0044`, después de un respaldo conjunto DB+media y un ensayo de restauración/migración aislado. El desfase hasta `0023` fue el hallazgo inicial; las puertas históricas 7/7 no verificaban migraciones aplicadas. El verificador incorpora ahora ese control separado. Consultar el [registro B10](./paquete_b10_operacion_local_y_despliegue.md) para evidencia, comandos y límites; no confundir esta reparación local con el cierre de B10 o del producto.

**Estado:** B3.1–B3.6, B4.1–B4.5, B6.1–B6.4, B7 y B8.1–B8.4 verificados. Puerta integral B8: 7/7, 479.66 s; pytest 457.26 s; exit code 0. **Actualizado:** 26/10/2026.

P01–P32 y capítulos 1–7 son la base heredada; el alcance funcional objetivo incluye datos reales, análisis, resultados y entrega. Las entregas limitan riesgo y producen incrementos integrados; no redefinen el producto como una versión reducida. El usuario priorizó empezar ahora la configuración de recorrido/prompts para mostrarla al profesor y recibir ajustes sin reconstruir el backend. No asignar semanas ni estimaciones hasta que el equipo mida tareas y disponibilidad.

**Objetivo de salida:** terminar el núcleo backend antes de concentrarse en el frontend. La [definición verificable de backend listo para frontend](./criterio_backend_listo_para_frontend.md) establece recorridos completos, API, integración y condiciones de cierre. B1.1–B1.3 implementan snapshots, revisión/aprobación ancladas y exportación DOCX del snapshot aprobado. B1+B2.2 establece documento canónico versionado y B1+B2.3 conecta propuestas P05/P29 mediante preview/diff y aceptación versionada. Sigue pendiente probar ida/vuelta con frontend, anclas por bloque y ampliar mappings solo con contratos tipados. B5.1 tiene jobs/worker/API; verificar una llamada LLM real requiere credenciales. No reiniciar bloques implementados ni declarar terminado el backend.

## Entregas

| Entrega | Resultado demostrable | Dependencias/decisiones previas |
|---|---|---|
| B0. Auditoría de brechas | Matriz código→requisito con rutas, estado, pruebas, migraciones/riesgos y primera entrega seleccionada. | Lectura de código, modelos, migraciones, API y pruebas vigentes. |
| B1. Versiones y revisión canónica | **B1.1–B1.3 y persistencia base B1+B2.2 implementados:** snapshot integral, comentarios/aprobación anclados, DOCX aprobado y documento canónico estructurado por capítulo. Sigue pendiente ida/vuelta del frontend, comentarios por bloque y aplicación de diffs IA aceptados. | Consultar B1.1, B1.2, B1.3 y [B1+B2.2](./paquete_b1_b2_2_documento_canonico.md). No rehacer snapshots, anclas actuales ni exportación. ADR-BE-06 queda PROPOSED hasta validar editor/frontend. |
| B2. API web base de proyecto/metodología | Servicios web cubren proyecto, perfil, temas, preparación/guardado de pasos, permisos y estados con errores/versiones estables. | B0; no duplicar lo existente. Acordar frontend/editor solo para el contrato compartido necesario. |
| B3. Búsqueda asistida, fuentes y procedencia | **Implementación en el corte:** B3.1–B3.5 implementados; B3.6 registra decisiones humanas versionadas de duplicidad, separación o preferencia por un registro. Ambos registros y su procedencia permanecen. | Migraciones `0027`–`0030`. Scopus/WoS sigue siendo búsqueda manual del usuario; API del proveedor no es requisito. La lectura con localizadores de otros formatos pasa a B7. Ver guía de continuidad. |
| B4. Citas, IEEE/Zotero y revisión de afirmaciones | **B4.1–B4.5 implementados:** ocurrencias de citas en revisiones canónicas, IEEE preliminar, evidencia vinculada a pasajes y revisión humana, propuestas de reemplazo con diff/aceptación, conexión Zotero OAuth 1.0a de solo lectura. | Migraciones `0031`–`0035`; P20 admite IEEE y conserva APA por compatibilidad. Render IEEE no es formato editorial completo. Falta configuración y prueba OAuth real con aplicación/cuenta de prueba. No hay dictamen semántico automático. Ver [detalle B4](./implementacion_b4_citas_ieee_zotero.md). |
| B5. Método configurable **implementado** | Recorrido/prompts por proyecto con versiones, diff, validación/publicación, modo de grafo y tareas `USR_...`; outputs custom se persisten desde el cliente. | [Contrato específico](./contrato_recorrido_y_prompts_configurables.md). P01–P32 conservan contratos fijos; persistencia y ejecución por dependencias reales verificadas. |
| B5.1. Ciclo de generación por tarea **parcialmente implementado** | Para P01–P32 y `USR_...`: API crea job, fija contexto/prompt/versiones, valida salida y deja propuesta para aceptar/rechazar. Worker, ciclo de decisión y adaptador Gemini implementados; falta verificar una llamada real con credenciales. | [Especificación de generación IA](./especificacion_generacion_ia_y_resultados.md) y [paquete Gemini B5.1](./implementacion_adaptador_gemini_b5_1.md). Reutilizar `AIGenerationJob`, `output_schema`, factory y aceptación existentes; no rehacer API/worker ni crear otra entidad. |
| B1+B2. Documento canónico y aceptación | **B1+B2.1–B1+B2.3 implementados en backend:** P05/P29 se materializan en `ChapterRevision`; hay documento por capítulo con árbol v1 y revisiones append-only; el snapshot v2 fija la versión y el DOCX aprobado la renderiza. P05/P29 presentan diff `REPLACE_DOCUMENT` con versiones/hash y solo se aplican tras aceptación explícita; `USR_...` y otros outputs no se mapean al árbol. **Pendiente:** round-trip real del editor frontend y comentarios anclados a bloques (hoy offsets Markdown). | Revisar [B1+B2.1](./paquete_b1_b2_1_materializacion_textual_propuestas.md), [B1+B2.2](./paquete_b1_b2_2_documento_canonico.md) y [B1+B2.3](./paquete_b1_b2_3_diffs_ia_documento.md). ADR-BE-06 sigue PROPOSED hasta validar el editor/frontend. |
| B6. Multiagentes, lotes y apoyos | **B6.1–B6.4 implementados y verificados:** puerta integral 7/7, 395.34 s, exit code 0; suite pytest 374.20 s. Incluye lotes, worker con concurrencia acotada, síntesis estructurada trazable y revisión puntual mediante invitaciones temporales de alcance mínimo. | Reutiliza `AIGenerationJob` y el worker existente; la síntesis no modifica documentos canónicos. El apoyo no recibe membresía general. Ver [paquete B6 completo](./paquete_b6_completo.md), [B6.3](./paquete_b6_3_sintesis_trazable.md), [B6.4](./paquete_b6_4_invitaciones_apoyo.md) y [pendientes](./pendientes_backend_despues_b4.md). |
| B7. Documentos multiformato | **Cerrado y verificado:** upload PDF/DOCX/PPTX/XLSX; original/hash preservado; segmentos/localizadores; fórmula y caché separadas; OCR selectivo para PDF mixto; indexación/búsqueda candidata con localizadores; harness reproducible. Puerta 7/7, 381.76 s, exit code 0; pytest 362.49 s. | Benchmark local ejecutado en 9 PDF/971 páginas, no representativo; no incluye formatos Office ni mide precisión OCR. Una evaluación de corpus autorizado más amplio es futura y no bloquea la implementación. No se afirma OCR de imágenes Office ni evaluación científica. Ver [paquete B7](./paquete_b7_multiformato.md). |
| B8. Datos, figuras y exportación | **Cerrado y verificado:** datasets/versiones originales; recetas tabulares declarativas; figuras BAR/LINE/SCATTER versionadas; nodos tipados; manifest/hash en snapshot; DOCX aprobado desde versiones congeladas. Puerta 7/7, 479.66 s, pytest 457.26 s, exit code 0. | [Paquete B8](./paquete_b8_datos_figuras.md). No ejecutar código del usuario, hacer inferencia estadística ni presentar datos sintéticos como evidencia académica. |
| Ampliación empírica posterior a P32 | Preparación de campo, registro de autorizaciones, datos originales, análisis por enfoque, resultados/discusión/conclusiones trazables y revisión; sin numeración P nueva hasta diseñar contratos. | Decisiones metodológicas e institucionales aplicables; modelos de datos/procedencia y revisión. [Criterio de salida](./criterio_backend_listo_para_frontend.md). |
| B9. Conectores licenciados opcionales | **Evaluación técnica concluida; ningún conector API habilitado.** El flujo manual asistido e importación B3 cubren la búsqueda base. Scopus/WoS API solo se implementará si agrega valor y UTP/proveedor confirma por escrito entitlement, uso, datos, autenticación y cuotas. n8n no tiene caso de uso confirmado. | B9 está **condicionado, no implementado ni bloqueante**. No reutilizar credenciales personales ni automatizar login. Ver [paquete B9](./paquete_b9_conectores_licenciados.md), con estado del código, evidencia oficial y puerta de habilitación. |
| B10. Operación local y despegue configurable | **Parcial: desarrollo local con Compose/Podman; respaldo conjunto DB+media privado y restore drill aislado probado.** La base activa fue migrada de `0023` a `0044` tras ensayar la actualización y leer los archivos restaurados. El nuevo verificador comprueba migraciones aplicadas; no hay scheduler ni copia fuera del disco. | Avanzar B10.1–B10.3 en local y mantener configurables DB/secrets/storage/workers/backups. B10.4 exige elegir infraestructura/responsables antes del piloto no local. Ver [paquete B10](./paquete_b10_operacion_local_y_despliegue.md); no afirmar que un volumen equivale a backup. |

Las filas pueden combinarse en un recorrido vertical cuando sus dependencias estén cubiertas. B9 no bloquea la búsqueda asistida ni la importación manual de B3. B4 distingue identidad bibliográfica, existencia de texto extraído y evaluación humana del respaldo de una afirmación. Su comportamiento detallado está en [implementación B4](./implementacion_b4_citas_ieee_zotero.md) y la participación de apoyos en [especificación de búsqueda y revisión de evidencia](./especificacion_busqueda_y_revision_de_evidencia.md).

**Orden operativo inmediato:** iniciar la integración del frontend con los contratos backend ya implementados, empezando por el editor enriquecido y la experiencia de dataset/tabla/figura. La integración frontend B1+B2 sigue pendiente. La evaluación representativa del corpus B7 puede planificarse como actividad empírica separada.

**Siguiente trabajo:** integración frontend de B1+B2 y completar las brechas priorizadas para el recorrido integrado. B5 por sí solo configura y ejecuta tareas con outputs aportados; B5.1 añade propuestas y adaptador Gemini, aunque la llamada real requiere credenciales. Snapshots, aprobación y DOCX aprobado ya existen. B9 fue evaluado y queda condicionado a evidencia institucional/proveedor y caso de uso; no bloquea esa integración. B10 y los recorridos integrados son parte de la salida.

## Definición de terminado por cambio

Un cambio de backend se considera implementado solo cuando:

1. Requisito y alcance se enlazan a este paquete y a la fuente académica/institucional cuando aplique.
2. Se inspeccionaron símbolo/ruta/modelo/migración existentes y se reutilizaron o justificó una adición.
3. Los contratos de entrada/salida, actor, scope, errores, versiones, idempotencia y transacción están documentados.
4. Los datos legados se leen; migraciones son comprobables y no destruyen historial.
5. Pruebas cubren éxito, acceso denegado, datos inválidos, concurrencia/repetición y efectos observables según el cambio.
6. Web y MCP llaman lógica de dominio común; el frontend nunca es autoridad de permisos.
7. Una tarea IA permanece propuesta hasta aceptación; una exportación indica snapshot y formato realmente comprobado.
8. README/API, guía backend, estado de producto y diagramas afectados se actualizan en el mismo cambio.
9. Las comprobaciones obligatorias del proyecto se ejecutan y se informa su salida/código. No decir “listo” si la puerta definida por `AGENTS.md` falla.

## Verificación de cierre de entrega

Usar la puerta requerida por `AGENTS.md` y reportar resultados reales. Además, para cada entrega guardar evidencia específica: IDs de revisión, salida API, conflicto, migración, job o archivo exportado. El conjunto automatizado no prueba validez científica, autorización externa ni aceptación del asesor; esas comprobaciones se registran por separado.

## Decisiones del equipo que pueden permanecer abiertas por etapas

No bloquear B0/B1 con decisiones no relacionadas. Antes de implementar el dominio correspondiente, resolver:

- guía UTP y formato exacto de entrega para el piloto IEEE;
- campos/forma del árbol de documento del editor;
- modelo de autenticación y acceso a la web;
- permisos/cuotas UTP de Scopus/WoS y proveedor IA web;
- prueba de OAuth Zotero en vivo y alcance de sincronización/campos vivos;
- retención de documentos y muestras de estilo;
- criterio de aprobación por capítulo y cambios retroactivos de metodología;
- formatos institucionales de DOCX/PDF y si LaTeX entra en el alcance demostrable.

La consulta e importación manual de Scopus/WoS no dependen de resolver permisos de API. Solo el conector programático requiere permisos y cuotas confirmados. Si se activan invitados puntuales, cerrar el paquete de recursos y la matriz de permisos antes de darles acceso; esto no bloquea el trabajo del tesista y asesor.
