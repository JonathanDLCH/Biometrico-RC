#!/usr/bin/env python3
"""
Programa principal para gestión de asistencias biométricas.
Previos: Obtener usuarios registrados en el dispositivo
Flujo: Obtener registros → Procesar → Generar reportes → Enviar emails
"""

import json
import logging
import pandas as pd
from datetime import datetime, date
from calendar import monthrange
from src.api_client import get_attendance_logs, sync_employees_from_api
from src.data_processor import AttendanceProcessor
from src.email_sender import send_attendance_reports, send_general_report_to_rh
from src.db import SessionLocal, init_db
from src.repository import (
    bulk_insert_attendance_logs,
    create_or_update_employee,
    get_attendance_records_for_employee,
)
from config.settings import LOG_FILE, HORA_ENTRADA, HORA_SALIDA, HORA_SALIDA_SABADO, LIMITE_RETARDO_MINUTOS, EMAIL_RH

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_biweekly_period():
    """
    Calcula el período quincenal (1-15 o 16-último día del mes).
    
    :return: Tupla (from_date, to_date) en formato YYYY-MM-DD
    """
    today = date.today()
    year = today.year
    month = today.month
    day = today.day
    
    # Determinar si estamos en primer o segundo quincena
    if day <= 15:
        # Primera quincena: del 1 al 15
        from_date = date(year, month, 1)
        to_date = date(year, month, 15)
    else:
        # Segunda quincena: del 16 al último día del mes
        from_date = date(year, month, 16)
        last_day = monthrange(year, month)[1]
        to_date = date(year, month, last_day)
    
    return from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")

def load_employees():
    """Carga la lista de empleados sincronizando primero con la API biométrica."""
    employees = sync_employees_from_api("config/employees.json")
    if not employees:
        return []
    return employees

def send_emails_to_employees_and_rh(df_all, from_date, to_date, resumen_global):
    """
    Envía reportes por email a empleados y RH.
    
    :param df_all: DataFrame con todos los análisis
    :param from_date: Fecha inicio
    :param to_date: Fecha fin
    :param resumen_global: Estadísticas globales
    """
    employees = load_employees()
    periodo = f"{from_date} al {to_date}"
    
    # Archivos de reporte general para RH
    general_reports = [
        "data/processed/reporte_general_asistencias.csv",
        "data/processed/reporte_horas_trabajadas.csv",
        "data/processed/resumen_global.json"
    ]
    
    # Enviar reporte general a RH
    send_general_report_to_rh(EMAIL_RH, general_reports, periodo, resumen_global)
    
    # Enviar reportes individuales a empleados (si tienen email)
    for employee in employees:
        enrollid = employee["id"]
        name = employee["name"]
        email = employee.get("userprofile", "").strip()
        
        if not email:
            logging.info(f"No hay email para {name}, omitiendo envío individual")
            continue
        
        # Filtrar datos del empleado
        df_employee = df_all[df_all["enrollid"] == enrollid]
        if df_employee.empty:
            logging.info(f"No hay datos para {name}, omitiendo envío")
            continue
        
        # Crear reporte individual (CSV con datos del empleado)
        individual_report = f"data/processed/reporte_{enrollid}_{name.replace(' ', '_')}.csv"
        df_employee.to_csv(individual_report, index=False)
        
        # Enviar email al empleado
        send_attendance_reports(
            employee_email=email,
            rh_emails=None,  # No enviar a RH en individuales
            report_files=[individual_report],
            periodo=periodo
        )

def process_all_employees(from_date, to_date):
    """
    Procesa asistencias para todos los empleados activos.
    
    :param from_date: Fecha de inicio (YYYY-MM-DD)
    :param to_date: Fecha de fin (YYYY-MM-DD)
    :return: DataFrame con análisis de todos los empleados
    """
    employees = load_employees()
    processor = AttendanceProcessor(
        hora_entrada=HORA_ENTRADA,
        hora_salida=HORA_SALIDA,
        hora_salida_sabado=HORA_SALIDA_SABADO,
        limite_retardo_min=LIMITE_RETARDO_MINUTOS
    )
    
    with SessionLocal() as session:
        for employee in employees:
            created = create_or_update_employee(session, employee)
            if not created:
                logging.warning(f"Empleado inválido o sin ID: {employee}")
                continue
        session.commit()

    all_results = []
    with SessionLocal() as session:
        for employee in employees:
            enrollid = employee["id"]
            name = employee["name"]
            logging.info(f"Procesando empleado: {name} (ID: {enrollid})")

            records = get_attendance_logs(enrollid, from_date, to_date)
            if not records:
                logging.warning(f"No hay registros para {name}")
                continue

            inserted = bulk_insert_attendance_logs(session, enrollid, records)
            if inserted:
                session.commit()
                logging.info(f"Insertados {inserted} registros nuevos para empleado {enrollid}")

            db_records = get_attendance_records_for_employee(session, enrollid, from_date, to_date)
            if not db_records:
                logging.warning(f"No se encontraron registros en DB para {name}")
                continue

            records_to_process = [
                {
                    "enrollid": rec.id_empleado,
                    "name": name,
                    "time": rec.register_time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for rec in db_records
            ]

            df_employee = processor.procesar_registros(records_to_process)

            if df_employee.empty:
                logging.warning(f"No se pudieron procesar registros para {name}")
                continue

            df_employee["employee_name"] = name
            all_results.append(df_employee)
    
    if not all_results:
        return pd.DataFrame()
    
    # Combinar todos los resultados
    df_all = pd.concat(all_results, ignore_index=True)
    return df_all

def generate_general_report(df_all, from_date, to_date):
    """
    Genera reporte general con empleados en filas y fechas en columnas.
    
    :param df_all: DataFrame con todos los análisis
    :param from_date: Fecha inicio
    :param to_date: Fecha fin
    """
    if df_all.empty:
        logging.warning("No hay datos para generar reporte general")
        return
    
    # Crear tabla pivote: filas = empleados, columnas = fechas, valores = estado
    pivot_table = df_all.pivot_table(
        index="employee_name",
        columns="date",
        values="estado",
        aggfunc="first"  # Si hay múltiples, toma el primero
    ).fillna("Sin registro")
    
    # Guardar como CSV
    pivot_table.to_csv("data/processed/reporte_general_asistencias.csv")
    
    # También guardar versión con más detalles (horas trabajadas)
    pivot_horas = df_all.pivot_table(
        index="employee_name",
        columns="date",
        values="horas_trabajadas",
        aggfunc="sum"
    ).fillna(0)
    
    pivot_horas.to_csv("data/processed/reporte_horas_trabajadas.csv")
    
    logging.info("Reportes generales generados exitosamente")
    
    # Mostrar resumen
    print("\n" + "="*80)
    print("REPORTE GENERAL DE ASISTENCIAS")
    print("="*80)
    print(f"Período: {from_date} al {to_date}")
    print(f"Empleados procesados: {len(pivot_table)}")
    print("-"*80)
    print("Vista previa del reporte de estados:")
    print(pivot_table.head(10).to_string())
    print("-"*80)
    print("Vista previa del reporte de horas:")
    print(pivot_horas.head(10).to_string())
    print("="*80 + "\n")


def generate_first_last_report(df_all):
    """Genera un reporte con la hora del primer y último registro de cada empleado."""
    if df_all.empty:
        logging.warning("No hay datos para generar el reporte de entradas y salidas")
        return

    reporte_entradas_salidas = df_all[["employee_name", "date", "hora_entrada", "hora_salida"]].copy()
    reporte_entradas_salidas = reporte_entradas_salidas.sort_values(["employee_name", "date"])
    reporte_entradas_salidas.to_csv("data/processed/reporte_entradas_salidas.csv", index=False)

    logging.info("Reporte de primer y último registro generado exitosamente")


def main():
    """
    Ejecuta el pipeline completo para todos los empleados.
    """
    # Calcular período quincenal automáticamente
    #from_date, to_date = "2024-06-01", "2024-06-15"  # Para pruebas manuales   
    from_date, to_date = get_biweekly_period()
    
    logging.info(f"Iniciando procesamiento general del {from_date} al {to_date}")
    
    # Paso 1: Procesar todos los empleados
    logging.info("Paso 1: Procesando todos los empleados...")
    df_all = process_all_employees(from_date, to_date)
    
    if df_all.empty:
        logging.error("No se obtuvieron datos de ningún empleado")
        return
    
    # Paso 2: Generar reportes generales
    logging.info("Paso 2: Generando reportes generales...")
    generate_general_report(df_all, from_date, to_date)
    
    # Paso 3: Generar resumen global
    logging.info("Paso 3: Generando resumen global...")
    processor = AttendanceProcessor(
        hora_entrada=HORA_ENTRADA,
        hora_salida=HORA_SALIDA,
        hora_salida_sabado=HORA_SALIDA_SABADO,
        limite_retardo_min=LIMITE_RETARDO_MINUTOS
    )
    
    resumen_global = {
        "total_empleados": len(df_all["enrollid"].unique()),
        "total_dias_analizados": len(df_all),
        "dias_normales": len(df_all[df_all["estado"] == "Normal"]),
        "dias_retardo": len(df_all[df_all["tiene_retardo"]]),
        "dias_sin_entrada": len(df_all[df_all["falta_entrada"]]),
        "dias_sin_salida": len(df_all[df_all["falta_salida"]]),
        "dias_horas_extra": len(df_all[df_all["tiene_horas_extra"]]),
        "total_retardo_minutos": df_all["retardo_minutos"].sum(),
        "total_horas_extra_minutos": df_all["horas_extra_minutos"].sum(),
        "promedio_horas_diarias": df_all["horas_trabajadas"].mean(),
    }
    
    with open("data/processed/resumen_global.json", "w") as f:
        json.dump(resumen_global, f, indent=4, default=str)
    
    # Mostrar resumen global
    print("\n" + "="*60)
    print("RESUMEN GLOBAL")
    print("="*60)
    for key, value in resumen_global.items():
        print(f"{key}: {value}")
    print("="*60 + "\n")

    # Generar reporte de primer y último registro por empleado
    logging.info("Paso 4: Generando reporte de primer y último registro...")
    generate_first_last_report(df_all)
    
    # Paso 5: Enviar emails
    logging.info("Paso 5: Enviando reportes por email...")
    #send_emails_to_employees_and_rh(df_all, from_date, to_date, resumen_global)
    
    logging.info("Procesamiento general completado exitosamente.")

if __name__ == "__main__":
    main()