# app/common.py
import streamlit as st
from snowflake.connector import connect
from cryptography.hazmat.primitives import serialization
import pandas as pd

@st.cache_resource
def get_connection():
    """
    Retorna una única conexión (singleton) a Snowflake usando key-pair o password.
    Streamlit se encarga de cachear este recurso para toda la sesión.
    """
    cfg = st.secrets['snowflake']
    conn_kwargs = {
        'user':    cfg['user'],
        'account': cfg['account'],
        'warehouse': cfg['warehouse'],
        'database':  cfg['database'],
        'schema':    cfg['schema'],
        'role':      cfg.get('role'),
    }
    # Key-pair
    pk_path = cfg.get('private_key_path')
    if pk_path:
        with open(pk_path, 'rb') as f:
            p_key = serialization.load_pem_private_key(f.read(), password=None)
        der = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        conn_kwargs['private_key'] = der
    else:
        pwd = cfg.get('password')
        if not pwd:
            raise ValueError("Se requiere password o private_key_path en los secrets.")
        conn_kwargs['password'] = pwd

    return connect(**conn_kwargs)

def run_query(sql: str, params: tuple = None) -> pd.DataFrame:
    """
    Ejecuta una consulta SELECT y devuelve un DataFrame.
    """
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(sql, params or ())
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)
    finally:
        cur.close()
