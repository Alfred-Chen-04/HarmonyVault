"""Drop and rebuild the HarmonyVault database.

Owner: Sky Zhou (sxz903).
"""

from __future__ import annotations

import sys
from pathlib import Path

import mysql.connector

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DB, SCHEMA_DIR  # noqa: E402
from scripts.setup_db import main as setup_main  # noqa: E402


def main() -> int:
    drop_sql = (SCHEMA_DIR / "99_drop_all.sql").read_text(encoding="utf-8")
    conn = mysql.connector.connect(
        host=DB.host, port=DB.port, user=DB.user, password=DB.password
    )
    try:
        with conn.cursor() as cur:
            for stmt in drop_sql.split(";"):
                if stmt.strip():
                    cur.execute(stmt)
        conn.commit()
    finally:
        conn.close()
    return setup_main()


if __name__ == "__main__":
    raise SystemExit(main())
