#!/usr/bin/env python3
"""
Generador de Diagramas Visuales para Diapositivas de Exposición (Semana 9 / 10):
1. diapositiva_01_funcion_plataforma:
   Infografía moderna 16:9 con actores, flujo secuencial de 5 pasos, servicios técnicos y narrativa de sustentación.
2. diapositiva_02_arquitectura_mvc:
   Arquitectura MVC/MVT con herramientas reales (tipo Netflix/SEI) adaptada a TesisMCP.
"""

import os
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image

OUT_DIR = "V1/docs/diagramas"
os.makedirs(OUT_DIR, exist_ok=True)

# ==============================================================================
# 1. DIAPOSITIVA 01: FUNCIÓN DE LA PLATAFORMA (¿CÓMO FUNCIONA TESISMCP?)
# ==============================================================================
SLIDE1_SVG = os.path.join(OUT_DIR, "diapositiva_01_funcion_plataforma.svg")
SLIDE1_PNG = os.path.join(OUT_DIR, "diapositiva_01_funcion_plataforma.png")
SLIDE1_DRAWIO = os.path.join(OUT_DIR, "diapositiva_01_funcion_plataforma.drawio")

slide1_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
  <defs>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#f8fafc"/>
    </linearGradient>
    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#2563eb"/>
      <stop offset="100%" stop-color="#3b82f6"/>
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.08"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#2563eb"/>
    </marker>
    <style>
      .main-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 38px; font-weight: 900; fill: #ffffff; letter-spacing: 0.08em; }
      .sub-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 16px; fill: #94a3b8; font-weight: 500; }
      .section-badge { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 13px; font-weight: bold; fill: #2563eb; letter-spacing: 0.05em; }
      .card-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 16px; font-weight: 700; fill: #0f172a; }
      .card-desc { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 13px; fill: #475569; line-height: 1.45; }
      .bullet { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 12px; fill: #334155; }
      .step-num { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 14px; font-weight: 800; fill: #ffffff; }
      .narrative-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 18px; font-weight: 800; fill: #0f172a; }
      .narrative-p { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 13.5px; fill: #334155; line-height: 1.6; }
      .tag { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; font-size: 11px; font-weight: 600; fill: #1e293b; }
    </style>
  </defs>

  <!-- Fondo General de Diapositiva -->
  <rect x="0" y="0" width="1920" height="1080" fill="#f1f5f9"/>

  <!-- ==================================================================== -->
  <!-- BARRA SUPERIOR DE ENCABEZADO (Banner Principal) -->
  <!-- ==================================================================== -->
  <rect x="30" y="25" width="1860" height="90" rx="12" fill="url(#headerGrad)" filter="url(#shadow)"/>
  <circle cx="75" cy="70" r="22" fill="#2563eb"/>
  <text x="75" y="77" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#ffffff" text-anchor="middle">T</text>
  <text x="115" y="65" class="main-title">FUNCIÓN DE LA PLATAFORMA</text>
  <text x="115" y="92" class="sub-title">TesisMCP — Asistencia Metodológica en Etapas Desacopladas y Supervisión Continua de Tesis</text>
  <rect x="1660" y="50" width="200" height="40" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1"/>
  <text x="1760" y="75" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#38bdf8" text-anchor="middle">Semana 10 — Corte Oficial</text>

  <!-- ==================================================================== -->
  <!-- COLUMNA 1: ACTORES / USUARIOS (Izquierda, w=320) -->
  <!-- ==================================================================== -->
  <rect x="30" y="135" width="320" height="885" rx="12" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>
  <text x="55" y="175" class="section-badge">ROLES DEL SISTEMA</text>
  <text x="55" y="200" class="card-title">Usuarios Participantes</text>
  <line x1="55" y1="215" x2="325" y2="215" stroke="#e2e8f0" stroke-width="1"/>

  <!-- Actor 1: Tesista -->
  <g transform="translate(50, 235)">
    <rect x="0" y="0" width="280" height="340" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>
    <circle cx="40" cy="40" r="24" fill="#dbeafe"/>
    <!-- Icono Usuario -->
    <circle cx="40" cy="34" r="10" fill="#2563eb"/>
    <path d="M 24 53 C 24 43, 56 43, 56 53" fill="#2563eb"/>
    <text x="75" y="36" class="card-title" font-size="18">Tesista</text>
    <text x="75" y="54" class="tag" fill="#64748b">Estudiante Investigador</text>
    <line x1="15" y1="75" x2="265" y2="75" stroke="#e2e8f0" stroke-width="1"/>
    
    <text x="15" y="102" class="card-desc" font-weight="bold" fill="#0f172a">¿Qué hace en la plataforma?</text>
    <text x="15" y="130" class="bullet">• Evalúa y elige su tema de tesis.</text>
    <text x="15" y="155" class="bullet">• Redacta su trabajo paso a paso (P01 a P12).</text>
    <text x="15" y="180" class="bullet">• Busca antecedentes científicos reales.</text>
    <text x="15" y="205" class="bullet">• Envía sus capítulos terminados a revisión.</text>
    <text x="15" y="230" class="bullet">• Lee y corrige las observaciones del asesor.</text>
    <text x="15" y="255" class="bullet">• Descarga su borrador oficial en Word.</text>
    
    <rect x="15" y="280" width="250" height="42" rx="6" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1"/>
    <text x="25" y="298" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#1e40af">Rol en la metodología:</text>
    <text x="25" y="313" font-family="Arial, sans-serif" font-size="10" fill="#2563eb">Elaboración activa con asistencia guiada.</text>
  </g>

  <!-- Actor 2: Docente Asesor -->
  <g transform="translate(50, 600)">
    <rect x="0" y="0" width="280" height="340" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>
    <circle cx="40" cy="40" r="24" fill="#fef3c7"/>
    <!-- Icono Docente -->
    <circle cx="40" cy="34" r="10" fill="#d97706"/>
    <path d="M 24 53 C 24 43, 56 43, 56 53" fill="#d97706"/>
    <text x="75" y="36" class="card-title" font-size="18">Docente Asesor</text>
    <text x="75" y="54" class="tag" fill="#64748b">Profesor Revisor Metodológico</text>
    <line x1="15" y1="75" x2="265" y2="75" stroke="#e2e8f0" stroke-width="1"/>
    
    <text x="15" y="102" class="card-desc" font-weight="bold" fill="#0f172a">¿Qué hace en la plataforma?</text>
    <text x="15" y="130" class="bullet">• Lee el avance del capítulo completo.</text>
    <text x="15" y="155" class="bullet">• Señala párrafos exactos a corregir.</text>
    <text x="15" y="180" class="bullet">• Deja observaciones claras y explicadas.</text>
    <text x="15" y="205" class="bullet">• Revisa que el tesista haya corregido.</text>
    <text x="15" y="230" class="bullet">• Da el visto bueno y aprueba el capítulo.</text>
    <text x="15" y="255" class="bullet">• Puede reabrir si se requiere más ajuste.</text>
    
    <rect x="15" y="280" width="250" height="42" rx="6" fill="#fef3c7" stroke="#fde68a" stroke-width="1"/>
    <text x="25" y="298" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#92400e">Rol en la metodología:</text>
    <text x="25" y="313" font-family="Arial, sans-serif" font-size="10" fill="#b45309">Control de calidad y dictamen académico.</text>
  </g>

  <rect x="50" y="955" width="280" height="50" rx="8" fill="#0f172a"/>
  <text x="190" y="976" font-family="Arial, sans-serif" font-size="11.5" font-weight="bold" fill="#38bdf8" text-anchor="middle">Colaboración Desacoplada:</text>
  <text x="190" y="993" font-family="Arial, sans-serif" font-size="10.5" fill="#cbd5e1" text-anchor="middle">Cada actor tiene permisos y funciones separadas.</text>

  <!-- ==================================================================== -->
  <!-- SECCIÓN CENTRAL: FLUJO SECUENCIAL DE 5 PASOS (x=370, w=1080) -->
  <!-- ==================================================================== -->
  <rect x="370" y="135" width="1080" height="580" rx="12" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>
  <text x="395" y="175" class="section-badge">CÓMO FUNCIONA LA PLATAFORMA</text>
  <text x="395" y="200" class="card-title">Recorrido sencillo paso a paso (De la idea al capítulo aprobado)</text>
  <line x1="395" y1="215" x2="1425" y2="215" stroke="#e2e8f0" stroke-width="1"/>

  <!-- Paso 1: Elige tu Tema -->
  <g transform="translate(390, 235)">
    <rect x="0" y="0" width="195" height="450" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>
    <circle cx="28" cy="28" r="16" fill="#2563eb"/>
    <text x="28" y="34" class="step-num" text-anchor="middle">1</text>
    <text x="55" y="34" class="card-title" font-size="14">Elige tu Tema</text>

    <!-- Mockup Card -->
    <rect x="15" y="60" width="165" height="95" rx="6" fill="#ffffff" stroke="#94a3b8" stroke-width="1"/>
    <rect x="15" y="60" width="165" height="22" rx="6" fill="#1e293b"/>
    <circle cx="26" cy="71" r="3" fill="#ef4444"/>
    <circle cx="36" cy="71" r="3" fill="#eab308"/>
    <circle cx="46" cy="71" r="3" fill="#22c55e"/>
    <text x="85" y="74" font-family="Arial, sans-serif" font-size="8" fill="#ffffff">Selección de Tema</text>
    <rect x="25" y="90" width="145" height="26" rx="3" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1"/>
    <text x="30" y="103" font-family="Arial, sans-serif" font-size="8" font-weight="bold" fill="#1e40af">Evaluar 3 opciones</text>
    <text x="30" y="113" font-family="Arial, sans-serif" font-size="7" fill="#2563eb">Puntaje por viabilidad</text>
    <rect x="25" y="122" width="145" height="24" rx="3" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1"/>
    <text x="30" y="135" font-family="Arial, sans-serif" font-size="7.5" font-weight="bold" fill="#065f46">Tema Ganador</text>
    <text x="30" y="144" font-family="Arial, sans-serif" font-size="6.5" fill="#047857">Alineado a línea UTP</text>

    <!-- Bullets Sencillos -->
    <text x="15" y="180" class="card-desc" font-weight="bold" fill="#0f172a">En este paso:</text>
    <text x="15" y="205" class="bullet">• El tesista inicia sesión.</text>
    <text x="15" y="228" class="bullet">• Propone varias ideas.</text>
    <text x="15" y="251" class="bullet">• Compara cuál es viable.</text>
    <text x="15" y="274" class="bullet">• Elige el mejor tema.</text>
    <text x="15" y="297" class="bullet">• Se conecta a un ODS.</text>
    <line x1="15" y1="318" x2="180" y2="318" stroke="#e2e8f0" stroke-width="1"/>
    
    <rect x="15" y="335" width="165" height="95" rx="6" fill="#eff6ff"/>
    <text x="25" y="355" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#1e40af">Lo que logras:</text>
    <text x="25" y="375" font-family="Arial, sans-serif" font-size="10" fill="#334155">Un tema claro y seguro,</text>
    <text x="25" y="392" font-family="Arial, sans-serif" font-size="10" fill="#334155">sin empezar a ciegas ni</text>
    <text x="25" y="409" font-family="Arial, sans-serif" font-size="10" fill="#334155">cambiarlo después.</text>
  </g>

  <!-- Flecha 1 -> 2 -->
  <line x1="590" y1="460" x2="603" y2="460" stroke="#2563eb" stroke-width="2.5" marker-end="url(#arrow)"/>

  <!-- Paso 2: Redacta Paso a Paso -->
  <g transform="translate(605, 235)">
    <rect x="0" y="0" width="195" height="450" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>
    <circle cx="28" cy="28" r="16" fill="#2563eb"/>
    <text x="28" y="34" class="step-num" text-anchor="middle">2</text>
    <text x="55" y="34" class="card-title" font-size="14">Redacta en Orden</text>

    <!-- Mockup Card -->
    <rect x="15" y="60" width="165" height="95" rx="6" fill="#ffffff" stroke="#94a3b8" stroke-width="1"/>
    <rect x="15" y="60" width="165" height="22" rx="6" fill="#1e293b"/>
    <text x="30" y="74" font-family="Arial, sans-serif" font-size="8" fill="#ffffff">Pasos Guiados (P01-P12)</text>
    <rect x="25" y="90" width="145" height="18" rx="3" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1"/>
    <text x="30" y="102" font-family="Arial, sans-serif" font-size="8" font-weight="bold" fill="#065f46">Título delimitado</text>
    <rect x="25" y="112" width="145" height="18" rx="3" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1"/>
    <text x="30" y="124" font-family="Arial, sans-serif" font-size="8" font-weight="bold" fill="#1e40af">Objetivos con Bloom</text>
    <rect x="25" y="133" width="145" height="18" rx="3" fill="#fef3c7" stroke="#fde68a" stroke-width="1"/>
    <text x="30" y="145" font-family="Arial, sans-serif" font-size="8" font-weight="bold" fill="#92400e">Matriz y Variables</text>

    <!-- Bullets Sencillos -->
    <text x="15" y="180" class="card-desc" font-weight="bold" fill="#0f172a">En este paso:</text>
    <text x="15" y="205" class="bullet">• Avanzas en orden estricto.</text>
    <text x="15" y="228" class="bullet">• Planteas el problema.</text>
    <text x="15" y="251" class="bullet">• Escribes las preguntas.</text>
    <text x="15" y="274" class="bullet">• Formulas hipótesis.</text>
    <text x="15" y="297" class="bullet">• Defines tus variables.</text>
    <line x1="15" y1="318" x2="180" y2="318" stroke="#e2e8f0" stroke-width="1"/>
    
    <rect x="15" y="335" width="165" height="95" rx="6" fill="#eff6ff"/>
    <text x="25" y="355" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#1e40af">Lo que logras:</text>
    <text x="25" y="375" font-family="Arial, sans-serif" font-size="10" fill="#334155">Que los objetivos y las</text>
    <text x="25" y="392" font-family="Arial, sans-serif" font-size="10" fill="#334155">preguntas coincidan de</text>
    <text x="25" y="409" font-family="Arial, sans-serif" font-size="10" fill="#334155">forma exacta.</text>
  </g>

  <!-- Flecha 2 -> 3 -->
  <line x1="805" y1="460" x2="818" y2="460" stroke="#2563eb" stroke-width="2.5" marker-end="url(#arrow)"/>

  <!-- Paso 3: Validación Automática -->
  <g transform="translate(820, 235)">
    <rect x="0" y="0" width="195" height="450" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>
    <circle cx="28" cy="28" r="16" fill="#2563eb"/>
    <text x="28" y="34" class="step-num" text-anchor="middle">3</text>
    <text x="55" y="34" class="card-title" font-size="14">Revisión Automática</text>

    <!-- Mockup Card -->
    <rect x="15" y="60" width="165" height="95" rx="6" fill="#ffffff" stroke="#94a3b8" stroke-width="1"/>
    <rect x="15" y="60" width="165" height="22" rx="6" fill="#1e293b"/>
    <text x="30" y="74" font-family="Arial, sans-serif" font-size="8" fill="#ffffff">Filtro Anti-Errores</text>
    <rect x="25" y="90" width="145" height="26" rx="3" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1"/>
    <text x="30" y="103" font-family="Arial, sans-serif" font-size="8" font-weight="bold" fill="#065f46">Cero Datos Inventados</text>
    <text x="30" y="113" font-family="Arial, sans-serif" font-size="7" fill="#047857">Rechazo de textos falsos</text>
    <rect x="25" y="122" width="145" height="26" rx="3" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1"/>
    <text x="30" y="135" font-family="Arial, sans-serif" font-size="7.5" font-weight="bold" fill="#1e40af">Guardado Seguro</text>
    <text x="30" y="145" font-family="Arial, sans-serif" font-size="6.5" fill="#2563eb">No se pierden cambios</text>

    <!-- Bullets Sencillos -->
    <text x="15" y="180" class="card-desc" font-weight="bold" fill="#0f172a">En este paso:</text>
    <text x="15" y="205" class="bullet">• Revisa que nada falte.</text>
    <text x="15" y="228" class="bullet">• Cuida la coherencia.</text>
    <text x="15" y="251" class="bullet">• Impide inventar citas.</text>
    <text x="15" y="274" class="bullet">• Protege contra pérdidas.</text>
    <text x="15" y="297" class="bullet">• Guarda cada versión.</text>
    <line x1="15" y1="318" x2="180" y2="318" stroke="#e2e8f0" stroke-width="1"/>
    
    <rect x="15" y="335" width="165" height="95" rx="6" fill="#eff6ff"/>
    <text x="25" y="355" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#1e40af">Lo que logras:</text>
    <text x="25" y="375" font-family="Arial, sans-serif" font-size="10" fill="#334155">Garantía de que la IA</text>
    <text x="25" y="392" font-family="Arial, sans-serif" font-size="10" fill="#334155">no alucina datos y todo</text>
    <text x="25" y="409" font-family="Arial, sans-serif" font-size="10" fill="#334155">queda respaldado.</text>
  </g>

  <!-- Flecha 3 -> 4 -->
  <line x1="1020" y1="460" x2="1033" y2="460" stroke="#2563eb" stroke-width="2.5" marker-end="url(#arrow)"/>

  <!-- Paso 4: Revisión del Asesor -->
  <g transform="translate(1035, 235)">
    <rect x="0" y="0" width="195" height="450" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>
    <circle cx="28" cy="28" r="16" fill="#2563eb"/>
    <text x="28" y="34" class="step-num" text-anchor="middle">4</text>
    <text x="55" y="34" class="card-title" font-size="14">Revisión Asesor</text>

    <!-- Mockup Card -->
    <rect x="15" y="60" width="165" height="95" rx="6" fill="#ffffff" stroke="#94a3b8" stroke-width="1"/>
    <rect x="15" y="60" width="165" height="22" rx="6" fill="#1e293b"/>
    <text x="30" y="74" font-family="Arial, sans-serif" font-size="8" fill="#ffffff">Comentarios al Margen</text>
    <rect x="25" y="90" width="145" height="18" rx="3" fill="#fef3c7" stroke="#fde68a" stroke-width="1"/>
    <text x="30" y="102" font-family="Arial, sans-serif" font-size="8" font-weight="bold" fill="#92400e">Capítulo en Revisión</text>
    <rect x="25" y="112" width="145" height="36" rx="3" fill="#fee2e2" stroke="#fca5a5" stroke-width="1"/>
    <text x="30" y="125" font-family="Arial, sans-serif" font-size="7.5" font-weight="bold" fill="#991b1b">Párrafo seleccionado:</text>
    <text x="30" y="138" font-family="Arial, sans-serif" font-size="7" fill="#b91c1c">"Alinear con objetivo 2"</text>

    <!-- Bullets Sencillos -->
    <text x="15" y="180" class="card-desc" font-weight="bold" fill="#0f172a">En este paso:</text>
    <text x="15" y="205" class="bullet">• Envías el capítulo listo.</text>
    <text x="15" y="228" class="bullet">• Tu asesor lo examina.</text>
    <text x="15" y="251" class="bullet">• Señala la frase a corregir.</text>
    <text x="15" y="274" class="bullet">• Te explica qué ajustar.</text>
    <text x="15" y="297" class="bullet">• Tú corriges ese punto.</text>
    <line x1="15" y1="318" x2="180" y2="318" stroke="#e2e8f0" stroke-width="1"/>
    
    <rect x="15" y="335" width="165" height="95" rx="6" fill="#eff6ff"/>
    <text x="25" y="355" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#1e40af">Lo que logras:</text>
    <text x="25" y="375" font-family="Arial, sans-serif" font-size="10" fill="#334155">Correcciones precisas,</text>
    <text x="25" y="392" font-family="Arial, sans-serif" font-size="10" fill="#334155">sin confusiones de qué</text>
    <text x="25" y="409" font-family="Arial, sans-serif" font-size="10" fill="#334155">versión se revisó.</text>
  </g>

  <!-- Flecha 4 -> 5 -->
  <line x1="1235" y1="460" x2="1248" y2="460" stroke="#2563eb" stroke-width="2.5" marker-end="url(#arrow)"/>

  <!-- Paso 5: Aprobación y Word -->
  <g transform="translate(1250, 235)">
    <rect x="0" y="0" width="185" height="450" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>
    <circle cx="28" cy="28" r="16" fill="#16a34a"/>
    <text x="28" y="34" class="step-num" text-anchor="middle">5</text>
    <text x="55" y="34" class="card-title" font-size="14">Aprobación / Word</text>

    <!-- Mockup Card -->
    <rect x="15" y="60" width="155" height="95" rx="6" fill="#ffffff" stroke="#94a3b8" stroke-width="1"/>
    <rect x="15" y="60" width="155" height="22" rx="6" fill="#14532d"/>
    <text x="25" y="74" font-family="Arial, sans-serif" font-size="8" fill="#ffffff">Capítulo Aprobado</text>
    <circle cx="77" cy="103" r="13" fill="#dcfce7"/>
    <path d="M 71 103 L 75 107 L 83 98" stroke="#16a34a" stroke-width="2.5" fill="none"/>
    <text x="77" y="128" font-family="Arial, sans-serif" font-size="8.5" font-weight="bold" fill="#166534" text-anchor="middle">APROBADO</text>
    <text x="77" y="142" font-family="Arial, sans-serif" font-size="7" fill="#4b5563" text-anchor="middle">0 observaciones</text>

    <!-- Bullets Sencillos -->
    <text x="15" y="180" class="card-desc" font-weight="bold" fill="#0f172a">En este paso:</text>
    <text x="15" y="205" class="bullet">• Asesor verifica cambios.</text>
    <text x="15" y="228" class="bullet">• Da el visto bueno final.</text>
    <text x="15" y="251" class="bullet">• Se congela esa versión.</text>
    <text x="15" y="274" class="bullet">• Descargas en Word.</text>
    <text x="15" y="297" class="bullet">• Pasas al siguiente tema.</text>
    <line x1="15" y1="318" x2="170" y2="318" stroke="#e2e8f0" stroke-width="1"/>
    
    <rect x="15" y="335" width="155" height="95" rx="6" fill="#dcfce7"/>
    <text x="25" y="355" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#166534">Resultado Final:</text>
    <text x="25" y="375" font-family="Arial, sans-serif" font-size="10" fill="#14532d">Tu borrador listo en</text>
    <text x="25" y="392" font-family="Arial, sans-serif" font-size="10" fill="#14532d">Word editable con el</text>
    <text x="25" y="409" font-family="Arial, sans-serif" font-size="10" fill="#14532d">aval de tu asesor.</text>
  </g>

  <!-- ==================================================================== -->
  <!-- FRANJA INFERIOR: SERVICIOS Y RESULTADO FINAL (x=370, y=730) -->
  <!-- ==================================================================== -->
  <rect x="370" y="730" width="1080" height="290" rx="12" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>

  <!-- Sub-bloque 1: Servicios que ayudan a no inventar datos -->
  <g transform="translate(390, 745)">
    <text x="0" y="20" class="section-badge">BÚSQUEDA CIENTÍFICA REAL</text>
    <text x="0" y="42" class="card-title">Servicios que ayudan a no inventar fuentes</text>

    <!-- Servicio 1: OpenAlex -->
    <rect x="0" y="60" width="160" height="80" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
    <text x="15" y="85" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#0f172a">OpenAlex</text>
    <text x="15" y="103" font-family="Arial, sans-serif" font-size="10" fill="#475569">Millones de artículos</text>
    <text x="15" y="118" font-family="Arial, sans-serif" font-size="10" fill="#475569">científicos de todo el mundo</text>

    <!-- Servicio 2: Semantic Scholar -->
    <rect x="175" y="60" width="160" height="80" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
    <text x="190" y="85" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#0f172a">Semantic Scholar</text>
    <text x="190" y="103" font-family="Arial, sans-serif" font-size="10" fill="#475569">Resúmenes y citas</text>
    <text x="190" y="118" font-family="Arial, sans-serif" font-size="10" fill="#475569">comprobables por internet</text>

    <!-- Servicio 3: ALICIA Concytec -->
    <rect x="350" y="60" width="160" height="80" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
    <text x="365" y="85" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#0f172a">ALICIA CONCYTEC</text>
    <text x="365" y="103" font-family="Arial, sans-serif" font-size="10" fill="#475569">Repositorio oficial de</text>
    <text x="365" y="118" font-family="Arial, sans-serif" font-size="10" fill="#475569">tesis peruanas sustentadas</text>

    <!-- Servicio 4: Conexión Segura MCP -->
    <rect x="525" y="60" width="160" height="80" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
    <text x="540" y="85" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#0f172a">Protocolo MCP</text>
    <text x="540" y="103" font-family="Arial, sans-serif" font-size="10" fill="#475569">Conexión segura entre la</text>
    <text x="540" y="118" font-family="Arial, sans-serif" font-size="10" fill="#475569">pantalla y el asistente de IA</text>
  </g>

  <!-- Sub-bloque 2: Camino de la información -->
  <g transform="translate(390, 905)">
    <text x="0" y="20" class="section-badge">EL CAMINO DE LA INFORMACIÓN</text>
    <line x1="0" y1="30" x2="685" y2="30" stroke="#e2e8f0" stroke-width="1"/>

    <!-- Step A: Pantalla -->
    <rect x="0" y="45" width="150" height="55" rx="6" fill="#1e293b"/>
    <text x="75" y="68" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#ffffff" text-anchor="middle">1. Pantalla del Usuario</text>
    <text x="75" y="85" font-family="Arial, sans-serif" font-size="9" fill="#94a3b8" text-anchor="middle">Tesista escribe o consulta</text>

    <line x1="155" y1="72" x2="185" y2="72" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <!-- Step B: Filtro -->
    <rect x="190" y="45" width="155" height="55" rx="6" fill="#1e293b"/>
    <text x="267" y="68" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#ffffff" text-anchor="middle">2. Filtro de Reglas</text>
    <text x="267" y="85" font-family="Arial, sans-serif" font-size="9" fill="#94a3b8" text-anchor="middle">Revisa que no falte nada</text>

    <line x1="350" y1="72" x2="380" y2="72" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <!-- Step C: Persistencia -->
    <rect x="385" y="45" width="155" height="55" rx="6" fill="#1e3a8a"/>
    <text x="462" y="68" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#ffffff" text-anchor="middle">3. Base de Datos</text>
    <text x="462" y="85" font-family="Arial, sans-serif" font-size="9" fill="#93c5fd" text-anchor="middle">Guarda todo con seguridad</text>

    <line x1="545" y1="72" x2="575" y2="72" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <!-- Step D: Aprobación -->
    <rect x="580" y="45" width="115" height="55" rx="6" fill="#14532d"/>
    <text x="637" y="68" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#ffffff" text-anchor="middle">4. Word Final</text>
    <text x="637" y="85" font-family="Arial, sans-serif" font-size="9" fill="#86efac" text-anchor="middle">Listo para imprimir</text>
  </g>

  <!-- Sub-bloque 3: Resultado Final -->
  <g transform="translate(1100, 745)">
    <rect x="0" y="0" width="330" height="260" rx="10" fill="#0f172a"/>
    <circle cx="165" cy="50" r="26" fill="#16a34a"/>
    <path d="M 153 50 L 161 58 L 177 42" stroke="#ffffff" stroke-width="3.5" fill="none"/>
    <text x="165" y="98" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#ffffff" text-anchor="middle">Resultado del Proyecto</text>
    <text x="165" y="120" font-family="Arial, sans-serif" font-size="12" fill="#38bdf8" text-anchor="middle">TesisMCP (Corte Semana 10)</text>

    <text x="25" y="155" font-family="Arial, sans-serif" font-size="12" fill="#f1f5f9">• Tema, problema y objetivos ordenados</text>
    <text x="25" y="180" font-family="Arial, sans-serif" font-size="12" fill="#f1f5f9">• Variables con indicadores claros</text>
    <text x="25" y="205" font-family="Arial, sans-serif" font-size="12" fill="#f1f5f9">• Correcciones del asesor registradas</text>
    <text x="25" y="230" font-family="Arial, sans-serif" font-size="12" fill="#f1f5f9">• Borrador listo en Microsoft Word</text>
  </g>

  <!-- ==================================================================== -->
  <!-- COLUMNA 3: NARRATIVA DE SUSTENTACIÓN (Derecha, w=410) -->
  <!-- ==================================================================== -->
  <rect x="1470" y="135" width="420" height="885" rx="12" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)"/>
  <rect x="1470" y="135" width="420" height="55" rx="12" fill="#1e293b"/>
  <text x="1495" y="170" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="#ffffff">GUÍA NARRATIVA (PARA EXPOSICIÓN)</text>

  <g transform="translate(1495, 215)">
    <text x="0" y="10" class="narrative-title">Cómo explicarlo al profesor:</text>

    <!-- Tarjeta de Discurso Sencillo -->
    <rect x="0" y="25" width="370" height="340" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
    <text x="15" y="55" class="narrative-p font-italic" font-weight="bold" fill="#1e40af">“En palabras sencillas...”</text>

    <text x="15" y="85" class="narrative-p">“En esta diapositiva mostramos cómo funciona</text>
    <text x="15" y="107" class="narrative-p">TesisMCP de manera muy clara y sencilla:</text>
    <text x="15" y="137" class="narrative-p">1. Primero, el tesista ingresa y evalúa varias</text>
    <text x="15" y="159" class="narrative-p">ideas hasta elegir un tema sólido y viable.</text>
    <text x="15" y="189" class="narrative-p">2. Luego redacta paso a paso su proyecto:</text>
    <text x="15" y="211" class="narrative-p">título, problema, objetivos y variables, sin</text>
    <text x="15" y="233" class="narrative-p">saltarse etapas para evitar el desorden.</text>
    <text x="15" y="263" class="narrative-p">3. El sistema valida automáticamente que no</text>
    <text x="15" y="285" class="narrative-p">falten datos ni se invente información.</text>
    <text x="15" y="315" class="narrative-p">4. Al terminar el capítulo, el asesor lo revisa</text>
    <text x="15" y="337" class="narrative-p">y señala los párrafos exactos a corregir.</text>
    <text x="15" y="367" class="narrative-p">5. Una vez subsanado, el asesor aprueba y</text>
    <text x="15" y="389" class="narrative-p">el tesista descarga su borrador en Word.”</text>

    <!-- Tarjeta de Puntos Clave Sencillos -->
    <text x="0" y="420" class="narrative-title">Beneficios clave para la tesis:</text>

    <rect x="0" y="435" width="370" height="215" rx="8" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1"/>

    <text x="15" y="460" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1e3a8a">1. Adiós a la tesis de un solo golpe:</text>
    <text x="15" y="480" font-family="Arial, sans-serif" font-size="11" fill="#334155">Dividir el trabajo en pasos evita que el alumno</text>
    <text x="15" y="497" font-family="Arial, sans-serif" font-size="11" fill="#334155">se abrume y asegura calidad metodológica.</text>

    <text x="15" y="525" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1e3a8a">2. Fuentes científicas de verdad:</text>
    <text x="15" y="545" font-family="Arial, sans-serif" font-size="11" fill="#334155">Búsquedas en catálogos abiertos reales para</text>
    <text x="15" y="562" font-family="Arial, sans-serif" font-size="11" fill="#334155">no inventar autores ni enlaces caídos.</text>

    <text x="15" y="590" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1e3a8a">3. Correcciones sin perderse:</text>
    <text x="15" y="610" font-family="Arial, sans-serif" font-size="11" fill="#334155">Cada observación queda guardada con el texto</text>
    <text x="15" y="627" font-family="Arial, sans-serif" font-size="11" fill="#334155">que la originó, sin confusiones de versiones.</text>
  </g>

    <text x="15" y="565" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1e3a8a">3. Auditoría de Solo Anexado:</text>
    <text x="15" y="585" font-family="Arial, sans-serif" font-size="11" fill="#334155">PostgreSQL protege con disparadores nativos</text>
    <text x="15" y="602" font-family="Arial, sans-serif" font-size="11" fill="#334155">el historial completo de correcciones docentes.</text>
  </g>
</svg>
"""

with open(SLIDE1_SVG, "w", encoding="utf-8") as f:
    f.write(slide1_svg)
print(f"SVG Diapositiva 01 generado: {SLIDE1_SVG}")

# Renderizar a PNG de alta resolución 1920x1080 vía Chrome Headless
TMP_HTML1 = "/tmp/slide1_render.html"
with open(TMP_HTML1, "w", encoding="utf-8") as f:
    f.write(f"<!DOCTYPE html><html><body style='margin:0;background:#f1f5f9;'>{slide1_svg}</body></html>")

subprocess.run([
    "google-chrome", "--headless", "--disable-gpu", "--force-device-scale-factor=1",
    f"--screenshot={SLIDE1_PNG}", "--window-size=1920,1080", "--default-background-color=f1f5f9",
    f"file://{TMP_HTML1}"
], check=True)

img1 = Image.open(SLIDE1_PNG)
img1.save(SLIDE1_PNG, optimize=True)
print(f"PNG Diapositiva 01 generado: {SLIDE1_PNG} ({os.path.getsize(SLIDE1_PNG)//1024} KB)")

# Generar Draw.io XML para Diapositiva 1
mxfile1 = ET.Element("mxfile", host="Electron", agent="Antigravity", version="21.6.8", type="device")
diag1 = ET.SubElement(mxfile1, "diagram", id="diag_slide1", name="Funcion_Plataforma_TesisMCP")
model1 = ET.SubElement(diag1, "mxGraphModel", dx="1920", dy="1080", grid="1", gridSize="10",
                        guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1",
                        pageScale="1", pageWidth="1920", pageHeight="1080", math="0", shadow="0")
root1 = ET.SubElement(model1, "root")
ET.SubElement(root1, "mxCell", id="0")
ET.SubElement(root1, "mxCell", id="1", parent="0")

banner = ET.SubElement(root1, "mxCell", id="banner", parent="1", value="<b>FUNCIÓN DE LA PLATAFORMA</b><br/>TesisMCP — Asistencia Metodológica y Supervisión Continua", vertex="1",
                       style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0f172a;fontColor=#ffffff;fontSize=18;align=left;spacingLeft=30;")
ET.SubElement(banner, "mxGeometry", x="30", y="25", width="1860", height="90", as_="geometry")

tree1 = ET.ElementTree(mxfile1)
ET.indent(tree1, space="  ", level=0)
tree1.write(SLIDE1_DRAWIO, encoding="utf-8", xml_declaration=True)
print(f"Draw.io Diapositiva 01 generado: {SLIDE1_DRAWIO}")


# ==============================================================================
# 2. DIAPOSITIVA 02: ARQUITECTURA MVC / MVT CON HERRAMIENTAS REALES (TIPO NETFLIX)
# ==============================================================================
SLIDE2_SVG = os.path.join(OUT_DIR, "diapositiva_02_arquitectura_mvc.svg")
SLIDE2_PNG = os.path.join(OUT_DIR, "diapositiva_02_arquitectura_mvc.png")
SLIDE2_DRAWIO = os.path.join(OUT_DIR, "diapositiva_02_arquitectura_mvc.drawio")

slide2_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">
  <defs>
    <linearGradient id="headerGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <filter id="shadow2" x="-5%" y="-5%" width="110%" height="115%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.07"/>
    </filter>
    <marker id="arrow2" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#0284c7"/>
    </marker>
    <marker id="arrowGray" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#64748b"/>
    </marker>
    <marker id="arrowGreen" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#10b981"/>
    </marker>
    <style>
      .main-title { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 34px; font-weight: 900; fill: #ffffff; letter-spacing: 0.05em; }
      .sub-title { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; fill: #94a3b8; font-weight: 500; }
      .col-header { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 19px; font-weight: 800; fill: #ffffff; letter-spacing: 0.03em; }
      .col-sub { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 12px; font-weight: 600; }
      .card-box { fill: #ffffff; stroke: #e2e8f0; stroke-width: 1.5; rx: 12; }
      .tool-title { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 16px; font-weight: 800; fill: #0f172a; }
      .tool-desc { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 12.5px; fill: #475569; line-height: 1.45; }
      .pill-tech { rx: 6; }
      .pill-txt { font-family: monospace; font-size: 11px; font-weight: 700; }
      .badge-code { fill: #f1f5f9; stroke: #cbd5e1; stroke-width: 1; rx: 4; }
      .badge-txt { font-family: monospace; font-size: 11px; fill: #334155; font-weight: 600; }
      .flow-label { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 11px; font-weight: 800; text-anchor: middle; }
    </style>
  </defs>

  <!-- Fondo General Limpio y Espacioso -->
  <rect x="0" y="0" width="1920" height="1080" fill="#f8fafc"/>

  <!-- BANNER SUPERIOR ELEGANTE -->
  <rect x="40" y="25" width="1840" height="90" rx="14" fill="url(#headerGrad2)" filter="url(#shadow2)"/>
  <rect x="65" y="48" width="44" height="44" rx="10" fill="#0284c7"/>
  <text x="87" y="78" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="#ffffff" text-anchor="middle">🏛️</text>
  <text x="130" y="64" class="main-title">ARQUITECTURA DE SOFTWARE: PATRÓN MODELO-VISTA-CONTROLADOR (MVC)</text>
  <text x="130" y="92" class="sub-title">TesisMCP — Ecosistema Tecnológico por Capas y Herramientas Reales de Implementación</text>
  <rect x="1630" y="48" width="225" height="44" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1"/>
  <text x="1742" y="75" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#38bdf8" text-anchor="middle">Semana 09 • Curso Integrador I</text>

  <!-- COLUMNA 1: VISTA (VIEW / INTERFAZ DE USUARIO) -->
  <rect x="50" y="135" width="540" height="730" rx="16" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow2)"/>
  <rect x="50" y="135" width="540" height="65" rx="16" fill="#0284c7"/>
  <rect x="50" y="175" width="540" height="25" fill="#0284c7"/>
  <text x="80" y="175" class="col-header">1. VISTA (View / Interfaz)</text>
  <text x="560" y="175" class="col-sub" fill="#e0f2fe" text-anchor="end">Capa de Presentación</text>

  <!-- Card V1: Claude Desktop / Antigravity IDE -->
  <g transform="translate(75, 220)">
    <rect x="0" y="0" width="490" height="145" class="card-box"/>
    <rect x="20" y="20" width="44" height="44" rx="10" fill="#e0f2fe"/>
    <text x="42" y="48" font-family="Arial, sans-serif" font-size="22" text-anchor="middle">💻</text>
    <text x="78" y="38" class="tool-title">Claude Desktop / Antigravity</text>
    <rect x="78" y="46" width="135" height="20" fill="#eff6ff" stroke="#bfdbfe" class="pill-tech"/>
    <text x="145" y="60" class="pill-txt" fill="#1d4ed8" text-anchor="middle">Cliente MCP Nativo</text>
    <text x="20" y="92" class="tool-desc">Interfaz conversacional donde el tesista redacta los pasos P01 a P12</text>
    <text x="20" y="110" class="tool-desc">con asistencia inteligente y retroalimentación metodológica en vivo.</text>
    <rect x="20" y="120" width="210" height="18" class="badge-code"/>
    <text x="28" y="133" class="badge-txt">Protocolo: stdio (JSON-RPC 2.0)</text>
  </g>

  <!-- Card V2: Django Admin Dashboard -->
  <g transform="translate(75, 385)">
    <rect x="0" y="0" width="490" height="145" class="card-box"/>
    <rect x="20" y="20" width="44" height="44" rx="10" fill="#fef3c7"/>
    <text x="42" y="48" font-family="Arial, sans-serif" font-size="22" text-anchor="middle">📋</text>
    <text x="78" y="38" class="tool-title">Django Admin Dashboard</text>
    <rect x="78" y="46" width="155" height="20" fill="#fffbeb" stroke="#fde68a" class="pill-tech"/>
    <text x="155" y="60" class="pill-txt" fill="#b45309" text-anchor="middle">Panel Web del Asesor</text>
    <text x="20" y="92" class="tool-desc">Portal de supervisión para el docente asesor. Permite revisar borradores,</text>
    <text x="20" y="110" class="tool-desc">auditar el historial de revisiones y registrar observaciones oficiales.</text>
    <rect x="20" y="120" width="235" height="18" class="badge-code"/>
    <text x="28" y="133" class="badge-txt">Tecnología: HTML5 + Django Templates</text>
  </g>

  <!-- Card V3: Swagger / OpenAPI UI -->
  <g transform="translate(75, 550)">
    <rect x="0" y="0" width="490" height="145" class="card-box"/>
    <rect x="20" y="20" width="44" height="44" rx="10" fill="#dcfce7"/>
    <text x="42" y="48" font-family="Arial, sans-serif" font-size="22" text-anchor="middle">⚡</text>
    <text x="78" y="38" class="tool-title">Swagger UI / OpenAPI 3.0</text>
    <rect x="78" y="46" width="150" height="20" fill="#f0fdf4" stroke="#bbf7d0" class="pill-tech"/>
    <text x="153" y="60" class="pill-txt" fill="#15803d" text-anchor="middle">Documentación REST</text>
    <text x="20" y="92" class="tool-desc">Documentación interactiva de la API para pruebas, consumo externo</text>
    <text x="20" y="110" class="tool-desc">y descarga directa del documento de tesis en formato Word (.docx).</text>
    <rect x="20" y="120" width="195" height="18" class="badge-code"/>
    <text x="28" y="133" class="badge-txt">Ruta: /api/v1/docs (OpenAPI)</text>
  </g>

  <!-- Resumen Limpio Capa Vista -->
  <g transform="translate(75, 715)">
    <rect x="0" y="0" width="490" height="125" rx="10" fill="#f0f9ff" stroke="#bae6fd" stroke-width="1"/>
    <text x="20" y="28" font-family="Arial, sans-serif" font-size="13.5" font-weight="bold" fill="#0369a1">Propósito de la Vista:</text>
    <text x="20" y="52" class="tool-desc">• Captura requerimientos e interacción directa del estudiante y profesor.</text>
    <text x="20" y="72" class="tool-desc">• Cero lógica de negocio incrustada (garantiza desacoplamiento limpio).</text>
    <text x="20" y="92" class="tool-desc">• Comunica acciones al Controlador mediante mensajes estandarizados.</text>
  </g>

  <!-- FLECHAS DE CONEXIÓN VISTA -> CONTROLADOR -->
  <line x1="595" y1="350" x2="685" y2="350" stroke="#0284c7" stroke-width="3" marker-end="url(#arrow2)"/>
  <rect x="605" y="322" width="70" height="20" rx="4" fill="#ffffff" stroke="#0284c7" stroke-width="1.2"/>
  <text x="640" y="336" class="flow-label" fill="#0284c7">Petición</text>

  <line x1="685" y1="430" x2="595" y2="430" stroke="#64748b" stroke-width="2.5" stroke-dasharray="6,4" marker-end="url(#arrowGray)"/>
  <rect x="605" y="438" width="70" height="20" rx="4" fill="#ffffff" stroke="#64748b" stroke-width="1.2"/>
  <text x="640" y="452" class="flow-label" fill="#64748b">Respuesta</text>

  <!-- COLUMNA 2: CONTROLADOR (CONTROLLER / ORQUESTACIÓN) -->
  <rect x="690" y="135" width="540" height="730" rx="16" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow2)"/>
  <rect x="690" y="135" width="540" height="65" rx="16" fill="#1e293b"/>
  <rect x="690" y="175" width="540" height="25" fill="#1e293b"/>
  <text x="720" y="175" class="col-header">2. CONTROLADOR (Controller)</text>
  <text x="1200" y="175" class="col-sub" fill="#38bdf8" text-anchor="end">Capa de Orquestación</text>

  <!-- Card C1: FastMCP Server -->
  <g transform="translate(715, 220)">
    <rect x="0" y="0" width="490" height="145" class="card-box"/>
    <rect x="20" y="20" width="44" height="44" rx="10" fill="#f1f5f9"/>
    <text x="42" y="48" font-family="Arial, sans-serif" font-size="22" text-anchor="middle">⚙️</text>
    <text x="78" y="38" class="tool-title">Servidor FastMCP (Python)</text>
    <rect x="78" y="46" width="155" height="20" fill="#f8fafc" stroke="#cbd5e1" class="pill-tech"/>
    <text x="155" y="60" class="pill-txt" fill="#0f172a" text-anchor="middle">FastMCP Protocol SDK</text>
    <text x="20" y="92" class="tool-desc">Publica y despacha 17 herramientas y 15 prompts oficiales de tesis.</text>
    <text x="20" y="110" class="tool-desc">Deserializa payloads JSON-RPC y coordina los servicios de dominio.</text>
    <rect x="20" y="120" width="240" height="18" class="badge-code"/>
    <text x="28" y="133" class="badge-txt">Herramientas: guardar_paso, observar...</text>
  </g>

  <!-- Card C2: Django Ninja REST API -->
  <g transform="translate(715, 385)">
    <rect x="0" y="0" width="490" height="145" class="card-box"/>
    <rect x="20" y="20" width="44" height="44" rx="10" fill="#fee2e2"/>
    <text x="42" y="48" font-family="Arial, sans-serif" font-size="22" text-anchor="middle">🚀</text>
    <text x="78" y="38" class="tool-title">Django Ninja API Routers</text>
    <rect x="78" y="46" width="155" height="20" fill="#fef2f2" stroke="#fca5a5" class="pill-tech"/>
    <text x="155" y="60" class="pill-txt" fill="#991b1b" text-anchor="middle">Controlador HTTP REST</text>
    <text x="20" y="92" class="tool-desc">Rutas asíncronas de alto rendimiento con validación estricta de tipos.</text>
    <text x="20" y="110" class="tool-desc">Conecta las peticiones web con los servicios de lógica de negocio.</text>
    <rect x="20" y="120" width="225" height="18" class="badge-code"/>
    <text x="28" y="133" class="badge-txt">Framework: Django Ninja (Type-Hinted)</text>
  </g>

  <!-- Card C3: Módulo de Seguridad SHA-256 -->
  <g transform="translate(715, 550)">
    <rect x="0" y="0" width="490" height="145" class="card-box"/>
    <rect x="20" y="20" width="44" height="44" rx="10" fill="#fef3c7"/>
    <text x="42" y="48" font-family="Arial, sans-serif" font-size="22" text-anchor="middle">🛡️</text>
    <text x="78" y="38" class="tool-title">Seguridad &amp; Token Auth</text>
    <rect x="78" y="46" width="160" height="20" fill="#fffbeb" stroke="#fde68a" class="pill-tech"/>
    <text x="158" y="60" class="pill-txt" fill="#92400e" text-anchor="middle">TokenResolver SHA-256</text>
    <text x="20" y="92" class="tool-desc">Valida la identidad de cada petición antes de despachar a los servicios.</text>
    <text x="20" y="110" class="tool-desc">Distingue entre Tesista y Docente Asesor; cero tokens en texto plano.</text>
    <rect x="20" y="120" width="235" height="18" class="badge-code"/>
    <text x="28" y="133" class="badge-txt">Seguridad: Hash criptográfico SHA-256</text>
  </g>

  <!-- Resumen Limpio Capa Controlador -->
  <g transform="translate(715, 715)">
    <rect x="0" y="0" width="490" height="125" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
    <text x="20" y="28" font-family="Arial, sans-serif" font-size="13.5" font-weight="bold" fill="#0f172a">Propósito del Controlador:</text>
    <text x="20" y="52" class="tool-desc">• El policía de tráfico: valida permisos y orquesta el flujo del sistema.</text>
    <text x="20" y="72" class="tool-desc">• Desacopla la vista de la base de datos (evita accesos directos inseguros).</text>
    <text x="20" y="92" class="tool-desc">• Convierte entradas JSON en objetos de dominio fuertemente tipados.</text>
  </g>

  <!-- FLECHAS DE CONEXIÓN CONTROLADOR -> MODELO -->
  <line x1="1235" y1="350" x2="1325" y2="350" stroke="#059669" stroke-width="3" marker-end="url(#arrowGreen)"/>
  <rect x="1245" y="322" width="70" height="20" rx="4" fill="#ffffff" stroke="#059669" stroke-width="1.2"/>
  <text x="1280" y="336" class="flow-label" fill="#059669">Servicios</text>

  <line x1="1325" y1="430" x2="1235" y2="430" stroke="#64748b" stroke-width="2.5" stroke-dasharray="6,4" marker-end="url(#arrowGray)"/>
  <rect x="1245" y="438" width="70" height="20" rx="4" fill="#ffffff" stroke="#64748b" stroke-width="1.2"/>
  <text x="1280" y="452" class="flow-label" fill="#64748b">Datos DAO</text>

  <!-- COLUMNA 3: MODELO (MODEL / NEGOCIO Y PERSISTENCIA) -->
  <rect x="1330" y="135" width="540" height="730" rx="16" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow2)"/>
  <rect x="1330" y="135" width="540" height="65" rx="16" fill="#059669"/>
  <rect x="1330" y="175" width="540" height="25" fill="#059669"/>
  <text x="1360" y="175" class="col-header">3. MODELO (Model / Negocio y Datos)</text>
  <text x="1840" y="175" class="col-sub" fill="#bbf7d0" text-anchor="end">Capa de Dominio y Persistencia</text>

  <!-- Card M1: Pydantic v2 & Dominio -->
  <g transform="translate(1355, 220)">
    <rect x="0" y="0" width="490" height="145" class="card-box"/>
    <rect x="20" y="20" width="44" height="44" rx="10" fill="#dcfce7"/>
    <text x="42" y="48" font-family="Arial, sans-serif" font-size="22" text-anchor="middle">🔬</text>
    <text x="78" y="38" class="tool-title">Dominio &amp; Contratos Pydantic 2</text>
    <rect x="78" y="46" width="165" height="20" fill="#f0fdf4" stroke="#bbf7d0" class="pill-tech"/>
    <text x="160" y="60" class="pill-txt" fill="#15803d" text-anchor="middle">Contratos extra='forbid'</text>
    <text x="20" y="92" class="tool-desc">El cerebro metodológico. Valida verbos Bloom, recuento de palabras,</text>
    <text x="20" y="110" class="tool-desc">coherencia de variables de investigación y máquina de estados del borrador.</text>
    <rect x="20" y="120" width="245" height="18" class="badge-code"/>
    <text x="28" y="133" class="badge-txt">Módulos: thesis.services + contracts.py</text>
  </g>

  <!-- Card M2: Django ORM (DAO) -->
  <g transform="translate(1355, 385)">
    <rect x="0" y="0" width="490" height="145" class="card-box"/>
    <rect x="20" y="20" width="44" height="44" rx="10" fill="#e0f2fe"/>
    <text x="42" y="48" font-family="Arial, sans-serif" font-size="22" text-anchor="middle">🔄</text>
    <text x="78" y="38" class="tool-title">Acceso a Datos (Django ORM)</text>
    <rect x="78" y="46" width="155" height="20" fill="#eff6ff" stroke="#bfdbfe" class="pill-tech"/>
    <text x="155" y="60" class="pill-txt" fill="#0369a1" text-anchor="middle">Patrón DAO (Data Access)</text>
    <text x="20" y="92" class="tool-desc">Puente objeto-relacional entre Python y PostgreSQL. Aísla las consultas SQL,</text>
    <text x="20" y="110" class="tool-desc">soporta transacciones atómicas y control de concurrencia optimista.</text>
    <rect x="20" y="120" width="255" height="18" class="badge-code"/>
    <text x="28" y="133" class="badge-txt">Modelos: Proyecto, Revision, Capitulo...</text>
  </g>

  <!-- Card M3: PostgreSQL 16 & Triggers -->
  <g transform="translate(1355, 550)">
    <rect x="0" y="0" width="490" height="145" class="card-box"/>
    <rect x="20" y="20" width="44" height="44" rx="10" fill="#ede9fe"/>
    <text x="42" y="48" font-family="Arial, sans-serif" font-size="22" text-anchor="middle">🐘</text>
    <text x="78" y="38" class="tool-title">Base de Datos PostgreSQL 16</text>
    <rect x="78" y="46" width="165" height="20" fill="#f5f3ff" stroke="#ddd6fe" class="pill-tech"/>
    <text x="160" y="60" class="pill-txt" fill="#6d28d9" text-anchor="middle">17 Tablas Físicas ACID</text>
    <text x="20" y="92" class="tool-desc">Almacén normalizado en 3NF. Incluye triggers PL/pgSQL que impiden</text>
    <text x="20" y="110" class="tool-desc">borrar o alterar revisiones pasadas, garantizando inmutabilidad total.</text>
    <rect x="20" y="120" width="265" height="18" class="badge-code"/>
    <text x="28" y="133" class="badge-txt">Trigger: tg_proteger_revision_capitulo</text>
  </g>

  <!-- Resumen Limpio Capa Modelo -->
  <g transform="translate(1355, 715)">
    <rect x="0" y="0" width="490" height="125" rx="10" fill="#f0fdf4" stroke="#bbf7d0" stroke-width="1"/>
    <text x="20" y="28" font-family="Arial, sans-serif" font-size="13.5" font-weight="bold" fill="#15803d">Propósito del Modelo:</text>
    <text x="20" y="52" class="tool-desc">• Aplica las reglas académicas estrictas (cero datos inventados o alucinados).</text>
    <text x="20" y="72" class="tool-desc">• Administra el estado de aprobación del borrador (Borrador ➔ Aprobado).</text>
    <text x="20" y="92" class="tool-desc">• Protege la trazabilidad histórica de observaciones para la sustentación.</text>
  </g>

  <!-- BARRA INFERIOR MODERNA: INFRAESTRUCTURA, CALIDAD Y PRINCIPIOS (SEMANA 9) -->
  <rect x="40" y="885" width="1840" height="160" rx="14" fill="#0f172a" filter="url(#shadow2)"/>

  <g transform="translate(65, 905)">
    <text x="0" y="18" font-family="Arial, sans-serif" font-size="13.5" font-weight="bold" fill="#38bdf8">PRINCIPIOS Y TECNOLOGÍAS TRANSVERSALES DE LA ARQUITECTURA (SEMANA 09):</text>

    <!-- Card Dock 1: MVC / MVT -->
    <rect x="0" y="32" width="425" height="85" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1"/>
    <text x="16" y="56" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#38bdf8">1. Arquitectura MVC / MVT</text>
    <text x="16" y="76" font-family="Arial, sans-serif" font-size="11.5" fill="#cbd5e1">Separación estricta de capas. La vista nunca</text>
    <text x="16" y="94" font-family="Arial, sans-serif" font-size="11.5" fill="#cbd5e1">toca la BD; el controlador orquesta y el modelo valida.</text>

    <!-- Card Dock 2: DAO & PostgreSQL -->
    <rect x="455" y="32" width="425" height="85" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1"/>
    <text x="471" y="56" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#38bdf8">2. Patrón DAO (Acceso a Datos)</text>
    <text x="471" y="76" font-family="Arial, sans-serif" font-size="11.5" fill="#cbd5e1">Aísla el motor de base de datos. Si se migra</text>
    <text x="471" y="94" font-family="Arial, sans-serif" font-size="11.5" fill="#cbd5e1">de motor, los contratos del tesista permanecen intactos.</text>

    <!-- Card Dock 3: TDD & pytest -->
    <rect x="910" y="32" width="425" height="85" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1"/>
    <text x="926" y="56" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#38bdf8">3. Metodología TDD &amp; Pytest</text>
    <text x="926" y="76" font-family="Arial, sans-serif" font-size="11.5" fill="#cbd5e1">Desarrollo guiado por pruebas: 32 tests de integración</text>
    <text x="926" y="94" font-family="Arial, sans-serif" font-size="11.5" fill="#cbd5e1">garantizan 100% de fiabilidad en cada hito.</text>

    <!-- Card Dock 4: SOLID & Docker -->
    <rect x="1365" y="32" width="425" height="85" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1"/>
    <text x="1381" y="56" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#38bdf8">4. Principios SOLID &amp; Docker</text>
    <text x="1381" y="76" font-family="Arial, sans-serif" font-size="11.5" fill="#cbd5e1">Responsabilidad única por servicio, modularidad extensible</text>
    <text x="1381" y="94" font-family="Arial, sans-serif" font-size="11.5" fill="#cbd5e1">y empaquetado en contenedores portables.</text>
  </g>
</svg>"""

with open(SLIDE2_SVG, "w", encoding="utf-8") as f:
    f.write(slide2_svg)
print(f"SVG Diapositiva 02 generado: {SLIDE2_SVG}")

# Renderizar a PNG de alta resolución 1920x1080 vía Chrome Headless
TMP_HTML2 = "/tmp/slide2_render.html"
with open(TMP_HTML2, "w", encoding="utf-8") as f:
    f.write(f"<!DOCTYPE html><html><body style='margin:0;background:#f8fafc;'>{slide2_svg}</body></html>")

subprocess.run([
    "google-chrome", "--headless", "--disable-gpu", "--force-device-scale-factor=1",
    f"--screenshot={SLIDE2_PNG}", "--window-size=1920,1080", "--default-background-color=f8fafc",
    f"file://{TMP_HTML2}"
], check=True)

img2 = Image.open(SLIDE2_PNG)
img2.save(SLIDE2_PNG, optimize=True)
print(f"PNG Diapositiva 02 generado: {SLIDE2_PNG} ({os.path.getsize(SLIDE2_PNG)//1024} KB)")

# Generar Draw.io XML enriquecido para Diapositiva 2
mxfile2 = ET.Element("mxfile", host="Electron", agent="Antigravity", version="21.6.8", type="device")
diag2 = ET.SubElement(mxfile2, "diagram", id="diag_slide2", name="Arquitectura_MVC_TesisMCP")
model2 = ET.SubElement(diag2, "mxGraphModel", dx="1920", dy="1080", grid="1", gridSize="10",
                        guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1",
                        pageScale="1", pageWidth="1920", pageHeight="1080", math="0", shadow="0")
root2 = ET.SubElement(model2, "root")
ET.SubElement(root2, "mxCell", id="0")
ET.SubElement(root2, "mxCell", id="1", parent="0")

# Banner
banner2 = ET.SubElement(root2, "mxCell", id="banner2", parent="1",
                        value="<b>ARQUITECTURA DE SOFTWARE: PATRÓN MODELO-VISTA-CONTROLADOR (MVC)</b><br/>TesisMCP — Ecosistema Tecnológico por Capas y Herramientas Reales (Semana 09)",
                        vertex="1",
                        style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0f172a;fontColor=#ffffff;fontSize=18;align=left;spacingLeft=30;")
ET.SubElement(banner2, "mxGeometry", x="40", y="25", width="1840", height="90", as_="geometry")

# Col 1: Vista
col1 = ET.SubElement(root2, "mxCell", id="col1", parent="1",
                    value="<b>1. VISTA (View / Interfaz)</b><br/><font color='#e0f2fe'>Capa de Presentación</font>",
                    vertex="1",
                    style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0284c7;fontColor=#ffffff;fontSize=15;align=center;verticalAlign=top;spacingTop=10;")
ET.SubElement(col1, "mxGeometry", x="50", y="135", width="540", height="730", as_="geometry")

# Cards Vista
v1 = ET.SubElement(root2, "mxCell", id="v1", parent="col1",
                   value="<b>Claude Desktop / Antigravity</b><br/><i>Cliente MCP Nativo (JSON-RPC stdio)</i><br/>Interfaz conversacional de redacción guiada P01-P12",
                   vertex="1",
                   style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#cbd5e1;fontColor=#0f172a;fontSize=12;align=left;spacingLeft=15;")
ET.SubElement(v1, "mxGeometry", x="25", y="85", width="490", height="145", as_="geometry")

v2 = ET.SubElement(root2, "mxCell", id="v2", parent="col1",
                   value="<b>Django Admin Dashboard</b><br/><i>Panel Web del Asesor (HTML5)</i><br/>Portal de supervisión para auditar avances y dejar observaciones",
                   vertex="1",
                   style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#cbd5e1;fontColor=#0f172a;fontSize=12;align=left;spacingLeft=15;")
ET.SubElement(v2, "mxGeometry", x="25", y="250", width="490", height="145", as_="geometry")

v3 = ET.SubElement(root2, "mxCell", id="v3", parent="col1",
                   value="<b>Swagger UI / OpenAPI 3.0</b><br/><i>Documentación REST (/api/v1/docs)</i><br/>Endpoints interactivos para pruebas y exportación a Word (.docx)",
                   vertex="1",
                   style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#cbd5e1;fontColor=#0f172a;fontSize=12;align=left;spacingLeft=15;")
ET.SubElement(v3, "mxGeometry", x="25", y="415", width="490", height="145", as_="geometry")

# Col 2: Controlador
col2 = ET.SubElement(root2, "mxCell", id="col2", parent="1",
                    value="<b>2. CONTROLADOR (Controller)</b><br/><font color='#38bdf8'>Capa de Orquestación</font>",
                    vertex="1",
                    style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;fontColor=#ffffff;fontSize=15;align=center;verticalAlign=top;spacingTop=10;")
ET.SubElement(col2, "mxGeometry", x="690", y="135", width="540", height="730", as_="geometry")

c1 = ET.SubElement(root2, "mxCell", id="c1", parent="col2",
                   value="<b>Servidor FastMCP (Python)</b><br/><i>FastMCP Protocol Engine</i><br/>Despacha 17 herramientas y 15 prompts oficiales de tesis",
                   vertex="1",
                   style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#cbd5e1;fontColor=#0f172a;fontSize=12;align=left;spacingLeft=15;")
ET.SubElement(c1, "mxGeometry", x="25", y="85", width="490", height="145", as_="geometry")

c2 = ET.SubElement(root2, "mxCell", id="c2", parent="col2",
                   value="<b>Django Ninja REST API</b><br/><i>Controlador HTTP REST Asíncrono</i><br/>Rutas con tipado estricto (/api/v1/) para proyectos y capítulos",
                   vertex="1",
                   style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#cbd5e1;fontColor=#0f172a;fontSize=12;align=left;spacingLeft=15;")
ET.SubElement(c2, "mxGeometry", x="25", y="250", width="490", height="145", as_="geometry")

c3 = ET.SubElement(root2, "mxCell", id="c3", parent="col2",
                   value="<b>Módulo de Seguridad SHA-256</b><br/><i>TokenResolver y Permisos</i><br/>Resuelve identidad del tesista y asesor antes de despachar",
                   vertex="1",
                   style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#cbd5e1;fontColor=#0f172a;fontSize=12;align=left;spacingLeft=15;")
ET.SubElement(c3, "mxGeometry", x="25", y="415", width="490", height="145", as_="geometry")

# Col 3: Modelo
col3 = ET.SubElement(root2, "mxCell", id="col3", parent="1",
                    value="<b>3. MODELO (Model / Negocio y Datos)</b><br/><font color='#bbf7d0'>Capa de Dominio y Persistencia</font>",
                    vertex="1",
                    style="rounded=1;whiteSpace=wrap;html=1;fillColor=#059669;fontColor=#ffffff;fontSize=15;align=center;verticalAlign=top;spacingTop=10;")
ET.SubElement(col3, "mxGeometry", x="1330", y="135", width="540", height="730", as_="geometry")

m1 = ET.SubElement(root2, "mxCell", id="m1", parent="col3",
                   value="<b>Dominio & Contratos Pydantic 2</b><br/><i>Contratos extra='forbid'</i><br/>Valida verbos Bloom, conteo de palabras y consistencia metodológica",
                   vertex="1",
                   style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#cbd5e1;fontColor=#0f172a;fontSize=12;align=left;spacingLeft=15;")
ET.SubElement(m1, "mxGeometry", x="25", y="85", width="490", height="145", as_="geometry")

m2 = ET.SubElement(root2, "mxCell", id="m2", parent="col3",
                   value="<b>Acceso a Datos (Django ORM)</b><br/><i>Patrón DAO (Data Access Object)</i><br/>Aísla consultas SQL y gestiona transacciones atómicas seguras",
                   vertex="1",
                   style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#cbd5e1;fontColor=#0f172a;fontSize=12;align=left;spacingLeft=15;")
ET.SubElement(m2, "mxGeometry", x="25", y="250", width="490", height="145", as_="geometry")

m3 = ET.SubElement(root2, "mxCell", id="m3", parent="col3",
                   value="<b>Base de Datos PostgreSQL 16</b><br/><i>17 Tablas Físicas Normalizadas (3NF)</i><br/>Triggers PL/pgSQL que protegen la inmutabilidad de revisiones",
                   vertex="1",
                   style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#cbd5e1;fontColor=#0f172a;fontSize=12;align=left;spacingLeft=15;")
ET.SubElement(m3, "mxGeometry", x="25", y="415", width="490", height="145", as_="geometry")

# Dock Inferior
dock = ET.SubElement(root2, "mxCell", id="dock", parent="1",
                     value="<b>PRINCIPIOS Y SERVICIOS TRANSVERSALES (SEMANA 09):</b> 1. MVC/MVT (Separación) | 2. DAO (Acceso desacoplado) | 3. TDD (32 tests pytest en verde) | 4. SOLID y Docker (Contenedores portables)",
                     vertex="1",
                     style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0f172a;fontColor=#ffffff;fontSize=12;align=center;")
ET.SubElement(dock, "mxGeometry", x="40", y="885", width="1840", height="160", as_="geometry")

tree2 = ET.ElementTree(mxfile2)
ET.indent(tree2, space="  ", level=0)
tree2.write(SLIDE2_DRAWIO, encoding="utf-8", xml_declaration=True)
print(f"Draw.io Diapositiva 02 generado: {SLIDE2_DRAWIO}")
