# app/main.py
import streamlit as st
from auth import login_page
from crud.duenos import list_duenos, create_dueno, update_dueno, delete_dueno
from common import run_query

# Intentamos el login; detiene la app si no autenticado
login_page()

# Sidebar: actualiza paginación y filtro para Dueños
st.sidebar.header("Parámetros de lista de Dueños")
filtro = st.sidebar.text_input("Buscar por nombre", key="filter_duenos")
limit = st.sidebar.number_input("Filas a mostrar", min_value=1, max_value=100, value=5, step=1, key="limit_duenos")
offset = st.sidebar.number_input("Offset", min_value=0, step=1, value=0, key="offset_duenos")

# Título principal
st.title("Sistema de Gestión Veterinaria")

# Menú principal
def main_menu():
    # Mapeamos siempre en minúsculas
    opciones_por_rol = {
        'admin':       ['Dueños', 'Mascotas', 'Citas', 'Reportes'],
        'recepcion':   ['Dueños', 'Mascotas', 'Citas'],
        'veterinario': ['Mascotas', 'Citas']
    }
    rol = st.session_state.get('rol_nombre', '').lower()
    # Si no existe la clave, devolvemos al menos un menú vacío para ver que carga.
    return st.sidebar.radio("Menú", opciones_por_rol.get(rol, []), key="menu")



def app():
    opcion = main_menu()

    if opcion == 'Dueños':
        st.header("Gestión de Dueños")
        # Listado con paginación y filtro
        try:
            df = list_duenos(limit=int(limit), offset=int(offset), filtro=filtro)
            st.dataframe(df)
        except Exception as e:
            st.error("Error al cargar la lista de dueños. Revisa los logs.")
            st.write(e)

        # Crear nuevo dueño
        with st.expander("Agregar nuevo dueño"):
            nombre     = st.text_input("Nombre", key="new_nombre")
            telefono   = st.text_input("Teléfono", key="new_telefono")
            correo     = st.text_input("Correo", key="new_correo")
            direccion  = st.text_input("Dirección", key="new_direccion")
            documento  = st.text_input("Documento ID", key="new_documento")

            if st.button("Crear", key="btn_create_dueno"):
                # 1) Pre‐chequeo de duplicados
                dup = run_query(
                    "SELECT 1 FROM vet_dueno WHERE documento_id = %s",
                    (documento,)
                )
                if not dup.empty:
                    st.error("Ya existe un dueño con ese Documento ID")
                else:
                    # 2) Invoca a tu capa CRUD y captura errores
                    try:
                        create_dueno(nombre, telefono, correo, direccion, documento)
                        st.success("Dueño creado exitosamente")
                    except ValueError as ve:
                        st.error(f"Error de validación: {ve}")
                    except Exception as e:
                        st.error("Error inesperado al crear dueño. Revisa los logs.")
                        st.write(e)
                # Refrescar
                #df = list_duenos(limit=int(limit), offset=int(offset), filtro=filtro)
                #st.dataframe(df)

        # Editar/Eliminar dueño
        if not df.empty:
            selected = st.selectbox("Selecciona dueño por ID", df["DUENO_ID"].tolist(), key="sel_dueno")
            if selected:
                row = df[df["DUENO_ID"] == selected].iloc[0]
                col1, col2 = st.columns(2)
                # Edición
                with col1:
                    upd_nombre    = st.text_input("Nombre", row["NOMBRE"], key="upd_nombre")
                    upd_tel       = st.text_input("Teléfono", row["TELEFONO"], key="upd_tel")
                    upd_correo    = st.text_input("Correo", row["CORREO"], key="upd_correo")
                    upd_dir       = st.text_input("Dirección", row["DIRECCION"], key="upd_dir")
                    upd_doc       = st.text_input("Documento ID", row["DOCUMENTO_ID"], key="upd_doc")
                    if st.button("Actualizar", key="btn_update_dueno"):
                        try:
                            affected = update_dueno(selected, upd_nombre, upd_tel, upd_correo, upd_dir, upd_doc)
                            st.success(f"Dueño actualiza­do")
                        except ValueError as ve:
                            st.error(f"Error de validación: {ve}")
                        except Exception as e:
                            st.error("Error inesperado al actualizar dueño. Revisa los logs.")
                            st.write(e)
                        #df = list_duenos(limit=int(limit), offset=int(offset), filtro=filtro)
                        #st.dataframe(df)
                # Eliminación lógica
                with col2:
                    if st.button("Eliminar", key="btn_delete_dueno"):
                        try:
                            _ = delete_dueno(selected)
                            st.success("Dueño eliminado (soft-delete)")
                        except Exception as e:
                            st.error("Error al eliminar dueño. Revisa los logs.")
                            st.write(e)
                        #df = list_duenos(limit=int(limit), offset=int(offset), filtro=filtro)
                        #st.dataframe(df)

if __name__ == '__main__':
    app()
