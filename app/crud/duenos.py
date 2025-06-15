# app/crud/duenos.py
"""
CRUD de Dueños: funciones para listar, crear, actualizar y borrar lógicamente.
Se implementa validación centralizada, captura de errores de unicidad y docstrings detallados.
"""
import re
import pandas as pd
from common import run_query, get_connection
from logging_config import logging
from snowflake.connector.errors import ProgrammingError

logger = logging.getLogger(__name__)


def _validate_dueno_data(nombre: str, telefono: str, correo: str, direccion: str, documento_id: str) -> None:
    """
    Valida campos obligatorios y formatos:
      - nombre, telefono, direccion, documento_id no pueden estar vacíos
      - telefono solo dígitos
      - correo con formato usuario@dominio.ext
    Lanza ValueError con mensaje descriptivo.
    """
    if not nombre.strip():
        raise ValueError("El nombre no puede estar vacío")
    if not telefono.strip():
        raise ValueError("El teléfono no puede estar vacío")
    if not telefono.isdigit():
        raise ValueError("El teléfono no es válido; debe contener solo dígitos")
    if not direccion.strip():
        raise ValueError("La dirección no puede estar vacía")
    if not documento_id.strip():
        raise ValueError("El documento ID no puede estar vacío")
    if not correo or not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", correo):
        raise ValueError("El correo no es válido; formato esperado usuario@dominio.ext")


def list_duenos(limit: int = 5, offset: int = 0, filtro: str = None) -> pd.DataFrame:
    """
    Devuelve dueños activos con paginación y filtro opcional por nombre.

    :param limit: número máximo de registros a devolver
    :param offset: posición inicial (para paginación)
    :param filtro: cadena para búsqueda en nombre (case-insensitive)
    :return: DataFrame con columnas dueno_id, nombre, telefono, correo, direccion, documento_id
    """
    sql_parts = [
        "SELECT dueno_id, nombre, telefono, correo, direccion, documento_id",
        "FROM vw_dueno_activo"
    ]
    params = []
    if filtro:
        sql_parts.append("WHERE LOWER(nombre) LIKE %s")
        params.append(f"%{filtro.lower()}%")
    sql_parts.append("ORDER BY dueno_id")
    sql_parts.append("LIMIT %s OFFSET %s")
    params.extend([limit, offset])
    query = " ".join(sql_parts)
    return run_query(query, tuple(params))


def create_dueno(nombre: str, telefono: str, correo: str, direccion: str, documento_id: str) -> None:
    """
    Inserta un nuevo dueño en la base de datos.
    Captura duplicados y errores de validación.

    :raises ValueError: si la validación de datos falla o documento duplicado
    :raises Exception: otros errores de base de datos
    """
    # Validación centralizada
    _validate_dueno_data(nombre, telefono, correo, direccion, documento_id)

    # Pre-chequeo de duplicados
    exists = run_query(
        "SELECT 1 FROM vet_dueno WHERE documento_id = %s",
        (documento_id,)
    )
    if not exists.empty:
        raise ValueError("Ya existe un dueño con ese Documento ID")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO vet_dueno(nombre, telefono, correo, direccion, documento_id) VALUES (%s, %s, %s, %s, %s)",
            (nombre, telefono, correo, direccion, documento_id)
        )
        conn.commit()
        logger.info(f"Dueño creado con documento_id={documento_id}")
    except ProgrammingError as pe:
        # Captura duplicados por constraint de DB
        if 'uq_dueno_doc' in str(pe).lower():
            conn.rollback()
            raise ValueError("Ya existe un dueño con ese Documento ID")
        conn.rollback()
        logger.error(f"Error de BD al crear dueño: {pe}")
        raise
    finally:
        cur.close()


def update_dueno(dueno_id: int, nombre: str, telefono: str, correo: str, direccion: str, documento_id: str) -> int:
    """
    Actualiza un dueño existente.

    :param dueno_id: ID del dueño a actualizar
    :raises ValueError: si la validación de datos falla o documento duplicado
    :raises Exception: otros errores de base de datos
    :return: número de filas afectadas
    """
    _validate_dueno_data(nombre, telefono, correo, direccion, documento_id)

    # Pre-chequeo de duplicados (excluyendo el mismo registro)
    exists = run_query(
        "SELECT 1 FROM vet_dueno WHERE documento_id = %s AND dueno_id != %s",
        (documento_id, dueno_id)
    )
    if not exists.empty:
        raise ValueError("Ya existe otro dueño con ese Documento ID")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE vet_dueno
               SET nombre = %s,
                   telefono = %s,
                   correo = %s,
                   direccion = %s,
                   documento_id = %s
             WHERE dueno_id = %s
            """,
            (nombre, telefono, correo, direccion, documento_id, dueno_id)
        )
        affected = cur.rowcount
        conn.commit()
        logger.info(f"Dueño actualizado: dueno_id={dueno_id}, filas={affected}")
        return affected
    except ProgrammingError as pe:
        if 'uq_dueno_doc' in str(pe).lower():
            conn.rollback()
            raise ValueError("Ya existe otro dueño con ese Documento ID")
        conn.rollback()
        logger.error(f"Error de BD al actualizar dueño {dueno_id}: {pe}")
        raise
    finally:
        cur.close()


def delete_dueno(dueno_id: int) -> str:
    """
    Elimina lógicamente un dueño llamando al procedimiento sp_soft_delete.

    :param dueno_id: ID del dueño a eliminar
    :return: mensaje de confirmación del SP
    :raises Exception: errores de base de datos
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL sp_soft_delete('vet_dueno', 'dueno_id', %s)", (str(dueno_id),))
        result = cur.fetchone()[0] if cur.description else ''
        conn.commit()
        logger.info(f"Soft-delete dueño dueno_id={dueno_id}: {result}")
        return result
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al eliminar dueño {dueno_id}: {e}")
        raise
    finally:
        cur.close()
