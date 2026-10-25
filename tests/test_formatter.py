"""
test_formatter.py — verifies that the formatter produces the correct output.

The formatter is the only thing an investigator sees. These tests guard
against a code change silently breaking a key signal in the output.
"""

from formatter import (
    CASH_DEPOSIT_CODE,
    _flag,
    _fmt_amount,
    format_case_summary,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_party(risk="LOW", pep="N", sanctions="N"):
    return {
        "party_id": "P001",
        "full_name": "Test Person",
        "date_of_birth": "1990-01-01",
        "address": "1 Test St",
        "nationality": "Australian",
        "entity_type": "INDIVIDUAL",
        "acn": None,
        "abn": None,
        "risk_rating": risk,
        "pep_flag": pep,
        "sanctions_flag": sanctions,
    }


def _make_transaction(
    txn_id,
    amount,
    code="001",
    desc="Purchase",
    country=None,
    txn_type="DEBIT",
    date="2024-10-01",
):
    return {
        "transaction_id": txn_id,
        "account_number": "062000-99999999",
        "transaction_date": date,
        "transaction_amount": amount,
        "transaction_type": txn_type,
        "transaction_narrative": "Test",
        "transaction_code": code,
        "transaction_code_desc": desc,
        "counterparty_bsb": None,
        "counterparty_name": None,
        "counterparty_country": country,
    }


def _make_case_data(party=None, transactions=None, alerts=None, dq_warnings=None):
    return {
        "party": party or _make_party(),
        "accounts": [
            {
                "account_id": "ACC001",
                "party_id": "P001",
                "account_type": "TRANSACTION",
                "account_number": "062000-99999999",
                "account_status": "ACTIVE",
                "open_date": "2020-01-01",
                "close_date": None,
            }
        ],
        "transactions": transactions or [],
        "alerts": alerts or [],
        "dq_warnings": dq_warnings or [],
    }


def _run(case_data):
    return format_case_summary(case_data, "P001", None, None, "unmasked", "2026-10-25")


# ---------------------------------------------------------------------------
# Helper function unit tests
# ---------------------------------------------------------------------------


def test_fmt_amount_none_returns_dash():
    assert _fmt_amount(None) == "—"


def test_fmt_amount_formats_correctly():
    result = _fmt_amount(9500.0)
    assert "AUD" in result
    assert "9,500.00" in result


def test_flag_y_returns_flagged():
    assert _flag("Y") == "YES [!]"


def test_flag_n_returns_no():
    assert _flag("N") == "No"


# ---------------------------------------------------------------------------
# Golden output — key signals present
# ---------------------------------------------------------------------------


def test_section_headers_present():
    output = _run(_make_case_data())
    for header in (
        "RISK SIGNALS",
        "PARTY PROFILE",
        "LINKED ACCOUNTS",
        "TRANSACTIONS",
        "ALERTS",
    ):
        assert header in output


def test_pep_flag_renders_correctly():
    output = _run(_make_case_data(party=_make_party(pep="Y", risk="HIGH")))
    assert "YES [!]" in output
    assert "HIGH" in output


def test_footer_present():
    output = _run(_make_case_data())
    assert "Decision reserved for the investigator" in output


def test_dq_warning_appears_in_output():
    case_data = _make_case_data(
        dq_warnings=["Transaction TXN_BAD excluded — invalid date"]
    )
    output = _run(case_data)
    assert "DATA QUALITY WARNINGS" in output
    assert "TXN_BAD" in output


def test_dq_section_absent_when_no_warnings():
    output = _run(_make_case_data(dq_warnings=[]))
    assert "DATA QUALITY WARNINGS" not in output


# ---------------------------------------------------------------------------
# Structuring indicator
# ---------------------------------------------------------------------------


def test_structuring_indicator_fires_for_two_near_threshold_deposits():
    txns = [
        _make_transaction(
            "T1", 9600.0, code=CASH_DEPOSIT_CODE, desc="Cash Deposit", txn_type="CREDIT"
        ),
        _make_transaction(
            "T2", 9700.0, code=CASH_DEPOSIT_CODE, desc="Cash Deposit", txn_type="CREDIT"
        ),
    ]
    output = _run(_make_case_data(transactions=txns))
    assert "STRUCTURING INDICATOR" in output


def test_structuring_indicator_does_not_fire_for_one_deposit():
    txns = [
        _make_transaction(
            "T1", 9600.0, code=CASH_DEPOSIT_CODE, desc="Cash Deposit", txn_type="CREDIT"
        ),
    ]
    output = _run(_make_case_data(transactions=txns))
    assert "STRUCTURING INDICATOR" not in output


def test_structuring_indicator_does_not_fire_above_threshold():
    txns = [
        _make_transaction(
            "T1",
            10500.0,
            code=CASH_DEPOSIT_CODE,
            desc="Cash Deposit",
            txn_type="CREDIT",
        ),
        _make_transaction(
            "T2",
            11000.0,
            code=CASH_DEPOSIT_CODE,
            desc="Cash Deposit",
            txn_type="CREDIT",
        ),
    ]
    output = _run(_make_case_data(transactions=txns))
    assert "STRUCTURING INDICATOR" not in output


# ---------------------------------------------------------------------------
# High-risk country flag
# ---------------------------------------------------------------------------


def test_high_risk_country_flagged():
    txns = [_make_transaction("T1", 25000.0, country="Cayman Islands")]
    output = _run(_make_case_data(transactions=txns))
    assert "High-Risk Country Activity" in output


def test_domestic_country_not_flagged():
    txns = [_make_transaction("T1", 500.0, country="Australia")]
    output = _run(_make_case_data(transactions=txns))
    assert "High-Risk Country Activity" not in output
