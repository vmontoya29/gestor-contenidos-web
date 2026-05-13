import pymysql
import streamlit as st

# ─────────────────────────────────────────
# CONEXIÓN A LA BASE DE DATOS
# Funciona tanto en LOCAL (XAMPP) como en
# PRODUCCIÓN (Streamlit Cloud con secrets)
# ─────────────────────────────────────────
def get_connection():
    try:
        # Intentar leer credenciales desde secrets.toml (para Streamlit Cloud)
        try:
            db = st.secrets["database"]
            conn = pymysql.connect(
                host=db["host"],
                port=int(db["port"]),
                user=db["user"],
                password=db["password"],
                database=db["database"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )
            return conn
        
        # Si no hay secrets.toml, usar configuración LOCAL (XAMPP)
        except Exception:
            conn = pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="",
                database="gestor_poli",
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )
            return conn
    
    except Exception as e:
        return None


# ─────────────────────────────────────────
# EJECUTAR CONSULTA SQL
# Recibe una consulta y parámetros opcionales
# ─────────────────────────────────────────
def run_query(query, params=None):
    conn = get_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    except Exception as e:
        return []
    finally:
        conn.close()