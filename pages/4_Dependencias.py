from components.footer import mostrar_pie
import streamlit as st
import sys
sys.path.append(".")
from core.database import run_query  # Función para consultar la base de datos

# ─────────────────────────────────────────
# TÍTULO Y DESCRIPCIÓN DE LA PÁGINA
# ─────────────────────────────────────────
st.title("🔗 Dependencias entre Materias")
st.markdown("Visualiza las materias por semestre y sus relaciones dentro de cada programa.")
st.divider()

# ─────────────────────────────────────────
# CARGAR TODOS LOS PROGRAMAS
# ─────────────────────────────────────────
programas = run_query("SELECT id, nombre, codigo FROM programas ORDER BY nombre")

if not programas:
    st.warning("No se encontraron programas.")
else:
    # Crear etiquetas únicas con nombre + código
    etiquetas = [f"{p['nombre']} ({p['codigo']})" for p in programas]
    seleccion = st.selectbox("Selecciona un programa:", etiquetas)
    prog = programas[etiquetas.index(seleccion)]

    # ─────────────────────────────────────────
    # CONSULTAR MATERIAS DEL PROGRAMA
    # ─────────────────────────────────────────
    materias = run_query("""
        SELECT m.nombre, m.codigo, m.periodo, m.creditos, m.nivel,
               d.version as version_doc
        FROM materias m
        LEFT JOIN documentos d ON d.materia_id = m.id
        WHERE m.programa_id = %s
        ORDER BY m.periodo, m.nombre
    """, (prog['id'],))

    if not materias:
        st.warning("Este programa no tiene materias registradas.")
    else:
        # ─────────────────────────────────────────
        # MÉTRICAS GENERALES
        # ─────────────────────────────────────────
        total = len(materias)
        semestres = sorted(set(m['periodo'] for m in materias))
        con_contenido = sum(1 for m in materias if m['version_doc'])

        c1, c2, c3 = st.columns(3)
        c1.metric("Total materias", total)
        c2.metric("Semestres", len(semestres))
        c3.metric("Con contenido", con_contenido)

        st.divider()

        # ─────────────────────────────────────────
        # FILTRO POR SEMESTRE
        # ─────────────────────────────────────────
        opciones = ["Todos los semestres"] + [f"Semestre {s}" for s in semestres]
        filtro = st.selectbox("Ver semestre:", opciones)

        st.divider()

        # ─────────────────────────────────────────
        # MOSTRAR MATERIAS POR SEMESTRE
        # ─────────────────────────────────────────
        for semestre in semestres:

            # Si hay filtro activo, saltar semestres que no coincidan
            if filtro != "Todos los semestres" and filtro != f"Semestre {semestre}":
                continue

            # Materias de este semestre
            materias_semestre = [m for m in materias if m['periodo'] == semestre]

            st.subheader(f"📅 Semestre {semestre}")

            # Mostrar cada materia como tarjeta
            cols = st.columns(3)
            for i, m in enumerate(materias_semestre):
                estado = "✅ V" + m['version_doc'] if m['version_doc'] else "❌ Sin contenido"
                creditos = m['creditos'] or 0

                # Determinar color de borde según estado
                if m['version_doc'] == '08':
                    borde = "🟢"  # Verde = versión 8
                elif m['version_doc']:
                    borde = "🟡"  # Amarillo = tiene contenido pero no v8
                else:
                    borde = "🔴"  # Rojo = sin contenido

                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"{borde} **{m['nombre']}**")
                        st.markdown(f"Código: `{m['codigo'] or 'N/A'}`")
                        st.markdown(f"Créditos: **{creditos}** | {estado}")

            st.divider()

        # ─────────────────────────────────────────
        # LEYENDA DE COLORES
        # ─────────────────────────────────────────
        st.markdown("**Leyenda:**  🟢 Versión 8  |  🟡 Tiene contenido (otra versión)  |  🔴 Sin contenido")

mostrar_pie()