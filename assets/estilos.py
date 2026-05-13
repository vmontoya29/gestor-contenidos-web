# ─────────────────────────────────────────
# SISTEMA DE ESTILOS CENTRALIZADO
# Politécnico Colombiano Jaime Isaza Cadavid
# ─────────────────────────────────────────

import streamlit as st
import sys
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
    
    css = """
        <style>
            [data-testid="stHeaderActionElements"] {
                display: none !important;
            }
    """
    
    # Si NO hay sesión activa, ocultar Panel de Administración
    if not st.session_state.get('logueado', False):
        css += """
            [data-testid="stSidebarNav"] ul li:has(a[href*="Panel_Administracion"]) {
                display: none !important;
            }
        """
        
        # Ocultar módulos desactivados (solo para usuarios sin login)
        try:
            from core.database import run_query
            config = run_query("SELECT modulo, visible FROM configuracion WHERE visible = 0")
            for item in config:
                modulo_archivo = MAPEO_MODULOS.get(item['modulo'], item['modulo'])
                css += f"""
                    [data-testid="stSidebarNav"] ul li:has(a[href*="{modulo_archivo}"]) {{
                        display: none !important;
                    }}
                """
        except Exception:
            pass
    
    css += "</style>"
    
    st.markdown(css, unsafe_allow_html=True)