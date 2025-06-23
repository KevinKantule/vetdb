# app/auth.py
import streamlit as st
import hashlib
from common import run_query

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(usuario: str, password: str):
    sql = """
    SELECT u.user_id,
           u.rol_id,
           r.rol_nombre,
           u.pass_hash
      FROM vet_usuario_sistema AS u
 LEFT JOIN vet_rol             AS r
        ON u.rol_id = r.rol_id
     WHERE u.usuario = %s
    """
    df = run_query(sql, (usuario,))
    if df.empty:
        return None
    row = df.iloc[0]
    if hash_password(password) != row["PASS_HASH"]:
        return None
    rol_nombre = (row["ROL_NOMBRE"] or "SinRol").capitalize()
    return {
        "user_id":    int(row["USER_ID"]),
        "rol_id":     int(row["ROL_ID"]),
        "rol_nombre": rol_nombre
    }

def login_page():
    # Si ya estamos autenticados no mostramos nada
    if st.session_state.get("authenticated"):
        return

    st.title("Login — VetDB")
    # Aquí abrimos el form
    with st.form("login_form"):
        usuario  = st.text_input("Usuario", key="login_user")
        password = st.text_input("Contraseña", type="password", key="login_pass")
        send     = st.form_submit_button("Ingresar")

    # Sólo procesamos cuando se envía el form
    if send:
        creds = check_credentials(usuario, password)
        if creds:
            st.session_state["authenticated"] = True
            st.session_state["user"]          = usuario
            st.session_state["rol_id"]        = creds["rol_id"]
            st.session_state["rol_nombre"]    = creds["rol_nombre"]
        else:
            st.error("Usuario o contraseña incorrectos")

    # Si después de intentar aún no estamos autenticados, cortamos aquí
    if not st.session_state.get("authenticated"):
        st.stop()
