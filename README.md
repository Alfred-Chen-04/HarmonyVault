# HarmonyVault

CSDS 341 final project (Spring 2026). A relational database for managing and discovering musical ideas.

**Team**: Jacob Liebson (jel212), Sky Zhou (sxz903), Alfred Chen (qxc225).

## What it does

Musicians keep accumulating short audio clips (melodies, chord progressions, rhythmic ideas). HarmonyVault stores each clip's metadata — title, duration, file path, musical key, mode, tempo, time signature — and lets the user tag clips, group them into projects, track version history, and share projects with collaborators. Audio capture and attribute detection are handled by external tools; HarmonyVault only stores and queries the metadata.

## Repository scope (post-pivot, 2026-04-17)

The project is split across two repositories:

| Component | Repository | Owner |
| --- | --- | --- |
| Schema, docs, data generation, canonical queries | **this repo** | Alfred (schema + docs), Sky (data) |
| Command-line interface | Jacob's separate Java repository | Jacob |

The command-line interface is written in **Java** and lives in Jacob's separate repository. The obsolete Python CLI and Flask web UI are archived under [legacy_python/](legacy_python/) for reference. See [docs/work_division.md](docs/work_division.md) for the full per-member breakdown.

Data flows from this repo to Jacob's Java CLI through **one CSV file per table**. The interchange contract is defined in [docs/csv_format.md](docs/csv_format.md).

## Prerequisites

- Python 3.11 or newer (for the data-generation scripts only)
- MySQL 8.x server, reachable over TCP (used by the Java CLI, and optionally by the tests here). A disposable container works:
  ```bash
  docker run -d --name hv-mysql -e MYSQL_ROOT_PASSWORD=dev -p 3306:3306 mysql:8
  ```
- The Kaggle "Ultimate Spotify Tracks" CSV placed at `data/SpotifyFeatures.csv`. Download from <https://www.kaggle.com/datasets/zaheenhamidani/ultimate-spotify-tracks-db>.

## Install (Python side)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # then edit DB credentials if running the tests
```

## Generate the CSV dataset

```bash
python scripts/setup_db.py
```

This runs the two CSV generators in order:

1. [scripts/load_spotify.py](scripts/load_spotify.py) — emits `data/csv/clips.csv` and `data/csv/musical_attributes.csv` from the Kaggle Spotify CSV.
2. [scripts/generate_synthetic.py](scripts/generate_synthetic.py) — emits the remaining seven CSV files (users, tags, projects, clip-tags, project-clips, project-collaborators, clip-versions) with Faker.

The nine output files follow the column order and encoding rules in [docs/csv_format.md](docs/csv_format.md). Jacob's Java CLI consumes them with `LOAD DATA LOCAL INFILE` in the FK-safe order listed in that spec.

A committed set of golden samples (≤ 10 rows per file) lives under `data/csv_sample/` for development against a realistic, FK-consistent dataset before the full generator runs.

## Run the tests

```bash
pytest
```

The test suite in this repo covers schema and query regressions:

- [tests/test_schema_loads.py](tests/test_schema_loads.py) — confirms all nine tables from [schema/01_create_tables.sql](schema/01_create_tables.sql) exist after load.
- [tests/test_queries_run.py](tests/test_queries_run.py) — confirms every `queries/*.sql` file parses and executes without error.

Both tests skip automatically if MySQL is not reachable, so `pytest` still passes in a syntax-only check environment.

## Project layout

| Path | Purpose |
| --- | --- |
| [schema/](schema/) | DDL: `CREATE TABLE`, triggers, indexes |
| [docs/](docs/) | ER diagram, FD derivation, normalization proof, integrity-constraint catalog, CSV interchange spec, work-division spec |
| [scripts/](scripts/) | Data ingest (Spotify CSV) and synthetic-data generation — both emit CSVs |
| [queries/](queries/) | Canonical SQL for every example query, plus RA/TRC equivalents |
| [tests/](tests/) | pytest smoke tests for schema and queries |
| [report/](report/) | Final report markdown plus screenshot assets |
| [presentation/](presentation/) | Slides for the in-class presentation |
| [legacy_python/](legacy_python/) | Archived pre-pivot Python CLI and Flask web UI |

See [AGENTS.md](AGENTS.md) for contributor conventions.

## License

Coursework, not intended for redistribution.
