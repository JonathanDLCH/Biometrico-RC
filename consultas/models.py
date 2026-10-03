from django.db import models


class BiometricDevice(models.Model):
    id_biometrico = models.PositiveIntegerField(primary_key=True)
    ip = models.CharField(max_length=20)
    sn = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    estado = models.BooleanField()
    usuario = models.CharField(max_length=30, null=True, blank=True)
    contrasena = models.CharField(max_length=30)
    ubicacion = models.CharField(max_length=100, null=True, blank=True)
    ultima_sincronizacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "biometricos"
        ordering = ["id_biometrico"]

    def __str__(self):
        return self.ubicacion or self.sn


class Employee(models.Model):
    id_empleado = models.PositiveIntegerField(primary_key=True)
    nombre = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100, null=True, blank=True)
    turno = models.CharField(max_length=50, null=True, blank=True)
    estado = models.BooleanField()
    mail = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "empleados"
        ordering = ["nombre", "id_empleado"]

    def __str__(self):
        return self.nombre


class AttendanceRecord(models.Model):
    id_registro = models.AutoField(primary_key=True)
    register_time = models.DateTimeField()
    tipo_registro = models.CharField(max_length=50, null=True, blank=True)
    biometrico = models.ForeignKey(
        BiometricDevice,
        db_column="id_biometrico",
        on_delete=models.DO_NOTHING,
        related_name="registros",
    )
    empleado = models.ForeignKey(
        Employee,
        db_column="id_empleado",
        on_delete=models.DO_NOTHING,
        related_name="registros",
    )

    class Meta:
        managed = False
        db_table = "registros"
        ordering = ["-register_time", "-id_registro"]

    def __str__(self):
        return f"{self.empleado_id} - {self.register_time:%Y-%m-%d %H:%M:%S}"
