from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import DATABASE_URL, SQLALCHEMY_ECHO

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no configurada. Establece la variable de entorno "
        "DATABASE_URL o DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME en .env"
    )

engine = create_engine(
    DATABASE_URL,
    echo=SQLALCHEMY_ECHO,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def init_db():
    from src.models import Base as ModelsBase

    ModelsBase.metadata.create_all(bind=engine)
