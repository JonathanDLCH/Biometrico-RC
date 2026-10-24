from django.urls import path

from . import views


urlpatterns = [
    path("", views.biometric_list, name="biometricos"),
    path("registros/", views.attendance_list, name="registros"),
    path("registros/exportar/", views.export_attendance_csv, name="exportar_registros"),
]
