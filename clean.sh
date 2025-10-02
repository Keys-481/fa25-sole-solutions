
#!/usr/bin/env bash
set -euo pipefail

echo "=== Sole Solutions: clean ==="

VENV_DIR=".venv"

# Remove virtual environment
if [ -d "$VENV_DIR" ]; then
  echo "Removing virtual environment..."
  rm -rf "$VENV_DIR"
fi

# Remove Python cache files
echo "Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete

# Remove build artifacts
echo "Removing build artifacts..."
rm -rf build/ dist/ *.egg-info

# Remove PyInstaller spec file (if generated)
if [ -f SoleSolutions.spec ]; then
  echo "Removing PyInstaller spec..."
  rm -f SoleSolutions.spec
fi

echo "Clean completed successfully."

