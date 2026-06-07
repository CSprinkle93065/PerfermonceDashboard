"""
System Theme Tests

Covers theme detection (QStyleHints.colorScheme or registry fallback)
and application of theme colors to widgets.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_theme_detection_uses_color_scheme_on_qt65_plus(qapp) -> None:
    """TC-THEME-01: apply_system_theme must react to QStyleHints.colorScheme == Dark."""
    try:
        from src.api import apply_system_theme
        from src.main_window import MainWindow
        from src.models import Settings
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    window = MainWindow(Settings())

    # Mock styleHints to report Dark
    mock_hints = MagicMock()
    mock_hints.colorScheme.return_value = Qt.ColorScheme.Dark

    with patch.object(QApplication, "styleHints", return_value=mock_hints):
        apply_system_theme(window)

    stylesheet = (window.styleSheet() or "").lower()
    assert (
        "background-color: #1e1e1e" in stylesheet
        or "color: #ffffff" in stylesheet
        or "dark" in stylesheet
    ), "Dark theme stylesheet indicators not found"


def test_theme_detection_falls_back_to_registry_light() -> None:
    """TC-THEME-02: When colorScheme is Unknown, registry AppsUseLightTheme=1 => light theme."""
    try:
        from src.api import apply_system_theme
        from src.main_window import MainWindow
        from src.models import Settings
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    window = MainWindow(Settings())

    mock_hints = MagicMock()
    mock_hints.colorScheme.return_value = Qt.ColorScheme.Unknown

    # Mock Windows registry read returning light mode (1)
    mock_reg_value = MagicMock()
    mock_reg_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_reg_value.__exit__ = MagicMock(return_value=False)

    with patch("src.api.winreg.OpenKey", return_value=MagicMock()):
        with patch("src.api.winreg.QueryValueEx", return_value=(1, "REG_DWORD")):
            with patch.object(QApplication, "styleHints", return_value=mock_hints):
                apply_system_theme(window)

    stylesheet = (window.styleSheet() or "").lower()
    assert (
        "background-color: #f0f0f0" in stylesheet
        or "color: #000000" in stylesheet
        or "light" in stylesheet
    ), "Light theme stylesheet indicators not found"


def test_theme_change_applied_to_widget_colors(qapp) -> None:
    """TC-THEME-03: After apply_system_theme, at least one widget must reflect the theme."""
    try:
        from src.api import apply_system_theme
        from src.main_window import MainWindow
        from src.models import Settings
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    window = MainWindow(Settings())

    mock_hints = MagicMock()
    mock_hints.colorScheme.return_value = Qt.ColorScheme.Dark

    with patch.object(QApplication, "styleHints", return_value=mock_hints):
        apply_system_theme(window)

    # Either the window has a non-empty stylesheet or its palette darkened
    has_stylesheet = bool(window.styleSheet())
    try:
        from PyQt6.QtGui import QPalette
        bg_lightness = window.palette().color(QPalette.ColorRole.Window).lightness()
        is_dark = bg_lightness < 128
    except Exception:
        is_dark = False

    assert has_stylesheet or is_dark, "Theme was not applied to widget colors"
