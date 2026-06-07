import json
from pathlib import Path

from src.models import Settings


DEFAULT_CONFIG_PATH = Path("settings.json")


def load_settings_json(config_path: Path = DEFAULT_CONFIG_PATH) -> Settings:
    """Load user settings from a JSON config file.
    Returns default Settings if the file does not exist or is malformed."""
    if not config_path.exists():
        return _default_settings()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Settings(**data)
    except Exception:
        return _default_settings()


def save_settings_json(settings: Settings, config_path: Path = DEFAULT_CONFIG_PATH) -> None:
    """Persist user settings to a JSON config file (atomic write)."""
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = config_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(settings.__dict__, f, indent=2, default=str)
        tmp_path.replace(config_path)
    except Exception as exc:
        raise RuntimeError(f"Failed to save settings to {config_path}: {exc}") from exc


def _default_settings() -> Settings:
    """Compute default settings, including lower-right corner position."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    screen = app.primaryScreen()
    if screen is not None:
        geom = screen.geometry()
        window_width = geom.width() // 10
        window_height = geom.height() // 10
        return Settings(
            window_x=geom.width() - window_width,
            window_y=geom.height() - window_height,
        )
    return Settings()
