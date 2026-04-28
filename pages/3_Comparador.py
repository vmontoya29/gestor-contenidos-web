import streamlit as st
import sys
sys.path.append(".")
from core.database import run_query  # Función para consultar la base de datos

# ─────────────────────────────────────────
# TÍTULO Y DESCRIPCIÓN DE LA PÁGINA
# ─────────────────────────────────────────
st.title("🔍 Comparador de Contenidos")
st.markdown("Compara las materias de dos programas académicos.")
st.divider()

# ─────────────────────────────────────────
# CARGAR TODOS LOS PROGRAMAS
# ─────────────────────────────────────────
programas = run_query("SELECT id, nombre, codigo FROM programas ORDER BY nombre")

if not programas:
    st.warning("No se encontraron programas.")
else:
    # Crear etiquetas únicas con nombre + código para el selector
    etiquetas = [f"{p['nombre']} ({p['codigo']})" for p in programas]

    # ─────────────────────────────────────────
    # SELECCIÓN DE DOS PROGRAMAS A COMPARAR
    # ─────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        sel1 = st.selectbox("Programa 1:", etiquetas, key="prog1")
    with col2:
        sel2 = st.selectbox("Programa 2:", etiquetas, key="prog2", index=1)

    # Obtener los datos completos usando el índice de la etiqueta
    prog1 = programas[etiquetas.index(sel1)]
    prog2 = programas[etiquetas.index(sel2)]

    if prog1['id'] == prog2['id']:
        st.warning("Selecciona dos programas diferentes para comparar.")
    else:
        # ─────────────────────────────────────────
        # CONSULTAR MATERIAS DE CADA PROGRAMA
        # ─────────────────────────────────────────
        def get_materias(programa_id):
            """Obtiene todas las materias de un programa con su estado"""
            return run_query("""
                SELECT m.nombre, m.codigo, m.periodo, m.creditos,
                       d.version as version_doc
                FROM materias m
                LEFT JOIN documentos d ON d.materia_id = m.id
                WHERE m.programa_id = %s
                ORDER BY m.periodo, m.nombre
            """, (programa_id,))

        materias1 = get_materias(prog1['id'])
        materias2 = get_materias(prog2['id'])

        # Extraer solo los nombres para comparar
        nombres1 = set(m['nombre'].upper().strip() for m in materias1)
        nombres2 = set(m['nombre'].upper().strip() for m in materias2)

        # ─────────────────────────────────────────
        # CALCULAR SIMILITUDES Y DIFERENCIAS
        # ─────────────────────────────────────────
        en_comun = nombres1 & nombres2
        solo_en_1 = nombres1 - nombres2
        solo_en_2 = nombres2 - nombres1

        # Mostrar métricas de comparación
        c1, c2, c3 = st.columns(3)
        c1.metric("En común", len(en_comun))
        c2.metric(f"Solo en {prog1['codigo']}", len(solo_en_1))
        c3.metric(f"Solo en {prog2['codigo']}", len(solo_en_2))

        st.divider()

        # ─────────────────────────────────────────
        # MOSTRAR MATERIAS EN COMÚN
        # ─────────────────────────────────────────
        if en_comun:
            with st.expander(f"✅ Materias en común ({len(en_comun)})", expanded=True):
                for nombre in sorted(en_comun):
                    st.markdown(f"- {nombre.title()}")

        # ─────────────────────────────────────────
        # MOSTRAR MATERIAS ÚNICAS DE CADA PROGRAMA
        # ─────────────────────────────────────────
        col_a, col_b = st.columns(2)

        with col_a:
            with st.expander(f"📘 Solo en {prog1['nombre']} ({len(solo_en_1)})"):
                for nombre in sorted(solo_en_1):
                    st.markdown(f"- {nombre.title()}")

        with col_b:
            with st.expander(f"📗 Solo en {prog2['nombre']} ({len(solo_en_2)})"):
                for nombre in sorted(solo_en_2):
                    st.markdown(f"- {nombre.title()}")

        st.divider()

        # ─────────────────────────────────────────
        # TABLA COMPARATIVA LADO A LADO
        # ─────────────────────────────────────────
        st.subheader("Tabla comparativa por semestre")

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown(f"**{prog1['nombre']} ({prog1['codigo']})**")
            for m in materias1:
                estado = "✅ V" + m['version_doc'] if m['version_doc'] else "❌"
                st.markdown(f"S{m['periodo']} — {m['nombre']} {estado}")

        with col_b:
            st.markdown(f"**{prog2['nombre']} ({prog2['codigo']})**")
            for m in materias2:
                estado = "✅ V" + m['version_doc'] if m['version_doc'] else "❌"
                st.markdown(f"S{m['periodo']} — {m['nombre']} {estado}")