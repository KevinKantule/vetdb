# app/crud/mascotas.py
"""
CRUD de Mascotas: funciones para listar, crear, actualizar y borrar lógicamente.
Implementa validación centralizada, captura de duplicados, logging, transacciones y docstrings.
"""
import re
import pandas as pd
from common import run_query, get_connection
from logging_config import logging
from snowflake.connector.errors import ProgrammingError

logger = logging.getLogger(__name__)


def _validate_mascota_data(nombre: str,
                           especie: str,
                           raza: str,
                           peso_kg: float,
                           color: str,
                           microchip: str,
                           sexo_id: int,
                           dueno_id: int) -> None:
    """
    Valida campos obligatorios y formatos para mascota:
      - nombre y especie no pueden estar vacíos
      - peso_kg debe ser número >= 0
      - microchip (si existe) solo alfanuméricos o guiones
      - sexo_id y dueno_id deben existir en sus tablas de dominio
    Lanza ValueError con mensaje descriptivo.
    """
    if not nombre.strip():
        raise ValueError("El nombre de la mascota no puede estar vacío")
    if not especie.strip():
        raise ValueError("La especie no puede estar vacía")
    if peso_kg is None:
        raise ValueError("El peso es obligatorio")
    try:
        p = float(peso_kg)
        if p < 0:
            raise ValueError("El peso debe ser un número positivo")
    except (TypeError, ValueError):
        raise ValueError("El peso debe ser un número válido")
    if microchip:
        if not re.fullmatch(r"[A-Za-z0-9\-]+", microchip):
            raise ValueError("El microchip tiene caracteres inválidos")
    # validar sexo_id existe en dominio
    exists = run_query("SELECT 1 FROM vet_sexo WHERE sexo_id = %s", (sexo_id,))
    if exists.empty:
        raise ValueError(f"sexo_id inválido: {sexo_id}")
    # validar dueño existe y activo
    exists = run_query(
        "SELECT 1 FROM vw_dueno_activo WHERE dueno_id = %s", (dueno_id,))
    if exists.empty:
        raise ValueError(f"dueno_id inválido o inactivo: {dueno_id}")


def list_mascotas(limit: int = 5,
                  offset: int = 0,
                  filtro: str = None) -> pd.DataFrame:
    """
    Devuelve mascotas activas, con dueno_id, dueno_nombre, sexo_id, y demás campos.
    """
    sql_parts = [
        "SELECT",
        "  m.mascota_id,",
        "  m.dueno_id,",
        "  d.nombre AS dueno_nombre,",
        "  m.sexo_id,",
        "  m.nombre,",
        "  m.especie,",
        "  m.raza,",
        "  m.fecha_nac,",
        "  m.peso_kg,",
        "  m.color,",
        "  m.microchip",
        "FROM vet_mascota m",
        "JOIN vet_dueno   d ON m.dueno_id = d.dueno_id",
        "WHERE m.is_active = TRUE"
    ]
    params = []
    if filtro:
        sql_parts.append(
            "  AND (LOWER(m.nombre)   LIKE %s OR LOWER(m.especie) LIKE %s)"
        )
        term = f"%{filtro.lower()}%"
        params.extend([term, term])

    sql_parts.append("ORDER BY m.mascota_id")
    sql_parts.append("LIMIT %s OFFSET %s")
    params.extend([limit, offset])

    query = "\n".join(sql_parts)
    return run_query(query, tuple(params))


def create_mascota(dueno_id: int,
                   nombre: str,
                   especie: str,
                   raza: str,
                   sexo_id: int,
                   fecha_nac: str,
                   peso_kg: float,
                   color: str,
                   microchip: str) -> None:
    """
    Inserta una nueva mascota.
    Captura duplicados de microchip y errores de validación.

    :raises ValueError: si falla validación o microchip duplicado
    :raises Exception: otros errores de base de datos
    """
    _validate_mascota_data(nombre, especie, raza, peso_kg,
                           color, microchip, sexo_id, dueno_id)
    if microchip:
        dup = run_query(
            "SELECT 1 FROM vet_mascota WHERE microchip = %s", (microchip,))
        if not dup.empty:
            raise ValueError(
                "Ya existe otra mascota con ese número de microchip")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO vet_mascota(dueno_id, nombre, especie, raza, sexo_id, fecha_nac, peso_kg, color, microchip)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (dueno_id, nombre, especie, raza, sexo_id,
             fecha_nac, peso_kg, color, microchip)
        )
        conn.commit()
        logger.info(f"Mascota creada: {nombre} (microchip={microchip})")
    except ProgrammingError as pe:
        if 'uq_microchip' in str(pe).lower():
            conn.rollback()
            raise ValueError(
                "Ya existe otra mascota con ese número de microchip")
        conn.rollback()
        logger.error(f"Error de BD al crear mascota: {pe}")
        raise
    finally:
        cur.close()


def update_mascota(mascota_id: int,
                   dueno_id: int,
                   nombre: str,
                   especie: str,
                   raza: str,
                   sexo_id: int,
                   fecha_nac: str,
                   peso_kg: float,
                   color: str,
                   microchip: str) -> int:
    """
    Actualiza datos de una mascota existente.

    :param mascota_id: ID de la mascota a modificar
    :return: filas afectadas
    :raises ValueError: si validación o duplicado falla
    :raises Exception: otros errores de BD
    """
    _validate_mascota_data(nombre, especie, raza, peso_kg,
                           color, microchip, sexo_id, dueno_id)
    if microchip:
        dup = run_query(
            "SELECT 1 FROM vet_mascota WHERE microchip = %s AND mascota_id != %s",
            (microchip, mascota_id)
        )
        if not dup.empty:
            raise ValueError("Otra mascota ya usa ese número de microchip")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE vet_mascota
               SET dueno_id = %s,
                   nombre    = %s,
                   especie   = %s,
                   raza      = %s,
                   sexo_id   = %s,
                   fecha_nac = %s,
                   peso_kg   = %s,
                   color     = %s,
                   microchip = %s
             WHERE mascota_id = %s
            """,
            (dueno_id, nombre, especie, raza, sexo_id,
             fecha_nac, peso_kg, color, microchip, mascota_id)
        )
        affected = cur.rowcount
        conn.commit()
        logger.info(f"Mascota actualizada: id={mascota_id}, filas={affected}")
        return affected
    except ProgrammingError as pe:
        if 'uq_microchip' in str(pe).lower():
            conn.rollback()
            raise ValueError("Otra mascota ya usa ese número de microchip")
        conn.rollback()
        logger.error(f"Error de BD al actualizar mascota {mascota_id}: {pe}")
        raise
    finally:
        cur.close()


def delete_mascota(mascota_id: int) -> str:
    """
    Elimina lógicamente una mascota llamando al SP sp_soft_delete.

    :param mascota_id: ID de la mascota a eliminar
    :return: mensaje de confirmación del SP
    :raises Exception: errores de BD
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "CALL sp_soft_delete('vet_mascota', 'mascota_id', %s)", (str(mascota_id),))
        result = cur.fetchone()[0] if cur.description else ''
        conn.commit()
        logger.info(f"Soft-delete mascota id={mascota_id}: {result}")
        return result
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al eliminar mascota {mascota_id}: {e}")
        raise
    finally:
        cur.close()
