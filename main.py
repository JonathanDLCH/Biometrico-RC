#!/usr/bin/env python3
"""Servicio diario para sincronizar un biometrico con la base de datos."""

import logging
from datetime import datetime, timedelta

from config.settings import API_HEADERS, INITIAL_SYNC_DAYS, LOG_FILE, SUPPORT_EMAILS
from src.api_client import build_api_url, get_attendance_logs, get_device_info, sync_employees_from_api
from src.db import SessionLocal, init_db
from src.email_sender import send_support_error
from src.repository import (
    bulk_insert_attendance_logs,
    create_or_update_employee,
    get_last_sync,
    mark_biometric_synced,
    get_all_biometric_devices,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def _date_string(value):
    return value.strftime("%Y-%m-%d")


def _sync_start(last_sync, now):
    if last_sync is None:
        return now - timedelta(days=INITIAL_SYNC_DAYS)
    return last_sync


def identify_biometric(device, device_info):
    """Valida que la respuesta corresponda a un biométrico ya registrado."""
    if not device_info:
        return False
    remote_sn = device_info.get("sn") or device_info.get("serial") or device_info.get("Serial")
    if remote_sn and device.sn and remote_sn != device.sn:
        logger.warning("La IP %s respondió con otro número de serie: %s", device.ip, remote_sn)
        return False
    logger.info("Biométrico identificado: id=%s, sn=%s, ip=%s", device.id_biometrico, device.sn, device.ip)
    return True


def sync_employees(session, employees):
    """Inserta o actualiza empleados usando su ID como clave unica."""
    valid_employees = []
    for employee in employees or []:
        saved = create_or_update_employee(session, employee)
        if saved is None:
            logger.warning("Empleado ignorado por no tener un ID valido: %s", employee)
            continue
        valid_employees.append(employee)
    session.flush()
    return valid_employees


def fetch_and_store_attendance(session, employees, biometric_id, api_url, password, headers, start, end):
    """Obtiene e inserta registros; None de la API se considera un error recuperable."""
    inserted = 0
    for employee in employees:
        employee_id = employee["id"]
        records = get_attendance_logs(
            employee_id,
            _date_string(start),
            _date_string(end),
            api_url,
            password,
            headers,
        )
        if records is None:
            raise RuntimeError(f"No se pudieron obtener registros del empleado {employee_id}")
        inserted += bulk_insert_attendance_logs(
            session,
            employee_id,
            records,
            biometric_id=biometric_id,
        )
    return inserted


def run_sync(now=None, session_factory=SessionLocal):
    """Ejecuta una sincronizacion completa y atomica."""
    now = now or datetime.now()

    with session_factory() as session:
        try:
            biometric_devices = get_all_biometric_devices(session)
            if not biometric_devices:
                raise RuntimeError("No hay biométricos configurados en la base de datos")

            total_employees = 0
            total_inserted = 0
            identified = 0
            for device in biometric_devices:
                api_url = build_api_url(device.ip)
                device_info = get_device_info(device.ip, device.contrasena, API_HEADERS)
                if not identify_biometric(device, device_info):
                    continue
                identified += 1
                employees = sync_employees_from_api(api_url, device.contrasena, API_HEADERS)
                last_sync = get_last_sync(session, device.id_biometrico)
                start = _sync_start(last_sync, now)
                valid_employees = sync_employees(session, employees)
                total_employees += len(valid_employees)
                total_inserted += fetch_and_store_attendance(
                    session, valid_employees, device.id_biometrico,
                    api_url, device.contrasena, API_HEADERS, start, now,
                )
                mark_biometric_synced(session, device.id_biometrico, now)
            if not identified:
                raise RuntimeError("No se pudo identificar ningún biométrico registrado")
            session.commit()
        except Exception:
            session.rollback()
            raise

    logger.info(
        "Sincronizacion completada: empleados=%s, registros_nuevos=%s, desde=%s, hasta=%s",
        total_employees,
        total_inserted,
        now,
        now,
    )
    return {"employees": total_employees, "attendance": total_inserted}


def main():
    """Punto de entrada diario; los fallos se notifican y quedan listos para reintento."""
    try:
        init_db()
        run_sync()
    except Exception as error:
        logger.exception("Fallo en la sincronizacion diaria")
        send_support_error(SUPPORT_EMAILS, error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
