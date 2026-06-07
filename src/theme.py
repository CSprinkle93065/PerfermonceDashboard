from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
import winreg


def detect_system_theme() -> str:
    """Detect the current Windows system theme (light or dark)."""
    app = QApplication.instance()
    if app is not None:
        try:
            scheme = app.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Dark:
                return "dark"
            elif scheme == Qt.ColorScheme.Light:
                return "light"
        except Exception:
            pass

    # Fallback to Windows registry
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value == 1 else "dark"
    except Exception:
        return "light"
