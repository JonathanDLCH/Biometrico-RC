import unittest
from datetime import datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.models import AttendanceRecord, Base
from src.repository import bulk_insert_attendance_logs


class TestAttendanceRepository(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_bulk_insert_ignores_existing_and_repeated_records(self):
        with Session(self.engine) as session:
            result = bulk_insert_attendance_logs(
                session,
                10,
                [
                    {"time": "2026-08-18 08:00:00"},
                    {"time": "2026-08-18 08:00:00"},
                ],
                biometric_id=None,
            )
            session.commit()
            records = session.scalars(select(AttendanceRecord)).all()

        self.assertEqual(result, 1)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].register_time, datetime(2026, 8, 18, 8, 0))


if __name__ == "__main__":
    unittest.main()
