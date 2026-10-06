from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from .forms import AttendanceFilterForm
from .metrics import calculate_employee_rankings
from .models import AttendanceRecord, BiometricDevice
from .models import Employee


@login_required
def biometric_list(request):
    devices = BiometricDevice.objects.all().order_by("id_biometrico")
    employees = Employee.objects.all().order_by("nombre", "id_empleado")
    attendance_records = AttendanceRecord.objects.select_related("empleado")
    rankings = calculate_employee_rankings(
        [
            {
                "employee_id": record.empleado_id,
                "employee_name": record.empleado.nombre,
                "date": record.register_time.date(),
                "register_time": record.register_time,
            }
            for record in attendance_records
        ]
    )

    return render(
        request,
        "consultas/biometric_list.html",
        {
            "devices": devices,
            "employees": employees,
            "total_records": attendance_records.count(),
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


@login_required
def attendance_list(request):
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
