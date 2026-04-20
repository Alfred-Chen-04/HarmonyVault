# Jacob Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge Jacob's Java CLI into HarmonyVault as `cli_java/`, satisfy every rubric item (a–i), and keep changes to the existing Java code minimal.

**Architecture:** All Java source lives in `cli_java/src/`. `DataLoader.java` handles bulk CSV ingestion via `LOAD DATA LOCAL INFILE`. `SqlLoader.java` parses `queries/*.sql` so the CLI runs queries from files instead of hardcoded strings. `HarmonyVaultCLI.java` gets three targeted edits: drop hand-entered IDs, wire the stored procedure for versioning, add a benchmark-query menu.

**Tech Stack:** Java 17+, mysql-connector-j 9.x, MySQL 8.x, Python 3.11 (Sky's generator — unchanged)

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `cli_java/src/DatabaseConfig.java` | modify | Read JDBC creds from `db.properties`; add `allowLoadLocalInfile=true` to URL |
| `cli_java/src/HarmonyVaultCLI.java` | modify | Remove hand-entered IDs; call `add_clip_version` stored proc; add benchmark menu |
| `cli_java/src/DataLoader.java` | **create** | LOAD DATA LOCAL INFILE × 9 tables in FK-safe order |
| `cli_java/src/SqlLoader.java` | **create** | Parse `-- E1: …` labelled blocks from `queries/*.sql` |
| `cli_java/db.properties.example` | **create** | Committed credential template |
| `cli_java/build.sh` | **create** | `javac` → `out/`, no external build tool |
| `cli_java/README.md` | **create** | Prerequisites + one-shot setup + run commands |
| `AGENTS.md` | modify | Reflect unified single-repo structure |

---

## Task 1: Create `cli_java/` and copy Jacob's source files

**Files:**
- Create: `cli_java/src/` `cli_java/lib/`
- Copy: `Jacob's Work/DatabaseConfig.java` → `cli_java/src/DatabaseConfig.java`
- Copy: `Jacob's Work/HarmonyVaultCLI.java` → `cli_java/src/HarmonyVaultCLI.java`

- [ ] **Step 1: Create directories**

Run from `HarmonyVault/`:
```bash
mkdir -p cli_java/src cli_java/lib cli_java/out
```

- [ ] **Step 2: Copy Java source files**

```bash
cp "../Jacob's Work/DatabaseConfig.java" cli_java/src/
cp "../Jacob's Work/HarmonyVaultCLI.java" cli_java/src/
```

- [ ] **Step 3: Download mysql-connector-j if not already present**

Download `mysql-connector-j-9.3.0.jar` (or latest 9.x) from Maven Central and place it at:
```
cli_java/lib/mysql-connector-j-9.3.0.jar
```
Direct download (if `curl` available):
```bash
curl -L "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.3.0/mysql-connector-j-9.3.0.jar" \
     -o cli_java/lib/mysql-connector-j-9.3.0.jar
```

- [ ] **Step 4: Add jar to .gitignore**

Open `HarmonyVault/.gitignore` and add:
```
cli_java/lib/*.jar
cli_java/out/
```

- [ ] **Step 5: Verify files exist**

```bash
ls cli_java/src/ cli_java/lib/
```
Expected: `DatabaseConfig.java  HarmonyVaultCLI.java` in `src/`, one `.jar` in `lib/`.

---

## Task 2: Modify `DatabaseConfig.java` — read from `db.properties`

**Files:**
- Modify: `cli_java/src/DatabaseConfig.java`
- Create: `cli_java/db.properties.example`

- [ ] **Step 1: Write `db.properties.example`**

Create `cli_java/db.properties.example`:
```properties
db.host=localhost
db.port=3306
db.name=harmonyvault
db.user=root
db.password=CSDS341PROJECT
```

- [ ] **Step 2: Add `db.properties` to `.gitignore`**

Add to `HarmonyVault/.gitignore`:
```
cli_java/db.properties
```

- [ ] **Step 3: Rewrite `DatabaseConfig.java`**

Replace the entire contents of `cli_java/src/DatabaseConfig.java` with:
```java
import java.io.*;
import java.sql.*;
import java.util.Properties;

public class DatabaseConfig {
    private static final Properties PROPS = new Properties();
    private static final String URL;

    static {
        File propFile = new File("cli_java/db.properties");
        if (!propFile.exists()) propFile = new File("db.properties");
        if (propFile.exists()) {
            try (InputStream in = new FileInputStream(propFile)) {
                PROPS.load(in);
            } catch (IOException e) {
                System.err.println("Warning: could not read db.properties — using defaults.");
            }
        }
        String host = PROPS.getProperty("db.host", "localhost");
        String port = PROPS.getProperty("db.port", "3306");
        String name = PROPS.getProperty("db.name", "harmonyvault");
        URL = "jdbc:mysql://" + host + ":" + port + "/" + name
            + "?allowLoadLocalInfile=true&useSSL=false&serverTimezone=UTC";
    }

    public static Connection getConnection() throws SQLException {
        return DriverManager.getConnection(
            URL,
            PROPS.getProperty("db.user", "root"),
            PROPS.getProperty("db.password", "")
        );
    }
}
```

- [ ] **Step 4: Create `cli_java/db.properties` from the example (not committed)**

```bash
cp cli_java/db.properties.example cli_java/db.properties
# Edit the password if your MySQL root password differs
```

---

## Task 3: Create `build.sh`

**Files:**
- Create: `cli_java/build.sh`

- [ ] **Step 1: Write build script**

Create `cli_java/build.sh`:
```bash
#!/usr/bin/env bash
# Run from HarmonyVault repo root: bash cli_java/build.sh
set -e

JAR=$(ls cli_java/lib/mysql-connector-j-*.jar 2>/dev/null | head -1)
if [ -z "$JAR" ]; then
  echo "ERROR: no mysql-connector-j jar in cli_java/lib/"
  exit 1
fi

mkdir -p cli_java/out
javac -cp "$JAR" cli_java/src/*.java -d cli_java/out
echo "Build OK. Run with:"
echo "  java -cp \"cli_java/out:$JAR\" DataLoader       # load CSVs once"
echo "  java -cp \"cli_java/out:$JAR\" HarmonyVaultCLI  # interactive CLI"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x cli_java/build.sh
```

- [ ] **Step 3: Test that it compiles (will have errors from the next tasks — that is expected)**

```bash
bash cli_java/build.sh 2>&1 | head -20
```
The compile should succeed at this point because we haven't changed the Java yet.
Expected: `Build OK.`

---

## Task 4: Create `SqlLoader.java`

**Files:**
- Create: `cli_java/src/SqlLoader.java`

- [ ] **Step 1: Create the file**

Create `cli_java/src/SqlLoader.java`:
```java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class SqlLoader {
    // Parse a queries/*.sql file and return [label, sql] pairs.
    // Labels are comment lines of the form:  -- E1: description text
    public static List<String[]> loadNamedQueries(String filepath) throws IOException {
        List<String> lines = Files.readAllLines(Paths.get(filepath));
        List<String[]> result = new ArrayList<>();
        Pattern labelPat = Pattern.compile("^--\\s+([A-Za-z]\\d+):\\s*(.*)$");

        String currentLabel = null;
        StringBuilder currentSql = new StringBuilder();

        for (String line : lines) {
            Matcher m = labelPat.matcher(line.trim());
            if (m.matches()) {
                flush(result, currentLabel, currentSql);
                currentLabel = m.group(1).toUpperCase() + ": " + m.group(2).trim();
                currentSql = new StringBuilder();
            } else if (currentLabel != null && !line.trim().startsWith("--")) {
                currentSql.append(line).append("\n");
            }
        }
        flush(result, currentLabel, currentSql);
        return result;
    }

    private static void flush(List<String[]> out, String label, StringBuilder sql) {
        if (label == null) return;
        String body = sql.toString().trim();
        if (body.endsWith(";")) body = body.substring(0, body.length() - 1).trim();
        if (!body.isEmpty()) out.add(new String[]{label, body});
    }
}
```

- [ ] **Step 2: Verify it compiles**

```bash
bash cli_java/build.sh
```
Expected: `Build OK.`

---

## Task 5: Create `DataLoader.java`

**Files:**
- Create: `cli_java/src/DataLoader.java`

This is the rubric §e deliverable: bulk load via `LOAD DATA LOCAL INFILE`.

**Prerequisite:** MySQL server must have `local_infile=ON`. Run once in MySQL CLI:
```sql
SET GLOBAL local_infile = 1;
```
Or add `local_infile=ON` to `/etc/mysql/my.cnf` under `[mysqld]`.

- [ ] **Step 1: Create the file**

Create `cli_java/src/DataLoader.java`:
```java
import java.io.File;
import java.sql.*;

public class DataLoader {

    // FK-safe load order matching docs/csv_format.md
    private static final String[][] TABLES = {
        {"users.csv",                 "Users",                 "userID, username, email, dateCreated"},
        {"tags.csv",                  "Tags",                  "tagID, userID, tagName"},
        {"clips.csv",                 "Clips",                 "clipID, userID, title, duration, filepath, dateCreated"},
        {"musical_attributes.csv",    "MusicalAttributes",     "clipID, musicalKey, mode, tempo, timeSignature"},
        {"projects.csv",              "Projects",              "projectID, ownerUserID, name, description, dateCreated"},
        {"clip_tags.csv",             "ClipTags",              "clipID, tagID"},
        {"project_clips.csv",         "ProjectClips",          "projectID, clipID"},
        {"project_collaborators.csv", "ProjectCollaborators",  "projectID, userID, role, addedAt"},
        {"clip_versions.csv",         "ClipVersions",          "versionID, clipID, versionNumber, notes, filepath, dateCreated"},
    };

    public static void main(String[] args) throws Exception {
        String csvDir = new File("data/csv").getAbsolutePath();
        System.out.println("Loading CSVs from: " + csvDir);

        try (Connection conn = DatabaseConfig.getConnection();
             Statement stmt = conn.createStatement()) {

            stmt.execute("SET FOREIGN_KEY_CHECKS = 0");
            stmt.execute("SET UNIQUE_CHECKS = 0");

            for (String[] t : TABLES) {
                String file = csvDir + File.separator + t[0];
                String table = t[1];
                String columns = t[2];

                if (!new File(file).exists()) {
                    System.out.println("  SKIP (file not found): " + t[0]);
                    continue;
                }

                // Escape backslashes in Windows paths
                String safePath = file.replace("\\", "/");

                String sql = "LOAD DATA LOCAL INFILE '" + safePath + "' " +
                    "INTO TABLE " + table + " " +
                    "CHARACTER SET utf8mb4 " +
                    "FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' " +
                    "LINES TERMINATED BY '\\n' " +
                    "IGNORE 1 LINES " +
                    "(" + columns + ")";

                stmt.execute(sql);

                try (ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM " + table)) {
                    rs.next();
                    System.out.printf("  LOADED %-30s → %d rows%n", table, rs.getInt(1));
                }
            }

            stmt.execute("SET FOREIGN_KEY_CHECKS = 1");
            stmt.execute("SET UNIQUE_CHECKS = 1");
            System.out.println("Done.");
        }
    }
}
```

- [ ] **Step 2: Verify it compiles**

```bash
bash cli_java/build.sh
```
Expected: `Build OK.`

---

## Task 6: Modify `HarmonyVaultCLI.java` — three targeted edits

**Files:**
- Modify: `cli_java/src/HarmonyVaultCLI.java`

### Edit A — Remove hand-entered IDs from `createClip`, `createProject`, `createTag`

- [ ] **Step 1: Replace `createClip`**

Find and replace the entire `createClip` method (lines ~208–225 in the original):

Old:
```java
    private static void createClip() {
        System.out.print("Assign Clip ID: "); int cID = Integer.parseInt(scanner.nextLine());
        System.out.print("Title: ");    String title = scanner.nextLine();
        System.out.print("Duration: "); double dur = Double.parseDouble(scanner.nextLine());
        System.out.print("Filepath: "); String path = scanner.nextLine();

        String sql = "INSERT INTO Clips (clipID, userID, title, duration, filepath) VALUES (?, ?, ?, ?, ?)";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setInt(1, cID);
            pstmt.setInt(2, currentUserID);
            pstmt.setString(3, title);
            pstmt.setDouble(4, dur);
            pstmt.setString(5, path);
            pstmt.executeUpdate();
            System.out.println("Clip #" + cID + " stored.");
        } catch (SQLException e) { System.out.println("Error: " + e.getMessage()); }
    }
```

New:
```java
    private static void createClip() {
        System.out.print("Title: ");    String title = scanner.nextLine();
        System.out.print("Duration (seconds): "); double dur = Double.parseDouble(scanner.nextLine());
        System.out.print("Filepath: "); String path = scanner.nextLine();

        String sql = "INSERT INTO Clips (userID, title, duration, filepath) VALUES (?, ?, ?, ?)";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            pstmt.setInt(1, currentUserID);
            pstmt.setString(2, title);
            pstmt.setDouble(3, dur);
            pstmt.setString(4, path);
            pstmt.executeUpdate();
            try (ResultSet keys = pstmt.getGeneratedKeys()) {
                if (keys.next()) System.out.println("Clip created with ID: " + keys.getInt(1));
            }
        } catch (SQLException e) { System.out.println("Error: " + e.getMessage()); }
    }
```

- [ ] **Step 2: Replace `createProject`**

Old:
```java
    private static void createProject() {
        System.out.print("Assign Project ID: ");    int pID = Integer.parseInt(scanner.nextLine());
        System.out.print("Name: ");                 String name = scanner.nextLine();
        System.out.print("Description: ");          String desc = scanner.nextLine();

        String sql = "INSERT INTO Projects (projectID, ownerUserID, name, description) VALUES (?, ?, ?, ?)";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setInt(1, pID);
            pstmt.setInt(2, currentUserID);
            pstmt.setString(3, name);
            pstmt.setString(4, desc);
            pstmt.executeUpdate();
            System.out.println("Project #" + pID + " stored.");
        } catch (SQLException e) { System.out.println("Error: " + e.getMessage()); }
    }
```

New:
```java
    private static void createProject() {
        System.out.print("Name: ");                 String name = scanner.nextLine();
        System.out.print("Description: ");          String desc = scanner.nextLine();

        String sql = "INSERT INTO Projects (ownerUserID, name, description) VALUES (?, ?, ?)";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            pstmt.setInt(1, currentUserID);
            pstmt.setString(2, name);
            pstmt.setString(3, desc);
            pstmt.executeUpdate();
            try (ResultSet keys = pstmt.getGeneratedKeys()) {
                if (keys.next()) System.out.println("Project created with ID: " + keys.getInt(1));
            }
        } catch (SQLException e) { System.out.println("Error: " + e.getMessage()); }
    }
```

- [ ] **Step 3: Replace `createTag`**

Old:
```java
    private static void createTag() {
        System.out.print("Assign Tag ID: ");    int tID = Integer.parseInt(scanner.nextLine());
        System.out.print("Tag Name: ");         String name = scanner.nextLine();

        String sql = "INSERT INTO Tags (tagID, userID, tagName) VALUES (?, ?, ?)";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setInt(1, tID);
            pstmt.setInt(2, currentUserID);
            pstmt.setString(3, name);
            pstmt.executeUpdate();
            System.out.println("Tag #" + tID + " created.");
        } catch (SQLException e) { System.out.println("Error: " + e.getMessage()); }
    }
```

New:
```java
    private static void createTag() {
        System.out.print("Tag Name: ");         String name = scanner.nextLine();

        String sql = "INSERT INTO Tags (userID, tagName) VALUES (?, ?)";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            pstmt.setInt(1, currentUserID);
            pstmt.setString(2, name);
            pstmt.executeUpdate();
            try (ResultSet keys = pstmt.getGeneratedKeys()) {
                if (keys.next()) System.out.println("Tag created with ID: " + keys.getInt(1));
            }
        } catch (SQLException e) { System.out.println("Error: " + e.getMessage()); }
    }
```

### Edit B — Wire `addNewVersion` to call the stored procedure

The stored procedure `add_clip_version(p_clipID, p_filepath, p_notes, OUT p_versionID)` is already defined in `queries/stored_procedures.sql`.

- [ ] **Step 4: Replace `addNewVersion`**

Old:
```java
    public static void addNewVersion(int clipId, String notes, String newFilepath) {
        String getVersionSql = "SELECT COALESCE(MAX(versionNumber), 0) FROM ClipVersions WHERE clipID = ?";
        String insertVersionSql = "INSERT INTO ClipVersions (clipID, versionNumber, notes, filepath, dateCreated) " +
                                "VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)";

        try (Connection conn = DatabaseConfig.getConnection()) {
            conn.setAutoCommit(false); // Start transaction

            int nextVersion = 1;
            try (PreparedStatement pstmtGet = conn.prepareStatement(getVersionSql)) {
                pstmtGet.setInt(1, clipId);
                ResultSet rs = pstmtGet.executeQuery();
                if (rs.next()) {
                    nextVersion = rs.getInt(1) + 1;
                }
            }

            try (PreparedStatement pstmtInsert = conn.prepareStatement(insertVersionSql)) {
                pstmtInsert.setInt(1, clipId);
                pstmtInsert.setInt(2, nextVersion);
                pstmtInsert.setString(3, notes);
                pstmtInsert.setString(4, newFilepath);
                pstmtInsert.executeUpdate();
            }

            conn.commit(); // Finalize both steps
            System.out.println("Successfully created version v" + nextVersion + " for Clip #" + clipId);

        } catch (SQLException e) {
            System.err.println("Error creating version: " + e.getMessage());
        }
    }
```

New (calls `CALL add_clip_version` — rubric §h):
```java
    public static void addNewVersion(int clipId, String notes, String newFilepath) {
        try (Connection conn = DatabaseConfig.getConnection();
             CallableStatement cs = conn.prepareCall("{CALL add_clip_version(?, ?, ?, ?)}")) {
            cs.setInt(1, clipId);
            cs.setString(2, newFilepath);
            cs.setString(3, notes);
            cs.registerOutParameter(4, java.sql.Types.INTEGER);
            cs.execute();
            System.out.println("Version created (versionID=" + cs.getInt(4) + ") for Clip #" + clipId);
        } catch (SQLException e) {
            System.err.println("Error creating version: " + e.getMessage());
        }
    }
```

### Edit C — Add "Benchmark queries" menu option

- [ ] **Step 5: Add menu option to `mainMenu`**

Find in `mainMenu`:
```java
        System.out.println("8. Enter direct access tool");
        System.out.println();
        System.out.println("100. Switch user");
```

Replace with:
```java
        System.out.println("8. Enter direct access tool");
        System.out.println("9. Run benchmark queries (E1-H3)");
        System.out.println();
        System.out.println("100. Switch user");
```

- [ ] **Step 6: Add the dispatch case**

Find in the `switch (choice)` block:
```java
            case 8 -> directAccessMenu();

            case 100 -> switchUser();
```

Replace with:
```java
            case 8 -> directAccessMenu();
            case 9 -> runBenchmarkQueries();

            case 100 -> switchUser();
```

- [ ] **Step 7: Add the `runBenchmarkQueries` method**

Add this method anywhere in the class (e.g., just before the closing `}`):
```java
    private static void runBenchmarkQueries() {
        String[] queryFiles = {"queries/easy.sql", "queries/medium.sql", "queries/hard.sql"};
        try (Connection conn = DatabaseConfig.getConnection()) {
            for (String filepath : queryFiles) {
                java.util.List<String[]> queries = SqlLoader.loadNamedQueries(filepath);
                for (String[] q : queries) {
                    String label = q[0];
                    String sql   = q[1];
                    System.out.println("\n=== " + label + " ===");
                    try (PreparedStatement pstmt = conn.prepareStatement(sql);
                         ResultSet rs = pstmt.executeQuery()) {
                        ResultSetMetaData meta = rs.getMetaData();
                        int cols = meta.getColumnCount();
                        StringBuilder header = new StringBuilder();
                        for (int i = 1; i <= cols; i++)
                            header.append(String.format("%-22s", meta.getColumnLabel(i)));
                        System.out.println(header);
                        System.out.println("-".repeat(22 * cols));
                        int rows = 0;
                        while (rs.next() && rows++ < 10) {
                            StringBuilder row = new StringBuilder();
                            for (int i = 1; i <= cols; i++)
                                row.append(String.format("%-22s", rs.getString(i)));
                            System.out.println(row);
                        }
                        if (rows == 0) System.out.println("(no rows)");
                    } catch (SQLException e) {
                        System.out.println("Query failed: " + e.getMessage());
                    }
                }
            }
        } catch (Exception e) {
            System.out.println("Benchmark error: " + e.getMessage());
        }
    }
```

- [ ] **Step 8: Verify it compiles**

```bash
bash cli_java/build.sh
```
Expected: `Build OK.` — any compile error means a typo in the edits above; fix before proceeding.

---

## Task 7: Create `cli_java/README.md`

**Files:**
- Create: `cli_java/README.md`

- [ ] **Step 1: Write README**

Create `cli_java/README.md`:
```markdown
# HarmonyVault CLI (Java)

Command-line interface for HarmonyVault. Owned by Jacob Liebson (jel212).

## Prerequisites

- Java 17+
- MySQL 8.x running locally with `local_infile = ON`
- `cli_java/lib/mysql-connector-j-9.x.jar` (not committed — see below)

### Enable local_infile in MySQL (once)

```sql
SET GLOBAL local_infile = 1;
```

### Get the connector jar

```bash
curl -L "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.3.0/mysql-connector-j-9.3.0.jar" \
     -o cli_java/lib/mysql-connector-j-9.3.0.jar
```

## Setup (run once, from repo root)

```bash
# 1. Generate the 9 CSV files
python scripts/setup_db.py

# 2. Apply the MySQL schema
mysql -u root -p < schema/01_create_tables.sql
mysql -u root -p < schema/02_constraints.sql
mysql -u root -p < schema/03_triggers.sql
mysql -u root -p < schema/04_indexes.sql
mysql -u root -p < queries/stored_procedures.sql

# 3. Configure credentials
cp cli_java/db.properties.example cli_java/db.properties
# Edit cli_java/db.properties and set db.password

# 4. Build
bash cli_java/build.sh

# 5. Load data (run once)
java -cp "cli_java/out:cli_java/lib/mysql-connector-j-9.3.0.jar" DataLoader
```

## Run the interactive CLI

```bash
java -cp "cli_java/out:cli_java/lib/mysql-connector-j-9.3.0.jar" HarmonyVaultCLI
```

## Menu reference

| Option | Description |
|--------|-------------|
| 1 | Create a new clip (ID auto-assigned) |
| 2 | Create a new project (ID auto-assigned) |
| 3 | Create a tag (ID auto-assigned) |
| 4 | Add clip to project |
| 5 | Add musical attributes to clip |
| 6 | Add tag to clip |
| 7 | Search clips (multi-filter, temp table) |
| 8 | Direct access: versions, team, clip details |
| 9 | **Benchmark queries** — runs E1–H3 from queries/*.sql |
| 100 | Switch user |
```

---

## Task 8: Update `AGENTS.md`

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Update the Tech Stack section (§2)**

Find:
```
- CLI language: Java (lives in Jacob's separate repository; uses `mysql-connector-j` with `allowLoadLocalInfile=true`)
```

Replace with:
```
- CLI language: Java (`cli_java/` in this repository; uses `mysql-connector-j` with `allowLoadLocalInfile=true`)
```

- [ ] **Step 2: Update the Run section (§4)**

Find:
```
- Jacob's Java CLI: see Jacob's repository README.
```

Replace with:
```
- Java CLI: `bash cli_java/build.sh` then `java -cp "cli_java/out:cli_java/lib/mysql-connector-j-*.jar" HarmonyVaultCLI`
- Load CSV data: `java -cp "cli_java/out:cli_java/lib/mysql-connector-j-*.jar" DataLoader`
```

- [ ] **Step 3: Update the Directory map (§5)**

Find the row:
```
| [queries/](queries/) | Jacob | Canonical SQL for every example query, plus RA/TRC equivalents |
```

Replace with (and add cli_java row before it):
```
| [cli_java/](cli_java/) | Jacob | Java CLI source, DataLoader, SqlLoader, build script |
| [queries/](queries/) | Jacob | Canonical SQL for every example query, plus RA/TRC equivalents |
```

- [ ] **Step 4: Update §1 (Project) — remove "separate repository" language**

Find:
```
- **Jacob's separate Java repository** owns the command-line interface.
```

Replace with:
```
- **`cli_java/`** (this repository) owns the command-line interface.
```

---

## Task 9: End-to-end integration test

- [ ] **Step 1: Generate CSV data from Sky's pipeline**

```bash
cd /Users/alfred/Desktop/CSDS\ 341\ Final\ Project/HarmonyVault
source .venv/bin/activate
python scripts/setup_db.py
```
Expected: 9 CSV files in `data/csv/`.

- [ ] **Step 2: Apply schema + stored procedures to MySQL**

```bash
mysql -u root -p < schema/01_create_tables.sql
mysql -u root -p < schema/02_constraints.sql
mysql -u root -p < schema/03_triggers.sql
mysql -u root -p < schema/04_indexes.sql
mysql -u root -p < queries/stored_procedures.sql
```
Each command prompts for password; no errors expected.

- [ ] **Step 3: Run DataLoader**

```bash
java -cp "cli_java/out:cli_java/lib/mysql-connector-j-9.3.0.jar" DataLoader
```
Expected output (row counts will vary):
```
Loading CSVs from: /path/to/HarmonyVault/data/csv
  LOADED Users                          → NNN rows
  LOADED Tags                           → NNN rows
  LOADED Clips                          → NNN rows
  LOADED MusicalAttributes              → NNN rows
  LOADED Projects                       → NNN rows
  LOADED ClipTags                       → NNN rows
  LOADED ProjectClips                   → NNN rows
  LOADED ProjectCollaborators           → NNN rows
  LOADED ClipVersions                   → NNN rows
Done.
```

- [ ] **Step 4: Run pytest suite**

```bash
source .venv/bin/activate
cp .env.example .env  # if .env doesn't exist; fill in credentials
pytest -v
```
Expected: all tests PASS (or SKIP if MySQL not configured for pytest).

- [ ] **Step 5: Smoke-test the CLI**

```bash
java -cp "cli_java/out:cli_java/lib/mysql-connector-j-9.3.0.jar" HarmonyVaultCLI
```
Test sequence:
1. Enter a valid `userID` from the loaded data (e.g. `1`) → should print `Logged in as: Producer_1`
2. Choose `9` → should print E1 through H3 results in table form
3. Choose `1` → create a clip (no ID prompt, system assigns one)
4. Choose `8` → `1` → enter the new clip ID → `2` → `Add New Version` → enter notes + filepath → should print `Version created (versionID=…)`
5. Choose `0` to exit search / `100` to switch user

- [ ] **Step 6: Final commit**

```bash
cd /Users/alfred/Desktop/CSDS\ 341\ Final\ Project/HarmonyVault
git add cli_java/ AGENTS.md docs/superpowers/
git commit -m "feat: merge Jacob's Java CLI into cli_java/, add DataLoader + SqlLoader + benchmark menu (rubric §d §e §g §h)"
```

---

## Self-Review Checklist

**Spec coverage:**
- §a ER diagram — ✅ untouched
- §b FDs + BCNF — ✅ untouched
- §c DDL + triggers — ✅ untouched
- §d 9 queries easy/medium/hard — ✅ Task 6 Edit C adds benchmark menu that runs them
- §e LOAD DATA INFILE — ✅ Task 5 DataLoader.java
- §f SQL + RA + TRC — ✅ queries/ra_trc.md untouched
- §g Java CLI all ops — ✅ Task 6 Edit A removes ID friction; all operations preserved
- §h Stored procedure — ✅ Task 6 Edit B wires `CALL add_clip_version`
- §i Work division — ✅ Task 8 updates AGENTS.md

**No placeholder scan:** All code blocks are complete. No TBD. No "fill in details".

**Type consistency:** `SqlLoader.loadNamedQueries(String)` defined in Task 4; called in Task 6 Edit C with matching signature `String filepath` and return `List<String[]>`. `DataLoader.main(String[])` standalone. `CallableStatement` is `java.sql.CallableStatement` — import not needed since `java.sql.*` is already imported in HarmonyVaultCLI.java.
