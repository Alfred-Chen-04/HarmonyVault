# CSV Interchange Format

**Owner**: Alfred Chen (qxc225). **Audience**: Sky (writes the CSVs) and Jacob (loads them into his Java CLI's MySQL instance).

This document specifies the CSV files that Sky's data-generation scripts must produce so that Jacob's Java CLI can load them with `LOAD DATA INFILE` (or a Java parser). The schema in [schema/01_create_tables.sql](../schema/01_create_tables.sql) is authoritative; this spec is derived from it. If the two ever disagree, the schema wins.

## Global rules

| Rule | Value |
| --- | --- |
| Output directory | `data/csv/` at repo root |
| Encoding | UTF-8, no BOM |
| Line terminator | `\n` (Unix LF) |
| Header row | Row 1 is column names in the order below. Loaders must skip it (`IGNORE 1 LINES`). |
| Field separator | `,` |
| Quoting | RFC 4180: quote a field with `"` iff it contains `,`, `"`, or a line break. Escape internal `"` as `""`. |
| Null marker | Literal `\N` (two chars: backslash + capital N). This is the MySQL `LOAD DATA INFILE` default. |
| Boolean-ish | Never. Use the enum strings required by the `CHECK` constraints (`'major'`/`'minor'`, `'owner'`/`'editor'`/`'viewer'`). |
| DATETIME format | `YYYY-MM-DD HH:MM:SS` (ISO 8601, space separator, no timezone) |
| DECIMAL format | Plain decimal, no thousands separators. Precision must fit the column (e.g., `duration` is `DECIMAL(8,2)`, so max `999999.99`). |
| AUTO_INCREMENT IDs | **Explicitly populated** by the generator. Do not leave them blank for MySQL to assign — downstream CSVs carry FK references to these exact IDs. Start from 1 in each table. |
| Row count guardrail | Each CSV should end with a trailing newline. No blank lines anywhere else. |

## Load order (FK-safe)

Loaders must ingest in this order because each file references IDs from earlier files:

1. `users.csv`
2. `tags.csv` *(FK → Users)*
3. `clips.csv` *(FK → Users)*
4. `musical_attributes.csv` *(FK → Clips, 1-to-1)*
5. `projects.csv` *(FK → Users)*
6. `clip_tags.csv` *(FK → Clips + Tags)*
7. `project_clips.csv` *(FK → Projects + Clips)*
8. `project_collaborators.csv` *(FK → Projects + Users)*
9. `clip_versions.csv` *(FK → Clips)*

Jacob's Java loader should also run `SET FOREIGN_KEY_CHECKS = 0;` before loading and `= 1;` after, since MySQL validates FKs row-by-row and a mid-load failure will leave the DB partially populated.

## Per-table spec

Column order below **must match** the CSV header exactly, which **must match** the `CREATE TABLE` column order in [schema/01_create_tables.sql](../schema/01_create_tables.sql).

### 1. `users.csv`
| # | Column | Type | Notes |
|---|---|---|---|
| 1 | `userID` | INT | Explicit, starts at 1. **Reserve `userID = 1` for the system/import user** (`username='system'`, `email='system@harmonyvault.local'`). |
| 2 | `username` | VARCHAR(64) | Unique. |
| 3 | `email` | VARCHAR(255) | Unique. Must satisfy `LIKE '%_@_%._%'`. |
| 4 | `dateCreated` | DATETIME | ISO 8601. |

### 2. `tags.csv`
| # | Column | Type | Notes |
|---|---|---|---|
| 1 | `tagID` | INT | Explicit, starts at 1. |
| 2 | `userID` | INT | FK → `users.csv`. |
| 3 | `tagName` | VARCHAR(64) | Unique per `(userID, tagName)`. |

### 3. `clips.csv`
| # | Column | Type | Notes |
|---|---|---|---|
| 1 | `clipID` | INT | Explicit, starts at 1. |
| 2 | `userID` | INT | FK → `users.csv`. Spotify-imported clips can own `userID = 1` initially; reassign to real users before writing the CSV so no clip is left on the system user after generation finishes. |
| 3 | `title` | VARCHAR(255) |  |
| 4 | `duration` | DECIMAL(8,2) | Seconds, > 0. Convert `duration_ms / 1000` and round to 2 decimals. |
| 5 | `filepath` | VARCHAR(512) | For Spotify rows use `spotify://<title>`. |
| 6 | `dateCreated` | DATETIME | ISO 8601. |

### 4. `musical_attributes.csv`
One row per `clipID` (1-to-1 with Clips). `clipID` is both PK and FK.

| # | Column | Type | Notes |
|---|---|---|---|
| 1 | `clipID` | INT | FK + PK. |
| 2 | `musicalKey` | VARCHAR(3) | Must be one of `C, C#, Db, D, D#, Eb, E, F, F#, Gb, G, G#, Ab, A, A#, Bb, B`. Map Kaggle integer keys via the table in [scripts/load_spotify.py](../scripts/load_spotify.py). |
| 3 | `mode` | VARCHAR(8) | Exactly `major` or `minor` (lowercase). |
| 4 | `tempo` | DECIMAL(6,2) | `0 < tempo < 400`. |
| 5 | `timeSignature` | VARCHAR(8) | Default `4/4`; must contain a `/`. |

### 5. `projects.csv`
| # | Column | Type | Notes |
|---|---|---|---|
| 1 | `projectID` | INT | Explicit, starts at 1. |
| 2 | `ownerUserID` | INT | FK → `users.csv`. |
| 3 | `name` | VARCHAR(255) | Unique per `(ownerUserID, name)`. |
| 4 | `description` | TEXT | Nullable — use `\N` when empty. |
| 5 | `dateCreated` | DATETIME | ISO 8601. |

### 6. `clip_tags.csv`
| # | Column | Type | Notes |
|---|---|---|---|
| 1 | `clipID` | INT | FK → `clips.csv`. |
| 2 | `tagID` | INT | FK → `tags.csv`. |

Composite PK `(clipID, tagID)` — no duplicates.

### 7. `project_clips.csv`
| # | Column | Type | Notes |
|---|---|---|---|
| 1 | `projectID` | INT | FK → `projects.csv`. |
| 2 | `clipID` | INT | FK → `clips.csv`. |

Composite PK `(projectID, clipID)` — no duplicates. The generator should respect the trigger rule in [schema/03_triggers.sql](../schema/03_triggers.sql): a clip's `userID` must be the project's owner or a listed collaborator. If the rule is violated, Jacob's MySQL will reject the row.

### 8. `project_collaborators.csv`
| # | Column | Type | Notes |
|---|---|---|---|
| 1 | `projectID` | INT | FK → `projects.csv`. |
| 2 | `userID` | INT | FK → `users.csv`. |
| 3 | `role` | VARCHAR(16) | Exactly one of `owner`, `editor`, `viewer`. |
| 4 | `addedAt` | DATETIME | ISO 8601. |

Composite PK `(projectID, userID)`. The project's owner does **not** need to be listed here if the schema has a trigger that auto-inserts them; if you are unsure, include the owner with `role='owner'` explicitly — duplicates will be rejected cleanly via the PK.

### 9. `clip_versions.csv`
| # | Column | Type | Notes |
|---|---|---|---|
| 1 | `versionID` | INT | Explicit, starts at 1. |
| 2 | `clipID` | INT | FK → `clips.csv`. |
| 3 | `versionNumber` | INT | `>= 1`, unique per `clipID`. |
| 4 | `notes` | TEXT | Nullable — use `\N` when empty. |
| 5 | `filepath` | VARCHAR(512) |  |
| 6 | `dateCreated` | DATETIME | ISO 8601. |

## Reference `LOAD DATA INFILE` snippet for Jacob

```sql
SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS = 0;

LOAD DATA LOCAL INFILE 'data/csv/users.csv'
INTO TABLE Users
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(userID, username, email, dateCreated);

-- ... repeat in the load order listed above ...

SET FOREIGN_KEY_CHECKS = 1;
SET UNIQUE_CHECKS = 1;
```

(Java equivalent: `mysql-connector-j` supports `LOAD DATA LOCAL INFILE` when `allowLoadLocalInfile=true` is in the JDBC URL.)

## Golden samples

Sky should commit a tiny, hand-sized sample set under `data/csv_sample/` (≤10 rows per file) so Jacob can exercise his loader against real, FK-consistent data before the full generator is finished. Full-size generated outputs go into `data/csv/` (which is `.gitignore`d).

## Changelog

- 2026-04-17 — Alfred: initial spec after team pivot to Java CLI.
