"""
conftest.py — shared pytest fixtures.

Provides a controlled SQLite database seeded with known test rows,
independent of setup.py or the real seed data.
"""

import sqlite3

import pytest

from setup import SQLITE_SCHEMA

TEST_ACCOUNT = "062000-99999999"
TEST_PARTY = "P001"


@pytest.fixture
def test_db(tmp_path):
    """
    Temporary SQLite database with a known set of rows.

    Includes: one valid party, one account, a mix of valid and
    invalid transactions, and one alert.
    """
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(SQLITE_SCHEMA)
    conn.execute("PRAGMA foreign_keys = OFF")

    conn.execute(
        "INSERT INTO party_data VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            TEST_PARTY,
            "Test Person",
            "1990-01-01",
            "1 Test St",
            "Australian",
            "INDIVIDUAL",
            None,
            None,
            "HIGH",
            "Y",
            "N",
        ),
    )
    conn.execute(
        "INSERT INTO account_data VALUES (?,?,?,?,?,?,?)",
        (
            "ACC001",
            TEST_PARTY,
            "TRANSACTION",
            TEST_ACCOUNT,
            "ACTIVE",
            "2020-01-01",
            None,
        ),
    )

    # Valid transaction
    conn.execute(
        "INSERT INTO transaction_data VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "TXN_OK",
            TEST_ACCOUNT,
            "2024-10-01",
            500.00,
            "DEBIT",
            "Test purchase",
            "001",
            "Purchase",
            None,
            None,
            None,
        ),
    )
    # Invalid date
    conn.execute(
        "INSERT INTO transaction_data VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "TXN_BAD_DATE",
            TEST_ACCOUNT,
            "2024-13-45",
            200.00,
            "DEBIT",
            "Bad date txn",
            "001",
            "Purchase",
            None,
            None,
            None,
        ),
    )
    # Missing amount
    conn.execute(
        "INSERT INTO transaction_data VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "TXN_BAD_AMT",
            TEST_ACCOUNT,
            "2024-10-02",
            None,
            "DEBIT",
            "Missing amount",
            "001",
            "Purchase",
            None,
            None,
            None,
        ),
    )
    # Two near-threshold cash deposits (triggers structuring indicator)
    conn.execute(
        "INSERT INTO transaction_data VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "TXN_STRUCT1",
            TEST_ACCOUNT,
            "2024-10-03",
            9600.00,
            "CREDIT",
            "Cash deposit",
            "003",
            "Cash Deposit",
            None,
            None,
            None,
        ),
    )
    conn.execute(
        "INSERT INTO transaction_data VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "TXN_STRUCT2",
            TEST_ACCOUNT,
            "2024-10-04",
            9700.00,
            "CREDIT",
            "Cash deposit",
            "003",
            "Cash Deposit",
            None,
            None,
            None,
        ),
    )

    conn.execute(
        "INSERT INTO alert_data VALUES (?,?,?,?,?,?,?)",
        (
            "ALT001",
            TEST_PARTY,
            "STRUCTURING",
            "2024-10-15",
            "OPEN",
            "SYSTEM",
            "Test alert",
        ),
    )

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()
    return db_path
