#!/usr/bin/env bash
set -euo pipefail

echo "=== Sole Solutions: tests ==="

export PYTHONPATH=src
VENV_DIR=".venv"

# Resolve venv python
if [ -x "$VENV_DIR/bin/python" ]; then
  VENV_PY="$VENV_DIR/bin/python"
elif [ -x "$VENV_DIR/Scripts/python.exe" ]; then
  VENV_PY="$VENV_DIR/Scripts/python.exe"
else
  echo "Error: venv python not found. Run ./build.sh first." >&2
  exit 2
fi

mod_exists () {
  "$VENV_PY" -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('$1') else 1)" >/dev/null 2>&1
}

# Run unit tests if any
if compgen -G "tests/test_*.py" >/dev/null 2>&1 || compgen -G "tests/**/*_test.py" >/dev/null 2>&1; then
  "$VENV_PY" -m pytest --maxfail=1 --disable-warnings -q
else
  echo "(no tests found; skipping pytest)"
fi

# Optional static checks if installed
if mod_exists ruff; then "$VENV_PY" -m ruff check .; else echo "(ruff not installed; skipping)"; fi
if mod_exists mypy; then "$VENV_PY" -m mypy -p sole_solutions -m main; else echo "(mypy not installed; skipping)"; fi

echo "All tests completed."
