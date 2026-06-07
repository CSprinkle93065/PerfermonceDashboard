from __future__ import annotations

import psutil
from datetime import datetime
from typing import TYPE_CHECKING

from src.models import SensorReading

if TYPE_CHECKING:
    pass

# Session state for fan max RPM tracking when no MaxRPM is reported.
_fan_session_max: dict[str, float] = {}


def read_cpu_utilization() -> SensorReading:
    """Read overall CPU utilization percentage using psutil."""
    value = psutil.cpu_percent(interval=None)
    return SensorReading(
        sensor_id="cpu_utilization",
        category="cpu",
        name="CPU",
        value=value,
        unit="%",
        timestamp=datetime.utcnow(),
    )


def read_memory_utilization() -> SensorReading:
    """Read overall memory/RAM utilization percentage using psutil."""
    mem = psutil.virtual_memory()
    return SensorReading(
        sensor_id="memory_utilization",
        category="memory",
        name="RAM",
        value=mem.percent,
        unit="%",
        timestamp=datetime.utcnow(),
    )


def _read_nvidia_gpu() -> SensorReading | None:
    """Attempt to read NVIDIA GPU utilization via NVML."""
    try:
        import pynvml

        pynvml.nvmlInit()
        count = pynvml.nvmlDeviceGetCount()
        if count == 0:
            pynvml.nvmlShutdown()
            return None
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        pynvml.nvmlShutdown()
        return SensorReading(
            sensor_id="gpu_utilization",
            category="gpu",
            name="GPU",
            value=float(util.gpu),
            unit="%",
            timestamp=datetime.utcnow(),
        )
    except Exception:
        return None


def _read_amd_gpu() -> SensorReading | None:
    """Attempt to read AMD GPU utilization via WMI."""
    try:
        import wmi

        c = wmi.WMI(namespace="root\\wmi")
        for gpu in c.query("SELECT * FROM AmdGpu"):
            if hasattr(gpu, "GPUUsage"):
                return SensorReading(
                    sensor_id="gpu_utilization",
                    category="gpu",
                    name="GPU",
                    value=float(gpu.GPUUsage),
                    unit="%",
                    timestamp=datetime.utcnow(),
                )
    except Exception:
        pass
    return None


def read_gpu_utilization() -> SensorReading | None:
    """Read overall GPU utilization percentage.
    Supports NVIDIA GPUs (via nvidia-ml-py / NVML) and AMD GPUs.
    Returns None if no supported GPU is present.
    """
    reading = _read_nvidia_gpu()
    if reading is not None:
        return reading
    return _read_amd_gpu()


def _read_npu() -> SensorReading | None:
    """Attempt to read NPU utilization via LibreHardwareMonitor or WMI."""
    try:
        import clr

        clr.AddReference("LibreHardwareMonitorLib")
        from LibreHardwareMonitor.Hardware import Computer, SensorType

        computer = Computer()
        computer.IsNPUEnabled = True
        computer.Open()
        for hardware in computer.Hardware:
            hardware.Update()
            if "npu" in hardware.Name.lower():
                for sensor in hardware.Sensors:
                    if sensor.SensorType == SensorType.Load and sensor.Value is not None:
                        reading = SensorReading(
                            sensor_id="npu_utilization",
                            category="npu",
                            name="NPU",
                            value=float(sensor.Value),
                            unit="%",
                            timestamp=datetime.utcnow(),
                        )
                        computer.Close()
                        return reading
        computer.Close()
    except Exception:
        pass

    # WMI fallback for NPU detection
    try:
        import wmi

        c = wmi.WMI()
        for proc in c.query("SELECT * FROM Win32_Processor"):
            if "npu" in proc.Name.lower():
                # No standard WMI property for NPU utilization
                pass
    except Exception:
        pass

    return None


def read_npu_utilization() -> SensorReading | None:
    """Read overall NPU utilization percentage.
    Returns None if no NPU is present.
    """
    return _read_npu()


def _read_temperatures_lhm() -> list[SensorReading]:
    """Read temperature sensors via LibreHardwareMonitor."""
    readings: list[SensorReading] = []
    try:
        import clr

        clr.AddReference("LibreHardwareMonitorLib")
        from LibreHardwareMonitor.Hardware import Computer, SensorType

        computer = Computer()
        computer.IsCPUEnabled = True
        computer.IsGPUEnabled = True
        computer.IsMotherboardEnabled = True
        computer.IsStorageEnabled = True
        computer.IsNPUEnabled = True
        computer.Open()
        for hardware in computer.Hardware:
            hardware.Update()
            for sensor in hardware.Sensors:
                if sensor.SensorType == SensorType.Temperature and sensor.Value is not None:
                    readings.append(
                        SensorReading(
                            sensor_id=f"temp_{hardware.Identifier}_{sensor.Index}",
                            category="temperature",
                            name=str(sensor.Name),
                            value=float(sensor.Value),
                            unit="°C",
                            timestamp=datetime.utcnow(),
                        )
                    )
        computer.Close()
    except Exception as exc:
        raise RuntimeError(f"LibreHardwareMonitor temperature read failed: {exc}") from exc
    return readings


def _read_temperatures_wmi() -> list[SensorReading]:
    """Read temperature sensors via Windows WMI fallback."""
    readings: list[SensorReading] = []
    try:
        import wmi

        c = wmi.WMI(namespace="root\\wmi")
        for temp in c.query("SELECT * FROM MSAcpi_ThermalZoneTemperature"):
            if hasattr(temp, "CurrentTemperature"):
                kelvin = temp.CurrentTemperature / 10.0
                celsius = kelvin - 273.15
                readings.append(
                    SensorReading(
                        sensor_id=f"wmi_temp_{temp.InstanceName}",
                        category="temperature",
                        name="Thermal Zone",
                        value=celsius,
                        unit="°C",
                        timestamp=datetime.utcnow(),
                    )
                )
    except Exception:
        pass
    return readings


def read_all_temperatures() -> list[SensorReading]:
    """Read all available temperature sensors.
    Uses LibreHardwareMonitor as primary; falls back to WMI on failure or empty results.
    """
    try:
        readings = _read_temperatures_lhm()
        if readings:
            return readings
    except Exception:
        pass
    return _read_temperatures_wmi()


def _read_fan_speeds_lhm() -> list[SensorReading]:
    """Read fan speed sensors via LibreHardwareMonitor and normalize to percentage."""
    readings: list[SensorReading] = []
    try:
        import clr

        clr.AddReference("LibreHardwareMonitorLib")
        from LibreHardwareMonitor.Hardware import Computer, SensorType

        computer = Computer()
        computer.IsCPUEnabled = True
        computer.IsGPUEnabled = True
        computer.IsMotherboardEnabled = True
        computer.Open()
        for hardware in computer.Hardware:
            hardware.Update()
            for sensor in hardware.Sensors:
                if sensor.SensorType == SensorType.Fan and sensor.Value is not None:
                    rpm = float(sensor.Value)
                    sensor_id = f"fan_{hardware.Identifier}_{sensor.Index}"

                    max_rpm = None
                    try:
                        if hasattr(sensor, "Max") and sensor.Max is not None:
                            max_rpm = float(sensor.Max)
                    except Exception:
                        pass

                    if max_rpm and max_rpm > 0:
                        pct = (rpm / max_rpm) * 100.0
                    else:
                        session_max = _fan_session_max.get(sensor_id, rpm)
                        if rpm > session_max:
                            session_max = rpm
                            _fan_session_max[sensor_id] = session_max
                        if session_max > 0:
                            pct = (rpm / session_max) * 100.0
                        else:
                            pct = 0.0

                    readings.append(
                        SensorReading(
                            sensor_id=sensor_id,
                            category="fan",
                            name=str(sensor.Name),
                            value=min(pct, 100.0),
                            unit="%",
                            timestamp=datetime.utcnow(),
                        )
                    )
        computer.Close()
    except Exception as exc:
        raise RuntimeError(f"LibreHardwareMonitor fan read failed: {exc}") from exc
    return readings


def _read_fan_speeds_wmi() -> list[SensorReading]:
    """Read fan speed sensors via Windows WMI fallback and normalize to percentage."""
    readings: list[SensorReading] = []
    try:
        import wmi

        c = wmi.WMI(namespace="root\\wmi")
        for fan in c.query("SELECT * FROM MSFan"):
            if hasattr(fan, "DesiredSpeed"):
                rpm = float(fan.DesiredSpeed)
                sensor_id = f"wmi_fan_{fan.InstanceName}"
                session_max = _fan_session_max.get(sensor_id, rpm)
                if rpm > session_max:
                    session_max = rpm
                    _fan_session_max[sensor_id] = session_max
                if session_max > 0:
                    pct = (rpm / session_max) * 100.0
                else:
                    pct = 0.0
                readings.append(
                    SensorReading(
                        sensor_id=sensor_id,
                        category="fan",
                        name="System Fan",
                        value=min(pct, 100.0),
                        unit="%",
                        timestamp=datetime.utcnow(),
                    )
                )
    except Exception:
        pass
    return readings


def read_all_fan_speeds() -> list[SensorReading]:
    """Read all available fan speed sensors and normalize each to percentage of max.
    Uses LibreHardwareMonitor as primary; falls back to WMI on failure or empty results.
    """
    try:
        readings = _read_fan_speeds_lhm()
        if readings:
            return readings
    except Exception:
        pass
    return _read_fan_speeds_wmi()


def poll_all_sensors() -> dict[str, SensorReading]:
    """Aggregate call that executes all sensor reads and returns a merged dict."""
    results: dict[str, SensorReading] = {}

    cpu = read_cpu_utilization()
    results[cpu.sensor_id] = cpu

    mem = read_memory_utilization()
    results[mem.sensor_id] = mem

    gpu = read_gpu_utilization()
    if gpu is not None:
        results[gpu.sensor_id] = gpu

    npu = read_npu_utilization()
    if npu is not None:
        results[npu.sensor_id] = npu

    temps = read_all_temperatures()
    for t in temps:
        results[t.sensor_id] = t

    fans = read_all_fan_speeds()
    for f in fans:
        results[f.sensor_id] = f

    return results
