# app/crud/citas.py
"""
CRUD de Citas: funciones para listar, crear, actualizar y eliminar citas.
Implementa validación centralizada, transacciones, logging y docstrings.
"""
import pandas as pd
from common import run_query, get_connection
from logging_config import logging
from snowflake.connector.errors import ProgrammingError

logger = logging.getLogger(__name__)


def _validate_cita_data(mascota_id: int,
                        vet_id: int,
                        fecha_hora: str,
                        servicio: str) -> None:
    """
    Valida los datos de una cita:
      - mascota_id debe existir y estar activo
      - vet_id debe existir y estar activo
      - fecha_hora no puede estar vacío
      - servicio no puede estar vacío
    Lanza ValueError si falla alguna validación.
    """
    # Validar mascota activa
    if run_query("SELECT 1 FROM vw_mascota_activa WHERE mascota_id = %s", (mascota_id,)).empty:
        raise ValueError(f"mascota_id inválido o inactiva: {mascota_id}")
    # Validar veterinario activo
    if run_query("SELECT 1 FROM vw_veterinario_activo WHERE vet_id = %s", (vet_id,)).empty:
        raise ValueError(f"vet_id inválido o inactivo: {vet_id}")
    # Fecha y hora obligatorias
    if not fecha_hora:
        raise ValueError("La fecha y hora de la cita son obligatorias")
    # Servicio obligatorio
    if not servicio.strip():
        raise ValueError("El servicio es obligatorio")


def list_citas(limit: int = 5,
               offset: int = 0,
               filtro: str = None) -> pd.DataFrame:
    """
    Devuelve las citas registradas, con paginación, filtro opcional
    y columnas mascota_id, mascota_nombre, vet_id, veterinario_nombre, fecha_hora, servicio, motivo.
    """
    sql_parts = [
        "SELECT",
        "  c.cita_id,",
        "  c.mascota_id,",
        "  m.nombre AS mascota_nombre,",
        "  c.vet_id,",
        "  v.nombre AS veterinario_nombre,",
        "  c.fecha_hora,",
        "  c.servicio,",
        "  c.motivo",
        "FROM vet_cita c",
        "JOIN vet_mascota      m ON c.mascota_id = m.mascota_id",
        "JOIN vet_veterinario  v ON c.vet_id     = v.vet_id",
        "WHERE 1 = 1"
    ]
    params = []
    if filtro:
        sql_parts.append("  AND (LOWER(c.servicio) LIKE %s OR LOWER(c.motivo) LIKE %s)")
        term = f"%{filtro.lower()}%"
        params.extend([term, term])

    sql_parts.append("ORDER BY c.fecha_hora DESC")
    sql_parts.append("LIMIT %s OFFSET %s")
    params.extend([limit, offset])

    query = "\n".join(sql_parts)
    return run_query(query, tuple(params))


def create_cita(mascota_id: int,
                vet_id: int,
                fecha_hora: str,
                servicio: str,
                motivo: str = None) -> None:
    """
    Inserta una nueva cita.

    :raises ValueError: si falla validación de datos
    :raises Exception: otros errores de BD
    """
    _validate_cita_data(mascota_id, vet_id, fecha_hora, servicio)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO vet_cita(mascota_id, vet_id, fecha_hora, servicio, motivo)"
            " VALUES (%s, %s, %s, %s, %s)",
            (mascota_id, vet_id, fecha_hora, servicio, motivo)
        )
        conn.commit()
        logger.info(f"Cita creada: mascota_id={mascota_id}, vet_id={vet_id}, fecha_hora={fecha_hora}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al crear cita: {e}")
        raise
    finally:
        cur.close()


def update_cita(cita_id: int,
                mascota_id: int,
                vet_id: int,
                fecha_hora: str,
                servicio: str,
                motivo: str = None) -> int:
    """
    Actualiza datos de una cita existente.

    :param cita_id: ID de la cita a actualizar
    :return: número de filas afectadas
    :raises ValueError: si falla validación
    :raises Exception: otros errores de BD
    """
    _validate_cita_data(mascota_id, vet_id, fecha_hora, servicio)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE vet_cita
               SET mascota_id = %s,
                   vet_id      = %s,
                   fecha_hora  = %s,
                   servicio    = %s,
                   motivo      = %s
             WHERE cita_id = %s
            """,
            (mascota_id, vet_id, fecha_hora, servicio, motivo, cita_id)
        )
        affected = cur.rowcount
        conn.commit()
        logger.info(f"Cita actualizada: cita_id={cita_id}, filas={affected}")
        return affected
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al actualizar cita {cita_id}: {e}")
        raise
    finally:
        cur.close()


def delete_cita(cita_id: int) -> int:
    """
    Elimina una cita de forma permanente.

    :param cita_id: ID de la cita a eliminar
    :return: número de filas afectadas
    :raises Exception: errores de BD
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM vet_cita WHERE cita_id = %s", (cita_id,))
        affected = cur.rowcount
        conn.commit()
        logger.info(f"Cita eliminada: cita_id={cita_id}, filas={affected}")
        return affected
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al eliminar cita {cita_id}: {e}")
        raise
    finally:
        cur.close()
