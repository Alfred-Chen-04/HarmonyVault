# Work Division

Required by report §h and by the TA's proposal feedback item 4: "Each team member must complete an individual technical component of the project... proposal writing, presentation creation, and report writing are not considered technical work and should be handled collectively."

Every track below can be completed *without* waiting on another member's code, beyond the initial `CREATE TABLE` output from the schema track.

## Alfred Chen (qxc225) — Schema track

- Final ER diagram (no foreign-key attributes inside entity boxes, per TA feedback item 3).
- Relational schema: nine tables, 3NF/BCNF (`schema/01_create_tables.sql`).
- Functional-dependency derivation and minimal-cover computation (`docs/functional_dependencies.md`).
- 3NF/BCNF proof with lossless-join and dependency-preservation justification (`docs/normalization.md`).
- Integrity-constraint catalog: primary keys, foreign keys, CHECK, UNIQUE, triggers (`docs/integrity_constraints.md`, `schema/03_triggers.sql`).
- Index design for the query workload (`schema/04_indexes.sql`).
- Repository skeleton and `AGENTS.md` so every member starts from the same layout.

Standalone: yes. Needs only the spec, the TA feedback, and the proposal. Does not call or read any code written by Jacob or Sky.

## Jacob Liebson (jel212) — Data track

- `scripts/load_spotify.py`: parse the Kaggle "Ultimate Spotify Tracks" CSV into `Clips` (title, duration, synthetic filepath, `userID = 1` or a round-robin of generated users) and `MusicalAttributes` (key, mode, tempo, time-signature).
- `scripts/generate_synthetic.py`: use Faker to generate users, tags, projects, project collaborators, project-clip assignments, clip tags, and clip versions. Output volumes should target at least 500 users, 10,000 clips, 50 projects, 200 tags, and realistic density of collaborator / tag / project-clip rows.
- `scripts/setup_db.py`: orchestrator that drops the DB, runs every file in `schema/` in filename order, then runs the two loaders above.
- `scripts/reset_db.py`: thin wrapper that only re-runs `99_drop_all.sql` + `setup_db.py` when the developer wants to start over.
- Scalability measurement: record wall-clock ingest time and final row counts; include in report §7 ("implementation") as the data-volume evidence.

Standalone: yes. Depends on Alfred's `CREATE TABLE` output but not on Alfred's Python, and not on Sky's CLI or web code.

## Sky Zhou (sxz903) — Application track

- `cli/` click-based command-line interface with subcommands for clips, projects, tags, search, and admin queries.
- `cli/db.py`: connection helper that reads SQL files from `queries/` and parameterizes safely.
- `queries/easy.sql` (3 queries), `queries/medium.sql` (3 queries), `queries/hard.sql` (3 queries): nine canonical queries that exercise the schema.
- `queries/ra_trc.md`: each of the nine queries expressed in relational algebra where possible; at least one query rendered in SQL + RA + TRC as the spec requires.
- Stored procedures where appropriate (e.g. "add clip with tags atomically") registered during `setup_db.py`.
- Query performance notes to justify `schema/04_indexes.sql` in report §10 (revisiting the schema).

Standalone: yes. Depends on the populated database from Jacob but not on anyone's Python code beyond the shared `config.py`.

## Web UI (extra credit, shared)

Jacob builds the Flask routes and server-side glue (`web/routes/`); Sky builds the Jinja templates and the Bootstrap styling (`web/templates/`, `web/static/`). Alfred reviews every SQL statement that appears in a route to make sure it still goes through `queries/*.sql`. This deliverable is optional for a three-person team but targets the up-to-3% extra credit; it is explicitly labeled as joint work in report §h.

## Collective (not counted as individual technical work)

- Final report writing (`report/final_report.md`).
- Presentation slides (`presentation/slides.pdf`).
- Installation / user / programmer manuals (appendices 1-3 of the report).
- Test plan and screenshots for submission.

## How to present this in the report

Report §8 ("per-member contributions") should copy the three "Standalone: yes" bullets above verbatim, add a one-paragraph "what I learned" section per member (covered separately in `report/final_report.md`), and cite the extra credit web UI as a joint stretch goal.
