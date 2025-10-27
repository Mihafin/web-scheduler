from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL не задан. Укажите строку подключения к PostgreSQL (Cloud SQL)."
        )
    if not url.startswith("postgresql"):
        raise RuntimeError("Поддерживается только PostgreSQL (psycopg2).")
    return url


def _engine_pool_kwargs() -> dict:
    pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    pool_pre_ping = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
    return {
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_recycle": pool_recycle,
        "pool_pre_ping": pool_pre_ping,
    }


DATABASE_URL = _get_database_url()

engine = create_engine(
    DATABASE_URL,
    **_engine_pool_kwargs(),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

