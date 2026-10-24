from collections import defaultdict
from datetime import date, datetime, time, timedelta


ENTRY_TIME = datetime.strptime("09:00:00", "%H:%M:%S").time()
EXIT_TIME = datetime.strptime("18:00:00", "%H:%M:%S").time()
DELAY_TOLERANCE_MINUTES = 30


def _day_records(records):
    grouped = defaultdict(list)
    for record in records:
        grouped[record["date"]].append(record)
    return grouped


def _minutes_late(entry_time):
    if entry_time <= ENTRY_TIME:
        return 0
    return int((datetime.combine(date.today(), entry_time) - datetime.combine(date.today(), ENTRY_TIME)).total_seconds() // 60)


def _hours_worked_for_day(day_records):
    if len(day_records) < 2:
        return 0

    first_entry = min(day_records, key=lambda record: record["register_time"]) 
    last_exit = max(day_records, key=lambda record: record["register_time"])
    duration = last_exit["register_time"] - first_entry["register_time"]
    return round(duration.total_seconds() / 3600, 2)


def calculate_average_entry_time(records):
    """Calcula la hora media de la primera marcación de cada empleado por día."""
    first_entries = {}
    for record in records:
        key = (record["employee_id"], record["date"])
        current_entry = first_entries.get(key)
        if current_entry is None or record["register_time"] < current_entry:
            first_entries[key] = record["register_time"]

    if not first_entries:
        return None

    average_minutes = round(
        sum(
            entry.hour * 60 + entry.minute + entry.second / 60
            for entry in first_entries.values()
        )
        / len(first_entries)
    ) % (24 * 60)
    return time(hour=average_minutes // 60, minute=average_minutes % 60)


def calculate_employee_record_counts(employees, records):
    """Ordena al personal activo por cantidad de registros, incluyendo quienes tienen cero."""
    employee_counts = {
        employee["employee_id"]: {
            "employee_id": employee["employee_id"],
            "employee_name": employee["employee_name"],
            "record_count": 0,
        }
        for employee in employees
    }

    for record in records:
        employee = employee_counts.get(record["employee_id"])
        if employee is not None:
            employee["record_count"] += 1

    return sorted(
        employee_counts.values(),
        key=lambda employee: (employee["record_count"], employee["employee_name"]),
    )


def calculate_employee_rankings(records):
    """Agrupa registros por empleado y calcula horas trabajadas y retardos."""
    employees = defaultdict(list)

    for record in records:
        employee_id = record["employee_id"]
        employees[employee_id].append(record)

    rankings = []
    for employee_id, employee_records in employees.items():
        employee_name = employee_records[0]["employee_name"]
        daily_hours = []
        delays = 0

        for day, day_entries in _day_records(employee_records).items():
            sorted_entries = sorted(day_entries, key=lambda item: item["register_time"])
            if len(sorted_entries) >= 2:
                daily_hours.append(_hours_worked_for_day(sorted_entries))
            first_entry = sorted_entries[0]
            if first_entry["register_time"].time() > ENTRY_TIME:
                delay_minutes = _minutes_late(first_entry["register_time"].time())
                if delay_minutes > DELAY_TOLERANCE_MINUTES:
                    delays += 1

        rankings.append(
            {
                "employee_id": employee_id,
                "employee_name": employee_name,
                "hours_worked": round(sum(daily_hours), 2),
                "delays": delays,
            }
        )

    rankings.sort(key=lambda item: (-item["hours_worked"], -item["delays"], item["employee_name"]))
    return rankings
