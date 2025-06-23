from common import run_query
import pandas as pd

def reporte_atendidos_hoy() -> pd.DataFrame:
    """Cantidad de mascotas atendidas HOY por veterinario."""
    sql = """
    SELECT v.nombre    AS veterinario,
           COUNT(*)     AS atendidos
      FROM vet_cita c
      JOIN vet_veterinario v ON c.vet_id = v.vet_id
     WHERE DATE(c.fecha_hora) = CURRENT_DATE()
     GROUP BY v.nombre
     ORDER BY atendidos DESC
    """
    return run_query(sql)

def reporte_ingresos_servicio_mes(year: int, month: int) -> pd.DataFrame:
    """Ingresos totales por servicio en el mes y año indicados."""
    sql = """
    SELECT c.servicio,
           SUM(f.monto) AS total
      FROM vet_factura f
      JOIN vet_cita    c ON f.cita_id = c.cita_id
     WHERE YEAR(f.fecha_pago)  = %s
       AND MONTH(f.fecha_pago) = %s
     GROUP BY c.servicio
     ORDER BY total DESC
    """
    return run_query(sql, (year, month))

def reporte_vacunas_pendientes() -> pd.DataFrame:
    """Listado de mascotas con vacunas ya vencidas o por vencer en 7 días."""
    sql = """
    SELECT m.nombre       AS mascota,
           v.nombre AS vacuna,
           vm.prox_vence AS vence
      FROM vet_vacuna_mascota vm
      JOIN vet_mascota       m ON vm.mascota_id = m.mascota_id
      JOIN vet_vacuna        v ON vm.vacuna_id  = v.vacuna_id
     WHERE vm.prox_vence < DATEADD(day, 7, CURRENT_DATE())
    """
    return run_query(sql)
