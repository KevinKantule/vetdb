# app/common.py
"""
Funciones de conexión y ejecución de consultas a Snowflake, usando autenticación por key-pair con pool.
"""
import streamlit as st
from snowflake.connector import connect
from cryptography.hazmat.primitives import serialization
import pandas as pd

@st.cache_resource
# @st.experimental_singleton para versiones antiguas
def get_connection():
    """
    Retorna una conexión singleton a Snowflake usando key-pair en formato DER.
    """
    cfg = st.secrets['snowflake']
    conn_kwargs = {
        'user': cfg['user'],
        'account': cfg['account'],
        'warehouse': cfg['warehouse'],
        'database': cfg['database'],
        'schema': cfg['schema'],
        'role': cfg.get('role')
    }
    # Autenticación con par de claves (DER)
    pk_path = cfg.get('private_key_path')
    if pk_path:
        with open(pk_path, 'rb') as key_file:
            p_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
            )
        der_key = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        conn_kwargs['private_key'] = der_key
    else:
        passwd = cfg.get('password')
        if not passwd:
            raise ValueError("Se requiere password o private_key_path en los secrets.")
        conn_kwargs['password'] = passwd
    return connect(**conn_kwargs)


def run_query(sql: str, params: tuple = None) -> pd.DataFrame:
    """
    Ejecuta una consulta SELECT y devuelve un DataFrame.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, params or ())
        cols = [c[0] for c in cur.description]
        data = cur.fetchall()
        return pd.DataFrame(data, columns=cols)
    finally:
        cur.close()
