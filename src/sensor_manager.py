"""
sensor_manager.py — IoT Environmental Telemetry & Data Management
==================================================================
Manages environmental sensor data collected from the ESP32 (DHT22 & PIR).
Tracks historical readings for dashboard visualization, computes running
averages, and evaluates environmental risk factors that exacerbate fatigue
(e.g., high cabin temperature, stagnant air, lack of driver movement).
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

import config


@dataclass
class SensorReading:
    """Represents a single timestamped sensor measurement."""
    temperature: Optional[float]
    humidity: Optional[float]
    pir_state: int
    timestamp: float = field(default_factory=time.time)
    connected: bool = False
    simulation: bool = False
    buzzer_on: bool = False


class SensorManager:
    """
    Maintains current and historical sensor readings, calculates moving averages,
    and detects ambient environmental conditions that impact alertness.
    """

    def __init__(self, history_maxlen: int = 120):
        self.history_maxlen = history_maxlen
        self.history: deque = deque(maxlen=history_maxlen)

        # Latest reading
        self.current = SensorReading(
            temperature=None,
            humidity=None,
            pir_state=0,
            connected=False,
            simulation=False,
            buzzer_on=False
        )

        # Environmental risk flags
        self.high_temp_warning = False
        self.low_temp_warning = False
        self.high_humidity_warning = False
        self.motion_detected = False
        self.last_motion_time = time.time()

    def update_from_dict(self, data: Dict[str, Any]) -> SensorReading:
        """
        Update current readings from serial bridge dictionary.
        """
        temp = data.get("temperature")
        hum = data.get("humidity")
        pir = int(data.get("pir_state", 0))
        conn = bool(data.get("connected", False))
        sim = bool(data.get("simulation", False))
        buzzer = bool(data.get("buzzer_on", False))
        ts = data.get("timestamp", time.time())

        reading = SensorReading(
            temperature=temp,
            humidity=hum,
            pir_state=pir,
            timestamp=ts,
            connected=conn,
            simulation=sim,
            buzzer_on=buzzer
        )

        self.current = reading
        self.history.append(reading)

        # Check environmental conditions
        if temp is not None:
            self.high_temp_warning = temp >= config.TEMP_WARNING_HIGH_C
            self.low_temp_warning = temp <= config.TEMP_WARNING_LOW_C
        if hum is not None:
            self.high_humidity_warning = hum >= config.HUMIDITY_WARNING_HIGH

        if pir == 1:
            self.motion_detected = True
            self.last_motion_time = ts
        else:
            self.motion_detected = False

        return reading

    def get_summary(self) -> Dict[str, Any]:
        """
        Return comprehensive status dictionary for dashboard and video overlay.
        """
        curr = self.current
        return {
            "temperature": curr.temperature,
            "humidity": curr.humidity,
            "pir_state": curr.pir_state,
            "motion_detected": self.motion_detected,
            "connected": curr.connected,
            "simulation": curr.simulation,
            "buzzer_on": curr.buzzer_on,
            "high_temp_warning": self.high_temp_warning,
            "low_temp_warning": self.low_temp_warning,
            "high_humidity_warning": self.high_humidity_warning,
            "seconds_since_motion": time.time() - self.last_motion_time,
            "samples_count": len(self.history),
        }

    def get_history_series(self) -> Dict[str, List[Any]]:
        """
        Extract time-series lists of recent readings for plotting in Streamlit.
        """
        timestamps = []
        temps = []
        humidities = []
        pirs = []

        for r in self.history:
            timestamps.append(time.strftime("%H:%M:%S", time.localtime(r.timestamp)))
            temps.append(r.temperature if r.temperature is not None else 0.0)
            humidities.append(r.humidity if r.humidity is not None else 0.0)
            pirs.append(r.pir_state)

        return {
            "time": timestamps,
            "temperature": temps,
            "humidity": humidities,
            "motion": pirs,
        }
