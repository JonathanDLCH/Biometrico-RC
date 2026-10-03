from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from .forms import AttendanceFilterForm
from .models import AttendanceRecord, BiometricDevice


@login_required
def biometric_list(request):
    devices = BiometricDevice.objects.all().order_by("id_biometrico")
    return render(request, "consultas/biometric_list.html", {"devices": devices})


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
