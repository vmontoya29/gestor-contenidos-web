# ─────────────────────────────────────────
# PANTALLA UNIFICADA: LOGIN Y PANEL TOTAL
# ─────────────────────────────────────────
import streamlit as st
import sys
import os
import re
import io
import bcrypt
import random
import string
import pdfplumber
from pypdf import PdfReader
from datetime import datetime

sys.path.append(".")
from assets.estilos import aplicar_estilos
from components.footer import mostrar_pie
from core.database import run_query, get_connection
from core.auth import login, cerrar_sesion, es_admin, enviar_correo_recuperacion, actualizar_password_recuperacion

aplicar_estilos()

CARPETA_UPLOADS = "data/uploads"
os.makedirs(CARPETA_UPLOADS, exist_ok=True)

def extraer_contenido_pdf(pdf_file):
    texto_completo = ""
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto: texto_completo += texto + "\n"
    resultado = {'competencias': '', 'resultados': '', 'contenidos': ''}
    
    match_comp = re.search(r'COMPETENCIAS.*?TRIBUTA.*?ASIGNATURA(.*?)(?:PRESENTACI[ÓO]N|3\.\s*PRESEN)', texto_completo, re.DOTALL | re.IGNORECASE)
    if match_comp: resultado['competencias'] = match_comp.group(1).strip()
    
    match_res = re.search(r'RESULTADOS\s+DE\s+APRENDIZAJE.*?TRIBUTA.*?ASIGNATURA(.*?)(?:OBJETIVOS|5\.\s*OBJETIVOS)', texto_completo, re.DOTALL | re.IGNORECASE)
    if match_res: resultado['resultados'] = match_res.group(1).strip()
    
    match_cont = re.search(r'CONTENIDOS\s+TEM[ÁA]TICOS.*?\(UNIDADES\)(.*?)(?:METODOLOG[ÍI]AS|7\.\s*METO)', texto_completo, re.DOTALL | re.IGNORECASE)
    if match_cont: resultado['contenidos'] = match_cont.group(1).strip()
    return resultado

# ─────────────────────────────────────────
# VISTA 1: USUARIO LOGUEADO (PANEL COMPLETO)
# ─────────────────────────────────────────
if st.session_state.get('logueado', False):
    st.title("🛠 Panel de Administración")
    st.markdown(f"Bienvenido al sistema, **{st.session_state.get('usuario_nombre', '')}**")
    st.divider()
    
    rol_actual = st.session_state.get('usuario_rol', '')
    es_super = (rol_actual == 'superadmin')
    es_admin_rol = (rol_actual == 'admin')
    puede_gestionar_docs = es_super or es_admin_rol
    
    nombres_tabs = ["⚙️ Configuración", "📋 Gestionar Documentos", "👤 Mi Perfil"]
    if es_super:
        nombres_tabs.append("👥 Control de la Plataforma")
        
    tabs_panel = st.tabs(nombres_tabs)
    tab1 = tabs_panel[0]
    tab2 = tabs_panel[1]
    tab3 = tabs_panel[2]
    if es_super:
        tab4 = tabs_panel[3]

    # ═════════════════════════════════════════
    # PESTAÑA 1: CONFIGURACIÓN DE MÓDULOS
    # ═════════════════════════════════════════
    with tab1:
        st.markdown("### Define qué módulos están visibles para los usuarios.")
        config = run_query("SELECT modulo, visible, descripcion FROM configuracion ORDER BY id")
        cambios = {}
        with st.container(border=True):
            for item in config:
                col1, col2 = st.columns(2)
                with col1: st.markdown(f"**{item['descripcion']}**")
                with col2:
                    estado = st.checkbox("Visible", value=bool(item['visible']), key=f"chk_{item['modulo']}")
                    cambios[item['modulo']] = estado
            st.markdown("---")
            if st.button("💾 Guardar configuración", type="primary", use_container_width=True):
                conn = get_connection()
                if conn:
                    try:
                        with conn.cursor() as cursor:
                            for modulo, visible in cambios.items():
                                cursor.execute("UPDATE configuracion SET visible = %s WHERE modulo = %s", (1 if visible else 0, modulo))
                        st.success("✅ Configuración guardada correctamente.")
                    except Exception as e: st.error(f"❌ Error al guardar: {e}")
                    finally: conn.close()

    # ═════════════════════════════════════════
    # PESTAÑA 2: GESTIONAR DOCUMENTOS (PDF)
    # ═════════════════════════════════════════
    with tab2:
        if not puede_gestionar_docs:
            st.warning("🔒 No tienes permisos para gestionar documentos. Contacta al administrador.")
            st.stop()
            
        st.markdown("### Sube el PDF del documento aprobado.")
        programas = run_query("SELECT id, nombre, codigo FROM programas ORDER BY nombre")
        
        if programas:
            etiquetas = [f"{p['nombre']} ({p['codigo']})" for p in programas]
            seleccion = st.selectbox("Selecciona el programa:", etiquetas, key="prog_doc")
            prog = programas[etiquetas.index(seleccion)]
            
            materias = run_query("""
                SELECT m.id, m.nombre, m.codigo,
                (SELECT MAX(d.version) FROM documentos d WHERE d.materia_id = m.id AND d.activo = 1) AS version_actual
                FROM materias m WHERE m.programa_id = %s ORDER BY m.periodo, m.nombre
            """, (prog['id'],))
            
            CODIGO_REQUERIDO = "Código: FD-GC70"
            
            for m_item in materias:
                key_exito = f"guardado_ok_{m_item['id']}"
                v_act = m_item['version_actual']
                
                if st.session_state.get(key_exito, False):
                    v_act = st.session_state.get(f"v_nueva_temp_{m_item['id']}", '08')
                    
                emoji = "🔴" if v_act is None else ("🟢" if v_act == '08' else "🟡")
                txt_v = "Sin documento" if v_act is None else f"v{v_act}"
                
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{m_item['nombre']}**")
                        st.caption(f"Código: {m_item['codigo']}")
                    with c2:
                        st.markdown(f"{emoji} {txt_v}")
                        
                    pdf_file = st.file_uploader(
                        "📎 Selecciona el PDF:",
                        type=['pdf'],
                        key=f"pdf_{m_item['id']}"
                    )
                    
                    if pdf_file:
                        pdf_bytes = io.BytesIO(pdf_file.read())
                        reader = PdfReader(pdf_bytes)
                        texto_validacion = ""
                        for page in reader.pages:
                            t = page.extract_text()
                            if t: texto_validacion += t
                            
                        if CODIGO_REQUERIDO not in texto_validacion:
                            st.error("Error: El documento no se puede subir.")
                        else:
                            if st.session_state.get(key_exito, False):
                                st.success(f"✅ ¡El documento para **{m_item['nombre']}** se guardó exitosamente!")
                            else:
                                st.warning(f" ¿Desea guardar **{pdf_file.name}** para **{m_item['nombre']}**?")
                                col_si, col_no = st.columns(2)
                                
                                with col_si:
                                    if st.button(" Sí, guardar", type="primary", use_container_width=True, key=f"btn_si_{m_item['id']}"):
                                        pdf_file.seek(0)
                                        contenido = extraer_contenido_pdf(pdf_file)
                                        conn = get_connection()
                                        if conn:
                                            try:
                                                with conn.cursor() as cursor:
                                                    match_version = re.search(r'Versi[oó]n:\s*(\d+)', texto_validacion, re.IGNORECASE)
                                                    if match_version:
                                                        version_extraida = match_version.group(1).zfill(2)
                                                    else:
                                                        version_extraida = "08"
                                                    
                                                    version_anterior = m_item['version_actual'] if m_item['version_actual'] else "Sin documento previo"
                                                    
                                                    if version_anterior == version_extraida:
                                                        historial_txt = f"Se volvió a cargar la versión v{version_extraida}."
                                                    else:
                                                        historial_txt = f"Cambio de versión detectado: v{version_anterior} ➡️ v{version_extraida}."

                                                    cursor.execute("UPDATE documentos SET activo = 0 WHERE materia_id = %s", (m_item['id'],))
                                                    fn = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{m_item['codigo']}_v{version_extraida}.pdf"
                                                    rp = os.path.join(CARPETA_UPLOADS, fn)
                                                    with open(rp, "wb") as f: 
                                                        f.write(pdf_bytes.getvalue())
                                                        
                                                    admin_actual = st.session_state.get('usuario_nombre', 'Superadmin')
                                                    cursor.execute("""
                                                        INSERT INTO documentos (materia_id, version, ruta_pdf, activo, creado_por, historial_version)
                                                        VALUES (%s, %s, %s, 1, %s, %s)
                                                    """, (m_item['id'], version_extraida, rp, admin_actual, historial_txt))
                                                    d_id = cursor.lastrowid
                                                    
                                                    comp = contenido.get('competencias', '').strip()
                                                    res = contenido.get('resultados', '').strip()
                                                    cont = contenido.get('contenidos', '').strip()
                                                    
                                                    if comp: cursor.execute("INSERT INTO contenidos (documento_id, tipo, texto) VALUES (%s, 'competencia', %s)", (d_id, comp))
                                                    if res: cursor.execute("INSERT INTO contenidos (documento_id, tipo, texto) VALUES (%s, 'resultado', %s)", (d_id, res))
                                                    if cont:
                                                        for line in cont.split('\n'):
                                                            if line.strip(): cursor.execute("INSERT INTO contenidos (documento_id, tipo, texto) VALUES (%s, 'contenido', %s)", (d_id, line.strip()))
                                                    
                                                    st.session_state[key_exito] = True
                                                    st.session_state[f"v_nueva_temp_{m_item['id']}"] = version_extraida
                                                    st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Error: {e}")
                                            finally:
                                                conn.close()
                                                
                                with col_no:
                                    if st.button("❌ No, cancelar", use_container_width=True, key=f"btn_no_{m_item['id']}"):
                                        st.rerun()
        else:
            st.info("No hay programas registrados todavía.")

    # ═════════════════════════════════════════
    # PESTAÑA 3: PERFIL DE USUARIO
    # ═════════════════════════════════════════
    with tab3:
        st.markdown("### Gestiona tus datos de acceso.")
        with st.container(border=True):
            st.markdown(f"**Nombre:** {st.session_state.get('usuario_nombre', '')}")
            st.markdown(f"**Correo:** {st.session_state.get('usuario_correo', '')}")
            st.markdown(f"**Rol:** {st.session_state.get('usuario_rol', '')}")
            st.markdown("#### 🔒 Cambiar Contraseña")
            with st.container(border=True):
                nueva_pwd_perfil = st.text_input("Nueva contraseña:", type="password", key="new_pwd_perf")
                confirmar_pwd_perfil = st.text_input("Confirmar nueva contraseña:", type="password", key="conf_pwd_perf")
                if st.button("Actualizar mi contraseña", type="primary", use_container_width=True):
                    if not nueva_pwd_perfil or not confirmar_pwd_perfil: st.error("⚠️ Rellena ambos campos.")
                    elif nueva_pwd_perfil != confirmar_pwd_perfil: st.error("❌ Las contraseñas no coinciden.")
                    elif len(nueva_pwd_perfil) < 6: st.error("⚠️ Al menos 6 caracteres.")
                    else:
                        with st.spinner("Actualizando..."):
                            correo_actual = st.session_state.get('usuario_correo', '')
                            if actualizar_password_recuperacion(correo_actual, nueva_pwd_perfil):
                                st.success("✅ Actualizada.")
                            else: st.error("❌ Error en Base de Datos.")
            st.markdown("---")
            if st.button("🚪 Cerrar Sesión del Sistema", type="secondary", use_container_width=True):
                cerrar_sesion()
                st.rerun()

    # ═════════════════════════════════════════
    # PESTAÑA 4: CONTROL DE LA PLATAFORMA (SOLO SUPERADMIN)
    # ═════════════════════════════════════════
    if es_super:
        with tab4:
            st.markdown("### Gestión de Estructura Académica y Usuarios")
            sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🎓 Registrar Nuevos", "✏️ Modificar/Corregir", "👥 Estado Usuarios"])
            
            with sub_tab1:
                with st.expander("🎓 Registrar Nuevo Programa Académico"):
                    prog_nombre = st.text_input("Nombre del Programa (Ej: Ingeniería Civil):", key="new_prog_nom")
                    prog_codigo = st.text_input("Código del Programa (Ej: 112A):", key="new_prog_cod")
                    if st.button("Guardar Programa Académico", type="primary", use_container_width=True):
                        if not prog_nombre or not prog_codigo: st.error("⚠️ Rellena los campos.")
                        else:
                            conn = get_connection()
                            if conn:
                                try:
                                    with conn.cursor() as cursor:
                                        cursor.execute("INSERT INTO programas (nombre, codigo) VALUES (%s, %s)", (prog_nombre.strip(), prog_codigo.strip().upper()))
                                    st.success("✅ Programa creado.")
                                except Exception: st.error("❌ Código duplicado.")
                                finally: conn.close()
                                
                with st.expander("📘 Registrar Nueva Materia para un Programa"):
                    progs_combobox = run_query("SELECT id, nombre, codigo FROM programas ORDER BY nombre")
                    if progs_combobox:
                        opciones_p = [f"{p['nombre']} ({p['codigo']})" for p in progs_combobox]
                        p_elegido = st.selectbox("Selecciona el programa:", opciones_p, key="sel_prog_mat")
                        id_programa_elegido = progs_combobox[opciones_p.index(p_elegido)]['id']
                        mat_nombre = st.text_input("Nombre de la materia:", key="new_mat_nom")
                        mat_codigo = st.text_input("Código de la materia:", key="new_mat_cod")
                        mat_periodo = st.number_input("Semestre:", min_value=1, max_value=10, value=1, key="new_mat_per")
                        mat_creditos = st.number_input("Créditos:", min_value=1, max_value=8, value=3, key="new_mat_cre")
                        if st.button("Guardar Materia", type="primary", use_container_width=True):
                            if not mat_nombre or not mat_codigo: st.error("⚠️ Rellena los campos.")
                            else:
                                conn = get_connection()
                                if conn:
                                    try:
                                        with conn.cursor() as cursor:
                                            cursor.execute("INSERT INTO materias (programa_id, nombre, codigo, periodo, creditos, nivel, version) VALUES (%s, %s, %s, %s, %s, 'Pregrado', '1')",
                                            (id_programa_elegido, mat_nombre.strip(), mat_codigo.strip().upper(), mat_periodo, mat_creditos))
                                        st.success("✅ Materia registrada.")
                                    except Exception: st.error("❌ Código duplicado.")
                                    finally: conn.close()
                    else: st.info("Crea un programa primero.")
                    
                with st.expander("👥 Registrar Nuevo Administrator / Coordinador"):
                    new_nom = st.text_input("Nombre completo:", key="usr_reg_nom")
                    new_cor = st.text_input("Correo institucional:", key="usr_reg_cor")
                    new_pass = st.text_input("Contraseña inicial:", type="password", key="usr_reg_pass")
                    if st.button("Registrar Usuario", type="primary", use_container_width=True):
                        if not new_nom or not new_cor or not new_pass: st.error("⚠️ Rellena los campos.")
                        elif not new_cor.endswith("@elpoli.edu.co"): st.error("⚠️ Correo institucional requerido.")
                        else:
                            hash_pwd = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            conn = get_connection()
                            if conn:
                                try:
                                    with conn.cursor() as cursor:
                                        cursor.execute("INSERT INTO usuarios (nombre, correo, password, rol, activo) VALUES (%s, %s, %s, 'admin', 1)", (new_nom, new_cor, hash_pwd))
                                    st.success("✅ Usuario creado.")
                                except Exception: st.error("❌ El correo ya existe.")
                                finally: conn.close()
                                
            with sub_tab2:
                st.markdown("#### ✏️ Corregir Datos Existentes")
                tipo_mod = st.radio("¿Qué deseas modificar?", ["Programa", "Materia", "Usuario/Administrador"], horizontal=True)
                if tipo_mod == "Programa":
                    progs_m = run_query("SELECT id, nombre, codigo FROM programas ORDER BY nombre")
                    if progs_m:
                        opc_p_m = [f"{p['nombre']} ({p['codigo']})" for p in progs_m]
                        p_sel_m = st.selectbox("Selecciona el programa a corregir:", opc_p_m)
                        p_data = progs_m[opc_p_m.index(p_sel_m)]
                        edit_p_nom = st.text_input("Corregir Nombre:", value=p_data['nombre'])
                        edit_p_cod = st.text_input("Corregir Código:", value=p_data['codigo'])
                        if st.button("💾 Actualizar Programa", type="primary", use_container_width=True):
                            conn = get_connection()
                            if conn:
                                try:
                                    with conn.cursor() as cursor:
                                        cursor.execute("UPDATE programas SET nombre = %s, codigo = %s WHERE id = %s", (edit_p_nom.strip(), edit_p_cod.strip().upper(), p_data['id']))
                                    st.success("✅ Guardado.")
                                except Exception as e: st.error(str(e))
                                finally: conn.close()
                elif tipo_mod == "Materia":
                    mats_m = run_query("SELECT id, nombre, codigo, periodo, creditos FROM materias ORDER BY nombre")
                    if mats_m:
                        opc_m_m = [f"{m['nombre']} ({m['codigo']})" for m in mats_m]
                        m_sel_m = st.selectbox("Selecciona la materia a corregir:", opc_m_m)
                        m_data = mats_m[opc_m_m.index(m_sel_m)]
                        edit_m_nom = st.text_input("Corregir Nombre:", value=m_data['nombre'])
                        edit_m_cod = st.text_input("Corregir Código:", value=m_data['codigo'])
                        edit_m_per = st.number_input("Semestre:", min_value=1, max_value=10, value=int(m_data['periodo']))
                        edit_m_cre = st.number_input("Créditos:", min_value=1, max_value=8, value=int(m_data['creditos']))
                        if st.button("💾 Actualizar Materia", type="primary", use_container_width=True):
                            conn = get_connection()
                            if conn:
                                try:
                                    with conn.cursor() as cursor:
                                        cursor.execute("UPDATE materias SET nombre = %s, codigo = %s, periodo = %s, creditos = %s WHERE id = %s", (edit_m_nom.strip(), edit_m_cod.strip().upper(), edit_m_per, edit_m_cre, m_data['id']))
                                    st.success("✅ Guardada.")
                                except Exception as e: st.error(str(e))
                                finally: conn.close()
                else:
                    usrs_m = run_query("SELECT id, nombre, correo FROM usuarios WHERE rol != 'superadmin' ORDER BY nombre")
                    if usrs_m:
                        opc_u_m = [f"{u['nombre']} ({u['correo']})" for u in usrs_m]
                        u_sel_m = st.selectbox("Selecciona el usuario a corregir:", opc_u_m)
                        u_data = usrs_m[opc_u_m.index(u_sel_m)]
                        edit_u_nom = st.text_input("Corregir Nombre del Administrador:", value=u_data['nombre'])
                        edit_u_cor = st.text_input("Corregir Correo del Administrador:", value=u_data['correo'])
                        if st.button("💾 Actualizar Datos de Administrador", type="primary", use_container_width=True):
                            if not edit_u_cor.endswith("@elpoli.edu.co"): st.error("⚠️ Debe terminar en @elpoli.edu.co")
                            else:
                                conn = get_connection()
                                if conn:
                                    try:
                                        with conn.cursor() as cursor:
                                            cursor.execute("UPDATE usuarios SET nombre = %s, correo = %s WHERE id = %s", (edit_u_nom.strip(), edit_u_cor.strip(), u_data['id']))
                                        st.success("✅ Administrador actualizado.")
                                    except Exception: st.error("❌ El correo ya está registrado en otro usuario.")
                                    finally: conn.close()
                    else: st.info("No hay usuarios registrados para modificar.")
                    
            with sub_tab3:
                st.markdown("#### Lista de Usuarios en el Sistema")
                usuarios_lista = run_query("SELECT id, nombre, correo, rol, activo FROM usuarios WHERE rol != 'superadmin' ORDER BY nombre")
                for u in usuarios_lista:
                    txt_act = "🟢 Activo" if u['activo'] == 1 else "🔴 Inactivo"
                    lbl_btn = "Desactivar" if u['activo'] == 1 else "Activar"
                    nuevo_estado = 0 if u['activo'] == 1 else 1
                    with st.container(border=True):
                        col_u1, col_u2, col_u3 = st.columns(3)
                        with col_u1: 
                            st.markdown(f"**{u['nombre']}**")
                            st.caption(f"Correo: {u['correo']}")
                        with col_u2: st.markdown(f"Rol: `{u['rol']}` | Estado: **{txt_act}**")
                        with col_u3:
                            if st.button(lbl_btn, key=f"btn_act_{u['id']}", use_container_width=True):
                                conn = get_connection()
                                if conn:
                                    try:
                                        with conn.cursor() as cursor:
                                            cursor.execute("UPDATE usuarios SET activo = %s WHERE id = %s", (nuevo_estado, u['id']))
                                        st.success("Estado cambiado.")
                                    except Exception as e: st.error(str(e))
                                    finally: conn.close()
    mostrar_pie()

# ─────────────────────────────────────────
# VISTA 2: FORMULARIO DE LOGIN (USUARIO NO LOGUEADO)
# ─────────────────────────────────────────
else:
    st.title("🔐 Iniciar Sesión")
    with st.container(border=True):
        correo = st.text_input("📧 Correo institucional", placeholder="ejemplo@elpoli.edu.co")
        password = st.text_input("🔑 Contraseña", type="password", placeholder="Tu contraseña")
        if st.button("Ingresar al Panel", type="primary", use_container_width=True):
            if not correo or not password: st.error("⚠️ Completa los campos.")
            elif not correo.endswith("@elpoli.edu.co"): st.error("⚠️ Solo correos @elpoli.edu.co")
            else:
                exito, mensaje = login(correo, password)
                if exito: 
                    st.success("¡Bienvenido!")
                    st.rerun()
                else: st.error(f"❌ {mensaje}")
                
    with st.expander("🔑 ¿Olvidaste tu contraseña?"):
        correo_recup = st.text_input("📧 Correo a recuperar:", key="email_recup_input")
        if st.button("Enviar nueva contraseña por correo", type="secondary", use_container_width=True):
            if not correo_recup: st.error("⚠️ Escribe tu correo.")
            else:
                existe = run_query("SELECT id FROM usuarios WHERE correo = %s AND activo = 1", (correo_recup,))
                if not existe: st.error("❌ Correo no registrado o inactivo.")
                else:
                    clave_temporal = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
                    if actualizar_password_recuperacion(correo_recup, clave_temporal):
                        if enviar_correo_recuperacion(correo_recup, clave_temporal): 
                            st.success("✅ Clave temporal enviada a tu correo.")
                        else: st.error("❌ Error SMTP al enviar. Verifica las credenciales.")
                    else: st.error("❌ Error en Base de Datos.")
    mostrar_pie()
