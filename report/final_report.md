# HarmonyVault — Final Report

**Course**: CSDS 341 Introduction to Database Systems, Spring 2026
**Team**: Jacob Liebson (jel212), Sky Zhou (sxz903), Alfred Chen (qxc225)
**Report length target**: ≤ 15 pages (per spec)
**Submission**: single zip to Canvas, 2026-05-01 23:59

> Writing guidance for the team: every section below corresponds to a rubric item in the project specification. Keep each section tight; do not exceed the 15-page cap. Screenshots, query outputs, and the ER diagram go in `report/assets/` and are embedded here by reference. Section owners are listed in square brackets after each heading — they are responsible for the first draft; Alfred does the final integration pass.

---

## 1. Application Background  *[Alfred]*

*Rubric §b.* Motivation, problem statement, existing solutions, and comparison to HarmonyVault.

### 1.1 The problem

Musicians accumulate short audio clips — half-finished melodies, chord progressions, drum loops, vocal takes — dozens per week for an active writer. Once the clips leave the DAW they live as opaque files on disk: `Voice Memo 2024-03-08 1.m4a`, `project_v12_bounce_final_FINAL.wav`, and so on. The metadata that *matters* musically (key, tempo, mode, time signature, mood, and which project the idea belongs to) is not written down anywhere the filesystem can search. Six months later, when the musician needs "that minor-key 72 BPM idea I had last spring," the ordinary filesystem is useless.

### 1.2 Why a relational database

The workload is exactly what relational systems are good at:

- **Data volume.** A single artist can produce thousands of clips per year. Real catalogs (e.g. the 232,000-track Kaggle Spotify dataset we use as seed data) easily exceed 10⁵ rows and require indexed retrieval.
- **Complex selection.** "All minor-key clips between 90 and 120 BPM tagged `cinematic` that appear in at least one shared project" is a natural multi-way join that a relational engine answers in milliseconds.
- **Integrity.** Foreign-key constraints and CHECK constraints keep the catalog self-consistent even when edited from multiple clients. A filesystem offers no such guarantees.
- **Collaboration.** Multiple users sharing a project need transactional semantics that filesystem sync cannot supply.

### 1.3 Existing solutions and how HarmonyVault differs

The TA's proposal feedback (item 2) asked us to compare HarmonyVault with existing tools. Four are directly adjacent:

| Tool | What it offers | What it lacks relative to HarmonyVault |
| --- | --- | --- |
| **Splice** (<https://splice.com>) | Cloud loop marketplace with key/BPM search and DAW integration | User does not own the catalog; cannot store or share private clips; no relational access for custom queries |
| **Loopcloud** (<https://www.loopcloud.com>) | Local caching client over a vendor loop library | Same vendor-lock-in problem as Splice; no project / collaboration model for the user's own clips |
| **Ableton Live Browser**, **Native Instruments Maschine** | In-DAW organization of samples, with tagging and preview | Tied to one workstation and one DAW; cannot be queried from outside the host application; no shareable project model |
| **iTunes / Apple Music library** | Indexed library with playlists | Built around finished tracks, not raw musical ideas; no per-clip musical attributes, no versioning, no collaboration |

HarmonyVault differs on four axes: (a) the user owns the catalog and its schema; (b) every attribute is queryable through standard SQL rather than a vendor UI; (c) the data model is relational end-to-end, so admin-style aggregate queries and cross-user analytics are possible; and (d) projects are first-class and can be shared through the `ProjectCollaborators` relation, which none of the four tools above support for a user's personal library.

## 2. What HarmonyVault Is Used For  *[Alfred]*

*Rubric §c.* Use cases that cover the platform's functionality, including the collaboration and administrative scenarios the TA's proposal feedback (item 3) asked us to add.

### 2.1 Personal-catalog use cases

- **U1. Capture an idea.** A user records a 30-second clip, then creates a `Clips` row with `title`, `duration`, and `filepath`, plus a matching `MusicalAttributes` row with the detected key, mode, tempo, and time signature.
- **U2. Tag an idea.** The user applies one or more free-form tags (`lofi`, `cinematic`, `aggressive`) through the `Tags` / `ClipTags` relations. Tag vocabulary is per-user, enforced by `UNIQUE(userID, tagName)`.
- **U3. Assemble a project.** The user creates a `Projects` row with a name and description, then adds clips through `ProjectClips`. A trigger (`schema/03_triggers.sql`) prevents adding a clip that the user does not own and is not a collaborator on.
- **U4. Version a clip.** When the user revises a clip, a new row is inserted into `ClipVersions` with an auto-assigned sequential `versionNumber`. The clip's canonical `filepath` stays on the original `Clips` row for backwards compatibility with references elsewhere.
- **U5. Search by musical criteria.** The user queries clips by key, mode, tempo range, and tag simultaneously — the kind of filter that a filesystem cannot answer. Realized by the Java CLI as `clips search --key C --mode minor --tempo-min 90 --tempo-max 120 --tag cinematic`.

### 2.2 Collaboration use cases (added per TA feedback)

- **U6. Invite a collaborator.** A project owner inserts a row into `ProjectCollaborators` with `role='editor'` or `'viewer'`. The project's owner is already registered as a collaborator via an insert trigger on `Projects`, so the list view includes them by default.
- **U7. Collaborator adds a clip.** An `editor` on project P who owns clip C can add C to P. The project-clip access-control trigger verifies the clip's owner is either P's owner or a listed collaborator; otherwise the insert is rejected with `SQLSTATE 45000`.
- **U8. Viewer-only access.** A `viewer` collaborator can list and play project clips but cannot insert into `ProjectClips`. This is enforced at the application layer because the role check requires session context the DBMS does not have.

### 2.3 Administrative use cases (added per TA feedback)

- **U9. Top tags across the catalog.** An admin aggregates across all users to find the most-used tags — `SELECT tagName, COUNT(*) FROM ClipTags JOIN Tags USING (tagID) GROUP BY tagName ORDER BY 2 DESC`. This is impossible in any of the four competing tools in §1.3.
- **U10. Most prolific collaborators.** `SELECT userID, COUNT(DISTINCT projectID) FROM ProjectCollaborators GROUP BY userID ORDER BY 2 DESC LIMIT 10`. Demonstrates cross-user reporting that requires a shared relational store.
- **U11. Musical-attribute distribution.** An admin computes the tempo histogram or the key-mode cross-tab over every clip, useful for seeding recommendations or debugging data-generation bias. Implemented as M3 in [queries/medium.sql](../queries/medium.sql).

## 3. Data Description and Constraints  *[Alfred]*

*Rubric §e.* The full constraint catalog is in [docs/integrity_constraints.md](../docs/integrity_constraints.md); this section summarizes it at the level a reader of the report needs.

HarmonyVault enforces integrity on four layers: entity integrity (primary keys on every relation), referential integrity (11 foreign keys with explicit `ON DELETE` / `ON UPDATE` actions, documented in [docs/integrity_constraints.md §2](../docs/integrity_constraints.md)), domain constraints (CHECKs on `email` shape, `duration > 0`, `mode ∈ {major, minor}`, `0 < tempo < 400`, the 17-value pitch-class set, `role ∈ {owner, editor, viewer}`, and `versionNumber ≥ 1`), and uniqueness (`Users.username`, `Users.email`, `Projects(ownerUserID, name)`, `Tags(userID, tagName)`, `ClipVersions(clipID, versionNumber)`).

Four semantic rules cannot be expressed declaratively and are enforced by triggers in [schema/03_triggers.sql](../schema/03_triggers.sql): (1) every project owner is auto-inserted into `ProjectCollaborators` so "list collaborators" always includes them; (2) a clip can only be added to a project if its owner is the project owner or a listed collaborator; (3) `ClipVersions.versionNumber` is auto-assigned to `MAX(existing) + 1` on null/zero input; (4) `versionNumber` is immutable once set.

## 4. ER Diagram  *[Alfred]*

*Rubric §d.* Embed [docs/ER_diagram.png](../docs/ER_diagram.png). The caption should note the three fixes made in response to the TA's proposal feedback (item 4):

1. **No foreign-key attributes inside entity boxes.** The proposal had `userID` inside `Clips`, `Tags`, and `Projects`, and `clipID` inside `MusicalAttributes`. All removed; the relationship diamonds express those links.
2. **Relationship attributes on the diamond, not on the entity.** `role` and `addedAt` hang off the `Collaborates` diamond, not off `Project` or `User`.
3. **Weak entities drawn with double borders.** `MusicalAttributes` and `ClipVersion` are weak entities of `Clip`; their identifying relationships (`Has`, `HasVersion`) use double-lined diamonds.

The entity / relationship content is enumerated in [docs/ER_diagram.md](../docs/ER_diagram.md).

## 5. Functional Dependencies  *[Alfred]*

*Rubric §g.* Full FD set and minimal covers are in [docs/functional_dependencies.md](../docs/functional_dependencies.md). In the report body, reproduce the "Summary of candidate keys" table from that document and call out the four relations with more than one candidate key: `Users` (three), `Projects` (two), `Tags` (two), `ClipVersions` (two).

## 6. Schema in 3NF / BCNF  *[Alfred]*

*Rubric §h.* Copy the nine `CREATE TABLE` statements from [schema/01_create_tables.sql](../schema/01_create_tables.sql), then reproduce the BCNF proof from [docs/normalization.md](../docs/normalization.md). Every relation is in BCNF (strictly stronger than 3NF) because every non-trivial FD has a candidate key on its left-hand side.

Explicitly address the TA's proposal-feedback item 5 by showing the **corrected intermediate relationship schemas** before the fold into entity tables:

- `Has(`**`clipID`**`, userID)` — many-to-one; PK is `{clipID}`, the "many" side.
- `Create(`**`projectID`**`, userID)` — many-to-one; PK is `{projectID}`.
- `To(`**`clipID`**`, attributeID)` — one-to-one; PK is a single side, `{clipID}`.

Each of these is then collapsed into the corresponding entity (`Clips.userID`, `Projects.ownerUserID`, `MusicalAttributes` keyed on `clipID`). The full derivation is in [docs/normalization.md §"Why the proposal's original relationship schemas were incorrect"](../docs/normalization.md).

## 7. Example Queries  *[Jacob]*

*Rubric §i.* Table of nine queries (E1–E3, M1–M3, H1–H3) with an English description for each (`queries/explanations.md`), then show **one** query — recommended: H1 — in all three of SQL, relational algebra, and tuple relational calculus, per [queries/ra_trc.md](../queries/ra_trc.md). Include screenshots of representative outputs from the running Java CLI.

The query list must explicitly include at least one query from each of the collaboration (U6–U8) and administrative (U9–U11) use-case groups.

## 8. Implementation  *[Sky for data volumes; Jacob for Java CLI]*

*Rubric §j.* OS targets: macOS and Linux. DBMS: MySQL 8.x. Data-generation language: Python 3.11 with pandas and Faker (emits nine CSVs). Command-line interface language: Java, using `mysql-connector-j` with `allowLoadLocalInfile=true` on the JDBC URL. Data flows as CSV files from this repo to the Java CLI's MySQL instance per the interchange contract in [docs/csv_format.md](../docs/csv_format.md).

Record final row counts produced by `scripts/setup_db.py`: expected **≥ 10,000** clips + matching `MusicalAttributes` rows from Spotify, plus ≥ 500 users, ≥ 80 projects, and the synthetic tag / collaborator / version rows. Include wall-clock timings for the generator and for the Java `LOAD DATA INFILE` ingest as the data-volume evidence.

Also briefly describe how the Java CLI wraps its bulk load in `SET FOREIGN_KEY_CHECKS = 0 … 1` to avoid row-by-row FK validation on the ingest path.

## 9. Integrity Constraints in Practice  *[Alfred]*

Reproduce [docs/integrity_constraints.md §5–§6](../docs/integrity_constraints.md): the four trigger-enforced rules and the application-layer validations, plus the rationale for splitting enforcement across CHECKs, triggers, and the application layer. Key tradeoff to highlight: CHECKs are declarative and evaluated by the DBMS on every row; triggers are necessary when the rule crosses tables (U7's project-clip access control is the canonical example); application-layer validation is used when the rule needs context (the authenticated user's role) that the DBMS does not have.

## 10. Per-Member Contributions  *[shared — Alfred integrates]*

*Rubric §k.* Copy the three "Standalone: yes" paragraphs from [docs/work_division.md](../docs/work_division.md) verbatim — one each for Alfred (schema + data-contract track), Sky (data track), and Jacob (application track, Java CLI in a separate repository). The archived Python CLI and Flask web UI are explicitly called out as a pre-pivot stretch goal, not as individual contributions.

## 11. What We Learned  *[one paragraph per member]*

*Rubric §l.* One paragraph per team member covering a concept not on the lecture slides:

- **Alfred**: Semantic constraints that cross tables (e.g. the project-clip access-control rule) cannot be expressed as CHECKs because MySQL CHECKs are single-row. Implementing them as triggers raises a secondary question — interaction with cascade deletes — that the lectures did not cover. Writing this out forced a clear split between what belongs in the schema, what belongs in a trigger, and what belongs at the application layer.
- **Sky**: Real-world data ingestion is dirtier than the course datasets. The Kaggle Spotify CSV mixes integer key codes (0–11) with string mode values ("major"/"minor") that sometimes arrive as booleans (0/1) depending on the file; normalizing both into our `CHECK` domains required more translation code than the lectures suggested was typical. Faker's `unique` decorators also deplete quickly at 500-user scale, which surfaced the difference between uniqueness enforcement in-memory vs. at the DBMS.
- **Jacob**: The same information need rendered in SQL, relational algebra, and tuple relational calculus is surprisingly un-mechanical — some SQL features (`GROUP BY`, `ORDER BY`, aggregate outputs) have no classical RA analogue. Picking which query to render in all three formalisms came down to choosing one that stays within selection / projection / join / rename, which is a constraint the lectures state but don't exercise at realistic sizes.

## 12. Conclusions  *[shared]*

Short section summarizing what works, the scale achieved, and what we would do differently with more time: full-text search on `Clips.title`, audio-similarity indexing via perceptual hashes, a proper web UI (the Flask prototype in [legacy_python/web/](../legacy_python/web/) is an archived starting point), cloud deployment with a managed MySQL instance.

---

## Appendix 1 — Installation Manual

Expanded version of [README.md](../README.md) with hand-holding for the TA. Covers the Docker-MySQL option, the Kaggle CSV download step, the Python `venv` creation, and the two-repo handoff (Alfred/Sky produce CSVs here → Jacob's Java CLI consumes them in its own repo).

## Appendix 2 — User Manual

Walk-through screenshots of Jacob's Java CLI:

1. Java CLI equivalent of `clips search --key C --mode minor --tempo-min 90 --tempo-max 120`.
2. Java CLI equivalent of `projects create --name "Album Draft" --user alfred`.
3. Java CLI's bulk-load command that ingests the nine CSV files in the FK-safe order.

## Appendix 3 — Programmer Manual

- **Module map** (this repo): [schema/](../schema/), [scripts/](../scripts/), [queries/](../queries/), [docs/](../docs/), [tests/](../tests/).
- **CSV interchange contract**: summarize [docs/csv_format.md](../docs/csv_format.md) — column order, null marker `\N`, line terminator `\n`, explicit AUTO_INCREMENT IDs, FK-safe load order.
- **Conventions**: every SQL file lives in [queries/](../queries/); every schema change updates [schema/01_create_tables.sql](../schema/01_create_tables.sql), the ER diagram, [docs/normalization.md](../docs/normalization.md), and (if column order changes) [docs/csv_format.md](../docs/csv_format.md) in the same commit.
- **Testing**: `pytest` runs the schema-presence check and the nine SQL smoke tests; the Java CLI has its own test suite in Jacob's repository.
