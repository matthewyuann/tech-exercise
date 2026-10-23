"""
db.py — SQLite connection and parameterised query execution.
Logs row counts only — no PII is written to logs.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger("db")


def run_query(db_path: Path, sql_path: Path, params: dict[str, Any]) -> list[dict]:
    """
    Execute a SQL file against the database and return results as a list of dicts.
    Logs the query name and row count. Never logs parameter values.
    """
    sql = sql_path.read_text(encoding="utf-8")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        cursor = conn.execute(sql, params)
        rows = [dict(row) for row in cursor.fetchall()]
        logger.info("%-30s %d row(s) returned", sql_path.name, len(rows))
        return rows
    finally:
        conn.close()
