from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QDialogButtonBox,
    QWidget,
)

from src.models import Settings


class SettingsDialog(QDialog):
    """Modal dialog for configuring widget settings."""

    def __init__(self, parent: QWidget, settings: Settings):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._settings = settings
        self._result: Settings | None = None

        layout = QVBoxLayout(self)

        # Refresh interval
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(QLabel("Refresh Interval:"))
        self._refresh_combo = QComboBox()
        self._refresh_combo.addItem("0.5 s", 500)
        self._refresh_combo.addItem("1 s", 1000)
        self._refresh_combo.addItem("2 s", 2000)
        self._refresh_combo.addItem("5 s", 5000)
        idx = self._refresh_combo.findData(settings.refresh_interval_ms)
        if idx >= 0:
            self._refresh_combo.setCurrentIndex(idx)
        refresh_layout.addWidget(self._refresh_combo)
        layout.addLayout(refresh_layout)

        # Always on top
        self._chk_top = QCheckBox("Always on Top")
        self._chk_top.setChecked(settings.always_on_top)
        layout.addWidget(self._chk_top)

        # Visibility toggles
        self._chk_util = QCheckBox("Show Utilization")
        self._chk_util.setChecked(settings.show_utilization)
        layout.addWidget(self._chk_util)

        self._chk_temps = QCheckBox("Show Temperatures")
        self._chk_temps.setChecked(settings.show_temperatures)
        layout.addWidget(self._chk_temps)

        self._chk_fans = QCheckBox("Show Fan Speeds")
        self._chk_fans.setChecked(settings.show_fan_speeds)
        layout.addWidget(self._chk_fans)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        self._result = Settings(
            refresh_interval_ms=self._refresh_combo.currentData(),
            always_on_top=self._chk_top.isChecked(),
            show_utilization=self._chk_util.isChecked(),
            show_temperatures=self._chk_temps.isChecked(),
            show_fan_speeds=self._chk_fans.isChecked(),
            window_x=self._settings.window_x,
            window_y=self._settings.window_y,
        )
        self.accept()

    def get_settings(self) -> Settings:
        return self._result if self._result is not None else self._settings
