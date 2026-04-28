import pymysql
import streamlit as st

def get_connection():
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
    except Exception as e:
        return None

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