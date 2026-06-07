"""
Settings Persistence Tests

Covers JSON config save/load, refresh rate, sensor visibility,
and position memory.
"""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _settings_dataclass():
    try:
        from src.models import Settings
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")
    return Settings


def test_json_config_save_load_roundtrip() -> None:
    """TC-SET-01: Settings must round-trip through JSON unchanged."""
    try:
        from src.api import load_settings_json, save_settings_json
    except ImportError as exc:
        pytest.skip(f"API not yet implemented: {exc}")

    Settings = _settings_dataclass()
    original = Settings(
        refresh_interval_ms=1000,
        always_on_top=True,
        show_utilization=True,
        show_temperatures=True,
        show_fan_speeds=True,
        window_x=100,
        window_y=200,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.json"
        save_settings_json(original, path)
        loaded = load_settings_json(path)

    assert loaded == original, f"Round-trip failed: {loaded} != {original}"


def test_refresh_rate_change_persists() -> None:
    """TC-SET-02: refresh_interval_ms must be stored and restored."""
    try:
        from src.api import load_settings_json, save_settings_json
    except ImportError as exc:
        pytest.skip(f"API not yet implemented: {exc}")

    Settings = _settings_dataclass()
    original = Settings(refresh_interval_ms=2000)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.json"
        save_settings_json(original, path)
        loaded = load_settings_json(path)

    assert loaded.refresh_interval_ms == 2000


def test_sensor_visibility_toggles_persist() -> None:
    """TC-SET-03: show_* booleans must round-trip correctly."""
    try:
        from src.api import load_settings_json, save_settings_json
    except ImportError as exc:
        pytest.skip(f"API not yet implemented: {exc}")

    Settings = _settings_dataclass()
    original = Settings(
        show_utilization=False,
        show_temperatures=False,
        show_fan_speeds=True,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.json"
        save_settings_json(original, path)
        loaded = load_settings_json(path)

    assert loaded.show_utilization is False
    assert loaded.show_temperatures is False
    assert loaded.show_fan_speeds is True


def test_position_memory_defaults_to_lower_right() -> None:
    """TC-SET-04: Default position must be lower-right corner of primary screen."""
    try:
        from src.api import load_settings_json
    except ImportError as exc:
        pytest.skip(f"API not yet implemented: {exc}")

    Settings = _settings_dataclass()
    nonexistent = Path("/nonexistent/config.json")
    loaded = load_settings_json(nonexistent)

    # Compute expected defaults using screen geometry
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        screen = app.primaryScreen()
        screen_geom = screen.geometry()
    except Exception:
        pytest.skip("QApplication / primaryScreen unavailable")

    # Window size is 10% of screen; default position = screen - window size
    window_width = screen_geom.width() // 10
    window_height = screen_geom.height() // 10
    expected_x = screen_geom.width() - window_width
    expected_y = screen_geom.height() - window_height

    assert loaded.window_x == expected_x, f"Expected x={expected_x}, got {loaded.window_x}"
    assert loaded.window_y == expected_y, f"Expected y={expected_y}, got {loaded.window_y}"


def test_always_on_top_setting_persists_and_applies() -> None:
    """TC-SET-05: always_on_top=False must result in window without topmost flag."""
    try:
        from src.api import load_settings_json, save_settings_json, build_main_window
    except ImportError as exc:
        pytest.skip(f"API not yet implemented: {exc}")

    # Ensure QApplication exists before build_main_window to avoid offscreen deadlock.
    from PyQt6.QtWidgets import QApplication
    _ = QApplication.instance() or QApplication(sys.argv)

    Settings = _settings_dataclass()
    original = Settings(always_on_top=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.json"
        save_settings_json(original, path)
        loaded = load_settings_json(path)
        window = build_main_window(loaded)

    from PyQt6.QtCore import Qt
    assert not (window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint), (
        "Window must NOT have WindowStaysOnTopHint when settings say False"
    )
