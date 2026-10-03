from django import forms
from django.core.exceptions import ValidationError

from .models import Employee


class AttendanceFilterForm(forms.Form):
    start_date = forms.DateField(
        label="Desde",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        label="Hasta",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    employee = forms.ModelChoiceField(
        label="Empleado",
        queryset=Employee.objects.order_by("nombre", "id_empleado"),
        required=False,
        empty_label="Todos los empleados",
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if end_date and not start_date:
            self.add_error("start_date", "Indica también la fecha inicial.")
        elif start_date and not end_date:
            cleaned_data["end_date"] = start_date
        elif start_date and end_date and end_date < start_date:
            raise ValidationError("La fecha final no puede ser anterior a la inicial.")

        return cleaned_data
