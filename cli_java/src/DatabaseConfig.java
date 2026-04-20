import java.io.*;
import java.sql.*;
import java.util.Properties;

public class DatabaseConfig {
    private static final Properties PROPS = new Properties();
    private static final String URL;

    static {
        // Look for db.properties in cli_java/ (repo root run) or cwd
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
