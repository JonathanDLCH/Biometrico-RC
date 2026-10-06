from collections import defaultdict
from datetime import date, datetime, timedelta


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
