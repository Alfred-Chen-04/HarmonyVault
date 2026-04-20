import java.io.File;
import java.sql.*;

public class DataLoader {

    // Load order: project_collaborators before project_clips so the access
    // trigger (trg_project_clips_before_insert_access) can validate clip owners.
    private static final String[][] TABLES = {
        {"users.csv",                 "Users",                "userID, username, email, dateCreated"},
        {"tags.csv",                  "Tags",                 "tagID, userID, tagName"},
        {"clips.csv",                 "Clips",                "clipID, userID, title, duration, filepath, dateCreated"},
        {"musical_attributes.csv",    "MusicalAttributes",    "clipID, musicalKey, mode, tempo, timeSignature"},
        {"projects.csv",              "Projects",             "projectID, ownerUserID, name, description, dateCreated"},
        {"clip_tags.csv",             "ClipTags",             "clipID, tagID"},
        {"project_collaborators.csv", "ProjectCollaborators", "projectID, userID, role, addedAt"},
        {"project_clips.csv",         "ProjectClips",         "projectID, clipID"},
        {"clip_versions.csv",         "ClipVersions",         "versionID, clipID, versionNumber, notes, filepath, dateCreated"},
    };

    public static void main(String[] args) throws Exception {
        String csvDir = new File("data/csv").getAbsolutePath();
        System.out.println("Loading CSVs from: " + csvDir);

        try (Connection conn = DatabaseConfig.getConnection();
             Statement stmt = conn.createStatement()) {

            stmt.execute("SET FOREIGN_KEY_CHECKS = 0");
            stmt.execute("SET UNIQUE_CHECKS = 0");

            for (String[] t : TABLES) {
                String file  = csvDir + File.separator + t[0];
                String table = t[1];
                String cols  = t[2];

                if (!new File(file).exists()) {
                    System.out.println("  SKIP (not found): " + t[0]);
                    continue;
                }

                // Use forward slashes for MySQL LOAD DATA even on Windows
                String safePath = file.replace("\\", "/");

                String sql =
                    "LOAD DATA LOCAL INFILE '" + safePath + "' " +
                    "INTO TABLE " + table + " " +
                    "CHARACTER SET utf8mb4 " +
                    "FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' " +
                    "LINES TERMINATED BY '\\n' " +
                    "IGNORE 1 LINES " +
                    "(" + cols + ")";

                stmt.execute(sql);

                try (ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM " + table)) {
                    rs.next();
                    System.out.printf("  LOADED %-30s → %,d rows%n", table, rs.getInt(1));
                }
            }

            stmt.execute("SET FOREIGN_KEY_CHECKS = 1");
            stmt.execute("SET UNIQUE_CHECKS = 1");
            System.out.println("\nDone. All tables loaded.");
        }
    }
}
