from datetime import date, datetime

from django.test import SimpleTestCase

from consultas.metrics import calculate_employee_rankings


class DashboardMetricsTests(SimpleTestCase):
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
