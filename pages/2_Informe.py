from components.footer import mostrar_pie
import streamlit as st
import sys
sys.path.append(".")
from core.database import run_query  # Función para consultar la base de datos
from fpdf import FPDF                # Librería para generar PDFs

# ─────────────────────────────────────────
# TÍTULO Y DESCRIPCIÓN DE LA PÁGINA
# ─────────────────────────────────────────
st.title("📋 Informe por Programa")
st.markdown("Detalle completo de cada programa académico.")
st.divider()

# ─────────────────────────────────────────
# CARGAR TODOS LOS PROGRAMAS DE LA BD
# ─────────────────────────────────────────
programas = run_query("SELECT id, nombre, codigo FROM programas ORDER BY nombre")

if not programas:
    st.warning("No se encontraron programas.")
else:
    # Mostrar selector con nombre + código para distinguir programas con mismo nombre
    nombres = [f"{p['nombre']} ({p['codigo']})" for p in programas]
    seleccion = st.selectbox("Selecciona un programa:", nombres)

    # Obtener el programa seleccionado usando el índice
    prog = programas[nombres.index(seleccion)]

    # ─────────────────────────────────────────
    # CONSULTAR MATERIAS DEL PROGRAMA SELECCIONADO
    # Incluye información del documento si existe
    # ─────────────────────────────────────────
    materias = run_query("""
        SELECT m.id, m.nombre, m.codigo, m.nivel, m.creditos, m.periodo, m.version,
               d.version as version_doc, d.fecha_subida
        FROM materias m
        LEFT JOIN documentos d ON d.materia_id = m.id
        WHERE m.programa_id = %s
        ORDER BY m.periodo, m.nombre
    """, (prog['id'],))

    # ─────────────────────────────────────────
    # CALCULAR MÉTRICAS GENERALES
    # ─────────────────────────────────────────
    total = len(materias)
    sin_contenido = sum(1 for m in materias if not m['version_doc'])
    con_contenido = total - sin_contenido
    en_v8 = sum(1 for m in materias if m['version_doc'] == '08')

    # Mostrar métricas en 4 columnas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total materias", total)
    col2.metric("Con contenido", con_contenido)
    col3.metric("Sin contenido", sin_contenido)
    col4.metric("En versión 8", en_v8)

    st.divider()

    # ─────────────────────────────────────────
    # FILTRO DE MATERIAS
    # ─────────────────────────────────────────
    filtro = st.radio("Filtrar por:", ["Todas", "Sin contenido", "Con contenido", "En versión 8"], horizontal=True)

    # Aplicar el filtro seleccionado
    if filtro == "Sin contenido":
        materias_filtradas = [m for m in materias if not m['version_doc']]
    elif filtro == "Con contenido":
        materias_filtradas = [m for m in materias if m['version_doc']]
    elif filtro == "En versión 8":
        materias_filtradas = [m for m in materias if m['version_doc'] == '08']
    else:
        materias_filtradas = materias  # Mostrar todas

    # ─────────────────────────────────────────
    # MOSTRAR LISTA DE MATERIAS
    # ─────────────────────────────────────────
    for m in materias_filtradas:
        # Definir ícono según si tiene contenido o no
        estado = "✅ V" + m['version_doc'] if m['version_doc'] else "❌ Sin contenido"
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 2])
            c1.markdown(f"**{m['nombre']}**  \nCódigo: `{m['codigo'] or 'N/A'}`")
            c2.markdown(f"Semestre: **{m['periodo']}**")
            c3.markdown(f"Créditos: **{m['creditos']}**")
            c4.markdown(f"Estado: {estado}")

    st.divider()

    # ─────────────────────────────────────────
    # GENERAR Y DESCARGAR PDF
    # ─────────────────────────────────────────
    if st.button("📥 Descargar informe PDF"):
        pdf = FPDF()
        pdf.add_page()

        # Título del informe
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"Informe: {prog['nombre']}", ln=True)

        # Resumen de métricas
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, f"Codigo: {prog['codigo']}  |  Total: {total}  |  Sin contenido: {sin_contenido}  |  V8: {en_v8}", ln=True)
        pdf.ln(4)

        # Encabezados de la tabla
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(80, 8, "Materia", border=1)
        pdf.cell(25, 8, "Semestre", border=1)
        pdf.cell(25, 8, "Creditos", border=1)
        pdf.cell(50, 8, "Estado", border=1)
        pdf.ln()

        # Filas de la tabla con cada materia
        pdf.set_font("Helvetica", "", 10)
        for m in materias:
            estado_txt = "V" + m['version_doc'] if m['version_doc'] else "Sin contenido"
            pdf.cell(80, 7, (m['nombre'] or "")[:40], border=1)
            pdf.cell(25, 7, str(m['periodo'] or ""), border=1)
            pdf.cell(25, 7, str(m['creditos'] or ""), border=1)
            pdf.cell(50, 7, estado_txt, border=1)
            pdf.ln()

        # Convertir PDF a bytes y ofrecer descarga
        pdf_bytes = pdf.output()
        st.download_button("📄 Descargar PDF", data=bytes(pdf_bytes),
                           file_name=f"informe_{prog['codigo']}.pdf",
                           mime="application/pdf")
        
mostrar_pie()