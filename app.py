from components.footer import mostrar_pie
import streamlit as st
import sys
sys.path.append(".")
from core.database import get_connection  # Conexión a la base de datos

# ─────────────────────────────────────────
# CONFIGURACIÓN GENERAL DE LA APP
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Gestor de Contenidos",
    page_icon="📚",
    layout="wide"
)

# ─────────────────────────────────────────
# PÁGINA DE INICIO
# ─────────────────────────────────────────
st.title("📚 Gestor de Contenidos Académicos")
st.markdown("### Bienvenido al sistema de gestión de programas académicos")
st.divider()

# ─────────────────────────────────────────
# VERIFICAR CONEXIÓN A LA BASE DE DATOS
# ─────────────────────────────────────────
conn = get_connection()
if conn:
    st.success("✅ Sistema conectado correctamente")
    conn.close()
else:
    st.error("❌ No se pudo conectar a la base de datos")

st.divider()

# ─────────────────────────────────────────
# DESCRIPCIÓN DE LAS SECCIONES
# ─────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 📊 Dashboard General")
        st.markdown("Resumen del estado de todos los programas académicos con indicadores de progreso.")

    with st.container(border=True):
        st.markdown("### 📋 Informe por Programa")
        st.markdown("Detalle completo de cada programa: materias, versiones y descarga en PDF.")

    with st.container(border=True):
        st.markdown("### 🔍 Comparador de Contenidos")
        st.markdown("Compara materias entre dos programas y encuentra similitudes y diferencias.")

with col2:
    with st.container(border=True):
        st.markdown("### 🔗 Dependencias")
        st.markdown("Visualiza las materias organizadas por semestre con su estado actual.")

    with st.container(border=True):
        st.markdown("### 🤖 IA — Renovar Asignatura")
        st.markdown("La IA analiza una asignatura y propone una versión actualizada con metodologías modernas.")

mostrar_pie()
