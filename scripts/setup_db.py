"""Provision or generate data for HarmonyVault.

Owner: Sky Zhou (sxz903) — data track.

Modes
-----
CSV mode (default — no DB credentials needed):
    Generates all nine CSVs under data/csv/. Jacob's Java CLI then loads
    them with LOAD DATA INFILE in the FK-safe order from docs/csv_format.md.

DB mode (--db):
    Applies the schema to a live MySQL instance, then loads data via one or
    both of the following sub-modes:

    --from-csv  Generate CSVs first, then INSERT IGNORE them into the DB.
                Default when neither sub-mode flag is given.
    --direct    Alias for --from-csv in this implementation; data always
                flows through CSV so Jacob's loader gets up-to-date files.

Usage
-----
    python scripts/setup_db.py                      # CSV only
    python scripts/setup_db.py --db                 # DB mode via CSV (default)
    python scripts/setup_db.py --db --from-csv      # explicit
    python scripts/setup_db.py --db --direct        # same as --from-csv here

Error policy
------------
Any failure aborts immediately. DB operations are wrapped in a transaction
and rolled back on error to leave the database in a clean state.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

def _exec_sql_file(cursor, path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for stmt in _split_statements(text):
        stmt = stmt.strip()
        if stmt:
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


def _apply_schema(conn, schema_dir: Path) -> None:
    sql_files = sorted(schema_dir.glob("0*.sql"))
    if not sql_files:
        raise FileNotFoundError(f"No schema files found in {schema_dir}")
    cur = conn.cursor()
    try:
        for sql_file in sql_files:
            print(f"  [schema] {sql_file.name}")
            try:
                _exec_sql_file(cur, sql_file)
            except Exception as e:
                raise RuntimeError(f"Failed executing {sql_file.name}: {e}") from e
        conn.commit()
        print("  [schema] done.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


# ---------------------------------------------------------------------------
# CSV mode
# ---------------------------------------------------------------------------

def run_csv_mode() -> int:
    print("📁 CSV mode — generating data files (no DB connection needed)...")
    try:
        from scripts import load_spotify, generate_synthetic
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 1

    print("  🎵 Generating Spotify data...")
    if load_spotify.main() != 0:
        return 1

    print("  🧪 Generating synthetic data...")
    if generate_synthetic.main() != 0:
        return 1

    print("✅ CSV generation complete → data/csv/")
    return 0


# ---------------------------------------------------------------------------
# DB mode
# ---------------------------------------------------------------------------

def run_db_mode() -> int:
    print("🗄️  DB mode — connecting to database...")
    try:
        import mysql.connector
        from config import DB, SCHEMA_DIR
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 1

    try:
        conn = mysql.connector.connect(
            host=DB.host, port=DB.port,
            user=DB.user, password=DB.password,
        )
    except mysql.connector.Error as e:
        print(f"❌ Cannot connect to database: {e}")
        return 1

    try:
        print("📐 Applying schema...")
        _apply_schema(conn, SCHEMA_DIR)
    except Exception as e:
        print(f"❌ Schema error (rolled back): {e}")
        conn.close()
        return 1

    # Generate CSVs first so Jacob's files are always up to date.
    print("📁 Generating CSVs...")
    if run_csv_mode() != 0:
        conn.close()
        return 1

    # Bulk-load CSVs into the DB.
    print("📥 Loading CSVs into database...")
    try:
        from scripts import load_csv_to_db
    except ImportError as e:
        print(f"❌ Import error: {e}")
        conn.close()
        return 1

    cur = conn.cursor()
    try:
        load_csv_to_db.main(cur)
        conn.commit()
        print("✅ Database provisioning complete.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Load error (rolled back): {e}")
        return 1
    finally:
        cur.close()
        conn.close()

    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--db",
        action="store_true",
        help="Connect to MySQL, apply schema, and load data.",
    )
    parser.add_argument(
        "--from-csv",
        dest="from_csv",
        action="store_true",
        help="(DB mode) Generate CSVs then bulk-load into the DB (default).",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="(DB mode) Alias for --from-csv; data always flows through CSV.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if not args.db:
        return run_csv_mode()
    return run_db_mode()


if __name__ == "__main__":
    raise SystemExit(main())
