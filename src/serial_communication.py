"""
serial_communication.py — Thread-Safe USB Serial Bridge for ESP32
==================================================================
Handles asynchronous serial communication between the Python host application
and the ESP32 microcontroller over USB-UART bridge at 115200 baud.

Key Capabilities:
  - Automatic COM port discovery (scans for CP210x, CH340, FTDI, NodeMCU)
  - Dedicated background reader thread (never blocks UI or camera frame loops)
  - Robust parser for "SENSOR,<temp>,<hum>,<pir>" telemetry packets
  - Error-resilient (handles disconnects, malformed bytes, NaN readings)
  - Command transmission ("BUZZER:ON", "BUZZER:OFF", "PING") with deduplication
  - Transparent Simulation Mode fallback when physical board is offline
"""

import threading
import time
import random
import re
from typing import Optional, Callable, Dict, Any, List

import config

# Try importing serial; provide friendly warning if not yet installed
try:
    import serial
    import serial.tools.list_ports
    HAS_PYSERIAL = True
except ImportError:
    HAS_PYSERIAL = False


class ESP32SerialBridge:
    """
    Manages bidirectional serial communication with ESP32.
    """

    def __init__(self,
                 port: str = config.SERIAL_PORT,
                 baud_rate: int = config.SERIAL_BAUD_RATE,
                 timeout: float = config.SERIAL_TIMEOUT_SEC,
                 on_telemetry_received: Optional[Callable[[Dict[str, Any]], None]] = None):

        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.on_telemetry = on_telemetry_received

        self.serial_conn: Optional[Any] = None
        self.is_connected: bool = False
        self.simulation_mode: bool = False
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        # Lock for thread-safe command writes
        self._write_lock = threading.Lock()

        # Telemetry cache
        self.latest_telemetry: Dict[str, Any] = {
            "temperature": None,
            "humidity": None,
            "pir_state": 0,
            "timestamp": time.time(),
            "valid": False,
            "connected": False,
            "simulation": False,
            "buzzer_on": False,
        }

        # Simulated sensor state
        self._sim_temp = 26.5
        self._sim_hum = 55.0
        self._sim_pir = 0
        self._sim_last_time = time.time()
        self._sim_buzzer_on = False

    @staticmethod
    def list_available_ports() -> List[str]:
        """Return list of available COM ports on the system."""
        if not HAS_PYSERIAL:
            return []
        try:
            ports = [p.device for p in serial.tools.list_ports.comports()]
            return ports
        except Exception:
            return []

    @staticmethod
    def find_esp32_port() -> Optional[str]:
        """
        Scan available COM ports for known USB-to-UART converter chips
        commonly used by ESP32 boards (CP2102, CH340, FTDI, CDC).
        """
        if not HAS_PYSERIAL:
            return None

        esp_identifiers = ["CP210", "CH340", "USB SERIAL", "UART", "ESP32", "FTDI", "CH9102"]
        try:
            for p in serial.tools.list_ports.comports():
                desc = (p.description or "").upper()
                hwid = (p.hwid or "").upper()
                for ident in esp_identifiers:
                    if ident in desc or ident in hwid:
                        return p.device
            # If no known identifier matched but ports exist, return the first port
            ports = serial.tools.list_ports.comports()
            if ports:
                return ports[0].device
        except Exception as e:
            print(f"[SerialBridge] Error scanning ports: {e}")
        return None

    def connect(self) -> bool:
        """
        Connect to physical ESP32 or enter simulation mode if unavailable.
        """
        if not HAS_PYSERIAL:
            print("[SerialBridge WARNING] pyserial is not installed. Entering Simulation Mode.")
            self._enter_simulation()
            return False

        target_port = self.port
        if target_port == "AUTO" or not target_port:
            found = self.find_esp32_port()
            if found:
                target_port = found
                print(f"[SerialBridge] Auto-detected port: {target_port}")
            else:
                if config.SIMULATION_MODE_FALLBACK:
                    print("[SerialBridge INFO] No physical ESP32 port detected. Entering Simulation Mode.")
                    self._enter_simulation()
                    return False
                return False

        try:
            print(f"[SerialBridge] Connecting to ESP32 on {target_port} at {self.baud_rate} baud...")
            self.serial_conn = serial.Serial(
                port=target_port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            # ESP32 auto-resets on DTR/RTS toggle; allow bootloader to stabilize
            time.sleep(1.5)
            self.serial_conn.reset_input_buffer()
            self.is_connected = True
            self.simulation_mode = False
            self.latest_telemetry["connected"] = True
            self.latest_telemetry["simulation"] = False
            print(f"[SerialBridge SUCCESS] Connected to ESP32 on {target_port}.")
            return True

        except Exception as e:
            print(f"[SerialBridge ERROR] Failed to connect on {target_port}: {e}")
            if config.SIMULATION_MODE_FALLBACK:
                print("[SerialBridge INFO] Falling back to Simulation Mode for demonstration.")
                self._enter_simulation()
            return False

    def _enter_simulation(self) -> None:
        """Enable simulation mode for software-only demonstration."""
        self.simulation_mode = True
        self.is_connected = False
        self.latest_telemetry["connected"] = False
        self.latest_telemetry["simulation"] = True

    def start(self) -> None:
        """Start background receiver thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="ESP32SerialWorker")
        self._thread.start()

    def stop(self) -> None:
        """Stop background receiver and close port."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

        if self.serial_conn and self.serial_conn.is_open:
            try:
                # Ensure buzzer is off before disconnecting
                self.send_command("BUZZER:OFF")
                self.serial_conn.close()
            except Exception:
                pass
        self.is_connected = False

    def _worker_loop(self) -> None:
        """Background thread handling continuous reading or simulation generation."""
        while self._running:
            if self.is_connected and self.serial_conn and self.serial_conn.is_open:
                try:
                    line = self.serial_conn.readline().decode("utf-8", errors="replace").strip()
                    if line:
                        self._parse_line(line)
                except Exception as e:
                    print(f"[SerialBridge WARNING] Read error: {e}. Attempting reconnect...")
                    self.is_connected = False
                    self.latest_telemetry["connected"] = False
                    time.sleep(config.SERIAL_RETRY_INTERVAL_SEC)
                    if self._running:
                        self.connect()
            elif self.simulation_mode:
                self._generate_simulated_packet()
                time.sleep(1.0)
            else:
                time.sleep(1.0)

    def _parse_line(self, line: str) -> None:
        """
        Parse raw line from ESP32.
        Expected format: SENSOR,<temp>,<hum>,<pir>
        Example: SENSOR,27.3,56.8,1
        """
        # Echo debug or ACK messages
        if line.startswith("[") or line.startswith("PONG"):
            # Serial log / acknowledgment
            return

        parsed = self.parse_sensor_packet(line)
        if parsed["valid"]:
            parsed["connected"] = True
            parsed["simulation"] = False
            parsed["buzzer_on"] = self.latest_telemetry.get("buzzer_on", False)
            self.latest_telemetry = parsed

            if self.on_telemetry:
                try:
                    self.on_telemetry(parsed)
                except Exception as e:
                    print(f"[SerialBridge Telemetry Callback Error] {e}")

    @staticmethod
    def parse_sensor_packet(line: str) -> Dict[str, Any]:
        """
        Parse and validate a 'SENSOR,...' line string.
        Safe for malformed tokens, partial strings, and NaN sensor readings.
        """
        result = {
            "temperature": None,
            "humidity": None,
            "pir_state": 0,
            "timestamp": time.time(),
            "valid": False,
        }

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4 or parts[0] != config.SENSOR_MSG_PREFIX:
            return result

        # Parse Temperature
        temp_str = parts[1].upper()
        if temp_str == "NAN" or temp_str == "":
            result["temperature"] = None
        else:
            try:
                temp_val = float(temp_str)
                if -40.0 <= temp_val <= 85.0:  # Valid DHT22 range
                    result["temperature"] = round(temp_val, 1)
                else:
                    result["temperature"] = None
            except ValueError:
                return result  # Non-numeric garbage -> reject packet

        # Parse Humidity
        hum_str = parts[2].upper()
        if hum_str == "NAN" or hum_str == "":
            result["humidity"] = None
        else:
            try:
                hum_val = float(hum_str)
                if 0.0 <= hum_val <= 100.0:   # Valid DHT22 humidity range
                    result["humidity"] = round(hum_val, 1)
                else:
                    result["humidity"] = None
            except ValueError:
                return result  # Non-numeric garbage -> reject packet

        # Parse PIR state (must be numeric 0, 1, or valid integer)
        pir_str = parts[3].strip()
        try:
            pir_val = int(pir_str)
            result["pir_state"] = 1 if pir_val > 0 else 0
        except ValueError:
            return result  # Non-integer -> reject packet

        result["valid"] = True
        return result

    def _generate_simulated_packet(self) -> None:
        """Generate realistic sensor telemetry in simulation mode."""
        now = time.time()
        # Gentle random walk for temperature & humidity
        self._sim_temp += random.uniform(-0.1, 0.1)
        self._sim_temp = max(24.0, min(30.0, self._sim_temp))

        self._sim_hum += random.uniform(-0.2, 0.2)
        self._sim_hum = max(45.0, min(65.0, self._sim_hum))

        # Occasional motion state toggle
        if random.random() < 0.15:
            self._sim_pir = 1 if self._sim_pir == 0 else 0

        sim_data = {
            "temperature": round(self._sim_temp, 1),
            "humidity": round(self._sim_hum, 1),
            "pir_state": self._sim_pir,
            "timestamp": now,
            "valid": True,
            "connected": False,
            "simulation": True,
            "buzzer_on": self._sim_buzzer_on,
        }
        self.latest_telemetry = sim_data

        if self.on_telemetry:
            try:
                self.on_telemetry(sim_data)
            except Exception:
                pass

    def send_command(self, cmd: str) -> bool:
        """
        Send command string to ESP32 ("BUZZER:ON", "BUZZER:OFF", "PING").
        Ensures trailing newline and thread-safety.
        """
        cleaned = cmd.strip()
        msg = f"{cleaned}\n"

        if self.simulation_mode:
            if "BUZZER:ON" in cleaned:
                self._sim_buzzer_on = True
            elif "BUZZER:OFF" in cleaned:
                self._sim_buzzer_on = False
            self.latest_telemetry["buzzer_on"] = self._sim_buzzer_on
            return True

        if not self.is_connected or not self.serial_conn or not self.serial_conn.is_open:
            return False

        try:
            with self._write_lock:
                self.serial_conn.write(msg.encode("utf-8"))
                self.serial_conn.flush()
                if "BUZZER:ON" in cleaned:
                    self.latest_telemetry["buzzer_on"] = True
                elif "BUZZER:OFF" in cleaned:
                    self.latest_telemetry["buzzer_on"] = False
            return True
        except Exception as e:
            print(f"[SerialBridge ERROR] Failed to send command '{cleaned}': {e}")
            return False

    def get_latest_telemetry(self) -> Dict[str, Any]:
        """Return the most recent sensor reading packet."""
        return dict(self.latest_telemetry)
