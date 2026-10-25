"""
loader.py — executes the 4 SQL queries and returns structured data for a given party.
Handles data quality issues: invalid dates and missing amounts are flagged, not silently dropped.
"""

import logging
from datetime import date
from pathlib import Path
from typing import Any

from db import run_query

logger = logging.getLogger("loader")

QUERIES_DIR = Path(__file__).parent / "queries"
CASH_REPORTING_THRESHOLD = 10_000.00  # AUD — illustrative, not regulatory guidance
STRUCTURING_WINDOW = 500.00  # Amount below threshold to flag as near-threshold


def _is_valid_date(value: str | None) -> bool:
    """Return True if value is a parseable ISO date string."""
    if not value:
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def load_party(db_path: Path, party_id: str) -> dict | None:
    """Return party profile or None if not found."""
    rows = run_query(
        db_path,
        QUERIES_DIR / "get_party.sql",
        {"party_id": party_id},
    )
    return rows[0] if rows else None


def load_accounts(db_path: Path, party_id: str) -> list[dict]:
    """Return all accounts for a party."""
    return run_query(
        db_path,
        QUERIES_DIR / "get_accounts.sql",
        {"party_id": party_id},
    )


def load_transactions(
    db_path: Path,
    party_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
) -> tuple[list[dict], list[str]]:
    """
    Return (valid_transactions, dq_warnings).
    Rows with invalid dates or missing amounts are excluded and reported as warnings.
    """
    rows = run_query(
        db_path,
        QUERIES_DIR / "get_transactions.sql",
        {"party_id": party_id, "from_date": from_date, "to_date": to_date},
    )

    valid, warnings = [], []
    for row in rows:
        issues = []

        if not _is_valid_date(row.get("transaction_date")):
            issues.append(f"invalid date '{row.get('transaction_date')}'")

        if row.get("transaction_amount") is None:
            issues.append("missing transaction_amount")

        if issues:
            warnings.append(
                f"Transaction {row['transaction_id']} excluded — {'; '.join(issues)}"
            )
            logger.warning(
                "transaction_data — %s excluded: %s",
                row["transaction_id"],
                "; ".join(issues),
            )
        else:
            valid.append(row)

    return valid, warnings


def load_alerts(db_path: Path, party_id: str) -> list[dict]:
    """Return all alerts for a party."""
    return run_query(
        db_path,
        QUERIES_DIR / "get_alerts.sql",
        {"party_id": party_id},
    )


def build_case_data(
    db_path: Path,
    party_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    """
    Load all data for a party and return a structured dict ready for formatting.
    Returns None for party if not found (caller handles the abstain path).
    """
    party = load_party(db_path, party_id)
    accounts = load_accounts(db_path, party_id)
    transactions, dq_warnings = load_transactions(db_path, party_id, from_date, to_date)
    alerts = load_alerts(db_path, party_id)

    return {
        "party": party,
        "accounts": accounts,
        "transactions": transactions,
        "alerts": alerts,
        "dq_warnings": dq_warnings,
    }
