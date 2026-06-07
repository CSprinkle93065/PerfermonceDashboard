# PerfermonceDashboard — Application Definition

**Workflow ID:** wvc_20260606_095420  
**Project:** PerfermonceDashboard  
**Version:** 0.1.0  
**Revision Type:** new_project  
**Stage:** 1 — Requirements Elicitation (Second Pass)

---

## 1. Application Overview

PerfermonceDashboard is a lightweight, compact desktop widget for Windows that provides real-time visibility into system hardware performance. It continuously monitors and displays:

- **CPU utilization** (overall percentage)
- **GPU utilization** (overall percentage, when available — NVIDIA and AMD both supported)
- **NPU utilization** (overall percentage, when available)
- **Memory utilization** (RAM usage percentage)
- **Temperatures** from all available thermal sensors (CPU, GPU, NPU, motherboard, storage, etc.)
- **Fan speeds** from all available fan controllers (CPU fan, case fans, GPU fan, etc.)

The widget remains visible above other windows via an "Always on Top" window flag, except when the user explicitly minimizes it. When minimized, the widget relinquishes its top-most status; upon restoration, it resumes the always-on-top behavior.

### Target User
Power users, gamers, system administrators, and enthusiasts who want at-a-glance hardware monitoring without the overhead of a full monitoring suite.

### Key Value Proposition
- Instant, always-visible system health overview
- Minimal resource footprint
- Zero-configuration startup with sensible defaults
- Configurable update interval
- Live-only display; no history retained

### Critical Architecture Constraint — Worker Threading
Per lessons learned LL-020, **all sensor polling (CPU, GPU, NPU, memory, temperature, and fan speed reads) MUST occur in a background worker thread**. The main Qt thread must NEVER be blocked by sensor reads. The worker thread emits data via Qt signals (`pyqtSignal`) to the main thread, which updates the UI. This ensures the widget remains responsive even if a sensor query hangs or takes longer than expected. A cancel mechanism MUST be provided: when the widget is closing or the worker is being restarted, any pending sensor read should be abandoned gracefully.

### Critical Quality Constraint — Startup Smoke Test
Per lessons learned LL-010, the QA Agent must include a startup smoke test (`tests/test_startup.py`) that imports every `src/` module and constructs `MainWindow` headlessly (`QT_QPA_PLATFORM=offscreen`) without crashing.

---

## 2. UI Layout

The widget is a single, compact, non-resizable frameless window with the following characteristics:

### Window Properties
- **Title bar:** None (frameless window). The header bar serves as the draggable region and contains the application title, custom minimize button, and custom close button.
- **Size:** 10% of the screen resolution horizontally and 10% vertically (e.g., on a 1920×1080 display, the widget is 192×108 pixels). Fixed, non-resizable.
- **Resizable:** No (fixed size).
- **Window flags:** `Qt.WindowType.WindowStaysOnTopHint` when active; `Qt.WindowType.FramelessWindowHint`.
- **Always on Top:** Enabled by default; disabled automatically on minimize, re-enabled on restore.
- **System tray icon:** Yes — a small icon in the Windows notification area allows minimize/restore/exit via a context menu with "Show", "Settings", and "Exit" options.
- **Theme:** Follows the Windows system theme (light or dark). Theme detection is performed via `QApplication.styleHints().colorScheme()` (Qt 6.5+). On older Qt versions, fall back to reading the Windows registry key `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize\AppsUseLightTheme`. The widget applies appropriate background, text, and accent colors based on the detected theme.
- **Position memory:** The widget remembers its last window position and restores it on next launch. Default position is the lower-right corner of the screen.

### Layout Structure (top to bottom)
The widget uses a vertical `QVBoxLayout` containing grouped sensor panels:

1. **Header Bar**
   - Application title label ("PerfermonceDashboard")
   - Gear/settings icon button (opens Settings dialog)
   - Minimize button
   - Close (X) button
   - The header bar area is clickable and draggable to move the window.

2. **Utilization Group** (`QGroupBox` titled "Utilization")
   - **CPU Row:** Label "CPU" + `QProgressBar` (0–100 %) + percentage label (e.g., "34 %")
   - **GPU Row:** Label "GPU" + `QProgressBar` (0–100 %) + percentage label (e.g., "12 %")
   - **NPU Row:** Label "NPU" + `QProgressBar` (0–100 %) + percentage label (e.g., "8 %")
   - **Memory Row:** Label "RAM" + `QProgressBar` (0–100 %) + percentage label (e.g., "58 %")

3. **Temperatures Group** (`QGroupBox` titled "Temperatures")
   - Dynamic list of `QLabel` rows, one per detected thermal sensor.
   - Each row shows: sensor name (e.g., "CPU Package") + value + unit (°C)
   - If no temperature sensors are detected, displays "No temperature sensors detected"
   - NPU temperature is displayed here if available.

4. **Fan Speeds Group** (`QGroupBox` titled "Fan Speeds")
   - Dynamic list of `QLabel` rows, one per detected fan.
   - Each row shows: fan name (e.g., "CPU Fan") + value + unit (% of maximum speed)
   - If no fan sensors are detected, displays "No fan sensors detected"

5. **Status Footer**
   - A small `QLabel` showing the refresh interval (e.g., "Update: 1 s")
   - An indicator dot (green/red) showing whether the worker thread is actively polling. Hovering over the dot reveals a tooltip with the timestamp of the last successful update.

### Always on Top / Minimize Behavior (Detailed)
- **On launch:** Window is shown in normal state with `WindowStaysOnTopHint` active.
- **On minimize:** The window is minimized to the taskbar (and optionally hidden from taskbar, visible only in system tray). The `WindowStaysOnTopHint` is removed before minimize to prevent the minimized icon from staying on top of the desktop.
- **On restore:** The window is restored to normal state and `WindowStaysOnTopHint` is re-applied.
- **System tray double-click:** Restores the window.
- **System tray context menu:** "Show", "Settings", "Exit".

---

## 3. User Actions

| # | Action | Description |
|---|--------|-------------|
| A1 | **Launch widget** | User starts the application. Widget appears on screen, worker thread begins polling. |
| A2 | **Minimize widget** | User clicks the minimize button or taskbar icon. Window minimizes; always-on-top is suspended. |
| A3 | **Restore widget** | User clicks the taskbar icon, system tray icon, or restores from minimized state. Window returns; always-on-top resumes. |
| A4 | **Close/exit widget** | User clicks the X button or selects Exit from the system tray menu. Worker thread is signaled to stop; application exits cleanly. |
| A5 | **Open Settings dialog** | User clicks the gear icon. A modal `QDialog` appears with configuration options. |
| A6 | **Configure refresh rate** | In Settings, user selects a polling interval from a dropdown or spinner. Change takes effect immediately (worker thread is restarted with new interval). |
| A7 | **Toggle Always on Top** | In Settings, user checks/unchecks a "Always on Top" checkbox. When checked, window gets `WindowStaysOnTopHint`; when unchecked, flag is removed immediately. |
| A8 | **Toggle sensor visibility** | In Settings, user checks/unchecks which sensor categories to display (Utilization, Temperatures, Fan Speeds). Hidden categories collapse their `QGroupBox`. |

---

## 4. Data Model

### 4.1 SensorReading
Represents a single snapshot reading from one sensor.

| Attribute | Type | Description |
|-----------|------|-------------|
| `sensor_id` | `str` | Unique identifier for the sensor (e.g., "cpu_package_temp", "gpu_utilization") |
| `category` | `str` | One of: `"cpu"`, `"gpu"`, `"npu"`, `"memory"`, `"temperature"`, `"fan"` |
| `name` | `str` | Human-readable label (e.g., "CPU Package", "GPU Core", "NPU Utilization") |
| `value` | `float` | Numeric reading value |
| `unit` | `str` | Unit string: `"%"`, `"°C"` |
| `timestamp` | `datetime` | UTC timestamp when the reading was taken |

### 4.2 Settings
Persisted user preferences stored in a JSON config file.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `refresh_interval_ms` | `int` | `1000` | Polling interval in milliseconds. Allowed values: 500, 1000, 2000, 5000 |
| `always_on_top` | `bool` | `True` | Whether the window stays on top |
| `show_utilization` | `bool` | `True` | Show CPU/GPU/NPU/RAM section |
| `show_temperatures` | `bool` | `True` | Show temperatures section |
| `show_fan_speeds` | `bool` | `True` | Show fan speeds section |
| `window_x` | `int` | screen_width - window_width | Last known window X position |
| `window_y` | `int` | screen_height - window_height | Last known window Y position |

### 4.3 Worker Thread Data Flow
The `SensorWorker` (a `QThread` or `QObject` moved to a `QThread`) emits the following signals:

| Signal | Payload | Direction |
|--------|---------|-----------|
| `data_ready(dict[str, SensorReading])` | Mapping of `sensor_id` → `SensorReading` | Worker → MainWindow |
| `error_occurred(str)` | Error message string | Worker → MainWindow |
| `finished()` | None | Worker → MainWindow (when stopping) |

The main thread MUST NOT call sensor APIs directly; it only receives data via `data_ready`.

---

## 5. API Function List

### 5.1 UI / Application Lifecycle

```python
def create_application(argv: list[str]) -> QApplication:
    """Create the PyQt6 QApplication singleton."""
```

```python
def build_main_window(settings: Settings) -> MainWindow:
    """Construct MainWindow with restored geometry and settings."""
```

```python
def run_startup_smoke_test() -> None:
    """Import all src modules and construct MainWindow headlessly (QT_QPA_PLATFORM=offscreen). 
    Raises AssertionError on failure. Required by LL-010."""
```

### 5.2 Window Behavior

```python
def apply_always_on_top(window: QMainWindow, enabled: bool) -> None:
    """Set or clear Qt.WindowType.WindowStaysOnTopHint on the given window."""
```

```python
def minimize_window(window: MainWindow, tray_icon: QSystemTrayIcon) -> None:
    """Minimize the window and hide from taskbar if tray icon is available.
    Removes always-on-top flag before minimizing."""
```

```python
def restore_window(window: MainWindow) -> None:
    """Restore the window from minimized/hidden state and re-apply always-on-top."""
```

```python
def apply_system_theme(window: MainWindow) -> None:
    """Detect the current Windows system theme (light/dark) and apply 
    appropriate stylesheet/colors to the widget.
    
    Theme detection is performed via QApplication.styleHints().colorScheme() 
    (Qt 6.5+). On older Qt versions, falls back to reading the Windows registry 
    key HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize\AppsUseLightTheme."""
```

### 5.3 Sensor Reading (Worker Thread Only)

```python
def read_cpu_utilization() -> SensorReading:
    """Read overall CPU utilization percentage using psutil.
    MUST be called from the worker thread, never the main Qt thread."""
```

```python
def read_memory_utilization() -> SensorReading:
    """Read overall memory/RAM utilization percentage using psutil.
    MUST be called from the worker thread, never the main Qt thread."""
```

```python
def read_gpu_utilization() -> SensorReading | None:
    """Read overall GPU utilization percentage.
    Returns None if no supported GPU is present.
    Supports both NVIDIA GPUs (via nvidia-ml-py / NVML) and AMD GPUs.
    MUST be called from the worker thread, never the main Qt thread."""
```

```python
def read_npu_utilization() -> SensorReading | None:
    """Read overall NPU (Neural Processing Unit) utilization percentage.
    Returns None if no NPU is present.
    MUST be called from the worker thread, never the main Qt thread."""
```

```python
def read_all_temperatures() -> list[SensorReading]:
    """Read all available temperature sensors (CPU, GPU, NPU, motherboard, storage, etc.).
    The worker thread first attempts to read the sensor category via LibreHardwareMonitor.
    If the call raises LibreHardwareMonitorException or returns an empty list, the worker
    thread immediately attempts the same read via Windows WMI (wmi / pywin32) before
    returning results. Returns a list of SensorReading objects (may be empty).
    MUST be called from the worker thread, never the main Qt thread."""
```

```python
def read_all_fan_speeds() -> list[SensorReading]:
    """Read all available fan speed sensors and normalize each value to a percentage
    of its maximum rated speed. Uses LibreHardwareMonitor as the primary sensor library;
    gracefully falls back to Windows WMI if LibreHardwareMonitor does not support a
    specific component. The worker thread first attempts to read via LibreHardwareMonitor.
    If the call raises LibreHardwareMonitorException or returns an empty list, the worker
    thread immediately attempts the same read via Windows WMI (wmi / pywin32) before
    returning results. Maximum rated speed is obtained from the sensor's MaxRPM property
    via LibreHardwareMonitor when available; if no MaxRPM is reported, the highest
    observed RPM across the current session is used as the denominator. Returns a list of
    SensorReading objects with unit set to '%' (may be empty).
    MUST be called from the worker thread, never the main Qt thread."""
```

```python
def poll_all_sensors() -> dict[str, SensorReading]:
    """Aggregate call that executes all sensor reads in sequence and returns a merged dict.
    This is the function invoked by the worker thread on each timer tick."""
```

### 5.4 Worker Thread Management

```python
class SensorWorker(QObject):
    data_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, interval_ms: int) -> None:
        """Initialize worker with polling interval."""

    def start_polling(self) -> None:
        """Begin the QTimer-driven polling loop in the worker thread."""

    def stop_polling(self) -> None:
        """Signal the worker to stop. The timer is stopped and finished() is emitted."""
```

### 5.5 Settings Persistence (JSON Config)

```python
def load_settings_json(config_path: Path) -> Settings:
    """Load user settings from a JSON config file.
    Returns default Settings if the file does not exist or is malformed."""
```

```python
def save_settings_json(settings: Settings, config_path: Path) -> None:
    """Persist user settings to a JSON config file (atomic write)."""
```

### 5.6 Settings Dialog

```python
def open_settings_dialog(parent: QWidget, current_settings: Settings) -> Settings | None:
    """Show a modal QDialog with refresh rate, always-on-top, and visibility toggles.
    Returns the updated Settings if the user clicks OK, or None if cancelled."""
```

### 5.7 User Action to API Mapping

| User Action | API Function(s) |
|-------------|-----------------|
| A1 — Launch widget | `create_application()`, `load_settings_json()`, `build_main_window()`, `SensorWorker.start_polling()` |
| A2 — Minimize widget | `minimize_window()` |
| A3 — Restore widget | `restore_window()` |
| A4 — Close/exit widget | `SensorWorker.stop_polling()`, `save_settings_json()`, `QApplication.quit()` |
| A5 — Open Settings dialog | `open_settings_dialog()` |
| A6 — Configure refresh rate | `open_settings_dialog()` → `save_settings_json()` → `SensorWorker.stop_polling()` → new `SensorWorker.start_polling()` |
| A7 — Toggle Always on Top | `open_settings_dialog()` → `save_settings_json()` → `apply_always_on_top()` |
| A8 — Toggle sensor visibility | `open_settings_dialog()` → `save_settings_json()` → MainWindow updates group visibility |

---

## 6. Toolchain

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Language | Python | 3.11+ | Application runtime |
| GUI Framework | PyQt6 | 6.x | Desktop widget UI, system tray, signals/slots, worker threads |
| Config File | JSON (stdlib) | — | Settings persistence |
| CPU/RAM Sensors | psutil | 5.9+ | Cross-platform CPU and memory utilization |
| GPU Sensors | nvidia-ml-py + AMD libraries | 12.x / latest | NVIDIA GPU utilization via NVML; AMD GPU via ADL or equivalent |
| NPU Sensors | LibreHardwareMonitor / WMI | — | NPU utilization and temperature where available |
| Temperature / Fan Sensors | LibreHardwareMonitor (primary) + Windows WMI (fallback) | — | Windows thermal and fan sensor access |
| Testing | pytest | 7.x | Unit and integration tests |
| Qt Testing | pytest-qt | 4.x | Qt-specific test fixtures and helpers |
| Packaging | PyInstaller | 6.x | Single-file executable build |
| Version Control | Git | — | Source control |
| CI / Release | GitHub CLI (`gh`) | — | Release creation and asset upload |

### Packaging Notes
- PyInstaller spec should produce a **single-file executable** under `dist/`.
- `dist/` MUST be added to `.gitignore` before the first commit (per lessons learned LL-007).
- Hidden imports may be required for `psutil` and PyQt6 plugins; the Packaging Agent must verify the executable runs on a clean Windows machine.

### Sensor Library Selection Notes
- `psutil` is the standard cross-platform choice for CPU and memory; it works on Windows without extra dependencies.
- For GPU: `nvidia-ml-py` is the official NVIDIA Python binding. AMD GPU support must also be implemented. If no supported GPU is present, GPU utilization displays as N/A.
- For NPU: Utilization and temperature are read via LibreHardwareMonitor or Windows WMI, depending on hardware support. If no NPU is present, the NPU row shows N/A.
- For temperatures and fans: **LibreHardwareMonitor is the PRIMARY sensor library** and must be bundled as a DLL. The worker thread first attempts to read the sensor category via LibreHardwareMonitor. If the call raises `LibreHardwareMonitorException` or returns an empty list, the worker thread immediately attempts the same read via Windows WMI (`wmi` / `pywin32`) before returning results. The worker thread handles missing sensors gracefully in all cases.

### Development Environment
- OS: Windows 10/11
- Display server: Standard Windows desktop (headless smoke tests use `QT_QPA_PLATFORM=offscreen`)
