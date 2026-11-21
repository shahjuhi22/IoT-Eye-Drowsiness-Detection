"""
test_ear.py — Unit Tests for Eye Aspect Ratio (EAR) Mathematical Engine
=======================================================================
Verifies Euclidean distance calculations, EAR calculations under open and
closed eye geometry, division-by-zero protection, and threshold classification.
"""

import unittest
import numpy as np

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ear_calculator import (
    euclidean_distance,
    calculate_ear,
    calculate_eyes_ear,
    is_eye_closed,
)


class TestEARCalculator(unittest.TestCase):

    def test_euclidean_distance(self):
        """Test L2 Euclidean distance between 2D points."""
        p1 = (0.0, 0.0)
        p2 = (3.0, 4.0)
        self.assertAlmostEqual(euclidean_distance(p1, p2), 5.0, places=5)

        # Identical points
        self.assertAlmostEqual(euclidean_distance(p1, p1), 0.0, places=5)

    def test_calculate_ear_open_eye(self):
        """
        Synthesize landmark coordinates for a realistic OPEN eye.
        Horizontal distance: 100 pixels (p1=(0,50), p4=(100,50))
        Vertical distances: ~35 pixels each (p2=(30,68), p6=(30,32), p3=(70,68), p5=(70,32))
        Expected EAR = (36 + 36) / (2 * 100) = 72 / 200 = 0.36
        """
        open_eye_pts = [
            (0.0, 50.0),    # P1: outer corner
            (30.0, 68.0),   # P2: top outer
            (70.0, 68.0),   # P3: top inner
            (100.0, 50.0),  # P4: inner corner
            (70.0, 32.0),   # P5: bottom inner
            (30.0, 32.0),   # P6: bottom outer
        ]
        ear = calculate_ear(open_eye_pts)
        self.assertAlmostEqual(ear, 0.36, places=2)
        self.assertFalse(is_eye_closed(ear, threshold=0.22))

    def test_calculate_ear_closed_eye(self):
        """
        Synthesize landmark coordinates for a CLOSED eye.
        Vertical eyelid distance collapses to ~6 pixels.
        Expected EAR = (6 + 6) / (2 * 100) = 12 / 200 = 0.06
        """
        closed_eye_pts = [
            (0.0, 50.0),    # P1: outer corner
            (30.0, 53.0),   # P2: top outer
            (70.0, 53.0),   # P3: top inner
            (100.0, 50.0),  # P4: inner corner
            (70.0, 47.0),   # P5: bottom inner
            (30.0, 47.0),   # P6: bottom outer
        ]
        ear = calculate_ear(closed_eye_pts)
        self.assertAlmostEqual(ear, 0.06, places=2)
        self.assertTrue(is_eye_closed(ear, threshold=0.22))

    def test_zero_width_division_by_zero_safety(self):
        """Ensure degenerate points with zero horizontal distance safely return 0.0."""
        zero_width_pts = [(50.0, 50.0)] * 6
        ear = calculate_ear(zero_width_pts)
        self.assertEqual(ear, 0.0)

    def test_invalid_input_length(self):
        """Ensure ValueError is raised if input does not have exactly 6 points."""
        with self.assertRaises(ValueError):
            calculate_ear([(0.0, 0.0)] * 4)

    def test_calculate_eyes_ear_combined(self):
        """Test calculation of left, right, and average EAR from full facial landmark array."""
        mock_landmarks = np.zeros((500, 2), dtype=np.float32)

        # Populate left eye indices: [33, 160, 158, 133, 153, 144] with open eye
        left_indices = [33, 160, 158, 133, 153, 144]
        left_pts = [(10, 50), (40, 68), (70, 68), (110, 50), (70, 32), (40, 32)]
        for idx, pt in zip(left_indices, left_pts):
            mock_landmarks[idx] = pt

        # Populate right eye indices: [362, 385, 387, 263, 373, 380] with closed eye
        right_indices = [362, 385, 387, 263, 373, 380]
        right_pts = [(210, 50), (240, 53), (270, 53), (310, 50), (270, 47), (240, 47)]
        for idx, pt in zip(right_indices, right_pts):
            mock_landmarks[idx] = pt

        l_ear, r_ear, avg_ear = calculate_eyes_ear(mock_landmarks, left_indices, right_indices)
        self.assertAlmostEqual(l_ear, 0.36, places=2)
        self.assertAlmostEqual(r_ear, 0.06, places=2)
        self.assertAlmostEqual(avg_ear, 0.21, places=2)


if __name__ == "__main__":
    unittest.main()
