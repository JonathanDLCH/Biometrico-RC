import csv
from datetime import date, datetime, time
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase

from consultas.views import export_attendance_csv


class AttendanceExportTests(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)
        self.record = SimpleNamespace(
            register_time=datetime(2026, 10, 3, 9, 5, 7),
            empleado_id=17,
            empleado=SimpleNamespace(nombre="Ana García"),
            biometrico=SimpleNamespace(ubicacion="Torre A"),
        )
        self.records = Mock()
        self.records.filter.return_value = self.records
        self.records.order_by.return_value.iterator.return_value = [self.record]

    def _export(self, query_string="", cleaned_data=None):
        request = self.request_factory.get(f"/registros/exportar/{query_string}")
        request.user = self.user
        form = Mock()
        form.is_valid.return_value = True
        form.cleaned_data = cleaned_data or {}
        with (
            patch("consultas.views.AttendanceFilterForm", return_value=form),
            patch(
                "consultas.views.AttendanceRecord.objects.select_related",
                return_value=self.records,
            ),
        ):
            response = export_attendance_csv(request)
        return response, form

    def test_exports_all_records_as_excel_compatible_csv(self):
        response, form = self._export()

        rows = list(csv.reader(StringIO(response.content.decode("utf-8-sig"))))
        self.assertEqual(
            rows,
            [
                ["Fecha y hora", "ID Empleado", "Empleado", "Ubicación"],
                ["2026-10-03 09:05:07", "17", "Ana García", "Torre A"],
            ],
        )
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment;", response["Content-Disposition"])
        form.is_valid.assert_not_called()

    def test_export_applies_requested_filters(self):
        employee = SimpleNamespace(id_empleado=17)
        response, form = self._export(
            "?start_date=2026-10-03&employee=17",
            {
                "start_date": date(2026, 10, 3),
                "end_date": None,
                "employee": employee,
            },
        )

        form.is_valid.assert_called_once()
        self.records.filter.assert_any_call(
            register_time__gte=datetime.combine(date(2026, 10, 3), time.min)
        )
        self.records.filter.assert_any_call(empleado=employee)
        self.assertEqual(response.status_code, 200)

    def test_export_requires_authentication(self):
        request = self.request_factory.get("/registros/exportar/")
        request.user = AnonymousUser()

        response = export_attendance_csv(request)

        self.assertEqual(response.status_code, 302)

    def test_formula_prefix_is_escaped_in_csv_text(self):
        self.record.empleado.nombre = "=HYPERLINK(\"https://example.com\")"

        response, _ = self._export()
        rows = list(csv.reader(StringIO(response.content.decode("utf-8-sig"))))

        self.assertEqual(rows[1][2], "'=HYPERLINK(\"https://example.com\")")
