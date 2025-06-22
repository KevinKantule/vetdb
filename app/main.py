# app/main.py
import streamlit as st
import pandas as pd
from auth import login_page
from crud.duenos import list_duenos, create_dueno, update_dueno, delete_dueno
from common import run_query
from crud.mascotas import (
    list_mascotas,
    create_mascota,
    update_mascota,
    delete_mascota
)
from crud.citas import list_citas, create_cita, update_cita, delete_cita


# Intentamos el login; detiene la app si no autenticado
login_page()

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
        st.header("🔎 Gestión de Dueños")

        # 1) Filtros + paginación en el body
        filtro = st.text_input("🔎 Buscar por nombre", key="filter_duenos")
        limit = st.number_input("Filas a mostrar", min_value=1,
                            max_value=100, value=5, step=1, key="limit_duenos")
        offset = st.number_input("Offset", min_value=0,
                             step=1, value=0, key="offset_duenos")

        # 2) Listado
        try:
            df = list_duenos(limit=int(limit), offset=int(offset), filtro=filtro)
            st.dataframe(df)
        except Exception as e:
            st.error("Error al cargar la lista de dueños. Revisa los logs.")
            st.write(e)
            return

        # 3) Crear nuevo dueño
        with st.expander("➕ Agregar nuevo dueño"):
            nombre = st.text_input("Nombre", key="new_nombre")
            telefono = st.text_input("Teléfono", key="new_telefono")
            correo = st.text_input("Correo", key="new_correo")
            direccion = st.text_input("Dirección", key="new_direccion")
            documento = st.text_input("Documento ID", key="new_documento")

            if st.button("Crear", key="btn_create_dueno"):
                dup = run_query(
                    "SELECT 1 FROM vet_dueno WHERE documento_id = %s", (documento,))
                if not dup.empty:
                    st.error("Ya existe un dueño con ese Documento ID")
                else:
                    try:
                        create_dueno(nombre, telefono, correo, direccion, documento)
                        st.success("Dueño creado exitosamente")
                    except ValueError as ve:
                        st.error(f"Error de validación: {ve}")
                    except Exception as e:
                        st.error("Error inesperado al crear dueño. Revisa los logs.")
                        st.write(e)
                # refresca la tabla
                #df = list_duenos(limit=int(limit), offset=int(offset), filtro=filtro)
                #st.dataframe(df)

        # 4) Editar / Eliminar
        if not df.empty:
            selected = st.selectbox("Selecciona dueño por ID", df["DUENO_ID"].tolist(), key="sel_dueno")
        if selected:
            row = df[df["DUENO_ID"] == selected].iloc[0]
            c1, c2 = st.columns(2)

            with c1:
                upd_nombre = st.text_input(
                    "Nombre", row["NOMBRE"], key="upd_nombre")
                upd_tel = st.text_input(
                    "Teléfono", row["TELEFONO"], key="upd_tel")
                upd_correo = st.text_input(
                    "Correo", row["CORREO"], key="upd_correo")
                upd_dir = st.text_input(
                    "Dirección", row["DIRECCION"], key="upd_dir")
                upd_doc = st.text_input(
                    "Documento ID", row["DOCUMENTO_ID"], key="upd_doc")
                if st.button("Actualizar", key="btn_update_dueno"):
                    try:
                        update_dueno(selected, upd_nombre, upd_tel,
                                     upd_correo, upd_dir, upd_doc)
                        st.success("Dueño actualizado")
                    except ValueError as ve:
                        st.error(f"Error de validación: {ve}")
                    except Exception as e:
                        st.error(
                            "Error inesperado al actualizar dueño. Revisa los logs.")
                        st.write(e)
                    #df = list_duenos(limit=int(limit), offset=int(offset), filtro=filtro)
                    #st.dataframe(df)

            with c2:
                if st.button("Eliminar", key="btn_delete_dueno"):
                    try:
                        delete_dueno(selected)
                        st.success("Dueño eliminado (soft-delete)")
                    except Exception as e:
                        st.error("Error al eliminar dueño. Revisa los logs.")
                        st.write(e)
                    #df = list_duenos(limit=int(limit), offset=int(offset), filtro=filtro)
                    #st.dataframe(df)

    elif opcion == 'Mascotas':
        st.header("Gestión de Mascotas")

        # 👉 Filtros y paginación específicos de Mascotas
        filtro_m = st.text_input(
            "🔎 Buscar nombre o especie", key="filter_mascotas")
        limit_m = st.number_input(
            "Filas a mostrar", min_value=1, max_value=100, value=5, key="limit_mascotas")
        offset_m = st.number_input(
            "Offset", min_value=0, step=1, value=0, key="offset_mascotas")

        # 1) Listado de mascotas
        try:
            dfm = list_mascotas(limit=int(limit_m), offset=int(offset_m), filtro=filtro_m)
            # muestra la columna dueno_nombre en lugar de DUENO_ID
            # tras obtener dfm de list_mascotas…
            # 1) renombra DUENO_NOMBRE → Dueño
            dfm_viz = dfm.rename(columns={"DUENO_NOMBRE": "Dueño"})
            
            # 2) elige el orden y las columnas que aparecen (omite DUENO_ID)
            cols = [
                "MASCOTA_ID",
                "Dueño",
                "NOMBRE",
                "ESPECIE",
                "RAZA",
                "FECHA_NAC",
                "PESO_KG",
                "COLOR",
                "MICROCHIP"
            ]
            dfm_viz = dfm_viz[cols]
            
            # 3) muéstralo
            st.dataframe(dfm_viz)

        except Exception as e:
            st.error("Error al cargar la lista de mascotas. Revisa los logs.")
            st.write(e)
            return

        # 2) Carga dominios: Dueños y Sexos
        duenos_df = list_duenos(limit=1000, offset=0, filtro=None)
        dueno_map = duenos_df.set_index("DUENO_ID")["NOMBRE"].to_dict()

        sexos_df = run_query(
            "SELECT sexo_id, descripcion FROM vet_sexo ORDER BY codigo", None)
        sexo_map = sexos_df.set_index("SEXO_ID")["DESCRIPCION"].to_dict()

        # 3) Formulario de creación
        with st.expander("➕ Agregar nueva mascota"):
            dueno_id = st.selectbox(
                "Dueño",
                options=list(dueno_map.keys()),
                format_func=lambda id: dueno_map[id],
                key="new_dueno"
            )
            nombre = st.text_input("Nombre", key="new_mnombre")
            especie = st.text_input("Especie", key="new_especie")
            raza = st.text_input("Raza", key="new_raza")
            sexo_id = st.selectbox(
                "Sexo",
                options=list(sexo_map.keys()),
                format_func=lambda id: sexo_map[id],
                key="new_sexo"
            )
            fecha_nac = st.date_input(
                "Fecha de nacimiento", key="new_fecha_nac")
            peso_kg = st.number_input(
                "Peso (kg)", min_value=0.0, format="%.2f", key="new_peso")
            color = st.text_input("Color", key="new_color")
            microchip = st.text_input("Microchip", key="new_microchip")

        if st.button("Crear", key="btn_create_mascota"):
            try:
                create_mascota(
                    dueno_id, nombre, especie, raza,
                    sexo_id, fecha_nac.strftime("%Y-%m-%d"),
                    peso_kg, color, microchip
                )
                st.success("Mascota creada exitosamente")
            except ValueError as ve:
                st.error(f"Error de validación: {ve}")
            except Exception as e:
                st.error(
                    "Error inesperado al crear mascota. Revisa los logs.")
                st.write(e)
            # refrescar
            # dfm = list_mascotas(limit=int(limit_m),
                # offset=int(offset_m), filtro=filtro_m)
            # st.dataframe(dfm)

        # 4) Edición y eliminación
        if not dfm.empty:
            selected_m = st.selectbox(
                "Selecciona mascota por ID",
                options=dfm["MASCOTA_ID"].tolist(),
                key="sel_mascota"
            )
            if selected_m:
                rowm = dfm[dfm["MASCOTA_ID"] == selected_m].iloc[0]
                # —> rowm["DUENO_ID"] ahora existe ✔
                current_dueno = int(rowm["DUENO_ID"])
                c1, c2 = st.columns(2)

                # — Edición —
                with c1:
                    # Nueva versión: casteo explicito a int y fallback a 0 si no lo encuentra
                    dueno_keys = list(dueno_map.keys())
                    current_dueno = int(rowm["DUENO_ID"])
                    try:
                        sel_idx = dueno_keys.index(current_dueno)
                    except ValueError:
                        sel_idx = 0

                    upd_dueno = st.selectbox(
                        "Dueño",
                        options=dueno_keys,
                        format_func=lambda id: dueno_map[id],
                        index=sel_idx,
                        key="upd_dueno"
                    )

                    upd_nombre = st.text_input(
                        "Nombre", rowm["NOMBRE"], key="upd_nombre_m")
                    upd_esp = st.text_input(
                        "Especie", rowm["ESPECIE"], key="upd_especie")
                    upd_raza = st.text_input(
                        "Raza", rowm["RAZA"], key="upd_raza")

                    sexo_keys = list(sexo_map.keys())
                    current_sexo = int(rowm["SEXO_ID"])
                    try:
                        sexo_idx = sexo_keys.index(current_sexo)
                    except ValueError:
                        sexo_idx = 0

                    upd_sexo = st.selectbox(
                        "Sexo",
                        options=sexo_keys,
                        format_func=lambda id: sexo_map[id],
                        index=sexo_idx,
                        key="upd_sexo"
                    )

                    upd_fecha = st.date_input(
                        "Fecha de nacimiento",
                        value=pd.to_datetime(rowm["FECHA_NAC"]),
                        key="upd_fecha"
                    )
                    upd_peso = st.number_input(
                        "Peso (kg)",
                        value=float(rowm["PESO_KG"]),
                        format="%.2f",
                        key="upd_peso"
                    )
                    upd_color = st.text_input(
                        "Color", rowm["COLOR"], key="upd_color")
                    upd_chip = st.text_input(
                        "Microchip", rowm["MICROCHIP"], key="upd_chip")

                    if st.button("Actualizar", key="btn_update_mascota"):
                        try:
                            affected = update_mascota(
                                selected_m, upd_dueno, upd_nombre, upd_esp, upd_raza,
                                upd_sexo, upd_fecha.strftime("%Y-%m-%d"),
                                upd_peso, upd_color, upd_chip
                            )
                            st.success(
                                f"Mascota actualizada ({affected} fila(s))")
                        except ValueError as ve:
                            st.error(f"Error de validación: {ve}")
                        except Exception as e:
                            st.error(
                                "Error inesperado al actualizar mascota. Revisa los logs.")
                            st.write(e)
                        # dfm = list_mascotas(limit=int(limit_m), offset=int(
                            # offset_m), filtro=filtro_m)
                        # st.dataframe(dfm)

                # — Eliminación lógica —
                with c2:
                    if st.button("Eliminar", key="btn_delete_mascota"):
                        try:
                            _ = delete_mascota(selected_m)
                            st.success("Mascota eliminada (soft-delete)")
                        except Exception as e:
                            st.error(
                                "Error al eliminar mascota. Revisa los logs.")
                            st.write(e)
                        # dfm = list_mascotas(limit=int(limit_m), offset=int(
                            # offset_m), filtro=filtro_m)
                        # st.dataframe(dfm)

    elif opcion == 'Citas':
        st.header("Gestión de Citas")

        # 🔎 Filtro y paginación en el cuerpo
        filtro_c = st.text_input(
            "🔎 Buscar servicio o motivo", key="filter_citas")
        limit_c = st.number_input(
            "Filas a mostrar", min_value=1, max_value=100, value=5, key="limit_citas")
        offset_c = st.number_input(
            "Offset", min_value=0, step=1, value=0, key="offset_citas")

        # 1) Listado de citas
        try:
            dfc = list_citas(limit=int(limit_c), offset=int(
                offset_c), filtro=filtro_c)
            st.dataframe(dfc)
        except Exception as e:
            st.error("Error al cargar la lista de citas. Revisa los logs.")
            st.write(e)
            return

        # 2) Carga dominios: Mascotas y Veterinarios
        masc_df = list_mascotas(limit=1000, offset=0, filtro=None)
        masc_map = masc_df.set_index("MASCOTA_ID")["NOMBRE"].to_dict()

        vets_df = run_query(
            "SELECT vet_id, nombre FROM vw_veterinario_activo ORDER BY nombre", None
        )
        vet_map = vets_df.set_index("VET_ID")["NOMBRE"].to_dict()

        # 3) Formulario de creación
        with st.expander("➕ Agregar nueva cita"):
            mascota_id = st.selectbox(
                "Mascota",
                options=list(masc_map.keys()),
                format_func=lambda i: f"{i} – {masc_map[i]}",
                key="new_mascota"
            )
            vet_id = st.selectbox(
                "Veterinario",
                options=list(vet_map.keys()),
                format_func=lambda i: f"{i} – {vet_map[i]}",
                key="new_vet"
            )
            fecha_hora = st.date_input("Fecha", key="new_fecha") \
                .strftime("%Y-%m-%d") + " " + \
                st.time_input("Hora", key="new_hora").strftime("%H:%M:%S")
            servicio = st.text_input("Servicio", key="new_servicio")
            motivo = st.text_input("Motivo",   key="new_motivo")

            if st.button("Crear", key="btn_create_cita"):
                try:
                    create_cita(mascota_id, vet_id,
                                fecha_hora, servicio, motivo)
                    st.success("Cita creada exitosamente")
                except ValueError as ve:
                    st.error(f"Error de validación: {ve}")
                except Exception as e:
                    st.error("Error inesperado al crear cita. Revisa los logs.")
                    st.write(e)
                dfc = list_citas(limit=int(limit_c), offset=int(
                    offset_c), filtro=filtro_c)
                st.dataframe(dfc)

        # 4) Edición y eliminación
        if not dfc.empty:
            selected_c = st.selectbox(
                "Selecciona cita por ID",
                options=dfc["CITA_ID"].tolist(),
                key="sel_cita"
            )
            if selected_c:
                rowc = dfc[dfc["CITA_ID"] == selected_c].iloc[0]
                c1, c2 = st.columns(2)

                # — Edición —
                with c1:
                    # Mascota
                    masc_keys = list(masc_map.keys())
                    cur_m = int(rowc["MASCOTA_ID"])
                    idx_m = masc_keys.index(cur_m) if cur_m in masc_keys else 0
                    upd_mascota = st.selectbox(
                        "Mascota",
                        options=masc_keys,
                        format_func=lambda i: f"{i} – {masc_map[i]}",
                        index=idx_m,
                        key="upd_mascota"
                    )
                    # Veterinario
                    vet_keys = list(vet_map.keys())
                    cur_v = int(rowc["VET_ID"])
                    idx_v = vet_keys.index(cur_v) if cur_v in vet_keys else 0
                    upd_vet = st.selectbox(
                        "Veterinario",
                        options=vet_keys,
                        format_func=lambda i: f"{i} – {vet_map[i]}",
                        index=idx_v,
                        key="upd_vet"
                    )
                    # Fecha y hora
                    fecha_val = pd.to_datetime(rowc["FECHA_HORA"])
                    upd_fecha = st.date_input(
                        "Fecha", value=fecha_val.date(), key="upd_fecha")
                    upd_hora = st.time_input(
                        "Hora",   value=fecha_val.time(),   key="upd_hora")
                    # Combina
                    upd_fh = upd_fecha.strftime(
                        "%Y-%m-%d") + " " + upd_hora.strftime("%H:%M:%S")

                    upd_servicio = st.text_input(
                        "Servicio", rowc["SERVICIO"], key="upd_servicio")
                    upd_motivo = st.text_input(
                        "Motivo",   rowc["MOTIVO"],   key="upd_motivo")

                    if st.button("Actualizar", key="btn_update_cita"):
                        try:
                            affected = update_cita(
                                selected_c,
                                upd_mascota,
                                upd_vet,
                                upd_fh,
                                upd_servicio,
                                upd_motivo
                            )
                            st.success(
                                f"Cita actualizada ({affected} fila(s))")
                        except ValueError as ve:
                            st.error(f"Error de validación: {ve}")
                        except Exception as e:
                            st.error(
                                "Error inesperado al actualizar cita. Revisa los logs.")
                            st.write(e)
                        dfc = list_citas(limit=int(limit_c), offset=int(
                            offset_c), filtro=filtro_c)
                        st.dataframe(dfc)

                # — Eliminación lógica —
                with c2:
                    if st.button("Eliminar", key="btn_delete_cita"):
                        try:
                            cnt = delete_cita(selected_c)
                            st.success(f"Cita eliminada ({cnt} fila(s))")
                        except Exception as e:
                            st.error(
                                "Error al eliminar cita. Revisa los logs.")
                            st.write(e)
                        dfc = list_citas(limit=int(limit_c), offset=int(
                            offset_c), filtro=filtro_c)
                        st.dataframe(dfc)


if __name__ == '__main__':
    app()
