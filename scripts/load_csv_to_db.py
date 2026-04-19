"""Bulk-load the nine data/csv/*.csv files into the live database.

Owner: Sky Zhou (sxz903).

Load order follows FK dependencies AND the trigger on ProjectClips (which
checks ProjectCollaborators), so project_collaborators is loaded before
project_clips even though the FK spec lists them in the opposite order.

Called by setup_db.py in --from-csv (DB) mode. The caller opens the
connection, passes a cursor, and commits after this function returns.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CSV_DIR  # noqa: E402


def _load_table(
    cur,
    csv_path: Path,
    table: str,
    columns: list[str],
    sort_key: tuple[str, ...] | None = None,
) -> int:
    if not csv_path.exists():
        print(f"  [load_csv] {csv_path.name} not found; skipping {table}")
        return 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if sort_key:
        rows.sort(key=lambda r: tuple(int(r[k]) for k in sort_key))

    tuples = [
        tuple(None if v == r"\N" else v for v in (row[c] for c in columns))
        for row in rows
    ]
    if not tuples:
        return 0

    placeholders = ",".join(["%s"] * len(columns))
    col_list = ",".join(columns)
    cur.executemany(
        f"INSERT IGNORE INTO {table} ({col_list}) VALUES ({placeholders})",
        tuples,
    )
    print(f"  [load_csv] {table:<30} {len(tuples):>7,} rows")
    return len(tuples)


def main(cur) -> None:
    """Load all nine tables. Caller must commit after this returns."""
    _load_table(cur, CSV_DIR / "users.csv", "Users",
                ["userID", "username", "email", "dateCreated"])

    _load_table(cur, CSV_DIR / "tags.csv", "Tags",
                ["tagID", "userID", "tagName"])

    _load_table(cur, CSV_DIR / "clips.csv", "Clips",
                ["clipID", "userID", "title", "duration", "filepath", "dateCreated"])

    _load_table(cur, CSV_DIR / "musical_attributes.csv", "MusicalAttributes",
                ["clipID", "musicalKey", "mode", "tempo", "timeSignature"])

    _load_table(cur, CSV_DIR / "projects.csv", "Projects",
                ["projectID", "ownerUserID", "name", "description", "dateCreated"])

    # Must precede project_clips: the ProjectClips BEFORE INSERT trigger
    # checks ProjectCollaborators to validate clip-owner access.
    _load_table(cur, CSV_DIR / "project_collaborators.csv", "ProjectCollaborators",
                ["projectID", "userID", "role", "addedAt"])

    _load_table(cur, CSV_DIR / "clip_tags.csv", "ClipTags",
                ["clipID", "tagID"])

    _load_table(cur, CSV_DIR / "project_clips.csv", "ProjectClips",
                ["projectID", "clipID"])

    # Sort by (clipID, versionNumber) so the sequential-number trigger
    # sees version 1 before version 2 for the same clip.
    _load_table(cur, CSV_DIR / "clip_versions.csv", "ClipVersions",
                ["versionID", "clipID", "versionNumber", "notes", "filepath", "dateCreated"],
                sort_key=("clipID", "versionNumber"))


if __name__ == "__main__":
    import mysql.connector
    from config import DB, SCHEMA_DIR  # noqa: E402
    from scripts.setup_db import _apply_schema  # noqa: E402

    conn = mysql.connector.connect(**{
        "host": DB.host, "port": DB.port,
        "user": DB.user, "password": DB.password,
    })
    try:
        with conn.cursor() as c:
            main(c)
        conn.commit()
        print("[load_csv] done.")
    finally:
        conn.close()
