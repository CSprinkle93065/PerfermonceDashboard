# PerfermonceDashboard API Reference

**Version:** 0.1.0  
**Module:** `src.api`

---

## UI / Application Lifecycle

### `create_application(argv: list[str]) -> QApplication`

Create the PyQt6 QApplication singleton.

**Parameters:**
- `argv` (`list[str]`): Command-line arguments passed to the application.

**Returns:**
- `QApplication`: The application singleton (creates one if none exists).

**Example:**
```python
from src.api import create_application
app = create_application(sys.argv)
```

---

### `build_main_window(settings: Settings) -> MainWindow`

Construct `MainWindow` with restored geometry and settings.

**Parameters:**
- `settings` (`Settings`): User settings loaded from JSON config.

**Returns:**
- `MainWindow`: The fully constructed main window widget.

**Example:**
```python
from src.api import build_main_window
from src.models import Settings
window = build_main_window(Settings())
```

---

### `run_startup_smoke_test() -> None`

Import all `src/` modules and construct `MainWindow` headlessly (`QT_QPA_PLATFORM=offscreen`).

**Raises:**
- `AssertionError`: If any module fails to import or `MainWindow` construction fails.

**Example:**
```python
from src.api import run_startup_smoke_test
run_startup_smoke_test()
```

---

## Window Behavior

### `apply_always_on_top(window: QMainWindow, enabled: bool) -> None`

Set or clear `Qt.WindowType.WindowStaysOnTopHint` on the given window.

**Parameters:**
- `window` (`QMainWindow`): The window to modify.
- `enabled` (`bool`): `True` to enable always-on-top, `False` to disable.

**Example:**
```python
from src.api import apply_always_on_top
apply_always_on_top(window, True)
```

---

### `minimize_window(window: MainWindow, tray_icon: QSystemTrayIcon | None) -> None`

Minimize the window and hide from taskbar if tray icon is available.
Removes always-on-top flag before minimizing.

**Parameters:**
- `window` (`MainWindow`): The widget window.
- `tray_icon` (`QSystemTrayIcon | None`): The system tray icon, or `None`.

**Example:**
```python
from src.api import minimize_window
minimize_window(window, tray_icon)
```

---

### `restore_window(window: MainWindow) -> None`

Restore the window from minimized/hidden state and re-apply always-on-top.

**Parameters:**
- `window` (`MainWindow`): The widget window.

**Example:**
```python
from src.api import restore_window
restore_window(window)
```

---

### `apply_system_theme(window: QMainWindow) -> None`

Detect the current Windows system theme (light/dark) and apply appropriate stylesheet/colors to the widget.

Theme detection is performed via `QApplication.styleHints().colorScheme()` (Qt 6.5+). On older Qt versions, falls back to reading the Windows registry key `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize\AppsUseLightTheme`.

**Parameters:**
- `window` (`QMainWindow`): The widget window.

**Example:**
```python
from src.api import apply_system_theme
apply_system_theme(window)
```

---

## Sensor Reading (Worker Thread Only)

### `read_cpu_utilization() -> SensorReading`

Read overall CPU utilization percentage using `psutil`.

**Returns:**
- `SensorReading`: Reading with `category="cpu"`, `unit="%"`.

**Example:**
```python
from src.api import read_cpu_utilization
reading = read_cpu_utilization()
print(f"CPU: {reading.value}%")
```

---

### `read_memory_utilization() -> SensorReading`

Read overall memory/RAM utilization percentage using `psutil`.

**Returns:**
- `SensorReading`: Reading with `category="memory"`, `unit="%"`.

**Example:**
```python
from src.api import read_memory_utilization
reading = read_memory_utilization()
print(f"RAM: {reading.value}%")
```

---

### `read_gpu_utilization() -> SensorReading | None`

Read overall GPU utilization percentage.

Supports both NVIDIA GPUs (via `nvidia-ml-py` / NVML) and AMD GPUs.

**Returns:**
- `SensorReading`: Reading with `category="gpu"`, `unit="%"`, or `None` if no supported GPU is present.

**Example:**
```python
from src.api import read_gpu_utilization
reading = read_gpu_utilization()
if reading:
    print(f"GPU: {reading.value}%")
```

---

### `read_npu_utilization() -> SensorReading | None`

Read overall NPU (Neural Processing Unit) utilization percentage.

**Returns:**
- `SensorReading`: Reading with `category="npu"`, `unit="%"`, or `None` if no NPU is present.

**Example:**
```python
from src.api import read_npu_utilization
reading = read_npu_utilization()
if reading:
    print(f"NPU: {reading.value}%")
```

---

### `read_all_temperatures() -> list[SensorReading]`

Read all available temperature sensors (CPU, GPU, NPU, motherboard, storage, etc.).

The worker thread first attempts to read via LibreHardwareMonitor. If the call raises an exception or returns an empty list, the worker thread immediately attempts the same read via Windows WMI before returning results.

**Returns:**
- `list[SensorReading]`: List of temperature readings (may be empty). Each element has `unit="°C"`.

**Example:**
```python
from src.api import read_all_temperatures
readings = read_all_temperatures()
for r in readings:
    print(f"{r.name}: {r.value} °C")
```

---

### `read_all_fan_speeds() -> list[SensorReading]`

Read all available fan speed sensors and normalize each value to a percentage of its maximum rated speed.

Uses LibreHardwareMonitor as the primary sensor library; gracefully falls back to Windows WMI. Maximum rated speed is obtained from the sensor's `MaxRPM` property when available; if no `MaxRPM` is reported, the highest observed RPM across the current session is used as the denominator.

**Returns:**
- `list[SensorReading]`: List of fan readings with `unit="%"` (may be empty).

**Example:**
```python
from src.api import read_all_fan_speeds
readings = read_all_fan_speeds()
for r in readings:
    print(f"{r.name}: {r.value}%")
```

---

### `poll_all_sensors() -> dict[str, SensorReading]`

Aggregate call that executes all sensor reads in sequence and returns a merged dict.

This is the function invoked by the worker thread on each timer tick.

**Returns:**
- `dict[str, SensorReading]`: Mapping of `sensor_id` to `SensorReading`.

**Example:**
```python
from src.api import poll_all_sensors
data = poll_all_sensors()
print(data.keys())
```

---

## Worker Thread Management

### `class SensorWorker(QObject)`

Background worker that polls sensors in a dedicated `QThread`.

**Signals:**
- `data_ready(dict)`: Emitted when a new sensor snapshot is available.
- `error_occurred(str)`: Emitted when a sensor read raises an exception.
- `finished()`: Emitted when polling has stopped.

**Methods:**
- `__init__(self, interval_ms: int)`: Initialize worker with polling interval.
- `start_polling(self) -> None`: Begin the `QTimer`-driven polling loop in the worker thread.
- `stop_polling(self) -> None`: Signal the worker to stop. The timer is stopped and `finished()` is emitted.

**Example:**
```python
from src.api import SensorWorker
worker = SensorWorker(interval_ms=1000)
worker.data_ready.connect(on_data)
worker.start_polling()
# ... later ...
worker.stop_polling()
```

---

## Settings Persistence (JSON Config)

### `load_settings_json(config_path: Path) -> Settings`

Load user settings from a JSON config file.

**Parameters:**
- `config_path` (`Path`): Path to the JSON config file.

**Returns:**
- `Settings`: Loaded settings, or default settings if the file does not exist or is malformed.

**Example:**
```python
from pathlib import Path
from src.api import load_settings_json
settings = load_settings_json(Path("settings.json"))
```

---

### `save_settings_json(settings: Settings, config_path: Path) -> None`

Persist user settings to a JSON config file (atomic write).

**Parameters:**
- `settings` (`Settings`): Settings to save.
- `config_path` (`Path`): Path to the JSON config file.

**Example:**
```python
from pathlib import Path
from src.api import save_settings_json, Settings
save_settings_json(Settings(), Path("settings.json"))
```

---

## Settings Dialog

### `open_settings_dialog(parent: QWidget, current_settings: Settings) -> Settings | None`

Show a modal `QDialog` with refresh rate, always-on-top, and visibility toggles.

**Parameters:**
- `parent` (`QWidget`): Parent widget for the dialog.
- `current_settings` (`Settings`): Current settings to populate the dialog.

**Returns:**
- `Settings | None`: Updated settings if the user clicks OK, or `None` if cancelled.

**Example:**
```python
from src.api import open_settings_dialog
new_settings = open_settings_dialog(window, current_settings)
if new_settings is not None:
    apply_settings(new_settings)
```
