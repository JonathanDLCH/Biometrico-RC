import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() in {"1", "true", "yes"}
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Define DJANGO_SECRET_KEY en el entorno.")
    SECRET_KEY = get_random_secret_key()

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "consultas.apps.ConsultasConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "consulta_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "consulta_service.wsgi.application"
ASGI_APPLICATION = "consulta_service.asgi.application"


def _database_settings():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        parsed = urlsplit(database_url)
        if parsed.scheme not in {"mysql", "mysql+pymysql"}:
            raise ImproperlyConfigured("DATABASE_URL debe usar MySQL.")
        database_name = unquote(parsed.path.lstrip("/"))
        if not database_name:
            raise ImproperlyConfigured("DATABASE_URL debe indicar una base de datos.")
        return {
            "ENGINE": "django.db.backends.mysql",
            "NAME": database_name,
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "localhost",
            "PORT": str(parsed.port or 3306),
            "OPTIONS": {"charset": "utf8mb4", "connect_timeout": 10},
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }

    required = ("DB_USER", "DB_PASSWORD", "DB_NAME")
    if not all(os.getenv(key) for key in required):
        raise ImproperlyConfigured(
            "Define DATABASE_URL o DB_USER, DB_PASSWORD y DB_NAME en el entorno."
        )
    return {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4", "connect_timeout": 10},
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }


DATABASES = {"default": _database_settings()}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = False

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "biometricos"
LOGOUT_REDIRECT_URL = "login"

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
