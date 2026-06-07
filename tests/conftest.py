"""pytest configuration and patches for PerfermonceDashboard tests."""

from PyQt6.QtTest import QSignalSpy

# PyQt6 6.11+ exposes QSignalSpy length via __len__ but not count().
# Tests reference count(), so we polyfill it when absent.
if not hasattr(QSignalSpy, "count"):
    QSignalSpy.count = lambda self: len(self)
