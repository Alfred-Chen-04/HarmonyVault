import java.sql.*;
import java.util.Scanner;

public class HarmonyVaultCLI {
    private static Scanner scanner = new Scanner(System.in);
    private static int currentUserID = -1;

    public static void main(String[] args) {
        System.out.println("=== HARMONY VAULT: DEMO MODE (EXPLICIT IDs) ===");
        while (true) {
            if (currentUserID == -1) loginMenu();
            else mainMenu();
        }
    }

    private static void loginMenu() {
        System.out.print("\nLogin - Enter User ID (or 0 to exit): ");
        int id = Integer.parseInt(scanner.nextLine());
        if (id == 0) System.exit(0);
        
        // Verify user exists
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement pstmt = conn.prepareStatement("SELECT username FROM Users WHERE userID = ?")) {
            pstmt.setInt(1, id);
            ResultSet rs = pstmt.executeQuery();
            if (rs.next()) {
                currentUserID = id;
                System.out.println("Logged in as: " + rs.getString("username"));
            } else {
                System.out.println("User ID not found in database.");
            }
        } catch (SQLException e) { e.printStackTrace(); }
    }

    private static void mainMenu() {
        System.out.println("\n--- OPERATIONS ---");
        System.out.println();
        System.out.println("1. Create clip");
        System.out.println("2. Create project");
        System.out.println("3. Create tag");
        System.out.println();
        System.out.println("4. Add clip to project");
        System.out.println("5. Add musical attributes to clip");
        System.out.println("6. Add tag to clip");
        System.out.println();
        System.out.println("7. Search clips");
        System.out.println();
        System.out.println("8. Enter direct access tool");
        System.out.println("9. Run benchmark queries (E1-H3)");
        System.out.println();
        System.out.println("100. Switch user");
        System.out.print("> ");

        int choice = Integer.parseInt(scanner.nextLine());
        switch (choice) {
            case 1:   createClip();            break;
            case 2:   createProject();         break;
            case 3:   createTag();             break;
            case 4:   addClipToProject();      break;
            case 5:   addAttributesToClip();   break;
            case 6:   addTagToClip();          break;
            case 7:   searchMode();            break;
            case 8:   directAccessMenu();      break;
            case 9:   runBenchmarkQueries();   break;
            case 100: switchUser();            break;
        }
    }

    public static void directAccessMenu() {
        Scanner scanner = new Scanner(System.in);
        System.out.println("\n--- DIRECT ACCESS ---");
        System.out.println("1. Manage clip versions (by ID)");
        System.out.println("2. Manage project team (by ID)");
        System.out.println("3. Inspect clip details (by ID)");
        System.out.println("4. Back");
        System.out.print("Choice > ");
        String choice = scanner.nextLine();

        switch (choice) {
            case "1":
                System.out.print("Enter Clip ID: ");
                try {
                    int clipId = Integer.parseInt(scanner.nextLine());
                    // First, check if clip exists
                    if (recordExists("Clips", "clipID", clipId)) {
                        manageClipVersionsFlow(clipId);
                    } else {
                        System.out.println("Error: Clip ID not found.");
                    }
                } catch (NumberFormatException e) {
                    System.out.println("Invalid ID format.");
                }
                break;

            case "2":
                System.out.print("Enter Project ID: ");
                try {
                    int projectId = Integer.parseInt(scanner.nextLine());
                    // First, check if project exists
                    if (recordExists("Projects", "projectID", projectId)) {
                        manageCollaborators(projectId); // Reusing the method we built!
                    } else {
                        System.out.println("Error: Project ID not found.");
                    }
                } catch (NumberFormatException e) {
                    System.out.println("Invalid ID format.");
                }
                break;
            
            case "3":
                System.out.print("Enter Clip ID to Inspect: ");
                try {
                    int id = Integer.parseInt(scanner.nextLine());
                    inspectClipDNA(id);
                } catch (NumberFormatException e) {
                    System.out.println("Invalid ID.");
                }
                break;
        }
    }

    public static void manageClipVersionsFlow(int clipId) {
        Scanner scanner = new Scanner(System.in);
        boolean back = false;

        while (!back) {
            System.out.println("\n--- VERSION MANAGEMENT [Clip #" + clipId + "] ---");
            System.out.println("1. Show History");
            System.out.println("2. Add New Version");
            System.out.println("3. Back");
            System.out.print("Choice > ");
            String choice = scanner.nextLine();

            if (choice.equals("1")) {
                showClipHistory(clipId);
            } else if (choice.equals("2")) {
                System.out.print("Notes for new version: ");
                String notes = scanner.nextLine();
                System.out.print("Path to new file: ");
                String path = scanner.nextLine();
                addNewVersion(clipId, notes, path);
            } else if (choice.equals("3")) {
                back = true;
            }
        }
    }

    private static boolean recordExists(String tableName, String idColumn, int id) {
        String sql = "SELECT 1 FROM " + tableName + " WHERE " + idColumn + " = ?";
        try (Connection conn = DatabaseConfig.getConnection();
            PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setInt(1, id);
            try (ResultSet rs = pstmt.executeQuery()) {
                return rs.next();
            }
        } catch (SQLException e) {
            return false;
        }
    }

    public static void inspectClipDNA(int clipId) {
        // We use GROUP_CONCAT to list all tags in a single row
        String sql = "SELECT c.title, c.duration, ma.musicalKey, ma.mode, ma.tempo, " +
                    "GROUP_CONCAT(t.tagName SEPARATOR ', ') as genres " +
                    "FROM Clips c " +
                    "LEFT JOIN MusicalAttributes ma ON c.clipID = ma.clipID " +
                    "LEFT JOIN ClipTags ct ON c.clipID = ct.clipID " +
                    "LEFT JOIN Tags t ON ct.tagID = t.tagID " +
                    "WHERE c.clipID = ? " +
                    "GROUP BY c.clipID";

        try (Connection conn = DatabaseConfig.getConnection();
            PreparedStatement pstmt = conn.prepareStatement(sql)) {
            
            pstmt.setInt(1, clipId);
            ResultSet rs = pstmt.executeQuery();

            if (rs.next()) {
                System.out.println("\n--- CLIP Details: [" + rs.getString("title") + "] ---");
                System.out.println("ID:         " + clipId);
                System.out.println("Duration:   " + rs.getDouble("duration") + "s");
                System.out.println("------------------------------------------");
                
                // Handle cases where Spotify attributes might be missing
                String key = rs.getString("musicalKey");
                if (key != null) {
                    System.out.printf("Musical Key: %-5s | Mode: %-10s%n", 
                        key, rs.getString("mode"));
                    System.out.printf("Tempo:       %-5.2f | Genres: %s%n", 
                        rs.getDouble("tempo"), 
                        (rs.getString("genres") != null ? rs.getString("genres") : "None"));
                } else {
                    System.out.println("Attributes: No musical data available.");
                }
                System.out.println("------------------------------------------");
            } else {
                System.out.println("Error: Clip #" + clipId + " not found.");
            }

        } catch (SQLException e) {
            System.err.println("Inspection failed: " + e.getMessage());
        }
    }


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


    private static void addClipToProject() {
        System.out.print("Clip ID: ");      int cID = Integer.parseInt(scanner.nextLine());
        System.out.print("Project ID: ");   int pID = Integer.parseInt(scanner.nextLine());

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement pstmt = conn.prepareStatement("INSERT INTO ProjectClips (projectID, clipID) VALUES (?, ?)")) {
            pstmt.setInt(1, pID);
            pstmt.setInt(2, cID);
            pstmt.executeUpdate();
            System.out.println("Success: Clip linked to Project.");
        } catch (SQLException e) { System.out.println("Link failed."); }
    }

    private static void addAttributesToClip() {
        System.out.print("Target Clip ID: ");       int cID = Integer.parseInt(scanner.nextLine());
        System.out.print("Key (e.g., C, F#): ");    String key = scanner.nextLine();
        System.out.print("Mode (major/minor): ");   String mode = scanner.nextLine();
        System.out.print("Tempo (BPM): ");          double tempo = Double.parseDouble(scanner.nextLine());

        String sql = "INSERT INTO MusicalAttributes (clipID, musicalKey, mode, tempo) VALUES (?, ?, ?, ?)";
        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setInt(1, cID);
            pstmt.setString(2, key);
            pstmt.setString(3, mode);
            pstmt.setDouble(4, tempo);
            pstmt.executeUpdate();
            System.out.println("Attributes linked to Clip #" + cID);
        } catch (SQLException e) { System.out.println("Check failed: " + e.getMessage()); }
    }

    private static void addTagToClip() {
        System.out.print("Clip ID: "); int cID = Integer.parseInt(scanner.nextLine());
        System.out.print("Tag ID: "); int tID = Integer.parseInt(scanner.nextLine());

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement pstmt = conn.prepareStatement("INSERT INTO ClipTags (clipID, tagID) VALUES (?, ?)")) {
            pstmt.setInt(1, cID);
            pstmt.setInt(2, tID);
            pstmt.executeUpdate();
            System.out.println("Success: Clip linked to Tag.");
        } catch (SQLException e) { System.out.println("Link failed."); }
    }

    private static void switchUser() {
        System.out.print("User ID: "); int uID = Integer.parseInt(scanner.nextLine());

        try (Connection conn = DatabaseConfig.getConnection();
             PreparedStatement pstmt = conn.prepareStatement("SELECT username FROM Users WHERE userID = ?")) {
            pstmt.setInt(1, uID);
            ResultSet rs = pstmt.executeQuery();
            if (rs.next()) {
                currentUserID = uID;
                System.out.println("Logged in as: " + rs.getString("username"));
            } else {
                System.out.println("User ID not found in database.");
            }
        } catch (SQLException e) { e.printStackTrace(); }
    }

    public static void manageCollaborators(int projectId) {
        Scanner scanner = new Scanner(System.in);
        boolean back = false;

        while (!back) {
            // 1. Display Current Team
            String sql = "SELECT u.username, pc.role, pc.addedAt FROM ProjectCollaborators pc " +
                        "JOIN Users u ON pc.userID = u.userID WHERE pc.projectID = ?";
                        
            try (Connection conn = DatabaseConfig.getConnection();
                PreparedStatement pstmt = conn.prepareStatement(sql)) {
                
                pstmt.setInt(1, projectId);
                ResultSet rs = pstmt.executeQuery();

                System.out.println("\n===== PROJECT COLLABORATORS =====");
                boolean hasCollabs = false;
                while (rs.next()) {
                    hasCollabs = true;
                    System.out.printf("- %-15s | Role: %-10s | Joined: %s%n", 
                        rs.getString("username"), 
                        rs.getString("role"),
                        rs.getTimestamp("addedAt"));
                }
                if (!hasCollabs) System.out.println("(No collaborators yet)");

                // 2. Action Menu
                System.out.println("\nACTIONS: [1] Add User [2] Remove User [3] Back");
                System.out.print("Choice > ");
                String choice = scanner.nextLine();

                switch (choice) {
                    case "1":
                        System.out.print("Enter username to add: ");
                        String userToAdd = scanner.nextLine();
                        System.out.print("Enter role (owner/editor/viewer): ");
                        String role = scanner.nextLine();
                        addCollaborator(projectId, userToAdd, role);
                        break;
                    case "2":
                        System.out.print("Enter username to remove: ");
                        String userToRemove = scanner.nextLine();
                        removeCollaborator(projectId, userToRemove);
                        break;
                    case "3":
                        back = true;
                        break;
                    default:
                        System.out.println("Invalid choice.");
                }
            } catch (SQLException e) {
                System.err.println("Error: " + e.getMessage());
                back = true;
            }
        }
    }

    public static void addCollaborator(int projectId, String username, String role) {
        String sql = "INSERT INTO ProjectCollaborators (projectID, userID, role, addedAt) " +
                    "SELECT ?, userID, ?, CURRENT_TIMESTAMP FROM Users WHERE username = ?";

        try (Connection conn = DatabaseConfig.getConnection();
            PreparedStatement pstmt = conn.prepareStatement(sql)) {
            
            pstmt.setInt(1, projectId);
            pstmt.setString(2, role.toLowerCase());
            pstmt.setString(3, username);
            
            int rows = pstmt.executeUpdate();
            if (rows > 0) {
                System.out.println("User '" + username + "' added to project as " + role);
            } else {
                System.out.println("User not found.");
            }
        } catch (SQLException e) {
            System.err.println("Failed to add collaborator: " + e.getMessage());
        }
    }

    public static void removeCollaborator(int projectId, String username) {
        String sql = "DELETE FROM ProjectCollaborators WHERE projectID = ? AND userID = " +
                    "(SELECT userID FROM Users WHERE username = ?)";

        try (Connection conn = DatabaseConfig.getConnection();
            PreparedStatement pstmt = conn.prepareStatement(sql)) {
            
            pstmt.setInt(1, projectId);
            pstmt.setString(2, username);
            
            int rows = pstmt.executeUpdate();
            if (rows > 0) {
                System.out.println("Successfully removed '" + username + "' from the project.");
            } else {
                System.out.println("User not found or not a collaborator on this project.");
            }
        } catch (SQLException e) {
            System.err.println("Failed to remove collaborator: " + e.getMessage());
        }
    }

    public static void showClipHistory(int clipId) {
        String sql = "SELECT versionNumber, notes, dateCreated FROM ClipVersions " +
                    "WHERE clipID = ? ORDER BY versionNumber DESC";

        try (Connection conn = DatabaseConfig.getConnection();
            PreparedStatement pstmt = conn.prepareStatement(sql)) {
            
            pstmt.setInt(1, clipId);
            ResultSet rs = pstmt.executeQuery();

            System.out.println("\n--- Version History for Clip #" + clipId + " ---");
            boolean hasVersions = false;
            while (rs.next()) {
                hasVersions = true;
                System.out.printf("v%d | %-20s | Created: %s%n",
                    rs.getInt("versionNumber"), 
                    rs.getString("notes"), 
                    rs.getTimestamp("dateCreated"));
            }
            
            if (!hasVersions) System.out.println("No previous versions found. This is the original clip.");

        } catch (SQLException e) {
            System.err.println("Error loading history: " + e.getMessage());
        }
    }

    public static void addNewVersion(int clipId, String notes, String newFilepath) {
        // Delegates to stored procedure add_clip_version — atomic, trigger-sequenced versioning
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

    private static void searchMode() {
        // We open ONE connection here and keep it open until the method returns
        try (Connection sessionConn = DatabaseConfig.getConnection()) {
            
            // 1. Initialize: Only grab clips belonging to the current user
            initializeTempTable(sessionConn);

            while (true) {
                System.out.println("\n=== SEARCH MODE (Refine Results) ===");
                System.out.println("1. Filter by project");
                System.out.println("2. Filter by tag");
                System.out.println("3. Filter by tempo");
                System.out.println("4. Filter by key");
                System.out.println("5. Filter by mode");
                System.out.println("6. Filter by time signature");
                System.out.println("7. Filter by date created");
                System.out.println();
                System.out.println("8. Show results / count");
                System.out.println("9. Reset search");
                System.out.println("0. Exit search");
                System.out.print("> ");

                int choice = Integer.parseInt(scanner.nextLine());
                if (choice == 0) break;

                switch (choice) {
                    case 1: {
                        System.out.print("Enter Project ID: ");
                        int pID = Integer.parseInt(scanner.nextLine());
                        applyFilter(sessionConn, "SELECT clipID FROM ProjectClips WHERE projectID = ?", pID);
                        break;
                    }
                    case 2: {
                        System.out.print("Enter Tag ID: ");
                        int tID = Integer.parseInt(scanner.nextLine());
                        applyFilter(sessionConn, "SELECT clipID FROM ClipTags WHERE tagID = ?", tID);
                        break;
                    }
                    case 3: {
                        System.out.print("Enter Minimum Tempo: ");
                        double minT = Double.parseDouble(scanner.nextLine());
                        System.out.print("Enter Maximum Tempo: ");
                        double maxT = Double.parseDouble(scanner.nextLine());
                        String sub3 = "SELECT clipID FROM MusicalAttributes WHERE tempo BETWEEN ? AND ?";
                        applyRangeFilter(sessionConn, sub3, minT, maxT);
                        break;
                    }
                    case 4: {
                        System.out.print("Enter Key (e.g., C, Eb, F#): ");
                        String key = scanner.nextLine();
                        applyFilter(sessionConn, "SELECT clipID FROM MusicalAttributes WHERE musicalKey = ?", key);
                        break;
                    }
                    case 5: {
                        System.out.print("Enter Mode (major/minor): ");
                        String mode = scanner.nextLine();
                        applyFilter(sessionConn, "SELECT clipID FROM MusicalAttributes WHERE mode = ?", mode);
                        break;
                    }
                    case 6: {
                        System.out.print("Enter Time Signature (e.g., 4/4, 3/4): ");
                        String ts = scanner.nextLine();
                        applyFilter(sessionConn, "SELECT clipID FROM MusicalAttributes WHERE timeSignature = ?", ts);
                        break;
                    }
                    case 7: {
                        System.out.print("Enter Start Date (YYYY-MM-DD): ");
                        String start = scanner.nextLine();
                        System.out.print("Enter End Date (YYYY-MM-DD): ");
                        String end = scanner.nextLine();
                        String sub7 = "SELECT clipID FROM Clips WHERE createdAt BETWEEN ? AND ?";
                        applyRangeFilter(sessionConn, sub7, start, end);
                        break;
                    }
                    case 8: displayTempResults(sessionConn); break;
                    case 9: initializeTempTable(sessionConn); break;
                }
            }
        } catch (SQLException e) {
            System.out.println("Search session error: " + e.getMessage());
        }
    }

    private static void initializeTempTable(Connection conn) throws SQLException {
        try (Statement stmt = conn.createStatement()) {
            stmt.execute("CREATE TEMPORARY TABLE IF NOT EXISTS TempResults (clipID INT PRIMARY KEY)");
            stmt.execute("TRUNCATE TABLE TempResults");
            
            // Optimization: Only load clips owned by the logged-in user
            String sql = "INSERT INTO TempResults (clipID) SELECT clipID FROM Clips WHERE userID = " + currentUserID;
            stmt.execute(sql);
            
            System.out.println("Search initialized with your library.");
        }
    }

    private static void applyFilter(Connection conn, String subQuery, Object param) throws SQLException {
        String sql = "DELETE FROM TempResults WHERE clipID NOT IN (" + subQuery + ")";
        
        try (PreparedStatement pstmt = conn.prepareStatement(sql)) {
            // This 'setObject' call is a JDBC superpower—it figures out the type for you
            pstmt.setObject(1, param);

            int removed = pstmt.executeUpdate();
            int remaining = getRemainingCount(conn);
            System.out.println("Filter applied. " + remaining + " clips match your criteria.");
        }
    }

    private static void applyRangeFilter(Connection conn, String subQuery, Object min, Object max) throws SQLException {
        // The subQuery should look like: "SELECT clipID FROM ... WHERE col BETWEEN ? AND ?"
        String sql = "DELETE FROM TempResults WHERE clipID NOT IN (" + subQuery + ")";
        
        try (PreparedStatement pstmt = conn.prepareStatement(sql)) {
            pstmt.setObject(1, min);
            pstmt.setObject(2, max);

            int removed = pstmt.executeUpdate();
            int remaining = getRemainingCount(conn);
            System.out.println("Range filter applied. " + remaining + " clips match.");
        }
    }

    private static int getRemainingCount(Connection conn) throws SQLException {
        try (Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM TempResults")) {
            return rs.next() ? rs.getInt(1) : 0;
        }
    }

    private static void displayTempResults(Connection conn) throws SQLException {
        String sql = "SELECT c.clipID, c.title FROM Clips c " +
                    "JOIN TempResults tr ON c.clipID = tr.clipID";
        try (Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(sql)) {
            System.out.println("\n--- MATCHING CLIPS ---");
            while (rs.next()) {
                System.out.println("#" + rs.getInt("clipID") + ": " + rs.getString("title"));
            }
        }
    }

    private static void runBenchmarkQueries() {
        String[] queryFiles = {"queries/easy.sql", "queries/medium.sql", "queries/hard.sql"};
        try (Connection conn = DatabaseConfig.getConnection()) {
            for (String filepath : queryFiles) {
                java.util.List<String[]> queries = SqlLoader.loadNamedQueries(filepath);
                for (String[] q : queries) {
                    String label = q[0];
                    String sqlQ  = q[1];
                    System.out.println("\n=== " + label + " ===");
                    try (PreparedStatement pstmt = conn.prepareStatement(sqlQ);
                         ResultSet rs = pstmt.executeQuery()) {
                        ResultSetMetaData meta = rs.getMetaData();
                        int cols = meta.getColumnCount();
                        StringBuilder header = new StringBuilder();
                        for (int i = 1; i <= cols; i++)
                            header.append(String.format("%-22s", meta.getColumnLabel(i)));
                        System.out.println(header);
                        StringBuilder sep = new StringBuilder();
                        for (int s = 0; s < 22 * cols; s++) sep.append('-');
                        System.out.println(sep);
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
}