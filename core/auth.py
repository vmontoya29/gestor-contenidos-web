# ─────────────────────────────────────────
# MÓDULO DE AUTENTICACIÓN
# Maneja el login del administrador
# ─────────────────────────────────────────

import streamlit as st
import bcrypt
from core.database import run_query

# ─────────────────────────────────────────
# FUNCIÓN 1: Iniciar sesión
# Verifica el correo y la contraseña del usuario
# ─────────────────────────────────────────
def login(correo, password):
    # Buscar el usuario en la base de datos por correo
    resultado = run_query(
        "SELECT id, nombre, correo, password, rol, activo FROM usuarios WHERE correo = %s",
        (correo,)
    )
    
    # Si no encuentra el correo
    if not resultado:
        return False, "Correo no encontrado"
    
    usuario = resultado[0]
    
    # Si el usuario está desactivado
    if usuario['activo'] != 1:
        return False, "Usuario desactivado"
    
    # Comparar la contraseña ingresada con la guardada (hasheada)
    password_bytes = password.encode('utf-8')
    hash_guardado = usuario['password'].encode('utf-8')
    
    if bcrypt.checkpw(password_bytes, hash_guardado):
        # Guardar datos del usuario en la sesión de Streamlit
        st.session_state['logueado'] = True
        st.session_state['usuario_id'] = usuario['id']
        st.session_state['usuario_nombre'] = usuario['nombre']
        st.session_state['usuario_correo'] = usuario['correo']
        st.session_state['usuario_rol'] = usuario['rol']
        return True, "Bienvenido"
    else:
        return False, "Contraseña incorrecta"


# ─────────────────────────────────────────
# FUNCIÓN 2: Cerrar sesión
# Borra los datos del usuario de la sesión
# ─────────────────────────────────────────
def cerrar_sesion():
    st.session_state['logueado'] = False
    st.session_state.pop('usuario_id', None)
    st.session_state.pop('usuario_nombre', None)
    st.session_state.pop('usuario_correo', None)
    st.session_state.pop('usuario_rol', None)


# ─────────────────────────────────────────
# FUNCIÓN 3: ¿Hay un admin logueado?
# Devuelve True si el usuario actual es admin o superadmin
# ─────────────────────────────────────────
def es_admin():
    if not st.session_state.get('logueado', False):
        return False
    rol = st.session_state.get('usuario_rol', '')
    return rol in ['admin', 'superadmin']