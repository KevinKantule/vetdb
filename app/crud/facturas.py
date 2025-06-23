import pandas as pd
from common import run_query, get_connection
from logging_config import logging

logger = logging.getLogger(__name__)

def list_facturas(limit=5, offset=0, filtro=None) -> pd.DataFrame:
    sql = ["SELECT factura_id, cita_id, monto, metodo_pago, fecha_pago",
           "FROM vet_factura"]
    params=[]
    if filtro:
        sql.append("WHERE LOWER(metodo_pago) LIKE %s")
        params.append(f"%{filtro.lower()}%")
    sql.append("ORDER BY fecha_pago DESC LIMIT %s OFFSET %s")
    params.extend([limit, offset])
    return run_query(" ".join(sql), tuple(params))

def create_factura(cita_id:int, monto:float, metodo:str) -> None:
    # aquí podrías validar que la cita exista
    conn, cur = get_connection(), None
    try:
        cur = conn.cursor()
        cur.execute(
          "INSERT INTO vet_factura(cita_id, monto, metodo_pago) VALUES (%s,%s,%s)",
          (cita_id, monto, metodo)
        )
        conn.commit()
        logger.info(f"Factura creada para cita {cita_id}")
    except Exception:
        conn.rollback()
        raise
    finally:
        if cur: cur.close()

def delete_factura(factura_id:int) -> int:
    conn, cur = get_connection(), None
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM vet_factura WHERE factura_id = %s", (factura_id,))
        cnt = cur.rowcount
        conn.commit()
        return cnt
    finally:
        if cur: cur.close()
