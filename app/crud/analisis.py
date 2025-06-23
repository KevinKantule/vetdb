# app/crud/analisis.py
import pandas as pd
from common import run_query
from datetime import date

def reporte_mascotas_hoy() -> tuple[str, pd.DataFrame]:
    """
    Cuenta cuántas mascotas fueron atendidas en la fecha de hoy.
    Devuelve un párrafo y el DataFrame con el resultado (para gráficas o Excel).
    """
    hoy = date.today().strftime("%Y-%m-%d")
    sql = """
      SELECT COUNT(*) AS atendidas
      FROM vet_cita
     WHERE TO_DATE(fecha_hora) = %s
    """
    df = run_query(sql, (hoy,))
    total = int(df.at[0, 'ATENDIDAS'])
    texto = f"Hoy, {hoy}, se atendieron {total} mascota{'s' if total != 1 else ''}."
    return texto, df

def reporte_ingresos_mes(ano: int, mes: int) -> tuple[str, pd.DataFrame]:
    """
    Suma los montos facturados en un mes específico.
    """
    sql = """
      SELECT SUM(monto) AS ingresos
      FROM vet_factura
     WHERE YEAR(fecha_pago)=%s AND MONTH(fecha_pago)=%s
    """
    df = run_query(sql, (ano, mes))
    ingresos = float(df.at[0, 'INGRESOS'] or 0)
    texto = f"En {mes:02d}/{ano}, los ingresos totales fueron de ${ingresos:,.2f}."
    return texto, df
