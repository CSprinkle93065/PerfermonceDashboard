"""
Window Behavior Tests

Covers Always on Top flag, minimize/restore cycle, and frameless drag.
"""

import os
import sys
from pathlib import Path

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


def _build_main_window(always_on_top: bool = True):
    try:
        from src.main_window import MainWindow
        from src.models import Settings
        from src.api import build_main_window
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    settings = Settings(always_on_top=always_on_top)
    return build_main_window(settings)


def test_always_on_top_applied_on_launch(qapp) -> None:
    """TC-WIN-01: Window flags must include WindowStaysOnTopHint when enabled."""
    window = _build_main_window(always_on_top=True)
    flags = window.windowFlags()
    assert flags & Qt.WindowType.WindowStaysOnTopHint, "WindowStaysOnTopHint must be set on launch"


def test_always_on_top_removed_on_minimize(qapp) -> None:
    """TC-WIN-02: Minimize must strip WindowStaysOnTopHint."""
    window = _build_main_window(always_on_top=True)

    try:
        from src.api import minimize_window
    except ImportError as exc:
        pytest.skip(f"API not yet implemented: {exc}")

    # Create a dummy tray icon if needed
    tray_icon = None
    try:
        from PyQt6.QtWidgets import QSystemTrayIcon
        tray_icon = QSystemTrayIcon()
    except Exception:
        pass

    minimize_window(window, tray_icon)
    flags = window.windowFlags()
    assert not (flags & Qt.WindowType.WindowStaysOnTopHint), (
        "WindowStaysOnTopHint must be removed before minimize"
    )


def test_always_on_top_reapplied_on_restore(qapp) -> None:
    """TC-WIN-03: Restore must re-apply WindowStaysOnTopHint."""
    window = _build_main_window(always_on_top=True)

    try:
        from src.api import minimize_window, restore_window
    except ImportError as exc:
        pytest.skip(f"API not yet implemented: {exc}")

    tray_icon = None
    try:
        from PyQt6.QtWidgets import QSystemTrayIcon
        tray_icon = QSystemTrayIcon()
    except Exception:
        pass

    minimize_window(window, tray_icon)
    restore_window(window)
    flags = window.windowFlags()
    assert flags & Qt.WindowType.WindowStaysOnTopHint, (
        "WindowStaysOnTopHint must be re-applied on restore"
    )


def test_frameless_window_drag_behavior(qapp) -> None:
    """TC-WIN-04: Simulated drag on header bar must move the window."""
    window = _build_main_window(always_on_top=True)
    window.show()
    qapp.processEvents()

    old_pos = window.pos()
    # Simulate press + move on the header bar region (assumed at top-left)
    press_event = None
    move_event = None
    try:
        from PyQt6.QtCore import QEvent, QPoint
        from PyQt6.QtGui import QMouseEvent
    except ImportError:
        pytest.skip("PyQt6 components unavailable")

    try:
        from PyQt6.QtCore import QPointF
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(10, 5),
            QPointF(10, 5),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(60, 35),
            QPointF(60, 35),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    except TypeError:
        # PyQt6 QMouseEvent signature may vary by minor version
        pytest.skip("QMouseEvent constructor signature mismatch — update test for installed PyQt6 version")

    if hasattr(window, "mousePressEvent") and press_event:
        window.mousePressEvent(press_event)
    if hasattr(window, "mouseMoveEvent") and move_event:
        window.mouseMoveEvent(move_event)

    qapp.processEvents()
    new_pos = window.pos()

    assert new_pos.x() - old_pos.x() == 50, f"Window X did not move by 50 (moved by {new_pos.x() - old_pos.x()})"
    assert new_pos.y() - old_pos.y() == 30, f"Window Y did not move by 30 (moved by {new_pos.y() - old_pos.y()})"
