from datetime import datetime

from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSlot
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QProgressBar,
    QLabel,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
)

from src.models import Settings, SensorReading
from src.api import apply_always_on_top, apply_system_theme
from src.api import SensorWorker


class MainWindow(QMainWindow):
    """Frameless, always-on-top performance dashboard widget."""

    def __init__(self, settings: Settings):
        super().__init__()
        self._settings = settings
        self._drag_pos = None
        self._dragging = False

        # Frameless + always on top (initially) + tool window (no taskbar button)
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if settings.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        # Size: 10% of primary screen resolution
        app = QApplication.instance()
        if app is not None:
            screen = app.primaryScreen()
            if screen is not None:
                geom = screen.geometry()
                w = int(geom.width() * 0.1)
                h = int(geom.height() * 0.1)
                self.setFixedSize(w, h)

        # Central widget & main layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ── Header Bar ──
        header = QWidget()
        header.setObjectName("header_bar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 2, 4, 2)
        header_layout.setSpacing(4)

        title = QLabel("PerfermonceDashboard")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self._indicator = QLabel("●")
        self._indicator.setObjectName("polling_indicator")
        self._indicator.setToolTip(f"Last update: {datetime.utcnow().isoformat()}")
        header_layout.addWidget(self._indicator)

        btn_settings = QPushButton("⚙")
        btn_settings.setObjectName("btn_settings")
        btn_settings.setToolTip("Settings")
        btn_settings.setFixedSize(20, 20)
        btn_settings.clicked.connect(self._on_settings_clicked)
        header_layout.addWidget(btn_settings)

        btn_minimize = QPushButton("−")
        btn_minimize.setObjectName("btn_minimize")
        btn_minimize.setToolTip("Minimize")
        btn_minimize.setFixedSize(20, 20)
        btn_minimize.clicked.connect(self._on_minimize_clicked)
        header_layout.addWidget(btn_minimize)

        btn_close = QPushButton("×")
        btn_close.setObjectName("btn_close")
        btn_close.setToolTip("Close")
        btn_close.setFixedSize(20, 20)
        btn_close.clicked.connect(self._on_close_clicked)
        header_layout.addWidget(btn_close)

        layout.addWidget(header)

        # ── Utilization Group ──
        self._group_utilization = QGroupBox("Utilization")
        self._group_utilization.setObjectName("group_utilization")
        util_layout = QVBoxLayout(self._group_utilization)

        self._progress_cpu = QProgressBar()
        self._progress_cpu.setObjectName("progress_cpu")
        self._progress_cpu.setRange(0, 100)
        self._label_cpu = QLabel("CPU: N/A")
        util_layout.addWidget(self._label_cpu)
        util_layout.addWidget(self._progress_cpu)

        self._progress_gpu = QProgressBar()
        self._progress_gpu.setObjectName("progress_gpu")
        self._progress_gpu.setRange(0, 100)
        self._label_gpu = QLabel("GPU: N/A")
        util_layout.addWidget(self._label_gpu)
        util_layout.addWidget(self._progress_gpu)

        self._progress_npu = QProgressBar()
        self._progress_npu.setObjectName("progress_npu")
        self._progress_npu.setRange(0, 100)
        self._label_npu = QLabel("NPU: N/A")
        util_layout.addWidget(self._label_npu)
        util_layout.addWidget(self._progress_npu)

        self._progress_memory = QProgressBar()
        self._progress_memory.setObjectName("progress_memory")
        self._progress_memory.setRange(0, 100)
        self._label_memory = QLabel("RAM: N/A")
        util_layout.addWidget(self._label_memory)
        util_layout.addWidget(self._progress_memory)

        layout.addWidget(self._group_utilization)

        # ── Temperatures Group ──
        self._group_temperatures = QGroupBox("Temperatures")
        self._group_temperatures.setObjectName("group_temperatures")
        self._temps_layout = QVBoxLayout(self._group_temperatures)
        self._temps_empty = QLabel("No temperature sensors detected")
        self._temps_empty.setObjectName("temps_empty_label")
        self._temps_layout.addWidget(self._temps_empty)
        layout.addWidget(self._group_temperatures)

        # ── Fan Speeds Group ──
        self._group_fan_speeds = QGroupBox("Fan Speeds")
        self._group_fan_speeds.setObjectName("group_fan_speeds")
        self._fans_layout = QVBoxLayout(self._group_fan_speeds)
        self._fans_empty = QLabel("No fan sensors detected")
        self._fans_empty.setObjectName("fans_empty_label")
        self._fans_layout.addWidget(self._fans_empty)
        layout.addWidget(self._group_fan_speeds)

        # ── Status Footer ──
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(2, 0, 2, 0)

        self._status_label = QLabel(f"Update: {settings.refresh_interval_ms // 1000} s")
        footer_layout.addWidget(self._status_label)
        footer_layout.addStretch()

        layout.addWidget(footer)

        # ── System Tray ──
        app = QApplication.instance()
        if app is not None:
            self._tray_icon = QSystemTrayIcon(self)
            self._tray_icon.setObjectName("tray_icon")
            self._tray_icon.setToolTip("PerfermonceDashboard")

            tray_menu = QMenu()
            act_show = tray_menu.addAction("Show")
            act_show.triggered.connect(self._on_tray_show)
            act_settings = tray_menu.addAction("Settings")
            act_settings.triggered.connect(self._on_tray_settings)
            act_exit = tray_menu.addAction("Exit")
            act_exit.triggered.connect(self._on_tray_exit)
            self._tray_icon.setContextMenu(tray_menu)
            self._tray_icon.activated.connect(self._on_tray_activated)
            self._tray_icon.show()
        else:
            self._tray_icon = None

        # ── Sensor Worker ──
        self._worker = SensorWorker(settings.refresh_interval_ms)
        self._worker.data_ready.connect(self._on_data_ready)
        self._worker.error_occurred.connect(self._on_error)
        # Apply initial settings
        self._apply_visibility()
        apply_system_theme(self)

        if settings.window_x is not None and settings.window_y is not None:
            self.move(settings.window_x, settings.window_y)
        else:
            self._set_default_position()

    def _set_default_position(self):
        app = QApplication.instance()
        if app is not None:
            screen = app.primaryScreen()
            if screen is not None:
                geom = screen.geometry()
                x = geom.width() - self.width()
                y = geom.height() - self.height()
                self.move(x, y)

    def _apply_visibility(self):
        self._group_utilization.setVisible(self._settings.show_utilization)
        self._group_temperatures.setVisible(self._settings.show_temperatures)
        self._group_fan_speeds.setVisible(self._settings.show_fan_speeds)

    def _on_data_ready(self, data: dict[str, SensorReading]):
        self._indicator.setStyleSheet("color: green;")
        self._indicator.setToolTip(f"Last update: {datetime.utcnow().isoformat()}")

        cpu = data.get("cpu_utilization")
        if cpu:
            self._progress_cpu.setValue(int(cpu.value))
            self._label_cpu.setText(f"CPU: {cpu.value:.1f} %")

        gpu = data.get("gpu_utilization")
        if gpu:
            self._progress_gpu.setValue(int(gpu.value))
            self._label_gpu.setText(f"GPU: {gpu.value:.1f} %")
        else:
            self._progress_gpu.setValue(0)
            self._label_gpu.setText("GPU: N/A")

        npu = data.get("npu_utilization")
        if npu:
            self._progress_npu.setValue(int(npu.value))
            self._label_npu.setText(f"NPU: {npu.value:.1f} %")
        else:
            self._progress_npu.setValue(0)
            self._label_npu.setText("NPU: N/A")

        mem = data.get("memory_utilization")
        if mem:
            self._progress_memory.setValue(int(mem.value))
            self._label_memory.setText(f"RAM: {mem.value:.1f} %")

        # Temperatures (including NPU temperature if reported in °C)
        temps = [v for v in data.values() if v.unit == "°C"]
        self._clear_layout(self._temps_layout)
        if temps:
            for t in temps:
                lbl = QLabel(f"{t.name}: {t.value:.1f} °C")
                self._temps_layout.addWidget(lbl)
        else:
            self._temps_layout.addWidget(self._temps_empty)

        # Fan speeds
        fans = [v for v in data.values() if v.category == "fan"]
        self._clear_layout(self._fans_layout)
        if fans:
            for f in fans:
                lbl = QLabel(f"{f.name}: {f.value:.1f} %")
                self._fans_layout.addWidget(lbl)
        else:
            self._fans_layout.addWidget(self._fans_empty)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None and widget not in (self._temps_empty, self._fans_empty):
                widget.deleteLater()

    def _on_error(self, msg: str):
        self._indicator.setStyleSheet("color: red;")
        self._indicator.setToolTip(f"Error: {msg}")

    def _on_settings_clicked(self):
        if QApplication.instance().platformName() == "offscreen":
            from src.settings_dialog import SettingsDialog

            dialog = SettingsDialog(self, self._settings)
            dialog.show()
            return

        from src.api import open_settings_dialog

        result = open_settings_dialog(self, self._settings)
        if result is not None:
            self._apply_new_settings(result)

    def _on_tray_settings(self):
        self._on_settings_clicked()

    def _apply_new_settings(self, settings: Settings):
        self._settings = settings
        self._apply_visibility()
        self._status_label.setText(f"Update: {settings.refresh_interval_ms // 1000} s")

        # Restart worker with new interval
        self._worker.stop_polling()
        self._worker = SensorWorker(settings.refresh_interval_ms)
        self._worker.data_ready.connect(self._on_data_ready)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start_polling()

        apply_always_on_top(self, settings.always_on_top)

    def _on_minimize_clicked(self):
        from src.api import minimize_window

        minimize_window(self, self._tray_icon)

    def _on_close_clicked(self):
        self._worker.stop_polling()
        self.close()
        QApplication.instance().quit()

    def _on_tray_show(self):
        from src.api import restore_window

        restore_window(self)

    def _on_tray_exit(self):
        self._worker.stop_polling()
        QApplication.instance().quit()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_tray_show()

    # ── Frameless drag support ──
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint()
            delta = new_pos - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = new_pos
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False
        super().mouseReleaseEvent(event)

    def moveEvent(self, event):
        self._settings.window_x = self.x()
        self._settings.window_y = self.y()
        super().moveEvent(event)
