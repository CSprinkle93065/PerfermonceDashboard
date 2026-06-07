from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot


class SensorWorker(QObject):
    """Background worker that polls sensors on a QTimer in a dedicated QThread."""

    data_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()
    _stop_requested = pyqtSignal()

    def __init__(self, interval_ms: int = 1000):
        super().__init__()
        self._interval_ms = interval_ms
        self._is_running = False
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._on_thread_started)
        self._stop_requested.connect(self._stop_timer)

    def _on_thread_started(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._poll)
        self._timer.start(self._interval_ms)

    @pyqtSlot()
    def _poll(self):
        if not self._is_running:
            return
        try:
            from src.worker import poll_all_sensors as _poll_fn
            data = _poll_fn()
            self.data_ready.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def start_polling(self):
        """Begin the QTimer-driven polling loop in the worker thread."""
        self._is_running = True
        self._thread.start()

    @pyqtSlot()
    def _stop_timer(self):
        if hasattr(self, "_timer") and self._timer is not None:
            self._timer.stop()

    def stop_polling(self):
        """Signal the worker to stop. The timer is stopped and finished() is emitted."""
        self._is_running = False
        self._stop_requested.emit()
        self._thread.quit()
        self._thread.wait(2000)
        self.finished.emit()
