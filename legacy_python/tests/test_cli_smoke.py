"""The CLI must at least print --help without import errors."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_cli_help_runs():
    result = subprocess.run(
        [sys.executable, "-m", "cli", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "HarmonyVault" in result.stdout
