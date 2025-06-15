# app/auth.py
"""
Módulo de autenticación: login y control de sesión.
"""
import streamlit as st
import hashlib
from common import run_query

def hash_password(password: str) -> str:
    """Genera SHA-256 hash de la contraseña."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(usuario: str, password: str):
    """
    Verifica las credenciales contra la tabla vet_usuario_sistema.
    Devuelve dict {'user_id', 'rol_id', 'rol_nombre'} o None.
    """
    # Obtiene user_id y rol_id
    sql = """
    SELECT user_id, rol_id
      FROM vet_usuario_sistema
     WHERE usuario = %s
    """
    df = run_query(sql, (usuario,))
    if df.empty:
        return None
    db_user_id = int(df.iloc[0]['USER_ID'])
    db_rol_id  = int(df.iloc[0]['ROL_ID'])

    # Obtiene el hash almacenado
    sql_hash = """
    SELECT pass_hash
      FROM vet_usuario_sistema
     WHERE user_id = %s
    """
    df_hash = run_query(sql_hash, (db_user_id,))
    stored_hash = df_hash.iloc[0]['PASS_HASH'].strip()

    # Compara
    if hash_password(password) == stored_hash:
        # Obtiene rol_nombre
        sql_rol = """
        SELECT rol_nombre
          FROM vet_rol
         WHERE rol_id = %s
        """
        df_rol = run_query(sql_rol, (db_rol_id,))
        rol_nombre = df_rol.iloc[0]['ROL_NOMBRE']
        return {
            'user_id': db_user_id,
            'rol_id': db_rol_id,
            'rol_nombre': rol_nombre
        }
    return None

def login_page():
    # 1) Si ya está en session_state, no mostramos nada de login
    if st.session_state.get("authenticated"):
        return

    # 2) Sólo si NO está autenticado mostramos el formulario
    st.title("Login - VetDB")
    usuario = st.text_input("Usuario", key="login_user")
    password = st.text_input("Contraseña", type="password", key="login_pass")

    if st.button("Ingresar"):
        creds = check_credentials(usuario, password)
        if creds:
            st.session_state["authenticated"] = True
            st.session_state["user"]          = usuario
            st.session_state["rol_id"]        = creds["rol_id"]
            # Asegúrate de normalizar el rol para que coincida con tus llaves:
            st.session_state["rol_nombre"]    = creds["rol_nombre"].capitalize()
        else:
            st.error("Usuario o contraseña incorrectos")

    # 3) Si aún no se autenticó, detenemos todo
    if not st.session_state.get("authenticated"):
        st.stop()


