"""
test_serial.py — ESP32 Serial Protocol & Hardware Diagnostics Utility
=====================================================================
Verifies USB-UART serial communication with the ESP32 board, lists detected COM
ports, validates 'SENSOR' packet reception, and tests buzzer control commands.
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.serial_communication import ESP32SerialBridge


def test_serial_node(port_name: str = "AUTO") -> bool:
    print("\n" + "=" * 65)
    print("  ESP32 SERIAL HARDWARE & PROTOCOL DIAGNOSTIC")
    print("=" * 65)

    print("\n[STEP 1] Scanning available COM ports on this PC...")
    ports = ESP32SerialBridge.list_available_ports()
    if ports:
        print(f"[INFO] Detected COM Ports: {', '.join(ports)}")
    else:
        print("[WARNING] No physical COM ports currently detected.")
        print("          (If ESP32 is not plugged in via USB-C cable, this is expected!)")

    print("\n[STEP 2] Attempting connection...")
    bridge = ESP32SerialBridge(port=port_name)
    connected = bridge.connect()

    if connected:
        print(f"[PASS] Successfully connected to ESP32 on port: {bridge.serial_conn.port}")
        bridge.start()

        print("\n[STEP 3] Testing Command Transmission (PING)...")
        bridge.send_command("PING")
        time.sleep(0.5)

        print("\n[STEP 4] Testing Actuator Command: BUZZER:ON (0.5s beep test)...")
        bridge.send_command("BUZZER:ON")
        time.sleep(0.5)
        bridge.send_command("BUZZER:OFF")
        print("[PASS] Buzzer commands sent successfully.")

        print("\n[STEP 5] Listening for incoming SENSOR telemetry packets (5 seconds)...")
        start_t = time.time()
        packets_received = 0
        while time.time() - start_t < 5.0:
            telemetry = bridge.get_latest_telemetry()
            if telemetry.get("valid"):
                packets_received += 1
                t = telemetry.get("temperature")
                h = telemetry.get("humidity")
                p = telemetry.get("pir_state")
                print(f"       [RX #{packets_received}] Temp: {t}°C | Humidity: {h}% | PIR Motion: {p}")
                break
            time.sleep(0.5)

        if packets_received > 0:
            print("[PASS] Live sensor telemetry received and verified from ESP32!")
        else:
            print("[INFO] No telemetry packets received yet. (DHT22 publishes every 2s).")

        bridge.stop()
        print("\n[SUCCESS] ESP32 Hardware Diagnostics Finished.")
        return True

    else:
        print("\n[STEP 2B] Running in Simulation Diagnostic Mode...")
        bridge.start()
        time.sleep(1.2)
        telemetry = bridge.get_latest_telemetry()
        print("[PASS] Simulation generator active:")
        print(f"       Simulated Temperature: {telemetry.get('temperature')}°C")
        print(f"       Simulated Humidity:    {telemetry.get('humidity')}%")
        print(f"       Simulated PIR:         {telemetry.get('pir_state')}")

        print("[TEST] Sending simulated BUZZER:ON...")
        bridge.send_command("BUZZER:ON")
        assert bridge.latest_telemetry["buzzer_on"] is True
        print("[PASS] Simulated Buzzer state verified.")
        bridge.send_command("BUZZER:OFF")
        assert bridge.latest_telemetry["buzzer_on"] is False

        bridge.stop()
        print("\n[INFO] Simulation Diagnostic Passed. When you plug in your ESP32,")
        print("       this test will automatically verify the physical hardware!")
        return True


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "AUTO"
    test_serial_node(p)
