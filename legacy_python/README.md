# legacy_python/

Archived on **2026-04-17** after the team pivoted the CLI track from Python to Java.

## What lives here and why

| Path | Original owner | Reason archived |
| --- | --- | --- |
| `cli/` | Sky Zhou | Superseded by Sky's Java CLI in a separate repository. That Java CLI is the graded CLI deliverable. |
| `web/` | Jacob + Sky | Depended on `cli/db.py`. The Flask web UI was an optional +3% extra-credit goal; the team chose to deprioritize it given the four-day demo timeline. Kept here in case we revive it for the final report screenshots. |
| `tests/test_cli_smoke.py` | shared | Tested `python -m cli --help`; obsolete once `cli/` moved out of the import path. |

## What is **not** here and why

Schema (`schema/`), docs (`docs/`), queries (`queries/`), data-generation scripts (`scripts/`), `tests/test_schema_loads.py`, and `tests/test_queries_run.py` all remain under the main tree — they are still the graded deliverable for the Alfred and Jacob tracks, and they do not depend on any code in this folder.

## How to revive (if needed)

1. `git mv legacy_python/cli ../cli`
2. `git mv legacy_python/web ../web`
3. `git mv legacy_python/tests/test_cli_smoke.py ../tests/test_cli_smoke.py`
4. Reinstall Python dependencies (`click`, `flask`) from `requirements.txt`.
5. Confirm `python -m cli --help` runs and `flask --app web.app run` serves.

The imports inside this folder still say `from cli import db` and `from web.routes import ...` — they will work again the moment the folders move back to the repo root.
