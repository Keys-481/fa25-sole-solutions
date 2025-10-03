#!/usr/bin/env bash
set -euo pipefail

echo "=== Sole Solutions: build ==="

VENV_DIR=".venv"

# Detect platform (helps on Git Bash/Windows)
is_macos=false
is_windows=false
case "${OSTYPE:-}" in
  darwin*) is_macos=true ;;
  msys*|cygwin*) is_windows=true ;;  # Git Bash / Cygwin
esac
# Fallback for some shells on Windows
if [[ "${OS:-}" == "Windows_NT" ]]; then
  is_windows=true
fi

# Choose a Python launcher
choose_python() {
  # Prefer explicit 3.12 if available
  if command -v py >/dev/null 2>&1; then
    if py -3.12 -V >/dev/null 2>&1; then echo "py -3.12"; return; fi
    echo "py -3"
    return
  fi
  if command -v python3.12 >/dev/null 2>&1; then echo "python3.12"; return; fi
  if command -v python3 >/dev/null 2>&1; then echo "python3"; return; fi
  if command -v python >/dev/null 2>&1; then echo "python"; return; fi
  echo ""
}

PYTHON="$(choose_python)"
if [[ -z "$PYTHON" ]]; then
  echo "Error: Python not found on PATH." >&2
  exit 1
fi

# Create venv if missing (prefer 3.12 if available)
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment ($VENV_DIR) using: $PYTHON"
  $PYTHON -m venv "$VENV_DIR"
fi

# Resolve venv python path (POSIX vs Windows)
if [[ -x "$VENV_DIR/bin/python" ]]; then
  VENV_PY="$VENV_DIR/bin/python"
elif [[ -x "$VENV_DIR/Scripts/python.exe" ]]; then
  VENV_PY="$VENV_DIR/Scripts/python.exe"
else
  echo "Error: venv python not found" >&2
  exit 2
fi

# Verify venv version; enforce 3.12 for packaging
VENV_VER="$("$VENV_PY" -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "Using venv Python $VENV_VER -> $VENV_PY"

if ! "$VENV_PY" -m pip --version >/dev/null 2>&1; then
  echo "Bootstrapping pip in venv..."
  "$VENV_PY" -m ensurepip --upgrade || true
fi

# Upgrade pip and install deps
"$VENV_PY" -m pip install --upgrade pip
[[ -f requirements.txt ]] && "$VENV_PY" -m pip install -r requirements.txt
[[ -f requirements-dev.txt ]] && "$VENV_PY" -m pip install -r requirements-dev.txt

# Packaging (PyInstaller)
if [[ "${PACKAGE:-0}" == "1" ]]; then
  # Require 3.12 for packaging (avoids Tk issues on Win/mac)
  if [[ "$VENV_VER" != "3.12" ]]; then
    echo "ERROR: Packaging requires Python 3.12, but venv is $VENV_VER."
    echo "Fix: remove .venv and recreate with Python 3.12, e.g.:"
    echo "  # Windows (PowerShell):  Remove-Item -Recurse -Force .venv; py -3.12 -m venv .venv"
    echo "  # Git Bash:             rm -rf .venv; py -3.12 -m venv .venv"
    exit 3
  fi

  echo "Packaging enabled (PyInstaller)..."
  "$VENV_PY" -m pip install pyinstaller

  if $is_macos; then
    # macOS: proper .app (windowed, onedir)
    "$VENV_PY" -m PyInstaller \
      --name "SoleSolutions" \
      --windowed \
      --onedir \
      --osx-bundle-identifier "edu.bsu.cobr.solesolutions" \
      --noconfirm \
      src/main.py
  elif $is_windows; then
    # Windows: robust onefile with Tk bundled
    "$VENV_PY" -m PyInstaller \
      --name "SoleSolutions" \
      --windowed \
      --onefile \
      --collect-all tkinter \
      --noconfirm \
      src/main.py
  else
    # Linux: simple onefile
    "$VENV_PY" -m PyInstaller \
      --name "SoleSolutions" \
      --onefile \
      --noconfirm \
      src/main.py
  fi

  echo "Packaged artifacts are in ./dist/"
fi

echo "Build completed successfully."
