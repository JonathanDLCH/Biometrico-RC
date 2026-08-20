import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import main


class FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def flush(self):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class TestSyncService(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 18, 18, 0, 0)
        self.device = SimpleNamespace(id_biometrico=3, sn="SN-3")
        self.employees = [{"id": 10, "name": "Ana"}, {"id": 20, "name": "Luis"}]
        self.session = FakeSession()

    @patch("main.create_or_update_biometric")
    def test_identify_biometric_creates_or_reuses_device(self, create_device):
        create_device.return_value = self.device

        result = main.identify_biometric(self.session, {"sn": "SN-3", "ip": "10.0.0.3"})

        self.assertIs(result, self.device)
        create_device.assert_called_once()

    @patch("main.create_or_update_employee", side_effect=[object(), None])
    def test_sync_employees_only_returns_valid_employees(self, create_employee):
        result = main.sync_employees(self.session, self.employees)

        self.assertEqual(result, [self.employees[0]])
        self.assertEqual(create_employee.call_count, 2)

    @patch("main.bulk_insert_attendance_logs", return_value=2)
    @patch("main.get_attendance_logs", return_value=[{"time": "2026-08-18 08:00:00"}])
    def test_fetch_and_store_attendance_uses_requested_window(self, get_logs, insert):
        result = main.fetch_and_store_attendance(
            self.session,
            [self.employees[0]],
            3,
            datetime(2026, 8, 17),
            self.now,
        )

        self.assertEqual(result, 2)
        get_logs.assert_called_once_with(10, "2026-08-17", "2026-08-18")
        insert.assert_called_once()

    @patch("main.mark_biometric_synced")
    @patch("main.fetch_and_store_attendance", return_value=4)
    @patch("main.sync_employees")
    @patch("main.get_last_sync", return_value=None)
    @patch("main.identify_biometric")
    @patch("main.sync_employees_from_api")
    @patch("main.get_device_info")
    def test_run_sync_commits_only_after_all_steps(
        self,
        get_device_info,
        sync_from_api,
        identify,
        get_last_sync,
        sync_employees,
        fetch,
        mark_synced,
    ):
        get_device_info.return_value = {"sn": "SN-3"}
        sync_from_api.return_value = self.employees
        identify.return_value = self.device
        sync_employees.return_value = self.employees

        result = main.run_sync(self.now, lambda: self.session)

        self.assertEqual(result, {"employees": 2, "attendance": 4})
        self.assertTrue(self.session.committed)
        self.assertFalse(self.session.rolled_back)
        mark_synced.assert_called_once_with( self.session, 3, self.now)

    @patch("main.mark_biometric_synced")
    @patch("main.fetch_and_store_attendance", side_effect=RuntimeError("API caída"))
    @patch("main.sync_employees", return_value=[])
    @patch("main.get_last_sync", return_value=None)
    @patch("main.identify_biometric")
    @patch("main.sync_employees_from_api", return_value=[])
    @patch("main.get_device_info", return_value={"sn": "SN-3"})
    def test_run_sync_rolls_back_and_does_not_move_cursor_on_error(
        self,
        get_device_info,
        sync_from_api,
        identify,
        get_last_sync,
        sync_employees,
        fetch,
        mark_synced,
    ):
        identify.return_value = self.device

        with self.assertRaisesRegex(RuntimeError, "API caída"):
            main.run_sync(self.now, lambda: self.session)

        self.assertFalse(self.session.committed)
        self.assertTrue(self.session.rolled_back)
        mark_synced.assert_not_called()

    @patch("main.send_support_error")
    @patch("main.init_db", side_effect=RuntimeError("base no disponible"))
    def test_main_notifies_support_when_startup_fails(self, init_db, send_error):
        result = main.main()

        self.assertEqual(result, 1)
        send_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
