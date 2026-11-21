"""
test_serial_protocol.py — Unit Tests for ESP32 Serial Protocol Parser
=====================================================================
Tests parsing of standard telemetry frames, NaN handling for faulty sensors,
malformed tokens, out-of-range sensor readings, and command strings.
"""

import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.serial_communication import ESP32SerialBridge


class TestSerialProtocol(unittest.TestCase):

    def test_parse_valid_telemetry_packet(self):
        """Test standard formatted packet from ESP32: SENSOR,26.4,58.2,1"""
        line = "SENSOR,26.4,58.2,1"
        res = ESP32SerialBridge.parse_sensor_packet(line)

        self.assertTrue(res["valid"])
        self.assertEqual(res["temperature"], 26.4)
        self.assertEqual(res["humidity"], 58.2)
        self.assertEqual(res["pir_state"], 1)

    def test_parse_nan_sensor_readings(self):
        """Test handling of NaN readings when DHT22 cable is disconnected."""
        line = "SENSOR,NAN,NAN,0"
        res = ESP32SerialBridge.parse_sensor_packet(line)

        self.assertTrue(res["valid"])
        self.assertIsNone(res["temperature"])
        self.assertIsNone(res["humidity"])
        self.assertEqual(res["pir_state"], 0)

    def test_parse_malformed_packets(self):
        """Ensure incomplete or corrupted packets are rejected gracefully without crashing."""
        invalid_packets = [
            "",
            "HELLO,WORLD",
            "SENSOR",
            "SENSOR,25.4",
            "SENSOR,25.4,50.0",  # Missing PIR field
            "DATA,25.4,50.0,1",  # Wrong prefix
            "SENSOR,abc,def,xyz",
        ]
        for pkt in invalid_packets:
            res = ESP32SerialBridge.parse_sensor_packet(pkt)
            self.assertFalse(res["valid"], f"Expected packet '{pkt}' to be marked invalid.")

    def test_parse_out_of_range_temperature(self):
        """Ensure unrealistic physical values (e.g. 150 C) are filtered out."""
        line = "SENSOR,150.0,50.0,0"
        res = ESP32SerialBridge.parse_sensor_packet(line)
        self.assertTrue(res["valid"])
        self.assertIsNone(res["temperature"])  # Out of valid DHT22 range (-40 to +85 C)
        self.assertEqual(res["humidity"], 50.0)

    def test_command_string_safety(self):
        """Test that buzzer actuation commands contain the required protocol format."""
        bridge = ESP32SerialBridge()
        bridge._enter_simulation()

        # In simulation mode, send_command should toggle internal state safely
        success_on = bridge.send_command("BUZZER:ON")
        self.assertTrue(success_on)
        self.assertTrue(bridge.latest_telemetry["buzzer_on"])

        success_off = bridge.send_command("BUZZER:OFF")
        self.assertTrue(success_off)
        self.assertFalse(bridge.latest_telemetry["buzzer_on"])


if __name__ == "__main__":
    unittest.main()
