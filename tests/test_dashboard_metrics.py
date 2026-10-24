from datetime import date, datetime

from django.test import SimpleTestCase

from consultas.metrics import (
    calculate_average_entry_time,
    calculate_employee_record_counts,
    calculate_employee_rankings,
)


class DashboardMetricsTests(SimpleTestCase):
    def test_ranks_active_employees_by_record_count_including_zero(self):
        employees = [
            {"employee_id": 1, "employee_name": "Ana López"},
            {"employee_id": 2, "employee_name": "Luis Pérez"},
            {"employee_id": 3, "employee_name": "Marta Ruiz"},
        ]
        records = [
            {"employee_id": 1},
            {"employee_id": 1},
            {"employee_id": 2},
            {"employee_id": 99},
        ]

        ranking = calculate_employee_record_counts(employees, records)

        self.assertEqual(
            ranking,
            [
                {"employee_id": 3, "employee_name": "Marta Ruiz", "record_count": 0},
                {"employee_id": 2, "employee_name": "Luis Pérez", "record_count": 1},
                {"employee_id": 1, "employee_name": "Ana López", "record_count": 2},
            ],
        )

    def test_record_count_ranking_is_empty_without_active_employees(self):
        self.assertEqual(calculate_employee_record_counts([], [{"employee_id": 1}]), [])

    def test_calculates_average_of_first_daily_entries(self):
        records = [
            {
                "employee_id": 1,
                "employee_name": "Ana López",
                "date": date(2026, 10, 1),
                "register_time": datetime(2026, 10, 1, 10, 5),
            },
            {
                "employee_id": 1,
                "employee_name": "Ana López",
                "date": date(2026, 10, 1),
                "register_time": datetime(2026, 10, 1, 18, 10),
            },
            {
                "employee_id": 1,
                "employee_name": "Ana López",
                "date": date(2026, 10, 2),
                "register_time": datetime(2026, 10, 2, 9, 0),
            },
            {
                "employee_id": 2,
                "employee_name": "Luis Pérez",
                "date": date(2026, 10, 1),
                "register_time": datetime(2026, 10, 1, 8, 50),
            },
            {
                "employee_id": 2,
                "employee_name": "Luis Pérez",
                "date": date(2026, 10, 1),
                "register_time": datetime(2026, 10, 1, 17, 30),
            },
            {
                "employee_id": 2,
                "employee_name": "Luis Pérez",
                "date": date(2026, 10, 2),
                "register_time": datetime(2026, 10, 2, 9, 15),
            },
        ]

        average_entry_time = calculate_average_entry_time(records)

        self.assertEqual(average_entry_time.hour, 9)
        self.assertEqual(average_entry_time.minute, 18)

    def test_average_entry_time_is_none_without_records(self):
        self.assertIsNone(calculate_average_entry_time([]))

    def test_calculates_hours_and_delays_for_each_employee(self):
        records = [
            {
                "employee_id": 1,
                "employee_name": "Ana López",
                "date": date(2026, 10, 1),
                "register_time": datetime(2026, 10, 1, 10, 5),
            },
            {
                "employee_id": 1,
                "employee_name": "Ana López",
                "date": date(2026, 10, 1),
                "register_time": datetime(2026, 10, 1, 18, 10),
            },
            {
                "employee_id": 1,
                "employee_name": "Ana López",
                "date": date(2026, 10, 2),
                "register_time": datetime(2026, 10, 2, 9, 00),
            },
            {
                "employee_id": 1,
                "employee_name": "Ana López",
                "date": date(2026, 10, 2),
                "register_time": datetime(2026, 10, 2, 18, 00),
            },
            {
                "employee_id": 2,
                "employee_name": "Luis Pérez",
                "date": date(2026, 10, 1),
                "register_time": datetime(2026, 10, 1, 8, 50),
            },
            {
                "employee_id": 2,
                "employee_name": "Luis Pérez",
                "date": date(2026, 10, 1),
                "register_time": datetime(2026, 10, 1, 17, 30),
            },
            {
                "employee_id": 2,
                "employee_name": "Luis Pérez",
                "date": date(2026, 10, 2),
                "register_time": datetime(2026, 10, 2, 9, 15),
            },
        ]

        rankings = calculate_employee_rankings(records)

        self.assertEqual(rankings[0]["employee_id"], 1)
        self.assertEqual(rankings[0]["hours_worked"], 17.08)
        self.assertEqual(rankings[0]["delays"], 1)
        self.assertEqual(rankings[1]["employee_id"], 2)
        self.assertEqual(rankings[1]["hours_worked"], 8.67)
        self.assertEqual(rankings[1]["delays"], 0)

    def test_ignores_incomplete_days_when_calculating_hours(self):
        records = [
            {
                "employee_id": 3,
                "employee_name": "Marta Ruiz",
                "date": date(2026, 10, 3),
                "register_time": datetime(2026, 10, 3, 9, 00),
            }
        ]

        rankings = calculate_employee_rankings(records)

        self.assertEqual(rankings[0]["hours_worked"], 0)
        self.assertEqual(rankings[0]["delays"], 0)
