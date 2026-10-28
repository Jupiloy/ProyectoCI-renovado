#!/usr/bin/env python3
"""
Generador de los Modelos Conceptual (ER) y Lógico Relacional (3NF) para TesisMCP.
Cumple estrictamente con:
- Blanco y negro puro (monocromo, fondos blancos, bordes 1.5px).
- Sin títulos redundantes integrados en la imagen (la leyenda académica va en Markdown).
- Anclado a la versión reducida (Capítulos 1 al 3, 15 entidades metodológicas).
- Generación dual:
    1. Imágenes PNG de alta resolución (optimizadas para < 500 KB).
    2. Archivos editables .drawio (compatibles con diagrams.net).
"""

import subprocess
import os
import xml.etree.ElementTree as ET
from PIL import Image

OUT_DIR = "V1/docs/diagramas"

# ==============================================================================
# 1. MODELO CONCEPTUAL (ER)
# ==============================================================================
# Entidades puras de negocio y relaciones semánticas (con N:M sin resolver aún)
DOT_CONCEPTUAL_PATH = os.path.join(OUT_DIR, "05_modelo_conceptual_er.dot")
PNG_CONCEPTUAL_PATH = os.path.join(OUT_DIR, "05_modelo_conceptual_er.png")
DRAWIO_CONCEPTUAL_PATH = os.path.join(OUT_DIR, "05_modelo_conceptual_er.drawio")

dot_conceptual = """digraph ModeloConceptual_ER {
    graph [
        bgcolor="white",
        rankdir=LR,
        splines=ortho,
        nodesep=0.6,
        ranksep=0.9,
        pad="0.25"
    ];

    node [
        shape=rectangle,
        style="solid",
        color="#000000",
        fontname="Arial Bold",
        fontsize=10,
        penwidth=1.5,
        fillcolor="#ffffff"
    ];

    edge [
        color="#000000",
        fontname="Arial",
        fontsize=9,
        arrowsize=0.7,
        penwidth=1.2
    ];

    // ENTIDADES CONCEPTUALES (Sustantivos del Dominio)
    Usuario [label="USUARIO\\n(Tesista / Asesor)"];
    TokenAcceso [label="TOKEN ACCESO\\n(Credencial MCP)"];
    Proyecto [label="PROYECTO DE TESIS\\n(Título, Alcance)"];
    Perfil [label="PERFIL INVESTIGACIÓN\\n(Idea, ODS, Problema)"];
    PasoProgreso [label="PASO METODOLÓGICO\\n(P01..P12 / Avance)"];
    FilaConsistencia [label="FILA CONSISTENCIA\\n(Pregunta, Objetivo, Hipótesis)"];
    Variable [label="VARIABLE INVESTIGACIÓN\\n(Independiente / Dependiente)"];
    Dimension [label="DIMENSIÓN\\n(Sub-constructo)"];
    Indicador [label="INDICADOR\\n(Escala, Medición P12)"];
    Capitulo [label="CAPÍTULO\\n(Capítulos 1, 2, 3)"];
    Revision [label="REVISIÓN\\n(Texto Inmutable, SHA-256)"];
    Comentario [label="COMENTARIO OBSERVACIÓN\\n(Fragmento y Feedback Asesor)"];
    EventoAuditoria [label="EVENTO AUDITORÍA\\n(Envío, Aprobación, Rechazo)"];

    // RELACIONES CONCEPTUALES DE ALTO NIVEL
    Usuario -> TokenAcceso [label="autentica\\n1 : N"];
    Usuario -> Proyecto [label="participa en\\nN : M"];
    Proyecto -> Perfil [label="define\\n1 : 1"];
    Proyecto -> PasoProgreso [label="ejecuta\\n1 : N"];
    Proyecto -> FilaConsistencia [label="formula\\n1 : N"];
    Proyecto -> Variable [label="contiene\\n1 : N"];
    Proyecto -> Capitulo [label="estructura\\n1 : N"];

    FilaConsistencia -> Variable [label="vincula\\nN : M"];
    Variable -> Dimension [label="se desglosa en\\n1 : N"];
    Dimension -> Indicador [label="se mide con\\n1 : N"];

    Capitulo -> Revision [label="versiona\\n1 : N"];
    Revision -> Comentario [label="recibe observación\\n1 : N"];
    Capitulo -> EventoAuditoria [label="audita decisión\\n1 : N"];
}
"""

with open(DOT_CONCEPTUAL_PATH, "w", encoding="utf-8") as f:
    f.write(dot_conceptual)

subprocess.run(["dot", "-Tpng", "-Gdpi=200", DOT_CONCEPTUAL_PATH, "-o", PNG_CONCEPTUAL_PATH], check=True)
img_c = Image.open(PNG_CONCEPTUAL_PATH).convert('P', palette=Image.ADAPTIVE, colors=16)
img_c.save(PNG_CONCEPTUAL_PATH, optimize=True)
print(f"Modelo Conceptual PNG: {PNG_CONCEPTUAL_PATH} ({os.path.getsize(PNG_CONCEPTUAL_PATH)//1024} KB)")

# DRAW.IO CONCEPTUAL
CONCEPTUAL_NODES = {
    "Usuario": {"name": "USUARIO\\n(Tesista / Asesor)", "x": 40, "y": 80, "w": 180, "h": 70},
    "TokenAcceso": {"name": "TOKEN ACCESO\\n(Credencial MCP)", "x": 40, "y": 240, "w": 180, "h": 70},
    "Proyecto": {"name": "PROYECTO DE TESIS\\n(Título, Alcance)", "x": 300, "y": 80, "w": 200, "h": 70},
    "Perfil": {"name": "PERFIL INVESTIGACIÓN\\n(Idea, ODS, Problema)", "x": 580, "y": 40, "w": 200, "h": 70},
    "PasoProgreso": {"name": "PASO METODOLÓGICO\\n(P01..P12 / Avance)", "x": 580, "y": 150, "w": 200, "h": 70},
    "Capitulo": {"name": "CAPÍTULO\\n(Capítulos 1, 2, 3)", "x": 300, "y": 270, "w": 200, "h": 70},
    "Revision": {"name": "REVISIÓN\\n(Texto Inmutable, SHA-256)", "x": 580, "y": 270, "w": 200, "h": 70},
    "Comentario": {"name": "COMENTARIO OBSERVACIÓN\\n(Fragmento y Feedback)", "x": 860, "y": 240, "w": 200, "h": 70},
    "EventoAuditoria": {"name": "EVENTO AUDITORÍA\\n(Envío, Aprobación, Rechazo)", "x": 860, "y": 340, "w": 200, "h": 70},
    "FilaConsistencia": {"name": "FILA CONSISTENCIA\\n(Pregunta, Objetivo, Hipótesis)", "x": 300, "y": 450, "w": 220, "h": 70},
    "Variable": {"name": "VARIABLE INVESTIGACIÓN\\n(Independiente / Dependiente)", "x": 580, "y": 450, "w": 220, "h": 70},
    "Dimension": {"name": "DIMENSIÓN\\n(Sub-constructo)", "x": 860, "y": 450, "w": 180, "h": 70},
    "Indicador": {"name": "INDICADOR\\n(Escala, Medición P12)", "x": 1100, "y": 450, "w": 180, "h": 70},
}

CONCEPTUAL_EDGES = [
    ("Usuario", "TokenAcceso", "autentica (1:N)"),
    ("Usuario", "Proyecto", "participa en (N:M)"),
    ("Proyecto", "Perfil", "define (1:1)"),
    ("Proyecto", "PasoProgreso", "ejecuta (1:N)"),
    ("Proyecto", "Capitulo", "estructura (1:N)"),
    ("Capitulo", "Revision", "versiona (1:N)"),
    ("Revision", "Comentario", "recibe observación (1:N)"),
    ("Capitulo", "EventoAuditoria", "audita decisión (1:N)"),
    ("Proyecto", "FilaConsistencia", "formula (1:N)"),
    ("Proyecto", "Variable", "contiene (1:N)"),
    ("FilaConsistencia", "Variable", "vincula (N:M)"),
    ("Variable", "Dimension", "se desglosa en (1:N)"),
    ("Dimension", "Indicador", "se mide con (1:N)"),
]

mxfile_c = ET.Element("mxfile", host="Electron", agent="Antigravity", version="21.6.8", type="device")
diag_c = ET.SubElement(mxfile_c, "diagram", id="diag_conceptual", name="Modelo_Conceptual_ER")
model_c = ET.SubElement(diag_c, "mxGraphModel", dx="1400", dy="900", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1400", pageHeight="900", math="0", shadow="0")
root_c = ET.SubElement(model_c, "root")
ET.SubElement(root_c, "mxCell", id="0")
ET.SubElement(root_c, "mxCell", id="1", parent="0")

for k, n in CONCEPTUAL_NODES.items():
    node = ET.SubElement(root_c, "mxCell", id=k, parent="1", value=n["name"].replace("\\n", "<br/>"), vertex="1")
    node.set("style", "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontStyle=1;fontSize=11;align=center;")
    geom = ET.SubElement(node, "mxGeometry", x=str(n["x"]), y=str(n["y"]), width=str(n["w"]), height=str(n["h"]))
    geom.set("as", "geometry")

for idx, (s, tgt, lbl) in enumerate(CONCEPTUAL_EDGES):
    edge = ET.SubElement(root_c, "mxCell", id=f"e_c_{idx}", parent="1", edge="1", source=s, target=tgt, value=lbl)
    edge.set("style", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;strokeWidth=1.5;endArrow=block;fontSize=10;fontColor=#000000;labelBackgroundColor=#ffffff;")
    geom = ET.SubElement(edge, "mxGeometry", relative="1")
    geom.set("as", "geometry")

tree_c = ET.ElementTree(mxfile_c)
ET.indent(tree_c, space="  ", level=0)
tree_c.write(DRAWIO_CONCEPTUAL_PATH, encoding="utf-8", xml_declaration=True)
print(f"Modelo Conceptual DRAWIO: {DRAWIO_CONCEPTUAL_PATH}")


# ==============================================================================
# 2. MODELO LÓGICO RELACIONAL (3NF)
# ==============================================================================
# 15 Entidades normalizadas, PK/FK explícitas, resolución N:M, tipos abstractos
DOT_LOGICAL_PATH = os.path.join(OUT_DIR, "06_modelo_logico_relacional.dot")
PNG_LOGICAL_PATH = os.path.join(OUT_DIR, "06_modelo_logico_relacional.png")
DRAWIO_LOGICAL_PATH = os.path.join(OUT_DIR, "06_modelo_logico_relacional.drawio")

dot_logical = """digraph ModeloLogico_3NF {
    graph [
        bgcolor="white",
        rankdir=LR,
        splines=ortho,
        nodesep=0.45,
        ranksep=0.75,
        pad="0.25"
    ];

    node [
        shape=plain,
        fontname="Arial",
        fontsize=9
    ];

    edge [
        color="#000000",
        fontname="Arial",
        fontsize=8,
        arrowsize=0.6,
        penwidth=1.0
    ];

    // Columna 1: Identidad y Proyecto Raíz
    USUARIO [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>USUARIO</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>UK</B> correo</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
        <TR><TD ALIGN="LEFT">nombre_visible</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
        <TR><TD ALIGN="LEFT">esta_activo</TD><TD ALIGN="RIGHT">Booleano</TD></TR>
    </TABLE>>];

    PROYECTO [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>PROYECTO</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">UUID</TD></TR>
        <TR><TD ALIGN="LEFT">nombre</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
        <TR><TD ALIGN="LEFT">titulo</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
        <TR><TD ALIGN="LEFT">estado</TD><TD ALIGN="RIGHT">Cadena (Activo/Archivado)</TD></TR>
    </TABLE>>];

    // Columna 2: Entidades Asociativas / Relacionadas Directas
    TOKEN_ACCESO [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>TOKEN_ACCESO</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> usuario_id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>UK</B> hash_token</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
    </TABLE>>];

    PARTICIPANTE_PROYECTO [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>PARTICIPANTE_PROYECTO</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> proyecto_id</TD><TD ALIGN="RIGHT">UUID</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> usuario_id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT">rol</TD><TD ALIGN="RIGHT">Cadena (Tesista/Asesor)</TD></TR>
        <TR><TD ALIGN="LEFT">activo</TD><TD ALIGN="RIGHT">Booleano</TD></TR>
    </TABLE>>];

    PERFIL_INVESTIGACION [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>PERFIL_INVESTIGACION</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK,FK</B> proyecto_id</TD><TD ALIGN="RIGHT">UUID (1:1)</TD></TR>
        <TR><TD ALIGN="LEFT">enfoque</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
        <TR><TD ALIGN="LEFT">tema</TD><TD ALIGN="RIGHT">Texto</TD></TR>
        <TR><TD ALIGN="LEFT">planteamiento_problema</TD><TD ALIGN="RIGHT">Texto</TD></TR>
    </TABLE>>];

    PROGRESO_PASO [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>PROGRESO_PASO [P01-P12]</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> proyecto_id</TD><TD ALIGN="RIGHT">UUID</TD></TR>
        <TR><TD ALIGN="LEFT">codigo_paso</TD><TD ALIGN="RIGHT">Cadena(3)</TD></TR>
        <TR><TD ALIGN="LEFT">estado</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
        <TR><TD ALIGN="LEFT">salida_json</TD><TD ALIGN="RIGHT">Estructura JSON</TD></TR>
    </TABLE>>];

    FILA_CONSISTENCIA [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>FILA_CONSISTENCIA</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> proyecto_id</TD><TD ALIGN="RIGHT">UUID</TD></TR>
        <TR><TD ALIGN="LEFT">orden</TD><TD ALIGN="RIGHT">Entero (0=Gen, 1..N)</TD></TR>
        <TR><TD ALIGN="LEFT">texto_pregunta</TD><TD ALIGN="RIGHT">Texto</TD></TR>
        <TR><TD ALIGN="LEFT">texto_objetivo</TD><TD ALIGN="RIGHT">Texto</TD></TR>
        <TR><TD ALIGN="LEFT">texto_hipotesis</TD><TD ALIGN="RIGHT">Texto</TD></TR>
    </TABLE>>];

    VARIABLE_INVESTIGACION [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>VARIABLE_INVESTIGACION</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> proyecto_id</TD><TD ALIGN="RIGHT">UUID</TD></TR>
        <TR><TD ALIGN="LEFT">nombre</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
        <TR><TD ALIGN="LEFT">rol</TD><TD ALIGN="RIGHT">Cadena (Indep/Dep)</TD></TR>
    </TABLE>>];

    CAPITULO [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>CAPITULO</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> proyecto_id</TD><TD ALIGN="RIGHT">UUID</TD></TR>
        <TR><TD ALIGN="LEFT">numero</TD><TD ALIGN="RIGHT">Entero (1..3)</TD></TR>
        <TR><TD ALIGN="LEFT">estado</TD><TD ALIGN="RIGHT">Cadena (Borrador/Revisión/Aprobado)</TD></TR>
    </TABLE>>];

    // Columna 3: Sub-entidades y Desglose
    VARIABLE_FILA_CONSISTENCIA [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>VARIABLE_FILA_CONSISTENCIA</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> fila_consistencia_id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> variable_id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
    </TABLE>>];

    DIMENSION_VARIABLE [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>DIMENSION_VARIABLE</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> variable_id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT">nombre</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
    </TABLE>>];

    REVISION_CAPITULO [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>REVISION_CAPITULO</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> capitulo_id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> creado_por_id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT">numero_revision</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT">contenido_sha256</TD><TD ALIGN="RIGHT">Cadena(64)</TD></TR>
    </TABLE>>];

    EVENTO_REVISION [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>EVENTO_REVISION</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> capitulo_id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT">accion</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
    </TABLE>>];

    // Columna 4: Detalles Finales
    INDICADOR [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>INDICADOR [P12]</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> dimension_id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT">nombre</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
        <TR><TD ALIGN="LEFT">escala_medicion</TD><TD ALIGN="RIGHT">Cadena</TD></TR>
    </TABLE>>];

    COMENTARIO_REVISION [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
        <TR><TD COLSPAN="2" BORDER="1"><B>COMENTARIO_REVISION</B></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B> id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> revision_id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B> autor_id</TD><TD ALIGN="RIGHT">Entero</TD></TR>
        <TR><TD ALIGN="LEFT">texto_seleccionado</TD><TD ALIGN="RIGHT">Texto</TD></TR>
        <TR><TD ALIGN="LEFT">estado</TD><TD ALIGN="RIGHT">Cadena (Abierto/Resuelto)</TD></TR>
    </TABLE>>];

    // Conexiones relacionales (1:N, 1:1)
    USUARIO -> TOKEN_ACCESO [label="1:N"];
    USUARIO -> PARTICIPANTE_PROYECTO [label="1:N"];

    PROYECTO -> PARTICIPANTE_PROYECTO [label="1:N"];
    PROYECTO -> PERFIL_INVESTIGACION [label="1:1"];
    PROYECTO -> PROGRESO_PASO [label="1:N"];
    PROYECTO -> FILA_CONSISTENCIA [label="1:N"];
    PROYECTO -> VARIABLE_INVESTIGACION [label="1:N"];
    PROYECTO -> CAPITULO [label="1:N"];

    FILA_CONSISTENCIA -> VARIABLE_FILA_CONSISTENCIA [label="1:N"];
    VARIABLE_INVESTIGACION -> VARIABLE_FILA_CONSISTENCIA [label="1:N"];
    VARIABLE_INVESTIGACION -> DIMENSION_VARIABLE [label="1:N"];
    DIMENSION_VARIABLE -> INDICADOR [label="1:N"];

    CAPITULO -> REVISION_CAPITULO [label="1:N"];
    REVISION_CAPITULO -> COMENTARIO_REVISION [label="1:N"];
    CAPITULO -> EVENTO_REVISION [label="1:N"];
}
"""

with open(DOT_LOGICAL_PATH, "w", encoding="utf-8") as f:
    f.write(dot_logical)

subprocess.run(["dot", "-Tpng", "-Gdpi=180", DOT_LOGICAL_PATH, "-o", PNG_LOGICAL_PATH], check=True)
img_l = Image.open(PNG_LOGICAL_PATH).convert('P', palette=Image.ADAPTIVE, colors=16)
img_l.save(PNG_LOGICAL_PATH, optimize=True)
print(f"Modelo Lógico PNG: {PNG_LOGICAL_PATH} ({os.path.getsize(PNG_LOGICAL_PATH)//1024} KB)")

# DRAW.IO LÓGICO
LOGICAL_NODES = {
    "USUARIO": {"title": "USUARIO", "x": 40, "y": 60, "w": 220, "h": 120,
                "fields": ["+ id: Entero [PK]", "+ correo: Cadena [UK]", "+ nombre_visible: Cadena", "+ esta_activo: Booleano"]},
    "PROYECTO": {"title": "PROYECTO", "x": 40, "y": 240, "w": 220, "h": 120,
                 "fields": ["+ id: UUID [PK]", "+ nombre: Cadena", "+ titulo: Cadena", "+ estado: Cadena"]},
    "TOKEN_ACCESO": {"title": "TOKEN_ACCESO", "x": 320, "y": 40, "w": 230, "h": 100,
                    "fields": ["+ id: Entero [PK]", "# usuario_id: Entero [FK]", "+ hash_token: Cadena [UK]"]},
    "PARTICIPANTE_PROYECTO": {"title": "PARTICIPANTE_PROYECTO", "x": 320, "y": 160, "w": 230, "h": 120,
                             "fields": ["+ id: Entero [PK]", "# proyecto_id: UUID [FK]", "# usuario_id: Entero [FK]", "+ rol: Cadena", "+ activo: Booleano"]},
    "PERFIL_INVESTIGACION": {"title": "PERFIL_INVESTIGACION", "x": 320, "y": 300, "w": 230, "h": 110,
                            "fields": ["+# proyecto_id: UUID [PK, FK 1:1]", "+ enfoque: Cadena", "+ tema: Texto", "+ planteamiento_problema: Texto"]},
    "PROGRESO_PASO": {"title": "PROGRESO_PASO [P01-P12]", "x": 320, "y": 430, "w": 230, "h": 110,
                      "fields": ["+ id: Entero [PK]", "# proyecto_id: UUID [FK]", "+ codigo_paso: Cadena(3)", "+ estado: Cadena", "+ salida_json: JSON"]},
    "FILA_CONSISTENCIA": {"title": "FILA_CONSISTENCIA", "x": 320, "y": 560, "w": 230, "h": 120,
                          "fields": ["+ id: Entero [PK]", "# proyecto_id: UUID [FK]", "+ orden: Entero", "+ texto_pregunta: Texto", "+ texto_objetivo: Texto"]},
    "VARIABLE_INVESTIGACION": {"title": "VARIABLE_INVESTIGACION", "x": 320, "y": 700, "w": 230, "h": 110,
                               "fields": ["+ id: Entero [PK]", "# proyecto_id: UUID [FK]", "+ nombre: Cadena", "+ rol: Cadena (Indep/Dep)"]},
    "CAPITULO": {"title": "CAPITULO [FSM]", "x": 320, "y": 830, "w": 230, "h": 110,
                 "fields": ["+ id: Entero [PK]", "# proyecto_id: UUID [FK]", "+ numero: Entero (1..3)", "+ estado: Cadena"]},

    "VARIABLE_FILA_CONSISTENCIA": {"title": "VARIABLE_FILA_CONSISTENCIA", "x": 620, "y": 620, "w": 230, "h": 100,
                                  "fields": ["+ id: Entero [PK]", "# fila_consistencia_id: Entero [FK]", "# variable_id: Entero [FK]"]},
    "DIMENSION_VARIABLE": {"title": "DIMENSION_VARIABLE", "x": 620, "y": 740, "w": 230, "h": 100,
                          "fields": ["+ id: Entero [PK]", "# variable_id: Entero [FK]", "+ nombre: Cadena"]},
    "INDICADOR": {"title": "INDICADOR [P12]", "x": 910, "y": 740, "w": 220, "h": 110,
                  "fields": ["+ id: Entero [PK]", "# dimension_id: Entero [FK]", "+ nombre: Cadena", "+ escala_medicion: Cadena"]},

    "REVISION_CAPITULO": {"title": "REVISION_CAPITULO [Inmutable]", "x": 620, "y": 860, "w": 230, "h": 120,
                          "fields": ["+ id: Entero [PK]", "# capitulo_id: Entero [FK]", "# creado_por_id: Entero [FK]", "+ numero_revision: Entero", "+ contenido_sha256: Cadena(64)"]},
    "COMENTARIO_REVISION": {"title": "COMENTARIO_REVISION", "x": 910, "y": 860, "w": 220, "h": 120,
                           "fields": ["+ id: Entero [PK]", "# revision_id: Entero [FK]", "# autor_id: Entero [FK]", "+ texto_seleccionado: Texto", "+ estado: Cadena"]},
    "EVENTO_REVISION": {"title": "EVENTO_REVISION [Auditoría]", "x": 620, "y": 1000, "w": 230, "h": 100,
                        "fields": ["+ id: Entero [PK]", "# capitulo_id: Entero [FK]", "+ accion: Cadena"]},
}

LOGICAL_EDGES = [
    ("USUARIO", "TOKEN_ACCESO", "1:N"),
    ("USUARIO", "PARTICIPANTE_PROYECTO", "1:N"),
    ("PROYECTO", "PARTICIPANTE_PROYECTO", "1:N"),
    ("PROYECTO", "PERFIL_INVESTIGACION", "1:1"),
    ("PROYECTO", "PROGRESO_PASO", "1:N"),
    ("PROYECTO", "FILA_CONSISTENCIA", "1:N"),
    ("PROYECTO", "VARIABLE_INVESTIGACION", "1:N"),
    ("PROYECTO", "CAPITULO", "1:N"),
    ("FILA_CONSISTENCIA", "VARIABLE_FILA_CONSISTENCIA", "1:N"),
    ("VARIABLE_INVESTIGACION", "VARIABLE_FILA_CONSISTENCIA", "1:N"),
    ("VARIABLE_INVESTIGACION", "DIMENSION_VARIABLE", "1:N"),
    ("DIMENSION_VARIABLE", "INDICADOR", "1:N"),
    ("CAPITULO", "REVISION_CAPITULO", "1:N"),
    ("REVISION_CAPITULO", "COMENTARIO_REVISION", "1:N"),
    ("CAPITULO", "EVENTO_REVISION", "1:N"),
]

mxfile_l = ET.Element("mxfile", host="Electron", agent="Antigravity", version="21.6.8", type="device")
diag_l = ET.SubElement(mxfile_l, "diagram", id="diag_logico", name="Modelo_Logico_Relacional")
model_l = ET.SubElement(diag_l, "mxGraphModel", dx="1400", dy="1100", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1300", pageHeight="1200", math="0", shadow="0")
root_l = ET.SubElement(model_l, "root")
ET.SubElement(root_l, "mxCell", id="0")
ET.SubElement(root_l, "mxCell", id="1", parent="0")

for k, t in LOGICAL_NODES.items():
    content = f"<b>{t['title']}</b><br/><hr/>" + "<br/>".join(t["fields"])
    node = ET.SubElement(root_l, "mxCell", id=k, parent="1", value=content, vertex="1")
    node.set("style", "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=6;fontSize=10;verticalAlign=top;")
    geom = ET.SubElement(node, "mxGeometry", x=str(t["x"]), y=str(t["y"]), width=str(t["w"]), height=str(t["h"]))
    geom.set("as", "geometry")

for idx, (s, tgt, card) in enumerate(LOGICAL_EDGES):
    edge = ET.SubElement(root_l, "mxCell", id=f"e_l_{idx}", parent="1", edge="1", source=s, target=tgt, value=card)
    edge.set("style", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;strokeWidth=1.5;endArrow=ERmany;startArrow=ERmandOne;fontSize=9;fontColor=#000000;labelBackgroundColor=#ffffff;")
    geom = ET.SubElement(edge, "mxGeometry", relative="1")
    geom.set("as", "geometry")

tree_l = ET.ElementTree(mxfile_l)
ET.indent(tree_l, space="  ", level=0)
tree_l.write(DRAWIO_LOGICAL_PATH, encoding="utf-8", xml_declaration=True)
print(f"Modelo Lógico DRAWIO: {DRAWIO_LOGICAL_PATH}")
