import yagmail
import logging
from config.settings import EMAIL_USER, EMAIL_PASSWORD

logging.basicConfig(level=logging.INFO)

def send_attendance_reports(employee_email=None, rh_emails=None, report_files=None, periodo=""):
    """
    Envía reportes de asistencia por email.
    
    :param employee_email: Email del empleado (opcional)
    :param rh_emails: Lista de emails de RH
    :param report_files: Lista de archivos adjuntos
    :param periodo: Período del reporte (ej. "2026-04-01 al 2026-04-15")
    """
    if not report_files:
        logging.warning("No hay archivos de reporte para enviar")
        return

    # Configurar remitente
    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASSWORD)

    # Determinar destinatarios
    recipients = []
    if rh_emails:
        recipients.extend(rh_emails)
    if employee_email:
        recipients.append(employee_email)

    if not recipients:
        logging.error("No hay destinatarios válidos para enviar el email")
        return

    # Asunto y contenido
    subject = f"Reporte de Asistencias - Período {periodo}"
    body = f"""
Estimado,

Adjunto el reporte de asistencias correspondiente al período {periodo}.

Este es un mensaje automático generado por el sistema de control biométrico.

Atentamente,
Sistema de Gestión de Asistencias
RealCity
"""

    try:
        # Enviar email
        yag.send(
            to=recipients,
            subject=subject,
            contents=body,
            attachments=report_files
        )
        logging.info(f"Email enviado exitosamente a: {', '.join(recipients)}")
        print(f"✅ Email enviado a: {', '.join(recipients)}")
    except Exception as e:
        logging.error(f"Error enviando email: {e}")
        print(f"❌ Error enviando email: {e}")

def send_general_report_to_rh(rh_emails, report_files, periodo, resumen_global):
    """
    Envía el reporte general consolidado al departamento de RH.
    
    :param rh_emails: Lista de emails de RH
    :param report_files: Archivos adjuntos
    :param periodo: Período del reporte
    :param resumen_global: Dict con estadísticas globales
    """
    if not rh_emails or not report_files:
        return

    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASSWORD)

    subject = f"Reporte General de Asistencias - {periodo}"
    
    # Crear contenido con resumen
    resumen_text = "\n".join([f"{k}: {v}" for k, v in resumen_global.items()])
    
    body = f"""
Estimado Departamento de Recursos Humanos,

Adjunto el reporte general consolidado de asistencias para todos los empleados.

Período: {periodo}

Resumen Ejecutivo:
{resumen_text}

Los archivos adjuntos contienen:
- reporte_general_asistencias.csv: Estados por empleado y fecha
- reporte_horas_trabajadas.csv: Horas trabajadas por empleado y fecha
- resumen_global.json: Estadísticas detalladas

Este es un mensaje automático generado por el sistema de control biométrico.

Atentamente,
Sistema de Gestión de Asistencias
RealCity
"""

    try:
        yag.send(
            to=rh_emails,
            subject=subject,
            contents=body,
            attachments=report_files
        )
        logging.info(f"Reporte general enviado a RH: {', '.join(rh_emails)}")
        print(f"✅ Reporte general enviado a RH: {', '.join(rh_emails)}")
    except Exception as e:
        logging.error(f"Error enviando reporte general: {e}")
        print(f"❌ Error enviando reporte general: {e}")