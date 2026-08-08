from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.db import Base


class Employee(Base):
    __tablename__ = "empleados"

    id_empleado = Column(Integer, primary_key=True, autoincrement=False)
    nombre = Column(String(100), nullable=False)
    departamento = Column(String(100), nullable=True)
    turno = Column(String(50), nullable=True)
    estado = Column(Boolean, nullable=False, default=True)
    mail = Column(String(100), nullable=True)

    registros = relationship("AttendanceRecord", back_populates="empleado")


class BiometricDevice(Base):
    __tablename__ = "biometricos"

    id_biometrico = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String(20), nullable=False)
    sn = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    estado = Column(Boolean, nullable=False, default=True)
    usuario = Column(String(30), nullable=True)
    contrasena = Column(String(30), nullable=False)
    ubicacion = Column(String(100), nullable=True)
    ultima_sincronizacion = Column(DateTime, nullable=True)


class AttendanceRecord(Base):
    __tablename__ = "registros"

    id_registro = Column(Integer, primary_key=True, autoincrement=True)
    register_time = Column(DateTime, nullable=False)
    tipo_registro = Column(String(50), nullable=True)
    id_biometrico = Column(Integer, ForeignKey("biometricos.id_biometrico"), nullable=True)
    id_empleado = Column(Integer, ForeignKey("empleados.id_empleado"), nullable=False)
    raw_payload = Column(String(500), nullable=True)

    empleado = relationship("Employee", back_populates="registros")

    __table_args__ = (
        UniqueConstraint("id_empleado", "register_time", name="uq_empleado_registro_fecha"),
    )
