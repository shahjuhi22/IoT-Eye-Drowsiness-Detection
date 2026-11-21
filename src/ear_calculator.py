"""
ear_calculator.py — Eye Aspect Ratio (EAR) Mathematical Engine
==============================================================
Implements the Soukupová and Čech (2016) Eye Aspect Ratio algorithm for
detecting eye-closure in real-time facial landmark frames.

EAR Equation:
              ||p2 - p6|| + ||p3 - p5||
    EAR  =  ─────────────────────────────
                    2 · ||p1 - p4||

Where:
    p1, p4 = Horizontal eye corner coordinates (lateral and medial canthi)
    p2, p6 = Vertical upper/lower eyelid landmarks (outer vertical pair)
    p3, p5 = Vertical upper/lower eyelid landmarks (inner vertical pair)
    || · || = Euclidean distance (L2 norm)

Behavior:
    - Eye fully open: EAR typically ranges from 0.25 to 0.38
    - Eye fully closed: EAR drops rapidly below 0.20 (typically 0.12 - 0.18)
    - Scale invariant: Normalizing by horizontal length ensures EAR remains stable
      regardless of distance between the subject and the webcam.
"""

from typing import List, Tuple, Union
import numpy as np


def euclidean_distance(pt1: Union[np.ndarray, Tuple[float, float], List[float]],
                       pt2: Union[np.ndarray, Tuple[float, float], List[float]]) -> float:
    """
    Compute 2D Euclidean distance between two points.
    
    Args:
        pt1: (x, y) coordinates of first point
        pt2: (x, y) coordinates of second point
        
    Returns:
        float: Euclidean distance
    """
    p1 = np.asarray(pt1, dtype=np.float64)[:2]
    p2 = np.asarray(pt2, dtype=np.float64)[:2]
    return float(np.linalg.norm(p1 - p2))


def calculate_ear(eye_points: Union[np.ndarray, List]) -> float:
    """
    Calculate the Eye Aspect Ratio (EAR) for a single eye given 6 landmarks.
    
    Expected order of 6 points:
        [P1 (outer), P2 (top-outer), P3 (top-inner), P4 (inner), P5 (bottom-inner), P6 (bottom-outer)]
        
    Args:
        eye_points: Iterable of 6 (x, y) landmark coordinates.
        
    Returns:
        float: Calculated EAR value. Returns 0.0 if points are degenerate.
    """
    if eye_points is None or len(eye_points) != 6:
        raise ValueError(f"calculate_ear expects exactly 6 landmark points, got {len(eye_points) if eye_points else 0}")

    pts = [np.asarray(pt, dtype=np.float64)[:2] for pt in eye_points]

    p1, p2, p3, p4, p5, p6 = pts[0], pts[1], pts[2], pts[3], pts[4], pts[5]

    # Two vertical distances
    v1 = euclidean_distance(p2, p6)
    v2 = euclidean_distance(p3, p5)

    # One horizontal distance
    h = euclidean_distance(p1, p4)

    # Prevent division by zero
    if h < 1e-6:
        return 0.0

    ear = (v1 + v2) / (2.0 * h)
    return float(ear)


def calculate_eyes_ear(landmarks: np.ndarray,
                       left_indices: List[int],
                       right_indices: List[int]) -> Tuple[float, float, float]:
    """
    Extract eye landmark coordinates from an array of facial landmarks and
    compute Left EAR, Right EAR, and Average EAR.
    
    Args:
        landmarks: Array or list of (x, y) coordinates for all face landmarks.
        left_indices: 6 indices representing the left eye.
        right_indices: 6 indices representing the right eye.
        
    Returns:
        Tuple[float, float, float]: (left_ear, right_ear, avg_ear)
    """
    if landmarks is None or len(landmarks) == 0:
        return 0.0, 0.0, 0.0

    left_pts = [landmarks[idx] for idx in left_indices]
    right_pts = [landmarks[idx] for idx in right_indices]

    left_ear = calculate_ear(left_pts)
    right_ear = calculate_ear(right_pts)
    avg_ear = (left_ear + right_ear) / 2.0

    return float(left_ear), float(right_ear), float(avg_ear)


def is_eye_closed(ear: float, threshold: float = 0.22) -> bool:
    """
    Determine whether an eye is closed based on threshold.
    
    Args:
        ear: Computed EAR value
        threshold: Eye closure threshold
        
    Returns:
        bool: True if closed (ear < threshold), False otherwise
    """
    return ear < threshold
