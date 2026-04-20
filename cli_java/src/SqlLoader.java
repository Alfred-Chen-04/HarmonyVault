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
