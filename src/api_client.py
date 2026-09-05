import logging

import requests

logging.basicConfig(level=logging.INFO)


def build_api_url(ip):
    return f"http://{ip}:80/api"


def _post(api_url, password, headers, payload):
    payload = {"password": password, **payload}
    response = requests.post(api_url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def get_user_list(api_url, password, headers=None):
    """
    Obtiene la lista de usuarios/empleados desde la API biométrica.

    :return: Lista de usuarios o None si hay error
    """
    try:
        data = _post(api_url, password, headers or {}, {"cmd": "getuserlist", "stn": 1})
        if data.get("result"):
            logging.info(f"Obtenidos {data.get('count', 0)} usuarios desde la API")
            return data.get("record", [])
        logging.error(f"Error en respuesta API de usuarios: {data}")
        return None
    except Exception as e:
        logging.error(f"Error en petición API de usuarios: {e}")
        return None


def get_device_info(ip, contrasena, headers=None):
    """
    Obtiene información del biométrico actual.

    :return: Dict con datos del dispositivo o None si hay error
    """
    payload = {
        "password": contrasena,
        "cmd": "reg"
    }
    api_url = build_api_url(ip)

    try:
        data = _post(api_url, contrasena, headers or {}, {"cmd": "reg"})

        if data.get("result") or data.get("sn"):
            record = data.get("record")
            record =[{
                'sn': data.get("sn"),
                'curip': data.get('curip'),
                'mac': data.get('mac')
            }]
            if isinstance(record, list) and record:
                record = record[0]
            if isinstance(record, dict):
                logging.info("Obtenida información del dispositivo biométrico actual")
                return record

        logging.error(f"Error en respuesta API de dispositivo: {data}")
        return None
    except Exception as e:
        logging.error(f"Error en petición API de dispositivo: {e}")
        return None


def sync_employees_from_api(api_url, password, headers=None):
    """Obtiene los empleados del biométrico indicado; la persistencia la hace el repositorio."""
    return get_user_list(api_url, password, headers) or []


def get_attendance_logs(enrollid, from_date, to_date, api_url, password, headers=None, index=0):
    """
    Obtiene los registros de asistencia para un empleado específico en un rango de fechas.

    :param enrollid: ID del empleado
    :param from_date: Fecha de inicio (YYYY-MM-DD)
    :param to_date: Fecha de fin (YYYY-MM-DD)
    :param index: Índice de paginación (por defecto 0)
    :return: Lista de registros o None si hay error
    """
    try:
        data = _post(
            api_url,
            password,
            headers or {},
            {
                "cmd": "getlog",
                "index": index,
                "enrollid": enrollid,
                "from": from_date,
                "to": to_date,
            },
        )

        if data.get("result"):
            logging.info(f"Obtenidos {data.get('count', 0)} registros para empleado {enrollid}")
            return data.get("record", [])
        else:
            logging.error(f"Error en respuesta API: {data}")
            return None
    except Exception as e:
        logging.error(f"Error en petición API: {e}")
        return None