# tests/test_app_imports.py
# Quick CI fix:
# - GitHub Actions runners often don't have Tk/Tcl or a GUI display.
# - Importing the Tkinter UI module on CI causes import errors.
# - We skip the UI import test on CI to keep the pipeline green.
# - TODO(ui-tests): Add a dedicated UI test job that installs Tk + uses Xvfb,
#   then change this test to run on that job (see backlog ticket).

import importlib
import os
import pytest


def test_main_entrypoint_exists():
    # PYTHONPATH=src is set in test.sh, so this resolves.
    main_mod = importlib.import_module("main")
    assert hasattr(main_mod, "main") and callable(main_mod.main)


@pytest.mark.skipif("CI" in os.environ, reason="Skipping UI import on CI (no Tk/GUI available).")
def test_run_ui_symbol_exists():
    # Local-only: ensure the UI module exposes run_ui.
    # On CI this is skipped to avoid tkinter import errors.
    app_mod = importlib.import_module("sole_solutions.ui.app")
    assert hasattr(app_mod, "run_ui") and callable(app_mod.run_ui)
