"""
drowsiness_detector.py — Real-Time State Machine for Blink & Drowsiness Analysis
================================================================================
Monitors real-time Eye Aspect Ratio (EAR) over time using precise frame timestamps
(time.perf_counter) rather than relying on assumed fixed frame rates.

Key Responsibilities:
  1. Tracks Eye Status: OPEN vs CLOSED per eye and combined.
  2. Counts Natural Blinks: closures lasting between MIN_BLINK and MAX_BLINK seconds.
  3. Detects Prolonged Closures:
     - Warning state at >= 1.0 second.
     - Drowsy / Alert state at >= 1.75 seconds.
  4. Triggers Buzzer Alerts with configurable cooldown to prevent spamming serial line.
  5. Handles Face Disappearance: Tracks duration of face absence and resets state
     cleanly when the face reappears.
  6. Calibration: Learns subject's baseline open-eye EAR across initial frames.
"""

import time
from enum import Enum
from typing import Dict, Any, Optional
import config


class DrowsinessState(Enum):
    CALIBRATING = "CALIBRATING"
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    DROWSY = "DROWSY"
    FACE_ABSENT = "FACE_ABSENT"


class DrowsinessDetector:
    """
    State machine that analyzes EAR time series to detect natural blinks,
    prolonged eye-closures, and drowsiness events.
    """

    def __init__(self,
                 ear_threshold: float = config.DEFAULT_EAR_THRESHOLD,
                 warning_duration: float = config.WARNING_DURATION_SEC,
                 drowsy_duration: float = config.DROWSY_DURATION_SEC,
                 blink_min_duration: float = config.BLINK_MIN_DURATION_SEC,
                 blink_max_duration: float = config.BLINK_MAX_DURATION_SEC,
                 cooldown_sec: float = config.ALERT_COOLDOWN_SEC,
                 calibration_enabled: bool = config.CALIBRATION_ENABLED,
                 calibration_frames: int = config.CALIBRATION_FRAMES):

        # Thresholds & timings
        self.base_ear_threshold = ear_threshold
        self.effective_ear_threshold = ear_threshold
        self.warning_duration = warning_duration
        self.drowsy_duration = drowsy_duration
        self.blink_min_duration = blink_min_duration
        self.blink_max_duration = blink_max_duration
        self.cooldown_sec = cooldown_sec

        # Calibration state
        self.calibration_enabled = calibration_enabled
        self.calibration_target_frames = calibration_frames
        self.calibration_samples = []
        self.is_calibrated = not calibration_enabled

        # Eye tracking & timers
        self.eye_closed_start_time: Optional[float] = None
        self.last_face_seen_time: Optional[float] = None
        self.last_buzzer_trigger_time: float = 0.0
        self.current_closure_duration: float = 0.0

        # Metrics
        self.blink_count: int = 0
        self.drowsy_event_count: int = 0
        self.state: DrowsinessState = (
            DrowsinessState.CALIBRATING if calibration_enabled else DrowsinessState.NORMAL
        )

        # Alert latch (True when active alarm state is reached)
        self.alarm_active: bool = False
        self.buzzer_command_needed: Optional[str] = None

    def reset_state(self) -> None:
        """Reset counters and transient timers."""
        self.eye_closed_start_time = None
        self.current_closure_duration = 0.0
        self.alarm_active = False
        self.buzzer_command_needed = "BUZZER:OFF"

    def update(self,
               face_detected: bool,
               left_ear: float = 0.0,
               right_ear: float = 0.0,
               timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Update drowsiness detector with the latest frame metrics.
        
        Args:
            face_detected: Whether a face is detected in the current frame.
            left_ear: Calculated left eye aspect ratio.
            right_ear: Calculated right eye aspect ratio.
            timestamp: Monotonic timestamp (seconds). Uses time.perf_counter() if None.
            
        Returns:
            Dict containing detailed current status for rendering and serial control.
        """
        now = time.perf_counter() if timestamp is None else timestamp
        avg_ear = (left_ear + right_ear) / 2.0 if face_detected else 0.0

        # Flag for whether an immediate serial command (BUZZER:ON or BUZZER:OFF) should be sent
        self.buzzer_command_needed = None

        # ---------------------------------------------------------------------
        # 1. Handle Face Absence
        # ---------------------------------------------------------------------
        if not face_detected:
            if self.last_face_seen_time is None:
                self.last_face_seen_time = now

            absence_duration = now - self.last_face_seen_time
            self.state = DrowsinessState.FACE_ABSENT
            self.current_closure_duration = 0.0
            self.eye_closed_start_time = None

            # If buzzer was buzzing and face disappeared, turn it off for safety
            if self.alarm_active:
                self.alarm_active = False
                self.buzzer_command_needed = "BUZZER:OFF"

            return {
                "face_detected": False,
                "state": self.state.value,
                "left_ear": 0.0,
                "right_ear": 0.0,
                "avg_ear": 0.0,
                "left_status": "NOT FOUND",
                "right_status": "NOT FOUND",
                "overall_status": "FACE ABSENT",
                "blink_count": self.blink_count,
                "closure_duration": 0.0,
                "absence_duration": absence_duration,
                "threshold": self.effective_ear_threshold,
                "alarm_active": self.alarm_active,
                "buzzer_command": self.buzzer_command_needed,
                "is_calibrated": self.is_calibrated,
            }

        # Face is visible
        self.last_face_seen_time = now

        # ---------------------------------------------------------------------
        # 2. Calibration Stage
        # ---------------------------------------------------------------------
        if self.calibration_enabled and not self.is_calibrated:
            self.state = DrowsinessState.CALIBRATING
            if avg_ear > 0.15:  # Avoid recording blinks during calibration
                self.calibration_samples.append(avg_ear)

            progress = len(self.calibration_samples) / float(self.calibration_target_frames)
            if len(self.calibration_samples) >= self.calibration_target_frames:
                baseline_ear = float(sum(self.calibration_samples) / len(self.calibration_samples))
                self.effective_ear_threshold = round(baseline_ear * config.CALIBRATION_EAR_RATIO, 3)
                self.is_calibrated = True
                self.state = DrowsinessState.NORMAL

            return {
                "face_detected": True,
                "state": self.state.value,
                "left_ear": left_ear,
                "right_ear": right_ear,
                "avg_ear": avg_ear,
                "left_status": "CALIBRATING",
                "right_status": "CALIBRATING",
                "overall_status": f"CALIBRATING ({int(progress*100)}%)",
                "blink_count": self.blink_count,
                "closure_duration": 0.0,
                "absence_duration": 0.0,
                "threshold": self.effective_ear_threshold,
                "alarm_active": False,
                "buzzer_command": None,
                "is_calibrated": self.is_calibrated,
            }

        # ---------------------------------------------------------------------
        # 3. Determine Individual & Combined Eye Status
        # ---------------------------------------------------------------------
        thresh = self.effective_ear_threshold
        left_closed = left_ear < thresh
        right_closed = right_ear < thresh
        eyes_closed = (left_closed and right_closed) or (avg_ear < thresh)

        left_status = "CLOSED" if left_closed else "OPEN"
        right_status = "CLOSED" if right_closed else "OPEN"

        # ---------------------------------------------------------------------
        # 4. State Machine: Open vs Closed Duration Processing
        # ---------------------------------------------------------------------
        if eyes_closed:
            if self.eye_closed_start_time is None:
                self.eye_closed_start_time = now
                self.current_closure_duration = 0.0
            else:
                self.current_closure_duration = now - self.eye_closed_start_time

            # Check duration thresholds
            if self.current_closure_duration >= self.drowsy_duration:
                # Drowsiness alert!
                prev_state = self.state
                self.state = DrowsinessState.DROWSY
                if not self.alarm_active:
                    # Check cooldown
                    if (now - self.last_buzzer_trigger_time) >= self.cooldown_sec:
                        self.alarm_active = True
                        self.last_buzzer_trigger_time = now
                        self.buzzer_command_needed = "BUZZER:ON"
                        self.drowsy_event_count += 1
            elif self.current_closure_duration >= self.warning_duration:
                self.state = DrowsinessState.WARNING
            else:
                # Brief closure so far (could develop into a blink or prolonged closure)
                self.state = DrowsinessState.NORMAL

            overall_status = "CLOSED"

        else:
            # Eyes are currently OPEN
            overall_status = "OPEN"

            if self.eye_closed_start_time is not None:
                # Eyes just opened! Calculate duration of closure
                closed_duration = now - self.eye_closed_start_time

                # Check if this qualifies as a natural blink
                if self.blink_min_duration <= closed_duration <= self.blink_max_duration:
                    self.blink_count += 1

                self.eye_closed_start_time = None
                self.current_closure_duration = 0.0

            # Turn off alarm if it was active
            if self.alarm_active:
                self.alarm_active = False
                self.buzzer_command_needed = "BUZZER:OFF"

            self.state = DrowsinessState.NORMAL

        return {
            "face_detected": True,
            "state": self.state.value,
            "left_ear": left_ear,
            "right_ear": right_ear,
            "avg_ear": avg_ear,
            "left_status": left_status,
            "right_status": right_status,
            "overall_status": overall_status,
            "blink_count": self.blink_count,
            "closure_duration": self.current_closure_duration,
            "absence_duration": 0.0,
            "threshold": self.effective_ear_threshold,
            "alarm_active": self.alarm_active,
            "buzzer_command": self.buzzer_command_needed,
            "is_calibrated": self.is_calibrated,
            "drowsy_event_count": self.drowsy_event_count,
        }
