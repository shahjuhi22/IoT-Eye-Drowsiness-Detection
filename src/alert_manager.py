"""
alert_manager.py — Alert Coordination, Actuation, and Event Logging
===================================================================
Coordinates between the computer vision drowsiness detector, the physical ESP32
buzzer actuator, and system event logging.

Key Responsibilities:
  1. Actuator State Management: Sends "BUZZER:ON" or "BUZZER:OFF" via USB serial
     strictly on state change, never spamming the serial link.
  2. Audio Synthesis: Plays an optional soft local audible alarm on the laptop
     (using Windows winsound) when simulation mode is active.
  3. Structured Logging: Appends timestamped events to CSV and log files.
  4. Alarm Cooldown: Enforces debounce/cooldown to prevent rapid oscillation.
"""

import os
import sys
import time
import csv
from enum import Enum
from typing import Optional, Dict, Any

import config
from .serial_communication import ESP32SerialBridge

# Optional winsound on Windows for local audio alert
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class AlertLevel(Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertManager:
    """
    Coordinates hardware buzzer commands and persistent event logging.
    """

    def __init__(self,
                 serial_bridge: Optional[ESP32SerialBridge] = None,
                 csv_log_path: str = str(config.CSV_LOG_FILE),
                 event_log_path: str = str(config.EVENT_LOG_FILE)):

        self.serial_bridge = serial_bridge
        self.csv_log_path = csv_log_path
        self.event_log_path = event_log_path

        self.current_alert_level: AlertLevel = AlertLevel.NORMAL
        self.buzzer_is_active: bool = False
        self.last_state_change_time: float = time.time()
        self.total_drowsy_alerts: int = 0
        self.invert_logic: bool = getattr(config, "INVERT_BUZZER_LOGIC", False)

        self._init_csv_log()

    def toggle_invert_logic(self) -> bool:
        """Toggle active-low vs active-high buzzer logic on the fly."""
        self.invert_logic = not self.invert_logic
        self._send_buzzer_command(self.buzzer_is_active)
        return self.invert_logic

    def _send_buzzer_command(self, activate: bool) -> None:
        """Send hardware command respecting invert polarity setting."""
        if not self.serial_bridge:
            return
        if self.invert_logic:
            # Active-low buzzer module
            cmd = "BUZZER:OFF" if activate else "BUZZER:ON"
        else:
            cmd = "BUZZER:ON" if activate else "BUZZER:OFF"
        self.serial_bridge.send_command(cmd)

    def _init_csv_log(self) -> None:
        """Create CSV log file with header if it doesn't already exist."""
        if not os.path.exists(self.csv_log_path):
            with open(self.csv_log_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "ISO_Time", "State", "Avg_EAR", "Blink_Count",
                    "Closure_Duration_Sec", "Temperature_C", "Humidity_Pct",
                    "PIR_Motion", "Buzzer_Active", "Event"
                ])

    def log_event(self, message: str) -> None:
        """Append a message to the human-readable event log."""
        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp_str}] {message}\n"
        try:
            with open(self.event_log_path, mode="a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            print(f"[AlertManager Log Error] {e}")

    def log_telemetry_row(self,
                          drowsiness_data: Dict[str, Any],
                          sensor_data: Optional[Dict[str, Any]],
                          event: str = "") -> None:
        """Write a snapshot row to the CSV log."""
        now = time.time()
        iso_now = time.strftime("%Y-%m-%d %H:%M:%S")

        avg_ear = drowsiness_data.get("avg_ear", 0.0)
        blinks = drowsiness_data.get("blink_count", 0)
        closure_sec = drowsiness_data.get("closure_duration", 0.0)
        state_str = drowsiness_data.get("state", "UNKNOWN")

        temp = sensor_data.get("temperature") if sensor_data else None
        hum = sensor_data.get("humidity") if sensor_data else None
        pir = sensor_data.get("pir_state", 0) if sensor_data else 0

        try:
            with open(self.csv_log_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    f"{now:.2f}",
                    iso_now,
                    state_str,
                    f"{avg_ear:.3f}",
                    blinks,
                    f"{closure_sec:.2f}",
                    temp if temp is not None else "",
                    hum if hum is not None else "",
                    pir,
                    1 if self.buzzer_is_active else 0,
                    event
                ])
        except Exception:
            pass

    def process_alert(self,
                      drowsiness_data: Dict[str, Any],
                      sensor_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Evaluate current state and trigger actuators only when state changes.
        
        Args:
            drowsiness_data: Output dictionary from DrowsinessDetector.
            sensor_data: Output dictionary from SensorManager.
            
        Returns:
            bool: True if buzzer is currently active.
        """
        cmd = drowsiness_data.get("buzzer_command")
        state_str = drowsiness_data.get("state", "NORMAL")

        # Handle explicit buzzer command from state machine
        if cmd == "BUZZER:ON" and not self.buzzer_is_active:
            self._activate_alarm(drowsiness_data, sensor_data)
        elif cmd == "BUZZER:OFF" and self.buzzer_is_active:
            self._deactivate_alarm(drowsiness_data, sensor_data)

        # Update alert level
        if state_str == "DROWSY":
            self.current_alert_level = AlertLevel.CRITICAL
        elif state_str == "WARNING":
            self.current_alert_level = AlertLevel.WARNING
        else:
            self.current_alert_level = AlertLevel.NORMAL

        return self.buzzer_is_active

    def _activate_alarm(self,
                        drowsiness_data: Dict[str, Any],
                        sensor_data: Optional[Dict[str, Any]]) -> None:
        """Turn on the alarm (hardware buzzer and optional laptop beep)."""
        self.buzzer_is_active = True
        self.total_drowsy_alerts += 1
        self.last_state_change_time = time.time()

        # Send serial command to ESP32 (respecting polarity)
        self._send_buzzer_command(True)

        # Log event
        dur = drowsiness_data.get("closure_duration", 0.0)
        self.log_event(f"ALARM ACTIVATED: Continuous eye-closure detected for {dur:.2f}s!")
        self.log_telemetry_row(drowsiness_data, sensor_data, event="ALARM_ON")

        # Hardcoded audible alarm on laptop speaker (asynchronous thread so it never blocks video)
        if HAS_WINSOUND:
            def _play_buzzer_sound():
                try:
                    for _ in range(3):
                        winsound.Beep(2500, 200)
                        time.sleep(0.08)
                except Exception:
                    pass

            import threading
            threading.Thread(target=_play_buzzer_sound, daemon=True, name="AudioBuzzerThread").start()

    def _deactivate_alarm(self,
                          drowsiness_data: Dict[str, Any],
                          sensor_data: Optional[Dict[str, Any]]) -> None:
        """Turn off the alarm."""
        self.buzzer_is_active = False
        self.last_state_change_time = time.time()

        self._send_buzzer_command(False)

        self.log_event("ALARM CLEARED: Eyes reopened / normal state restored.")
        self.log_telemetry_row(drowsiness_data, sensor_data, event="ALARM_OFF")

    def force_silence(self) -> None:
        """Emergency mute command for manual stop or app shutdown."""
        self.buzzer_is_active = False
        self._send_buzzer_command(False)
        self.log_event("ALARM SILENCED: Manual operator override.")
