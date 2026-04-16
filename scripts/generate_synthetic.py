"""Generate synthetic users, tags, projects, collaborators, and versions.

Owner: Jacob Liebson (jel212). Uses Faker so the data looks realistic in
the demo and the report screenshots. Numbers are controlled by constants
at the top of this file.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import mysql.connector
from faker import Faker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DB  # noqa: E402

NUM_USERS = 500
NUM_TAGS_PER_USER = 5
NUM_PROJECTS = 80
CLIPS_PER_PROJECT = 12
COLLABORATORS_PER_PROJECT = 3
VERSIONS_PER_CLIP_MAX = 3
TAG_ASSIGNMENTS_PER_CLIP_MAX = 3


def main() -> int:
    fake = Faker()
    Faker.seed(42)
    random.seed(42)

    conn = mysql.connector.connect(**DB.to_connector_kwargs())
    try:
        with conn.cursor() as cur:
            # --- Users ---
            users: list[int] = []
            for _ in range(NUM_USERS):
                username = fake.unique.user_name()[:64]
                email = fake.unique.email()[:255]
                cur.execute(
                    "INSERT INTO Users (username, email) VALUES (%s, %s)",
                    (username, email),
                )
                users.append(cur.lastrowid)

            # --- Tags ---
            mood_words = [
                "chill", "dark", "bright", "melancholy", "energetic",
                "dreamy", "aggressive", "lofi", "cinematic", "groovy",
                "ambient", "dance", "sad", "hopeful", "raw",
            ]
            tag_pool: dict[int, list[int]] = {}
            for uid in users:
                picks = random.sample(mood_words, NUM_TAGS_PER_USER)
                tag_pool[uid] = []
                for name in picks:
                    cur.execute(
                        "INSERT IGNORE INTO Tags (userID, tagName) VALUES (%s, %s)",
                        (uid, name),
                    )
                    if cur.lastrowid:
                        tag_pool[uid].append(cur.lastrowid)

            # --- Reassign a subset of existing clips from system to real users ---
            cur.execute("SELECT clipID FROM Clips WHERE userID = 1")
            system_clip_ids = [row[0] for row in cur.fetchall()]
            for clip_id in system_clip_ids:
                cur.execute(
                    "UPDATE Clips SET userID = %s WHERE clipID = %s",
                    (random.choice(users), clip_id),
                )

            # --- Tag a sample of clips ---
            cur.execute("SELECT clipID, userID FROM Clips")
            for clip_id, owner in cur.fetchall():
                owner_tags = tag_pool.get(owner, [])
                if not owner_tags:
                    continue
                chosen = random.sample(
                    owner_tags,
                    k=min(len(owner_tags),
                          random.randint(0, TAG_ASSIGNMENTS_PER_CLIP_MAX)),
                )
                for tag_id in chosen:
                    cur.execute(
                        "INSERT IGNORE INTO ClipTags (clipID, tagID) "
                        "VALUES (%s, %s)",
                        (clip_id, tag_id),
                    )

            # --- Projects ---
            project_ids: list[int] = []
            project_owner_of: dict[int, int] = {}
            for _ in range(NUM_PROJECTS):
                owner = random.choice(users)
                name = fake.unique.catch_phrase()[:255]
                desc = fake.sentence(nb_words=12)
                cur.execute(
                    "INSERT INTO Projects (ownerUserID, name, description) "
                    "VALUES (%s, %s, %s)",
                    (owner, name, desc),
                )
                project_ids.append(cur.lastrowid)
                project_owner_of[cur.lastrowid] = owner

            # --- Collaborators (owner auto-added via trigger) ---
            for pid in project_ids:
                owner = project_owner_of[pid]
                candidates = [u for u in users if u != owner]
                collaborators = random.sample(
                    candidates, k=COLLABORATORS_PER_PROJECT
                )
                for uid in collaborators:
                    role = random.choice(["editor", "viewer"])
                    cur.execute(
                        "INSERT IGNORE INTO ProjectCollaborators "
                        "(projectID, userID, role) VALUES (%s, %s, %s)",
                        (pid, uid, role),
                    )

            # --- Project-Clip assignments (respect trigger access rule) ---
            for pid in project_ids:
                owner = project_owner_of[pid]
                cur.execute(
                    "SELECT userID FROM ProjectCollaborators WHERE projectID = %s",
                    (pid,),
                )
                allowed = {row[0] for row in cur.fetchall()} | {owner}
                placeholders = ",".join(["%s"] * len(allowed))
                cur.execute(
                    f"SELECT clipID FROM Clips WHERE userID IN ({placeholders}) "
                    f"ORDER BY RAND() LIMIT %s",
                    (*allowed, CLIPS_PER_PROJECT),
                )
                for (clip_id,) in cur.fetchall():
                    cur.execute(
                        "INSERT IGNORE INTO ProjectClips (projectID, clipID) "
                        "VALUES (%s, %s)",
                        (pid, clip_id),
                    )

            # --- Clip versions ---
            cur.execute("SELECT clipID, filepath FROM Clips ORDER BY RAND() "
                        "LIMIT 2000")
            for clip_id, filepath in cur.fetchall():
                extra = random.randint(0, VERSIONS_PER_CLIP_MAX)
                for _ in range(extra):
                    cur.execute(
                        "INSERT INTO ClipVersions "
                        "(clipID, versionNumber, notes, filepath) "
                        "VALUES (%s, 0, %s, %s)",
                        (clip_id, fake.sentence(nb_words=6),
                         f"{filepath}.v{random.randint(2, 9)}"),
                    )

        conn.commit()
        print("[synthetic] generated users, tags, projects, collaborators, versions")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
