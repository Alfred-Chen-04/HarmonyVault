"""Generate synthetic users, tags, projects, collaborators, and versions.

Owner: Sky Zhou (sxz903).

Reads the clips.csv produced by load_spotify.py, reassigns clip ownership to
synthetic users, then emits the remaining seven CSVs into data/csv/. All IDs
are assigned explicitly so downstream FK references stay consistent.

Run after load_spotify.py (setup_db.py orchestrates both).
"""

from __future__ import annotations

import csv
import random
import sys
from datetime import datetime
from pathlib import Path

from faker import Faker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CSV_DIR  # noqa: E402

NUM_USERS = 500
NUM_TAGS_PER_USER = 5
NUM_PROJECTS = 80
CLIPS_PER_PROJECT = 12
COLLABORATORS_PER_PROJECT = 3
VERSIONS_PER_CLIP_MAX = 3
TAG_ASSIGNMENTS_PER_CLIP_MAX = 3

MOOD_WORDS = [
    "chill", "dark", "bright", "melancholy", "energetic",
    "dreamy", "aggressive", "lofi", "cinematic", "groovy",
    "ambient", "dance", "sad", "hopeful", "raw",
]


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    fake = Faker()
    Faker.seed(42)
    rng = random.Random(42)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    CSV_DIR.mkdir(parents=True, exist_ok=True)

    # --- Read clips.csv written by load_spotify ---
    clips_csv = CSV_DIR / "clips.csv"
    if not clips_csv.exists():
        print("[synthetic] clips.csv not found — run load_spotify.py first")
        return 1
    with open(clips_csv, newline="", encoding="utf-8") as f:
        raw_clips = list(csv.DictReader(f))
    print(f"[synthetic] read {len(raw_clips):,} clips from {clips_csv}")

    # --- Users (IDs 2..NUM_USERS+1; ID 1 = system user, created by schema SQL) ---
    user_rows: list[dict] = []
    user_ids: list[int] = []
    for i in range(NUM_USERS):
        uid = i + 2
        user_rows.append({
            "userID": uid,
            "username": fake.unique.user_name()[:64],
            "email": fake.unique.email()[:255],
            "dateCreated": now,
        })
        user_ids.append(uid)

    # --- Tags ---
    tag_rows: list[dict] = []
    tag_id = 1
    user_tag_pool: dict[int, list[int]] = {}
    for uid in user_ids:
        picks = rng.sample(MOOD_WORDS, NUM_TAGS_PER_USER)
        user_tag_pool[uid] = []
        for name in picks:
            tag_rows.append({"tagID": tag_id, "userID": uid, "tagName": name})
            user_tag_pool[uid].append(tag_id)
            tag_id += 1

    # --- Reassign clip ownership from system user (1) to real users ---
    clip_owner_of: dict[int, int] = {}
    for r in raw_clips:
        cid = int(r["clipID"])
        new_uid = rng.choice(user_ids)
        r["userID"] = new_uid
        clip_owner_of[cid] = new_uid
    clip_fields = ["clipID", "userID", "title", "duration", "filepath", "dateCreated"]
    _write_csv(clips_csv, clip_fields, raw_clips)

    # --- ClipTags ---
    clip_tag_rows: list[dict] = []
    seen_ct: set[tuple[int, int]] = set()
    for r in raw_clips:
        cid = int(r["clipID"])
        owner_tags = user_tag_pool.get(clip_owner_of[cid], [])
        if not owner_tags:
            continue
        k = rng.randint(0, min(len(owner_tags), TAG_ASSIGNMENTS_PER_CLIP_MAX))
        for tid in rng.sample(owner_tags, k):
            if (cid, tid) not in seen_ct:
                clip_tag_rows.append({"clipID": cid, "tagID": tid})
                seen_ct.add((cid, tid))

    # --- Projects ---
    project_rows: list[dict] = []
    project_ids: list[int] = []
    project_owner_of: dict[int, int] = {}
    for pid in range(1, NUM_PROJECTS + 1):
        owner = rng.choice(user_ids)
        project_rows.append({
            "projectID": pid,
            "ownerUserID": owner,
            "name": fake.unique.catch_phrase()[:255],
            "description": fake.sentence(nb_words=12),
            "dateCreated": now,
        })
        project_ids.append(pid)
        project_owner_of[pid] = owner

    # --- ProjectCollaborators (owner listed explicitly with role='owner') ---
    collab_rows: list[dict] = []
    project_allowed: dict[int, set[int]] = {}
    seen_collab: set[tuple[int, int]] = set()
    for pid in project_ids:
        owner = project_owner_of[pid]
        project_allowed[pid] = {owner}
        collab_rows.append({
            "projectID": pid, "userID": owner,
            "role": "owner", "addedAt": now,
        })
        seen_collab.add((pid, owner))
        candidates = [u for u in user_ids if u != owner]
        for uid in rng.sample(candidates, min(len(candidates), COLLABORATORS_PER_PROJECT)):
            if (pid, uid) not in seen_collab:
                collab_rows.append({
                    "projectID": pid, "userID": uid,
                    "role": rng.choice(["editor", "viewer"]),
                    "addedAt": now,
                })
                project_allowed[pid].add(uid)
                seen_collab.add((pid, uid))

    # --- ProjectClips (respects trigger: clip owner must be project collaborator) ---
    clip_by_owner: dict[int, list[int]] = {}
    for cid, uid in clip_owner_of.items():
        clip_by_owner.setdefault(uid, []).append(cid)

    pc_rows: list[dict] = []
    seen_pc: set[tuple[int, int]] = set()
    for pid in project_ids:
        eligible = []
        for uid in project_allowed[pid]:
            eligible.extend(clip_by_owner.get(uid, []))
        eligible = list(set(eligible))
        rng.shuffle(eligible)
        for cid in eligible[:CLIPS_PER_PROJECT]:
            if (pid, cid) not in seen_pc:
                pc_rows.append({"projectID": pid, "clipID": cid})
                seen_pc.add((pid, cid))

    # --- ClipVersions (versionNumber sequential per clipID starting at 1) ---
    ver_rows: list[dict] = []
    ver_id = 1
    sample = rng.sample(raw_clips, min(len(raw_clips), 2000))
    for r in sample:
        cid = int(r["clipID"])
        filepath = r["filepath"]
        for v in range(1, rng.randint(0, VERSIONS_PER_CLIP_MAX) + 1):
            ver_rows.append({
                "versionID": ver_id,
                "clipID": cid,
                "versionNumber": v,
                "notes": fake.sentence(nb_words=6),
                "filepath": f"{filepath}.v{v + 1}",
                "dateCreated": now,
            })
            ver_id += 1

    # --- Write all CSVs ---
    _write_csv(CSV_DIR / "users.csv",
               ["userID", "username", "email", "dateCreated"], user_rows)
    _write_csv(CSV_DIR / "tags.csv",
               ["tagID", "userID", "tagName"], tag_rows)
    _write_csv(CSV_DIR / "projects.csv",
               ["projectID", "ownerUserID", "name", "description", "dateCreated"],
               project_rows)
    _write_csv(CSV_DIR / "clip_tags.csv",
               ["clipID", "tagID"], clip_tag_rows)
    _write_csv(CSV_DIR / "project_collaborators.csv",
               ["projectID", "userID", "role", "addedAt"], collab_rows)
    _write_csv(CSV_DIR / "project_clips.csv",
               ["projectID", "clipID"], pc_rows)
    _write_csv(CSV_DIR / "clip_versions.csv",
               ["versionID", "clipID", "versionNumber", "notes", "filepath", "dateCreated"],
               ver_rows)

    print(
        f"[synthetic] users={len(user_rows)}, tags={len(tag_rows)}, "
        f"projects={len(project_rows)}, clip_tags={len(clip_tag_rows)}, "
        f"project_clips={len(pc_rows)}, collaborators={len(collab_rows)}, "
        f"versions={len(ver_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
