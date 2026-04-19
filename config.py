"""Single source of truth for runtime configuration.

Loads values from a `.env` file at the repo root, falling back to process
environment variables. Every other module (CLI, scripts, web) imports from
here so credentials and paths live in exactly one place.

DB is loaded lazily so that CSV-only scripts (load_spotify, generate_synthetic)
can import path constants without needing database credentials in the environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parent
load_dotenv(REPO_ROOT / ".env")


@dataclass(frozen=True)
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

    def to_connector_kwargs(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
        }


def _require(key: str) -> str:
    value = os.environ.get(key)
    if value is None or value == "":
        raise RuntimeError(
            f"Missing required environment variable {key}. "
            "Copy .env.example to .env and fill it in."
        )
    return value


def _make_db() -> DBConfig:
    return DBConfig(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=_require("DB_USER"),
        password=_require("DB_PASSWORD"),
        database=os.environ.get("DB_NAME", "harmonyvault"),
    )


# Path constants — always safe to import, no credentials needed.
SPOTIFY_CSV_PATH = REPO_ROOT / os.environ.get(
    "SPOTIFY_CSV_PATH", "data/SpotifyFeatures.csv"
)
SPOTIFY_LOAD_LIMIT = int(os.environ.get("SPOTIFY_LOAD_LIMIT", "10000"))

SCHEMA_DIR = REPO_ROOT / "schema"
QUERIES_DIR = REPO_ROOT / "queries"
CSV_DIR = REPO_ROOT / "data" / "csv"
CSV_SAMPLE_DIR = REPO_ROOT / "data" / "csv_sample"

# DB is constructed on first access so scripts that only generate CSVs
# can import this module without database credentials in the environment.
_db_instance: DBConfig | None = None


def __getattr__(name: str):
    global _db_instance
    if name == "DB":
        if _db_instance is None:
            _db_instance = _make_db()
        return _db_instance
    raise AttributeError(f"module 'config' has no attribute {name!r}")
