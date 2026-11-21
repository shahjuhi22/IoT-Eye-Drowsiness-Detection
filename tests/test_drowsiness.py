"""
test_drowsiness.py — Unit Tests for Drowsiness Detection State Machine
======================================================================
Tests blink counting, prolonged eye-closure duration calculation, state
transitions (NORMAL -> WARNING -> DROWSY), buzzer command triggering, cooldown
logic, face disappearance, and recovery.
"""

import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.drowsiness_detector import DrowsinessDetector, DrowsinessState


class TestDrowsinessDetector(unittest.TestCase):

    def setUp(self):
        # Deterministic detector with calibration disabled for unit testing
        self.detector = DrowsinessDetector(
            ear_threshold=0.22,
            warning_duration=1.0,
            drowsy_duration=1.75,
            blink_min_duration=0.08,
            blink_max_duration=0.40,
            cooldown_sec=2.0,
            calibration_enabled=False
        )

    def test_open_eyes_remains_normal(self):
        """Continuous open eyes should maintain NORMAL state with zero blinks."""
        t = 100.0
        for i in range(10):
            res = self.detector.update(face_detected=True, left_ear=0.32, right_ear=0.32, timestamp=t + i * 0.033)
            self.assertEqual(res["state"], DrowsinessState.NORMAL.value)
            self.assertEqual(res["overall_status"], "OPEN")
            self.assertEqual(res["blink_count"], 0)
            self.assertFalse(res["alarm_active"])
            self.assertIsNone(res["buzzer_command"])

    def test_natural_blink_detection(self):
        """
        A brief closure lasting 0.20s should increment blink count exactly once
        and remain in NORMAL state without triggering an alarm.
        """
        t = 100.0
        # 1. Open eyes
        self.detector.update(face_detected=True, left_ear=0.32, right_ear=0.32, timestamp=t)

        # 2. Eyes close at t = 100.1
        self.detector.update(face_detected=True, left_ear=0.10, right_ear=0.10, timestamp=t + 0.1)

        # 3. Eyes remain closed at t = 100.2
        self.detector.update(face_detected=True, left_ear=0.10, right_ear=0.10, timestamp=t + 0.2)

        # 4. Eyes reopen at t = 100.3 (Total closure duration = 0.20s -> Valid blink)
        res = self.detector.update(face_detected=True, left_ear=0.32, right_ear=0.32, timestamp=t + 0.3)

        self.assertEqual(res["blink_count"], 1)
        self.assertEqual(res["state"], DrowsinessState.NORMAL.value)
        self.assertFalse(res["alarm_active"])
        self.assertIsNone(res["buzzer_command"])

    def test_prolonged_closure_warning_and_drowsy_alarm(self):
        """
        Continuous eye closure:
        - At 1.20s: State transitions to WARNING.
        - At 1.80s: State transitions to DROWSY and triggers BUZZER:ON.
        - Reopening: State returns to NORMAL and triggers BUZZER:OFF.
        """
        t = 200.0
        # Frame 1: Eyes close
        self.detector.update(face_detected=True, left_ear=0.12, right_ear=0.12, timestamp=t)

        # Frame 2: Closure at 0.5s -> Still developing
        res_05 = self.detector.update(face_detected=True, left_ear=0.12, right_ear=0.12, timestamp=t + 0.5)
        self.assertEqual(res_05["state"], DrowsinessState.NORMAL.value)
        self.assertFalse(res_05["alarm_active"])

        # Frame 3: Closure at 1.2s -> Triggers WARNING
        res_12 = self.detector.update(face_detected=True, left_ear=0.12, right_ear=0.12, timestamp=t + 1.2)
        self.assertEqual(res_12["state"], DrowsinessState.WARNING.value)
        self.assertFalse(res_12["alarm_active"])

        # Frame 4: Closure at 1.8s -> Triggers DROWSY + BUZZER:ON
        res_18 = self.detector.update(face_detected=True, left_ear=0.12, right_ear=0.12, timestamp=t + 1.8)
        self.assertEqual(res_18["state"], DrowsinessState.DROWSY.value)
        self.assertTrue(res_18["alarm_active"])
        self.assertEqual(res_18["buzzer_command"], "BUZZER:ON")

        # Frame 5: Reopening eyes -> Returns to NORMAL + BUZZER:OFF
        res_open = self.detector.update(face_detected=True, left_ear=0.30, right_ear=0.30, timestamp=t + 2.5)
        self.assertEqual(res_open["state"], DrowsinessState.NORMAL.value)
        self.assertFalse(res_open["alarm_active"])
        self.assertEqual(res_open["buzzer_command"], "BUZZER:OFF")

    def test_cooldown_prevents_repeated_buzzer_spam(self):
        """
        After an alarm is triggered, re-entering closure within the cooldown window
        should not re-emit BUZZER:ON.
        """
        t = 300.0
        # Trigger first alarm
        self.detector.update(face_detected=True, left_ear=0.10, right_ear=0.10, timestamp=t)
        res_alarm = self.detector.update(face_detected=True, left_ear=0.10, right_ear=0.10, timestamp=t + 1.8)
        self.assertEqual(res_alarm["buzzer_command"], "BUZZER:ON")

        # Clear alarm by opening eyes
        self.detector.update(face_detected=True, left_ear=0.30, right_ear=0.30, timestamp=t + 2.0)

        # Immediately close eyes again at t = 302.2 (Within 2s cooldown of 301.8)
        self.detector.update(face_detected=True, left_ear=0.10, right_ear=0.10, timestamp=t + 2.2)
        # Prolonged closure at t = 303.5 (Only 1.7s since last trigger)
        res_cooldown = self.detector.update(face_detected=True, left_ear=0.10, right_ear=0.10, timestamp=t + 3.5)
        self.assertNotEqual(res_cooldown["buzzer_command"], "BUZZER:ON")

    def test_face_disappearance_and_recovery(self):
        """
        When face disappears, state transitions to FACE_ABSENT.
        When face reappears, state transitions back to NORMAL without spurious alarms.
        """
        t = 400.0
        # Face visible
        self.detector.update(face_detected=True, left_ear=0.32, right_ear=0.32, timestamp=t)

        # Face disappears
        res_absent = self.detector.update(face_detected=False, timestamp=t + 0.5)
        self.assertEqual(res_absent["state"], DrowsinessState.FACE_ABSENT.value)
        self.assertEqual(res_absent["overall_status"], "FACE ABSENT")

        # Face reappears
        res_back = self.detector.update(face_detected=True, left_ear=0.30, right_ear=0.30, timestamp=t + 2.0)
        self.assertEqual(res_back["state"], DrowsinessState.NORMAL.value)
        self.assertEqual(res_back["overall_status"], "OPEN")


if __name__ == "__main__":
    unittest.main()
