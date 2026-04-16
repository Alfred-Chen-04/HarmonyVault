"""Provision the HarmonyVault database from scratch.

Runs every file under ``schema/`` in filename order, then calls the
Spotify ingest and synthetic-data generator. Idempotent: re-running the
script drops the existing database and rebuilds it.

Owner: Jacob Liebson (jel212) — data track.
"""

from __future__ import annotations

import sys
from pathlib import Path

import mysql.connector

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DB, SCHEMA_DIR  # noqa: E402


def run_sql_file(cursor, path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    # Split on DELIMITER // ... DELIMITER ; blocks for trigger bodies.
    statements = _split_statements(text)
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt:
            continue
        cursor.execute(stmt)


def _split_statements(text: str) -> list[str]:
    """Split a SQL script on `;` while respecting `DELIMITER //` blocks."""
    out: list[str] = []
    buf: list[str] = []
    delim = ";"
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.upper().startswith("DELIMITER "):
            if buf:
                out.append("\n".join(buf))
                buf = []
            delim = stripped.split()[1]
            continue
        buf.append(raw_line)
        if stripped.endswith(delim):
            body = "\n".join(buf)
            if delim != ";":
                body = body.rsplit(delim, 1)[0]
            out.append(body)
            buf = []
    if buf:
        out.append("\n".join(buf))
    return out


def main() -> int:
    # Connect without selecting a database so we can create it.
    bootstrap = mysql.connector.connect(
        host=DB.host, port=DB.port, user=DB.user, password=DB.password
    )
    try:
        with bootstrap.cursor() as cur:
            for sql_file in sorted(SCHEMA_DIR.glob("0*.sql")):
                print(f"[schema] running {sql_file.name}")
                run_sql_file(cur, sql_file)
        bootstrap.commit()
    finally:
        bootstrap.close()

    # Now that schema + constraints + triggers + indexes are in place,
    # load real and synthetic data. Import lazily so schema provisioning
    # works even when those modules are not yet implemented.
    try:
        from scripts import load_spotify, generate_synthetic
    except ImportError:
        print("[data] loader modules not yet implemented; skipping data load")
        return 0

    load_spotify.main()
    generate_synthetic.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
