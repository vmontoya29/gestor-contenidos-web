# ─────────────────────────────────────────
# MÓDULO DE AUTENTICACIÓN
# Maneja el login y la recuperación por correo
# ─────────────────────────────────────────

import streamlit as st
import bcrypt
import smtplib
from email.mime.text import MIMEText
from core.database import run_query

# ─────────────────────────────────────────
# FUNCIÓN 1: Iniciar sesión
# ─────────────────────────────────────────
def login(correo, password):
    # Buscar el usuario en la base de datos por correo
    resultado = run_query(
        "SELECT id, nombre, correo, password, rol, activo FROM usuarios WHERE correo = %s",
        (correo,)
    )
    
    if not resultado:
        return False, "Correo no encontrado"
    
    usuario = resultado[0]
    
    if usuario['activo'] != 1:
        return False, "Usuario desactivado"
    
    # Comparar la contraseña ingresada con el hash guardado
    password_bytes = password.encode('utf-8')
    hash_guardado = usuario['password'].encode('utf-8')
    
    if bcrypt.checkpw(password_bytes, hash_guardado):
        # Guardar datos en la sesión de Streamlit
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
# ─────────────────────────────────────────
def cerrar_sesion():
    st.session_state['logueado'] = False
    st.session_state.pop('usuario_id', None)
    st.session_state.pop('usuario_nombre', None)
    st.session_state.pop('usuario_correo', None)
    st.session_state.pop('usuario_rol', None)

# ─────────────────────────────────────────
# FUNCIÓN 3: ¿Hay un admin logueado?
# ─────────────────────────────────────────
def es_admin():
    if not st.session_state.get('logueado', False):
        return False
    rol = st.session_state.get('usuario_rol', '')
    return rol in ['admin', 'superadmin']

# ─────────────────────────────────────────
# FUNCIÓN 4: Enviar correo de recuperación
# Conecta con Gmail usando las credenciales seguras
# ─────────────────────────────────────────
def enviar_correo_recuperacion(correo_destino, nueva_clave):
    try:
        # Leer credenciales desde secrets.toml
        smtp_config = st.secrets["smtp"]
        
        # Estructurar el mensaje de texto sencillo
        msg = MIMEText(f"Tu nueva contraseña temporal es: {nueva_clave}")
        msg['Subject'] = 'Recuperación de Contraseña - Gestor Poli'
        msg['From'] = smtp_config["correo"]
        msg['To'] = correo_destino
        
        # Conexión SSL segura con el servidor de Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(smtp_config["correo"], smtp_config["password"])
            server.sendmail(smtp_config["correo"], correo_destino, msg.as_string())
        return True
    except Exception:
        return False
    
# ─────────────────────────────────────────
# FUNCIÓN 5: Cambiar contraseña en Base de Datos
# Genera el hash seguro y lo actualiza por correo
# ─────────────────────────────────────────
def actualizar_password_recuperacion(correo, nueva_password):
    from core.database import get_connection
    # Crear hash seguro con bcrypt
    nuevo_hash = bcrypt.hashpw(nueva_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                # Actualizar la clave del usuario según su correo
                cursor.execute("UPDATE usuarios SET password = %s WHERE correo = %s", (nuevo_hash, correo))
            return True
        except Exception:
            return False
        finally:
            conn.close()
    return False

