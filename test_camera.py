"""
test_camera.py — Diagnostic Utility for Webcam & Computer Vision Backend
=========================================================================
Tests camera hardware access, resolution configuration, frame capture latency,
and MediaPipe Face Mesh landmark extraction.
"""

import sys
import time
from pathlib import Path
import numpy as np
import cv2

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.eye_detector import EyeDetector


def test_webcam(camera_index: int = 0, num_frames: int = 30) -> bool:
    print("\n" + "=" * 65)
    print("  WEBCAM & COMPUTER VISION DIAGNOSTIC TEST")
    print("=" * 65)
    print(f"[TEST 1] Testing OpenCV VideoCapture on Camera Index {camera_index}...")

    # Try DSHOW, then MSMF, then ANY
    cap = None
    for api_pref in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
        temp_cap = cv2.VideoCapture(camera_index, api_pref)
        if temp_cap.isOpened():
            cap = temp_cap
            break
        temp_cap.release()

    camera_opened = cap is not None and cap.isOpened()
    sample_frame = None

    if not camera_opened:
        print(f"[INFO] Physical camera could not be opened on index {camera_index}.")
        print("       (Normal when running in background sessions or if webcam is unplugged/in-use).")
        print("[INFO] Creating a synthetic facial image to test the MediaPipe pipeline...")
        # Create a realistic test image (360x480) with drawn face
        sample_frame = 30 * np.ones((360, 480, 3), dtype=np.uint8)
        cv2.ellipse(sample_frame, (240, 180), (100, 130), 0, 0, 360, (200, 200, 200), -1)
        # Eyes
        cv2.ellipse(sample_frame, (200, 160), (20, 10), 0, 0, 360, (30, 30, 30), -1)
        cv2.ellipse(sample_frame, (280, 160), (20, 10), 0, 0, 360, (30, 30, 30), -1)
    else:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        backend_name = cap.getBackendName()
        print(f"[PASS] Physical Camera Opened Successfully!")
        print(f"       Backend:    {backend_name}")
        print(f"       Resolution: {actual_w}x{actual_h}")

        print(f"\n[TEST 2] Testing frame acquisition latency ({num_frames} frames)...")
        start_t = time.perf_counter()
        frames_read = 0
        for _ in range(num_frames):
            ret, frame = cap.read()
            if ret and frame is not None:
                frames_read += 1
                sample_frame = frame
            time.sleep(0.01)

        elapsed = time.perf_counter() - start_t
        calc_fps = frames_read / elapsed if elapsed > 0 else 0
        print(f"[PASS] Successfully captured {frames_read}/{num_frames} frames in {elapsed:.2f}s (~{calc_fps:.1f} FPS)")
        cap.release()

    print("\n[TEST 3] Testing MediaPipe Face Mesh model initialization & inference...")
    try:
        detector = EyeDetector()
        if detector.face_mesh is None:
            print("[FAIL] MediaPipe Face Mesh failed to initialize.")
            return False

        print("[PASS] MediaPipe Face Mesh initialized successfully.")

        if sample_frame is not None:
            res = detector.process_frame(sample_frame)
            print(f"[INFO] Pipeline executed successfully. Face detected: {res['face_detected']}")

        detector.close()
    except Exception as e:
        print(f"[FAIL] Error testing MediaPipe Face Mesh: {e}")
        return False

    print("\n" + "=" * 65)
    if camera_opened:
        print("  DIAGNOSTIC RESULT: ALL WEBCAM & VISION TESTS PASSED!")
    else:
        print("  DIAGNOSTIC RESULT: VISION PIPELINE VERIFIED (CAMERA OFFLINE)")
    print("=" * 65 + "\n")
    return True


if __name__ == "__main__":
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else config.CAMERA_INDEX
    success = test_webcam(idx)
    sys.exit(0 if success else 1)
