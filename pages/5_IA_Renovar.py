from components.footer import mostrar_pie
import streamlit as st
import sys
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
    competencias = " ".join(c['texto'] for c in contenidos if c['tipo'] == 'competencia')
    resultados = " ".join(c['texto'] for c in contenidos if c['tipo'] == 'resultado')
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

Por favor proporciona:
1. COMPETENCIAS ACTUALIZADAS
2. RESULTADOS DE APRENDIZAJE ACTUALIZADOS
3. CONTENIDOS ACTUALIZADOS con temas modernos
4. METODOLOGÍAS RECOMENDADAS
5. JUSTIFICACIÓN de los cambios

Responde en español y de forma estructurada.
"""
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                propuesta = response.choices[0].message.content
                st.session_state['propuesta'] = propuesta
                st.session_state['materia_propuesta'] = materia['nombre']
                st.session_state['codigo_propuesta'] = materia['codigo']
                st.session_state['programa_propuesta'] = prog['nombre']

            except Exception as e:
                st.error(f"Error al conectar con la IA: {e}")

    # ─────────────────────────────────────────
    # MOSTRAR PROPUESTA Y BOTONES
    # ─────────────────────────────────────────
    if 'propuesta' in st.session_state:
        st.subheader("📋 Propuesta generada por la IA")
        st.markdown(st.session_state['propuesta'])
        st.divider()
        
        st.info("📄 Descarga la propuesta en PDF para enviarla a los responsables académicos para su revisión y aprobación.")

        # ─────────────────────────────────────────
        # GENERAR PDF
        # ─────────────────────────────────────────
        def generar_pdf():
            pdf = FPDF()
            pdf.add_page()
            
            # Título
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Propuesta de Renovacion de Asignatura", ln=True, align="C")
            pdf.ln(5)
            
            # Subtítulo institucional
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, "Politecnico Colombiano Jaime Isaza Cadavid", ln=True, align="C")
            pdf.cell(0, 6, "Gestor de Contenidos Academicos", ln=True, align="C")
            pdf.ln(8)
            
            # Datos de la asignatura
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Informacion de la Asignatura", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, f"Programa: {st.session_state['programa_propuesta']}", ln=True)
            pdf.cell(0, 6, f"Asignatura: {st.session_state['materia_propuesta']}", ln=True)
            pdf.cell(0, 6, f"Codigo: {st.session_state['codigo_propuesta']}", ln=True)
            pdf.cell(0, 6, f"Fecha de generacion: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
            pdf.ln(5)
            
            # Línea separadora
            pdf.set_draw_color(212, 160, 23)
            pdf.set_line_width(0.5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            # Contenido de la propuesta
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Propuesta generada por IA", ln=True)
            pdf.ln(3)
            
            pdf.set_font("Helvetica", "", 10)
            
            # Limpiar texto para PDF (FPDF no soporta unicode bien)
            texto = st.session_state['propuesta']
            texto = texto.replace("**", "").replace("•", "-").replace("✅", "").replace("❌", "")
            texto = texto.encode('latin-1', 'replace').decode('latin-1')
            
            pdf.multi_cell(0, 5, texto)
            
            # Sección de aprobación
            pdf.ln(10)
            pdf.set_draw_color(212, 160, 23)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Espacio para revision y aprobacion", ln=True)
            pdf.ln(5)
            
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, "Nombre del revisor: _______________________________________", ln=True)
            pdf.ln(3)
            pdf.cell(0, 6, "Cargo: _______________________________________________", ln=True)
            pdf.ln(3)
            pdf.cell(0, 6, "Fecha de revision: ____ / ____ / ________", ln=True)
            pdf.ln(5)
            pdf.cell(0, 6, "Decision:   [ ] Aprobada    [ ] Aprobada con cambios    [ ] Rechazada", ln=True)
            pdf.ln(5)
            pdf.cell(0, 6, "Observaciones:", ln=True)
            pdf.ln(3)
            pdf.cell(0, 6, "_________________________________________________________________", ln=True)
            pdf.ln(5)
            pdf.cell(0, 6, "_________________________________________________________________", ln=True)
            pdf.ln(5)
            pdf.cell(0, 6, "_________________________________________________________________", ln=True)
            pdf.ln(10)
            pdf.cell(0, 6, "Firma: _______________________________________", ln=True)
            
            return bytes(pdf.output())

        # Botones
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
                del st.session_state['propuesta']
                st.rerun()

else:
    st.warning("Esta asignatura no tiene contenido cargado aún.")

mostrar_pie()