# HarmonyVault CLI (Java)

Command-line interface for HarmonyVault. Owner: Jacob Liebson (jel212).

## Prerequisites

- Java 8+
- MySQL 8.x running locally with `local_infile = ON`
- `cli_java/lib/mysql-connector-j-9.x.jar` (not committed — download once, see below)

### Enable local_infile in MySQL (run once in MySQL CLI)

```sql
SET GLOBAL local_infile = 1;
```

### Download the connector jar (run once from repo root)

```bash
curl -L "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.3.0/mysql-connector-j-9.3.0.jar" \
     -o cli_java/lib/mysql-connector-j-9.3.0.jar
```

## One-time Setup (run from repo root)

```bash
# 1. Generate the 9 CSV files (Sky's pipeline)
source .venv/bin/activate
python scripts/setup_db.py

# 2. Apply the MySQL schema
mysql -u root -p < schema/01_create_tables.sql
mysql -u root -p < schema/02_constraints.sql
mysql -u root -p < schema/03_triggers.sql
mysql -u root -p < schema/04_indexes.sql
mysql -u root -p < queries/stored_procedures.sql

# 3. Configure credentials
cp cli_java/db.properties.example cli_java/db.properties
# Edit cli_java/db.properties — set db.password to your MySQL root password

# 4. Build
bash cli_java/build.sh

# 5. Load data into MySQL
java -cp "cli_java/out:cli_java/lib/mysql-connector-j-9.3.0.jar" DataLoader
```

## Run the interactive CLI

```bash
java -cp "cli_java/out:cli_java/lib/mysql-connector-j-9.3.0.jar" HarmonyVaultCLI
```

## Menu reference

| Option | Description |
|--------|-------------|
| 1 | Create a new clip (ID auto-assigned by DB) |
| 2 | Create a new project (ID auto-assigned by DB) |
| 3 | Create a tag (ID auto-assigned by DB) |
| 4 | Add clip to project |
| 5 | Add musical attributes to clip |
| 6 | Add tag to clip |
| 7 | Search clips (multi-filter via temp table) |
| 8 | Direct access — version history, team management, clip inspection |
| 9 | **Benchmark queries** — runs E1–H3 from `queries/*.sql` |
| 100 | Switch user |

## Reload data (wipe and re-import)

```bash
mysql -u root -p harmonyvault < schema/99_drop_all.sql
mysql -u root -p < schema/01_create_tables.sql
mysql -u root -p < schema/02_constraints.sql
mysql -u root -p < schema/03_triggers.sql
mysql -u root -p < schema/04_indexes.sql
mysql -u root -p < queries/stored_procedures.sql
java -cp "cli_java/out:cli_java/lib/mysql-connector-j-9.3.0.jar" DataLoader
```
