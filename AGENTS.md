# HarmonyVault — Agent Guide

This file orients any AI coding agent (Claude Code, Cursor, etc.) working on the HarmonyVault repository. Keep it in sync with the real codebase as it evolves.

## 1. Project

HarmonyVault is the CSDS 341 (Spring 2026) final project for a team of three: Jacob Liebson (jel212), Sky Zhou (sxz903), and Alfred Chen (qxc225). It is a relational database backend for a music-idea management system. Musicians accumulate short audio recordings (melodies, chord progressions, rhythmic ideas) that are hard to organize in a file system. HarmonyVault stores the metadata (key, tempo, mode, time signature, tags, projects, versions, collaborators) of those clips and lets users query them; audio capture and attribute detection are assumed to be done by external tools.

The deliverables are a working MySQL database, a Python command-line interface, an optional local Flask web UI, a written report, and an in-class presentation. The final submission is due on Canvas on 2026-05-01.

## 2. Tech stack

- Database: MySQL 8.x
- Language: Python 3.11+
- CLI framework: click
- Web framework: Flask + Jinja + Bootstrap (served locally)
- DB driver: mysql-connector-python
- Data tools: pandas (Spotify CSV ingest), Faker (synthetic data)
- Test framework: pytest
- OS targets: macOS and Linux

## 3. Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit DB credentials
python scripts/setup_db.py    # creates schema, loads Spotify data, generates synthetic rows
```

A MySQL 8 server must be reachable at the host/port defined in `.env`. A quick option is Docker:

```bash
docker run -d --name hv-mysql -e MYSQL_ROOT_PASSWORD=dev -p 3306:3306 mysql:8
```

## 4. Run

- CLI entry point: `python -m cli --help`
- Web server: `flask --app web.app run` (defaults to http://localhost:5000)
- Tests: `pytest`
- Reset database: `python scripts/reset_db.py`

## 5. Directory map

| Path | Owner | Purpose |
| --- | --- | --- |
| `AGENTS.md` | Alfred | This file |
| `README.md` | Alfred | User-facing install + run instructions |
| `schema/` | Alfred | DDL: `CREATE TABLE`, constraints, triggers, indexes |
| `docs/` | Alfred | ER diagram, functional dependencies, normalization proof, integrity constraint catalog, work-division spec |
| `scripts/` | Jacob | Data ingest (Spotify CSV) and synthetic data generation |
| `cli/` | Sky | click-based command-line interface |
| `queries/` | Sky | Canonical SQL for every example query, plus RA/TRC equivalents |
| `web/` | Jacob + Sky | Local Flask UI (extra credit) |
| `data/` | Jacob | Downloaded CSVs (gitignored) |
| `tests/` | shared | pytest smoke tests for schema, queries, CLI |
| `report/` | shared | Final report markdown plus screenshot assets |
| `presentation/` | shared | Slides for the in-class presentation |

## 6. Schema quick reference

Nine relations. `PK` = primary key, `FK` = foreign key. See `schema/01_create_tables.sql` for the authoritative DDL and `docs/normalization.md` for the 3NF/BCNF proof.

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

- SQL keywords in UPPERCASE; identifiers in `snake_case_or_camelCase` (match what is already in `schema/`).
- Never commit `data/*.csv`, `.env`, or `.venv/`. `.gitignore` enforces this.
- All user-facing SQL belongs in `queries/*.sql`. CLI commands and web routes read these files through `cli/db.py` helpers. No inline SQL in Python.
- Any change that touches the schema must update three things in the same commit: `schema/01_create_tables.sql`, `docs/ER_diagram.drawio` (and re-export `.png`), and `docs/normalization.md`.
- All report prose, code comments, identifiers, and UI copy must be in English. Internal team chat can be bilingual.
- Commit messages reference the rubric section they serve when relevant (e.g. "report §5 — add BCNF proof for ClipVersions").

## 8. How Claude Code should help

- When asked to add a query: place the SQL in the right file under `queries/`, wire a CLI subcommand or Flask route that calls it through `db.py`, and add a smoke test in `tests/test_queries_run.py`.
- When asked to change the schema: update `schema/01_create_tables.sql`, regenerate the ER diagram in `docs/`, refresh the FD and normalization docs, and bump the relevant section in `report/final_report.md`.
- When asked about the rubric: the spec is `Spring2026_Final_Project_Specification-Design-Implementation.pdf` in the parent directory; the TA's proposal feedback is in `Proposal Feedback.docx` in the same location. Both are authoritative.
- When unsure which teammate owns an area: check `docs/work_division.md`. Do not reassign work without prompting Alfred.
- Before the 2026-04-22 TA demo, every change must keep `pytest` green and `python -m cli --help` working end-to-end.
