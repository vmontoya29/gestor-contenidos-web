# ─────────────────────────────────────────
# PANEL DE ADMINISTRACIÓN
# Pantalla unificada para el administrador
# Incluye: Configuración, Gestionar Documentos, Mi Perfil
# ─────────────────────────────────────────

from components.footer import mostrar_pie
import streamlit as st
import sys
import os
import re
import bcrypt
from datetime import datetime
import pdfplumber
sys.path.append(".")
from assets.estilos import aplicar_estilos
aplicar_estilos()
from core.database import run_query, get_connection
from core.auth import es_admin

# ─────────────────────────────────────────
# VERIFICAR PERMISOS
# ─────────────────────────────────────────
if not es_admin():
    st.error("🔒 Esta sección es solo para administradores.")
    st.info("Inicia sesión como administrador para acceder.")
    st.stop()

# ─────────────────────────────────────────
# CARPETA PARA PDFs
# ─────────────────────────────────────────
CARPETA_UPLOADS = "data/uploads"
os.makedirs(CARPETA_UPLOADS, exist_ok=True)

# ─────────────────────────────────────────
# FUNCIÓN: EXTRAER CONTENIDO DEL PDF
# ─────────────────────────────────────────
def extraer_contenido_pdf(pdf_file):
    texto_completo = ""
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                texto_completo += texto + "\n"
    
    resultado = {'competencias': '', 'resultados': '', 'contenidos': ''}
    
    match_comp = re.search(
        r'COMPETENCIAS.*?TRIBUTA.*?ASIGNATURA(.*?)(?:PRESENTACI[ÓO]N|3\.\s*PRESENTACI)',
        texto_completo, re.DOTALL | re.IGNORECASE
    )
    if match_comp:
        resultado['competencias'] = match_comp.group(1).strip()
    
    match_res = re.search(
        r'RESULTADOS\s+DE\s+APRENDIZAJE.*?TRIBUTA.*?ASIGNATURA(.*?)(?:OBJETIVOS|5\.\s*OBJETIVOS)',
        texto_completo, re.DOTALL | re.IGNORECASE
    )
    if match_res:
        resultado['resultados'] = match_res.group(1).strip()
    
    match_cont = re.search(
        r'CONTENIDOS\s+TEM[ÁA]TICOS.*?\(UNIDADES\)(.*?)(?:METODOLOG[ÍI]AS|7\.\s*METODOLOG)',
        texto_completo, re.DOTALL | re.IGNORECASE
    )
    if match_cont:
        resultado['contenidos'] = match_cont.group(1).strip()
    
    return resultado

# ─────────────────────────────────────────
# TÍTULO
# ─────────────────────────────────────────
st.title("🛠️ Panel de Administración")
st.markdown(f"Bienvenido, **{st.session_state.get('usuario_nombre', '')}**")
st.divider()

# ─────────────────────────────────────────
# PESTAÑAS
# ─────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["⚙️ Configuración", "📋 Gestionar Documentos", "👤 Mi Perfil"])

# ═════════════════════════════════════════
# PESTAÑA 1: CONFIGURACIÓN
# ═════════════════════════════════════════
with tab1:
    st.markdown("### Define qué módulos están visibles para los usuarios.")
    st.caption("Marca los módulos que quieres que vean los usuarios. Desmárcalos para ocultarlos.")
    st.markdown("")
    
    config = run_query("SELECT modulo, visible, descripcion FROM configuracion ORDER BY id")
    cambios = {}
    
    with st.container(border=True):
        for item in config:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{item['descripcion']}**")
                st.caption(f"Módulo: `{item['modulo']}`")
            with col2:
                estado = st.checkbox(
                    "Visible",
                    value=bool(item['visible']),
                    key=f"chk_{item['modulo']}"
                )
                cambios[item['modulo']] = estado
            st.markdown("---")
    
    if st.button("💾 Guardar configuración", type="primary", use_container_width=True):
        conn = get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    for modulo, visible in cambios.items():
                        cursor.execute(
                            "UPDATE configuracion SET visible = %s WHERE modulo = %s",
                            (1 if visible else 0, modulo)
                        )
                st.success("✅ Configuración guardada correctamente.")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")
            finally:
                conn.close()

# ═════════════════════════════════════════
# PESTAÑA 2: GESTIONAR DOCUMENTOS
# ═════════════════════════════════════════
with tab2:
    st.markdown("### Sube el PDF del documento aprobado.")
    st.caption("La app extraerá automáticamente competencias, resultados y contenidos.")
    st.markdown("")
    
    programas = run_query("SELECT id, nombre, codigo FROM programas ORDER BY nombre")
    etiquetas = [f"{p['nombre']} ({p['codigo']})" for p in programas]
    seleccion = st.selectbox("Selecciona el programa:", etiquetas, key="prog_doc")
    prog = programas[etiquetas.index(seleccion)]
    
    st.markdown("")
    
    materias = run_query("""
        SELECT m.id, m.nombre, m.codigo,
               (SELECT MAX(d.version) FROM documentos d 
                WHERE d.materia_id = m.id AND d.activo = 1) AS version_actual
        FROM materias m
        WHERE m.programa_id = %s
        ORDER BY m.nombre
    """, (prog['id'],))
    
    st.markdown(f"#### Materias del programa: **{prog['nombre']}**")
    st.caption(f"Total: {len(materias)} materias")
    st.markdown("")
    
    for materia in materias:
        version = materia['version_actual']
        if version is None:
            estado_emoji = "🔴"
            estado_texto = "Sin documento"
        elif version == '08':
            estado_emoji = "🟢"
            estado_texto = f"v{version} (actualizada)"
        else:
            estado_emoji = "🟡"
            estado_texto = f"v{version} (desactualizada)"
        
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"**{materia['nombre']}**")
                st.caption(f"Código: {materia['codigo']}")
            with col2:
                st.markdown(f"{estado_emoji} {estado_texto}")
            with col3:
                if st.button("📥 Cargar", key=f"btn_mat_{materia['id']}"):
                    st.session_state['materia_seleccionada'] = materia
                    st.session_state['mostrar_formulario'] = True
                    st.session_state.pop('contenido_extraido', None)
                    st.session_state.pop('pdf_file_data', None)
                    st.rerun()
    
    # Formulario de carga
    if st.session_state.get('mostrar_formulario', False):
        st.divider()
        materia_sel = st.session_state['materia_seleccionada']
        st.markdown(f"#### 📥 Cargar PDF — {materia_sel['nombre']}")
        
        with st.container(border=True):
            pdf_file = st.file_uploader("📎 Selecciona el PDF:", type=['pdf'], key="pdf_up_admin")
            
            if pdf_file:
                if st.button("🔍 Procesar PDF", type="primary", use_container_width=True):
                    with st.spinner("Procesando..."):
                        try:
                            pdf_file.seek(0)
                            st.session_state['pdf_file_data'] = pdf_file.getvalue()
                            pdf_file.seek(0)
                            contenido = extraer_contenido_pdf(pdf_file)
                            st.session_state['contenido_extraido'] = contenido
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
        
        if 'contenido_extraido' in st.session_state:
            contenido = st.session_state['contenido_extraido']
            st.markdown("")
            st.markdown("### 👁️ Vista previa")
            st.info("Revisa que el contenido se haya extraído correctamente.")
            
            competencias = st.text_area("📋 Competencias:", value=contenido.get('competencias', ''), height=150)
            resultados = st.text_area("🎯 Resultados:", value=contenido.get('resultados', ''), height=150)
            contenidos = st.text_area("📚 Contenidos:", value=contenido.get('contenidos', ''), height=250)
            version = st.text_input("Versión:", value="08", max_chars=2)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Guardar", type="primary", use_container_width=True, key="btn_save_doc"):
                    if not competencias and not resultados and not contenidos:
                        st.error("⚠️ No hay contenido para guardar.")
                    else:
                        conn = get_connection()
                        if conn:
                            try:
                                with conn.cursor() as cursor:
                                    cursor.execute("UPDATE documentos SET activo = 0 WHERE materia_id = %s", (materia_sel['id'],))
                                    fecha = datetime.now().strftime('%Y%m%d%H%M%S')
                                    nombre_pdf = f"{fecha}_{materia_sel['codigo']}_v{version}.pdf"
                                    ruta_pdf = os.path.join(CARPETA_UPLOADS, nombre_pdf)
                                    with open(ruta_pdf, "wb") as f:
                                        f.write(st.session_state['pdf_file_data'])
                                    cursor.execute("INSERT INTO documentos (materia_id, version, ruta_pdf, activo) VALUES (%s, %s, %s, 1)", (materia_sel['id'], version, ruta_pdf))
                                    doc_id = cursor.lastrowid
                                    if competencias.strip():
                                        cursor.execute("INSERT INTO contenidos (documento_id, tipo, texto) VALUES (%s, 'competencia', %s)", (doc_id, competencias.strip()))
                                    if resultados.strip():
                                        cursor.execute("INSERT INTO contenidos (documento_id, tipo, texto) VALUES (%s, 'resultado', %s)", (doc_id, resultados.strip()))
                                    if contenidos.strip():
                                        for linea in contenidos.strip().split('\n'):
                                            if linea.strip():
                                                cursor.execute("INSERT INTO contenidos (documento_id, tipo, texto) VALUES (%s, 'contenido', %s)", (doc_id, linea.strip()))
                                st.success(f"✅ Documento guardado para {materia_sel['nombre']}")
                                st.balloons()
                                st.session_state.pop('mostrar_formulario', None)
                                st.session_state.pop('materia_seleccionada', None)
                                st.session_state.pop('contenido_extraido', None)
                                st.session_state.pop('pdf_file_data', None)
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                            finally:
                                conn.close()
            with col2:
                if st.button("❌ Cancelar", use_container_width=True, key="btn_cancel_doc"):
                    st.session_state.pop('mostrar_formulario', None)
                    st.session_state.pop('materia_seleccionada', None)
                    st.session_state.pop('contenido_extraido', None)
                    st.session_state.pop('pdf_file_data', None)
                    st.rerun()

# ═════════════════════════════════════════
# PESTAÑA 3: MI PERFIL
# ═════════════════════════════════════════
with tab3:
    usuario_id = st.session_state.get('usuario_id')
    nombre = st.session_state.get('usuario_nombre', '')
    correo_actual = st.session_state.get('usuario_correo', '')
    rol = st.session_state.get('usuario_rol', '')
    
    with st.container(border=True):
        st.markdown("### Datos actuales")
        st.markdown(f"**Nombre:** {nombre}")
        st.markdown(f"**Correo:** {correo_actual}")
        st.markdown(f"**Rol:** {rol}")
    
    st.markdown("")
    
    # Cambiar correo
    with st.container(border=True):
        st.markdown("### 📧 Cambiar correo")
        nuevo_correo = st.text_input("Nuevo correo:", placeholder="nuevo@elpoli.edu.co", key="new_email")
        
        if st.button("Actualizar correo", type="primary", key="btn_email"):
            if not nuevo_correo:
                st.error("⚠️ Escribe el nuevo correo.")
            elif not nuevo_correo.endswith("@elpoli.edu.co"):
                st.error("⚠️ Solo correos institucionales (@elpoli.edu.co).")
            elif nuevo_correo == correo_actual:
                st.warning("⚠️ El correo nuevo es igual al actual.")
            else:
                conn = get_connection()
                if conn:
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute("UPDATE usuarios SET correo = %s WHERE id = %s", (nuevo_correo, usuario_id))
                        st.session_state['usuario_correo'] = nuevo_correo
                        st.success("✅ Correo actualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                    finally:
                        conn.close()
    
    st.markdown("")
    
    # Cambiar contraseña
    with st.container(border=True):
        st.markdown("### 🔑 Cambiar contraseña")
        password_actual = st.text_input("Contraseña actual:", type="password", key="pass_actual")
        nueva_password = st.text_input("Nueva contraseña:", type="password", help="Mínimo 8 caracteres", key="pass_nueva")
        confirmar_password = st.text_input("Confirmar nueva:", type="password", key="pass_conf")
        
        if st.button("Actualizar contraseña", type="primary", key="btn_pass"):
            if not password_actual or not nueva_password or not confirmar_password:
                st.error("⚠️ Completa todos los campos.")
            elif len(nueva_password) < 8:
                st.error("⚠️ Mínimo 8 caracteres.")
            elif nueva_password != confirmar_password:
                st.error("⚠️ Las contraseñas no coinciden.")
            else:
                resultado = run_query("SELECT password FROM usuarios WHERE id = %s", (usuario_id,))
                if resultado:
                    hash_guardado = resultado[0]['password'].encode('utf-8')
                    if not bcrypt.checkpw(password_actual.encode('utf-8'), hash_guardado):
                        st.error("❌ La contraseña actual es incorrecta.")
                    else:
                        nuevo_hash = bcrypt.hashpw(nueva_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        conn = get_connection()
                        if conn:
                            try:
                                with conn.cursor() as cursor:
                                    cursor.execute("UPDATE usuarios SET password = %s WHERE id = %s", (nuevo_hash, usuario_id))
                                st.success("✅ Contraseña actualizada.")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                            finally:
                                conn.close()

mostrar_pie()