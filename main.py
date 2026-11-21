"""
main.py — Real-Time IoT Eye Blink and Drowsiness Monitoring System
==================================================================
Entry point for the desktop computer vision & IoT sensor monitoring application.
Integrates MediaPipe Face Mesh, Eye Aspect Ratio (EAR) mathematics, USB serial
telemetry with the ESP32 microcontroller, buzzer alarm actuation, and live HUD overlay.

Key Controls:
  - Q : Quit application safely (ensures buzzer is silenced before closing)
  - C : Recalibrate personalized baseline EAR
  - S : Toggle between Physical ESP32 Serial and Software Simulation Mode
  - B : Test trigger buzzer manually
  - R : Reset blink and alert counters
"""

import sys
import os
import time
import argparse
from pathlib import Path
import cv2

# Ensure project root is in Python module search path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.eye_detector import EyeDetector
from src.drowsiness_detector import DrowsinessDetector
from src.serial_communication import ESP32SerialBridge
from src.sensor_manager import SensorManager
from src.alert_manager import AlertManager


def print_banner() -> None:
    """Print student-friendly terminal banner matching project style."""
    print("\n" + "=" * 76)
    print("  IoT-BASED SMART EYE MONITORING & DROWSINESS DETECTION SYSTEM")
    print("  ESP32 (DHT22 + PIR + Buzzer) | OpenCV & MediaPipe Face Mesh (EAR)")
    print("=" * 76)
    print("  Interactive Hotkeys:")
    print("    [Q] Quit Application          [C] Recalibrate Baseline EAR")
    print("    [S] Toggle Simulation Mode    [B] Test Buzzer Sound")
    print("    [I] Invert Buzzer Polarity    [R] Reset Counters")
    print("    [H] Print Help")
    print("=" * 76 + "\n")


def parse_args():
    parser = argparse.ArgumentParser(description="IoT Eye Monitoring & Drowsiness Detection System")
    parser.add_argument("--camera", type=int, default=config.CAMERA_INDEX,
                        help=f"Camera index (default: {config.CAMERA_INDEX})")
    parser.add_argument("--port", type=str, default=config.SERIAL_PORT,
                        help=f"ESP32 Serial Port (default: {config.SERIAL_PORT})")
    parser.add_argument("--simulate", action="store_true",
                        help="Force Simulation Mode without attempting physical ESP32 connection")
    parser.add_argument("--demo", action="store_true",
                        help="Run with interactive simulated webcam feed (no physical camera required)")
    parser.add_argument("--threshold", type=float, default=config.DEFAULT_EAR_THRESHOLD,
                        help=f"Default EAR threshold (default: {config.DEFAULT_EAR_THRESHOLD})")
    parser.add_argument("--no-calibrate", action="store_true",
                        help="Skip automatic initial calibration")
    return parser.parse_args()


class SyntheticCamera:
    """Generates an interactive synthetic video feed for demonstration without a webcam."""

    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self.eyes_closed = False
        self.last_toggle_time = time.time()
        self.is_opened = True

    def isOpened(self) -> bool:
        return self.is_opened

    def set(self, propId, value):
        return True

    def read(self):
        time.sleep(0.033)  # ~30 FPS
        now = time.time()
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img[:] = (24, 24, 27)  # Dark slate background

        # Draw realistic synthetic face oval
        center_x, center_y = self.width // 2, self.height // 2 - 10
        cv2.ellipse(img, (center_x, center_y), (140, 180), 0, 0, 360, (190, 190, 200), -1)
        cv2.ellipse(img, (center_x, center_y), (140, 180), 0, 0, 360, (120, 120, 130), 2)

        # Eye locations
        left_eye_center = (center_x - 55, center_y - 25)
        right_eye_center = (center_x + 55, center_y - 25)

        if not self.eyes_closed:
            # Eyes OPEN
            for ec in [left_eye_center, right_eye_center]:
                cv2.ellipse(img, ec, (26, 14), 0, 0, 360, (255, 255, 255), -1)
                cv2.ellipse(img, ec, (26, 14), 0, 0, 360, (40, 40, 40), 2)
                cv2.circle(img, ec, 8, (60, 40, 30), -1)
                cv2.circle(img, (ec[0] - 2, ec[1] - 2), 3, (255, 255, 255), -1)
        else:
            # Eyes CLOSED
            for ec in [left_eye_center, right_eye_center]:
                cv2.line(img, (ec[0] - 26, ec[1]), (ec[0] + 26, ec[1]), (30, 30, 30), 3)

        # Subtle mouth
        cv2.ellipse(img, (center_x, center_y + 80), (35, 10), 0, 0, 180, (70, 70, 90), 2)

        # Instructions banner for demo mode
        cv2.putText(img, "[DEMO FEED] Press SPACEBAR to Toggle Eyes Open / Closed",
                    (center_x - 220, self.height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1)

        return True, img

    def release(self):
        self.is_opened = False


def main():
    args = parse_args()
    print_banner()

    # 1. Initialize Sensor Manager
    sensor_mgr = SensorManager()

    # 2. Initialize ESP32 Serial Bridge
    serial_bridge = ESP32SerialBridge(
        port=args.port,
        baud_rate=config.SERIAL_BAUD_RATE,
        on_telemetry_received=sensor_mgr.update_from_dict
    )

    if args.simulate:
        print("[INFO] Simulation mode forced via command line argument.")
        serial_bridge.connect()  # Will enter simulation
    else:
        connected = serial_bridge.connect()
        if not connected:
            print("[INFO] Physical ESP32 not connected. Running in Simulation Mode.")
            print("       (You can test everything without physical hardware!)")

    # Start asynchronous background reader thread
    serial_bridge.start()

    # 3. Initialize Alert Manager
    alert_mgr = AlertManager(serial_bridge=serial_bridge)
    alert_mgr.log_event("Application initialized.")

    # 4. Initialize Computer Vision Eye Detector
    print("[INFO] Loading MediaPipe Face Mesh model...")
    eye_detector = EyeDetector()

    # 5. Initialize Drowsiness State Machine
    drowsiness_detector = DrowsinessDetector(
        ear_threshold=args.threshold,
        warning_duration=config.WARNING_DURATION_SEC,
        drowsy_duration=config.DROWSY_DURATION_SEC,
        calibration_enabled=not args.no_calibrate,
        calibration_frames=config.CALIBRATION_FRAMES
    )

    # 6. Open Webcam
    is_synthetic = args.demo
    if args.demo:
        print("[INFO] Launching with Interactive Synthetic Video Feed (--demo)...")
        cap = SyntheticCamera(config.FRAME_WIDTH, config.FRAME_HEIGHT)
    else:
        print(f"[INFO] Opening camera index {args.camera}...")
        cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY)

        if not cap.isOpened():
            print(f"\n[WARNING] Could not open physical camera (index {args.camera}).")
            print("          Falling back to Interactive Synthetic Video Feed for demonstration.")
            print("          (Press SPACEBAR in the video window to toggle eyes open/closed!)\n")
            cap = SyntheticCamera(config.FRAME_WIDTH, config.FRAME_HEIGHT)
            is_synthetic = True

    # Configure capture resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    window_name = "IoT Eye Monitoring & Drowsiness Detection System"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, config.FRAME_WIDTH, config.FRAME_HEIGHT)

    # Performance / FPS counters
    prev_time = time.perf_counter()
    fps = 30.0
    frame_counter = 0

    print("[SUCCESS] Camera stream started. Press 'Q' in the video window to quit.\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[WARNING] Frame capture returned empty. Retrying...")
                time.sleep(0.05)
                continue

            frame_counter += 1
            now = time.perf_counter()
            dt = now - prev_time
            prev_time = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)

            # Flip frame horizontally for mirror-view
            frame = cv2.flip(frame, 1)

            # -----------------------------------------------------------------
            # Step A: Facial Landmark Detection & EAR Extraction
            # -----------------------------------------------------------------
            det_res = eye_detector.process_frame(frame)

            # -----------------------------------------------------------------
            # Step B: Drowsiness State Machine Evaluation
            # -----------------------------------------------------------------
            drowsy_res = drowsiness_detector.update(
                face_detected=det_res["face_detected"],
                left_ear=det_res["left_ear"],
                right_ear=det_res["right_ear"],
                timestamp=now
            )

            # -----------------------------------------------------------------
            # Step C: Alert & Actuator Coordination (USB Serial Command)
            # -----------------------------------------------------------------
            sensor_summary = sensor_mgr.get_summary()
            sensor_summary["connected"] = serial_bridge.is_connected
            sensor_summary["simulation"] = serial_bridge.simulation_mode

            alert_mgr.process_alert(drowsy_res, sensor_summary)

            # Periodic CSV telemetry logging
            if frame_counter % 30 == 0:
                alert_mgr.log_telemetry_row(drowsy_res, sensor_summary)

            # -----------------------------------------------------------------
            # Step D: Render Heads-Up Display (HUD)
            # -----------------------------------------------------------------
            display_frame = eye_detector.render_overlay(
                frame=frame,
                detection_res=det_res,
                drowsiness_res=drowsy_res,
                sensor_data=sensor_summary,
                fps=fps
            )

            cv2.imshow(window_name, display_frame)

            # -----------------------------------------------------------------
            # Step E: Keyboard Interaction
            # -----------------------------------------------------------------
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:  # 'Q' or ESC
                print("\n[INFO] Exiting application...")
                break

            elif key == 32:  # SPACEBAR
                if isinstance(cap, SyntheticCamera):
                    cap.eyes_closed = not cap.eyes_closed
                    status = "CLOSED" if cap.eyes_closed else "OPEN"
                    print(f"[DEMO] Toggled Synthetic Eyes to: {status}")

            elif key == ord('c'):
                print("[INFO] Initiating baseline EAR recalibration...")
                drowsiness_detector.is_calibrated = False
                drowsiness_detector.calibration_samples.clear()
                drowsiness_detector.state = drowsiness_detector.state.CALIBRATING

            elif key == ord('s'):
                if serial_bridge.simulation_mode:
                    print("[INFO] Attempting physical ESP32 reconnection...")
                    serial_bridge.connect()
                else:
                    print("[INFO] Switching to Simulation Mode...")
                    serial_bridge._enter_simulation()

            elif key == ord('i') or key == ord('I'):
                inv = alert_mgr.toggle_invert_logic()
                print(f"[HOTKEY] Buzzer Polarity Inverted: {'Active-LOW' if inv else 'Active-HIGH (Normal)'}")

            elif key == ord('b') or key == ord('B'):
                # Manual test buzzer toggle
                test_state = not alert_mgr.buzzer_is_active
                print(f"[INFO] Manual Buzzer Test: {'ON' if test_state else 'OFF'}")
                if test_state:
                    alert_mgr._activate_alarm(drowsy_res, sensor_summary)
                else:
                    alert_mgr._deactivate_alarm(drowsy_res, sensor_summary)

            elif key == ord('r'):
                print("[INFO] Resetting blink counter and alarm metrics...")
                drowsiness_detector.blink_count = 0
                drowsiness_detector.drowsy_event_count = 0
                drowsiness_detector.reset_state()

            elif key == ord('h'):
                print("\nInteractive Hotkeys:")
                print("  Q: Quit")
                print("  C: Recalibrate Baseline EAR")
                print("  S: Toggle Simulation Mode")
                print("  B: Test Buzzer Actuator")
                print("  R: Reset Metrics\n")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")

    finally:
        # Safe teardown
        print("[INFO] Shutting down cleanly...")
        alert_mgr.force_silence()
        cap.release()
        cv2.destroyAllWindows()
        eye_detector.close()
        serial_bridge.stop()
        print("[DONE] Cleanup complete. System safely halted.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
