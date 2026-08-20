import logging

import yagmail

from config.settings import EMAIL_PASSWORD, EMAIL_USER

logger = logging.getLogger(__name__)


def send_support_error(recipients, error):
    """Envía el error de una ejecución a soporte sin ocultar el fallo original."""
    if not recipients:
        logger.warning("SUPPORT_EMAILS no está configurado; no se envió la alerta")
        return False
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.warning("EMAIL_USER/EMAIL_PASSWORD no están configurados; no se envió la alerta")
        return False

    try:
        yagmail.SMTP(EMAIL_USER, EMAIL_PASSWORD).send(
            to=recipients,
            subject="Fallo en sincronización biométrica",
            contents=(
                "La sincronización diaria falló. El cursor no avanzó y se reintentará.\n\n"
                f"Error: {error}"
            ),
        )
        logger.info("Alerta de sincronización enviada a soporte")
        return True
    except Exception:
        logger.exception("No se pudo enviar la alerta a soporte")
        return False
