import streamlit as st

# ─────────────────────────────────────────
# COMPONENTE: PIE DE PÁGINA
# Reutilizable en todas las páginas
# ─────────────────────────────────────────
def mostrar_pie():
    st.markdown("""
        <div style='
            text-align: center;
            padding: 16px;
            margin-top: 20px;
            border: 1px solid #d4a017;
            border-top: 4px solid #d4a017;
            background-color: #f0f5ea;
            border-radius: 8px;
            font-size: 13px;
            color: #5a7a4a;
        '>
            📚 <b style='color:#2d5a1b;'>Gestor de Contenidos Académicos</b>
            · Politécnico Colombiano Jaime Isaza Cadavid<br>
            <b style='color:#2d5a1b;'>Viviana Montoya Marín</b><br>
            <span style='color:#888; font-size:11px;'>
                Streamlit · MySQL · IA con Groq/LLaMA
            </span>
        </div>
    """, unsafe_allow_html=True)