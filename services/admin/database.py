import os
from sqlalchemy import create_engine, text

DB_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER','postgres')}:{os.getenv('DB_PASSWORD','postgres')}"
    f"@{os.getenv('DB_HOST','localhost')}:{os.getenv('DB_PORT','5432')}/{os.getenv('DB_NAME','healthai')}"
)

engine = create_engine(DB_URL, echo=False, future=True, pool_pre_ping=True)


def fetch_all(sql: str, params: dict = {}) -> list[dict]:
    with engine.connect() as c:
        return [dict(r) for r in c.execute(text(sql), params).mappings()]


def fetch_one(sql: str, params: dict = {}) -> dict | None:
    with engine.connect() as c:
        r = c.execute(text(sql), params).mappings().first()
        return dict(r) if r else None


def execute(sql: str, params: dict = {}) -> int:
    with engine.begin() as c:
        result = c.execute(text(sql), params)
        return result.rowcount
