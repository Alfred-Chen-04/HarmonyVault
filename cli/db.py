"""Connection and query helpers used by every CLI subcommand.

Owner: Sky Zhou (sxz903).

All SQL lives in files under ``queries/``. Callers pass a filename and
a parameter dict; the helper substitutes ``%(named)s`` placeholders.
This keeps the convention in AGENTS.md enforced: no inline SQL in Python.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import mysql.connector
from mysql.connector.cursor import MySQLCursorDict

from config import DB, QUERIES_DIR


@contextmanager
def connect() -> Iterator[mysql.connector.MySQLConnection]:
    conn = mysql.connector.connect(**DB.to_connector_kwargs())
    try:
        yield conn
    finally:
        conn.close()


def load_query(name: str) -> str:
    """Read a named SQL file from queries/."""
    path = QUERIES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"queries/{name} not found")
    return path.read_text(encoding="utf-8")


def run_query(sql: str, params: dict[str, Any] | None = None) -> list[dict]:
    """Execute a read-only SQL string and return dict rows."""
    with connect() as conn:
        cur: MySQLCursorDict = conn.cursor(dictionary=True)
        cur.execute(sql, params or {})
        return cur.fetchall()


def run_named(name: str, params: dict[str, Any] | None = None) -> list[dict]:
    """Execute a named SQL file from ``queries/`` and return dict rows."""
    return run_query(load_query(name), params)


def run_mutation(sql: str, params: dict[str, Any] | None = None) -> int:
    """Execute an INSERT/UPDATE/DELETE and return the affected rowcount."""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or {})
        conn.commit()
        return cur.rowcount
