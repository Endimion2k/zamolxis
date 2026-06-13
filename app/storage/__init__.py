"""Stocare SQLite pentru dosarele clasificate (fără dependențe externe)."""

from .db import conecteaza, init_db
from .repo import (
    get_caz,
    get_grup,
    list_cazuri,
    list_grupuri,
    log_scan,
    statistici,
    upsert_caz,
    upsert_grup,
)

__all__ = [
    "conecteaza",
    "init_db",
    "upsert_caz",
    "get_caz",
    "list_cazuri",
    "log_scan",
    "statistici",
    "upsert_grup",
    "list_grupuri",
    "get_grup",
]
