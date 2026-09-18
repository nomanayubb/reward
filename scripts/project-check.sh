#!/usr/bin/env bash
# Standard project validation. Run from the repository root.
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-.venv/bin/python}"
if [ ! -x "$PYTHON" ]; then
    PYTHON="python"
fi

echo "==> Django system check"
"$PYTHON" manage.py check

echo "==> Pending migrations"
"$PYTHON" manage.py makemigrations --check --dry-run

echo "==> Tests"
"$PYTHON" -m pytest

if "$PYTHON" -m ruff --version >/dev/null 2>&1; then
    echo "==> Ruff"
    "$PYTHON" -m ruff check .
else
    echo "==> Ruff not installed (skipping)"
fi

echo "==> All checks passed"
