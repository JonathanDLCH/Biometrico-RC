import os
from dotenv import load_dotenv

load_dotenv()

# API Biométrico
API_URL = os.getenv("BIOMETRIC_API_URL", "http://192.168.10.2:80/api")
API_PASSWORD = os.getenv("BIOMETRIC_PASSWORD")
API_DEVICE_COOKIE = os.getenv("BIOMETRIC_DEVICE_COOKIE", "")
API_HEADERS = {
    "Cookie": API_DEVICE_COOKIE,
}

# Otros
LOG_FILE = "logs/biometrico.log"
# Base de datos MySQL/MariaDB
DATABASE_URL = os.getenv("DATABASE_URL")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

if not DATABASE_URL and DB_USER and DB_PASSWORD and DB_NAME:
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() in ("1", "true", "yes")

# Configuración de Email
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RH = [email.strip() for email in os.getenv("EMAIL_RH", "").split(",") if email.strip()]
SUPPORT_EMAILS = [email.strip() for email in os.getenv("SUPPORT_EMAILS", "").split(",") if email.strip()]
INITIAL_SYNC_DAYS = int(os.getenv("INITIAL_SYNC_DAYS", "1"))