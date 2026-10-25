"""
test_data_quality.py — verifies that the CSV seed files are structurally correct.

The other test files assume the CSVs are well-formed. If a column is renamed or
a required field goes blank, setup.py loads it silently and the script produces
wrong output with no error. These tests catch that at the source.
"""

import csv
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent / "data"

EXPECTED_COLUMNS = {
    "party_data": {
        "party_id",
        "full_name",
        "date_of_birth",
        "address",
        "nationality",
        "entity_type",
        "acn",
        "abn",
        "risk_rating",
        "pep_flag",
        "sanctions_flag",
    },
    "account_data": {
        "account_id",
        "party_id",
        "account_type",
        "account_number",
        "account_status",
        "open_date",
        "close_date",
    },
    "transaction_data": {
        "transaction_id",
        "account_number",
        "transaction_date",
        "transaction_amount",
        "transaction_type",
        "transaction_narrative",
        "transaction_code",
        "transaction_code_desc",
        "counterparty_bsb",
        "counterparty_name",
        "counterparty_country",
    },
    "alert_data": {
        "alert_id",
        "party_id",
        "alert_type",
        "alert_date",
        "alert_status",
        "alert_source",
        "description",
    },
}

REQUIRED_FIELDS = {
    "party_data": ["party_id"],
    "account_data": ["account_id", "party_id"],
    "transaction_data": ["transaction_id", "account_number"],
    "alert_data": ["alert_id", "party_id"],
}

ENVIRONMENTS = ["masked", "unmasked"]


@pytest.mark.parametrize("env", ENVIRONMENTS)
@pytest.mark.parametrize("table", list(EXPECTED_COLUMNS.keys()))
def test_csv_has_expected_columns(env, table):
    csv_path = DATA_DIR / env / f"{table}.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        actual = set(csv.DictReader(f).fieldnames or [])
    assert (
        actual == EXPECTED_COLUMNS[table]
    ), f"{env}/{table}.csv columns do not match schema"


def test_masked_and_unmasked_columns_match():
    for table in EXPECTED_COLUMNS:
        cols = {}
        for env in ENVIRONMENTS:
            csv_path = DATA_DIR / env / f"{table}.csv"
            with open(csv_path, newline="", encoding="utf-8") as f:
                cols[env] = set(csv.DictReader(f).fieldnames or [])
        assert (
            cols["masked"] == cols["unmasked"]
        ), f"{table}.csv columns differ between masked and unmasked"


@pytest.mark.parametrize("env", ENVIRONMENTS)
@pytest.mark.parametrize("table,fields", list(REQUIRED_FIELDS.items()))
def test_required_fields_not_blank(env, table, fields):
    csv_path = DATA_DIR / env / f"{table}.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for field in fields:
            assert row.get(
                field
            ), f"{env}/{table}.csv has a blank '{field}' — required field"
