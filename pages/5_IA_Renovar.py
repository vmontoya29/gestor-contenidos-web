from components.footer import mostrar_pie
import streamlit as st
import sys
sys.path.append(".")
from core.database import run_query  # Función para consultar la base de datos
from groq import Groq                # Librería de Groq (IA gratuita)

# ─────────────────────────────────────────
# CONFIGURACIÓN DE GROQ
# ─────────────────────────────────────────
client = Groq(api_key=st.secrets["groq"]["api_key"])

# ─────────────────────────────────────────
# TÍTULO Y DESCRIPCIÓN DE LA PÁGINA
# ─────────────────────────────────────────
st.title("🤖 IA — Renovar Asignatura")
st.markdown("Selecciona una asignatura y la IA propone una versión actualizada.")
st.divider()

# ─────────────────────────────────────────
# SELECCIONAR PROGRAMA Y MATERIA
# ─────────────────────────────────────────
programas = run_query("SELECT id, nombre, codigo FROM programas ORDER BY nombre")
etiquetas = [f"{p['nombre']} ({p['codigo']})" for p in programas]
seleccion = st.selectbox("Selecciona el programa:", etiquetas)
prog = programas[etiquetas.index(seleccion)]

materias = run_query("""
    SELECT m.id, m.nombre, m.codigo
    FROM materias m
    WHERE m.programa_id = %s
    ORDER BY m.nombre
""", (prog['id'],))

nombres_materias = [m['nombre'] for m in materias]
materia_sel = st.selectbox("Selecciona la asignatura:", nombres_materias)
materia = next(m for m in materias if m['nombre'] == materia_sel)

# ─────────────────────────────────────────
# CARGAR CONTENIDO ACTUAL DE LA MATERIA
# ─────────────────────────────────────────
contenidos = run_query("""
    SELECT c.tipo, c.texto
    FROM contenidos c
    JOIN documentos d ON c.documento_id = d.id
    WHERE d.materia_id = %s
""", (materia['id'],))

if contenidos:
    # Organizar contenidos por tipo
    competencias = " ".join(c['texto'] for c in contenidos if c['tipo'] == 'competencia')
    resultados = " ".join(c['texto'] for c in contenidos if c['tipo'] == 'resultado')
    contenido_list = [c['texto'] for c in contenidos if c['tipo'] == 'contenido']

    # Mostrar contenido actual de la asignatura
    with st.expander("📄 Ver contenido actual de la asignatura"):
        st.markdown("**Competencias:**")
        st.write(competencias or "No registradas")
        st.markdown("**Resultados de aprendizaje:**")
        st.write(resultados or "No registrados")
        st.markdown("**Contenidos:**")
        for i, c in enumerate(contenido_list, 1):
            st.markdown(f"{i}. {c}")

    st.divider()

    # ─────────────────────────────────────────
    # BOTÓN PARA GENERAR PROPUESTA CON IA
    # ─────────────────────────────────────────
    if st.button("🤖 Generar propuesta actualizada con IA"):
        with st.spinner("La IA está analizando y generando la propuesta..."):
            try:
                # Construir el prompt con el contenido actual
                prompt = f"""
Eres un experto en diseño curricular universitario.
Analiza el siguiente programa de asignatura y propón una versión actualizada
basada en las tendencias más recientes y metodologías modernas de enseñanza.

ASIGNATURA: {materia['nombre']}
CÓDIGO: {materia['codigo']}

COMPETENCIAS ACTUALES:
{competencias}

RESULTADOS DE APRENDIZAJE ACTUALES:
{resultados}

CONTENIDOS ACTUALES:
{chr(10).join(contenido_list)}

Por favor proporciona:
1. COMPETENCIAS ACTUALIZADAS
2. RESULTADOS DE APRENDIZAJE ACTUALIZADOS
3. CONTENIDOS ACTUALIZADOS con temas modernos
4. METODOLOGÍAS RECOMENDADAS
5. JUSTIFICACIÓN de los cambios

Responde en español y de forma estructurada.
"""
                # Llamar a Groq con modelo gratuito llama
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                # Guardar propuesta en session state
                propuesta = response.choices[0].message.content
                st.session_state['propuesta'] = propuesta

            except Exception as e:
                st.error(f"Error al conectar con la IA: {e}")

    # ─────────────────────────────────────────
    # MOSTRAR PROPUESTA Y BOTÓN DE APROBACIÓN
    # ─────────────────────────────────────────
    if 'propuesta' in st.session_state:
        st.subheader("📋 Propuesta generada por la IA")
        st.markdown(st.session_state['propuesta'])
        st.divider()
        st.warning("⚠️ Revisa la propuesta antes de aprobarla.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Aprobar propuesta"):
                st.success("✅ Propuesta aprobada exitosamente.")
                st.balloons()
                del st.session_state['propuesta']
        with col2:
            if st.button("❌ Rechazar propuesta"):
                st.info("Propuesta rechazada. Puedes generar una nueva.")
                del st.session_state['propuesta']
else:
    st.warning("Esta asignatura no tiene contenido cargado aún.")

mostrar_pie()