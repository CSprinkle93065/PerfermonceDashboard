from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SensorReading:
    sensor_id: str
    category: str
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Settings:
    refresh_interval_ms: int = 1000
    always_on_top: bool = True
    show_utilization: bool = True
    show_temperatures: bool = True
    show_fan_speeds: bool = True
    window_x: int | None = None
    window_y: int | None = None
