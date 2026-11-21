"""
upload_firmware.py — Automated 1-Click ESP32 Firmware Flasher
=============================================================
Scans for ESP32 COM port and flashes the pre-compiled binary using esptool.exe.
"""

import sys
import os
import time
import subprocess
from pathlib import Path
import serial.tools.list_ports

PROJECT_ROOT = Path(__file__).resolve().parent
ESPTOOL_EXE = Path("C:/Users/shahj/AppData/Local/Arduino15/packages/esp32/tools/esptool_py/5.3.1/esptool.exe")
MERGED_BIN = PROJECT_ROOT / "esp32_firmware" / "build" / "eye_monitor_esp32.ino.merged.bin"


def find_com_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = (p.description or "").upper()
        if any(k in desc for k in ["CP210", "CH340", "USB SERIAL", "UART", "ESP32", "SERIAL"]):
            return p.device
    if ports:
        return ports[0].device
    return None


def upload(port: str) -> bool:
    print(f"\n[INFO] Found ESP32 on port: {port}")
    
    for baud in ["921600", "460800", "115200"]:
        print(f"[INFO] Attempting to flash firmware at {baud} baud...")
        cmd = [
            str(ESPTOOL_EXE),
            "--chip", "esp32",
            "--port", port,
            "--baud", baud,
            "--before", "default-reset",
            "--after", "hard-reset",
            "write-flash",
            "-z",
            "--flash_mode", "dio",
            "--flash_freq", "80m",
            "--flash_size", "4MB",
            "0x0", str(MERGED_BIN)
        ]

        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
            print(proc.stdout)
            if proc.returncode == 0:
                print("\n" + "=" * 65)
                print("  [SUCCESS] FIRMWARE UPLOAD COMPLETE!")
                print("  Your ESP32 is now flashed and running the eye monitor system.")
                print("  Buzzer and LED will beep 3 times at startup!")
                print("=" * 65 + "\n")
                return True
            else:
                print(f"[RETRY] Flashing at {baud} baud did not succeed. Trying fallback baud rate...")
        except Exception as e:
            print(f"[ERROR] Failed to run esptool: {e}")

    print("\n[FAIL] Flashing failed on all baud rates.")
    print("TIP: Hold down the 'BOOT' button on the ESP32 while plugging it in, then try again.")
    return False


def main():
    print("=" * 65)
    print("  ESP32 AUTOMATED FIRMWARE UPLOADER")
    print("=" * 65)

    port = find_com_port()
    if port:
        upload(port)
        return

    print("\n[WAITING] Scanning for ESP32 COM port...")
    print("          If your ESP32 driver is not installed yet, please double-click:")
    print("          'INSTALL_DRIVER.bat' to install the CP2102 driver.")
    print("          Waiting (Press Ctrl+C to cancel)...")

    while True:
        time.sleep(1.5)
        port = find_com_port()
        if port:
            upload(port)
            break


if __name__ == "__main__":
    main()
