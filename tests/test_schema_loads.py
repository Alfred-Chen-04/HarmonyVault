"""Smoke tests: schema structure, constraints, and trigger existence."""

from __future__ import annotations

import pytest

EXPECTED_TABLES = {
    "Users", "Clips", "MusicalAttributes", "Projects", "Tags",
    "ClipTags", "ProjectClips", "ProjectCollaborators", "ClipVersions",
}

# (table, column) pairs that must exist
EXPECTED_COLUMNS = [
    ("Users",                "userID"),
    ("Users",                "username"),
    ("Users",                "email"),
    ("Users",                "dateCreated"),
    ("Clips",                "clipID"),
    ("Clips",                "userID"),
    ("Clips",                "title"),
    ("Clips",                "duration"),
    ("Clips",                "filepath"),
    ("Clips",                "dateCreated"),
    ("MusicalAttributes",    "clipID"),
    ("MusicalAttributes",    "musicalKey"),
    ("MusicalAttributes",    "mode"),
    ("MusicalAttributes",    "tempo"),
    ("MusicalAttributes",    "timeSignature"),
    ("Projects",             "projectID"),
    ("Projects",             "ownerUserID"),
    ("Projects",             "name"),
    ("Projects",             "description"),
    ("Projects",             "dateCreated"),
    ("Tags",                 "tagID"),
    ("Tags",                 "userID"),
    ("Tags",                 "tagName"),
    ("ClipTags",             "clipID"),
    ("ClipTags",             "tagID"),
    ("ProjectClips",         "projectID"),
    ("ProjectClips",         "clipID"),
    ("ProjectCollaborators", "projectID"),
    ("ProjectCollaborators", "userID"),
    ("ProjectCollaborators", "role"),
    ("ProjectCollaborators", "addedAt"),
    ("ClipVersions",         "versionID"),
    ("ClipVersions",         "clipID"),
    ("ClipVersions",         "versionNumber"),
    ("ClipVersions",         "notes"),
    ("ClipVersions",         "filepath"),
    ("ClipVersions",         "dateCreated"),
]

# Triggers that must be registered
EXPECTED_TRIGGERS = {
    "trg_projects_after_insert_owner_collab",
    "trg_project_clips_before_insert_access",
    "trg_clip_versions_before_insert_seq",
    "trg_clip_versions_before_update_immutable_number",
}


def test_tables_exist(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("SHOW TABLES")
        present = {row[0] for row in cur.fetchall()}
    missing = EXPECTED_TABLES - present
    assert not missing, f"missing tables: {missing}"


@pytest.mark.parametrize("table,col", EXPECTED_COLUMNS,
                         ids=lambda x: x if isinstance(x, str) else x)
def test_column_exists(db_conn, table, col):
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "  AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            (table, col),
        )
        (count,) = cur.fetchone()
    assert count == 1, f"{table}.{col} column missing"


def test_triggers_exist(db_conn):
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT TRIGGER_NAME FROM information_schema.TRIGGERS "
            "WHERE TRIGGER_SCHEMA = DATABASE()"
        )
        present = {row[0] for row in cur.fetchall()}
    missing = EXPECTED_TRIGGERS - present
    assert not missing, f"missing triggers: {missing}"


def test_users_unique_constraints(db_conn):
    """username and email must each have a UNIQUE key."""
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT COLUMN_NAME FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "  AND TABLE_NAME = 'Users' AND NON_UNIQUE = 0 "
            "  AND INDEX_NAME != 'PRIMARY'",
        )
        unique_cols = {row[0] for row in cur.fetchall()}
    assert "username" in unique_cols, "Users.username missing UNIQUE constraint"
    assert "email"    in unique_cols, "Users.email missing UNIQUE constraint"


def test_clips_duration_positive(db_conn):
    """Inserting a clip with duration ≤ 0 must be rejected."""
    with db_conn.cursor() as cur:
        # Ensure there is at least one user to reference.
        cur.execute("SELECT userID FROM Users LIMIT 1")
        row = cur.fetchone()
        if row is None:
            pytest.skip("No users in DB; skipping domain-constraint test")
        uid = row[0]
        with pytest.raises(Exception):
            cur.execute(
                "INSERT INTO Clips (userID, title, duration, filepath) "
                "VALUES (%s, 'bad', -1.0, '/tmp/x')",
                (uid,),
            )
    db_conn.rollback()


def test_musical_attributes_mode_check(db_conn):
    """Inserting an invalid mode must be rejected by CHECK constraint."""
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT clipID FROM Clips "
            "WHERE clipID NOT IN (SELECT clipID FROM MusicalAttributes) "
            "LIMIT 1"
        )
        row = cur.fetchone()
        if row is None:
            pytest.skip("No unattributed clip available")
        cid = row[0]
        with pytest.raises(Exception):
            cur.execute(
                "INSERT INTO MusicalAttributes "
                "(clipID, musicalKey, mode, tempo, timeSignature) "
                "VALUES (%s, 'C', 'lydian', 120.0, '4/4')",
                (cid,),
            )
    db_conn.rollback()


def test_owner_auto_inserted_as_collaborator(db_conn):
    """Creating a project must auto-insert the owner into ProjectCollaborators."""
    with db_conn.cursor() as cur:
        cur.execute("SELECT userID FROM Users ORDER BY RAND() LIMIT 1")
        row = cur.fetchone()
        if row is None:
            pytest.skip("No users in DB")
        uid = row[0]
        cur.execute(
            "INSERT INTO Projects (ownerUserID, name) VALUES (%s, %s)",
            (uid, f"__test_collab_{uid}__"),
        )
        pid = cur.lastrowid
        cur.execute(
            "SELECT role FROM ProjectCollaborators "
            "WHERE projectID = %s AND userID = %s",
            (pid, uid),
        )
        collab_row = cur.fetchone()
        # Clean up before asserting so we don't leave junk in the DB.
        cur.execute("DELETE FROM Projects WHERE projectID = %s", (pid,))
    db_conn.rollback()
    assert collab_row is not None, "Owner not auto-inserted into ProjectCollaborators"
    assert collab_row[0] == "owner", "Auto-inserted collaborator role is not 'owner'"
