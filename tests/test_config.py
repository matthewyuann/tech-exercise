"""
test_config.py — verifies that the config module fails loudly on misconfiguration.

Without these guards, a wrong DB_ENV or a missing database produces a confusing
Python error deep in the call stack. The config module catches both early.
"""

import pytest

from config import get_db_path


def test_invalid_env_raises_value_error(monkeypatch):
    monkeypatch.setenv("DB_ENV", "production")
    with pytest.raises(ValueError, match="Invalid DB_ENV"):
        get_db_path()


def test_missing_db_raises_file_not_found(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_ENV", "masked")
    with pytest.raises(FileNotFoundError, match="setup.py"):
        get_db_path(base_dir=tmp_path)
