"""
eye_detector.py — Computer Vision Engine for Face & Eye Landmark Detection
===========================================================================
Detects human faces from camera frames and extracts precise eye landmarks
using Google MediaPipe Face Mesh. Computes Eye Aspect Ratio (EAR) and
renders a comprehensive, student-friendly Heads-Up Display (HUD) overlay.

Features:
  - 468/478-point MediaPipe Face Mesh integration
  - 6-point Left Eye & Right Eye EAR landmark extraction
  - Graceful fallback / recovery when face turns away or disappears
  - Clean OpenCV drawing with anti-aliased HUD metrics
  - Visual color cues: GREEN (Normal), YELLOW (Warning), RED (Drowsy Alarm)
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np

import config
from .ear_calculator import calculate_eyes_ear


class EyeStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


class EyeDetector:
    """
    OpenCV & MediaPipe Face Mesh pipeline for extracting eye landmarks,
    calculating EAR, and drawing overlays on live frames.
    Includes OpenCV Haar cascade fallback for maximum reliability.
    """

    def __init__(self,
                 max_num_faces: int = 1,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):

        self.max_num_faces = max_num_faces
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.backend = "none"
        self.mp_face_mesh = None
        self.face_mesh = None
        self.face_cascade = None
        self.eye_cascade = None

        self._init_vision_pipeline()

        # Landmark index lists from config
        self.left_indices = config.LEFT_EYE_LANDMARKS
        self.right_indices = config.RIGHT_EYE_LANDMARKS
        self.left_contour = config.LEFT_EYE_CONTOUR
        self.right_contour = config.RIGHT_EYE_CONTOUR

    def _init_vision_pipeline(self) -> bool:
        """Initialize MediaPipe Face Mesh model with Haar Cascade fallback."""
        try:
            import mediapipe as mp
            if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_mesh"):
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    max_num_faces=self.max_num_faces,
                    refine_landmarks=True,
                    min_detection_confidence=self.min_detection_confidence,
                    min_tracking_confidence=self.min_tracking_confidence
                )
                self.backend = "mediapipe_solutions"
                return True
        except Exception as e:
            print(f"[EyeDetector WARNING] MediaPipe Solutions not available: {e}")

        # Fallback to OpenCV Haar Cascades
        try:
            face_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            eye_path = cv2.data.haarcascades + "haarcascade_eye.xml"
            self.face_cascade = cv2.CascadeClassifier(face_path)
            self.eye_cascade = cv2.CascadeClassifier(eye_path)
            self.backend = "opencv_cascade"
            print("[EyeDetector INFO] Operating with OpenCV Haar Cascade vision fallback.")
            return True
        except Exception as e:
            print(f"[EyeDetector ERROR] Failed to initialize Haar Cascade fallback: {e}")
            self.backend = "none"
            return False

    def process_frame(self, frame_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Process a single BGR camera frame and extract facial landmarks and EAR.
        """
        if frame_bgr is None:
            return self._empty_result()

        if self.backend == "mediapipe_solutions" and self.face_mesh is not None:
            return self._process_mediapipe(frame_bgr)
        elif self.backend == "opencv_cascade" and self.face_cascade is not None:
            return self._process_cascade(frame_bgr)
        else:
            return self._empty_result()

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "face_detected": False,
            "left_ear": 0.0,
            "right_ear": 0.0,
            "avg_ear": 0.0,
            "left_pts": [],
            "right_pts": [],
            "face_box": None,
            "all_landmarks": None,
            "backend": self.backend,
        }

    def _process_mediapipe(self, frame_bgr: np.ndarray) -> Dict[str, Any]:
        h, w, _ = frame_bgr.shape
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self.face_mesh.process(frame_rgb)
        frame_rgb.flags.writeable = True

        if not results.multi_face_landmarks:
            return self._empty_result()

        face_landmarks = results.multi_face_landmarks[0]
        landmarks_px = np.array(
            [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark],
            dtype=np.int32
        )

        left_ear, right_ear, avg_ear = calculate_eyes_ear(
            landmarks_px, self.left_indices, self.right_indices
        )

        left_pts = [tuple(landmarks_px[idx]) for idx in self.left_indices]
        right_pts = [tuple(landmarks_px[idx]) for idx in self.right_indices]

        min_x = max(0, int(np.min(landmarks_px[:, 0])))
        max_x = min(w, int(np.max(landmarks_px[:, 0])))
        min_y = max(0, int(np.min(landmarks_px[:, 1])))
        max_y = min(h, int(np.max(landmarks_px[:, 1])))
        face_box = (min_x, min_y, max_x - min_x, max_y - min_y)

        return {
            "face_detected": True,
            "left_ear": left_ear,
            "right_ear": right_ear,
            "avg_ear": avg_ear,
            "left_pts": left_pts,
            "right_pts": right_pts,
            "face_box": face_box,
            "all_landmarks": landmarks_px,
            "backend": "mediapipe",
        }

    def _process_cascade(self, frame_bgr: np.ndarray) -> Dict[str, Any]:
        """OpenCV Haar Cascade fallback for face and eye tracking."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(100, 100))

        if len(faces) == 0:
            return self._empty_result()

        fx, fy, fw, fh = faces[0]
        face_box = (int(fx), int(fy), int(fw), int(fh))

        # Search for eyes strictly in the upper half of the face
        eye_roi_gray = gray[fy:fy + int(fh * 0.55), fx:fx + fw]
        eyes = self.eye_cascade.detectMultiScale(eye_roi_gray, scaleFactor=1.1, minNeighbors=3, minSize=(25, 25))

        # If at least 2 eyes detected, eyes are OPEN; if 0 detected inside upper face, CLOSED
        if len(eyes) >= 2:
            est_ear = 0.31
        elif len(eyes) == 1:
            est_ear = 0.24
        else:
            est_ear = 0.12

        return {
            "face_detected": True,
            "left_ear": est_ear,
            "right_ear": est_ear,
            "avg_ear": est_ear,
            "left_pts": [],
            "right_pts": [],
            "face_box": face_box,
            "all_landmarks": None,
            "backend": "haar_cascade",
        }

    def render_overlay(self,
                       frame: np.ndarray,
                       detection_res: Dict[str, Any],
                       drowsiness_res: Dict[str, Any],
                       sensor_data: Optional[Dict[str, Any]] = None,
                       fps: float = 0.0) -> np.ndarray:
        """
        Draw a clean, aesthetic Heads-Up Display (HUD) on the video frame.
        Includes eye landmarks, bounding box, EAR metrics, drowsiness warnings,
        and live ESP32 sensor values.
        """
        annotated = frame.copy()
        h, w, _ = annotated.shape

        state = drowsiness_res.get("state", "NORMAL")
        alarm_active = drowsiness_res.get("alarm_active", False)

        # Determine theme color based on status
        if state == "DROWSY" or alarm_active:
            theme_color = (0, 0, 255)       # Red
            status_text = "DROWSINESS DETECTED - ALARM!"
        elif state == "WARNING":
            theme_color = (0, 165, 255)     # Orange
            status_text = "WARNING: PROLONGED EYE CLOSURE"
        elif state == "CALIBRATING":
            theme_color = (255, 200, 0)     # Cyan/Yellow
            status_text = "CALIBRATING BASELINE EAR..."
        elif state == "FACE_ABSENT":
            theme_color = (128, 128, 128)   # Grey
            status_text = "FACE NOT DETECTED"
        else:
            theme_color = (0, 220, 0)       # Green
            status_text = "NORMAL - EYES FOCUSED"

        # ---------------------------------------------------------------------
        # 1. Draw Eye Landmarks & Contours if Face Detected
        # ---------------------------------------------------------------------
        if detection_res.get("face_detected", False):
            landmarks = detection_res.get("all_landmarks")
            if landmarks is not None:
                # Draw subtle face box
                x, y, bw, bh = detection_res["face_box"]
                cv2.rectangle(annotated, (x, y), (x + bw, y + bh), (60, 60, 60), 1)

                # Draw Left Eye Contour
                left_contour_pts = np.array([landmarks[idx] for idx in self.left_contour], dtype=np.int32)
                cv2.polylines(annotated, [left_contour_pts], isClosed=True, color=theme_color, thickness=1, lineType=cv2.LINE_AA)

                # Draw Right Eye Contour
                right_contour_pts = np.array([landmarks[idx] for idx in self.right_contour], dtype=np.int32)
                cv2.polylines(annotated, [right_contour_pts], isClosed=True, color=theme_color, thickness=1, lineType=cv2.LINE_AA)

                # Draw 6 key EAR landmark dots per eye
                for pt in detection_res["left_pts"] + detection_res["right_pts"]:
                    cv2.circle(annotated, pt, 2, (0, 255, 255), -1, lineType=cv2.LINE_AA)

        # ---------------------------------------------------------------------
        # 2. Top Banner — Status & Alerts
        # ---------------------------------------------------------------------
        # Semi-transparent header banner
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (w, 50), (20, 20, 20), -1)
        # Status color indicator strip
        cv2.rectangle(overlay, (0, 0), (w, 4), theme_color, -1)
        cv2.addWeighted(overlay, 0.75, annotated, 0.25, 0, annotated)

        # Status text
        cv2.putText(annotated, status_text, (15, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, theme_color, 2, cv2.LINE_AA)

        # FPS indicator on top right
        fps_text = f"FPS: {fps:.1f}"
        cv2.putText(annotated, fps_text, (w - 110, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)

        # ---------------------------------------------------------------------
        # 3. Bottom HUD Panel — Vision & IoT Sensor Telemetry
        # ---------------------------------------------------------------------
        panel_height = 110
        panel_top = h - panel_height
        panel_overlay = annotated.copy()
        cv2.rectangle(panel_overlay, (0, panel_top), (w, h), (15, 15, 15), -1)
        cv2.addWeighted(panel_overlay, 0.82, annotated, 0.18, 0, annotated)

        # Column 1: Eye Metrics
        left_ear = drowsiness_res.get("left_ear", 0.0)
        right_ear = drowsiness_res.get("right_ear", 0.0)
        avg_ear = drowsiness_res.get("avg_ear", 0.0)
        thresh = drowsiness_res.get("threshold", 0.22)
        blinks = drowsiness_res.get("blink_count", 0)
        duration = drowsiness_res.get("closure_duration", 0.0)

        c1_x = 15
        cv2.putText(annotated, f"EAR: {avg_ear:.3f} (L:{left_ear:.2f} R:{right_ear:.2f})",
                    (c1_x, panel_top + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(annotated, f"Threshold: {thresh:.3f} | Blinks: {blinks}",
                    (c1_x, panel_top + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (220, 220, 220), 1, cv2.LINE_AA)
        cv2.putText(annotated, f"Closure Time: {duration:.2f}s (Max:{config.DROWSY_DURATION_SEC}s)",
                    (c1_x, panel_top + 75), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
                    theme_color if duration > 0.5 else (180, 180, 180), 1, cv2.LINE_AA)

        # Column 2: IoT Sensor Telemetry (DHT22 & PIR)
        c2_x = int(w * 0.52)
        if sensor_data:
            temp = sensor_data.get("temperature")
            hum = sensor_data.get("humidity")
            pir = sensor_data.get("pir_state", 0)
            conn = sensor_data.get("connected", False)
            sim = sensor_data.get("simulation", False)
            buzzer = sensor_data.get("buzzer_on", False)

            conn_label = "SIMULATION" if sim else ("CONNECTED" if conn else "OFFLINE")
            conn_color = (0, 200, 255) if sim else ((0, 255, 0) if conn else (0, 0, 255))

            temp_str = f"{temp:.1f}C" if temp is not None else "N/A"
            hum_str = f"{hum:.1f}%" if hum is not None else "N/A"
            motion_str = "MOTION DETECTED" if pir == 1 else "NO MOTION"
            buzzer_str = "BUZZER: ON" if buzzer else "BUZZER: OFF"
            buzzer_color = (0, 0, 255) if buzzer else (120, 120, 120)

            cv2.putText(annotated, f"ESP32: {conn_label}",
                        (c2_x, panel_top + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.48, conn_color, 1, cv2.LINE_AA)
            cv2.putText(annotated, f"Temp: {temp_str} | Humidity: {hum_str}",
                        (c2_x, panel_top + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1, cv2.LINE_AA)
            cv2.putText(annotated, f"PIR: {motion_str} | {buzzer_str}",
                        (c2_x, panel_top + 75), cv2.FONT_HERSHEY_SIMPLEX, 0.48, buzzer_color, 1, cv2.LINE_AA)
        else:
            cv2.putText(annotated, "IoT Sensors: Initializing...",
                        (c2_x, panel_top + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (150, 150, 150), 1, cv2.LINE_AA)

        return annotated

    def close(self) -> None:
        """Release MediaPipe resources."""
        if self.face_mesh is not None:
            self.face_mesh.close()
            self.face_mesh = None
