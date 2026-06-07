"""
Worker Thread Tests — LL-020 (CRITICAL)

Verify SensorWorker runs in a separate thread, does not block the
main Qt thread, and emits data_ready from the worker thread.
"""

import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import QCoreApplication, QObject, QThread, QTimer, pyqtSignal
from PyQt6.QtTest import QSignalSpy


@pytest.fixture(scope="module")
def qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)
    yield app


def _make_worker():
    try:
        from src.worker import SensorWorker
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")
    return SensorWorker(interval_ms=100)


def test_sensor_worker_runs_in_separate_thread(qapp) -> None:
    """TC-WORKER-01: The worker's execution thread must differ from main Qt thread."""
    worker = _make_worker()
    main_thread_id = QThread.currentThread()

    worker.start_polling()
    QTimer.singleShot(300, lambda: worker.stop_polling())

    # Allow event loop to spin so the worker thread starts
    spy = QSignalSpy(worker.finished)
    qapp.processEvents()
    time.sleep(0.5)
    qapp.processEvents()

    assert worker.thread() is not None
    assert worker.thread() != main_thread_id, "SensorWorker must run in a dedicated QThread"


def test_sensor_polling_does_not_block_ui(qapp) -> None:
    """TC-WORKER-02: A singleshot timer on the main thread must fire despite polling."""
    worker = _make_worker()
    callback_fired = False
    start_ms = None

    def mark_callback():
        nonlocal callback_fired, start_ms
        callback_fired = True
        start_ms = time.time()

    worker.start_polling()
    t0 = time.time()
    QTimer.singleShot(50, mark_callback)

    # Process events for up to 400 ms
    for _ in range(40):
        qapp.processEvents()
        time.sleep(0.01)
        if callback_fired:
            break

    worker.stop_polling()
    elapsed_ms = (time.time() - t0) * 1000

    assert callback_fired, "Main-thread singleshot timer never fired — UI may be blocked"
    assert elapsed_ms < 200, f"Main thread was blocked for {elapsed_ms:.1f} ms"


def test_data_ready_signal_emitted_from_worker(qapp) -> None:
    """TC-WORKER-03: data_ready must be emitted with a dict of SensorReading values."""
    worker = _make_worker()
    spy = QSignalSpy(worker.data_ready)

    with patch("src.worker.poll_all_sensors", return_value={"cpu": MagicMock()}):
        worker.start_polling()

        deadline = time.time() + 5.0
        while len(spy) == 0 and time.time() < deadline:
            qapp.processEvents()
            time.sleep(0.05)

        worker.stop_polling()

    assert len(spy) >= 1, "data_ready was never emitted within 5 seconds"
    payload = spy[0][0]
    assert isinstance(payload, dict), "data_ready payload must be a dict"


def test_stop_polling_emits_finished_and_halts(qapp) -> None:
    """TC-WORKER-04: stop_polling must emit finished and prevent further data_ready."""
    worker = _make_worker()
    finished_spy = QSignalSpy(worker.finished)
    data_spy = QSignalSpy(worker.data_ready)

    worker.start_polling()
    qapp.processEvents()
    time.sleep(0.1)

    worker.stop_polling()

    # Spin until finished arrives
    for _ in range(50):
        qapp.processEvents()
        time.sleep(0.01)
        if finished_spy.count() == 1:
            break

    assert finished_spy.count() == 1, "finished signal was not emitted exactly once"

    # No new data_ready should appear after stop
    post_stop_count = data_spy.count()
    time.sleep(0.2)
    qapp.processEvents()
    assert data_spy.count() == post_stop_count, "data_ready emitted after stop_polling"
