from components.footer import mostrar_pie
import streamlit as st
import sys
import re
sys.path.append(".")
from assets.estilos import aplicar_estilos
aplicar_estilos()
from core.database import run_query
from groq import Groq
from fpdf import FPDF
from datetime import datetime
import io

# ─────────────────────────────────────────
# CONFIGURACIÓN DE GROQ
# ─────────────────────────────────────────
client = Groq(api_key=st.secrets["groq"]["api_key"])

# ─────────────────────────────────────────
# TÍTULO
# ─────────────────────────────────────────
st.title("🧠 IA — Renovar Asignatura")
st.markdown("La IA genera una propuesta de actualización. Descárgala en PDF para revisión y aprobación.")
st.divider()

# ─────────────────────────────────────────
# SELECCIONAR PROGRAMA Y MATERIA
# ─────────────────────────────────────────
programas = run_query("SELECT id, nombre, codigo FROM programas ORDER BY nombre")
etiquetas = [f"{p['nombre']} ({p['codigo']})" for p in programas]
seleccion = st.selectbox("Selecciona el programa:", etiquetas)
prog = programas[etiquetas.index(seleccion)]

materias = run_query("""
    SELECT m.id, m.nombre, m.codigo
    FROM materias m
    WHERE m.programa_id = %s
    ORDER BY m.nombre
""", (prog['id'],))

nombres_materias = [m['nombre'] for m in materias]
materia_sel = st.selectbox("Selecciona la asignatura:", nombres_materias)
materia = next(m for m in materias if m['nombre'] == materia_sel)

# ─────────────────────────────────────────
# CARGAR CONTENIDO ACTUAL
# ─────────────────────────────────────────
contenidos = run_query("""
    SELECT c.tipo, c.texto
    FROM contenidos c
    JOIN documentos d ON c.documento_id = d.id
    WHERE d.materia_id = %s
""", (materia['id'],))

if contenidos:
    competencias   = " ".join(c['texto'] for c in contenidos if c['tipo'] == 'competencia')
    resultados     = " ".join(c['texto'] for c in contenidos if c['tipo'] == 'resultado')
    contenido_list = [c['texto'] for c in contenidos if c['tipo'] == 'contenido']

    with st.expander("📄 Ver contenido actual de la asignatura"):
        st.markdown("**Competencias:**")
        st.write(competencias or "No registradas")
        st.markdown("**Resultados de aprendizaje:**")
        st.write(resultados or "No registrados")
        st.markdown("**Contenidos:**")
        for i, c in enumerate(contenido_list, 1):
            st.markdown(f"{i}. {c}")

    st.divider()

    # ─────────────────────────────────────────
    # BOTÓN PARA GENERAR PROPUESTA
    # ─────────────────────────────────────────
    if st.button("🧠 Generar propuesta actualizada con IA", type="primary"):
        with st.spinner("La IA está analizando y generando la propuesta..."):
            try:
                prompt = f"""
Eres un experto en diseño curricular universitario.
Analiza el siguiente programa de asignatura y propón una versión actualizada
basada en las tendencias más recientes y metodologías modernas de enseñanza.

ASIGNATURA: {materia['nombre']}
CÓDIGO: {materia['codigo']}

COMPETENCIAS ACTUALES:
{competencias}

RESULTADOS DE APRENDIZAJE ACTUALES:
{resultados}

CONTENIDOS ACTUALES:
{chr(10).join(contenido_list)}

Por favor proporciona en español y de forma estructurada:
1. COMPETENCIAS ACTUALIZADAS
2. RESULTADOS DE APRENDIZAJE ACTUALIZADOS
3. CONTENIDOS ACTUALIZADOS con temas modernos
4. METODOLOGÍAS RECOMENDADAS
5. JUSTIFICACIÓN DE LOS CAMBIOS
6. BIBLIOGRAFÍA Y RECURSOS WEB

INSTRUCCIONES PARA LA BIBLIOGRAFÍA (sección 6):
- NO incluyas URLs ni enlaces.
- Formato para libros: Autor, A. (Año). Título del libro. Editorial.
- Formato para artículos: Autor, A. (Año). Título del artículo. Revista, volumen(número), páginas.
- Formato para recursos web: Nombre del recurso. Organización responsable. Descripción breve de 1 línea.
- Incluye mínimo 6 referencias reales y verificables relacionadas con la asignatura.
- Numera cada referencia del 1 al 6 (o más).

Responde en español y de forma estructurada. No uses URLs en ninguna parte de tu respuesta.
"""
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                propuesta = response.choices[0].message.content

                # ── Limpiar URLs inventadas que puedan quedar ──
                propuesta = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', propuesta)  # Quita [texto](url)
                propuesta = re.sub(r'https?://\S+', '', propuesta)               # Quita URLs sueltas

                # ── Separar propuesta y bibliografía ──
                match_biblio = re.search(r'(6\.\s*BIBLIOGRAF[ÍI]A.*)', propuesta, re.IGNORECASE | re.DOTALL)
                if match_biblio:
                    inicio = match_biblio.start()
                    bibliografia = propuesta[inicio:]
                    propuesta_sin_biblio = propuesta[:inicio].rstrip()
                    # Limpiar líneas finales que queden solo con asteriscos o numeración suelta
                    propuesta_sin_biblio = re.sub(r'(\n|\r)*[\*\s\d\.]+\s*$', '', propuesta_sin_biblio).rstrip()
                else:
                    bibliografia = ""
                    propuesta_sin_biblio = propuesta

                st.session_state['propuesta']            = propuesta
                st.session_state['propuesta_sin_biblio'] = propuesta_sin_biblio
                st.session_state['bibliografia']         = bibliografia
                st.session_state['materia_propuesta']    = materia['nombre']
                st.session_state['codigo_propuesta']     = materia['codigo']
                st.session_state['programa_propuesta']   = prog['nombre']

            except Exception as e:
                st.error(f"Error al conectar con la IA: {e}")

    # ─────────────────────────────────────────
    # MOSTRAR PROPUESTA Y BIBLIOGRAFÍA
    # ─────────────────────────────────────────
    if 'propuesta' in st.session_state:
        st.subheader("📋 Propuesta generada por la IA")
        st.markdown(st.session_state['propuesta_sin_biblio'])

        # ── Bibliografía con botones de búsqueda ──
        if st.session_state.get('bibliografia'):
            st.markdown("---")
            st.markdown("**6. Bibliografía y Recursos Web**")
            st.caption("Haz clic en 🔍 para buscar cada referencia en Google Académico.")

            lineas = st.session_state['bibliografia'].split('\n')
            for linea in lineas:
                linea = linea.strip()
                # Saltar encabezados de sección y líneas vacías
                if not linea:
                    continue
                if re.match(r'^6\.?\s*BIBLIOGRAF', linea, re.IGNORECASE):
                    continue
                if re.match(r'^\*{0,2}6\.?\s*BIBLIOGRAF', linea, re.IGNORECASE):
                    continue

                # Limpiar asteriscos Markdown de negrillas
                linea_limpia = re.sub(r'\*+', '', linea).strip()
                if not linea_limpia:
                    continue

                # Construir URL de búsqueda en Google Académico
                terminos = re.sub(r'^\d+[\.\)]\s*', '', linea_limpia)  # quitar número inicial
                url_busqueda = "https://scholar.google.com/scholar?q=" + terminos.replace(" ", "+")[:150]

                col_texto, col_boton = st.columns([5, 1])
                with col_texto:
                    st.markdown(linea_limpia)
                with col_boton:
                    st.link_button("🔍 Buscar", url_busqueda)

        st.divider()
        st.info("📄 Descarga la propuesta en PDF para enviarla a los responsables académicos.")

        # ─────────────────────────────────────────
        # GENERAR PDF
        # ─────────────────────────────────────────
        def generar_pdf():
            pdf = FPDF()
            pdf.add_page()

            # Título
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Propuesta de Renovacion de Asignatura", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(5)

            # Subtítulo institucional
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, "Politecnico Colombiano Jaime Isaza Cadavid", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.cell(0, 6, "Gestor de Contenidos Academicos", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(8)

            # Datos de la asignatura
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Informacion de la Asignatura", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, f"Programa: {st.session_state['programa_propuesta']}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Asignatura: {st.session_state['materia_propuesta']}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Codigo: {st.session_state['codigo_propuesta']}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Fecha de generacion: {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)

            # Línea separadora
            pdf.set_draw_color(212, 160, 23)
            pdf.set_line_width(0.5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            # Propuesta sin bibliografía
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Propuesta generada por IA", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            pdf.set_font("Helvetica", "", 10)
            texto = st.session_state['propuesta_sin_biblio']
            texto = re.sub(r'\*+', '', texto)
            texto = texto.replace("•", "-").replace("✅", "").replace("❌", "")
            texto = texto.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, texto)

            # Bibliografía
            if st.session_state.get('bibliografia'):
                pdf.ln(5)
                pdf.set_draw_color(212, 160, 23)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 8, "6. Bibliografia y Recursos Web", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(3)
                pdf.set_font("Helvetica", "", 9)

                lineas_pdf = st.session_state['bibliografia'].split('\n')
                for linea in lineas_pdf:
                    linea = linea.strip()
                    if not linea:
                        continue
                    if re.match(r'^\*{0,2}6\.?\s*BIBLIOGRAF', linea, re.IGNORECASE):
                        continue
                    linea = re.sub(r'\*+', '', linea).strip()
                    linea = re.sub(r'https?://\S+', '', linea).strip()
                    linea = linea.encode('latin-1', 'replace').decode('latin-1')
                    if linea:
                        pdf.multi_cell(0, 5, linea)
                        pdf.ln(1)

            # Sección de aprobación
            pdf.ln(10)
            pdf.set_draw_color(212, 160, 23)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Espacio para revision y aprobacion", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, "Nombre del revisor: _______________________________________", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            pdf.cell(0, 6, "Cargo: _______________________________________________", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            pdf.cell(0, 6, "Fecha de revision: ____ / ____ / ________", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            pdf.cell(0, 6, "Decision:   [ ] Aprobada    [ ] Aprobada con cambios    [ ] Rechazada", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            pdf.cell(0, 6, "Observaciones:", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            pdf.cell(0, 6, "_________________________________________________________________", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            pdf.cell(0, 6, "_________________________________________________________________", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            pdf.cell(0, 6, "_________________________________________________________________", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)
            pdf.cell(0, 6, "Firma: _______________________________________", new_x="LMARGIN", new_y="NEXT")

            return bytes(pdf.output())

        # ─────────────────────────────────────────
        # BOTONES DE DESCARGA Y REGENERAR
        # ─────────────────────────────────────────
        col1, col2 = st.columns(2)

        with col1:
            pdf_bytes = generar_pdf()
            nombre_archivo = f"propuesta_{materia['codigo']}_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button(
                label="📥 Descargar propuesta en PDF",
                data=pdf_bytes,
                file_name=nombre_archivo,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

        with col2:
            if st.button("🔄 Generar nueva propuesta", use_container_width=True):
                for key in ['propuesta', 'propuesta_sin_biblio', 'bibliografia']:
                    st.session_state.pop(key, None)
                st.rerun()

else:
    st.warning("Esta asignatura no tiene contenido cargado aún.")

mostrar_pie()