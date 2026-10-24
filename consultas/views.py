import csv
from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .forms import AttendanceFilterForm
from .metrics import (
    calculate_average_entry_time,
    calculate_employee_record_counts,
    calculate_employee_rankings,
)
from .models import AttendanceRecord, BiometricDevice
from .models import Employee


@login_required
def biometric_list(request):
    devices = BiometricDevice.objects.all().order_by("id_biometrico")
    employees = Employee.objects.filter(estado=True).order_by("nombre", "id_empleado")
    attendance_records = AttendanceRecord.objects.select_related("empleado")
    metric_records = [
        {
            "employee_id": record.empleado_id,
            "employee_name": record.empleado.nombre,
            "date": record.register_time.date(),
            "register_time": record.register_time,
        }
        for record in attendance_records
    ]
    rankings = calculate_employee_rankings(metric_records)
    average_entry_time = calculate_average_entry_time(metric_records)
    least_registered_employees = calculate_employee_record_counts(
        [
            {"employee_id": employee.id_empleado, "employee_name": employee.nombre}
            for employee in employees
        ],
        metric_records,
    )[:3]

    return render(
        request,
        "consultas/biometric_list.html",
        {
            "devices": devices,
            "employees": employees,
            "total_records": attendance_records.count(),
            "average_entry_time": average_entry_time,
            "least_registered_employees": least_registered_employees,
            "top_workers": rankings[:3],
            "delay_leaders": sorted(
                rankings,
                key=lambda item: (-item["delays"], -item["hours_worked"], item["employee_name"]),
            )[:3],
            "recent_syncs": devices.filter(ultima_sincronizacion__isnull=False).order_by(
                "-ultima_sincronizacion"
            )[:5],
        },
    )


def _attendance_records_for_request(request):
    form = AttendanceFilterForm(request.GET or None)
    records = AttendanceRecord.objects.select_related("empleado", "biometrico")
    filter_keys = {"start_date", "end_date", "employee"}
    filters_requested = any(key in request.GET for key in filter_keys)

    if filters_requested:
        if form.is_valid():
            start_date = form.cleaned_data.get("start_date")
            end_date = form.cleaned_data.get("end_date")
            employee = form.cleaned_data.get("employee")
            if start_date:
                records = records.filter(
                    register_time__gte=datetime.combine(start_date, time.min)
                )
            if end_date:
                records = records.filter(
                    register_time__lt=datetime.combine(end_date + timedelta(days=1), time.min)
                )
            if employee:
                records = records.filter(empleado=employee)
        else:
            records = records.none()

    return form, records, filters_requested


@login_required
def attendance_list(request):
    form, records, filters_requested = _attendance_records_for_request(request)
    page_number = request.GET.get("page")
    page_obj = Paginator(records.order_by("-register_time", "-id_registro"), 100).get_page(
        page_number
    )
    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        "consultas/attendance_list.html",
        {
            "form": form,
            "page_obj": page_obj,
            "total_records": page_obj.paginator.count,
            "querystring": query_params.urlencode(),
            "filters_requested": filters_requested,
        },
    )


def _safe_csv_text(value):
    text = str(value or "")
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


@login_required
def export_attendance_csv(request):
    _, records, _ = _attendance_records_for_request(request)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="registros-asistencia.csv"'
    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow(["Fecha y hora", "ID Empleado", "Empleado", "Ubicación"])
    for record in records.order_by("-register_time", "-id_registro").iterator():
        timestamp = record.register_time
        if timezone.is_aware(timestamp):
            timestamp = timezone.localtime(timestamp)
        writer.writerow(
            [
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                record.empleado_id,
                _safe_csv_text(record.empleado.nombre),
                _safe_csv_text(record.biometrico.ubicacion or "Sin ubicación"),
            ]
        )

    return response
