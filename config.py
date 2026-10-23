"""
config.py — loads environment configuration from .env and resolves the database path.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
VALID_ENVS = {"masked", "unmasked"}


def get_db_path() -> Path:
    """Return the SQLite database path for the configured environment."""
    env = os.getenv("DB_ENV", "masked").strip().lower()

    if env not in VALID_ENVS:
        raise ValueError(
            f"Invalid DB_ENV '{env}'. Must be one of: {', '.join(sorted(VALID_ENVS))}.\n"
            f"Check your .env file."
        )

    db_path = BASE_DIR / "data" / f"{env}.db"

    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found: {db_path}\n"
            f"Run 'python setup.py' to create and seed the databases."
        )

    return db_path


def get_env_name() -> str:
    """Return the active environment name."""
    return os.getenv("DB_ENV", "masked").strip().lower()
