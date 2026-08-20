import json
from datetime import datetime

from sqlalchemy import select

from src.models import AttendanceRecord, BiometricDevice, Employee


def normalize_biometric_data(device_data):
    return {
        "ip": device_data.get("ip") or device_data.get("host") or device_data.get("address"),
        "sn": device_data.get("sn") or device_data.get("serial") or device_data.get("Serial"),
        "modelo": device_data.get("model") or device_data.get("modelo") or "UNKNOWN",
        "estado": device_data.get("estado") if isinstance(device_data.get("estado"), bool) else True,
        "usuario": device_data.get("usuario") or device_data.get("user") or None,
        "contrasena": device_data.get("contrasena") or device_data.get("password") or "unknown",
    }


def normalize_employee_data(employee_data):
    return {
        "id_empleado": int(employee_data.get("id")) if employee_data.get("id") is not None else None,
        "nombre": employee_data.get("name") or employee_data.get("nombre"),
        "departamento": employee_data.get("department") or employee_data.get("departamento"),
        "turno": employee_data.get("turno"),
        "estado": employee_data.get("estado") if isinstance(employee_data.get("estado"), bool) else True,
        "mail": (
            employee_data.get("email")
            or employee_data.get("userprofile")
            or employee_data.get("mail")
            or employee_data.get("correo")
        ),
    }


def get_all_biometric_devices(session):
    statement = select(BiometricDevice).order_by(BiometricDevice.id_biometrico)
    return session.scalars(statement).all()


def get_biometric_by_sn(session, sn):
    if not sn:
        return None
    statement = select(BiometricDevice).where(BiometricDevice.sn == sn)
    return session.scalars(statement).first()


def get_biometric_by_ip(session, ip):
    if not ip:
        return None
    statement = select(BiometricDevice).where(BiometricDevice.ip == ip)
    return session.scalars(statement).first()


def get_last_sync(session, biometric_id):
    device = session.get(BiometricDevice, biometric_id)
    return device.ultima_sincronizacion if device else None


def mark_biometric_synced(session, biometric_id, synced_at):
    device = session.get(BiometricDevice, biometric_id)
    if device is None:
        raise ValueError(f"Biométrico no encontrado: {biometric_id}")
    device.ultima_sincronizacion = synced_at
    session.add(device)


def get_all_employees(session):
    statement = select(Employee).order_by(Employee.nombre)
    return session.scalars(statement).all()


def get_all_employees_dict(session):
    return [
        {
            "id": employee.id_empleado,
            "name": employee.nombre,
            "email": employee.mail,
        }
        for employee in get_all_employees(session)
    ]


def create_or_update_biometric(session, device_data):
    normalized = normalize_biometric_data(device_data)
    if normalized["sn"] is None:
        return None

    device = get_biometric_by_sn(session, normalized["sn"])
    if device is None and normalized["ip"]:
        device = get_biometric_by_ip(session, normalized["ip"])

    if device is None:
        device = BiometricDevice(sn=normalized["sn"], ip=normalized["ip"] or "unknown")

    if normalized["ip"]:
        device.ip = normalized["ip"]
    if normalized["modelo"]:
        device.modelo = normalized["modelo"]
    if normalized["usuario"]:
        device.usuario = normalized["usuario"]
    if normalized["contrasena"]:
        device.contrasena = normalized["contrasena"]

    session.add(device)
    return device


def create_or_update_employee(session, employee_data):
    normalized = normalize_employee_data(employee_data)
    if normalized["id_empleado"] is None:
        return None

    employee = session.get(Employee, normalized["id_empleado"])
    if employee is None:
        employee = Employee(id_empleado=normalized["id_empleado"])

    if normalized["nombre"]:
        employee.nombre = normalized["nombre"]
    if normalized["departamento"]:
        employee.departamento = normalized["departamento"]
    if normalized["turno"]:
        employee.turno = normalized["turno"]
    if normalized["mail"]:
        employee.mail = normalized["mail"]
    if normalized["estado"] is not None:
        employee.estado = normalized["estado"]

    session.add(employee)
    return employee


def get_attendance_records_for_employee(session, employee_id, from_date, to_date):
    from_datetime = datetime.strptime(from_date, "%Y-%m-%d")
    to_datetime = datetime.strptime(to_date, "%Y-%m-%d")
    to_datetime = to_datetime.replace(hour=23, minute=59, second=59)

    statement = (
        select(AttendanceRecord)
        .where(
            AttendanceRecord.id_empleado == employee_id,
            AttendanceRecord.register_time >= from_datetime,
            AttendanceRecord.register_time <= to_datetime,
        )
        .order_by(AttendanceRecord.register_time)
    )
    return session.scalars(statement).all()


def bulk_insert_attendance_logs(session, employee_id, records, biometric_id=None):
    if not records:
        return 0

    parsed_records = []
    for record in records:
        time_string = record.get("time")
        if not time_string:
            continue

        try:
            register_time = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

        parsed_records.append(
            {
                "register_time": register_time,
                "tipo_registro": (
                    record.get("tipo_registro")
                    or record.get("type")
                    or record.get("mode")
                    or record.get("inout")
                    or record.get("event")
                    or ""
                ),
                "id_biometrico": biometric_id,
                "raw_payload": json.dumps(record, ensure_ascii=False),
            }
        )

    if not parsed_records:
        return 0

    times = [item["register_time"] for item in parsed_records]
    existing_times = set(
        session.scalars(
            select(AttendanceRecord.register_time).where(
                AttendanceRecord.id_empleado == employee_id,
                AttendanceRecord.register_time.in_(times),
            )
        ).all()
    )

    inserted = 0
    for item in parsed_records:
        if item["register_time"] in existing_times:
            continue

        attendance = AttendanceRecord(
            id_empleado=employee_id,
            register_time=item["register_time"],
            tipo_registro=str(item["tipo_registro"]),
            id_biometrico=item["id_biometrico"],
            raw_payload=item["raw_payload"],
        )
        session.add(attendance)
        existing_times.add(item["register_time"])
        inserted += 1

    return inserted
