import os


os.environ.setdefault("DJANGO_DEBUG", "true")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret")
os.environ.setdefault("DATABASE_URL", "mysql+pymysql://test:test@localhost/test")

from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
