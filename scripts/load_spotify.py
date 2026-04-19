"""Parse the Kaggle Spotify Tracks CSV and write clips.csv + musical_attributes.csv.

Owner: Sky Zhou (sxz903).

If the Kaggle CSV is not present, generates FALLBACK_CLIPS synthetic clips so
that setup_db.py and generate_synthetic.py can run on a fresh checkout without
a Kaggle account. Download the real dataset from:
  https://www.kaggle.com/datasets/zaheenhamidani/ultimate-spotify-tracks-db
and place SpotifyFeatures.csv at data/SpotifyFeatures.csv (or set
SPOTIFY_CSV_PATH in .env) to use real data.
"""

from __future__ import annotations

import csv
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CSV_DIR, SPOTIFY_CSV_PATH, SPOTIFY_LOAD_LIMIT  # noqa: E402

FALLBACK_CLIPS = 500

KEY_INT_TO_NAME = {
    0: "C", 1: "C#", 2: "D",  3: "D#", 4: "E",  5: "F",
    6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B",
}


def _translate_mode(val) -> str:
    if isinstance(val, str):
        return val.lower()
    return "major" if int(val) == 1 else "minor"


def _translate_key(val) -> str:
    if isinstance(val, str):
        return val
    return KEY_INT_TO_NAME[int(val) % 12]


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clip_rows: list[dict] = []
    attr_rows: list[dict] = []

    if not SPOTIFY_CSV_PATH.exists():
        print(f"[spotify] CSV not found at {SPOTIFY_CSV_PATH}; "
              f"generating {FALLBACK_CLIPS} synthetic clips.")
        rng = random.Random(42)
        keys = list(KEY_INT_TO_NAME.values())
        for i in range(1, FALLBACK_CLIPS + 1):
            clip_rows.append({
                "clipID": i,
                "userID": 1,
                "title": f"Synthetic Clip {i}",
                "duration": round(rng.uniform(30.0, 300.0), 2),
                "filepath": f"spotify://synthetic-{i}",
                "dateCreated": now,
            })
            attr_rows.append({
                "clipID": i,
                "musicalKey": rng.choice(keys),
                "mode": rng.choice(["major", "minor"]),
                "tempo": round(rng.uniform(60.0, 180.0), 2),
                "timeSignature": "4/4",
            })
    else:
        try:
            import pandas as pd
            df = pd.read_csv(SPOTIFY_CSV_PATH,
                             nrows=SPOTIFY_LOAD_LIMIT or None)
            print(f"[spotify] loaded {len(df):,} rows from CSV")
            rows_iter = (row for _, row in df.iterrows())
        except ImportError:
            print("[spotify] pandas not available; using csv module")
            with open(SPOTIFY_CSV_PATH, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                raw = []
                for i, row in enumerate(reader):
                    if SPOTIFY_LOAD_LIMIT and i >= SPOTIFY_LOAD_LIMIT:
                        break
                    raw.append(row)
            print(f"[spotify] loaded {len(raw):,} rows from CSV")
            rows_iter = iter(raw)

        for i, row in enumerate(rows_iter, start=1):
            title = str(row.get("track_name") or "Untitled")[:255]
            duration_ms = float(row.get("duration_ms") or 0)
            duration_s = round(duration_ms / 1000.0, 2) if duration_ms > 0 else 1.0
            clip_rows.append({
                "clipID": i,
                "userID": 1,
                "title": title,
                "duration": duration_s,
                "filepath": f"spotify://{title[:200]}",
                "dateCreated": now,
            })
            try:
                m_key = _translate_key(row["key"])
                mode = _translate_mode(row["mode"])
                tempo = round(float(row["tempo"]), 2)
                tempo = min(max(tempo, 1.0), 399.99)
                ts = str(row.get("time_signature") or "4/4")
                if "/" not in ts:
                    ts = f"{ts}/4"
                attr_rows.append({
                    "clipID": i,
                    "musicalKey": m_key,
                    "mode": mode,
                    "tempo": tempo,
                    "timeSignature": ts[:8],
                })
            except (KeyError, ValueError, TypeError):
                pass

    clip_fields = ["clipID", "userID", "title", "duration", "filepath", "dateCreated"]
    attr_fields = ["clipID", "musicalKey", "mode", "tempo", "timeSignature"]
    _write_csv(CSV_DIR / "clips.csv", clip_fields, clip_rows)
    _write_csv(CSV_DIR / "musical_attributes.csv", attr_fields, attr_rows)
    print(f"[spotify] {len(clip_rows):,} clips          → {CSV_DIR}/clips.csv")
    print(f"[spotify] {len(attr_rows):,} attributes     → {CSV_DIR}/musical_attributes.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
