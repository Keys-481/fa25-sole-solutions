#!/usr/bin/env bash
set -euo pipefail

echo "=== Sole Solutions: build ==="

VENV_DIR=".venv"

# Pick a Python launcher
if command -v python3 >/dev/null 2>&1; then PYTHON=python3
elif command -v py >/dev/null 2>&1; then PYTHON="py -3"
elif command -v python >/dev/null 2>&1; then PYTHON=python
else
  echo "Error: Python not found" >&2
  exit 1
fi

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
  $PYTHON -m venv "$VENV_DIR"
fi

# Resolve venv python path (POSIX vs Windows)
if [ -x "$VENV_DIR/bin/python" ]; then
  VENV_PY="$VENV_DIR/bin/python"
elif [ -x "$VENV_DIR/Scripts/python.exe" ]; then
  VENV_PY="$VENV_DIR/Scripts/python.exe"
else
  echo "Error: venv python not found" >&2
  exit 2
fi

# Upgrade pip and install deps
$VENV_PY -m pip install --upgrade pip
[ -f requirements.txt ] && $VENV_PY -m pip install -r requirements.txt
[ -f requirements-dev.txt ] && $VENV_PY -m pip install -r requirements-dev.txt

# --- Optional packaging (only when PACKAGE=1) ---
if [ "${PACKAGE:-0}" = "1" ]; then
  echo "Packaging enabled (PyInstaller)..."
  $VENV_PY -m pip install pyinstaller
  # Build a single-file GUI app from your entry point
  $VENV_PY -m PyInstaller \
    --name "SoleSolutions" \
    --onefile \
    --noconsole \
    src/main.py
  echo "Packaged artifacts are in ./dist/"
fi

echo "Build completed successfully."
