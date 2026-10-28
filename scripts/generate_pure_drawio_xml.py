#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import os

OUT_DIR = "V1/docs/diagramas"

def make_drawio_file(diagram_name, cells):
    mxfile = ET.Element("mxfile", host="Electron", modified="2026-10-19T17:00:00.000Z", agent="Antigravity", version="21.6.8", type="device")
    diagram = ET.SubElement(mxfile, "diagram", id="diag_" + diagram_name, name=diagram_name)
    model = ET.SubElement(diagram, "mxGraphModel", dx="1422", dy="800", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1600", pageHeight="1000", math="0", shadow="0")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    for c in cells:
        cell_elem = ET.SubElement(root, "mxCell", id=c["id"], parent=c.get("parent", "1"))
        if "value" in c:
            cell_elem.set("value", c["value"])
        if "style" in c:
            cell_elem.set("style", c["style"])
        if c.get("vertex"):
            cell_elem.set("vertex", "1")
            geom = ET.SubElement(cell_elem, "mxGeometry", x=str(c["x"]), y=str(c["y"]), width=str(c["width"]), height=str(c["height"]))
            geom.set("as", "geometry")
        elif c.get("edge"):
            cell_elem.set("edge", "1")
            if "source" in c:
                cell_elem.set("source", c["source"])
            if "target" in c:
                cell_elem.set("target", c["target"])
            geom = ET.SubElement(cell_elem, "mxGeometry", relative="1")
            geom.set("as", "geometry")

    tree = ET.ElementTree(mxfile)
    ET.indent(tree, space="  ", level=0)
    out_path = os.path.join(OUT_DIR, f"{diagram_name}.drawio")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"Generado: {out_path}")

# 1. ISHIKAWA
ishikawa_cells = [
    {"id": "spine", "edge": True, "style": "endArrow=block;html=1;strokeWidth=4;strokeColor=#000000;endFill=1;", "x": 60, "y": 420, "width": 1000, "height": 0},
    {"id": "head", "vertex": True, "x": 1080, "y": 360, "width": 260, "height": 120, "value": "<b>PROBLEMA PRINCIPAL</b><br/><br/>Desarticulación metodológica y rechazo de proyectos de tesis en revisiones universitarias", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=2;fillColor=#ffffff;fontSize=12;"},
    {"id": "c1", "vertex": True, "x": 80, "y": 90, "width": 240, "height": 130, "value": "<b>TECNOLOGÍA (IA SIN GOBIERNO)</b><br/><br/>• LLMs comerciales sin estado<br/>• Alucinación de fuentes y DOIs<br/>• Cero validación determinista", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=10;fontSize=11;"},
    {"id": "c2", "vertex": True, "x": 580, "y": 90, "width": 240, "height": 130, "value": "<b>METODOLOGÍA (FORMULACIÓN)</b><br/><br/>• Ruptura del hilo conductor<br/>• Inconsistencia taxonómica Bloom<br/>• Operacionalización ambigua", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=10;fontSize=11;"},
    {"id": "c3", "vertex": True, "x": 80, "y": 520, "width": 240, "height": 130, "value": "<b>SUPERVISIÓN (REVISIÓN DOCENTE)</b><br/><br/>• Correcciones dispersas en Word<br/>• Observaciones no ancladas a texto<br/>• Pérdida de historial de versiones", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=10;fontSize=11;"},
    {"id": "c4", "vertex": True, "x": 580, "y": 520, "width": 240, "height": 130, "value": "<b>DATOS Y CONTROL DE VERSIONES</b><br/><br/>• Sobrescritura silenciosa de avances<br/>• Carencia de inmutabilidad en BD<br/>• Aprobación con comentarios abiertos", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=10;fontSize=11;"},
]
make_drawio_file("01_ishikawa_situacion_problematica", ishikawa_cells)

# 2. FODA
foda_cells = [
    {"id": "f", "vertex": True, "x": 40, "y": 40, "width": 560, "height": 340, "value": "<b>FORTALEZAS (F) — Factores Internos (+)</b><br/><br/>• Arquitectura desacoplada: el LLM no escribe directo en la BD.<br/>• Inmutabilidad en PostgreSQL con triggers que protegen revisiones.<br/>• Control de versiones optimista con lock_version.<br/>• Observaciones ancladas a texto exacto (start_cp, end_cp).<br/>• 32 pruebas automatizadas y Definition of Done Gate (7/7 verde).", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=15;fontSize=12;verticalAlign=top;"},
    {"id": "o", "vertex": True, "x": 620, "y": 40, "width": 560, "height": 340, "value": "<b>OPORTUNIDADES (O) — Factores Externos (+)</b><br/><br/>• Adopción creciente del protocolo estándar abierto MCP.<br/>• Integración con APIs académicas libres: OpenAlex, Semantic Scholar y ALICIA.<br/>• Exigencia de rigor metodológico y originalidad en normativas SUNEDU.<br/>• Alta demanda de optimización en horas de supervisión docente.", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=15;fontSize=12;verticalAlign=top;"},
    {"id": "d", "vertex": True, "x": 40, "y": 400, "width": 560, "height": 340, "value": "<b>DEBILIDADES (D) — Factores Internos (-)</b><br/><br/>• Alcance delimitado a primeros 3 capítulos (P01 a P12).<br/>• Interfaz web de usuario aún no implementada (interacción vía MCP/API).<br/>• Exploración científica actual limitada a metadatos.<br/>• Necesidad de configuración de tokens MCP para alternar roles.", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=15;fontSize=12;verticalAlign=top;"},
    {"id": "a", "vertex": True, "x": 620, "y": 400, "width": 560, "height": 340, "value": "<b>AMENAZAS (A) — Factores Externos (-)</b><br/><br/>• Caídas o cambios de esquema en APIs externas de búsqueda.<br/>• Resistencia docente tradicional al uso de IA en formulación de tesis.<br/>• Variaciones de costos en proveedores de tokens LLM de cada usuario.<br/>• Riesgo de complacencia del alumno al aceptar sugerencias sin leer.", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=15;fontSize=12;verticalAlign=top;"},
]
make_drawio_file("02_foda_diagnostico_estrategico", foda_cells)

# 3. CASOS DE USO
usecase_cells = [
    {"id": "actor_t", "vertex": True, "x": 60, "y": 300, "width": 120, "height": 140, "value": "<b>TESISTA</b><br/>(Estudiante Titular)", "style": "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;strokeColor=#000000;strokeWidth=2;fillColor=#ffffff;"},
    {"id": "actor_a", "vertex": True, "x": 1040, "y": 300, "width": 120, "height": 140, "value": "<b>DOCENTE ASESOR</b><br/>(Revisor / Jurado)", "style": "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;strokeColor=#000000;strokeWidth=2;fillColor=#ffffff;"},
    {"id": "bound", "vertex": True, "x": 240, "y": 40, "width": 740, "height": 720, "value": "<b>Sistema TesisMCP (Backend Django + Servidor MCP + PostgreSQL 16)</b>", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=2;fillColor=#ffffff;verticalAlign=top;spacingTop=10;fontStyle=1;"},
    {"id": "uc1", "vertex": True, "x": 280, "y": 90, "width": 300, "height": 55, "value": "CU01: Registrar y Explorar Idea", "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontStyle=1;"},
    {"id": "uc2", "vertex": True, "x": 280, "y": 165, "width": 300, "height": 55, "value": "CU02: Consultar Literatura Científica", "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontStyle=1;"},
    {"id": "uc3", "vertex": True, "x": 280, "y": 240, "width": 300, "height": 55, "value": "CU03: Guardar Paso Metodológico (P01-P12)", "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontStyle=1;"},
    {"id": "uc4", "vertex": True, "x": 280, "y": 315, "width": 300, "height": 55, "value": "CU04: Enviar Capítulo a Revisión (READY)", "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontStyle=1;"},
    {"id": "uc5", "vertex": True, "x": 460, "y": 390, "width": 300, "height": 55, "value": "CU05: Consultar Estado y Matriz", "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontStyle=1;"},
    {"id": "uc6", "vertex": True, "x": 280, "y": 465, "width": 300, "height": 55, "value": "CU06: Asignar Asesor al Proyecto", "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontStyle=1;"},
    {"id": "uc7", "vertex": True, "x": 640, "y": 165, "width": 300, "height": 55, "value": "CU07: Observar Fragmento de Texto", "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontStyle=1;"},
    {"id": "uc8", "vertex": True, "x": 640, "y": 240, "width": 300, "height": 55, "value": "CU08: Resolver Observación (RESOLVED)", "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontStyle=1;"},
    {"id": "uc9", "vertex": True, "x": 640, "y": 315, "width": 300, "height": 55, "value": "CU09: Decidir Capítulo (Aprobar / Reabrir)", "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontStyle=1;"},
    {"id": "uc10", "vertex": True, "x": 460, "y": 550, "width": 300, "height": 55, "value": "CU10: Exportar Borrador Editable (.docx)", "style": "ellipse;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontStyle=1;"},
    # Links
    {"id": "l1", "edge": True, "source": "actor_t", "target": "uc1", "style": "endArrow=none;html=1;strokeColor=#000000;strokeWidth=1.5;"},
    {"id": "l2", "edge": True, "source": "actor_t", "target": "uc2", "style": "endArrow=none;html=1;strokeColor=#000000;strokeWidth=1.5;"},
    {"id": "l3", "edge": True, "source": "actor_t", "target": "uc3", "style": "endArrow=none;html=1;strokeColor=#000000;strokeWidth=1.5;"},
    {"id": "l4", "edge": True, "source": "actor_t", "target": "uc4", "style": "endArrow=none;html=1;strokeColor=#000000;strokeWidth=1.5;"},
    {"id": "l5", "edge": True, "source": "actor_t", "target": "uc5", "style": "endArrow=none;html=1;strokeColor=#000000;strokeWidth=1.5;"},
    {"id": "l6", "edge": True, "source": "actor_a", "target": "uc5", "style": "endArrow=none;html=1;strokeColor=#000000;strokeWidth=1.5;"},
    {"id": "l7", "edge": True, "source": "actor_a", "target": "uc7", "style": "endArrow=none;html=1;strokeColor=#000000;strokeWidth=1.5;"},
    {"id": "l8", "edge": True, "source": "actor_a", "target": "uc8", "style": "endArrow=none;html=1;strokeColor=#000000;strokeWidth=1.5;"},
    {"id": "l9", "edge": True, "source": "actor_a", "target": "uc9", "style": "endArrow=none;html=1;strokeColor=#000000;strokeWidth=1.5;"},
    {"id": "l10", "edge": True, "source": "actor_t", "target": "uc10", "style": "endArrow=none;html=1;strokeColor=#000000;strokeWidth=1.5;"},
    {"id": "l11", "edge": True, "source": "actor_a", "target": "uc10", "style": "endArrow=none;html=1;strokeColor=#000000;strokeWidth=1.5;"},
]
make_drawio_file("03_casos_uso_sistema", usecase_cells)

# 4. DER (17 TABLAS)
der_cells = [
    # Table 1: tesis_usuario
    {"id": "tab1", "vertex": True, "x": 40, "y": 40, "width": 260, "height": 160, "value": "<b>tesis_usuario [Identidad]</b><br/><hr/><u>id</u> (UUID, PK)<br/>email (VARCHAR 254, UNIQUE)<br/>first_name, last_name (VARCHAR)<br/>is_active, is_staff (BOOL)<br/>created_at, updated_at (TIMESTAMP)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab2", "vertex": True, "x": 330, "y": 40, "width": 260, "height": 160, "value": "<b>tesis_token_acceso_mcp [Auth]</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>user_id</i> (UUID, FK)<br/>token_hash (VARCHAR 64, SHA256)<br/>client_name (VARCHAR)<br/>created_at, expires_at (TIMESTAMP)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab3", "vertex": True, "x": 620, "y": 40, "width": 260, "height": 160, "value": "<b>tesis_proyecto [Proyecto]</b><br/><hr/><u>id</u> (UUID, PK)<br/>title (VARCHAR 255)<br/>status (VARCHAR, choices)<br/>created_at, updated_at (TIMESTAMP)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab4", "vertex": True, "x": 910, "y": 40, "width": 260, "height": 160, "value": "<b>tesis_participante_proyecto</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>project_id</i> (UUID, FK)<br/><i>user_id</i> (UUID, FK)<br/>role (VARCHAR: OWNER/ADVISOR)<br/>active (BOOL), joined_at (TIMESTAMP)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},

    {"id": "tab5", "vertex": True, "x": 40, "y": 230, "width": 260, "height": 170, "value": "<b>tesis_perfil_investigacion</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>project_id</i> (UUID, FK 1:1)<br/>problem_statement (TEXT)<br/>ods_code, approach, place (VARCHAR)<br/><b>lock_version</b> (INT, Concurrencia)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab6", "vertex": True, "x": 330, "y": 230, "width": 260, "height": 170, "value": "<b>tesis_progreso_paso [P01-P12]</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>project_id</i> (UUID, FK)<br/>step_code (VARCHAR 3)<br/>status (IN_PROGRESS/COMPLETED)<br/><b>output_json</b> (JSONB, Pydantic)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab7", "vertex": True, "x": 620, "y": 230, "width": 260, "height": 170, "value": "<b>tesis_fila_consistencia [Matriz]</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>project_id</i> (UUID, FK)<br/>row_number (INT, 0=Gen, 1..N)<br/>question, objective, hypothesis (TEXT)<br/>is_general (BOOL)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab8", "vertex": True, "x": 910, "y": 230, "width": 260, "height": 170, "value": "<b>tesis_variable_investigacion</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>project_id</i> (UUID, FK)<br/>name (VARCHAR 255)<br/>variable_type (INDEPENDENT/DEPENDENT)<br/>conceptual_def, operational_def (TEXT)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},

    {"id": "tab9", "vertex": True, "x": 40, "y": 430, "width": 260, "height": 150, "value": "<b>tesis_variable_fila_consistencia</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>variable_id</i> (BIGINT, FK)<br/><i>consistency_row_id</i> (BIGINT, FK)<br/>(Relación N:M variable - fila)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab10", "vertex": True, "x": 330, "y": 430, "width": 260, "height": 150, "value": "<b>tesis_dimension_variable</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>variable_id</i> (BIGINT, FK)<br/>name (VARCHAR 255)<br/>description (TEXT)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab11", "vertex": True, "x": 620, "y": 430, "width": 260, "height": 150, "value": "<b>tesis_indicador [P12]</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>dimension_id</i> (BIGINT, FK)<br/>name (VARCHAR 255)<br/>measurement_scale (NOMINAL/ORDINAL)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab12", "vertex": True, "x": 910, "y": 430, "width": 260, "height": 150, "value": "<b>tesis_capitulo [FSM]</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>project_id</i> (UUID, FK)<br/>number (SMALLINT: 1, 2, 3)<br/>status (DRAFT, READY, APPROVED)<br/><i>approved_revision_id</i> (BIGINT, FK)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},

    {"id": "tab13", "vertex": True, "x": 40, "y": 610, "width": 260, "height": 160, "value": "<b>tesis_revision_capitulo [Inmutable]</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>chapter_id</i> (BIGINT, FK)<br/>revision_no (INT)<br/>step_code (VARCHAR 3)<br/>content_md (TEXT), content_sha256<br/><b>TRIGGER: Bloquea UPDATE/DELETE</b>", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab14", "vertex": True, "x": 330, "y": 610, "width": 260, "height": 160, "value": "<b>tesis_comentario_revision</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>revision_id</i> (BIGINT, FK)<br/><i>author_id</i> (UUID, FK)<br/><b>start_cp, end_cp</b> (INT, Texto exacto)<br/>body (TEXT), status (OPEN/RESOLVED)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab15", "vertex": True, "x": 620, "y": 610, "width": 260, "height": 160, "value": "<b>tesis_evento_revision [Auditoría]</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>chapter_id</i> (BIGINT, FK)<br/><i>revision_id</i> (BIGINT, FK)<br/><i>actor_id</i> (UUID, FK)<br/>action, reason (TEXT)<br/><b>TRIGGER: Bloquea UPDATE/DELETE</b>", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
    {"id": "tab16", "vertex": True, "x": 910, "y": 610, "width": 260, "height": 160, "value": "<b>tesis_usuario_grupo / permiso</b><br/><hr/><u>id</u> (BIGINT, PK)<br/><i>user_id</i> (UUID, FK)<br/><i>group_id / permission_id</i> (INT, FK)<br/>(Tablas intermedias auth Django)", "style": "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;"},
]
make_drawio_file("04_der_modelo_fisico_17_tablas", der_cells)

print("4 archivos .drawio puros generados.")
