import json
import logging
from pathlib import Path

import requests

from config.settings import API_URL, API_PASSWORD, API_HEADERS

logging.basicConfig(level=logging.INFO)


def get_user_list():
    """
    Obtiene la lista de usuarios/empleados desde la API biométrica.

    :return: Lista de usuarios o None si hay error
    """
    payload = {
        "password": API_PASSWORD,
        "cmd": "getuserlist",
        "stn": 1
    }

    try:
        response = requests.post(API_URL, json=payload, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("result"):
            logging.info(f"Obtenidos {data.get('count', 0)} usuarios desde la API")
            return data.get("record", [])
        logging.error(f"Error en respuesta API de usuarios: {data}")
        return None
    except requests.RequestException as e:
        logging.error(f"Error en petición API de usuarios: {e}")
        return None


def sync_employees_from_api(employees_file_path=None):
    """
    Sincroniza la lista de empleados con la API biométrica.

    Si el archivo no existe o está vacío, lo crea con la información recibida.
    Si existen empleados, se actualiza el registro cuando el id ya existe y se añade
    uno nuevo cuando aparece en la API.

    :param employees_file_path: Ruta del archivo JSON de empleados.
    :return: Lista de empleados sincronizada.
    """
    employees_file_path = Path(employees_file_path or "config/employees.json")
    employees_file_path.parent.mkdir(parents=True, exist_ok=True)

    existing_employees = []
    if employees_file_path.exists() and employees_file_path.stat().st_size > 0:
        try:
            existing_employees = json.loads(employees_file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logging.warning(f"El archivo {employees_file_path} tiene formato inválido; se recreará")
            existing_employees = []

    if not isinstance(existing_employees, list):
        existing_employees = []

    api_employees = get_user_list() or []
    if not api_employees:
        return existing_employees

    employee_by_id = {employee.get("id"): employee for employee in existing_employees if employee.get("id") is not None}

    for api_employee in api_employees:
        employee_id = api_employee.get("id")
        if employee_id is None:
            continue

        if employee_id in employee_by_id:
            existing_employee = employee_by_id[employee_id]
            merged_employee = dict(existing_employee)
            for key, value in api_employee.items():
                if value in [None, "", []]:
                    continue
                if key not in merged_employee or merged_employee.get(key) in [None, "", []]:
                    merged_employee[key] = value
                else:
                    merged_employee[key] = value
            employee_by_id[employee_id] = merged_employee
        else:
            employee_by_id[employee_id] = dict(api_employee)

    synchronized_employees = list(employee_by_id.values())
    synchronized_employees.sort(key=lambda employee: employee.get("id", 0))

    employees_file_path.write_text(json.dumps(synchronized_employees, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info(f"Empleados sincronizados y guardados en {employees_file_path}")
    return synchronized_employees


def get_attendance_logs(enrollid, from_date, to_date, index=0):
    """
    Obtiene los registros de asistencia para un empleado específico en un rango de fechas.

    :param enrollid: ID del empleado
    :param from_date: Fecha de inicio (YYYY-MM-DD)
    :param to_date: Fecha de fin (YYYY-MM-DD)
    :param index: Índice de paginación (por defecto 0)
    :return: Lista de registros o None si hay error
    """
    payload = {
        "password": API_PASSWORD,
        "cmd": "getlog",
        "index": index,
        "enrollid": enrollid,
        "from": from_date,
        "to": to_date
    }

    try:
        response = requests.post(API_URL, json=payload, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("result"):
            logging.info(f"Obtenidos {data.get('count', 0)} registros para empleado {enrollid}")
            return data.get("record", [])
        else:
            logging.error(f"Error en respuesta API: {data}")
            return None
    except Exception as e:
        logging.error(f"Error en petición API: {e}")
        return None