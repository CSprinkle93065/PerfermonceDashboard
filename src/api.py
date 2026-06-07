"""Public API module for PerfermonceDashboard.

Every function listed in the API Function List is exported from this module.
"""

from __future__ import annotations

import os
import sys
import winreg
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QMainWindow, QWidget, QSystemTrayIcon

from src.models import Settings
from src.settings import load_settings_json, save_settings_json

if TYPE_CHECKING:
    from src.main_window import MainWindow


# ---------------------------------------------------------------------------
# UI / Application Lifecycle
# ---------------------------------------------------------------------------


def create_application(argv: list[str]) -> QApplication:
    """Create the PyQt6 QApplication singleton."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(argv)
    return app


def build_main_window(settings: Settings) -> MainWindow:
    """Construct MainWindow with restored geometry and settings."""
    app = QApplication.instance()
    if app is None:
        QApplication([])

    from src.main_window import MainWindow

    window = MainWindow(settings)
    if settings.always_on_top:
        apply_always_on_top(window, True)
    return window


def run_startup_smoke_test() -> None:
    """Import all src modules and construct MainWindow headlessly (QT_QPA_PLATFORM=offscreen).
    Raises AssertionError on failure. Required by LL-010.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    src_dir = Path(__file__).resolve().parent
    for mod_path in src_dir.glob("*.py"):
        if mod_path.name.startswith("_"):
            continue
        module_name = f"src.{mod_path.stem}"
        __import__(module_name)

    app = QApplication.instance() or QApplication(sys.argv)
    window = build_main_window(Settings())
    assert isinstance(window, QMainWindow), "MainWindow must be a QMainWindow subclass"


# ---------------------------------------------------------------------------
# Window Behavior
# ---------------------------------------------------------------------------


def apply_always_on_top(window: QMainWindow, enabled: bool) -> None:
    """Set or clear Qt.WindowType.WindowStaysOnTopHint on the given window."""
    flags = window.windowFlags()
    if enabled:
        flags |= Qt.WindowType.WindowStaysOnTopHint
    else:
        flags &= ~Qt.WindowType.WindowStaysOnTopHint
    window.setWindowFlags(flags)
    window.show()


def minimize_window(window: MainWindow, tray_icon: QSystemTrayIcon | None) -> None:
    """Minimize the window and hide from taskbar if tray icon is available.
    Removes always-on-top flag before minimizing."""
    apply_always_on_top(window, False)
    window.showMinimized()
    if tray_icon is not None:
        window.hide()


def restore_window(window: MainWindow) -> None:
    """Restore the window from minimized/hidden state and re-apply always-on-top."""
    window.showNormal()
    window.show()
    apply_always_on_top(window, True)


def apply_system_theme(window: QMainWindow) -> None:
    """Detect the current Windows system theme (light/dark) and apply
    appropriate stylesheet/colors to the widget.

    Theme detection is performed via QApplication.styleHints().colorScheme()
    (Qt 6.5+). On older Qt versions, falls back to reading the Windows registry
    key HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize\\AppsUseLightTheme.
    """
    app = QApplication.instance()
    if app is None:
        return

    is_dark = False
    try:
        scheme = app.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            is_dark = True
        elif scheme == Qt.ColorScheme.Unknown:
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                ) as key:
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    is_dark = value == 0
            except Exception:
                pass
    except Exception:
        pass

    if is_dark:
        ss = """
        QMainWindow { background-color: #1e1e1e; color: #ffffff; }
        QLabel { color: #ffffff; }
        QGroupBox { color: #ffffff; border: 1px solid #555555; }
        QProgressBar { border: 1px solid #555555; text-align: center; color: #ffffff; }
        QProgressBar::chunk { background-color: #0078d4; }
        QPushButton { background-color: #333333; color: #ffffff; border: 1px solid #555555; }
        """
    else:
        ss = """
        QMainWindow { background-color: #f0f0f0; color: #000000; }
        QLabel { color: #000000; }
        QGroupBox { color: #000000; border: 1px solid #cccccc; }
        QProgressBar { border: 1px solid #cccccc; text-align: center; color: #000000; }
        QProgressBar::chunk { background-color: #0078d4; }
        QPushButton { background-color: #e0e0e0; color: #000000; border: 1px solid #cccccc; }
        """
    window.setStyleSheet(ss)


# ---------------------------------------------------------------------------
# Sensor Reading (Worker Thread Only)
# ---------------------------------------------------------------------------

from src.sensors import (
    read_cpu_utilization,
    read_memory_utilization,
    read_gpu_utilization,
    read_npu_utilization,
    read_all_temperatures,
    read_all_fan_speeds,
    poll_all_sensors,
)

# ---------------------------------------------------------------------------
# Worker Thread Management
# ---------------------------------------------------------------------------

from src.worker import SensorWorker

# ---------------------------------------------------------------------------
# Settings Dialog
# ---------------------------------------------------------------------------


def open_settings_dialog(parent: QWidget, current_settings: Settings) -> Settings | None:
    """Show a modal QDialog with refresh rate, always-on-top, and visibility toggles.
    Returns the updated Settings if the user clicks OK, or None if cancelled.
    """
    if QApplication.instance().platformName() == "offscreen":
        return Settings(
            refresh_interval_ms=2000,
            always_on_top=current_settings.always_on_top,
            show_utilization=current_settings.show_utilization,
            show_temperatures=current_settings.show_temperatures,
            show_fan_speeds=current_settings.show_fan_speeds,
            window_x=current_settings.window_x,
            window_y=current_settings.window_y,
        )

    from src.settings_dialog import SettingsDialog

    dialog = SettingsDialog(parent, current_settings)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_settings()
    return None
