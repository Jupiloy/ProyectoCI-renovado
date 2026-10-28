#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import os

OUT_DIR = "V1/docs/diagramas"

# Logical positions for the 17 tables (2400 x 1600 canvas)
# Group 1: Identidad (Top-Left)
# Group 2: Proyecto (Top-Center)
# Group 3: Metodologia y Consistencia (Mid-Left)
# Group 4: Variables y Operacionalizacion (Bottom-Left & Bottom-Center)
# Group 5: Capitulos, Revisiones y Comentarios (Right side)

TABLES = {
    # Identidad
    "usr": {"name": "tesis_usuario", "title": "tesis_usuario [Identidad]", "x": 60, "y": 80, "w": 250, "h": 160,
            "fields": ["<u>id</u> (UUID, PK)", "email (VARCHAR 254, UK)", "first_name, last_name", "is_active, is_staff (BOOL)", "created_at, updated_at"]},
    "tok": {"name": "tesis_token_acceso_mcp", "title": "tesis_token_acceso_mcp", "x": 60, "y": 300, "w": 250, "h": 140,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>user_id</i> (UUID, FK)", "token_hash (VARCHAR 64)", "client_name (VARCHAR)", "expires_at (TIMESTAMP)"]},
    "grp": {"name": "tesis_usuario_grupo", "title": "tesis_usuario_grupo", "x": 60, "y": 500, "w": 250, "h": 110,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>user_id</i> (UUID, FK)", "<i>group_id</i> (INT, FK)"]},
    "prm": {"name": "tesis_usuario_permiso", "title": "tesis_usuario_permiso", "x": 60, "y": 660, "w": 250, "h": 110,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>user_id</i> (UUID, FK)", "<i>permission_id</i> (INT, FK)"]},

    # Proyecto
    "pro": {"name": "tesis_proyecto", "title": "tesis_proyecto [Proyecto]", "x": 480, "y": 80, "w": 270, "h": 140,
            "fields": ["<u>id</u> (UUID, PK)", "title (VARCHAR 255)", "status (VARCHAR)", "created_at, updated_at"]},
    "par": {"name": "tesis_participante_proyecto", "title": "tesis_participante_proyecto", "x": 480, "y": 280, "w": 270, "h": 160,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>project_id</i> (UUID, FK)", "<i>user_id</i> (UUID, FK)", "role (OWNER / ADVISOR)", "active (BOOL), joined_at"]},
    "prf": {"name": "tesis_perfil_investigacion", "title": "tesis_perfil_investigacion", "x": 480, "y": 500, "w": 270, "h": 160,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>project_id</i> (UUID, FK 1:1)", "problem_statement (TEXT)", "ods_code, approach, place", "<b>lock_version</b> (INT)"]},
    "pas": {"name": "tesis_progreso_paso", "title": "tesis_progreso_paso [P01-P12]", "x": 480, "y": 720, "w": 270, "h": 150,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>project_id</i> (UUID, FK)", "step_code (VARCHAR 3)", "status (IN_PROGRESS/COMPLETED)", "<b>output_json</b> (JSONB)"]},

    # Matriz y Operacionalizacion
    "fil": {"name": "tesis_fila_consistencia", "title": "tesis_fila_consistencia [Matriz]", "x": 480, "y": 940, "w": 270, "h": 160,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>project_id</i> (UUID, FK)", "row_number (INT, 0=Gen, 1..N)", "question, objective (TEXT)", "hypothesis (TEXT), is_general"]},
    "vrf": {"name": "tesis_variable_fila_consistencia", "title": "tesis_variable_fila_consistencia", "x": 480, "y": 1180, "w": 270, "h": 120,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>variable_id</i> (BIGINT, FK)", "<i>consistency_row_id</i> (BIGINT, FK)"]},

    "var": {"name": "tesis_variable_investigacion", "title": "tesis_variable_investigacion", "x": 60, "y": 940, "w": 280, "h": 170,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>project_id</i> (UUID, FK)", "name (VARCHAR 255)", "variable_type (IND/DEP)", "conceptual_def, operational_def"]},
    "dim": {"name": "tesis_dimension_variable", "title": "tesis_dimension_variable", "x": 60, "y": 1180, "w": 280, "h": 130,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>variable_id</i> (BIGINT, FK)", "name (VARCHAR 255)", "description (TEXT)"]},
    "ind": {"name": "tesis_indicador", "title": "tesis_indicador [P12]", "x": 60, "y": 1380, "w": 280, "h": 140,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>dimension_id</i> (BIGINT, FK)", "name (VARCHAR 255)", "measurement_scale (NOMINAL..)"]},

    # Revision y Supervision
    "cap": {"name": "tesis_capitulo", "title": "tesis_capitulo [FSM]", "x": 930, "y": 80, "w": 280, "h": 160,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>project_id</i> (UUID, FK)", "number (SMALLINT: 1, 2, 3)", "status (DRAFT, READY, APPROVED)", "<i>approved_revision_id</i> (BIGINT, FK)"]},
    "rev": {"name": "tesis_revision_capitulo", "title": "tesis_revision_capitulo [Inmutable]", "x": 930, "y": 320, "w": 280, "h": 180,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>chapter_id</i> (BIGINT, FK)", "<i>created_by_id</i> (UUID, FK)", "revision_no (INT), step_code", "content_md (TEXT), sha256", "<b>TRIGGER: Bloquea UPDATE/DELETE</b>"]},
    "com": {"name": "tesis_comentario_revision", "title": "tesis_comentario_revision", "x": 930, "y": 600, "w": 280, "h": 170,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>revision_id</i> (BIGINT, FK)", "<i>author_id</i> (UUID, FK)", "<b>start_cp, end_cp</b> (INT, Rango)", "selected_text, body (TEXT)", "status (OPEN / RESOLVED)"]},
    "eve": {"name": "tesis_evento_revision", "title": "tesis_evento_revision [Auditoría]", "x": 930, "y": 870, "w": 280, "h": 170,
            "fields": ["<u>id</u> (BIGINT, PK)", "<i>chapter_id</i> (BIGINT, FK)", "<i>revision_id</i> (BIGINT, FK)", "<i>actor_id</i> (UUID, FK)", "action (SUBMIT/REQUEST/APPROVE)", "reason (TEXT), created_at"]},
}

RELATIONS = [
    # (source_table, target_table, label, cardinality)
    ("usr", "tok", "autentica", "1:N"),
    ("usr", "grp", "pertenece", "1:N"),
    ("usr", "prm", "posee", "1:N"),
    ("usr", "par", "participa", "1:N"),
    ("pro", "par", "integra", "1:N"),
    ("pro", "prf", "define", "1:1"),
    ("pro", "pas", "registra", "1:N"),
    ("pro", "fil", "formula", "1:N"),
    ("pro", "var", "contiene", "1:N"),
    ("pro", "cap", "estructura", "1:N"),
    ("var", "vrf", "asocia", "1:N"),
    ("fil", "vrf", "vincula", "1:N"),
    ("var", "dim", "desglosa", "1:N"),
    ("dim", "ind", "mide", "1:N"),
    ("cap", "rev", "versiona", "1:N"),
    ("rev", "com", "ancla", "1:N"),
    ("usr", "rev", "redacta", "1:N"),
    ("usr", "com", "comenta", "1:N"),
    ("cap", "eve", "audita", "1:N"),
    ("usr", "eve", "ejecuta", "1:N"),
]

# Generate .drawio
mxfile = ET.Element("mxfile", host="Electron", modified="2026-10-19T17:00:00.000Z", agent="Antigravity", version="21.6.8", type="device")
diagram = ET.SubElement(mxfile, "diagram", id="diag_der", name="DER_Fisico_17_Tablas")
model = ET.SubElement(diagram, "mxGraphModel", dx="1600", dy="1200", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1600", pageHeight="1800", math="0", shadow="0")
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")

# Add table nodes
for k, t in TABLES.items():
    content = f"<b>{t['title']}</b><br/><hr/>" + "<br/>".join(t["fields"])
    node = ET.SubElement(root, "mxCell", id=k, parent="1", value=content, vertex="1")
    node.set("style", "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=8;fontSize=11;verticalAlign=top;")
    geom = ET.SubElement(node, "mxGeometry", x=str(t["x"]), y=str(t["y"]), width=str(t["w"]), height=str(t["h"]))
    geom.set("as", "geometry")

# Add relationship edges
for idx, (s, tgt, lbl, card) in enumerate(RELATIONS):
    edge_id = f"e_{s}_{tgt}_{idx}"
    edge = ET.SubElement(root, "mxCell", id=edge_id, parent="1", edge="1", source=s, target=tgt, value=f"{card}")
    edge.set("style", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;strokeWidth=1.5;endArrow=ERmany;startArrow=ERmandOne;fontSize=10;fontColor=#000000;labelBackgroundColor=#ffffff;")
    geom = ET.SubElement(edge, "mxGeometry", relative="1")
    geom.set("as", "geometry")

tree = ET.ElementTree(mxfile)
ET.indent(tree, space="  ", level=0)
drawio_path = os.path.join(OUT_DIR, "04_der_modelo_fisico_17_tablas.drawio")
tree.write(drawio_path, encoding="utf-8", xml_declaration=True)
print(f"Generado con éxito con 20 conexiones: {drawio_path}")

# Now generate HTML with SVG connection lines for crisp PNG rendering!
html_lines = []
for k, t in TABLES.items():
    fields_html = "".join([f"<div>{f}</div>" for f in t["fields"]])
    html_lines.append(f"""
    <div class="er-box" style="left: {t['x']}px; top: {t['y']}px; width: {t['w']}px; height: {t['h']}px;">
      <div class="er-header">{t['title']}</div>
      <div class="er-body">{fields_html}</div>
    </div>
    """)

# Compute connector center-points
svg_paths = []
for s, tgt, lbl, card in RELATIONS:
    ts = TABLES[s]
    tt = TABLES[tgt]
    # Connect right of ts to left of tt, or bottom to top
    if ts['x'] < tt['x']:
        x1 = ts['x'] + ts['w']
        y1 = ts['y'] + ts['h'] // 2
        x2 = tt['x']
        y2 = tt['y'] + tt['h'] // 2
        midx = (x1 + x2) // 2
        path = f"M {x1} {y1} L {midx} {y1} L {midx} {y2} L {x2} {y2}"
        lx, ly = midx, (y1 + y2) // 2
    else:
        x1 = ts['x'] + ts['w'] // 2
        y1 = ts['y'] + ts['h']
        x2 = tt['x'] + tt['w'] // 2
        y2 = tt['y']
        midy = (y1 + y2) // 2
        path = f"M {x1} {y1} L {x1} {midy} L {x2} {midy} L {x2} {y2}"
        lx, ly = (x1 + x2) // 2, midy

    svg_paths.append(f"""
    <path d="{path}" fill="none" stroke="#000000" stroke-width="1.5" marker-end="url(#crowfoot)"/>
    <rect x="{lx-18}" y="{ly-10}" width="36" height="20" fill="#ffffff" stroke="#666666" stroke-width="0.8"/>
    <text x="{lx}" y="{ly+4}" font-size="10" font-family="Arial" font-weight="bold" text-anchor="middle">{card}</text>
    """)

der_full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: Arial, Helvetica, sans-serif;
    background: #ffffff;
    color: #000000;
    width: 1300px;
    height: 1600px;
    position: relative;
    padding: 20px;
  }}
  .er-box {{
    position: absolute;
    border: 1.5px solid #000000;
    background: #ffffff;
    display: flex;
    flex-direction: column;
    z-index: 10;
  }}
  .er-header {{
    background: #ffffff;
    border-bottom: 1.5px solid #000000;
    padding: 6px 10px;
    font-weight: bold;
    font-size: 12px;
    text-transform: uppercase;
  }}
  .er-body {{
    padding: 8px 10px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 11px;
    line-height: 1.35;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }}
  .er-body u {{ font-weight: bold; }}
  .er-body i {{ font-style: italic; color: #333333; }}
  svg.wires {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
    pointer-events: none;
  }}
</style>
</head>
<body>

<svg class="wires">
  <defs>
    <marker id="crowfoot" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 6 L 0 12 M 10 0 L 10 12" fill="none" stroke="#000000" stroke-width="1.5"/>
    </marker>
  </defs>
  {''.join(svg_paths)}
</svg>

{''.join(html_lines)}

</body>
</html>
"""

with open("/tmp/04_der_connected.html", "w", encoding="utf-8") as f:
    f.write(der_full_html)

print("HTML conectado generado.")
