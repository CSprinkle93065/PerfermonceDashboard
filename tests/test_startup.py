"""
Startup Smoke Test — LL-010 (CRITICAL)

Imports every src module and constructs MainWindow headlessly
using QT_QPA_PLATFORM=offscreen.
"""

import os
import sys
from pathlib import Path

# Ensure QT_QPA_PLATFORM is offscreen before PyQt6 is imported
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

# Add project root to path so `src` is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_import_all_src_modules() -> None:
    """Every .py file in src/ must import without raising."""
    src_dir = PROJECT_ROOT / "src"
    if not src_dir.exists():
        pytest.skip("src/ directory does not exist yet — source code not implemented")

    modules = sorted(src_dir.glob("*.py"))
    imported = []

    for mod_path in modules:
        if mod_path.name.startswith("_"):
            continue
        module_name = f"src.{mod_path.stem}"
        try:
            __import__(module_name)
            imported.append(module_name)
        except Exception as exc:
            pytest.fail(f"Import failed for {module_name}: {exc}")

    assert len(imported) > 0, "No src modules found to import"


def test_construct_main_window_headlessly() -> None:
    """MainWindow must instantiate without crashing in offscreen mode."""
    from PyQt6.QtWidgets import QApplication, QMainWindow

    # QApplication singleton may already exist from prior tests
    app = QApplication.instance() or QApplication(sys.argv)

    try:
        from src.main_window import MainWindow
        from src.models import Settings
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    settings = Settings()
    window = MainWindow(settings)

    assert isinstance(window, QMainWindow), "MainWindow must be a QMainWindow subclass"
    assert window is not None, "MainWindow instance must not be None"
