"""
config.py — Central Configuration for IoT Eye Blink & Drowsiness Monitoring System
==================================================================================
All thresholds, timing parameters, pin numbers, and communication options
are defined here to allow easy tuning for demonstrations and evaluations.
"""

import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = DATA_DIR / "logs"
DIAGRAMS_DIR = PROJECT_ROOT / "diagrams"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Camera & Video Configuration
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0             # 0 = Default laptop webcam, 1 = External USB webcam
FRAME_WIDTH = 640            # Capture width in pixels
FRAME_HEIGHT = 480           # Capture height in pixels
TARGET_FPS = 30              # Target frame rate for video processing

# ---------------------------------------------------------------------------
# Eye Aspect Ratio (EAR) & Landmark Detection Configuration
# ---------------------------------------------------------------------------
# Standard MediaPipe Face Mesh landmark indices for Left & Right Eyes
# 6 landmarks per eye for EAR computation:
# [P1_outer_corner, P2_top_outer, P3_top_inner, P4_inner_corner, P5_bottom_inner, P6_bottom_outer]
LEFT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]

# All perimeter landmarks for drawing full eye contours on video
LEFT_EYE_CONTOUR = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
RIGHT_EYE_CONTOUR = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]

# Default EAR threshold separating OPEN vs CLOSED eyes
# An eye is considered CLOSED if EAR < EAR_THRESHOLD
DEFAULT_EAR_THRESHOLD = 0.23

# Auto-calibration parameters
# If enabled, calculates personalized baseline EAR during first N frames of normal viewing
CALIBRATION_ENABLED = True
CALIBRATION_FRAMES = 45      # ~1.5 seconds of stable open-eye capture
CALIBRATION_EAR_RATIO = 0.78 # Threshold is set to 78% of measured open-eye EAR

# ---------------------------------------------------------------------------
# Blink & Drowsiness Timing Configuration (Timestamp-Based)
# ---------------------------------------------------------------------------
# Using timestamps rather than assuming a fixed frame rate ensures reliability
# even if CPU load causes frame rate drops.
BLINK_MIN_DURATION_SEC = 0.08   # Discard optical noise shorter than 80ms
BLINK_MAX_DURATION_SEC = 0.40   # Short closure < 400ms counted as natural blink

WARNING_DURATION_SEC = 0.60     # Continuous closure >= 0.6s triggers visual warning
DROWSY_DURATION_SEC = 1.10      # Continuous closure >= 1.1s triggers Drowsiness Alert & Buzzer

# Buzzer alert cooldown in seconds (prevents hammering ESP32 with repeated serial commands)
ALERT_COOLDOWN_SEC = 1.0

# Face absence detection: if face is lost for longer than this duration, trigger warning
FACE_ABSENCE_ALERT_SEC = 3.0

# ---------------------------------------------------------------------------
# ESP32 Serial Communication Configuration
# ---------------------------------------------------------------------------
SERIAL_PORT = "AUTO"            # "AUTO" scans COM ports, or set manually e.g. "COM3"
SERIAL_BAUD_RATE = 115200       # Standard baud rate matching ESP32 firmware
SERIAL_TIMEOUT_SEC = 1.0        # Serial read/write timeout in seconds
SERIAL_RETRY_INTERVAL_SEC = 3.0 # Interval between reconnection attempts

# Simulation Mode: if True, generates realistic DHT22 & PIR readings locally
# Automatically falls back to True if physical ESP32 is not connected!
SIMULATION_MODE_FALLBACK = True

# ---------------------------------------------------------------------------
# Serial Protocol Commands & Formatting
# ---------------------------------------------------------------------------
# Sensor packet sent by ESP32: "SENSOR,<temperature_c>,<humidity_pct>,<pir_state>\n"
SENSOR_MSG_PREFIX = "SENSOR"

# Commands sent from Python to ESP32:
# INVERT_BUZZER_LOGIC: False because ESP32 firmware handles active-low internally
INVERT_BUZZER_LOGIC = False

CMD_BUZZER_ON = "BUZZER:ON\n"
CMD_BUZZER_OFF = "BUZZER:OFF\n"
CMD_PING = "PING\n"

# ---------------------------------------------------------------------------
# Environmental Sensor Limits & Thresholds
# ---------------------------------------------------------------------------
TEMP_WARNING_HIGH_C = 35.0      # Temperature warning threshold
TEMP_WARNING_LOW_C = 15.0       # Cold warning threshold
HUMIDITY_WARNING_HIGH = 80.0    # Humidity warning threshold (%)
HUMIDITY_WARNING_LOW = 25.0     # Dry air warning threshold (%)

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
CSV_LOG_FILE = LOGS_DIR / "eye_monitoring_log.csv"
EVENT_LOG_FILE = LOGS_DIR / "system_events.log"
LOG_FLUSH_INTERVAL_SEC = 5.0
