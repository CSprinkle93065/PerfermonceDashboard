# Project Context: PerfermonceDashboard

**Current Version:** 0.1.1
**GitHub Repository:** https://github.com/CSprinkle93065/PerfermonceDashboard
**Release Stage:** pre-release
**Git Branch:** main
**Last Updated:** 2026-06-07

## What This Version Contains
PerfermonceDashboard is a lightweight, frameless system performance monitoring widget for Windows. It displays real-time CPU, GPU, NPU, and Memory utilization as progress bars, plus all available temperature sensors and fan speeds (as percentage of maximum). The widget stays always-on-top when active, minimizes to the system tray, and adapts to the Windows system theme (light/dark). Settings are persisted in a JSON config file.

## Version History

| Version | Type | Date | Summary |
|---------|------|------|---------|
| 0.1.1 | bug_fix | 2026-06-07 | Fixed widget size too small (10% of screen) causing all sensor data to be invisible. Increased to max(12% width, 400) × max(25% height, 500). |
| 0.1.0 | new_project | 2026-06-06 | Initial release — system monitoring widget |

## Open Work Items
None

## Definition Summary
Single-window PyQt6 widget with frameless hints, system tray icon, and a worker thread for sensor polling. Uses psutil for CPU/RAM, nvidia-ml-py for NVIDIA GPUs, LibreHardwareMonitor DLL (with WMI fallback) for temperatures/fans/NPU. Settings stored in JSON. Packaged as single-file PyInstaller executable.
