#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET

OUT_DIR = "V1/docs/diagramas"
os.makedirs(OUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. ISHIKAWA (CAUSA-EFECTO) - SIN TITULO ARRIBA, PURO B/N
# -----------------------------------------------------------------------------
ishikawa_html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: Arial, Helvetica, sans-serif;
    background: #ffffff;
    color: #000000;
    padding: 20px;
    width: 1750px;
    height: 900px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .fishbone-container {
    position: relative;
    width: 100%;
    height: 100%;
    border: 1.5px solid #000000;
    padding: 20px;
    background: #ffffff;
  }
  .spine {
    position: absolute;
    top: 430px;
    left: 40px;
    width: 1300px;
    height: 3.5px;
    background: #000000;
  }
  .head-box {
    position: absolute;
    top: 365px;
    left: 1340px;
    width: 350px;
    height: 130px;
    border: 2px solid #000000;
    background: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 15px;
  }
  .head-title {
    font-size: 13px;
    font-weight: bold;
    text-transform: uppercase;
    color: #333333;
    margin-bottom: 6px;
  }
  .head-desc {
    font-size: 14.5px;
    font-weight: bold;
    line-height: 1.35;
  }

  .category-box {
    position: absolute;
    width: 300px;
    border: 1.5px solid #000000;
    background: #ffffff;
    padding: 14px;
  }
  .cat-title {
    font-size: 13px;
    font-weight: bold;
    text-transform: uppercase;
    border-bottom: 1px solid #000000;
    padding-bottom: 5px;
    margin-bottom: 8px;
    text-align: center;
  }
  ul {
    padding-left: 18px;
    font-size: 12.5px;
    line-height: 1.45;
  }
  li { margin-bottom: 6px; }

  .rib-top-1 { top: 30px; left: 80px; }
  .rib-top-2 { top: 30px; left: 720px; }
  .rib-bot-1 { top: 500px; left: 80px; }
  .rib-bot-2 { top: 500px; left: 720px; }

  svg.connectors {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }
</style>
</head>
<body>

<div class="fishbone-container">
  <svg class="connectors">
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#000000"/>
      </marker>
    </defs>
    <line x1="1300" y1="431" x2="1340" y2="431" stroke="#000000" stroke-width="3.5" marker-end="url(#arrow)" />
    <line x1="380" y1="210" x2="520" y2="429" stroke="#000000" stroke-width="2" marker-end="url(#arrow)" />
    <line x1="1020" y1="210" x2="1160" y2="429" stroke="#000000" stroke-width="2" marker-end="url(#arrow)" />
    <line x1="380" y1="640" x2="520" y2="433" stroke="#000000" stroke-width="2" marker-end="url(#arrow)" />
    <line x1="1020" y1="640" x2="1160" y2="433" stroke="#000000" stroke-width="2" marker-end="url(#arrow)" />
  </svg>

  <div class="spine"></div>

  <div class="category-box rib-top-1">
    <div class="cat-title">Tecnología (IA sin Gobierno)</div>
    <ul>
      <li><strong>LLMs comerciales sin estado:</strong> Respuestas volátiles y sin memoria entre sesiones.</li>
      <li><strong>Alucinación de fuentes:</strong> Invención de autores, DOIs y páginas inexistentes.</li>
      <li><strong>Cero validación determinista:</strong> Ausencia de contratos de datos que verifiquen salidas.</li>
    </ul>
  </div>

  <div class="category-box rib-top-2">
    <div class="cat-title">Metodología (Formulación)</div>
    <ul>
      <li><strong>Ruptura del hilo conductor:</strong> Desarticulación entre problemas, objetivos e hipótesis.</li>
      <li><strong>Inconsistencia taxonómica:</strong> Uso de verbos no jerárquicos o no alineados a Bloom.</li>
      <li><strong>Operacionalización ambigua:</strong> Dimensiones e indicadores sin escala de medición definida.</li>
    </ul>
  </div>

  <div class="category-box rib-bot-1">
    <div class="cat-title">Supervisión (Revisión Docente)</div>
    <ul>
      <li><strong>Correcciones dispersas:</strong> Múltiples archivos Word enviados por WhatsApp y correo.</li>
      <li><strong>Observaciones huérfanas:</strong> Comentarios no anclados a fragmentos de texto exactos.</li>
      <li><strong>Pérdida de historial:</strong> Dificultad para saber qué versión previa fue aprobada.</li>
    </ul>
  </div>

  <div class="category-box rib-bot-2">
    <div class="cat-title">Datos y Control de Versiones</div>
    <ul>
      <li><strong>Sobrescritura silenciosa:</strong> Cambios concurrentes no detectados sin control optimista.</li>
      <li><strong>Carencia de inmutabilidad:</strong> Posibilidad de alterar registros y eventos históricos.</li>
      <li><strong>Aprobación ciega:</strong> Cierre de capítulos a pesar de mantener observaciones sin resolver.</li>
    </ul>
  </div>

  <div class="head-box">
    <div class="head-title">Problema Principal</div>
    <div class="head-desc">Desarticulación metodológica y rechazo de proyectos de tesis en revisiones universitarias</div>
  </div>
</div>

</body>
</html>
"""
with open("/tmp/01_ishikawa_pure.html", "w", encoding="utf-8") as f:
    f.write(ishikawa_html)

# -----------------------------------------------------------------------------
# 2. MATRIZ FODA (2x2) - SIN TITULO ARRIBA, PURO B/N
# -----------------------------------------------------------------------------
foda_html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: Arial, Helvetica, sans-serif;
    background: #ffffff;
    color: #000000;
    padding: 20px;
    width: 1750px;
    height: 900px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .foda-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    border: 2px solid #000000;
    width: 100%;
    height: 100%;
  }
  .foda-quadrant {
    border: 1px solid #000000;
    padding: 24px;
    display: flex;
    flex-direction: column;
    background: #ffffff;
  }
  .quadrant-title {
    font-size: 15px;
    font-weight: bold;
    text-transform: uppercase;
    border-bottom: 1.5px solid #000000;
    padding-bottom: 8px;
    margin-bottom: 14px;
    letter-spacing: 0.5px;
    display: flex;
    justify-content: space-between;
  }
  .quadrant-tag {
    font-size: 11.5px;
    border: 1px solid #000000;
    padding: 2px 7px;
    font-weight: normal;
  }
  ul {
    padding-left: 20px;
    font-size: 13.5px;
    line-height: 1.5;
  }
  li {
    margin-bottom: 11px;
  }
  li strong {
    color: #000000;
  }
</style>
</head>
<body>

<div class="foda-grid">
  <div class="foda-quadrant">
    <div class="quadrant-title">
      <span>Fortalezas (F)</span>
      <span class="quadrant-tag">Factores Internos (+)</span>
    </div>
    <ul>
      <li><strong>Arquitectura desacoplada determinista:</strong> El LLM no escribe directamente en la BD; toda persistencia pasa por contratos Pydantic 2 y servicios Django.</li>
      <li><strong>Inmutabilidad física en PostgreSQL:</strong> Triggers en PL/pgSQL que bloquean modificaciones o borrados accidentales en revisiones y eventos.</li>
      <li><strong>Control de versiones optimista:</strong> Mecanismo lock_version que detecta colisiones y evita sobrescritura de avances concurrentes.</li>
      <li><strong>Supervisión precisa:</strong> Comentarios de asesor anclados por posición exacta de caracteres (start_cp, end_cp) con bloqueo de aprobación si existen observaciones abiertas.</li>
      <li><strong>Batería de pruebas automatizadas:</strong> 32 pruebas unitarias y de integración respaldadas por Definition of Done Gate (7/7 en verde).</li>
    </ul>
  </div>

  <div class="foda-quadrant">
    <div class="quadrant-title">
      <span>Oportunidades (O)</span>
      <span class="quadrant-tag">Factores Externos (+)</span>
    </div>
    <ul>
      <li><strong>Adopción del estándar abierto MCP:</strong> Interoperabilidad con múltiples clientes de IA (Antigravity, Claude Desktop, Cursor) sin dependencias propietarias.</li>
      <li><strong>Integración con fuentes científicas abiertas:</strong> Consultas automatizadas a OpenAlex, Semantic Scholar y repositorio nacional ALICIA (Concytec).</li>
      <li><strong>Exigencia institucional de rigor metodológico:</strong> Normativas SUNEDU y UTP que demandan consistencia matemática entre preguntas, objetivos e hipótesis.</li>
      <li><strong>Demanda de supervisión docente eficiente:</strong> Necesidad urgente de reducir horas invertidas en comparar archivos Word duplicados.</li>
    </ul>
  </div>

  <div class="foda-quadrant">
    <div class="quadrant-title">
      <span>Debilidades (D)</span>
      <span class="quadrant-tag">Factores Internos (-)</span>
    </div>
    <ul>
      <li><strong>Alcance delimitado en Semana 10:</strong> Catálogo operativo circunscrito a Capítulos 1 al 3 (P01 a P12); Capítulos 4 al 7 en etapa de diseño.</li>
      <li><strong>Falta de interfaz gráfica para el estudiante:</strong> Actualmente la interacción requiere un cliente MCP sobre stdio, Django Admin o llamadas a la API REST.</li>
      <li><strong>Búsqueda científica limitada a metadatos:</strong> El corte actual no incluye aún OCR ni segmentación de PDFs con comprobación física de página.</li>
      <li><strong>Curva técnica inicial:</strong> Requiere configuración de tokens locales MCP para alternar entre roles de tesista y asesor.</li>
    </ul>
  </div>

  <div class="foda-quadrant">
    <div class="quadrant-title">
      <span>Amenazas (A)</span>
      <span class="quadrant-tag">Factores Externos (-)</span>
    </div>
    <ul>
      <li><strong>Inestabilidad o cuotas de APIs externas:</strong> Caídas o cambios de esquema en proveedores como Semantic Scholar u OpenAlex.</li>
      <li><strong>Resistencia docente tradicional:</strong> Desconfianza hacia el uso de inteligencia artificial en la formulación de tesis por temor a plagio.</li>
      <li><strong>Costos de inferencia de modelos LLM:</strong> Variaciones en precios de tokens de proveedores externos asumidos por cada usuario.</li>
      <li><strong>Riesgo de uso complaciente del alumno:</strong> Tendencia a aceptar sugerencias sintéticas del modelo sin lectura crítica del contenido.</li>
    </ul>
  </div>
</div>

</body>
</html>
"""
with open("/tmp/02_foda_pure.html", "w", encoding="utf-8") as f:
    f.write(foda_html)

# -----------------------------------------------------------------------------
# 3. CASOS DE USO UML - SIN TITULO ARRIBA, PURO B/N
# -----------------------------------------------------------------------------
casos_uso_html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: Arial, Helvetica, sans-serif;
    background: #ffffff;
    color: #000000;
    padding: 20px;
    width: 1750px;
    height: 900px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .uml-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1.5px solid #000000;
    width: 100%;
    height: 100%;
    padding: 25px 40px;
    position: relative;
    background: #ffffff;
  }
  .actor-box {
    width: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 10px;
  }
  .actor-icon {
    width: 65px;
    height: 105px;
  }
  .actor-name {
    font-size: 15px;
    font-weight: bold;
    text-transform: uppercase;
    border: 1.5px solid #000000;
    padding: 5px 12px;
    background: #ffffff;
  }
  .actor-desc {
    font-size: 12px;
    color: #333333;
  }

  .system-boundary {
    width: 1150px;
    height: 810px;
    border: 2px solid #000000;
    position: relative;
    padding: 20px;
    background: #ffffff;
  }
  .system-title {
    position: absolute;
    top: 12px;
    left: 20px;
    font-size: 13.5px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .usecases-grid {
    margin-top: 35px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    height: 730px;
  }

  .usecase {
    border: 1.5px solid #000000;
    border-radius: 50px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 10px 16px;
    background: #ffffff;
  }
  .uc-title {
    font-size: 13.5px;
    font-weight: bold;
  }
  .uc-code {
    font-size: 11.5px;
    color: #444444;
    margin-top: 3px;
  }

  svg.uml-lines {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }
</style>
</head>
<body>

<div class="uml-container">
  <svg class="uml-lines">
    <line x1="240" y1="450" x2="330" y2="120" stroke="#000000" stroke-width="1.5"/>
    <line x1="240" y1="450" x2="330" y2="210" stroke="#000000" stroke-width="1.5"/>
    <line x1="240" y1="450" x2="330" y2="300" stroke="#000000" stroke-width="1.5"/>
    <line x1="240" y1="450" x2="330" y2="390" stroke="#000000" stroke-width="1.5"/>
    <line x1="240" y1="450" x2="330" y2="480" stroke="#000000" stroke-width="1.5"/>
    <line x1="240" y1="450" x2="330" y2="570" stroke="#000000" stroke-width="1.5"/>
    <line x1="240" y1="450" x2="330" y2="745" stroke="#000000" stroke-width="1.5"/>

    <line x1="1510" y1="450" x2="880" y2="480" stroke="#000000" stroke-width="1.5"/>
    <line x1="1510" y1="450" x2="900" y2="210" stroke="#000000" stroke-width="1.5"/>
    <line x1="1510" y1="450" x2="900" y2="300" stroke="#000000" stroke-width="1.5"/>
    <line x1="1510" y1="450" x2="900" y2="390" stroke="#000000" stroke-width="1.5"/>
    <line x1="1510" y1="450" x2="900" y2="745" stroke="#000000" stroke-width="1.5"/>
  </svg>

  <div class="actor-box">
    <svg class="actor-icon" viewBox="0 0 100 150">
      <circle cx="50" cy="30" r="20" stroke="#000000" stroke-width="3" fill="none"/>
      <line x1="50" y1="50" x2="50" y2="100" stroke="#000000" stroke-width="3"/>
      <line x1="20" y1="70" x2="80" y2="70" stroke="#000000" stroke-width="3"/>
      <line x1="50" y1="100" x2="20" y2="145" stroke="#000000" stroke-width="3"/>
      <line x1="50" y1="100" x2="80" y2="145" stroke="#000000" stroke-width="3"/>
    </svg>
    <div class="actor-name">Tesista</div>
    <div class="actor-desc">Estudiante titular con token MCP de redacción y avance</div>
  </div>

  <div class="system-boundary">
    <div class="system-title">Sistema TesisMCP (Backend Django + Servidor MCP + PostgreSQL 16)</div>

    <div class="usecases-grid">
      <div class="usecase">
        <div class="uc-title">CU01: Registrar y Explorar Idea</div>
        <div class="uc-code">MCP: registrar_idea, explorar_idea</div>
      </div>
      <div class="usecase">
        <div class="uc-title">CU02: Consultar Literatura Científica</div>
        <div class="uc-code">MCP: buscar_semantic_scholar, buscar_alicia</div>
      </div>
      <div class="usecase">
        <div class="uc-title">CU03: Guardar Paso Metodológico (P01-P12)</div>
        <div class="uc-code">MCP: guardar_paso (Control lock_version)</div>
      </div>
      <div class="usecase">
        <div class="uc-title">CU04: Enviar Capítulo a Revisión (READY)</div>
        <div class="uc-code">MCP: enviar_capitulo (Requiere 100% pasos)</div>
      </div>
      <div class="usecase">
        <div class="uc-title">CU05: Consultar Estado y Matriz</div>
        <div class="uc-code">MCP: obtener_estado, consultar_capitulo</div>
      </div>
      <div class="usecase">
        <div class="uc-title">CU06: Asignar Asesor al Proyecto</div>
        <div class="uc-code">MCP: asignar_asesor</div>
      </div>
      <div class="usecase">
        <div class="uc-title">CU07: Observar Fragmento de Texto</div>
        <div class="uc-code">MCP: observar_fragmento (start_cp, end_cp)</div>
      </div>
      <div class="usecase">
        <div class="uc-title">CU08: Resolver Observación (RESOLVED)</div>
        <div class="uc-code">MCP: resolver_observacion</div>
      </div>
      <div class="usecase">
        <div class="uc-title">CU09: Decidir Capítulo (Aprobar / Reabrir)</div>
        <div class="uc-code">MCP: decidir_capitulo (Sin comentarios abiertos)</div>
      </div>
      <div class="usecase">
        <div class="uc-title">CU10: Exportar Borrador Editable (.docx)</div>
        <div class="uc-code">API: /api/v1/projects/{id}/export/docx</div>
      </div>
    </div>
  </div>

  <div class="actor-box">
    <svg class="actor-icon" viewBox="0 0 100 150">
      <circle cx="50" cy="30" r="20" stroke="#000000" stroke-width="3" fill="none"/>
      <line x1="50" y1="50" x2="50" y2="100" stroke="#000000" stroke-width="3"/>
      <line x1="20" y1="70" x2="80" y2="70" stroke="#000000" stroke-width="3"/>
      <line x1="50" y1="100" x2="20" y2="145" stroke="#000000" stroke-width="3"/>
      <line x1="50" y1="100" x2="80" y2="145" stroke="#000000" stroke-width="3"/>
    </svg>
    <div class="actor-name">Docente Asesor</div>
    <div class="actor-desc">Profesor revisor con permisos de observación y aprobación</div>
  </div>
</div>

</body>
</html>
"""
with open("/tmp/03_casos_uso_pure.html", "w", encoding="utf-8") as f:
    f.write(casos_uso_html)

# -----------------------------------------------------------------------------
# 4. DER FÍSICO (17 TABLAS) - SIN TITULO ARRIBA, PURO B/N
# -----------------------------------------------------------------------------
der_html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: Arial, Helvetica, sans-serif;
    background: #ffffff;
    color: #000000;
    padding: 20px;
    width: 2000px;
    height: 1550px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .er-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(4, 350px);
    gap: 12px;
    border: 1.5px solid #000000;
    padding: 12px;
    width: 100%;
    height: 100%;
    background: #ffffff;
  }
  .er-table {
    border: 1.5px solid #000000;
    background: #ffffff;
    display: flex;
    flex-direction: column;
    font-size: 12px;
  }
  .table-header {
    background: #ffffff;
    border-bottom: 1.5px solid #000000;
    padding: 6px 10px;
    font-weight: bold;
    font-size: 13px;
    display: flex;
    justify-content: space-between;
  }
  .table-module {
    font-size: 10px;
    color: #444444;
    text-transform: uppercase;
  }
  .table-body {
    padding: 8px 10px;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 3px;
    line-height: 1.35;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 11.5px;
  }
  .pk { font-weight: bold; text-decoration: underline; }
  .fk { font-style: italic; color: #222222; }
  .table-rel {
    border-top: 1px dashed #777777;
    padding-top: 4px;
    margin-top: auto;
    font-size: 11px;
    font-family: Arial, sans-serif;
    color: #444444;
  }
</style>
</head>
<body>

<div class="er-grid">
  <!-- 1. tesis_usuario -->
  <div class="er-table">
    <div class="table-header"><span>tesis_usuario</span><span class="table-module">Identidad</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (UUID, PK)</div>
      <div>email (VARCHAR, UNIQUE)</div>
      <div>first_name, last_name (VARCHAR)</div>
      <div>is_active, is_staff (BOOL)</div>
      <div>created_at, updated_at (TIMESTAMP)</div>
      <div class="table-rel">1:N con tokens, proyectos y comentarios</div>
    </div>
  </div>

  <!-- 2. tesis_token_acceso_mcp -->
  <div class="er-table">
    <div class="table-header"><span>tesis_token_acceso_mcp</span><span class="table-module">Identidad</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">user_id</span> (UUID, FK -> tesis_usuario)</div>
      <div>token_hash (VARCHAR 64, SHA-256)</div>
      <div>client_name (VARCHAR)</div>
      <div>created_at, expires_at (TIMESTAMP)</div>
      <div class="table-rel">Tokens stdio con hash sin texto plano</div>
    </div>
  </div>

  <!-- 3. tesis_usuario_grupo & permiso -->
  <div class="er-table">
    <div class="table-header"><span>tesis_usuario_grupo / permiso</span><span class="table-module">Identidad</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">user_id</span> (UUID, FK -> tesis_usuario)</div>
      <div><span class="fk">group_id / permission_id</span> (INT, FK)</div>
      <div class="table-rel">Tablas intermedias de auth Django</div>
    </div>
  </div>

  <!-- 4. tesis_proyecto -->
  <div class="er-table">
    <div class="table-header"><span>tesis_proyecto</span><span class="table-module">Proyecto</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (UUID, PK)</div>
      <div>title (VARCHAR 255)</div>
      <div>status (VARCHAR, choices: DRAFT..)</div>
      <div>created_at, updated_at (TIMESTAMP)</div>
      <div class="table-rel">Contenedor central de la investigación</div>
    </div>
  </div>

  <!-- 5. tesis_participante_proyecto -->
  <div class="er-table">
    <div class="table-header"><span>tesis_participante_proyecto</span><span class="table-module">Proyecto</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">project_id</span> (UUID, FK -> tesis_proyecto)</div>
      <div><span class="fk">user_id</span> (UUID, FK -> tesis_usuario)</div>
      <div>role (VARCHAR: OWNER / ADVISOR)</div>
      <div>active (BOOL), joined_at (TIMESTAMP)</div>
      <div class="table-rel">Control de permisos por rol en el backend</div>
    </div>
  </div>

  <!-- 6. tesis_perfil_investigacion -->
  <div class="er-table">
    <div class="table-header"><span>tesis_perfil_investigacion</span><span class="table-module">Metodología</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">project_id</span> (UUID, FK 1:1 -> tesis_proyecto)</div>
      <div>problem_statement (TEXT)</div>
      <div>ods_code, approach, unit_of_analysis</div>
      <div>place, period_text (VARCHAR)</div>
      <div><strong>lock_version</strong> (INT, Optimistic Lock)</div>
      <div class="table-rel">Persistencia de estado metodológico central</div>
    </div>
  </div>

  <!-- 7. tesis_progreso_paso -->
  <div class="er-table">
    <div class="table-header"><span>tesis_progreso_paso</span><span class="table-module">Metodología</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">project_id</span> (UUID, FK -> tesis_proyecto)</div>
      <div>step_code (VARCHAR 3, P01..P12)</div>
      <div>status (VARCHAR, IN_PROGRESS/COMPLETED)</div>
      <div><strong>output_json</strong> (JSONB, Contrato Pydantic)</div>
      <div>completed_at (TIMESTAMP)</div>
      <div class="table-rel">Salida inmutable de pasos P01 a P12</div>
    </div>
  </div>

  <!-- 8. tesis_fila_consistencia -->
  <div class="er-table">
    <div class="table-header"><span>tesis_fila_consistencia</span><span class="table-module">Consistencia</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">project_id</span> (UUID, FK -> tesis_proyecto)</div>
      <div>row_number (INT, 0=General, 1..N=Espec)</div>
      <div>question, objective, hypothesis (TEXT)</div>
      <div>is_general (BOOL)</div>
      <div class="table-rel">Alineamiento de preguntas, obj e hipótesis</div>
    </div>
  </div>

  <!-- 9. tesis_variable_investigacion -->
  <div class="er-table">
    <div class="table-header"><span>tesis_variable_investigacion</span><span class="table-module">Operacionalización</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">project_id</span> (UUID, FK -> tesis_proyecto)</div>
      <div>name (VARCHAR 255)</div>
      <div>variable_type (INDEPENDENT / DEPENDENT)</div>
      <div>conceptual_definition (TEXT)</div>
      <div>operational_definition (TEXT)</div>
      <div class="table-rel">Variables identificadas en P04 y P11</div>
    </div>
  </div>

  <!-- 10. tesis_variable_fila_consistencia -->
  <div class="er-table">
    <div class="table-header"><span>tesis_variable_fila_consistencia</span><span class="table-module">Operacionalización</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">variable_id</span> (BIGINT, FK -> tesis_variable)</div>
      <div><span class="fk">consistency_row_id</span> (BIGINT, FK -> tesis_fila)</div>
      <div class="table-rel">N:M entre variables y filas de matriz</div>
    </div>
  </div>

  <!-- 11. tesis_dimension_variable -->
  <div class="er-table">
    <div class="table-header"><span>tesis_dimension_variable</span><span class="table-module">Operacionalización</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">variable_id</span> (BIGINT, FK -> tesis_variable)</div>
      <div>name (VARCHAR 255)</div>
      <div>description (TEXT)</div>
      <div class="table-rel">Desglose de cada variable en dimensiones</div>
    </div>
  </div>

  <!-- 12. tesis_indicador -->
  <div class="er-table">
    <div class="table-header"><span>tesis_indicador</span><span class="table-module">Operacionalización</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">dimension_id</span> (BIGINT, FK -> tesis_dimension)</div>
      <div>name (VARCHAR 255)</div>
      <div>measurement_scale (NOMINAL/ORDINAL..)</div>
      <div class="table-rel">Indicadores finales de P12 con escala</div>
    </div>
  </div>

  <!-- 13. tesis_capitulo -->
  <div class="er-table">
    <div class="table-header"><span>tesis_capitulo</span><span class="table-module">Revisión FSM</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">project_id</span> (UUID, FK -> tesis_proyecto)</div>
      <div>number (SMALLINT: 1, 2, 3)</div>
      <div>status (VARCHAR, FSM: DRAFT, READY..)</div>
      <div><span class="fk">approved_revision_id</span> (BIGINT, FK)</div>
      <div>approved_at (TIMESTAMP)</div>
      <div class="table-rel">Ciclo de vida del capítulo académico</div>
    </div>
  </div>

  <!-- 14. tesis_revision_capitulo -->
  <div class="er-table">
    <div class="table-header"><span>tesis_revision_capitulo</span><span class="table-module">Revisión FSM</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">chapter_id</span> (BIGINT, FK -> tesis_capitulo)</div>
      <div>revision_no (INT)</div>
      <div>step_code (VARCHAR 3)</div>
      <div>content_md (TEXT, Copia completa)</div>
      <div>content_sha256 (VARCHAR 64)</div>
      <div><strong>TRIGGER: Bloquea UPDATE/DELETE</strong></div>
      <div class="table-rel">Historial inmutable de versiones</div>
    </div>
  </div>

  <!-- 15. tesis_comentario_revision -->
  <div class="er-table">
    <div class="table-header"><span>tesis_comentario_revision</span><span class="table-module">Supervisión</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">revision_id</span> (BIGINT, FK -> tesis_revision)</div>
      <div><span class="fk">author_id</span> (UUID, FK -> tesis_usuario)</div>
      <div><strong>start_cp, end_cp</strong> (INT, Rango texto)</div>
      <div>selected_text (TEXT)</div>
      <div>body (TEXT), status (OPEN / RESOLVED)</div>
      <div class="table-rel">Observación anclada por posición exacta</div>
    </div>
  </div>

  <!-- 16. tesis_evento_revision -->
  <div class="er-table">
    <div class="table-header"><span>tesis_evento_revision</span><span class="table-module">Supervisión</span></div>
    <div class="table-body">
      <div><span class="pk">id</span> (BIGINT, PK)</div>
      <div><span class="fk">chapter_id</span> (BIGINT, FK -> tesis_capitulo)</div>
      <div><span class="fk">revision_id</span> (BIGINT, FK -> tesis_revision)</div>
      <div><span class="fk">actor_id</span> (UUID, FK -> tesis_usuario)</div>
      <div>action (SUBMIT, REQUEST_CHANGES, APPROVE)</div>
      <div>reason (TEXT), created_at (TIMESTAMP)</div>
      <div><strong>TRIGGER: Bloquea UPDATE/DELETE</strong></div>
      <div class="table-rel">Bitácora auditable de decisiones docentes</div>
    </div>
  </div>
</div>

</body>
</html>
"""
with open("/tmp/04_der_pure.html", "w", encoding="utf-8") as f:
    f.write(der_html)

print("Plantillas HTML puras generadas con éxito.")
