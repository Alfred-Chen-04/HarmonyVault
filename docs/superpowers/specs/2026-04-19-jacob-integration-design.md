# Jacob Integration Design — 2026-04-19

## Goal
Merge `Jacob's Work/` into `HarmonyVault/cli_java/` so the project ships as a single unified repository with 100% rubric coverage for the 4/22 demo and 5/1 final submission.

## Directory layout after merge

```
HarmonyVault/
  cli_java/
    src/
      DatabaseConfig.java    (change: read db.properties, fix JDBC URL)
      HarmonyVaultCLI.java   (change: remove hand-entered IDs, add benchmark menu, call stored proc)
      DataLoader.java        (NEW: LOAD DATA LOCAL INFILE × 9 tables)
    lib/
      mysql-connector-j-*.jar
    db.properties.example
    build.sh                 (NEW: javac + jar)
    README.md                (NEW)
  data/csv/         ← Sky's setup_db.py output (gitignored)
  data/csv_sample/  ← committed golden 10-row samples (unchanged)
  queries/          ← canonical SQL read by CLI at runtime (unchanged)
  schema/           ← Alfred's DDL (unchanged)
  scripts/          ← Sky's generators (unchanged)
```

Jacob's `*_import.csv` files are discarded; `data/csv/` from `setup_db.py` is the single authoritative data source.

## Rubric coverage

| § | Artifact | Status |
|---|---|---|
| a | `docs/ER_diagram.*` | ✅ exists |
| b | `docs/normalization.md`, `functional_dependencies.md` | ✅ exists |
| c | `schema/01_create_tables.sql`, triggers, indexes | ✅ exists |
| d | 9 queries easy/medium/hard; CLI "Benchmark queries" menu | needs menu |
| e | `cli_java/src/DataLoader.java` LOAD DATA LOCAL INFILE | NEW |
| f | `queries/ra_trc.md` SQL+RA+TRC | ✅ exists |
| g | `HarmonyVaultCLI.java` all basic ops | needs ID fix |
| h | stored procedure; CLI calls `sp_add_clip_version` | needs wiring |
| i | `docs/work_division.md` | needs small update |

## Changes to HarmonyVaultCLI.java (minimal)

1. `DatabaseConfig`: load `db.properties` instead of hardcoded password; add `allowLoadLocalInfile=true` to URL.
2. `createClip / createProject / createTag`: remove "Assign ID" prompts; use `Statement.RETURN_GENERATED_KEYS`.
3. Main menu: add option `9. Benchmark queries` — loads and runs E1–H3 from `queries/*.sql`.
4. `addNewVersion`: replace manual transaction with `CALL sp_add_clip_version(clipId, notes, filepath)`.

## New files

- `DataLoader.java`: loads 9 CSVs in FK-safe order using `LOAD DATA LOCAL INFILE`; called as standalone entrypoint or from CLI first-run check.
- `db.properties.example`: template with placeholder password.
- `build.sh`: `javac` + `jar` into `harmonyvault-cli.jar`.
- `cli_java/README.md`: build + run instructions, prerequisites.

## Stored procedure

Add to `queries/stored_procedures.sql`:

```sql
DELIMITER $$
CREATE PROCEDURE sp_add_clip_version(
    IN p_clipID INT, IN p_notes TEXT, IN p_filepath VARCHAR(512))
BEGIN
    DECLARE next_ver INT;
    SELECT COALESCE(MAX(versionNumber), 0) + 1 INTO next_ver
    FROM ClipVersions WHERE clipID = p_clipID;
    INSERT INTO ClipVersions (clipID, versionNumber, notes, filepath, dateCreated)
    VALUES (p_clipID, next_ver, p_notes, p_filepath, CURRENT_TIMESTAMP);
END$$
DELIMITER ;
```

## Constraints

- Minimal changes to Jacob's existing code.
- No new dependencies beyond `mysql-connector-j` already in use.
- Must pass `pytest` (schema + query smoke tests).
- Must demo cleanly on 4/22.
