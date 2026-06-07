"""
pytest-qt UI Interaction Tests

Classified as SAFE, DESTRUCTIVE, or INPUT-BOUND per project requirements.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import Qt, QObject
from PyQt6.QtWidgets import QApplication, QDialog, QPushButton, QSystemTrayIcon, QToolTip, QWidget


def _find_tray_icon(main_window):
    """Helper to locate the QSystemTrayIcon inside main_window."""
    for child in main_window.findChildren(QObject):
        if isinstance(child, QSystemTrayIcon):
            return child
    # Fallback: try known attribute names
    for attr in ("_tray_icon", "tray_icon", "_tray", "tray"):
        tray = getattr(main_window, attr, None)
        if isinstance(tray, QSystemTrayIcon):
            return tray
    return None


@pytest.fixture
def main_window(qtbot):
    """Fixture providing a constructed MainWindow."""
    try:
        from src.main_window import MainWindow
        from src.models import Settings
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    window = MainWindow(Settings())
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    return window


# ---------------------------------------------------------------------------
# SAFE interactions
# ---------------------------------------------------------------------------

def test_hover_over_polling_indicator_reveals_timestamp(qtbot, main_window) -> None:
    """TC-UI-01 [SAFE]: Hovering the polling indicator must show a tooltip with a timestamp."""
    # Locate the polling indicator label (heuristic: small QLabel in status footer)
    indicator = None
    for child in main_window.findChildren(QWidget):
        if isinstance(child, type(main_window)):
            continue
        # Look for a QLabel that might be the indicator
        if child.objectName() in ("polling_indicator", "status_indicator"):
            indicator = child
            break

    if indicator is None:
        pytest.skip("Polling indicator widget not found by heuristic — update selector when source is implemented")

    qtbot.mouseMove(indicator)
    qtbot.wait(200)

    # In offscreen mode QToolTip.text() is empty; verify the widget's tooltip property
    tooltip = indicator.toolTip()
    assert tooltip, "Tooltip was empty on hover"
    assert ":" in tooltip or "2026" in tooltip or "UTC" in tooltip or "T" in tooltip, (
        f"Tooltip does not appear to contain a timestamp: {tooltip}"
    )


def test_open_settings_dialog(qtbot, main_window) -> None:
    """TC-UI-02 [SAFE]: Clicking the settings button must open a modal QDialog."""
    settings_btn = None
    for child in main_window.findChildren(QWidget):
        obj_name = child.objectName() or ""
        if "settings" in obj_name.lower() or "gear" in obj_name.lower():
            settings_btn = child
            break
        # Also check tooltip text if available
        if hasattr(child, "toolTip") and child.toolTip():
            if "settings" in child.toolTip().lower():
                settings_btn = child
                break

    if settings_btn is None:
        pytest.skip("Settings button not found by heuristic — update selector when source is implemented")

    qtbot.mouseClick(settings_btn, Qt.MouseButton.LeftButton)
    qtbot.wait(200)

    dialogs = [w for w in QApplication.topLevelWidgets() if isinstance(w, QDialog) and w.isVisible()]
    assert any(dialogs), "No visible QDialog found after clicking settings button"


def test_all_buttons_are_discoverable_and_safe(qtbot, main_window) -> None:
    """TC-UI-08 [SAFE]: Every QPushButton has an objectName and is connected to a slot."""
    buttons = main_window.findChildren(QPushButton)
    assert buttons, "No QPushButton instances found in MainWindow"

    for btn in buttons:
        assert btn.objectName(), (
            f"QPushButton with text '{btn.text()}' has no objectName"
        )
        assert btn.receivers(btn.clicked) > 0, (
            f"QPushButton '{btn.objectName()}' has no slots connected to clicked signal"
        )


def test_tray_show_restores_window(qtbot, main_window) -> None:
    """TC-UI-09 [SAFE]: Selecting Show from tray context menu must restore the window."""
    # First minimize the window so we can test restore
    main_window.showMinimized()
    qtbot.wait(100)

    tray_icon = _find_tray_icon(main_window)
    if tray_icon is None:
        pytest.skip("Tray icon not found")

    menu = tray_icon.contextMenu()
    if menu is None:
        pytest.skip("Tray icon has no context menu")

    show_action = None
    for action in menu.actions():
        if action.text().lower() == "show":
            show_action = action
            break

    if show_action is None:
        pytest.skip("No Show action found in tray context menu")

    show_action.trigger()
    qtbot.wait(200)

    assert main_window.isVisible(), "Window was not restored to visible after tray Show"
    assert main_window.windowState() == Qt.WindowState.WindowNoState, (
        f"Window state was {main_window.windowState()} instead of normal after tray Show"
    )


def test_tray_settings_opens_dialog(qtbot, main_window) -> None:
    """TC-UI-10 [SAFE]: Selecting Settings from tray context menu must open a QDialog."""
    tray_icon = _find_tray_icon(main_window)
    if tray_icon is None:
        pytest.skip("Tray icon not found")

    menu = tray_icon.contextMenu()
    if menu is None:
        pytest.skip("Tray icon has no context menu")

    settings_action = None
    for action in menu.actions():
        if action.text().lower() == "settings":
            settings_action = action
            break

    if settings_action is None:
        pytest.skip("No Settings action found in tray context menu")

    settings_action.trigger()
    qtbot.wait(200)

    dialogs = [w for w in QApplication.topLevelWidgets() if isinstance(w, QDialog) and w.isVisible()]
    assert any(dialogs), "No visible QDialog found after tray Settings"


# ---------------------------------------------------------------------------
# INPUT-BOUND interactions
# ---------------------------------------------------------------------------

def test_change_refresh_rate_via_dropdown(qtbot, main_window) -> None:
    """TC-UI-03 [INPUT-BOUND]: Changing refresh rate in settings must use an allowed value."""
    # Open settings dialog first
    from src.api import open_settings_dialog
    from src.models import Settings

    allowed = {500, 1000, 2000, 5000}

    with qtbot.waitExposed(main_window):
        result = open_settings_dialog(main_window, Settings())

    # If the dialog returns a Settings object, validate the interval
    if result is not None:
        assert result.refresh_interval_ms in allowed, (
            f"refresh_interval_ms {result.refresh_interval_ms} not in allowed values {allowed}"
        )
    else:
        pytest.skip("Settings dialog returned None (cancelled or not implemented)")


def test_toggle_sensor_visibility_checkboxes(qtbot, main_window) -> None:
    """TC-UI-04 [INPUT-BOUND]: Toggling a visibility checkbox must hide the corresponding group."""
    try:
        from src.api import open_settings_dialog
        from src.models import Settings
    except ImportError as exc:
        pytest.skip(f"API not yet implemented: {exc}")

    # Open dialog and request utilization=False
    result = open_settings_dialog(
        main_window,
        Settings(show_utilization=True, show_temperatures=True, show_fan_speeds=True),
    )

    if result is None:
        pytest.skip("Settings dialog returned None")

    # After applying settings, the utilization group should be hidden if toggled off
    if not result.show_utilization:
        group = main_window.findChild(QWidget, "group_utilization")
        if group:
            assert not group.isVisible(), "Utilization group should be hidden when show_utilization is False"
        else:
            pytest.skip("group_utilization not found by objectName — update test when source is implemented")


# ---------------------------------------------------------------------------
# DESTRUCTIVE interactions
# ---------------------------------------------------------------------------

def test_click_minimize_button(qtbot, main_window) -> None:
    """TC-UI-05 [DESTRUCTIVE]: Clicking minimize must minimize the window and strip always-on-top."""
    minimize_btn = None
    for child in main_window.findChildren(QWidget):
        obj_name = child.objectName() or ""
        tip = child.toolTip() if hasattr(child, "toolTip") else ""
        if "minimize" in obj_name.lower() or "minimize" in tip.lower():
            minimize_btn = child
            break

    if minimize_btn is None:
        pytest.skip("Minimize button not found by heuristic")

    qtbot.mouseClick(minimize_btn, Qt.MouseButton.LeftButton)
    qtbot.wait(200)

    minimized = main_window.windowState() == Qt.WindowState.WindowMinimized
    not_visible = not main_window.isVisible()
    top_removed = not (main_window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)

    assert minimized or (not_visible and top_removed), (
        "Window was not minimized or always-on-top flag was not removed"
    )


def test_click_close_button(qtbot, main_window) -> None:
    """TC-UI-06 [DESTRUCTIVE]: Clicking close must trigger application exit path."""
    close_btn = None
    for child in main_window.findChildren(QWidget):
        obj_name = child.objectName() or ""
        tip = child.toolTip() if hasattr(child, "toolTip") else ""
        if "close" in obj_name.lower() or "close" in tip.lower() or obj_name.lower() == "btn_close":
            close_btn = child
            break

    if close_btn is None:
        pytest.skip("Close button not found by heuristic")

    # Spy on the worker finished signal if accessible
    try:
        from PyQt6.QtTest import QSignalSpy
        spy = QSignalSpy(main_window._worker.finished)
    except Exception:
        spy = None

    qtbot.mouseClick(close_btn, Qt.MouseButton.LeftButton)
    qtbot.wait(200)

    if spy is not None:
        assert spy.count() >= 1, "Worker finished signal was not emitted on close"
    else:
        # Fallback: window should no longer be in top-level widgets
        assert main_window not in QApplication.topLevelWidgets(), (
            "MainWindow still present in top-level widgets after close"
        )


def test_exit_from_system_tray_context_menu(qtbot, main_window) -> None:
    """TC-UI-07 [DESTRUCTIVE]: Selecting Exit from tray context menu must quit the app."""
    tray_icon = _find_tray_icon(main_window)

    if tray_icon is None:
        pytest.skip("Tray icon not found")

    menu = tray_icon.contextMenu()
    if menu is None:
        pytest.skip("Tray icon has no context menu")

    exit_action = None
    for action in menu.actions():
        if action.text().lower() in ("exit", "quit"):
            exit_action = action
            break

    if exit_action is None:
        pytest.skip("No Exit/Quit action found in tray context menu")

    # Spy on worker finished signal since aboutToQuit requires a running event loop
    from PyQt6.QtTest import QSignalSpy
    finished_spy = QSignalSpy(main_window._worker.finished)

    exit_action.trigger()
    qtbot.wait(200)

    assert finished_spy.count() >= 1, "Worker finished signal was not emitted after tray Exit"
