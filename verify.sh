#!/usr/bin/env bash
# verify.sh — runs all checks in one command.
# Usage: bash verify.sh
# Requires: venv activated and dependencies installed (pip install -r requirements.txt)
set -euo pipefail

echo "=== AML Case Summary — verify ==="
echo ""

echo "--- Seeding databases ---"
python setup.py
echo ""

echo "--- Lint (ruff) ---"
python -m ruff check .
echo ""

echo "--- Tests (pytest) ---"
python -m pytest tests/ -v
echo ""

echo "=== All checks passed ==="
