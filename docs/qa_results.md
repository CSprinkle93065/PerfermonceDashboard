# QA Results: PerfermonceDashboard v0.1.1

**Workflow ID:** wvc_20260607_044118  
**Project:** PerfermonceDashboard  
**Version:** 0.1.1  
**Revision Type:** bug_fix  
**Stage:** 7 — Automated Testing  
**Date:** 2026-06-07

---

## 1. Execution Summary

| Metric | Value |
|--------|-------|
| Tests Collected | 47 |
| Passed | 47 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Collection Errors | 0 |
| Execution Time | ~2.72 s |

**Command:**
```bash
python -m pytest tests/ -v --tb=short
```

**Environment:**
- Platform: win32
- Python: 3.14.2
- pytest: 9.0.3
- PyQt6: 6.11.0
- Qt runtime: 6.11.0

---

## 2. Test Results by File

| Test File | Cases | Passed | Failed | Errors |
|-----------|-------|--------|--------|--------|
| `test_sensor_reading.py` | 14 | 14 | 0 | 0 |
| `test_settings.py` | 5 | 5 | 0 | 0 |
| `test_startup.py` | 2 | 2 | 0 | 0 |
| `test_system_theme.py` | 3 | 3 | 0 | 0 |
| `test_ui_interactions.py` | 10 | 10 | 0 | 0 |
| `test_ui_layout.py` | 5 | 5 | 0 | 0 |
| `test_window_behavior.py` | 4 | 4 | 0 | 0 |
| `test_worker_thread.py` | 4 | 4 | 0 | 0 |

---

## 3. Bug Fix Verification

**Fix:** Widget sizing changed from `10% of screen resolution` (384×240 on 4K) to `max(12% width, 400) × max(25% height, 500)`.

**Verification:**
- `test_ui_layout.py::test_window_size_uses_12_percent_width_25_percent_height` — **PASSED**
- `test_settings.py::test_position_memory_defaults_to_lower_right` — **PASSED** (uses updated size formula for default position)

Both updated tests correctly assert the new sizing formula in `src/main_window.py`.

---

## 4. Critical User Workflow Coverage

Tests verifying behavioral outcomes (state change, data persistence, or visible UI update):

| Workflow | Test(s) | Outcome Verified |
|----------|---------|------------------|
| Launch widget | `test_construct_main_window_headlessly` | `MainWindow` is a `QMainWindow` |
| Minimize widget | `test_click_minimize_button`, `test_always_on_top_removed_on_minimize` | Window minimized; `WindowStaysOnTopHint` removed |
| Restore widget | `test_tray_show_restores_window`, `test_always_on_top_reapplied_on_restore` | Window visible and normal state; top flag re-applied |
| Close/exit widget | `test_click_close_button`, `test_exit_from_system_tray_context_menu` | Worker `finished` signal emitted; window removed |
| Open Settings dialog | `test_open_settings_dialog`, `test_tray_settings_opens_dialog` | Visible `QDialog` appears |
| Configure refresh rate | `test_change_refresh_rate_via_dropdown` | Selected value is in allowed set `{500, 1000, 2000, 5000}` |
| Toggle Always on Top | `test_always_on_top_setting_persists_and_applies` | Window flag matches saved setting |
| Toggle sensor visibility | `test_toggle_sensor_visibility_checkboxes` | Corresponding `QGroupBox` hidden when toggled off |
| Sensor polling | `test_data_ready_signal_emitted_from_worker` | Signal emitted with `dict` payload |

---

## 5. GUI Integration Tests (pytest-qt)

The following pytest-qt tests exercise complete workflows (`input → action → verified outcome`):

1. **`test_click_minimize_button`** — Clicks the minimize button; verifies window is minimized or hidden and `WindowStaysOnTopHint` is stripped.
2. **`test_click_close_button`** — Clicks the close button; verifies worker `finished` signal is emitted or window is removed from top-level widgets.
3. **`test_exit_from_system_tray_context_menu`** — Triggers the Exit tray action; verifies worker `finished` signal is emitted.
4. **`test_tray_show_restores_window`** — Triggers the Show tray action on a minimized window; verifies window becomes visible and returns to normal state.
5. **`test_toggle_sensor_visibility_checkboxes`** — Opens settings dialog with utilization off; verifies the utilization group is hidden.
6. **`test_change_refresh_rate_via_dropdown`** — Opens settings dialog; verifies returned refresh interval is in the allowed set.
7. **`test_open_settings_dialog`** — Clicks the settings button; verifies a visible `QDialog` appears.
8. **`test_tray_settings_opens_dialog`** — Triggers the Settings tray action; verifies a visible `QDialog` appears.

---

## 6. Warnings

40 deprecation warnings were observed (all non-fatal):
- `datetime.datetime.utcnow()` is deprecated in Python 3.14. These originate from `src/sensor_readers.py` and `src/main_window.py`.

These warnings do not affect test pass/fail status and are unrelated to the v0.1.1 bug fix.

---

## 7. Quality Gate Assessment

| Gate | Criterion | Result |
|------|-----------|--------|
| **G7.1** | All test cases pass. Zero failures. Zero collection errors. At least one test per critical user workflow verifies a behavioral outcome. | **PASS** |
| **G7.2** | All API functions called in tests exist and behave as defined. No `AttributeError` or missing function exceptions. | **PASS** |
| **G7.3** | At least one GUI integration test exercises a complete user workflow via pytest-qt. | **PASS** |

---

## 8. Verdict

**Overall Status:** **PASS**

The v0.1.1 bug fix (widget sizing update) is verified. All 47 tests pass. The test suite includes multiple GUI integration tests that exercise complete user workflows via pytest-qt, and all API functions behave as specified.
