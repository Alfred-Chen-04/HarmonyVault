"""Single source of truth for runtime configuration.

Loads values from a `.env` file at the repo root, falling back to process
environment variables. Every other module (CLI, scripts, web) imports from
here so credentials and paths live in exactly one place.
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


DB = DBConfig(
    host=os.environ.get("DB_HOST", "127.0.0.1"),
    port=int(os.environ.get("DB_PORT", "3306")),
    user=_require("DB_USER"),
    password=_require("DB_PASSWORD"),
    database=os.environ.get("DB_NAME", "harmonyvault"),
)

SPOTIFY_CSV_PATH = REPO_ROOT / os.environ.get(
    "SPOTIFY_CSV_PATH", "data/SpotifyFeatures.csv"
)
SPOTIFY_LOAD_LIMIT = int(os.environ.get("SPOTIFY_LOAD_LIMIT", "10000"))

SCHEMA_DIR = REPO_ROOT / "schema"
QUERIES_DIR = REPO_ROOT / "queries"
