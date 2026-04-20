# HarmonyVault — Agent Guide

This file orients any AI coding agent (Claude Code, Cursor, etc.) working on the HarmonyVault repository. Keep it in sync with the real codebase as it evolves.

## 1. Project

HarmonyVault is the CSDS 341 (Spring 2026) final project for a team of three: Jacob Liebson (jel212), Sky Zhou (sxz903), and Alfred Chen (qxc225). It is a relational database backend for a music-idea management system. Musicians accumulate short audio recordings (melodies, chord progressions, rhythmic ideas) that are hard to organize in a file system. HarmonyVault stores the metadata (key, tempo, mode, time signature, tags, projects, versions, collaborators) of those clips and lets users query them; audio capture and attribute detection are assumed to be done by external tools.

The deliverable is split across two repositories after the 2026-04-17 pivot:

- **This repo** owns the MySQL schema, the data-generation scripts (which now emit one CSV per table), the canonical SQL queries, the ER / FD / normalization documents, and the written report.
- **`cli_java/`** (this repository) owns the command-line interface. The Java CLI reads the CSVs produced here and ingests them via `LOAD DATA LOCAL INFILE`.

The submission is due on Canvas on 2026-05-01. The TA demo is on 2026-04-22 at 11:00 AM.

## 2. Tech stack

- Database: MySQL 8.x
- Data-generation language: Python 3.11+
- Data tools: pandas (Spotify CSV ingest), Faker (synthetic data)
- CSV output format: UTF-8, `\N` as the NULL marker, RFC 4180 quoting — see [docs/csv_format.md](docs/csv_format.md)
- CLI language: Java (`cli_java/` in this repository; uses `mysql-connector-j` with `allowLoadLocalInfile=true`)
- Test framework: pytest (schema + query smoke tests only)
- OS targets: macOS and Linux

## 3. Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # optional; only needed for the pytest suite
python scripts/setup_db.py    # emits the nine CSV files into data/csv/
```

The Java CLI (separate repo) loads those CSVs into its own MySQL instance.

## 4. Run

- Regenerate the CSV dataset: `python scripts/setup_db.py`
- Tests: `pytest`
- Java CLI: `bash cli_java/build.sh` then `java -cp "cli_java/out:cli_java/lib/mysql-connector-j-*.jar" HarmonyVaultCLI`
- Load CSV data: `java -cp "cli_java/out:cli_java/lib/mysql-connector-j-*.jar" DataLoader`

## 5. Directory map

| Path | Owner | Purpose |
| --- | --- | --- |
| [AGENTS.md](AGENTS.md) | Alfred | This file |
| [README.md](README.md) | Alfred | User-facing install + run instructions |
| [schema/](schema/) | Alfred | DDL: `CREATE TABLE`, triggers, indexes |
| [docs/](docs/) | Alfred | ER diagram, FDs, normalization proof, integrity constraints, CSV interchange spec, work-division spec |
| [scripts/](scripts/) | Sky | CSV generation (Spotify + Faker) |
| [cli_java/](cli_java/) | Jacob | Java CLI source, DataLoader, SqlLoader, build script |
| [queries/](queries/) | Jacob | Canonical SQL for every example query, plus RA/TRC equivalents |
| [data/csv/](data/) | Sky | Generated CSVs (gitignored) |
| `data/csv_sample/` | Sky | Tiny FK-consistent sample CSVs for Jacob to develop against |
| [tests/](tests/) | shared | pytest schema + query smoke tests |
| [report/](report/) | shared | Final report markdown plus screenshot assets |
| [presentation/](presentation/) | shared | Slides for the in-class presentation |
| [legacy_python/](legacy_python/) | archived | Pre-pivot Python CLI and Flask web UI — do not modify |

## 6. Schema quick reference

Nine relations. `PK` = primary key, `FK` = foreign key. See [schema/01_create_tables.sql](schema/01_create_tables.sql) for the authoritative DDL and [docs/normalization.md](docs/normalization.md) for the BCNF proof.

```
Users(userID PK, username UNIQUE, email UNIQUE, dateCreated)
Clips(clipID PK, userID FK→Users, title, duration, filepath, dateCreated)
MusicalAttributes(clipID PK/FK→Clips, musicalKey, mode, tempo, timeSignature)
Projects(projectID PK, ownerUserID FK→Users, name, description, dateCreated)
Tags(tagID PK, userID FK→Users, tagName, UNIQUE(userID, tagName))
ClipTags(clipID FK→Clips, tagID FK→Tags, PK(clipID, tagID))
ProjectClips(projectID FK→Projects, clipID FK→Clips, PK(projectID, clipID))
ProjectCollaborators(projectID FK→Projects, userID FK→Users, role, addedAt, PK(projectID, userID))
ClipVersions(versionID PK, clipID FK→Clips, versionNumber, notes, filepath, dateCreated,
             UNIQUE(clipID, versionNumber))
```

## 7. Conventions

- SQL keywords in UPPERCASE; identifiers in `camelCase` (match what is already in [schema/](schema/)).
- Never commit `data/csv/*`, `.env`, or `.venv/`. `.gitignore` enforces this. `data/csv_sample/*` **is** committed so Jacob has something to develop against.
- CSV column order must match the `CREATE TABLE` column order exactly. Header row is the column list. The loader on Jacob's side uses `IGNORE 1 LINES`.
- All user-facing SQL belongs in [queries/](queries/) so that the Java CLI can load query text at runtime instead of embedding SQL strings.
- Any schema change must update three artifacts in the same commit: [schema/01_create_tables.sql](schema/01_create_tables.sql), [docs/ER_diagram.drawio](docs/ER_diagram.drawio) (re-export the `.png`), and [docs/normalization.md](docs/normalization.md). It may also require an update to [docs/csv_format.md](docs/csv_format.md) if it changes column order, types, or CHECKs.
- All report prose, code comments, identifiers, and UI copy must be in English. Internal team chat can be bilingual.
- Commit messages reference the rubric section they serve when relevant (e.g. "report §5 — add BCNF proof for ClipVersions").

## 8. How Claude Code should help

- When asked to add a query: place the SQL in the right file under [queries/](queries/) and add a smoke test in [tests/test_queries_run.py](tests/test_queries_run.py). The Java CLI side is owned by Jacob.
- When asked to change the schema: update [schema/01_create_tables.sql](schema/01_create_tables.sql), regenerate the ER diagram in [docs/](docs/), refresh the FD and normalization docs, update [docs/csv_format.md](docs/csv_format.md) if column order / types change, and bump the relevant section in [report/final_report.md](report/final_report.md).
- When asked about the rubric: the spec is `Spring2026_Final_Project_Specification-Design-Implementation.pdf` in the parent directory; the TA's proposal feedback is `Proposal Feedback.docx` in the same place. Both are authoritative.
- When unsure which teammate owns an area: check [docs/work_division.md](docs/work_division.md). Do not reassign work without prompting Alfred.
- Before the 2026-04-22 TA demo, every change must keep `pytest` green and must not break the CSV contract in [docs/csv_format.md](docs/csv_format.md) without a coordinated update on Jacob's Java side.
- Archived Python code lives in [legacy_python/](legacy_python/). Do not modify it unless explicitly asked to revive the web UI for extra credit.
