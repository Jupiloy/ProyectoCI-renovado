# Pendientes del backend después de B4

**Estado operativo local tras la reparación:** la base `tesismcp` de `tesismcp-local-pg` recibió las migraciones `0024`–`0044`, después de un respaldo conjunto DB+media y un ensayo de restauración/migración aislado. El desfase hasta `0023` fue el hallazgo inicial; las puertas históricas 7/7 no verificaban migraciones aplicadas. El verificador incorpora ahora ese control separado. Consultar el [registro B10](./paquete_b10_operacion_local_y_despliegue.md) para evidencia, comandos y límites; no confundir esta reparación local con el cierre de B10 o del producto.

**Corte:** B8.1–B8.4 implementados y verificados, 26/10/2026.  
**Última puerta — reparación operativa local:** 8/8 controles, 214 pruebas, exit code 0; gate 508.47 s, pytest 482.20 s. Detalle en [registro B10](./paquete_b10_operacion_local_y_despliegue.md).

**Puerta histórica B8.1 (no es la última ejecución):** `TESISMCP_DB_CONTAINER=tesismcp-local-pg ./scripts/verify_podman.sh`, 7/7 pasos aprobados, exit code 0, 383.36 s; pytest 364.62 s (26/10/2026).  
**Estado:** B6.1–B6.4, B7 y B8.1–B8.4 verificados. B8 agrega cuatro modelos (54→58) y migraciones `0041`–`0044`; su puerta integral pasó 7/7 (479.66 s; pytest 457.26 s; exit code 0). B8 ya no es trabajo pendiente. El benchmark local de B7 cubrió 9 PDF/971 páginas y no se considera representativo; la evaluación con corpus autorizado multiformato sigue como trabajo empírico. Se mantienen 32 pasos, 34 herramientas MCP y 35 prompts.

Este archivo es la lista de trabajo restante. El estado de cada punto se debe cambiar solo después de inspeccionar código, completar la implementación acordada y ejecutar la verificación. “Implementado” no significa que dependa de credenciales externas o pruebas institucionales que no estén disponibles.

## 1. B6.1 — control de lotes de generación (cerrado)

**Estado:** implementado y verificado. La puerta integral pasó 7/7, 288.97 s, exit code 0. Conteo comprobado por el verificador: 47 modelos y 36 migraciones.

**Objetivo:** permitir que el titular solicite un grupo acotado de tareas IA independientes, consultar su progreso agregado y cancelar únicamente las tareas que aún no comenzaron.

**Diseño acordado para esta subentrega:**

- Reutilizar `AIGenerationJob`, el snapshot de contexto, la validación y los flujos de aceptación/rechazo existentes. No crear un segundo sistema de jobs ni un agente con escritura directa.
- Persistir lote, orden de sus tareas, asociaciones a jobs existentes, versión de recorrido/estado, solicitud idempotente y hash de contenido.
- Aceptar un máximo pequeño y acotado de tareas distintas; rechazar IDs repetidos y dependencias bloqueantes entre tareas del mismo lote. Las dependencias externas siguen verificándose con `request_task_generation`.
- Crear el lote y todos sus jobs atómicamente. Si una tarea falla validación, no debe quedar un lote medio creado.
- Consultar conteos/estados derivados de los jobs reales. Cada salida se acepta o rechaza por separado; no sintetizar una respuesta global ni modificar capítulos automáticamente.
- Cancelar solo jobs `QUEUED`. Un job `RUNNING` no se cancela a la fuerza; el endpoint informa cuáles siguen ejecutándose.

**Rutas añadidas:** `POST /api/v1/projects/{project_id}/ai-batches`, `GET /api/v1/projects/{project_id}/ai-batches`, `GET /api/v1/projects/{project_id}/ai-batches/{batch_id}` y `POST /api/v1/projects/{project_id}/ai-batches/{batch_id}/cancel`.

**Límite de implementación:** si `TESISMCP_SYNC_AI_GENERATION=True`, el servicio rechaza la creación de lotes. Los trabajos del lote permanecen asíncronos para que un proveedor no se invoque dentro de la transacción de fan-out. El límite de concurrencia efectiva se implementa en B6.2 y su cierre queda sujeto a la puerta integral.

**Fuera de B6.1:** ejecución paralela efectiva (el worker B5.1 actual es singleton), síntesis o merge entre resultados, selección libre de proveedor/modelo por proyecto, nuevos agentes con capacidades propias, invitaciones de expertos/bibliotecarios y asignación de recursos compartidos. B6.1 no cierra B6.

## 2. B6.2 — concurrencia segura del worker (cerrado)

**Objetivo:** habilitar consumidores concurrentes acotados sin reclamar dos veces el mismo `AIGenerationJob`, sin reintentos silenciosos y sin alterar B5.1/B6.1.

**Implementado y verificado:** reclamo `QUEUED`→`RUNNING` en la misma transacción con `skip_locked`; comando con límite `--concurrency` y máximo configurable; recuperación de jobs `RUNNING` huérfanos a `FAILED/WORKER_INTERRUPTED` después de tomar el advisory lock, nunca reencolado automático; servicio Compose `ai_worker` independiente del worker documental. El valor por defecto es uno y el máximo de despliegue predeterminado cuatro. No es un límite monetario. Puerta integral: 7/7, 313.67 s, exit code 0; suite pytest: aprobada en 293.13 s.

**Archivos previstos:** `backend/thesis/services/ai_jobs.py`, `backend/thesis/management/commands/run_ai_worker.py`, `backend/config/settings.py`, `backend/thesis/tests/test_ai_generation.py`, `compose.yaml` y documentos de estado/continuidad. No se espera modelo, migración ni ruta API nueva.

**Evidencia:** pruebas PostgreSQL de reclamo simultáneo único, recuperación sin reintento, semántica `--once` y límites inválidos; suite focalizada 19/19; puerta integral aprobada. Ver [paquete B6.2](./paquete_b6_2_concurrencia_worker.md).

## B6.3/B6.4 — Implementación conjunta en revisión final

B6.3 y B6.4 se implementaron en una única entrega porque ambos reutilizan la cola B6 y materializan las dos capacidades de apoyo acordadas: síntesis revisable de resultados y participación puntual de un apoyo externo. La migración `0037_projectsupportinvitation_supportcontribution_and_more.py` añade cuatro modelos: `AIGenerationBatchSynthesis`, `ProjectSupportInvitation`, `SupportInvitationSource` y `SupportContribution`.

Las pruebas focalizadas B6.3/B6.4 pasaron **20/20** contra PostgreSQL, incluida la instalación limpia de la migración, las transiciones protegidas y el recorrido HTTP de invitación en `backend/thesis/tests/test_ai_batches.py` y `backend/thesis/tests/test_support_invitations.py` contra PostgreSQL en Podman. La puerta integral conjunta pasó 7/7; resultado total 395.34 s, pytest 374.20 s, exit code 0.

Ver [paquete B6 completo](./paquete_b6_completo.md), [B6.3](./paquete_b6_3_sintesis_trazable.md) y [B6.4](./paquete_b6_4_invitaciones_apoyo.md).

## 3. Pendientes posteriores priorizados

**Corte histórico más reciente con puerta integral:** B6 completo y B8 verificados. Después se hicieron cambios de sesión web, configuración Gemini y P20/IEEE que están pendientes de prueba por decisión del usuario; no usar la puerta anterior como evidencia de estos cambios. No reimplementar B6.1–B6.4.

| Prioridad | Bloque | Estado exacto | Qué falta para cerrarlo |
|---|---|---|---|
| Alta | B6.2 concurrencia de workers | Cerrado y verificado | Reclamo atómico, worker con concurrencia configurable, recuperación conservadora y pruebas PostgreSQL. No se afirma límite monetario real: límites de cuota y gasto son externos. |
| Alta | B6.3 síntesis y revisión de lote | Cerrado y verificado | Selección de 2–8 jobs exitosos del mismo lote; snapshot/hash congelado; síntesis estructurada con referencias a task_id seleccionados; decisión auxiliar del titular; worker compartido; no modifica documentos ni acepta outputs fuente. Ver [paquete B6.3](./paquete_b6_3_sintesis_trazable.md). |
| Alta | Sesión de acceso web | Implementación local añadida, pendiente de verificación | `GET /api/v1/auth/session/`, `POST /api/v1/auth/login/` y `POST /api/v1/auth/logout/` usan sesión Django y CSRF. Sin registro público, recuperación, límite de intentos ni soporte entre dominios. Verificar con pruebas y definir gestión de cuentas antes del piloto. |
| Condicional | B5.1 Gemini server-side | Vía opcional, separada de BYOA | El modelo principal acordado es el cliente/agente del usuario conectado a MCP. B5.1 conserva jobs directos del backend con proveedor deshabilitado por defecto; solo activarlo si el equipo decide mantener esa opción y aportar credenciales. Llamada real no verificada. |
| Alta | B1+B2 frontend/round-trip | Pendiente | Implementar o integrar UI web propia: leer/editar árbol canónico, conservar UUIDs de bloque y ocurrencias de citas, enviar con versión/idempotencia, mostrar diff, comentarios y snapshot aprobado. Añadir anclas por ID de bloque sin romper comentarios históricos por offsets. |
| Media | B6.4 invitaciones de apoyo acotadas | Cerrado y verificado con B6 | Cuenta activa existente, aceptación autenticada por token, tarea y fuentes explícitas, vencimiento/revocación, lectura de extractos, PDF grant con SHA, aportes de texto append-only. Sin membresía global, correo, registro de cuenta, upload ni aprobación. Ver [paquete B6.4](./paquete_b6_4_invitaciones_apoyo.md). |
| Media | B4.6 IEEE por tipo documental | Parcial | Contrastar cada tipo de referencia y formato con la guía aprobada del piloto; implementar plantillas y pruebas específicas. La vista/exportación actual es preliminar, con metadatos faltantes visibles. |
| Media | B4.7 coherencia P20/IEEE | Parcial | P20 admite IEEE y conserva APA_7; la plantilla MCP prioriza IEEE. Los recorridos ya publicados conservan sus prompts y requieren una versión nueva para cambiarlos. Falta validar formato IEEE por tipo y decidir cómo elegir estilo por proyecto; no confundir P20 con las citas estructuradas del editor. |
| Media | B4.8 Zotero en vivo | Dependiente de credenciales | Registrar aplicación OAuth Zotero, configurar callback y secretos en un entorno de prueba; validar autorización, lectura, importación no verificada y revocación. La API key Fernet necesita plan seguro de rotación/recuperación antes de producción. |
| Baja/condicional | Campos Zotero activos en DOCX | No implementado / opcional | Solo si el piloto lo requiere: prototipo exportable y validación de actualizar campos en Word/LibreOffice. La exportación estática IEEE no cumple esta capacidad. |
| Media | B7 multiformato | Cerrado y verificado | Upload PDF/DOCX/PPTX/XLSX, original/hash, estados y jobs; `SourceSegment` conserva localizadores; OCRmyPDF `--skip-text` para PDF mixto/escaneado; indexación y recuperación devuelven pasaje con localizador. Puerta integral 7/7, 381.76 s, exit code 0; pytest 362.49 s. Benchmark local: 9 PDF/971 páginas, 4 con páginas sin texto digital; sin ejecución/medición de precisión OCR y sin representatividad declarada. Evaluación multiformato autorizada y rendimiento general siguen abiertos como evaluación empírica. Ver [paquete B7](./paquete_b7_multiformato.md). |
| Cerrado | B8 datos, figuras y exportación | B8.1–B8.4 implementados y verificados | Datasets CSV/XLSX originales, recetas tabulares y figuras PNG versionadas; bloques de documento tipados; manifest y hash en snapshot; DOCX aprobado genera tabla/figura desde versiones exactas. Puerta 7/7, 479.66 s, pytest 457.26 s, exit code 0. No hacer inferencia estadística ni presentar datos sintéticos como evidencia académica. Ver [paquete B8](./paquete_b8_datos_figuras.md). |
| Media | Etapas posteriores a P32 | Pendiente | Protocolo/ética, datos de campo, análisis reproducible cuantitativo/cualitativo/mixto, resultados/discusión/conclusiones ligados a evidencia. P32 actual no calcula estadística desde respuestas originales. |
| Condicional | B9 conectores licenciados | **Evaluación técnica cerrada; implementación API condicionada y no bloqueante** | No se encontraron adaptadores Scopus/WoS ni evidencia de entitlement del proyecto. La búsqueda manual asistida, el registro de ejecución declarada y la importación RIS/BibTeX/CSV ya están implementados. Para abrir código API: confirmación UTP/proveedor del plan y uso por aplicación, autenticación, campos/retención, límites, prueba real autorizada y caso de uso que supere la ruta existente. No usar credenciales personales, automatizar login ni introducir n8n sin caso concreto. Ver [paquete B9](./paquete_b9_conectores_licenciados.md). |
| Transversal | B10 operación local y preparación configurable | **Parcial; no cerrado** | Compose local, backup conjunto DB+media manual y restauración aislada probada; base activa actualizada hasta `0044`. Faltan automatización/frecuencia/retención, copia fuera del disco, configuración segura por entorno y, antes de piloto no local, HTTPS/storage privado/monitoreo/aceptación. Ver [paquete B10](./paquete_b10_operacion_local_y_despliegue.md). |
| Condicional | Gemini real | Dependiente de credencial | Configurar credencial en servidor y ejecutar un caso controlado de generar → revisar → aceptar/rechazar. Tests con adaptador simulado no equivalen a conexión real. |

## 3. Reglas que no se deben perder en los bloques siguientes

1. Tesista/titular y asesor siguen siendo los actores académicos principales. Un asesor puede cubrir funciones temática y metodológica.
2. Experto, bibliotecario y administrador institucional son apoyos/capacidades optativas. No crear roles universales ni dar acceso global a proyectos.
3. Todo job registra actor, proyecto, versión de estado/recorrido/prompt y contexto/hash. Un resultado obsoleto no se acepta sobre el documento actual.
4. Cada agente/tarea tiene salida tipada, entrada permitida, límites y error visible. Los agentes no acceden directamente a ORM ni aprueban, fusionan fuentes o cambian el manuscrito.
5. Scopus/WoS manual permanece disponible sin API. Los datos que el usuario importa no se describen como consultas ejecutadas por TesisMCP.
6. Referencias, metadatos, extracción textual y respaldo semántico son estados separados. IEEE preliminar y OAuth no probada no se anuncian como capacidades completas.
7. Antes de declarar terminado un bloque, actualizar esta lista y [guía de continuidad](./guia_continuidad_backend.md), [plan](./plan_entregas_backend.md), README/API afectados y ejecutar la puerta de `AGENTS.md`.

## 4. Fuentes de navegación

- [Plan de entregas backend](./plan_entregas_backend.md)
- [Guía de continuidad](./guia_continuidad_backend.md)
- [Criterio de backend listo para frontend](./criterio_backend_listo_para_frontend.md)
- [Contrato de permisos](./matriz_permisos_y_cuentas_backend.md)
- [ADR del backend](./registro_decisiones_backend.md)
- [B4 citas/IEEE/Zotero](./implementacion_b4_citas_ieee_zotero.md)
- [B5.1 generación IA](./especificacion_generacion_ia_y_resultados.md)
