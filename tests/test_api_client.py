import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.api_client import get_attendance_logs, sync_employees_from_api

class TestApiClient(unittest.TestCase):
    @patch('src.api_client.requests.post')
    def test_get_attendance_logs_success(self, mock_post):
        # Mock respuesta exitosa
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": True,
            "count": 14,
            "record": [
                {"enrollid": 52, "time": "2026-04-15 09:40:57"},
                {"enrollid": 52, "time": "2026-04-15 19:35:30"}
            ]
        }
        mock_post.return_value = mock_response

        records = get_attendance_logs(52, "2026-04-01", "2026-04-15")
        self.assertIsNotNone(records)
        self.assertEqual(len(records), 2)

    @patch('src.api_client.requests.post')
    def test_get_attendance_logs_failure(self, mock_post):
        mock_post.side_effect = Exception("Connection error")
        records = get_attendance_logs(52, "2026-04-01", "2026-04-15")
        self.assertIsNone(records)

    @patch('src.api_client.requests.post')
    def test_sync_employees_from_api_creates_file_and_adds_new_user(self, mock_post):
        with tempfile.TemporaryDirectory() as tmpdir:
            employees_path = Path(tmpdir) / "employees.json"
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "result": True,
                "count": 2,
                "record": [
                    {"id": 10, "name": "Empleado Uno", "department": "STAFF"},
                    {"id": 20, "name": "Empleado Dos", "department": "OPERATIONS"}
                ]
            }
            mock_post.return_value = mock_response

            employees = sync_employees_from_api(employees_file_path=employees_path)

            self.assertEqual(len(employees), 2)
            self.assertTrue(employees_path.exists())
            persisted = json.loads(employees_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted[1]["name"], "Empleado Dos")

    @patch('src.api_client.requests.post')
    def test_sync_employees_from_api_preserves_existing_email(self, mock_post):
        with tempfile.TemporaryDirectory() as tmpdir:
            employees_path = Path(tmpdir) / "employees.json"
            employees_path.write_text(
                json.dumps([{"id": 10, "name": "Empleado Uno", "department": "OLD", "email": "empleado@example.com"}]),
                encoding="utf-8"
            )
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "result": True,
                "count": 1,
                "record": [{"id": 10, "name": "Empleado Uno", "department": "STAFF"}]
            }
            mock_post.return_value = mock_response

            employees = sync_employees_from_api(employees_file_path=employees_path)

            self.assertEqual(employees[0]["department"], "STAFF")
            self.assertEqual(employees[0]["email"], "empleado@example.com")

if __name__ == '__main__':
    unittest.main()