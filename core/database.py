import pymysql  # Librería para conectarse a MySQL/MariaDB

# ─────────────────────────────────────────
# CONEXIÓN A LA BASE DE DATOS
# Retorna la conexión si es exitosa, o None si falla
# ─────────────────────────────────────────
def get_connection():
    try:
        conn = pymysql.connect(
            host="localhost",       # Servidor de base de datos (local)
            user="root",            # Usuario de MySQL
            password="",            # Contraseña (vacía en XAMPP por defecto)
            database="gestor_poli", # Nombre de la base de datos
            charset="utf8mb4",      # Codificación para caracteres especiales
            cursorclass=pymysql.cursors.DictCursor,  # Resultados como diccionario
            autocommit=True,        # Guardar cambios automáticamente
        )
        return conn
    except Exception as e:
        # Si falla la conexión, retorna None (no lanza error)
        return None

# ─────────────────────────────────────────
# EJECUTAR CONSULTA SQL
# query  → la consulta SQL a ejecutar
# params → valores para reemplazar los %s en la consulta
# Retorna lista de resultados o lista vacía si falla
# ─────────────────────────────────────────
def run_query(query, params=None):
    conn = get_connection()
    if not conn:
        return []  # Si no hay conexión, retorna vacío
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()  # Retorna todos los resultados
    except Exception as e:
        return []  # Si hay error en la consulta, retorna vacío
    finally:
        conn.close()  # Siempre cerrar la conexión al terminar