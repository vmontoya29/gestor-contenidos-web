# ─────────────────────────────────────────
# PANTALLA DE LOGIN
# Permite al administrador iniciar sesión
# ─────────────────────────────────────────

import streamlit as st
import sys
sys.path.append(".")
from assets.estilos import aplicar_estilos
aplicar_estilos()
from core.auth import login, cerrar_sesion
from components.footer import mostrar_pie

# ─────────────────────────────────────────
# TÍTULO DE LA PÁGINA
# ─────────────────────────────────────────
st.title("🔐 Iniciar Sesión")
st.markdown("Acceso para administradores del sistema.")
st.divider()

# ─────────────────────────────────────────
# SI YA HAY UN USUARIO LOGUEADO
# Mostrar mensaje y botón para cerrar sesión
# ─────────────────────────────────────────
if st.session_state.get('logueado', False):
    nombre = st.session_state.get('usuario_nombre', '')
    correo = st.session_state.get('usuario_correo', '')
    rol = st.session_state.get('usuario_rol', '')
    
    with st.container(border=True):
        st.success(f"✅ Sesión activa")
        st.markdown(f"**Nombre:** {nombre}")
        st.markdown(f"**Correo:** {correo}")
        st.markdown(f"**Rol:** {rol}")
    
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🛠️ Ir al Panel de Administración", type="primary", use_container_width=True):
            st.switch_page("pages/6_Panel_Administracion.py")
    
    with col2:
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            cerrar_sesion()
            st.success("Sesión cerrada correctamente.")
            st.rerun()

# ─────────────────────────────────────────
# SI NO HAY USUARIO LOGUEADO
# Mostrar formulario de login
# ─────────────────────────────────────────
else:
    with st.container(border=True):
        st.markdown("### Ingresa tus credenciales")
        
        # Campo de correo
        correo = st.text_input(
            "📧 Correo institucional",
            placeholder="ejemplo@elpoli.edu.co"
        )
        
        # Campo de contraseña (oculta)
        password = st.text_input(
            "🔑 Contraseña",
            type="password",
            placeholder="Tu contraseña"
        )
        
        st.markdown("")
        
        # Botón de inicio de sesión
        if st.button("Ingresar", type="primary", use_container_width=True):
            
            # Validar que ambos campos estén llenos
            if not correo or not password:
                st.error("⚠️ Por favor completa todos los campos.")
            
            # Validar que el correo sea del Politécnico
            elif not correo.endswith("@elpoli.edu.co"):
                st.error("⚠️ Solo se permiten correos institucionales (@elpoli.edu.co).")
            
            # Intentar iniciar sesión
            else:
                exito, mensaje = login(correo, password)
                if exito:
                    st.success(f"✅ {mensaje}")
                    st.switch_page("pages/6_Panel_Administracion.py")
                else:
                    st.error(f"❌ {mensaje}")

mostrar_pie()