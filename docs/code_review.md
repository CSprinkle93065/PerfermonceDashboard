# Code Review — PerfermonceDashboard v0.1.0 (Re-Review)

**Workflow ID:** wvc_20260606_095420  
**Reviewer:** Code Critic (Stage 6 — Re-Review)  
**Date:** 2026-06-06  
**Result:** GO

---

## Executive Summary

Both previously failed quality gates (G6.2 and G6.5) have been corrected. A full sanity check confirms no regressions or new issues were introduced by the two targeted fixes.

---

## Re-Review Scope

This re-review verifies **only** the corrections mandated in the previous Stage 6 iteration:

1. **G6.2 Fix:** `src/main_window.py` must import `SensorWorker` through `src.api` rather than directly from `src.worker`.
2. **G6.5 Fix:** `src/settings.py` `save_settings_json()` must wrap file I/O in a `try/except` block.

---

## Fix Verification

### Fix 1 — G6.2: API Boundary Bypass

**File:** `src/main_window.py`  
**Status:** Corrected ✓

```python
# BEFORE (failed)
from src.worker import SensorWorker

# AFTER (fixed)
from src.api import SensorWorker
```

The `MainWindow` UI widget now routes the `SensorWorker` import through the public API boundary (`src.api`), consistent with the precedent established in SpiderFEA v0.1.2. No other UI widget imports business-logic modules directly.

### Fix 2 — G6.5: Missing Error Handling on Settings Save

**File:** `src/settings.py`  
**Status:** Corrected ✓

```python
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
```

All file I/O operations (`mkdir`, `open`, `json.dump`, `Path.replace`) are now protected by a `try/except` wrapper. An unhandled exception on `aboutToQuit` can no longer prevent clean shutdown.

---

## Sanity Check — No Regressions Introduced

| Area | Finding |
|------|---------|
| **G6.1** | All 18 API functions/classes remain present and correctly named in `src/api.py`. No additions or removals. |
| **G6.3** | No new hardcoded absolute paths, credentials, or environment-specific values introduced. |
| **G6.4** | No new security issues (no `eval()`, no unchecked subprocess calls, no unvalidated file writes). |
| **G6.6** | `docs/api_reference.md` remains in sync with `src/api.py`; no API signatures changed. |
| **Worker Thread Safety** | `SensorWorker` still runs in a dedicated `QThread`; `MainWindow` never calls sensor APIs directly. |
| **JSON Config** | Still no `sqlite3` usage; settings persistence remains JSON-based. |
| **LHM + WMI Fallbacks** | All sensor read paths retain their `try/except` fallback chains. |
| **Fan Normalization** | RPM-to-percentage logic unchanged; still caps at `100.0`. |
| **NPU Support** | `read_npu_utilization()` still exposed through `src/api.py`; UI still displays NPU bar. |

---

## Quality Gate Assessment

| Gate | Result | Notes |
|------|--------|-------|
| **G6.1** | **PASS** | All 18 API functions/classes from the API Function List are present and correctly named in `src/api.py`. |
| **G6.2** | **PASS** | `src/main_window.py` now imports `SensorWorker` from `src.api`. UI widgets do not bypass the API boundary. |
| **G6.3** | **PASS** | No hardcoded absolute paths, credentials, or environment-specific values. |
| **G6.4** | **PASS** | No `eval()`, no `subprocess` with user input, no unchecked file writes outside the project directory. |
| **G6.5** | **PASS** | `save_settings_json()` in `src/settings.py` now wraps all file I/O in `try/except`. Error handling exists at all system boundaries. |
| **G6.6** | **PASS** | `docs/api_reference.md` accurately documents every exported function/class in `src/api.py`. |

---

## Minor Observations (Informational)

These observations were present in the initial review and remain unchanged; they are **not** blockers.

- `src/theme.py` is not imported by any other module; its logic is duplicated inside `apply_system_theme()` in `src/api.py`.
- `src/sensor_worker.py` performs a runtime import `from src.worker import poll_all_sensors` inside `_poll()`. While functional, it creates a circular dependency pattern.
- `main.py` accesses `window._worker` (a private attribute) to start polling. Encapsulating this via a public accessor or an API function would improve separation of concerns.
