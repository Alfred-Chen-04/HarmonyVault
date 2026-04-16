"""Pytest fixtures shared across the test suite.

Every test that touches the database is skipped automatically when
MySQL is not reachable, so `pytest` still passes on machines where
only the syntax of the code is being verified.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(scope="session")
def db_conn():
    mysql = pytest.importorskip("mysql.connector")
    from config import DB

    try:
        conn = mysql.connect(**DB.to_connector_kwargs())
    except Exception as exc:
        pytest.skip(f"MySQL not reachable: {exc}")
    yield conn
    conn.close()
