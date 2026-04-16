"""Smoke test: every table declared in schema/01_create_tables.sql exists."""

from __future__ import annotations

EXPECTED = {
    "Users", "Clips", "MusicalAttributes", "Projects", "Tags",
    "ClipTags", "ProjectClips", "ProjectCollaborators", "ClipVersions",
}


def test_tables_exist(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("SHOW TABLES")
        present = {row[0] for row in cur.fetchall()}
    missing = EXPECTED - present
    assert not missing, f"missing tables: {missing}"
