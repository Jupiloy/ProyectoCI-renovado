#!/usr/bin/env python3
"""
Generador de Diagramas UML en Blanco y Negro Puro (Estilo Diagrams.net / Draw.io):
1. 08_secuencia_guardar_paso: Diagrama de Secuencia UML (Líneas de vida, mensajes, transacciones y alt).
2. 09_estados_revision_capitulo: Diagrama de Máquina de Estados UML (Estados, guardas y transiciones).
"""

import os
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image

OUT_DIR = "V1/docs/diagramas"
os.makedirs(OUT_DIR, exist_ok=True)

# ==============================================================================
# 1. DIAGRAMA DE SECUENCIA UML (08_secuencia_guardar_paso)
# ==============================================================================
SEQ_SVG = os.path.join(OUT_DIR, "08_secuencia_guardar_paso.svg")
SEQ_PNG = os.path.join(OUT_DIR, "08_secuencia_guardar_paso.png")
SEQ_DRAWIO = os.path.join(OUT_DIR, "08_secuencia_guardar_paso.drawio")

seq_svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 740" width="1120" height="740">
  <defs>
    <marker id="arrow-solid" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
    </marker>
    <marker id="arrow-open" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 2 L 7 5 L 0 8" fill="none" stroke="#000000" stroke-width="1.5"/>
    </marker>
    <style>
      .life-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 11px; font-weight: bold; fill: #000000; text-anchor: middle; }
      .life-sub { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 9.5px; fill: #000000; text-anchor: middle; }
      .msg-txt { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 10px; font-weight: 600; fill: #000000; }
      .frame-lbl { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 10px; font-weight: bold; fill: #000000; }
      .guard-txt { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 10px; font-style: italic; fill: #000000; }
    </style>
  </defs>

  <rect x="0" y="0" width="1120" height="740" fill="#ffffff"/>

  <!-- Encabezado del Diagrama -->
  <text x="35" y="32" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#000000">DIAGRAMA DE SECUENCIA UML — GUARDADO DE UN PASO Y CONTROL DE CONCURRENCIA</text>
  <line x1="35" y1="42" x2="1085" y2="42" stroke="#000000" stroke-width="1"/>

  <!-- ==================================================================== -->
  <!-- PARTICIPANTES / LÍNEAS DE VIDA -->
  <!-- ==================================================================== -->
  <!-- Participante 1: Tesista -->
  <rect x="60" y="55" width="160" height="45" fill="#ffffff" stroke="#000000" stroke-width="1.5"/>
  <text x="140" y="73" class="life-title">:Tesista</text>
  <text x="140" y="88" class="life-sub">Cliente MCP / API REST</text>
  <line x1="140" y1="100" x2="140" y2="690" stroke="#000000" stroke-width="1.2" stroke-dasharray="6,4"/>

  <!-- Participante 2: StepService -->
  <rect x="330" y="55" width="170" height="45" fill="#ffffff" stroke="#000000" stroke-width="1.5"/>
  <text x="415" y="73" class="life-title">:ServicioPasos</text>
  <text x="415" y="88" class="life-sub">thesis.services (Dominio)</text>
  <line x1="415" y1="100" x2="415" y2="690" stroke="#000000" stroke-width="1.2" stroke-dasharray="6,4"/>

  <!-- Participante 3: Contratos Pydantic -->
  <rect x="610" y="55" width="170" height="45" fill="#ffffff" stroke="#000000" stroke-width="1.5"/>
  <text x="695" y="73" class="life-title">:ContratosPydantic</text>
  <text x="695" y="88" class="life-sub">SalidaEstricta (extra='forbid')</text>
  <line x1="695" y1="100" x2="695" y2="690" stroke="#000000" stroke-width="1.2" stroke-dasharray="6,4"/>

  <!-- Participante 4: PostgreSQL 16 -->
  <rect x="890" y="55" width="160" height="45" fill="#ffffff" stroke="#000000" stroke-width="1.5"/>
  <text x="970" y="73" class="life-title">:PostgreSQL 16</text>
  <text x="970" y="88" class="life-sub">tesismcp_reducido_docente</text>
  <line x1="970" y1="100" x2="970" y2="690" stroke="#000000" stroke-width="1.2" stroke-dasharray="6,4"/>

  <!-- ==================================================================== -->
  <!-- BARRAS DE ACTIVACIÓN -->
  <!-- ==================================================================== -->
  <rect x="134" y="115" width="12" height="550" fill="#ffffff" stroke="#000000" stroke-width="1.2"/>
  <rect x="409" y="125" width="12" height="530" fill="#ffffff" stroke="#000000" stroke-width="1.2"/>
  <rect x="689" y="160" width="12" height="60" fill="#ffffff" stroke="#000000" stroke-width="1.2"/>
  <rect x="964" y="275" width="12" height="185" fill="#ffffff" stroke="#000000" stroke-width="1.2"/>
  <rect x="964" y="550" width="12" height="40" fill="#ffffff" stroke="#000000" stroke-width="1.2"/>

  <!-- ==================================================================== -->
  <!-- FLUJO DE MENSAJES SÍNCRONOS Y ASÍNCRONOS -->
  <!-- ==================================================================== -->
  <!-- Mensaje 1: Tesista -> ServicioPasos -->
  <line x1="146" y1="130" x2="407" y2="130" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow-solid)"/>
  <text x="155" y="123" class="msg-txt">1: guardar_paso_servicio(id_proyecto, paso_codigo, salida_json, lock_version_esperada)</text>

  <!-- Mensaje 2: ServicioPasos -> Contratos Pydantic -->
  <line x1="421" y1="165" x2="687" y2="165" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow-solid)"/>
  <text x="430" y="158" class="msg-txt">2: validar_contrato(SalidaEstricta, extra="forbid")</text>

  <!-- Mensaje 3: Contratos -> ServicioPasos (retorno) -->
  <line x1="689" y1="210" x2="421" y2="210" stroke="#000000" stroke-width="1.5" stroke-dasharray="4,4" marker-end="url(#arrow-open)"/>
  <text x="470" y="203" class="msg-txt">3: contrato_valido(datos_tipados)</text>

  <!-- Mensaje 4: ServicioPasos -> PostgreSQL (bloqueo y lectura concurrente) -->
  <line x1="421" y1="260" x2="962" y2="260" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow-solid)"/>
  <text x="430" y="253" class="msg-txt">4: BEGIN &amp; SELECT FOR UPDATE lock_version FROM tesis_proyecto</text>

  <!-- ==================================================================== -->
  <!-- FRAGMENTO CONDICIONAL ALT (Concurrencia Optimista) -->
  <!-- ==================================================================== -->
  <rect x="75" y="285" width="990" height="360" fill="none" stroke="#000000" stroke-width="1.5"/>
  <rect x="75" y="285" width="55" height="22" fill="#ffffff" stroke="#000000" stroke-width="1.5"/>
  <text x="102" y="300" text-anchor="middle" class="frame-lbl">alt</text>

  <!-- Caso 1: Versión Válida -->
  <text x="145" y="310" class="guard-txt">[lock_version_bd == lock_version_esperada: Versión vigente]</text>

  <!-- Mensaje 5: Materialización en BD -->
  <line x1="421" y1="335" x2="962" y2="335" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow-solid)"/>
  <text x="430" y="328" class="msg-txt">5: INSERT / UPDATE entidades (tesis_progreso, tesis_consistencia, tesis_variable)</text>

  <!-- Mensaje 6: Creación de Revisión Inmutable -->
  <line x1="421" y1="375" x2="962" y2="375" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow-solid)"/>
  <text x="430" y="368" class="msg-txt">6: INSERT tesis_revision_capitulo (historial append-only auditado)</text>

  <!-- Mensaje 7: Incremento de Versión y Commit -->
  <line x1="421" y1="415" x2="962" y2="415" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow-solid)"/>
  <text x="430" y="408" class="msg-txt">7: lock_version += 1 &amp; COMMIT TRANSACTION</text>

  <!-- Mensaje 8: Retorno exitoso a Tesista -->
  <line x1="409" y1="445" x2="148" y2="445" stroke="#000000" stroke-width="1.5" stroke-dasharray="4,4" marker-end="url(#arrow-open)"/>
  <text x="175" y="438" class="msg-txt">8: return PasoGuardadoDTO(id_revision, nueva_lock_version, status="COMPLETED")</text>

  <!-- Línea divisoria del ALT -->
  <line x1="75" y1="475" x2="1065" y2="475" stroke="#000000" stroke-width="1.2" stroke-dasharray="6,4"/>

  <!-- Caso 2: Conflicto Concurrente -->
  <text x="145" y="495" class="guard-txt">[lock_version_bd != lock_version_esperada: Conflicto detectado]</text>

  <!-- Mensaje 9: Rollback en PostgreSQL -->
  <line x1="421" y1="535" x2="962" y2="535" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow-solid)"/>
  <text x="430" y="528" class="msg-txt">9: ROLLBACK TRANSACTION (Cero modificaciones persistidas)</text>

  <!-- Mensaje 10: Error devuelto al Tesista -->
  <line x1="409" y1="575" x2="148" y2="575" stroke="#000000" stroke-width="1.5" stroke-dasharray="4,4" marker-end="url(#arrow-open)"/>
  <text x="175" y="568" class="msg-txt">10: raise VersionConflictException("VERSION_CONFLICT: Estado desactualizado")</text>

  <rect x="175" y="595" width="460" height="24" rx="4" fill="#ffffff" stroke="#000000" stroke-width="1"/>
  <text x="405" y="611" text-anchor="middle" font-family="Arial, sans-serif" font-size="9.5" fill="#000000">Garantía: La base de datos rechaza escrituras con versiones obsoletas de forma determinista.</text>
</svg>
"""

with open(SEQ_SVG, "w", encoding="utf-8") as f:
    f.write(seq_svg_content)
print(f"SVG de Secuencia generado: {SEQ_SVG}")

# Renderizar PNG vía Chrome Headless
TMP_HTML_SEQ = "/tmp/seq_render.html"
with open(TMP_HTML_SEQ, "w", encoding="utf-8") as f:
    f.write(f"<!DOCTYPE html><html><body style='margin:0;background:white;'>{seq_svg_content}</body></html>")

subprocess.run([
    "google-chrome", "--headless", "--disable-gpu", "--force-device-scale-factor=2",
    f"--screenshot={SEQ_PNG}", "--window-size=1120,740", "--default-background-color=00000000",
    f"file://{TMP_HTML_SEQ}"
], check=True)

img = Image.open(SEQ_PNG)
bbox = img.getbbox()
if bbox:
    img = img.crop(bbox)
img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=32).save(SEQ_PNG, optimize=True)
print(f"PNG Secuencia generado: {SEQ_PNG} ({os.path.getsize(SEQ_PNG)//1024} KB)")

# Generar Draw.io XML para Secuencia
mxfile = ET.Element("mxfile", host="Electron", agent="Antigravity", version="21.6.8", type="device")
diag = ET.SubElement(mxfile, "diagram", id="diag_seq", name="Secuencia_Guardar_Paso_UML")
model = ET.SubElement(diag, "mxGraphModel", dx="1200", dy="800", grid="1", gridSize="10",
                      guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1",
                      pageScale="1", pageWidth="1150", pageHeight="780", math="0", shadow="0")
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")

life_style = ("shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;"
              "recursiveResize=0;outlineConnect=0;strokeColor=#000000;strokeWidth=1.5;fillColor=#ffffff;fontSize=11;fontFamily=Arial;fontStyle=1;")
msg_style = ("html=1;verticalAlign=bottom;endArrow=block;edgeStyle=elbowEdgeStyle;elbow=vertical;curved=0;rounded=0;"
             "strokeColor=#000000;strokeWidth=1.5;fontSize=10;fontFamily=Arial;labelBackgroundColor=#ffffff;")
ret_style = ("html=1;verticalAlign=bottom;endArrow=open;dashed=1;endSize=8;edgeStyle=elbowEdgeStyle;elbow=vertical;curved=0;rounded=0;"
             "strokeColor=#000000;strokeWidth=1.5;fontSize=10;fontFamily=Arial;labelBackgroundColor=#ffffff;")

l1 = ET.SubElement(root, "mxCell", id="l1", parent="1", value=":Tesista<br/>(Cliente MCP/API)", vertex="1", style=life_style)
ET.SubElement(l1, "mxGeometry", x="60", y="50", width="160", height="620", as_="geometry")

l2 = ET.SubElement(root, "mxCell", id="l2", parent="1", value=":ServicioPasos<br/>thesis.services", vertex="1", style=life_style)
ET.SubElement(l2, "mxGeometry", x="330", y="50", width="170", height="620", as_="geometry")

l3 = ET.SubElement(root, "mxCell", id="l3", parent="1", value=":ContratosPydantic<br/>SalidaEstricta", vertex="1", style=life_style)
ET.SubElement(l3, "mxGeometry", x="610", y="50", width="170", height="620", as_="geometry")

l4 = ET.SubElement(root, "mxCell", id="l4", parent="1", value=":PostgreSQL 16<br/>tesismcp_reducido", vertex="1", style=life_style)
ET.SubElement(l4, "mxGeometry", x="890", y="50", width="160", height="620", as_="geometry")

tree = ET.ElementTree(mxfile)
ET.indent(tree, space="  ", level=0)
tree.write(SEQ_DRAWIO, encoding="utf-8", xml_declaration=True)
print(f"Draw.io Secuencia generado: {SEQ_DRAWIO}")


# ==============================================================================
# 2. DIAGRAMA DE MÁQUINA DE ESTADOS UML (09_estados_revision_capitulo)
# ==============================================================================
STATE_SVG = os.path.join(OUT_DIR, "09_estados_revision_capitulo.svg")
STATE_PNG = os.path.join(OUT_DIR, "09_estados_revision_capitulo.png")
STATE_DRAWIO = os.path.join(OUT_DIR, "09_estados_revision_capitulo.drawio")

state_svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 620" width="1100" height="620">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
    </marker>
    <style>
      .state-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 12px; font-weight: bold; fill: #000000; text-anchor: middle; letter-spacing: 0.05em; }
      .state-body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 10px; fill: #000000; }
      .trans-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 10px; font-weight: bold; fill: #000000; text-anchor: middle; }
      .guard-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 9px; font-style: italic; fill: #000000; text-anchor: middle; }
      .pill { fill: #ffffff; stroke: #000000; stroke-width: 1; rx: 4; }
    </style>
  </defs>

  <rect x="0" y="0" width="1100" height="620" fill="#ffffff"/>

  <!-- Encabezado del Diagrama -->
  <text x="35" y="32" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#000000">DIAGRAMA DE ESTADOS UML — CICLO DE REVISIÓN DOCENTE (Capitulo.status)</text>
  <line x1="35" y1="42" x2="1065" y2="42" stroke="#000000" stroke-width="1"/>

  <!-- Estado Inicial: Pseudo-estado [*] -->
  <circle cx="50" cy="180" r="12" fill="#000000"/>
  <line x1="62" y1="180" x2="120" y2="180" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="85" y="165" class="guard-label">crear()</text>

  <!-- ==================================================================== -->
  <!-- ESTADO 1: BORRADOR (DRAFT) -->
  <!-- ==================================================================== -->
  <rect x="120" y="130" width="230" height="100" rx="10" fill="#ffffff" stroke="#000000" stroke-width="1.8"/>
  <text x="235" y="152" class="state-title">BORRADOR (DRAFT)</text>
  <line x1="120" y1="162" x2="350" y2="162" stroke="#000000" stroke-width="1.2"/>
  <text x="135" y="180" class="state-body">entry / habilitar_escritura_pasos()</text>
  <text x="135" y="198" class="state-body">do / tesista_guarda_pasos(P01..P12)</text>
  <text x="135" y="216" class="state-body">exit / verificar_pasos_completos()</text>

  <!-- Transición DRAFT -> READY -->
  <line x1="350" y1="180" x2="490" y2="180" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <rect x="375" y="145" width="105" height="28" class="pill"/>
  <text x="427" y="157" class="trans-label">enviar_capitulo()</text>
  <text x="427" y="169" class="guard-label">[100% pasos COMPLETED]</text>

  <!-- ==================================================================== -->
  <!-- ESTADO 2: ENVIADO A REVISIÓN (READY) -->
  <!-- ==================================================================== -->
  <rect x="490" y="130" width="240" height="100" rx="10" fill="#ffffff" stroke="#000000" stroke-width="1.8"/>
  <text x="610" y="152" class="state-title">ENVIADO (READY)</text>
  <line x1="490" y1="162" x2="730" y2="162" stroke="#000000" stroke-width="1.2"/>
  <text x="505" y="180" class="state-body">entry / bloquear_edicion_tesista()</text>
  <text x="505" y="198" class="state-body">do / asesor_examina_capitulo()</text>
  <text x="505" y="216" class="state-body">do / registrar_observaciones_ancladas()</text>

  <!-- Transición READY -> APPROVED -->
  <line x1="730" y1="180" x2="860" y2="180" stroke="#000000" stroke-width="1.5" marker-end="url(#arrow)"/>
  <rect x="745" y="145" width="100" height="28" class="pill"/>
  <text x="795" y="157" class="trans-label">decidir(APPROVE)</text>
  <text x="795" y="169" class="guard-label">[0 obs. abiertas]</text>

  <!-- ==================================================================== -->
  <!-- ESTADO 3: APROBADO (APPROVED) -->
  <!-- ==================================================================== -->
  <rect x="860" y="130" width="220" height="100" rx="10" fill="#ffffff" stroke="#000000" stroke-width="2"/>
  <text x="970" y="152" class="state-title">APROBADO (APPROVED)</text>
  <line x1="860" y1="162" x2="1080" y2="162" stroke="#000000" stroke-width="1.2"/>
  <text x="875" y="180" class="state-body">entry / registrar_aprobacion()</text>
  <text x="875" y="198" class="state-body">do / congelar_version_oficial()</text>
  <text x="875" y="216" class="state-body">exit / registrar_motivo_reapertura()</text>

  <!-- ==================================================================== -->
  <!-- ESTADO 4: CAMBIOS SOLICITADOS (CHANGES_REQUESTED) -->
  <!-- ==================================================================== -->
  <rect x="340" y="380" width="270" height="100" rx="10" fill="#ffffff" stroke="#000000" stroke-width="1.8"/>
  <text x="475" y="402" class="state-title">CAMBIOS SOLICITADOS</text>
  <line x1="340" y1="412" x2="610" y2="412" stroke="#000000" stroke-width="1.2"/>
  <text x="355" y="430" class="state-body">entry / listar_observaciones_abiertas()</text>
  <text x="355" y="448" class="state-body">do / tesista_corrige_texto_anclado()</text>
  <text x="355" y="466" class="state-body">exit / crear_nueva_revision_inmutable()</text>

  <!-- Transición READY -> CHANGES_REQUESTED -->
  <path d="M 610 230 L 610 320 L 520 320 L 520 380" stroke="#000000" stroke-width="1.5" fill="none" marker-end="url(#arrow)"/>
  <rect x="525" y="275" width="150" height="28" class="pill"/>
  <text x="600" y="287" class="trans-label">decidir(REQUEST_CHANGES)</text>
  <text x="600" y="299" class="guard-label">[observaciones_abiertas &gt; 0]</text>

  <!-- Transición CHANGES_REQUESTED -> DRAFT -->
  <path d="M 340 430 L 235 430 L 235 230" stroke="#000000" stroke-width="1.5" fill="none" marker-end="url(#arrow)"/>
  <rect x="150" y="325" width="145" height="28" class="pill"/>
  <text x="222" y="337" class="trans-label">guardar_paso_servicio()</text>
  <text x="222" y="349" class="guard-label">[Tesista subsana observaciones]</text>

  <!-- Transición APPROVED -> DRAFT (Reapertura por Asesor) -->
  <path d="M 970 130 L 970 75 L 235 75 L 235 130" stroke="#000000" stroke-width="1.5" stroke-dasharray="6,4" fill="none" marker-end="url(#arrow)"/>
  <rect x="510" y="60" width="180" height="28" class="pill"/>
  <text x="600" y="73" class="trans-label">decidir(REOPEN)</text>
  <text x="600" y="85" class="guard-label">[Solo Asesor y con motivo registrado]</text>

  <!-- Nota explicativa al pie -->
  <rect x="120" y="525" width="860" height="45" rx="6" fill="#ffffff" stroke="#000000" stroke-width="1"/>
  <text x="140" y="545" font-family="Arial, sans-serif" font-size="10.5" font-weight="bold" fill="#000000">Garantía de Inmutabilidad en Base de Datos:</text>
  <text x="140" y="560" font-family="Arial, sans-serif" font-size="9.5" fill="#000000">Cada ciclo de revisión genera registros append-only en tesis_revision_capitulo protegidos por triggers PL/pgSQL.</text>
</svg>
"""

with open(STATE_SVG, "w", encoding="utf-8") as f:
    f.write(state_svg_content)
print(f"SVG de Estados generado: {STATE_SVG}")

# Renderizar PNG vía Chrome Headless
TMP_HTML_STATE = "/tmp/state_render.html"
with open(TMP_HTML_STATE, "w", encoding="utf-8") as f:
    f.write(f"<!DOCTYPE html><html><body style='margin:0;background:white;'>{state_svg_content}</body></html>")

subprocess.run([
    "google-chrome", "--headless", "--disable-gpu", "--force-device-scale-factor=2",
    f"--screenshot={STATE_PNG}", "--window-size=1100,620", "--default-background-color=00000000",
    f"file://{TMP_HTML_STATE}"
], check=True)

img = Image.open(STATE_PNG)
bbox = img.getbbox()
if bbox:
    img = img.crop(bbox)
img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=32).save(STATE_PNG, optimize=True)
print(f"PNG Estados generado: {STATE_PNG} ({os.path.getsize(STATE_PNG)//1024} KB)")

# Generar Draw.io XML para Estados
mxfile = ET.Element("mxfile", host="Electron", agent="Antigravity", version="21.6.8", type="device")
diag = ET.SubElement(mxfile, "diagram", id="diag_state", name="Estados_Revision_Capitulo_UML")
model = ET.SubElement(diag, "mxGraphModel", dx="1200", dy="800", grid="1", gridSize="10",
                      guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1",
                      pageScale="1", pageWidth="1150", pageHeight="700", math="0", shadow="0")
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")

state_style = ("rounded=1;whiteSpace=wrap;html=1;strokeColor=#000000;strokeWidth=1.8;fillColor=#ffffff;"
               "align=left;verticalAlign=top;spacingLeft=10;spacingTop=6;fontSize=10;fontColor=#000000;fontFamily=Arial;")
edge_style = ("edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
              "strokeColor=#000000;strokeWidth=1.5;endArrow=block;fontSize=10;fontColor=#000000;labelBackgroundColor=#ffffff;")

s_draft = ET.SubElement(root, "mxCell", id="s_draft", parent="1", value="<b>BORRADOR (DRAFT)</b><br/><hr/>entry / habilitar_escritura_pasos()<br/>do / tesista_guarda_pasos(P01..P12)", vertex="1", style=state_style)
ET.SubElement(s_draft, "mxGeometry", x="120", y="130", width="230", height="100", as_="geometry")

s_ready = ET.SubElement(root, "mxCell", id="s_ready", parent="1", value="<b>ENVIADO (READY)</b><br/><hr/>entry / bloquear_edicion_tesista()<br/>do / asesor_examina_capitulo()", vertex="1", style=state_style)
ET.SubElement(s_ready, "mxGeometry", x="490", y="130", width="240", height="100", as_="geometry")

s_appr = ET.SubElement(root, "mxCell", id="s_appr", parent="1", value="<b>APROBADO (APPROVED)</b><br/><hr/>entry / registrar_aprobacion()<br/>do / congelar_version_oficial()", vertex="1", style=state_style)
ET.SubElement(s_appr, "mxGeometry", x="860", y="130", width="220", height="100", as_="geometry")

s_chg = ET.SubElement(root, "mxCell", id="s_chg", parent="1", value="<b>CAMBIOS SOLICITADOS</b><br/><hr/>entry / listar_observaciones_abiertas()<br/>do / tesista_corrige_texto()", vertex="1", style=state_style)
ET.SubElement(s_chg, "mxGeometry", x="340", y="380", width="270", height="100", as_="geometry")

tree = ET.ElementTree(mxfile)
ET.indent(tree, space="  ", level=0)
tree.write(STATE_DRAWIO, encoding="utf-8", xml_declaration=True)
print(f"Draw.io Estados generado: {STATE_DRAWIO}")
