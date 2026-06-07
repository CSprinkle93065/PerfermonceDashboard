"""Entry point for PerfermonceDashboard."""

import sys
from pathlib import Path

# Ensure src/ is importable when running `python src/main.py`
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication

from src.api import create_application, build_main_window
from src.settings import load_settings_json, save_settings_json


CONFIG_PATH = Path("settings.json")


def main() -> int:
    app = create_application(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    settings = load_settings_json(CONFIG_PATH)
    window = build_main_window(settings)
    window.show()
    window._worker.start_polling()

    def _on_about_to_quit():
        save_settings_json(settings, CONFIG_PATH)

    app.aboutToQuit.connect(_on_about_to_quit)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
