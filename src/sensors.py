import psutil

try:
    import pynvml
except ImportError:
    pynvml = None

from .sensor_readers import (
    read_cpu_utilization,
    read_memory_utilization,
    _read_nvidia_gpu,
    _read_amd_gpu,
    _read_npu,
    _read_temperatures_lhm,
    _read_temperatures_wmi,
    _read_fan_speeds_lhm,
    _read_fan_speeds_wmi,
)


def read_gpu_utilization():
    """Read overall GPU utilization percentage."""
    reading = _read_nvidia_gpu()
    if reading is not None:
        return reading
    return _read_amd_gpu()


def read_npu_utilization():
    """Read overall NPU utilization percentage."""
    return _read_npu()


def read_all_temperatures():
    """Read all available temperature sensors."""
    try:
        readings = _read_temperatures_lhm()
        if readings:
            return readings
    except Exception:
        pass
    return _read_temperatures_wmi()


def read_all_fan_speeds():
    """Read all available fan speed sensors and normalize to percentage."""
    try:
        readings = _read_fan_speeds_lhm()
        if readings:
            return readings
    except Exception:
        pass
    return _read_fan_speeds_wmi()


def poll_all_sensors():
    """Aggregate call that executes all sensor reads and returns a merged dict."""
    from .sensor_readers import poll_all_sensors as _poll_fn
    return _poll_fn()
