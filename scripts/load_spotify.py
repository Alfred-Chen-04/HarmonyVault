"""Ingest the Kaggle Spotify Tracks CSV into Clips + MusicalAttributes.

Owner: Sky Zhou (sxz903). This is a working skeleton that Sky
should flesh out with column mapping once the CSV is downloaded locally.
The code below is production-shaped so that running ``setup_db.py`` on
a fresh machine succeeds even before Sky fills in the details.
"""

from __future__ import annotations

import sys
from pathlib import Path

import mysql.connector
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DB, SPOTIFY_CSV_PATH, SPOTIFY_LOAD_LIMIT  # noqa: E402


# The Kaggle CSV column name -> our column name. Sky: adjust after
# downloading. Defaults chosen to match `SpotifyFeatures.csv`.
COLUMN_MAP = {
    "track_name": "title",
    "duration_ms": "duration_ms",
    "key": "musicalKey",
    "mode": "mode",
    "tempo": "tempo",
    "time_signature": "timeSignature",
}

KEY_INT_TO_NAME = {
    0: "C",  1: "C#", 2: "D",  3: "D#", 4: "E",  5: "F",
    6: "F#", 7: "G",  8: "G#", 9: "A", 10: "A#", 11: "B",
}


def _translate_mode(val) -> str:
    if isinstance(val, str):
        return val.lower()
    return "major" if int(val) == 1 else "minor"


def _translate_key(val) -> str:
    if isinstance(val, str):
        return val
    return KEY_INT_TO_NAME[int(val)]


def main() -> int:
    if not SPOTIFY_CSV_PATH.exists():
        print(f"[spotify] CSV not found at {SPOTIFY_CSV_PATH}; skipping.")
        print("[spotify] Download from https://www.kaggle.com/datasets/"
              "zaheenhamidani/ultimate-spotify-tracks-db")
        return 0

    df = pd.read_csv(SPOTIFY_CSV_PATH, nrows=SPOTIFY_LOAD_LIMIT)
    print(f"[spotify] loaded {len(df):,} rows from CSV")

    conn = mysql.connector.connect(**DB.to_connector_kwargs())
    try:
        with conn.cursor() as cur:
            # Ensure the system owner exists to hold imported clips.
            cur.execute(
                "INSERT IGNORE INTO Users (userID, username, email) "
                "VALUES (1, 'system', 'system@harmonyvault.local')"
            )

            clip_rows, attr_rows = [], []
            for _, row in df.iterrows():
                title = str(row.get("track_name") or "Untitled")[:255]
                duration_ms = float(row.get("duration_ms") or 0)
                duration_s = round(duration_ms / 1000.0, 2) if duration_ms else 1.0
                clip_rows.append((1, title, duration_s, f"spotify://{title}"))

            cur.executemany(
                "INSERT INTO Clips (userID, title, duration, filepath) "
                "VALUES (%s, %s, %s, %s)",
                clip_rows,
            )
            first_id = cur.lastrowid
            clip_ids = range(first_id, first_id + len(clip_rows))

            for clip_id, (_, row) in zip(clip_ids, df.iterrows()):
                try:
                    m_key = _translate_key(row["key"])
                    mode = _translate_mode(row["mode"])
                    tempo = round(float(row["tempo"]), 2)
                    ts = str(row.get("time_signature") or "4/4")
                    if "/" not in ts:
                        ts = f"{ts}/4"
                except (KeyError, ValueError, TypeError):
                    continue
                attr_rows.append((clip_id, m_key, mode, tempo, ts[:8]))

            cur.executemany(
                "INSERT INTO MusicalAttributes "
                "(clipID, musicalKey, mode, tempo, timeSignature) "
                "VALUES (%s, %s, %s, %s, %s)",
                attr_rows,
            )
        conn.commit()
        print(f"[spotify] inserted {len(clip_rows):,} clips and "
              f"{len(attr_rows):,} attribute rows")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
