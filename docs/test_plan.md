# Test Plan: PerfermonceDashboard

**Workflow ID:** wvc_20260606_095420  
**Project:** PerfermonceDashboard  
**Version:** 0.1.0  
**Stage:** 3 — Test Plan Creation  
**Date:** 2026-06-06

---

## 1. Scope

This test plan covers:
- **API unit tests** for sensor reading, settings persistence, window behavior, and system theme detection.
- **UI construction tests** verifying widget presence, layout structure, and window properties.
- **Classified UI interaction tests** (SAFE, DESTRUCTIVE, INPUT-BOUND) using `pytest-qt`.
- **Worker thread tests** ensuring sensor polling never blocks the main Qt thread.
- **Startup smoke tests** importing every `src/` module and constructing `MainWindow` headlessly.

Visual pixel-perfect rendering is out of scope; layout correctness is verified via AST inspection and widget assertions.

---

## 2. Quality Gates

| Gate | Criterion | Status |
|------|-----------|--------|
| G3.1 | Every User Action from the definition has at least one test case with a deterministic PASS/FAIL criterion. | PASS |
| G3.2 | Every test case specifies an explicit API call signature and an executable pytest assertion (not a description). | PASS |
| G3.3 | No User Action is present in the definition whose outcome cannot be verified via the API Function List. | PASS |

---

## 3. User Action → Test Case Mapping

| User Action | Test Case(s) | File |
|-------------|--------------|------|
| A1 — Launch widget | TC-STARTUP-01, TC-WORKER-01 | `test_startup.py`, `test_worker_thread.py` |
| A2 — Minimize widget | TC-WIN-02, TC-UI-06 | `test_window_behavior.py`, `test_ui_interactions.py` |
| A3 — Restore widget | TC-WIN-03, TC-UI-09 | `test_window_behavior.py`, `test_ui_interactions.py` |
| A4 — Close/exit widget | TC-WORKER-03, TC-UI-06, TC-UI-07 | `test_worker_thread.py`, `test_ui_interactions.py` |
| A5 — Open Settings dialog | TC-UI-02, TC-UI-10, TC-SET-04 | `test_ui_interactions.py`, `test_settings.py` |
| A6 — Configure refresh rate | TC-SET-02, TC-UI-04 | `test_settings.py`, `test_ui_interactions.py` |
| A7 — Toggle Always on Top | TC-WIN-01, TC-SET-05 | `test_window_behavior.py`, `test_settings.py` |
| A8 — Toggle sensor visibility | TC-SET-03, TC-UI-05 | `test_settings.py`, `test_ui_interactions.py` |

---

## 4. Test Cases

### 4.1 Startup Smoke Tests (`test_startup.py`)

#### TC-STARTUP-01: Import all src modules and construct MainWindow headlessly

| Field | Value |
|-------|-------|
| **User Action** | A1 — Launch widget |
| **Classification** | SAFE |
| **Preconditions** | `QT_QPA_PLATFORM=offscreen` environment variable is set. `src/` package exists with all expected modules. |
| **API Call** | `build_main_window(settings=Settings())` |
| **Expected Result** | All `src/*.py` modules import without exception. `MainWindow` instance is created successfully and `isinstance(window, QMainWindow)` is `True`. |
| **Pass Criterion** | `assert all(mod is not None for mod in imported_modules) and isinstance(window, QMainWindow)` |

---

### 4.2 Worker Thread Tests (`test_worker_thread.py`)

#### TC-WORKER-01: SensorWorker runs in a separate thread

| Field | Value |
|-------|-------|
| **User Action** | A1 — Launch widget |
| **Classification** | SAFE |
| **Preconditions** | `QApplication` exists. `SensorWorker` is instantiated with `interval_ms=100`. |
| **API Call** | `worker.start_polling()` |
| **Expected Result** | The thread ID executing the polling timer callback is different from the main Qt thread ID. |
| **Pass Criterion** | `assert worker.thread() != QThread.currentThread()` while polling is active |

#### TC-WORKER-02: Sensor polling does not block UI responsiveness

| Field | Value |
|-------|-------|
| **User Action** | A1 — Launch widget (ongoing) |
| **Classification** | SAFE |
| **Preconditions** | `SensorWorker` is actively polling with `interval_ms=100`. A `QTimer` singleshot is queued on the main thread. |
| **API Call** | `worker.start_polling()` then `QTimer.singleShot(50, callback)` |
| **Expected Result** | The singleshot callback fires within 200 ms, proving the main event loop was not blocked by sensor I/O. |
| **Pass Criterion** | `assert callback_fired_ms < 200` |

#### TC-WORKER-03: data_ready signal is emitted from worker thread

| Field | Value |
|-------|-------|
| **User Action** | A1 — Launch widget (ongoing) |
| **Classification** | SAFE |
| **Preconditions** | `SensorWorker` is connected to a `QSignalSpy` or mock slot on the main thread. Worker polls once. |
| **API Call** | `worker.data_ready.connect(spy); worker.start_polling()` |
| **Expected Result** | `data_ready` signal is emitted at least once within 5 seconds, and the payload is a `dict[str, SensorReading]`. |
| **Pass Criterion** | `assert len(spy) >= 1 and isinstance(spy[0][0], dict) and all(isinstance(v, SensorReading) for v in spy[0][0].values())` |

#### TC-WORKER-04: Worker stopPolling emits finished and abandons pending reads

| Field | Value |
|-------|-------|
| **User Action** | A4 — Close/exit widget |
| **Classification** | DESTRUCTIVE |
| **Preconditions** | `SensorWorker` is actively polling. |
| **API Call** | `worker.stop_polling()` |
| **Expected Result** | `finished` signal is emitted. `worker.is_running` (or equivalent internal state) is `False`. No further `data_ready` emissions occur. |
| **Pass Criterion** | `assert finished_spy.count() == 1 and not worker._is_running` |

---

### 4.3 Sensor Reading Tests (`test_sensor_reading.py`)

#### TC-SENSOR-01: read_cpu_utilization returns valid percentage

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `psutil` is installed. |
| **API Call** | `read_cpu_utilization()` |
| **Expected Result** | Returns a `SensorReading` with `0.0 <= value <= 100.0`, `unit == "%"`, `category == "cpu"`. |
| **Pass Criterion** | `assert 0.0 <= reading.value <= 100.0 and reading.unit == "%" and reading.category == "cpu"` |

#### TC-SENSOR-02: read_memory_utilization returns valid percentage

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `psutil` is installed. |
| **API Call** | `read_memory_utilization()` |
| **Expected Result** | Returns a `SensorReading` with `0.0 <= value <= 100.0`, `unit == "%"`, `category == "memory"`. |
| **Pass Criterion** | `assert 0.0 <= reading.value <= 100.0 and reading.unit == "%" and reading.category == "memory"` |

#### TC-SENSOR-03: read_gpu_utilization handles NVIDIA GPU

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `nvidia-ml-py` is installed and an NVIDIA GPU is present (mocked if absent). |
| **API Call** | `read_gpu_utilization()` |
| **Expected Result** | Returns a `SensorReading` with `0.0 <= value <= 100.0`, `unit == "%"`, `category == "gpu"`. |
| **Pass Criterion** | `assert reading is not None and 0.0 <= reading.value <= 100.0 and reading.category == "gpu"` |

#### TC-SENSOR-04: read_gpu_utilization handles AMD GPU

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | AMD GPU libraries are present (mocked). |
| **API Call** | `read_gpu_utilization()` |
| **Expected Result** | Returns a `SensorReading` with `0.0 <= value <= 100.0`, `unit == "%"`, `category == "gpu"`. |
| **Pass Criterion** | `assert reading is not None and 0.0 <= reading.value <= 100.0 and reading.category == "gpu"` |

#### TC-SENSOR-05: read_gpu_utilization returns None when no GPU is present

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | Neither NVIDIA nor AMD GPU is present (monkeypatched environment). |
| **API Call** | `read_gpu_utilization()` |
| **Expected Result** | Returns `None`. |
| **Pass Criterion** | `assert read_gpu_utilization() is None` |

#### TC-SENSOR-06: read_all_temperatures returns list of SensorReading with Celsius unit

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | At least one temperature sensor is available (mocked). |
| **API Call** | `read_all_temperatures()` |
| **Expected Result** | Returns a `list[SensorReading]`. Every element has `unit == "°C"` and `value > -273.15`. |
| **Pass Criterion** | `assert all(r.unit == "°C" and r.value > -273.15 for r in readings)` |

#### TC-SENSOR-07: read_all_fan_speeds returns list of SensorReading with percentage unit

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | At least one fan sensor is available (mocked). |
| **API Call** | `read_all_fan_speeds()` |
| **Expected Result** | Returns a `list[SensorReading]`. Every element has `unit == "%"` and `0.0 <= value <= 100.0`. |
| **Pass Criterion** | `assert all(r.unit == "%" and 0.0 <= r.value <= 100.0 for r in readings)` |

#### TC-SENSOR-08: read_all_fan_speeds max-speed derivation uses MaxRPM when available

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | Mocked LibreHardwareMonitor fan sensor reports `MaxRPM = 2000` and current `RPM = 1000`. |
| **API Call** | `read_all_fan_speeds()` |
| **Expected Result** | Returned `SensorReading.value == 50.0` (1000 / 2000 * 100). |
| **Pass Criterion** | `assert any(r.value == 50.0 for r in readings)` |

#### TC-SENSOR-09: read_all_fan_speeds max-speed derivation falls back to highest observed RPM

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | Mocked sensor reports no `MaxRPM`; first call returns `RPM = 800`, second call returns `RPM = 400`. Session state tracked. |
| **API Call** | `read_all_fan_speeds()` (called twice) |
| **Expected Result** | Second call returns `value == 50.0` (400 / 800 * 100) because 800 is the highest observed RPM. |
| **Pass Criterion** | `assert second_readings[0].value == 50.0` |

#### TC-SENSOR-10: LibreHardwareMonitor → WMI fallback trigger on exception

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `read_all_temperatures()` is called with `LibreHardwareMonitor` patched to raise `LibreHardwareMonitorException`. WMI is mocked to return synthetic data. |
| **API Call** | `read_all_temperatures()` |
| **Expected Result** | Function does not propagate exception. Returns the WMI-fallback data. |
| **Pass Criterion** | `assert len(readings) == 1 and readings[0].name == "WMI Mock Temp"` |

#### TC-SENSOR-11: LibreHardwareMonitor → WMI fallback trigger on empty list

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `read_all_fan_speeds()` is called with `LibreHardwareMonitor` patched to return `[]`. WMI is mocked to return synthetic data. |
| **API Call** | `read_all_fan_speeds()` |
| **Expected Result** | Function returns the WMI-fallback data. |
| **Pass Criterion** | `assert len(readings) == 1 and readings[0].name == "WMI Mock Fan"` |

#### TC-SENSOR-12: read_npu_utilization returns valid reading when NPU is available

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | NPU is present (mocked). |
| **API Call** | `read_npu_utilization()` |
| **Expected Result** | Returns a `SensorReading` with `0.0 <= value <= 100.0`, `unit == "%"`, `category == "npu"`. |
| **Pass Criterion** | `assert reading is not None and 0.0 <= reading.value <= 100.0 and reading.category == "npu"` |

#### TC-SENSOR-13: read_npu_utilization returns None when no NPU is present

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | No NPU is present (monkeypatched environment). |
| **API Call** | `read_npu_utilization()` |
| **Expected Result** | Returns `None`. |
| **Pass Criterion** | `assert read_npu_utilization() is None` |

#### TC-SENSOR-14: read_all_temperatures includes NPU temperature when available

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | NPU temperature sensor is present (mocked). |
| **API Call** | `read_all_temperatures()` |
| **Expected Result** | Returned list contains a `SensorReading` with `category == "npu"` or `name` containing "NPU". |
| **Pass Criterion** | `assert any("npu" in r.category.lower() or "npu" in r.name.lower() for r in readings)` |

---

### 4.4 UI Layout Tests (`test_ui_layout.py`) — AST-Based Headless

#### TC-LAYOUT-01: MainWindow is frameless

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `src/main_window.py` exists. |
| **API Call** | AST inspection of `MainWindow.__init__` |
| **Expected Result** | AST contains a call setting `Qt.WindowType.FramelessWindowHint` on the window. |
| **Pass Criterion** | `assert any("FramelessWindowHint" in ast.dump(node) for node in frameless_nodes)` |

#### TC-LAYOUT-02: Window size is 10% of screen resolution

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `src/main_window.py` exists. |
| **API Call** | AST inspection of `MainWindow.__init__` |
| **Expected Result** | AST contains a `resize()` or `setFixedSize()` call using `QApplication.primaryScreen().geometry()` or `QScreen` size multiplied by `0.1`. |
| **Pass Criterion** | `assert any("resize" in ast.dump(node) and "0.1" in ast.dump(node) for node in size_nodes)` |

#### TC-LAYOUT-03: Grouped panels exist (Utilization, Temperatures, Fan Speeds)

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `src/main_window.py` exists. |
| **API Call** | AST inspection for `QGroupBox` constructor calls |
| **Expected Result** | AST contains exactly three `QGroupBox` instantiations with titles "Utilization", "Temperatures", and "Fan Speeds" (case-insensitive). |
| **Pass Criterion** | `assert {"Utilization", "Temperatures", "Fan Speeds"} <= {extract_title(node) for node in groupbox_nodes}` |

#### TC-LAYOUT-04: System tray icon is created

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `src/main_window.py` exists. |
| **API Call** | AST inspection for `QSystemTrayIcon` instantiation |
| **Expected Result** | AST contains at least one `QSystemTrayIcon(...)` call. |
| **Pass Criterion** | `assert any("QSystemTrayIcon" in ast.dump(node) for node in ast.walk(tree))` |

#### TC-LAYOUT-05: Header bar contains close/minimize/settings buttons

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `src/main_window.py` exists. |
| **API Call** | AST inspection for `QPushButton` or `QToolButton` constructors with object names or tooltip text matching "close", "minimize", and "settings". |
| **Expected Result** | AST contains button constructions for close, minimize, and settings (gear). |
| **Pass Criterion** | `assert {"close", "minimize", "settings"} <= {extract_button_role(node) for node in button_nodes}` |

---

### 4.5 Window Behavior Tests (`test_window_behavior.py`)

#### TC-WIN-01: Always on Top flag is applied on launch

| Field | Value |
|-------|-------|
| **User Action** | A7 — Toggle Always on Top (default ON) |
| **Classification** | SAFE |
| **Preconditions** | `MainWindow` is constructed with `settings.always_on_top == True`. |
| **API Call** | `build_main_window(settings=Settings(always_on_top=True))` |
| **Expected Result** | Window flags include `Qt.WindowType.WindowStaysOnTopHint`. |
| **Pass Criterion** | `assert window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint` |

#### TC-WIN-02: Always on Top is removed on minimize

| Field | Value |
|-------|-------|
| **User Action** | A2 — Minimize widget |
| **Classification** | DESTRUCTIVE |
| **Preconditions** | Window is visible with `WindowStaysOnTopHint` set. |
| **API Call** | `minimize_window(window, tray_icon)` |
| **Expected Result** | `WindowStaysOnTopHint` is no longer present in window flags. |
| **Pass Criterion** | `assert not (window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)` |

#### TC-WIN-03: Always on Top is re-applied on restore

| Field | Value |
|-------|-------|
| **User Action** | A3 — Restore widget |
| **Classification** | SAFE |
| **Preconditions** | Window was minimized and `WindowStaysOnTopHint` was removed. Settings has `always_on_top == True`. |
| **API Call** | `restore_window(window)` |
| **Expected Result** | `WindowStaysOnTopHint` is present again. |
| **Pass Criterion** | `assert window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint` |

#### TC-WIN-04: Frameless window drag behavior

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | Window is frameless and visible. |
| **API Call** | Simulate `mousePressEvent` at header bar coordinates, then `mouseMoveEvent` with offset `(50, 30)`. |
| **Expected Result** | Window geometry has moved by approximately `(50, 30)`. |
| **Pass Criterion** | `assert window.pos().x() - old_x == 50 and window.pos().y() - old_y == 30` |

---

### 4.6 Settings Tests (`test_settings.py`)

#### TC-SET-01: JSON config save and load round-trip

| Field | Value |
|-------|-------|
| **User Action** | A1 — Launch widget (settings restored) |
| **Classification** | SAFE |
| **Preconditions** | Temporary directory exists. |
| **API Call** | `save_settings_json(settings, path)` then `load_settings_json(path)` |
| **Expected Result** | Loaded `Settings` object equals the original. |
| **Pass Criterion** | `assert loaded == original` (or field-by-field equality for dataclass) |

#### TC-SET-02: Refresh rate change takes effect

| Field | Value |
|-------|-------|
| **User Action** | A6 — Configure refresh rate |
| **Classification** | INPUT-BOUND |
| **Preconditions** | Settings object exists. |
| **API Call** | `save_settings_json(Settings(refresh_interval_ms=2000), path)` then `load_settings_json(path)` |
| **Expected Result** | Loaded `refresh_interval_ms == 2000`. |
| **Pass Criterion** | `assert loaded.refresh_interval_ms == 2000` |

#### TC-SET-03: Sensor visibility toggles persist

| Field | Value |
|-------|-------|
| **User Action** | A8 — Toggle sensor visibility |
| **Classification** | INPUT-BOUND |
| **Preconditions** | Settings object exists. |
| **API Call** | `save_settings_json(Settings(show_utilization=False, show_temperatures=False, show_fan_speeds=True), path)` then `load_settings_json(path)` |
| **Expected Result** | Loaded booleans match written values. |
| **Pass Criterion** | `assert loaded.show_utilization is False and loaded.show_temperatures is False and loaded.show_fan_speeds is True` |

#### TC-SET-04: Position memory defaults to lower-right corner

| Field | Value |
|-------|-------|
| **User Action** | A1 — Launch widget |
| **Classification** | SAFE |
| **Preconditions** | No config file exists. Screen geometry is known. |
| **API Call** | `load_settings_json(nonexistent_path)` |
| **Expected Result** | Default `window_x == screen_width - window_width` and `window_y == screen_height - window_height`. |
| **Pass Criterion** | `assert settings.window_x == screen.width() - window_width and settings.window_y == screen.height() - window_height` |

#### TC-SET-05: Always on Top setting persists and is applied

| Field | Value |
|-------|-------|
| **User Action** | A7 — Toggle Always on Top |
| **Classification** | INPUT-BOUND |
| **Preconditions** | Settings saved with `always_on_top=False`. |
| **API Call** | `save_settings_json(Settings(always_on_top=False), path); loaded = load_settings_json(path); build_main_window(loaded)` |
| **Expected Result** | Built window does NOT have `WindowStaysOnTopHint`. |
| **Pass Criterion** | `assert not (window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)` |

---

### 4.7 System Theme Tests (`test_system_theme.py`)

#### TC-THEME-01: Theme detection uses QStyleHints.colorScheme on Qt 6.5+

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | PyQt6 version >= 6.5. |
| **API Call** | `apply_system_theme(window)` with `QStyleHints.colorScheme()` mocked to `Qt.ColorScheme.Dark`. |
| **Expected Result** | Window stylesheet contains dark-theme colors (e.g., dark background, light text). |
| **Pass Criterion** | `assert "background-color: #1e1e1e" in window.styleSheet().lower() or "color: #ffffff" in window.styleSheet().lower()` |

#### TC-THEME-02: Theme detection falls back to registry on older Qt

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | PyQt6 < 6.5 OR `colorScheme()` returns `Unknown`. Windows registry key `AppsUseLightTheme == 1` (light mode). |
| **API Call** | `apply_system_theme(window)` |
| **Expected Result** | Window stylesheet contains light-theme colors. |
| **Pass Criterion** | `assert "background-color: #f0f0f0" in window.styleSheet().lower() or "color: #000000" in window.styleSheet().lower()` |

#### TC-THEME-03: Theme change is applied to widget colors

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `MainWindow` is constructed. |
| **API Call** | `apply_system_theme(window)` with dark theme mocked. |
| **Expected Result** | At least one child widget (e.g., central widget or group box) has a style sheet or palette reflecting the dark theme. |
| **Pass Criterion** | `assert window.centralWidget().styleSheet() != "" or window.palette().color(QPalette.ColorRole.Window).lightness() < 128` |

---

### 4.8 pytest-qt UI Interaction Tests (`test_ui_interactions.py`)

#### TC-UI-01: Hover over polling indicator reveals timestamp tooltip — SAFE

| Field | Value |
|-------|-------|
| **Classification** | SAFE |
| **Preconditions** | `MainWindow` is visible. Worker has emitted at least one `data_ready`. |
| **API Call** | `qtbot.mouseMove(polling_indicator_label)` |
| **Expected Result** | `QToolTip.text()` contains a timestamp string (ISO format or locale time). |
| **Pass Criterion** | `assert "2026-" in QToolTip.text() or ":" in QToolTip.text()` |

#### TC-UI-02: Open Settings dialog — SAFE

| Field | Value |
|-------|-------|
| **User Action** | A5 — Open Settings dialog |
| **Classification** | SAFE |
| **Preconditions** | `MainWindow` is visible. |
| **API Call** | `qtbot.mouseClick(settings_button, Qt.MouseButton.LeftButton)` |
| **Expected Result** | A modal `QDialog` is opened and is visible. Dialog window title contains "Settings". |
| **Pass Criterion** | `assert any(isinstance(w, QDialog) and w.isVisible() for w in QApplication.topLevelWidgets())` |

#### TC-UI-03: Change refresh rate via dropdown/spinner — INPUT-BOUND

| Field | Value |
|-------|-------|
| **User Action** | A6 — Configure refresh rate |
| **Classification** | INPUT-BOUND |
| **Preconditions** | Settings dialog is open. |
| **API Call** | `qtbot.mouseClick(refresh_combo, Qt.MouseButton.LeftButton); qtbot.keyClick(refresh_combo, Qt.Key.Key_Down); qtbot.keyClick(refresh_combo, Qt.Key.Key_Enter)` |
| **Expected Result** | Selected value in combo box is one of the allowed values (500, 1000, 2000, 5000). |
| **Pass Criterion** | `assert refresh_combo.currentData() in {500, 1000, 2000, 5000}` |

#### TC-UI-04: Toggle sensor visibility checkboxes — INPUT-BOUND

| Field | Value |
|-------|-------|
| **User Action** | A8 — Toggle sensor visibility |
| **Classification** | INPUT-BOUND |
| **Preconditions** | Settings dialog is open. MainWindow has all three groups visible. |
| **API Call** | `qtbot.mouseClick(utilization_checkbox, Qt.MouseButton.LeftButton)` |
| **Expected Result** | Checkbox is unchecked. Corresponding `QGroupBox` in `MainWindow` is hidden. |
| **Pass Criterion** | `assert not utilization_checkbox.isChecked() and not utilization_groupbox.isVisible()` |

#### TC-UI-05: Click minimize button — DESTRUCTIVE

| Field | Value |
|-------|-------|
| **User Action** | A2 — Minimize widget |
| **Classification** | DESTRUCTIVE |
| **Preconditions** | `MainWindow` is visible and not minimized. |
| **API Call** | `qtbot.mouseClick(minimize_button, Qt.MouseButton.LeftButton)` |
| **Expected Result** | Window state is `Qt.WindowState.WindowMinimized` OR window is not visible AND `WindowStaysOnTopHint` is removed. |
| **Pass Criterion** | `assert window.windowState() == Qt.WindowState.WindowMinimized or (not window.isVisible() and not (window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))` |

#### TC-UI-06: Click close button — DESTRUCTIVE

| Field | Value |
|-------|-------|
| **User Action** | A4 — Close/exit widget |
| **Classification** | DESTRUCTIVE |
| **Preconditions** | `MainWindow` is visible. Worker is running. |
| **API Call** | `qtbot.mouseClick(close_button, Qt.MouseButton.LeftButton)` |
| **Expected Result** | `QApplication` top-level widgets no longer contain `MainWindow` OR worker `finished` signal was emitted. |
| **Pass Criterion** | `assert window not in QApplication.topLevelWidgets() or finished_spy.count() == 1` |

#### TC-UI-07: Select Exit from system tray context menu — DESTRUCTIVE

| Field | Value |
|-------|-------|
| **User Action** | A4 — Close/exit widget (via tray) |
| **Classification** | DESTRUCTIVE |
| **Preconditions** | System tray icon is active. Context menu is triggered programmatically. |
| **API Call** | `tray_icon.contextMenu().actions()[-1].trigger()` (Exit action) |
| **Expected Result** | Application quits; `QCoreApplication.instance()` is `None` or `aboutToQuit` signal fired. |
| **Pass Criterion** | `assert quit_spy.count() == 1` |

#### TC-UI-08: All buttons are discoverable and safe — SAFE

| Field | Value |
|-------|-------|
| **User Action** | A1 — Launch widget (construction-time audit) |
| **Classification** | SAFE |
| **Preconditions** | `MainWindow` is constructed and visible. |
| **API Call** | `main_window.findChildren(QPushButton)` |
| **Expected Result** | Every `QPushButton` has a non-empty `objectName` and at least one slot connected to `clicked`. |
| **Pass Criterion** | `assert all(btn.objectName() and btn.receivers(btn.clicked) > 0 for btn in buttons)` |

#### TC-UI-09: Select Show from system tray context menu — SAFE

| Field | Value |
|-------|-------|
| **User Action** | A3 — Restore widget (via tray) |
| **Classification** | SAFE |
| **Preconditions** | `MainWindow` is minimized. System tray icon is active. |
| **API Call** | `tray_icon.contextMenu().findChild("Show").trigger()` |
| **Expected Result** | Window becomes visible and its state is normal (not minimized). |
| **Pass Criterion** | `assert main_window.isVisible() and main_window.windowState() == Qt.WindowState.WindowNoState` |

#### TC-UI-10: Select Settings from system tray context menu — SAFE

| Field | Value |
|-------|-------|
| **User Action** | A5 — Open Settings dialog (via tray) |
| **Classification** | SAFE |
| **Preconditions** | System tray icon is active. |
| **API Call** | `tray_icon.contextMenu().findChild("Settings").trigger()` |
| **Expected Result** | A modal `QDialog` is opened and is visible. |
| **Pass Criterion** | `assert any(isinstance(w, QDialog) and w.isVisible() for w in QApplication.topLevelWidgets())` |

---

## 5. Test Execution Matrix

| Test File | # Cases | Types | Qt Needed |
|-----------|---------|-------|-----------|
| `test_startup.py` | 1 | Smoke | Yes (offscreen) |
| `test_worker_thread.py` | 4 | Unit / Threading | Yes |
| `test_sensor_reading.py` | 14 | Unit / Mocking | No |
| `test_ui_layout.py` | 5 | AST / Static | No |
| `test_window_behavior.py` | 4 | Unit / Qt | Yes (offscreen) |
| `test_settings.py` | 5 | Unit / I/O | No |
| `test_system_theme.py` | 3 | Unit / Mocking | Yes (offscreen) |
| `test_ui_interactions.py` | 10 | UI / pytest-qt | Yes (offscreen or display) |

**Total:** 46 test cases

---

## 6. Running the Suite

```bash
# Headless (CI)
set QT_QPA_PLATFORM=offscreen
python -m pytest tests/ -v

# With display (local)
python -m pytest tests/ -v
```

---

## 7. Verdict

**Verdict:** GO
