#!/usr/bin/env bash
# Run from HarmonyVault repo root: bash cli_java/build.sh
set -e

JAR=$(ls cli_java/lib/mysql-connector-j-*.jar 2>/dev/null | head -1)
if [ -z "$JAR" ]; then
  echo "ERROR: no mysql-connector-j jar found in cli_java/lib/"
  echo "Download it with:"
  echo '  curl -L "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.3.0/mysql-connector-j-9.3.0.jar" -o cli_java/lib/mysql-connector-j-9.3.0.jar'
  exit 1
fi

mkdir -p cli_java/out
javac -cp "$JAR" cli_java/src/*.java -d cli_java/out
echo "Build OK."
echo ""
echo "Run with:"
echo "  java -cp \"cli_java/out:$JAR\" DataLoader       # load CSVs once"
echo "  java -cp \"cli_java/out:$JAR\" HarmonyVaultCLI  # interactive CLI"
