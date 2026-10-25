"""
test_loader.py — verifies DQ handling and abstain paths.

The DQ logic is silent by design: bad rows are excluded and reported
as warnings. These tests verify both sides — bad rows stay out and
warnings are raised — so investigators are never silently shown
incomplete data.
"""

from loader import build_case_data, load_party, load_transactions


def test_invalid_date_excluded(test_db):
    valid, warnings = load_transactions(test_db, "P001")
    ids = [t["transaction_id"] for t in valid]
    assert "TXN_BAD_DATE" not in ids


def test_invalid_date_raises_warning(test_db):
    _, warnings = load_transactions(test_db, "P001")
    assert any("TXN_BAD_DATE" in w for w in warnings)


def test_missing_amount_excluded(test_db):
    valid, _ = load_transactions(test_db, "P001")
    ids = [t["transaction_id"] for t in valid]
    assert "TXN_BAD_AMT" not in ids


def test_missing_amount_raises_warning(test_db):
    _, warnings = load_transactions(test_db, "P001")
    assert any("TXN_BAD_AMT" in w for w in warnings)


def test_valid_transaction_passes_through(test_db):
    valid, _ = load_transactions(test_db, "P001")
    ids = [t["transaction_id"] for t in valid]
    assert "TXN_OK" in ids


def test_unknown_party_returns_none(test_db):
    result = load_party(test_db, "P999")
    assert result is None


def test_build_case_data_returns_expected_structure(test_db):
    data = build_case_data(test_db, "P001")
    assert set(data.keys()) == {"party", "accounts", "transactions", "alerts", "dq_warnings"}
    assert data["party"]["party_id"] == "P001"
    assert isinstance(data["accounts"], list)
    assert isinstance(data["transactions"], list)
    assert isinstance(data["dq_warnings"], list)
