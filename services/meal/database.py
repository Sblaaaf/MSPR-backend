import os
from sqlalchemy import create_engine, text

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "healthai"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def get_engine() -> "Engine":
    url = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )
    return create_engine(url, echo=False, future=True, pool_pre_ping=True)


engine = get_engine()


def fetch_all(query: str, params: dict | None = None) -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return [dict(row) for row in result.mappings()]


def fetch_one(query: str, params: dict | None = None) -> dict | None:
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        row = result.mappings().first()
        return dict(row) if row else None


def execute_write(query: str, params: dict | None = None):
    with engine.begin() as conn:
        return conn.execute(text(query), params or {})
