import requests
import json
import logging
from config.settings import API_URL, API_PASSWORD, API_HEADERS

logging.basicConfig(level=logging.INFO)

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
    except requests.RequestException as e:
        logging.error(f"Error en petición API: {e}")
        return None