from components.footer import mostrar_pie
import streamlit as st
import sys
sys.path.append(".")
from core.database import run_query  # Función para consultar la base de datos

# ─────────────────────────────────────────
# TÍTULO Y DESCRIPCIÓN DE LA PÁGINA
# ─────────────────────────────────────────
st.title("📊 Dashboard General")
st.markdown("Resumen del estado de todos los programas académicos.")
st.divider()

# ─────────────────────────────────────────
# CARGAR TODOS LOS PROGRAMAS DE LA BD
# ─────────────────────────────────────────
programas = run_query("SELECT id, nombre, codigo FROM programas ORDER BY nombre")

if not programas:
    st.warning("No se encontraron programas en la base de datos.")
else:
    # Recorrer cada programa y mostrar su tarjeta de resumen
    for prog in programas:

        # Total de materias del programa
        total = run_query(
            "SELECT COUNT(*) as total FROM materias WHERE programa_id = %s",
            (prog['id'],)
        )

        # Materias sin ningún documento cargado
        sin_contenido = run_query(
            """SELECT COUNT(*) as total FROM materias m
               WHERE m.programa_id = %s
               AND NOT EXISTS (
                   SELECT 1 FROM documentos d WHERE d.materia_id = m.id
               )""",
            (prog['id'],)
        )

        # Materias que ya están en versión 8
        con_v8 = run_query(
            """SELECT COUNT(*) as total FROM materias m
               JOIN documentos d ON d.materia_id = m.id
               WHERE m.programa_id = %s AND d.version = '08'""",
            (prog['id'],)
        )

        # Extraer los números de cada consulta
        total_n = total[0]['total'] if total else 0
        sin_n = sin_contenido[0]['total'] if sin_contenido else 0
        v8_n = con_v8[0]['total'] if con_v8 else 0
        con_n = total_n - sin_n

        # Calcular porcentaje de materias con contenido
        pct = int((con_n / total_n) * 100) if total_n > 0 else 0

        # ─────────────────────────────────────────
        # TARJETA DE CADA PROGRAMA
        # ─────────────────────────────────────────
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)

            # Nombre y código del programa
            col1.markdown(f"**{prog['nombre']}**  \nCódigo: `{prog['codigo']}`")

            # Métricas principales
            col2.metric("Total materias", total_n)
            col3.metric("Sin contenido", sin_n,
                        delta=f"-{sin_n}" if sin_n > 0 else "0",
                        delta_color="inverse")
            col4.metric("En versión 8", v8_n)

            # Barra de progreso con porcentaje
            st.progress(pct, text=f"{pct}% con contenido cargado")
            
mostrar_pie()