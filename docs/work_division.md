# Work Division

Required by report §h and by the TA's proposal feedback item 4: *"Each team member must complete an individual technical component of the project... proposal writing, presentation creation, and report writing are not considered technical work and should be handled collectively."*

This version reflects the **2026-04-17 pivot**: Sky had already written a Java CLI in a separate repository, so the Python `cli/` and `web/` folders were archived to `legacy_python/`. The interchange between Alfred/Jacob (this repo) and Sky (Java repo) is now one CSV file per table, defined in [docs/csv_format.md](csv_format.md).

Every track below can be completed *without* waiting on another member's code, beyond the initial `CREATE TABLE` output from the schema track.

## Alfred Chen (qxc225) — Schema + data-contract track

- Final ER diagram with **no foreign-key attributes inside entity boxes** (per TA feedback item 3). Source in [docs/ER_diagram.drawio](ER_diagram.drawio); exported PNG in [docs/ER_diagram.png](ER_diagram.png).
- Relational schema: nine tables, every relation in BCNF (strictly stronger than 3NF) — [schema/01_create_tables.sql](../schema/01_create_tables.sql).
- Triggers and index design — [schema/03_triggers.sql](../schema/03_triggers.sql), [schema/04_indexes.sql](../schema/04_indexes.sql).
- Functional-dependency derivation with minimal-cover for every relation — [docs/functional_dependencies.md](functional_dependencies.md).
- BCNF proof with the corrected intermediate relationship schemas the TA asked for (many-to-one → PK from "many" side; 1-1 → PK from one side; followed by the collapse into entity tables) — [docs/normalization.md](normalization.md).
- Integrity-constraint catalog covering PKs, FKs, CHECKs, UNIQUEs, trigger-enforced rules, and application-layer validations — [docs/integrity_constraints.md](integrity_constraints.md).
- **CSV interchange specification** — [docs/csv_format.md](csv_format.md). This is the contract that unblocks Jacob's CSV generator and Sky's Java `LOAD DATA INFILE`.
- Repository coordination: post-pivot cleanup ([legacy_python/](../legacy_python/)), [README.md](../README.md), and [AGENTS.md](../AGENTS.md).

Standalone: yes. Depends on nothing except the spec and the TA feedback. Does not call or read any code written by Jacob or Sky.

## Jacob Liebson (jel212) — Data track

- [scripts/load_spotify.py](../scripts/load_spotify.py): parse the Kaggle "Ultimate Spotify Tracks" CSV and emit two CSV files — `data/csv/clips.csv` and `data/csv/musical_attributes.csv` — that match the column order in [docs/csv_format.md](csv_format.md). Kaggle integer keys are translated to pitch-class strings through the table in that same script.
- [scripts/generate_synthetic.py](../scripts/generate_synthetic.py): Faker-driven generator that emits the remaining seven CSVs (`users.csv`, `tags.csv`, `projects.csv`, `clip_tags.csv`, `project_clips.csv`, `project_collaborators.csv`, `clip_versions.csv`). Target volumes: ≥ 500 users, ≥ 10,000 clips (from Spotify), ≥ 80 projects, realistic density of collaborator, tag, and project-clip rows. All AUTO_INCREMENT IDs are assigned explicitly so that downstream CSVs can carry the FK values.
- [scripts/setup_db.py](../scripts/setup_db.py): orchestrator that runs the two generators above and leaves the nine CSV files ready in `data/csv/` for Sky's Java loader to consume.
- Golden-sample CSVs committed under `data/csv_sample/` (≤ 10 rows per file) so Sky can exercise his Java loader against FK-consistent data before the full dataset is generated.
- Scalability measurement: record wall-clock generation time and final row counts; supply the numbers to Alfred for report §7 (implementation) as the data-volume evidence.

Standalone: yes. Depends on Alfred's schema and CSV spec but not on any of Sky's Java code.

## Sky Zhou (sxz903) — Application track (Java, separate repository)

- Java command-line interface with subcommands for clips, projects, tags, search, and admin queries. Uses `mysql-connector-j` with `allowLoadLocalInfile=true` in the JDBC URL.
- `LOAD DATA LOCAL INFILE` ingestion of the nine CSV files produced by Jacob's generator, in the FK-safe order listed in [docs/csv_format.md](csv_format.md) — wrapped in `SET FOREIGN_KEY_CHECKS = 0 … 1` to avoid row-by-row FK validation overhead.
- [queries/easy.sql](../queries/easy.sql), [queries/medium.sql](../queries/medium.sql), [queries/hard.sql](../queries/hard.sql): nine canonical queries (E1–E3, M1–M3, H1–H3) that exercise the schema. SQL lives in this repo so Alfred and Jacob can regression-test it; the Java CLI reads these files at runtime.
- [queries/ra_trc.md](../queries/ra_trc.md): each of the nine queries expressed in relational algebra (where possible); at least one query rendered in all three of SQL, RA, and TRC as the spec requires.
- Stored procedures where appropriate (e.g. "add clip with tags atomically"). Registered once after the CSVs are loaded.
- Query-performance notes to justify [schema/04_indexes.sql](../schema/04_indexes.sql) in report §10 (revisiting the schema).

Standalone: yes. Depends on the CSV files from Jacob but not on anyone's Python code beyond the shared [config.py](../config.py).

## Collective (not counted as individual technical work)

- Final report writing ([report/final_report.md](../report/final_report.md)) — Alfred integrates.
- Presentation slides ([presentation/slides.pdf](../presentation/slides.pdf)).
- Installation / user / programmer manuals (appendices 1–3 of the report).
- Demo run-through and screenshots for submission.

## Archived tracks

- **Python click CLI** (`legacy_python/cli/`) — replaced by Sky's Java CLI.
- **Flask web UI** (`legacy_python/web/`) — deprioritized for the demo. Re-enabling it as a +3% extra-credit deliverable is reversible; see [legacy_python/README.md](../legacy_python/README.md).

## How to present this in the report

Report §9 (per-member contributions) should copy the three "Standalone: yes" paragraphs above verbatim, then add a one-paragraph "what I learned" block per member (see §10). The extra-credit web UI is cited as an archived stretch goal, not as an individual contribution.
