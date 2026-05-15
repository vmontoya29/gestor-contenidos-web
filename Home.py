import streamlit as st
import sys
sys.path.append(".")
from assets.estilos import aplicar_estilos
from core.database import get_connection, run_query
from components.footer import mostrar_pie

st.set_page_config(
    page_title="Gestor de Contenidos",
    page_icon="📚",
    layout="wide"
)

aplicar_estilos()

# ─────────────────────────────────────────
# TÍTULO
# ─────────────────────────────────────────
st.title("📚 Gestor de Contenidos Académicos")
st.markdown("### Bienvenido al sistema de gestión de programas académicos")
st.divider()

# ─────────────────────────────────────────
# VERIFICAR CONEXIÓN
# ─────────────────────────────────────────
conn = get_connection()
if conn:
    st.success("✅ Sistema conectado correctamente")
    conn.close()
else:
    st.error("❌ No se pudo conectar a la base de datos")

st.divider()

# ─────────────────────────────────────────
# CARGAR CONFIGURACIÓN DE MÓDULOS VISIBLES
# ─────────────────────────────────────────
es_admin_actual = st.session_state.get('logueado', False)

# Si es admin, ve TODO. Si no, solo lo que está visible en BD.
if es_admin_actual:
    modulos_visibles = ['Dashboard', 'Informe', 'Comparador', 'Dependencias', 'IA_Renovar']
else:
    config = run_query("SELECT modulo FROM configuracion WHERE visible = 1")
    modulos_visibles = [item['modulo'] for item in config]

# ─────────────────────────────────────────
# TARJETAS DE MÓDULOS (filtradas por configuración)
# ─────────────────────────────────────────
tarjetas = []

if 'Dashboard' in modulos_visibles:
    tarjetas.append({
        'titulo': '📊 Dashboard General',
        'descripcion': 'Resumen del estado de todos los programas académicos con indicadores de progreso.',
        'boton': 'Ir al Dashboard',
        'pagina': 'pages/1_Dashboard.py',
        'key': 'btn_dashboard'
    })

if 'Informe' in modulos_visibles:
    tarjetas.append({
        'titulo': '📋 Informe por Programa',
        'descripcion': 'Detalle completo de cada programa: materias, versiones y descarga en PDF.',
        'boton': 'Ver Informes',
        'pagina': 'pages/2_Informe.py',
        'key': 'btn_informe'
    })

if 'Comparador' in modulos_visibles:
    tarjetas.append({
        'titulo': '🔍 Comparador de Contenidos',
        'descripcion': 'Compara materias entre dos programas y encuentra similitudes y diferencias.',
        'boton': 'Ir al Comparador',
        'pagina': 'pages/3_Comparador.py',
        'key': 'btn_comparador'
    })

if 'Dependencias' in modulos_visibles:
    tarjetas.append({
        'titulo': '🔗 Dependencias',
        'descripcion': 'Visualiza las materias organizadas por semestre con su estado actual.',
        'boton': 'Ver Dependencias',
        'pagina': 'pages/4_Dependencias.py',
        'key': 'btn_dependencias'
    })

if 'IA_Renovar' in modulos_visibles:
    tarjetas.append({
        'titulo': '🤖 IA — Renovar Asignatura',
        'descripcion': 'La IA analiza una asignatura y propone una versión actualizada con metodologías modernas.',
        'boton': 'Usar IA',
        'pagina': 'pages/5_IA_Renovar.py',
        'key': 'btn_ia'
    })

# Mostrar tarjetas en 2 columnas
if tarjetas:
    col1, col2 = st.columns(2)
    for i, t in enumerate(tarjetas):
        columna = col1 if i % 2 == 0 else col2
        with columna:
            with st.container(border=True):
                st.markdown(f"### {t['titulo']}")
                st.markdown(t['descripcion'])
                if st.button(t['boton'], key=t['key'], use_container_width=True):
                    st.switch_page(t['pagina'])
else:
    st.info("No hay módulos disponibles en este momento.")

st.divider()

# ─────────────────────────────────────────
# SECCIÓN DE ADMIN / LOGIN 
# ─────────────────────────────────────────
if es_admin_actual:
    st.markdown("### 🛠️ Panel de Administración")
    with st.container(border=True):
        st.markdown("Accede al panel completo para configurar el sistema, gestionar documentos y actualizar tu perfil.")
        # Cambio aquí: Ahora te redirige a la página 0_Login.py que es donde vive el panel unificado
        if st.button("Ir al Panel de Administración", type="primary", use_container_width=True, key="btn_panel"):
            st.switch_page("pages/0_Login.py")
else:
    with st.container(border=True):
        st.markdown("### 🔐 ¿Eres administrador?")
        st.markdown("Inicia sesión para acceder a las funciones de administración.")
        if st.button("Iniciar Sesión", key="btn_login", use_container_width=True, type="primary"):
            st.switch_page("pages/0_Login.py")

mostrar_pie()
