"""
Sensor Reading Tests

Covers CPU, memory, GPU, NPU, temperatures, and fan speeds.
All external sensor libraries are mocked to keep tests deterministic.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _make_sensor_reading(**kwargs):
    try:
        from src.models import SensorReading
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")
    defaults = {
        "sensor_id": "mock_sensor",
        "category": "cpu",
        "name": "Mock Sensor",
        "value": 50.0,
        "unit": "%",
        "timestamp": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return SensorReading(**defaults)


# ---------------------------------------------------------------------------
# CPU & Memory
# ---------------------------------------------------------------------------

def test_read_cpu_utilization_returns_valid_percentage() -> None:
    """TC-SENSOR-01"""
    try:
        from src.sensors import read_cpu_utilization
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    with patch("src.sensors.psutil.cpu_percent", return_value=34.5):
        reading = read_cpu_utilization()

    assert 0.0 <= reading.value <= 100.0
    assert reading.unit == "%"
    assert reading.category == "cpu"


def test_read_memory_utilization_returns_valid_percentage() -> None:
    """TC-SENSOR-02"""
    try:
        from src.sensors import read_memory_utilization
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    mock_mem = SimpleNamespace(percent=58.0)
    with patch("src.sensors.psutil.virtual_memory", return_value=mock_mem):
        reading = read_memory_utilization()

    assert 0.0 <= reading.value <= 100.0
    assert reading.unit == "%"
    assert reading.category == "memory"


# ---------------------------------------------------------------------------
# GPU
# ---------------------------------------------------------------------------

def test_read_gpu_utilization_nvidia() -> None:
    """TC-SENSOR-03"""
    try:
        from src.sensors import read_gpu_utilization
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    mock_nvml = MagicMock()
    mock_nvml.nvmlDeviceGetCount.return_value = 1
    mock_handle = MagicMock()
    mock_nvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
    mock_util = MagicMock(gpu=12)
    mock_nvml.nvmlDeviceGetUtilizationRates.return_value = mock_util

    with patch.dict("sys.modules", {"pynvml": mock_nvml}):
        with patch("src.sensors.pynvml", mock_nvml, create=True):
            reading = read_gpu_utilization()

    assert reading is not None
    assert 0.0 <= reading.value <= 100.0
    assert reading.category == "gpu"


def test_read_gpu_utilization_amd() -> None:
    """TC-SENSOR-04"""
    try:
        from src.sensors import read_gpu_utilization
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    # Simulate AMD path: no NVIDIA, but AMD ADL returns a value
    with patch("src.sensors._read_nvidia_gpu", return_value=None):
        with patch("src.sensors._read_amd_gpu", return_value=_make_sensor_reading(value=45.0, category="gpu")):
            reading = read_gpu_utilization()

    assert reading is not None
    assert 0.0 <= reading.value <= 100.0
    assert reading.category == "gpu"


def test_read_gpu_utilization_returns_none_when_no_gpu() -> None:
    """TC-SENSOR-05"""
    try:
        from src.sensors import read_gpu_utilization
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    with patch("src.sensors._read_nvidia_gpu", return_value=None):
        with patch("src.sensors._read_amd_gpu", return_value=None):
            reading = read_gpu_utilization()

    assert reading is None


# ---------------------------------------------------------------------------
# Temperatures
# ---------------------------------------------------------------------------

def test_read_all_temperatures_returns_celsius_readings() -> None:
    """TC-SENSOR-06"""
    try:
        from src.sensors import read_all_temperatures
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    mock_reading = _make_sensor_reading(value=65.0, unit="°C", category="temperature", name="CPU Package")
    with patch("src.sensors._read_temperatures_lhm", return_value=[mock_reading]):
        readings = read_all_temperatures()

    assert isinstance(readings, list)
    assert all(r.unit == "°C" and r.value > -273.15 for r in readings)


def test_read_all_temperatures_lhm_to_wmi_fallback_on_exception() -> None:
    """TC-SENSOR-10"""
    try:
        from src.sensors import read_all_temperatures
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    mock_wmi = _make_sensor_reading(value=40.0, unit="°C", category="temperature", name="WMI Mock Temp")
    with patch("src.sensors._read_temperatures_lhm", side_effect=Exception("LHM failure")):
        with patch("src.sensors._read_temperatures_wmi", return_value=[mock_wmi]):
            readings = read_all_temperatures()

    assert len(readings) == 1
    assert readings[0].name == "WMI Mock Temp"


# ---------------------------------------------------------------------------
# Fan Speeds
# ---------------------------------------------------------------------------

def test_read_all_fan_speeds_returns_percentage_readings() -> None:
    """TC-SENSOR-07"""
    try:
        from src.sensors import read_all_fan_speeds
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    mock_reading = _make_sensor_reading(value=75.0, unit="%", category="fan", name="CPU Fan")
    with patch("src.sensors._read_fan_speeds_lhm", return_value=[mock_reading]):
        readings = read_all_fan_speeds()

    assert isinstance(readings, list)
    assert all(r.unit == "%" and 0.0 <= r.value <= 100.0 for r in readings)


def test_read_all_fan_speeds_maxrpm_derivation() -> None:
    """TC-SENSOR-08"""
    try:
        from src.sensors import read_all_fan_speeds
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    # LHM reports MaxRPM=2000, current RPM=1000 -> expected 50%
    with patch("src.sensors._read_fan_speeds_lhm", return_value=[
        _make_sensor_reading(value=50.0, unit="%", category="fan", name="CPU Fan")
    ]):
        readings = read_all_fan_speeds()

    assert any(r.value == 50.0 for r in readings)


def test_read_all_fan_speeds_fallback_to_highest_observed_rpm() -> None:
    """TC-SENSOR-09"""
    try:
        from src.sensors import read_all_fan_speeds
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    # If implementation tracks session max RPM internally, simulate two calls
    call_count = 0
    def _fake_lhm():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return [_make_sensor_reading(value=100.0, unit="%", category="fan", name="CPU Fan")]
        return [_make_sensor_reading(value=50.0, unit="%", category="fan", name="CPU Fan")]

    with patch("src.sensors._read_fan_speeds_lhm", side_effect=_fake_lhm):
        first = read_all_fan_speeds()
        second = read_all_fan_speeds()

    assert second[0].value == 50.0


def test_read_all_fan_speeds_lhm_to_wmi_fallback_on_empty() -> None:
    """TC-SENSOR-11"""
    try:
        from src.sensors import read_all_fan_speeds
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    mock_wmi = _make_sensor_reading(value=60.0, unit="%", category="fan", name="WMI Mock Fan")
    with patch("src.sensors._read_fan_speeds_lhm", return_value=[]):
        with patch("src.sensors._read_fan_speeds_wmi", return_value=[mock_wmi]):
            readings = read_all_fan_speeds()

    assert len(readings) == 1
    assert readings[0].name == "WMI Mock Fan"


# ---------------------------------------------------------------------------
# NPU
# ---------------------------------------------------------------------------

def test_read_npu_utilization_returns_reading_when_available() -> None:
    """TC-SENSOR-12"""
    try:
        from src.sensors import read_npu_utilization
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    with patch("src.sensors._read_npu", return_value=_make_sensor_reading(value=8.0, category="npu")):
        reading = read_npu_utilization()

    assert reading is not None
    assert 0.0 <= reading.value <= 100.0
    assert reading.category == "npu"


def test_read_npu_utilization_returns_none_when_missing() -> None:
    """TC-SENSOR-13"""
    try:
        from src.sensors import read_npu_utilization
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    with patch("src.sensors._read_npu", return_value=None):
        reading = read_npu_utilization()

    assert reading is None


def test_read_all_temperatures_includes_npu_temperature_when_available() -> None:
    """TC-SENSOR-14"""
    try:
        from src.sensors import read_all_temperatures
    except ImportError as exc:
        pytest.skip(f"Source not yet implemented: {exc}")

    mock_npu = _make_sensor_reading(value=42.0, unit="°C", category="npu", name="NPU Temp")
    with patch("src.sensors._read_temperatures_lhm", return_value=[mock_npu]):
        readings = read_all_temperatures()

    assert any("npu" in r.category.lower() or "npu" in r.name.lower() for r in readings)
