"""Every query file in queries/ should parse and return without error."""

from __future__ import annotations

from pathlib import Path

import pytest

QUERIES_DIR = Path(__file__).resolve().parent.parent / "queries"
SQL_FILES = sorted(p for p in QUERIES_DIR.glob("*.sql")
                   if p.name != "cli_search_clips.sql")


@pytest.mark.parametrize("sql_path", SQL_FILES, ids=lambda p: p.name)
def test_sql_file_executes(db_conn, sql_path):
    text = sql_path.read_text(encoding="utf-8")
    statements = [s.strip() for s in text.split(";") if s.strip()
                  and not s.strip().startswith("--")]
    with db_conn.cursor() as cur:
        for stmt in statements:
            try:
                cur.execute(stmt)
                cur.fetchall()
            except Exception as exc:
                pytest.fail(f"{sql_path.name}: {exc}\nSTATEMENT:\n{stmt}")
