from fastapi import Header, Query
from typing import Optional


def get_language(
    x_language: Optional[str] = Header(None, alias="X-Language"),
    language: Optional[str] = Query(None),
) -> str:
    lang = x_language or language or "EN"
    return lang.upper() if lang.upper() in ("EN", "FR") else "EN"
