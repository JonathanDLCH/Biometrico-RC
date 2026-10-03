from datetime import date

from django.test import SimpleTestCase

from consultas.forms import AttendanceFilterForm


class AttendanceFilterFormTests(SimpleTestCase):
    def test_single_date_queries_that_day(self):
        form = AttendanceFilterForm(
            data={"start_date": "2026-10-03", "end_date": "", "employee": ""}
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["end_date"], date(2026, 10, 3))

    def test_end_date_requires_start_date(self):
        form = AttendanceFilterForm(
            data={"start_date": "", "end_date": "2026-10-03", "employee": ""}
        )

        self.assertFalse(form.is_valid())
        self.assertIn("start_date", form.errors)

    def test_end_date_cannot_precede_start_date(self):
        form = AttendanceFilterForm(
            data={"start_date": "2026-10-04", "end_date": "2026-10-03", "employee": ""}
        )

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
