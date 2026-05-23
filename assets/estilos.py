# ─────────────────────────────────────────
# SISTEMA DE ESTILOS CENTRALIZADO
# Politécnico Colombiano Jaime Isaza Cadavid
# ─────────────────────────────────────────

import streamlit as st
import sys
import base64
sys.path.append(".")

# ─────────────────────────────────────────
# PALETA DE COLORES INSTITUCIONALES
# ─────────────────────────────────────────
COLORES = {
    'verde_principal': '#2d5a1b',
    'verde_claro': '#5a7a4a',
    'verde_fondo': '#f0f5ea',
    'dorado': '#d4a017',
    'dorado_claro': '#f4d160',
    'gris_texto': '#333333',
    'gris_suave': '#888888',
    'blanco': '#ffffff',
}

# ─────────────────────────────────────────
# MAPEO: módulo en BD → nombre del archivo
# ─────────────────────────────────────────
MAPEO_MODULOS = {
    'Dashboard': 'Dashboard',
    'Informe': 'Informe',
    'Comparador': 'Comparador',
    'Dependencias': 'Dependencias',
    'IA_Renovar': 'IA_Renovar',
}

# ─────────────────────────────────────────
# FUNCIÓN: APLICAR ESTILOS GLOBALES
# ─────────────────────────────────────────
def aplicar_estilos():
    """Aplica estilos globales y oculta módulos según configuración."""

    try:
        with open("assets/logo_politecnico.png", "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

        css = f"""
            <style>
                /* Ocultar botones innecesarios */
                [data-testid="stHeaderActionElements"] {{
                    display: none !important;
                }}

                /* Ocultar botón de colapsar sidebar */
                [data-testid="stSidebarCollapseButton"] {{
                    display: none !important;
                }}

                /* Ocultar menú automático de Streamlit */
                [data-testid="stSidebarNav"] {{
                    display: none !important;
                }}

                /* Logo arriba del sidebar */
                [data-testid="stSidebar"]::before {{
                    content: "";
                    display: block;
                    background-image: url("data:image/png;base64,{logo_b64}");
                    background-repeat: no-repeat;
                    background-position: center;
                    background-size: 90%;
                    height: 180px;
                    margin: 40px 0 0 0;
                }}
            </style>
        """
        st.markdown(css, unsafe_allow_html=True)

    except Exception:
        pass

    # ─────────────────────────────────────────
    # NAVEGACIÓN MANUAL EN SIDEBAR
    # ─────────────────────────────────────────
    logueado = st.session_state.get('logueado', False)

    try:
        from core.database import run_query
        config = run_query("SELECT modulo, visible FROM configuracion")
        visibilidad = {item['modulo']: item['visible'] for item in config}
    except Exception:
        visibilidad = {}

    st.sidebar.page_link("Home.py",                 label="🏠 Home")

    if logueado or visibilidad.get('Dashboard', 1):
        st.sidebar.page_link("pages/1_Dashboard.py",    label="📊 Dashboard")

    if logueado or visibilidad.get('Informe', 1):
        st.sidebar.page_link("pages/2_Informe.py",      label="📋 Informe")

    if logueado or visibilidad.get('Comparador', 1):
        st.sidebar.page_link("pages/3_Comparador.py",   label="🔍 Comparador")

    if logueado or visibilidad.get('Dependencias', 1):
        st.sidebar.page_link("pages/4_Dependencias.py", label="🔗 Dependencias")

    if logueado or visibilidad.get('IA_Renovar', 1):
        st.sidebar.page_link("pages/5_IA_Renovar.py",   label="🧠 IA Renovar")

    st.sidebar.divider()
    st.sidebar.page_link("pages/0_Login.py",        label="🔐 Login")