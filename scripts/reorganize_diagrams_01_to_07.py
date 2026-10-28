#!/usr/bin/env python3
"""
Script para reorganizar y estandarizar los 7 diagramas oficiales en docs/diagramas/
del corte Semana 10 (V1).
"""

import os
import shutil
import xml.etree.ElementTree as ET

DIAG_DIR = "V1/docs/diagramas"
DOCS_DIR = "V1/docs"
REPORT_MD = os.path.join(DOCS_DIR, "07_INFORME_BASE_SEMANA_10.md")

def create_lean_canvas_drawio(out_path):
    mxfile = ET.Element("mxfile", host="Electron", agent="Antigravity", version="21.6.8", type="device")
    diag = ET.SubElement(mxfile, "diagram", id="diag_lean_canvas", name="Lean_Canvas_TesisMCP")
    model = ET.SubElement(diag, "mxGraphModel", dx="1600", dy="1000", grid="1", gridSize="10",
                          guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1",
                          pageScale="1", pageWidth="1450", pageHeight="900", math="0", shadow="0")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    # Estilo base
    box_style = ("rounded=0;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.5;"
                 "fillColor=#ffffff;align=left;verticalAlign=top;spacingLeft=12;spacingTop=12;"
                 "spacingRight=12;spacingBottom=12;fontSize=11;fontColor=#000000;fontFamily=Arial;")

    boxes = [
        # (id, title, x, y, w, h, content)
        (
            "box_problem",
            "1. PROBLEMA",
            20, 20, 275, 530,
            "<b>1. PROBLEMA</b><br/><br/>"
            "• <b>Pérdida de contexto e hilo conductor:</b> Desarticulación frecuente entre problemas, objetivos, hipótesis y variables al trabajar en sesiones dispersas.<br/><br/>"
            "• <b>Alucinaciones e invención de fuentes:</b> Los LLM comerciales inventan citas, autores y páginas inexistentes por falta de verificación a texto completo.<br/><br/>"
            "• <b>Revisión docente fragmentada:</b> Correcciones del asesor dispersas en múltiples archivos Word sin trazabilidad de cambios ni historial.<br/><br/>"
            "----------------------------------------<br/>"
            "<b>ALTERNATIVAS EXISTENTES</b><br/>"
            "• Chats de IA generalistas sin estado ni reglas (ChatGPT, Claude web).<br/>"
            "• Plantillas Word y formatos institucionales estáticos.<br/>"
            "• Portales tradicionales de subida de archivos (sin asistencia metodológica)."
        ),
        (
            "box_solution",
            "4. SOLUCIÓN",
            305, 20, 275, 260,
            "<b>4. SOLUCIÓN</b><br/><br/>"
            "• <b>Ruta guiada P01 a P12:</b> Desacople en 12 pasos secuenciales para los capítulos 1 al 3 con prerrequisitos bloqueantes.<br/><br/>"
            "• <b>Servidor MCP + API REST:</b> 17 herramientas y 15 prompts que aíslan el modelo de la persistencia directa.<br/><br/>"
            "• <b>Supervisión con observaciones ancladas:</b> Máquina de estados FSM y comentarios vinculados a posiciones exactas de caracteres."
        ),
        (
            "box_metrics",
            "8. MÉTRICAS CLAVE",
            305, 290, 275, 260,
            "<b>8. MÉTRICAS CLAVE</b><br/><br/>"
            "• <b>Rigor de contratos:</b> 100% de salidas validadas bajo contratos estrictos Pydantic 2 sin campos huérfanos.<br/><br/>"
            "• <b>Resolución de observaciones:</b> Tasa de comentarios en estado resuelto antes de la aprobación del capítulo.<br/><br/>"
            "• <b>Control de versiones:</b> Detección determinista de colisiones concurrentes mediante control de versiones optimista.<br/><br/>"
            "• <b>Automatización auditada:</b> 32 pruebas automatizadas y 7 compuertas en verde."
        ),
        (
            "box_uvp",
            "3. PROPUESTA DE VALOR ÚNICA",
            590, 20, 275, 530,
            "<b>3. PROPUESTA DE VALOR ÚNICA</b><br/><br/>"
            "<i>\"Asistencia metodológica estructurada y supervisión docente inmutable.\"</i><br/><br/>"
            "• Una plataforma que no redacta libremente ni inventa fuentes: guía al estudiante paso a paso (P01 a P12) y valida consistencia lógica matemática.<br/><br/>"
            "• <b>Trazabilidad auditable:</b> El estudiante sabe exactamente qué aprobó su docente y qué revisión está vigente.<br/><br/>"
            "• <b>Cero tolerancia al formateo ciego:</b> Cada decisión metodológica se materializa en tablas relacionales estructuradas.<br/><br/>"
            "----------------------------------------<br/>"
            "<b>CONCEPTO DE ALTO NIVEL</b><br/>"
            "<i>\"El entorno de desarrollo y validación determinista para tesis universitarias asistidas por IA.\"</i>"
        ),
        (
            "box_advantage",
            "9. VENTAJA DIFERENCIAL",
            875, 20, 275, 260,
            "<b>9. VENTAJA DIFERENCIAL</b><br/><br/>"
            "• <b>Arquitectura desacoplada:</b> El LLM no escribe directamente en la BD; solo propone contratos Pydantic validados por el backend Django.<br/><br/>"
            "• <b>Inmutabilidad física en PostgreSQL:</b> Disparadores en la base de datos que impiden modificar o borrar revisiones y eventos históricos.<br/><br/>"
            "• <b>Integraciones académicas verificadas:</b> Conectores a OpenAlex, Semantic Scholar y ALICIA (Concytec)."
        ),
        (
            "box_channels",
            "5. CANALES",
            875, 290, 275, 260,
            "<b>5. CANALES</b><br/><br/>"
            "• <b>Cliente MCP local:</b> Comunicación mediante transporte stdio para clientes de IA (Antigravity, Claude Desktop, Cursor).<br/><br/>"
            "• <b>API REST HTTP:</b> Endpoints /api/v1/ mediante Django Ninja para integraciones web.<br/><br/>"
            "• <b>Django Admin:</b> Panel de auditoría e inspección para revisión y docencia.<br/><br/>"
            "• <b>Repositorio y CLI:</b> Scripts deterministas de verificación y defensa académica."
        ),
        (
            "box_customer",
            "2. SEGMENTO DE CLIENTES",
            1160, 20, 275, 530,
            "<b>2. SEGMENTO DE CLIENTES</b><br/><br/>"
            "• <b>Estudiantes de tesis / curso integrador:</b> Tesistas de pregrado en ingeniería y ciencias que necesitan formular y defender su proyecto con rigor metodológico.<br/><br/>"
            "• <b>Docentes asesores y revisores:</b> Profesores que supervisan múltiples proyectos y requieren revisar borradores por capítulos, realizar observaciones puntuales y certificar avances sin confusiones de versiones.<br/><br/>"
            "----------------------------------------<br/>"
            "<b>EARLY ADOPTERS</b><br/>"
            "Estudiantes y docentes del Curso Integrador I (Sistemas - Software) de la Universidad Tecnológica del Perú (Filial Piura)."
        ),
        (
            "box_cost",
            "7. ESTRUCTURA DE COSTOS",
            20, 560, 560, 280,
            "<b>7. ESTRUCTURA DE COSTOS</b><br/><br/>"
            "<b>Costos de prototipo (Semana 10):</b><br/>"
            "• Infraestructura: S/. 0.00 (Entorno local en computadoras del equipo).<br/>"
            "• Software: S/. 0.00 (Stack 100% libre: Python, Django, PostgreSQL 16, SDK MCP).<br/>"
            "• Consumo LLM: Descentralizado (cuenta propia de cada usuario en su cliente de IA).<br/><br/>"
            "<b>Costos proyectados (Despliegue):</b><br/>"
            "• Servidor VPS: ~USD 12 - 20 / mes (Docker + PostgreSQL gestionado).<br/>"
            "• Almacenamiento PDF/OCR: Almacenamiento local o S3 compatible según volumen de tesis."
        ),
        (
            "box_revenue",
            "6. SOSTENIBILIDAD Y RETORNO DE VALOR",
            590, 560, 845, 280,
            "<b>6. SOSTENIBILIDAD Y RETORNO DE VALOR</b><br/><br/>"
            "<b>Retorno académico e institucional:</b><br/>"
            "• <b>Reducción de reprocesos:</b> Detección temprana de inconsistencias entre variables y objetivos antes de la sustentación.<br/>"
            "• <b>Mayor productividad docente:</b> Centralización de observaciones y eliminación de cadenas de correos con archivos duplicados.<br/><br/>"
            "<b>Modelo de adopción viable:</b><br/>"
            "• <b>Open Core / Auto-alojado:</b> Esquema de código abierto para universidades con soporte en gobernanza de datos.<br/>"
            "• <b>Tesis institucional:</b> Validación de conformidad con normativas SUNEDU y repositorios institucionales (ALICIA / RENATI)."
        ),
    ]

    for b_id, title, x, y, w, h, content in boxes:
        node = ET.SubElement(root, "mxCell", id=b_id, parent="1", value=content, vertex="1")
        node.set("style", box_style)
        geom = ET.SubElement(node, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h))
        geom.set("as", "geometry")

    tree = ET.ElementTree(mxfile)
    ET.indent(tree, space="  ", level=0)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"Creado Drawio Lean Canvas: {out_path}")

if __name__ == "__main__":
    lean_drawio_path = os.path.join(DIAG_DIR, "02_lean_canvas_tesismcp.drawio")
    create_lean_canvas_drawio(lean_drawio_path)
