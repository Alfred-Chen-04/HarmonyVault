# HarmonyVault

CSDS 341 final project (Spring 2026). A relational database for managing and discovering musical ideas.

**Team**: Jacob Liebson (jel212), Sky Zhou (sxz903), Alfred Chen (qxc225).

## What it does

Musicians keep accumulating short audio clips (melodies, chord progressions, rhythmic ideas). HarmonyVault stores each clip's metadata — title, duration, file path, musical key, mode, tempo, time signature — and lets the user tag clips, group them into projects, track version history, and share projects with collaborators. Audio capture and attribute detection are handled by external tools; HarmonyVault only stores and queries the metadata.

## Prerequisites

- Python 3.11 or newer
- MySQL 8.x server, reachable over TCP. A disposable container works:
  ```bash
  docker run -d --name hv-mysql -e MYSQL_ROOT_PASSWORD=dev -p 3306:3306 mysql:8
  ```
- The Kaggle "Ultimate Spotify Tracks" CSV placed at `data/SpotifyFeatures.csv`. Download it from <https://www.kaggle.com/datasets/zaheenhamidani/ultimate-spotify-tracks-db>.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # then edit DB credentials
```

## Initialize the database

```bash
python scripts/setup_db.py
```

This script (1) runs every file under `schema/` in order, (2) loads the Spotify CSV into `Clips` and `MusicalAttributes`, and (3) generates synthetic users, tags, projects, collaborators, and clip versions with Faker.

## Use the CLI

```bash
python -m cli --help
python -m cli clips search --key "C" --mode minor --tempo-min 90 --tempo-max 120
python -m cli projects create --name "Album Draft" --user alfred
python -m cli clips assign --clip-id 42 --project "Album Draft"
python -m cli admin top-tags --limit 10
```

## Use the web UI (optional)

```bash
flask --app web.app run
# open http://localhost:5000
```

## Run the tests

```bash
pytest
```

## Project layout

See `AGENTS.md` for the full directory map and the conventions every contributor follows.

## License

Coursework, not intended for redistribution.
