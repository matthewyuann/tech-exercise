"""
setup.py — creates and seeds the masked and unmasked SQLite databases from CSV files.

Run once before using main.py:
    python setup.py

Safe to re-run — existing data is cleared and reloaded.
"""

import csv
import logging
import sqlite3
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("setup")

DATA_DIR = Path(__file__).parent / "data"
ENVIRONMENTS = ["unmasked", "masked"]
TABLES = ["party_data", "account_data", "transaction_data", "alert_data"]

# SQLite-equivalent schema (production target is Cloud Spanner — see schema.sql)
SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS party_data (
    party_id        TEXT    NOT NULL PRIMARY KEY,
    full_name       TEXT,
    date_of_birth   TEXT,
    address         TEXT,
    nationality     TEXT,
    entity_type     TEXT    NOT NULL,
    acn             TEXT,
    abn             TEXT,
    risk_rating     TEXT    NOT NULL,
    pep_flag        TEXT    NOT NULL,
    sanctions_flag  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS account_data (
    account_id      TEXT    NOT NULL PRIMARY KEY,
    party_id        TEXT    NOT NULL,
    account_type    TEXT    NOT NULL,
    account_number  TEXT    NOT NULL UNIQUE,
    account_status  TEXT    NOT NULL,
    open_date       TEXT    NOT NULL,
    close_date      TEXT,
    FOREIGN KEY (party_id) REFERENCES party_data (party_id)
);

CREATE TABLE IF NOT EXISTS transaction_data (
    transaction_id          TEXT    NOT NULL PRIMARY KEY,
    account_number          TEXT    NOT NULL,
    transaction_date        TEXT    NOT NULL,
    transaction_amount      REAL,
    transaction_type        TEXT    NOT NULL,
    transaction_narrative   TEXT,
    transaction_code        TEXT    NOT NULL,
    transaction_code_desc   TEXT    NOT NULL,
    counterparty_bsb        TEXT,
    counterparty_name       TEXT,
    counterparty_country    TEXT,
    FOREIGN KEY (account_number) REFERENCES account_data (account_number)
);

CREATE TABLE IF NOT EXISTS alert_data (
    alert_id        TEXT    NOT NULL PRIMARY KEY,
    party_id        TEXT    NOT NULL,
    alert_type      TEXT    NOT NULL,
    alert_date      TEXT    NOT NULL,
    alert_status    TEXT    NOT NULL,
    alert_source    TEXT    NOT NULL,
    description     TEXT,
    FOREIGN KEY (party_id) REFERENCES party_data (party_id)
);
"""


def seed_table(conn: sqlite3.Connection, table: str, csv_path: Path) -> int:
    """Load a CSV into a table. Returns the number of rows inserted."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        logger.warning("%-20s no rows found in %s", table, csv_path.name)
        return 0

    columns = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in columns)
    col_names = ", ".join(columns)

    conn.execute(f"DELETE FROM {table}")

    inserted = 0
    for row in rows:
        # Empty CSV cells become NULL in the database
        values = [v if v != "" else None for v in row.values()]
        conn.execute(
            f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", values
        )
        inserted += 1

    return inserted


def setup_environment(env: str) -> None:
    """Create and seed the SQLite database for one environment."""
    db_path = DATA_DIR / f"{env}.db"
    csv_dir = DATA_DIR / env

    logger.info("%-10s creating database at %s", env, db_path)

    conn = sqlite3.connect(db_path)
    conn.executescript(SQLITE_SCHEMA)

    # Delete in reverse dependency order before reseeding
    conn.execute("PRAGMA foreign_keys = OFF")
    for table in reversed(TABLES):
        conn.execute(f"DELETE FROM {table}")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()

    for table in TABLES:
        csv_path = csv_dir / f"{table}.csv"

        if not csv_path.exists():
            conn.close()
            raise FileNotFoundError(
                f"Seed file not found: {csv_path}\n"
                f"Expected data/{env}/{table}.csv"
            )

        count = seed_table(conn, table, csv_path)
        conn.commit()
        logger.info("%-10s %-25s %d rows loaded", env, table, count)

    conn.close()
    logger.info("%-10s database ready\n", env)


def main() -> None:
    for env in ENVIRONMENTS:
        setup_environment(env)
    logger.info("Setup complete — run: python main.py --party-id <id> [--env masked|unmasked]")


if __name__ == "__main__":
    main()
