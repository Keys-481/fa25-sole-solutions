# tests/test_app_imports.py

from sole_solutions.ui.app import run_ui
import main as main_mod  # PYTHONPATH=src is set in test.sh

def test_run_ui_is_callable():
    assert callable(run_ui)

def test_main_entrypoint_exists():
    assert hasattr(main_mod, "main") and callable(main_mod.main)