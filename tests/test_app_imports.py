# tests/test_app_imports.py
import importlib


def test_run_ui_is_callable():
    # Import inside the test so CI environments without Tk can still collect tests.
    app_mod = importlib.import_module("sole_solutions.ui.app")
    assert hasattr(app_mod, "run_ui") and callable(app_mod.run_ui)


def test_main_entrypoint_exists():
    # PYTHONPATH=src is set in test.sh, so this import resolves.
    import main as main_mod
    assert hasattr(main_mod, "main") and callable(main_mod.main)
