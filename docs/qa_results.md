# QA Results: PerfermonceDashboard v0.1.0

**Workflow ID:** wvc_20260606_095420  
**Stage:** 7 — Automated Testing  
**Date:** 2026-06-06  
**Tester:** QA Agent  

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Tests | 47 |
| Passed | 47 |
| Failed | 0 |
| Skipped | 0 |
| Collection Errors | 0 |

**Verdict: GO**

All test cases from the test plan execute successfully. Zero regressions. All Quality Gates pass.

---

## Quality Gate Results

| Gate | Criterion | Result |
|------|-----------|--------|
| G7.1 | All test cases have passing pytest assertions; zero failures; zero collection errors; at least one behavioral-outcome test per critical workflow. | **PASS** |
| G7.2 | All API functions called in tests exist and behave as defined; no AttributeError or missing function exceptions. | **PASS** |
| G7.3 | At least one GUI integration test exercises a complete user workflow via pytest-qt (input → action → verified outcome). | **PASS** |

---

## Per-Module Test Results

### `test_startup.py` (2/2 PASSED)
- `test_import_all_src_modules` — PASSED
- `test_construct_main_window_headlessly` — PASSED

### `test_worker_thread.py` (4/4 PASSED)
- `test_sensor_worker_runs_in_separate_thread` — PASSED
- `test_sensor_polling_does_not_block_ui` — PASSED
- `test_data_ready_signal_emitted_from_worker` — PASSED
- `test_stop_polling_emits_finished_and_halts` — PASSED

### `test_sensor_reading.py` (14/14 PASSED)
- `test_read_cpu_utilization_returns_valid_percentage` — PASSED
- `test_read_memory_utilization_returns_valid_percentage` — PASSED
- `test_read_gpu_utilization_nvidia` — PASSED
- `test_read_gpu_utilization_amd` — PASSED
- `test_read_gpu_utilization_returns_none_when_no_gpu` — PASSED
- `test_read_all_temperatures_returns_celsius_readings` — PASSED
- `test_read_all_temperatures_lhm_to_wmi_fallback_on_exception` — PASSED
- `test_read_all_fan_speeds_returns_percentage_readings` — PASSED
- `test_read_all_fan_speeds_maxrpm_derivation` — PASSED
- `test_read_all_fan_speeds_fallback_to_highest_observed_rpm` — PASSED
- `test_read_all_fan_speeds_lhm_to_wmi_fallback_on_empty` — PASSED
- `test_read_npu_utilization_returns_reading_when_available` — PASSED
- `test_read_npu_utilization_returns_none_when_missing` — PASSED
- `test_read_all_temperatures_includes_npu_temperature_when_available` — PASSED

### `test_ui_layout.py` (5/5 PASSED)
- `test_main_window_is_frameless` — PASSED
- `test_window_size_is_10_percent_of_screen` — PASSED
- `test_grouped_panels_exist` — PASSED
- `test_system_tray_icon_is_created` — PASSED
- `test_header_bar_contains_close_minimize_settings_buttons` — PASSED

### `test_window_behavior.py` (4/4 PASSED)
- `test_always_on_top_applied_on_launch` — PASSED
- `test_always_on_top_removed_on_minimize` — PASSED
- `test_always_on_top_reapplied_on_restore` — PASSED
- `test_frameless_window_drag_behavior` — PASSED

### `test_settings.py` (5/5 PASSED)
- `test_json_config_save_load_roundtrip` — PASSED
- `test_refresh_rate_change_persists` — PASSED
- `test_sensor_visibility_toggles_persist` — PASSED
- `test_position_memory_defaults_to_lower_right` — PASSED
- `test_always_on_top_setting_persists_and_applies` — PASSED

### `test_system_theme.py` (3/3 PASSED)
- `test_theme_detection_uses_color_scheme_on_qt65_plus` — PASSED
- `test_theme_detection_falls_back_to_registry_light` — PASSED
- `test_theme_change_applied_to_widget_colors` — PASSED

### `test_ui_interactions.py` (10/10 PASSED)
- `test_hover_over_polling_indicator_reveals_timestamp` — PASSED
- `test_open_settings_dialog` — PASSED
- `test_all_buttons_are_discoverable_and_safe` — PASSED
- `test_tray_show_restores_window` — PASSED
- `test_tray_settings_opens_dialog` — PASSED
- `test_change_refresh_rate_via_dropdown` — PASSED
- `test_toggle_sensor_visibility_checkboxes` — PASSED
- `test_click_minimize_button` — PASSED
- `test_click_close_button` — PASSED
- `test_exit_from_system_tray_context_menu` — PASSED

---

## Critical Workflow Verification (G7.1 Behavioral Outcomes)

The following tests verify state changes, data persistence, or visible UI updates:

| Workflow | Test | Verified Outcome |
|----------|------|------------------|
| Sensor polling | `test_sensor_polling_does_not_block_ui` | Main-thread timer fires within 200 ms while worker polls. |
| Worker signals | `test_data_ready_signal_emitted_from_worker` | `data_ready` emitted with `dict` payload. |
| Worker stop | `test_stop_polling_emits_finished_and_halts` | `finished` emitted; no further `data_ready` after stop. |
| Minimize | `test_always_on_top_removed_on_minimize` | `WindowStaysOnTopHint` removed from window flags. |
| Restore | `test_always_on_top_reapplied_on_restore` | `WindowStaysOnTopHint` re-applied after restore. |
| Drag | `test_frameless_window_drag_behavior` | Window position changes by simulated delta. |
| Settings persist | `test_json_config_save_load_roundtrip` | Settings dataclass round-trips through JSON unchanged. |
| Refresh rate | `test_refresh_rate_change_persists` | `refresh_interval_ms == 2000` after load. |
| Visibility toggle | `test_sensor_visibility_toggles_persist` | `show_*` booleans match written values. |
| Always on top | `test_always_on_top_setting_persists_and_applies` | Window built without `WindowStaysOnTopHint`. |
| Theme | `test_theme_detection_uses_color_scheme_on_qt65_plus` | Dark stylesheet applied when colorScheme mocked to Dark. |
| Settings dialog | `test_open_settings_dialog` | Visible `QDialog` appears after settings button click. |
| Sensor visibility UI | `test_toggle_sensor_visibility_checkboxes` — INPUT-BOUND | Group box hidden when checkbox unchecked. |
| Minimize UI | `test_click_minimize_button` — DESTRUCTIVE | Window minimized / always-on-top removed. |
| Close UI | `test_click_close_button` — DESTRUCTIVE | Worker `finished` emitted on close. |
| Tray restore | `test_tray_show_restores_window` | Window visible and state normal after tray Show. |
| Tray settings | `test_tray_settings_opens_dialog` | Visible `QDialog` appears after tray Settings. |
| Tray exit | `test_exit_from_system_tray_context_menu` — DESTRUCTIVE | Worker `finished` emitted after tray Exit. |

---

## GUI Integration Workflow (G7.3)

`test_toggle_sensor_visibility_checkboxes` in `test_ui_interactions.py` exercises a complete user workflow via pytest-qt:

1. **Input:** A `MainWindow` is constructed with all groups visible.
2. **Action:** `open_settings_dialog` is called; within the dialog, the utilization checkbox is unchecked.
3. **Verified Outcome:** The returned `Settings` object has `show_utilization=False`, and the corresponding `group_utilization` `QGroupBox` in `MainWindow` is hidden.

This satisfies G7.3: input → action → verified outcome via pytest-qt.

---

## Bugs Found During Test Implementation

**None.**

All test failures encountered during implementation were attributable to test-environment or test-code issues, not defects in `src/`:

1. **Offscreen QApplication initialization order:** `test_always_on_top_setting_persists_and_applies` hung when `src.api` was imported before `QApplication` was instantiated in the offscreen pytest environment. **Resolution:** Added explicit `QApplication` creation before `build_main_window` in the test.
2. **`QApplication.toolTip()` does not exist in PyQt6:** `test_hover_over_polling_indicator_reveals_timestamp` used `QApplication.toolTip()`. **Resolution:** Changed to `indicator.toolTip()`, which verifies the widget's tooltip property directly.
3. **`aboutToQuit` requires a running event loop:** `test_exit_from_system_tray_context_menu` expected `aboutToQuit` to fire after `QApplication.quit()` in a headless test without `exec()`. **Resolution:** Verified `worker.finished` emission instead, which is the direct synchronous effect of the tray exit handler.
4. **PyQt6 6.11 `QMouseEvent` constructor requires `QPointF`:** `test_frameless_window_drag_behavior` used `QPoint` for `QMouseEvent` constructor arguments. **Resolution:** Updated to `QPointF` with matching local and global positions.

---

## Test Coverage Summary

| Category | Tests | Status |
|----------|-------|--------|
| Startup / Smoke | 2 | ✅ Pass |
| Worker Thread | 4 | ✅ Pass |
| Sensor Reading (mocked) | 14 | ✅ Pass |
| UI Layout (AST) | 5 | ✅ Pass |
| Window Behavior | 4 | ✅ Pass |
| Settings Persistence | 5 | ✅ Pass |
| System Theme | 3 | ✅ Pass |
| UI Interactions (pytest-qt) | 10 | ✅ Pass |
| **Total** | **47** | **47 Pass / 0 Fail / 0 Skip** |

---

## Known Limitations / Notes

- `datetime.utcnow()` deprecation warnings are emitted from `src/sensor_readers.py` and `src/main_window.py`. These are warnings, not errors, and do not affect test outcomes.
- The offscreen platform does not support `QSystemTrayIcon` icon rendering or window raise; Qt warning messages are emitted but do not affect functionality or test results.
- All external sensor dependencies (`psutil`, `pynvml`, `wmi`, `clr` / LibreHardwareMonitor) are mocked or monkeypatched in tests.

---

## Sign-off

**QA Agent:** Automated  
**Result:** GO — All gates pass. Ready for packaging.
