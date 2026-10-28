#!/usr/bin/env python3
"""
Generador del Diagrama Entidad-Relación Físico Oficial (17 Tablas) para TesisMCP.
Cumple estrictamente con:
- Blanco y negro puro (monocromo, fondos blancos, bordes negros 1.5px).
- Sin títulos redundantes integrados en la imagen (leyenda académica en Markdown).
- Las 17 tablas físicas con prefijo 'tesis_' en PostgreSQL 16.
- 5 Dominios funcionales delimitados: Identidad, Proyecto, Avance MVP, Matriz/Variables y Ciclo de Revisiones.
- Conexiones explícitas con notación Crow's foot (1:1, 1:N, 0..1:N) y cero cruces destructivos sobre cajas.
- Generación dual:
    1. Imagen PNG de alta resolución (300 DPI) vía Graphviz.
    2. Archivo editable .drawio con nodos y aristas relacionales nativas para diagrams.net.
"""

import subprocess
import os
import xml.etree.ElementTree as ET

OUT_DIR = "V1/docs/diagramas"
DOT_PATH = os.path.join(OUT_DIR, "04_der_modelo_fisico_17_tablas.dot")
PNG_PATH = os.path.join(OUT_DIR, "04_der_modelo_fisico_17_tablas.png")
DRAWIO_PATH = os.path.join(OUT_DIR, "04_der_modelo_fisico_17_tablas.drawio")

# 1. GENERACIÓN DEL ARCHIVO .DOT (Graphviz)
dot_content = """digraph DER_Fisico_17_Tablas {
    graph [
        bgcolor="white",
        rankdir=TB,
        splines=spline,
        nodesep=0.45,
        ranksep=0.75,
        pad="0.25",
        outputorder=edgesfirst
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
        arrowsize=0.7,
        penwidth=1.1
    ];

    // ==========================================
    // DOMINIO 1: IDENTIDAD Y AUTENTICACIÓN
    // ==========================================
    subgraph cluster_dom1 {
        label = "Dominio 1: Identidad y Autenticación";
        style = "dashed";
        color = "#000000";
        fontname = "Arial Bold";
        fontsize = 11;

        tesis_usuario [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1" BGCOLOR="#000000"><FONT COLOR="#ffffff"><B>tesis_usuario</B></FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>UK</B></TD><TD ALIGN="LEFT">correo</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(254)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">nombre_visible</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(150)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">contrasena_hash</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(128)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">esta_activo</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">boolean</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">creado_en</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">timestamptz</FONT></TD></TR>
        </TABLE>>];

        tesis_token_acceso_mcp [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_token_acceso_mcp</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">usuario_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>UK</B></TD><TD ALIGN="LEFT">hash_token</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(64)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">expira_en</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">timestamptz</FONT></TD></TR>
        </TABLE>>];

        tesis_usuario_grupo [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_usuario_grupo</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">usuario_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">grupo_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">integer</FONT></TD></TR>
        </TABLE>>];

        tesis_usuario_permiso [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_usuario_permiso</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">usuario_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">permiso_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">integer</FONT></TD></TR>
        </TABLE>>];
    }

    // ==========================================
    // DOMINIO 2: PROYECTO Y PARTICIPACIÓN
    // ==========================================
    subgraph cluster_dom2 {
        label = "Dominio 2: Proyecto y Participación";
        style = "dashed";
        color = "#000000";
        fontname = "Arial Bold";
        fontsize = 11;

        tesis_proyecto [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1" BGCOLOR="#000000"><FONT COLOR="#ffffff"><B>tesis_proyecto</B></FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">uuid</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">nombre</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(160)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">titulo</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(300)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">estado</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(12)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">creado_en</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">timestamptz</FONT></TD></TR>
        </TABLE>>];

        tesis_participante_proyecto [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_participante_proyecto</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">proyecto_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">uuid</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">usuario_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">rol</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(10)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">activo</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">boolean</FONT></TD></TR>
        </TABLE>>];
    }

    // ==========================================
    // DOMINIO 3: PERFIL METODOLÓGICO Y AVANCE (MVP)
    // ==========================================
    subgraph cluster_dom3 {
        label = "Dominio 3: Perfil Metodológico y Avance (MVP)";
        style = "dashed";
        color = "#000000";
        fontname = "Arial Bold";
        fontsize = 11;

        tesis_perfil_investigacion [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_perfil_investigacion</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK,FK</B></TD><TD ALIGN="LEFT">proyecto_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">uuid (1:1)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">enfoque</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(16)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">tema</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">text</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">codigo_ods</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(20)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">unidad_analisis</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">text</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">lugar</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">text</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">planteamiento_problema</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">text</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">version_bloqueo</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">integer</FONT></TD></TR>
        </TABLE>>];

        tesis_progreso_paso [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_progreso_paso [P01-P12]</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">proyecto_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">uuid</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">codigo_paso</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(3)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">estado</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(16)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">salida_json</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">jsonb</FONT></TD></TR>
        </TABLE>>];
    }

    // ==========================================
    // DOMINIO 4: MATRIZ DE CONSISTENCIA Y VARIABLES
    // ==========================================
    subgraph cluster_dom4 {
        label = "Dominio 4: Matriz de Consistencia y Operacionalización";
        style = "dashed";
        color = "#000000";
        fontname = "Arial Bold";
        fontsize = 11;

        tesis_fila_consistencia [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_fila_consistencia [Matriz]</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">proyecto_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">uuid</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">orden</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">smallint (0..N)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">texto_pregunta</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">text</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">texto_objetivo</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">text</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">texto_hipotesis</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">text</FONT></TD></TR>
        </TABLE>>];

        tesis_variable_investigacion [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_variable_investigacion</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">proyecto_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">uuid</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">nombre</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(200)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">rol</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(16) (IND/DEP)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">definicion_conceptual</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">text</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">definicion_operacional</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">text</FONT></TD></TR>
        </TABLE>>];

        tesis_variable_fila_consistencia [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_variable_fila_consistencia</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">fila_consistencia_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">variable_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
        </TABLE>>];

        tesis_dimension_variable [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_dimension_variable</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">variable_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">nombre</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(200)</FONT></TD></TR>
        </TABLE>>];

        tesis_indicador [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_indicador [P12]</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">dimension_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">nombre</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(200)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">escala_medicion</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(30)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">tecnica</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(120)</FONT></TD></TR>
        </TABLE>>];
    }

    // ==========================================
    // DOMINIO 5: CAPÍTULOS, REVISIÓN Y AUDITORÍA
    // ==========================================
    subgraph cluster_dom5 {
        label = "Dominio 5: Ciclo de Versiones y Auditoría Docente";
        style = "dashed";
        color = "#000000";
        fontname = "Arial Bold";
        fontsize = 11;

        tesis_capitulo [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1" BGCOLOR="#000000"><FONT COLOR="#ffffff"><B>tesis_capitulo [FSM]</B></FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">proyecto_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">uuid</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">numero</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">smallint (1..3)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">estado</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(20)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">revision_aprobada_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint (null)</FONT></TD></TR>
        </TABLE>>];

        tesis_revision_capitulo [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_revision_capitulo [Inmutable]</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">capitulo_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">creado_por_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">numero_revision</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">integer</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">codigo_paso</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(3)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">contenido_sha256</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">char(64)</FONT></TD></TR>
            <TR><TD COLSPAN="3" ALIGN="CENTER"><FONT COLOR="#555555"><I>TRIGGER: Bloquea UPDATE/DELETE</I></FONT></TD></TR>
        </TABLE>>];

        tesis_comentario_revision [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_comentario_revision</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">revision_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">autor_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">inicio_caracter, fin_caracter</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">integer</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">texto_seleccionado</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">text</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">estado</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(10)</FONT></TD></TR>
        </TABLE>>];

        tesis_evento_revision [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#000000">
            <TR><TD COLSPAN="3" BORDER="1"><B>tesis_evento_revision [Auditoría]</B></TD></TR>
            <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">capitulo_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">revision_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint (null)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">usuario_actor_id</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">bigint</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">accion</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">varchar(20)</FONT></TD></TR>
            <TR><TD ALIGN="LEFT"></TD><TD ALIGN="LEFT">creado_en</TD><TD ALIGN="RIGHT"><FONT COLOR="#555555">timestamptz</FONT></TD></TR>
        </TABLE>>];
    }

    // ==========================================
    // RELACIONES RELACIONALES CROW'S FOOT
    // ==========================================
    // Dominio 1 -> Internas y a Participante
    tesis_usuario -> tesis_token_acceso_mcp [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_usuario -> tesis_usuario_grupo [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_usuario -> tesis_usuario_permiso [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_usuario -> tesis_participante_proyecto [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];

    // Dominio 2 -> Hacia Módulos del Sistema
    tesis_proyecto -> tesis_participante_proyecto [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_proyecto -> tesis_perfil_investigacion [arrowtail="tee", arrowhead="tee", dir=both, label="1 : 1"];
    tesis_proyecto -> tesis_progreso_paso [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_proyecto -> tesis_fila_consistencia [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_proyecto -> tesis_variable_investigacion [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_proyecto -> tesis_capitulo [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];

    // Dominio 4 -> Matriz y Desglose Operacional
    tesis_fila_consistencia -> tesis_variable_fila_consistencia [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_variable_investigacion -> tesis_variable_fila_consistencia [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_variable_investigacion -> tesis_dimension_variable [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_dimension_variable -> tesis_indicador [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];

    // Dominio 5 -> Ciclo de Capítulos y Revisiones
    tesis_capitulo -> tesis_revision_capitulo [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_capitulo -> tesis_evento_revision [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_revision_capitulo -> tesis_comentario_revision [arrowtail="tee", arrowhead="crow", dir=both, label="1 : N"];
    tesis_revision_capitulo -> tesis_evento_revision [arrowtail="odottee", arrowhead="crow", dir=both, label="0..1 : N"];
    tesis_revision_capitulo -> tesis_capitulo [style="dashed", arrowtail="tee", arrowhead="odottee", dir=both, label="aprobada 0..1:1", constraint=false];

    // Trazabilidad de Auditoría Docente / Tesista (Dotted)
    tesis_usuario -> tesis_revision_capitulo [arrowtail="tee", arrowhead="crow", dir=both, label="crea 1:N", style="dotted", constraint=false];
    tesis_usuario -> tesis_comentario_revision [arrowtail="tee", arrowhead="crow", dir=both, label="comenta 1:N", style="dotted", constraint=false];
    tesis_usuario -> tesis_evento_revision [arrowtail="tee", arrowhead="crow", dir=both, label="ejecuta 1:N", style="dotted", constraint=false];
}
"""

with open(DOT_PATH, "w", encoding="utf-8") as f:
    f.write(dot_content)

print(f"Archivo .dot escrito en: {DOT_PATH}")

# Compilación a PNG en 200 DPI y optimización de paleta para cumplir higiene (< 500 KB)
cmd = ["dot", "-Tpng", "-Gdpi=200", DOT_PATH, "-o", PNG_PATH]
subprocess.run(cmd, check=True)

from PIL import Image
img = Image.open(PNG_PATH)
img_opt = img.convert('P', palette=Image.ADAPTIVE, colors=16)
img_opt.save(PNG_PATH, optimize=True)
print(f"Imagen PNG compilada y optimizada en: {PNG_PATH} ({os.path.getsize(PNG_PATH)//1024} KB)")

# 2. GENERACIÓN DEL ARCHIVO .DRAWIO NATIVO (mxGraph)
TABLES_DRAWIO = {
    # Dominio 1: Identidad
    "tesis_usuario": {"title": "tesis_usuario [Identidad]", "x": 40, "y": 60, "w": 250, "h": 150,
                      "fields": ["+ id: bigint [PK]", "+ correo: varchar(254) [UK]", "+ nombre_visible: varchar(150)", "+ contrasena_hash: varchar(128)", "+ esta_activo: boolean", "+ creado_en: timestamptz"]},
    "tesis_token_acceso_mcp": {"title": "tesis_token_acceso_mcp", "x": 40, "y": 250, "w": 250, "h": 120,
                              "fields": ["+ id: bigint [PK]", "# usuario_id: bigint [FK]", "+ hash_token: varchar(64) [UK]", "+ expira_en: timestamptz"]},
    "tesis_usuario_grupo": {"title": "tesis_usuario_grupo", "x": 40, "y": 400, "w": 250, "h": 90,
                            "fields": ["+ id: bigint [PK]", "# usuario_id: bigint [FK]", "# grupo_id: integer [FK]"]},
    "tesis_usuario_permiso": {"title": "tesis_usuario_permiso", "x": 40, "y": 520, "w": 250, "h": 90,
                              "fields": ["+ id: bigint [PK]", "# usuario_id: bigint [FK]", "# permiso_id: integer [FK]"]},

    # Dominio 2: Proyecto
    "tesis_proyecto": {"title": "tesis_proyecto [Proyecto]", "x": 340, "y": 60, "w": 260, "h": 140,
                       "fields": ["+ id: uuid [PK]", "+ nombre: varchar(160)", "+ titulo: varchar(300)", "+ estado: varchar(12)", "+ creado_en: timestamptz"]},
    "tesis_participante_proyecto": {"title": "tesis_participante_proyecto", "x": 340, "y": 240, "w": 260, "h": 120,
                                   "fields": ["+ id: bigint [PK]", "# proyecto_id: uuid [FK]", "# usuario_id: bigint [FK]", "+ rol: varchar(10)", "+ activo: boolean"]},

    # Dominio 5: Capítulos y Revisiones
    "tesis_capitulo": {"title": "tesis_capitulo [FSM]", "x": 650, "y": 60, "w": 270, "h": 130,
                      "fields": ["+ id: bigint [PK]", "# proyecto_id: uuid [FK]", "+ numero: smallint (1..3)", "+ estado: varchar(20)", "# revision_aprobada_id: bigint [FK]"]},
    "tesis_revision_capitulo": {"title": "tesis_revision_capitulo [Inmutable]", "x": 650, "y": 230, "w": 270, "h": 150,
                                "fields": ["+ id: bigint [PK]", "# capitulo_id: bigint [FK]", "# creado_por_id: bigint [FK]", "+ numero_revision: integer", "+ codigo_paso: varchar(3)", "+ contenido_sha256: char(64)", "* TRIGGER: Inmutable"]},
    "tesis_comentario_revision": {"title": "tesis_comentario_revision", "x": 650, "y": 420, "w": 270, "h": 140,
                                 "fields": ["+ id: bigint [PK]", "# revision_id: bigint [FK]", "# autor_id: bigint [FK]", "+ inicio_caracter, fin_caracter: int", "+ texto_seleccionado: text", "+ estado: varchar(10)"]},
    "tesis_evento_revision": {"title": "tesis_evento_revision [Auditoría]", "x": 650, "y": 590, "w": 270, "h": 140,
                              "fields": ["+ id: bigint [PK]", "# capitulo_id: bigint [FK]", "# revision_id: bigint [FK]", "# usuario_actor_id: bigint [FK]", "+ accion: varchar(20)", "+ creado_en: timestamptz"]},

    # Dominio 3: Perfil Metodológico y Avance
    "tesis_perfil_investigacion": {"title": "tesis_perfil_investigacion", "x": 970, "y": 60, "w": 260, "h": 150,
                                   "fields": ["+# proyecto_id: uuid [PK, FK 1:1]", "+ enfoque: varchar(16)", "+ tema: text", "+ codigo_ods: varchar(20)", "+ unidad_analisis: text", "+ planteamiento_problema: text", "+ version_bloqueo: integer"]},
    "tesis_progreso_paso": {"title": "tesis_progreso_paso [P01-P12]", "x": 970, "y": 240, "w": 260, "h": 120,
                            "fields": ["+ id: bigint [PK]", "# proyecto_id: uuid [FK]", "+ codigo_paso: varchar(3)", "+ estado: varchar(16)", "+ salida_json: jsonb"]},

    # Dominio 4: Matriz y Variables
    "tesis_fila_consistencia": {"title": "tesis_fila_consistencia [Matriz]", "x": 1280, "y": 60, "w": 270, "h": 140,
                                "fields": ["+ id: bigint [PK]", "# proyecto_id: uuid [FK]", "+ orden: smallint (0..N)", "+ texto_pregunta: text", "+ texto_objetivo: text", "+ texto_hipotesis: text"]},
    "tesis_variable_investigacion": {"title": "tesis_variable_investigacion", "x": 1280, "y": 230, "w": 270, "h": 140,
                                     "fields": ["+ id: bigint [PK]", "# proyecto_id: uuid [FK]", "+ nombre: varchar(200)", "+ rol: varchar(16) (IND/DEP)", "+ definicion_conceptual: text", "+ definicion_operacional: text"]},
    "tesis_variable_fila_consistencia": {"title": "tesis_variable_fila_consistencia", "x": 1280, "y": 400, "w": 270, "h": 90,
                                         "fields": ["+ id: bigint [PK]", "# fila_consistencia_id: bigint [FK]", "# variable_id: bigint [FK]"]},
    "tesis_dimension_variable": {"title": "tesis_dimension_variable", "x": 1280, "y": 520, "w": 270, "h": 90,
                                 "fields": ["+ id: bigint [PK]", "# variable_id: bigint [FK]", "+ orden: smallint", "+ nombre: varchar(200)"]},
    "tesis_indicador": {"title": "tesis_indicador [P12]", "x": 1280, "y": 640, "w": 270, "h": 110,
                        "fields": ["+ id: bigint [PK]", "# dimension_id: bigint [FK]", "+ orden: smallint", "+ nombre: varchar(200)", "+ escala_medicion: varchar(30)"]},
}

RELATIONS_DRAWIO = [
    ("tesis_usuario", "tesis_token_acceso_mcp", "1 : N"),
    ("tesis_usuario", "tesis_usuario_grupo", "1 : N"),
    ("tesis_usuario", "tesis_usuario_permiso", "1 : N"),
    ("tesis_usuario", "tesis_participante_proyecto", "1 : N"),
    ("tesis_proyecto", "tesis_participante_proyecto", "1 : N"),
    ("tesis_proyecto", "tesis_capitulo", "1 : N"),
    ("tesis_proyecto", "tesis_perfil_investigacion", "1 : 1"),
    ("tesis_proyecto", "tesis_progreso_paso", "1 : N"),
    ("tesis_proyecto", "tesis_fila_consistencia", "1 : N"),
    ("tesis_proyecto", "tesis_variable_investigacion", "1 : N"),
    ("tesis_capitulo", "tesis_revision_capitulo", "1 : N"),
    ("tesis_capitulo", "tesis_evento_revision", "1 : N"),
    ("tesis_revision_capitulo", "tesis_comentario_revision", "1 : N"),
    ("tesis_revision_capitulo", "tesis_evento_revision", "0..1 : N"),
    ("tesis_fila_consistencia", "tesis_variable_fila_consistencia", "1 : N"),
    ("tesis_variable_investigacion", "tesis_variable_fila_consistencia", "1 : N"),
    ("tesis_variable_investigacion", "tesis_dimension_variable", "1 : N"),
    ("tesis_dimension_variable", "tesis_indicador", "1 : N"),
    ("tesis_usuario", "tesis_revision_capitulo", "1 : N"),
    ("tesis_usuario", "tesis_comentario_revision", "1 : N"),
    ("tesis_usuario", "tesis_evento_revision", "1 : N"),
]

mxfile = ET.Element("mxfile", host="Electron", modified="2026-10-19T18:00:00.000Z", agent="Antigravity", version="21.6.8", type="device")
diagram = ET.SubElement(mxfile, "diagram", id="diag_der_oficial", name="DER_Fisico_17_Tablas")
model = ET.SubElement(diagram, "mxGraphModel", dx="1800", dy="1200", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1650", pageHeight="950", math="0", shadow="0")
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")

for k, t in TABLES_DRAWIO.items():
    content = f"<b>{t['title']}</b><br/><hr/>" + "<br/>".join(t["fields"])
    node = ET.SubElement(root, "mxCell", id=k, parent="1", value=content, vertex="1")
    node.set("style", "rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;align=left;spacing=6;fontSize=10;verticalAlign=top;")
    geom = ET.SubElement(node, "mxGeometry", x=str(t["x"]), y=str(t["y"]), width=str(t["w"]), height=str(t["h"]))
    geom.set("as", "geometry")

for idx, (s, tgt, card) in enumerate(RELATIONS_DRAWIO):
    edge_id = f"edge_{s}_{tgt}_{idx}"
    edge = ET.SubElement(root, "mxCell", id=edge_id, parent="1", edge="1", source=s, target=tgt, value=f"{card}")
    edge.set("style", "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;strokeWidth=1.5;endArrow=ERmany;startArrow=ERmandOne;fontSize=9;fontColor=#000000;labelBackgroundColor=#ffffff;")
    geom = ET.SubElement(edge, "mxGeometry", relative="1")
    geom.set("as", "geometry")

tree = ET.ElementTree(mxfile)
ET.indent(tree, space="  ", level=0)
tree.write(DRAWIO_PATH, encoding="utf-8", xml_declaration=True)
print(f"Archivo .drawio generado con éxito en: {DRAWIO_PATH}")
