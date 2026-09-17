"""
Veyro — Gesture Posture Classifier
====================================
Classifies 3D world hand landmarks into discrete hand postures:
  - OPEN_PALM : All 5 fingers extended facing forward (System Arming)
  - FIST      : All fingers curled tight (System Disarming)
  - POINTING  : Index extended, other fingers curled (Cursor Steering)
  - TWO_FINGERS: Index and Middle extended (Scroll Mode)
  - UNKNOWN   : Ambiguous or incidental hand pose (Silence over action)

Scale-invariant: uses 3D world landmark distances in meters.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class GestureType(str, Enum):
    OPEN_PALM = "OPEN_PALM"
    FIST = "FIST"
    POINTING = "POINTING"
    TWO_FINGERS = "TWO_FINGERS"
    UNKNOWN = "UNKNOWN"


@dataclass
class GestureResult:
    label: GestureType
    confidence: float
    bitmask: int
    finger_states: Dict[str, bool]


class GestureClassifier:
    """
    Pure classifier: maps 3D/2D hand landmarks to GestureResult.
    """

    def _dist_3d(self, p1, p2) -> float:
        return math.hypot(p1.x - p2.x, p1.y - p2.y, p1.z - p2.z)

    def _dist_2d(self, p1, p2) -> float:
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def classify(self, landmarks_3d, landmarks_2d=None) -> GestureResult:
        """
        Classify hand landmarks into a gesture.

        Args:
            landmarks_3d: 21 3D world landmarks (in meters, wrist at origin)
            landmarks_2d: Optional 21 2D normalized landmarks

        Returns:
            GestureResult with label, confidence, bitmask, and finger_states
        """
        if not landmarks_3d or len(landmarks_3d) < 21:
            return GestureResult(
                label=GestureType.UNKNOWN,
                confidence=0.0,
                bitmask=0,
                finger_states={f: False for f in ["thumb", "index", "middle", "ring", "pinky"]},
            )

        wrist = landmarks_3d[0]

        # Check each finger extension using 3D Euclidean distances
        # Fingers: (tip_idx, pip_idx, mcp_idx)
        fingers = {
            "index": (8, 6, 5),
            "middle": (12, 10, 9),
            "ring": (16, 14, 13),
            "pinky": (20, 18, 17),
        }

        states: Dict[str, bool] = {}
        for name, (tip_i, pip_i, mcp_i) in fingers.items():
            d_tip = self._dist_3d(landmarks_3d[tip_i], wrist)
            d_pip = self._dist_3d(landmarks_3d[pip_i], wrist)
            d_mcp = self._dist_3d(landmarks_3d[mcp_i], wrist)

            # Extended if tip is significantly farther from wrist than PIP & MCP
            is_ext = (d_tip > d_pip * 1.05) and (d_tip > d_mcp * 1.35)
            states[name] = is_ext

        # Thumb extension: check tip distance from index MCP and pinky MCP
        thumb_tip = landmarks_3d[4]
        index_mcp = landmarks_3d[5]
        pinky_mcp = landmarks_3d[17]

        d_thumb_pinky = self._dist_3d(thumb_tip, pinky_mcp)
        d_index_pinky = self._dist_3d(index_mcp, pinky_mcp)

        # Thumb is open when it extends away from the palm width baseline
        thumb_open = d_thumb_pinky > (d_index_pinky * 0.95)
        states["thumb"] = thumb_open

        # Build bitmask: [Thumb, Index, Middle, Ring, Pinky]
        bitmask = 0
        if states["thumb"]:
            bitmask |= 1 << 4
        if states["index"]:
            bitmask |= 1 << 3
        if states["middle"]:
            bitmask |= 1 << 2
        if states["ring"]:
            bitmask |= 1 << 1
        if states["pinky"]:
            bitmask |= 1 << 0

        # Count curled fingers using knuckle proximity
        curled_count = 0
        for name, (tip_i, pip_i, mcp_i) in fingers.items():
            d_tip_mcp = self._dist_3d(landmarks_3d[tip_i], landmarks_3d[mcp_i])
            if d_tip_mcp < 0.065:
                curled_count += 1

        # Hand span: max distance from wrist to any non-thumb fingertip
        max_span = max(self._dist_3d(landmarks_3d[t], wrist) for t in [8, 12, 16, 20])
        num_extended_4 = sum([states["index"], states["middle"], states["ring"], states["pinky"]])

        # 1. OPEN PALM: All 4 non-thumb fingers extended + thumb open
        if num_extended_4 == 4 and states["thumb"]:
            return GestureResult(
                label=GestureType.OPEN_PALM,
                confidence=0.98,
                bitmask=bitmask,
                finger_states=states,
            )
        elif num_extended_4 == 4:
            # All 4 main fingers up even if thumb is slightly tucked
            return GestureResult(
                label=GestureType.OPEN_PALM,
                confidence=0.88,
                bitmask=bitmask,
                finger_states=states,
            )

        # 2. FIST: All 4 fingers curled OR compact span with at least 3 curled
        if num_extended_4 == 0 or (curled_count >= 3 and max_span < 0.125):
            return GestureResult(
                label=GestureType.FIST,
                confidence=0.95,
                bitmask=bitmask,
                finger_states=states,
            )

        # 3. POINTING: Only index finger extended
        if states["index"] and not states["middle"] and not states["ring"] and not states["pinky"]:
            return GestureResult(
                label=GestureType.POINTING,
                confidence=0.95,
                bitmask=bitmask,
                finger_states=states,
            )

        # 4. TWO FINGERS: Index + Middle extended
        if states["index"] and states["middle"] and not states["ring"] and not states["pinky"]:
            return GestureResult(
                label=GestureType.TWO_FINGERS,
                confidence=0.92,
                bitmask=bitmask,
                finger_states=states,
            )

        # Incidental or transitional movement
        return GestureResult(
            label=GestureType.UNKNOWN,
            confidence=0.40,
            bitmask=bitmask,
            finger_states=states,
        )


class PostureHoldDetector:
    """
    Measures duration of held postures with a grace window.
    Prevents single-frame tracking flickers from instantly wiping progress.
    """

    def __init__(self, target_posture: GestureType, required_seconds: float, grace_seconds: float = 0.45) -> None:
        self.target_posture = target_posture
        self.required_seconds = float(required_seconds)
        self.grace_seconds = float(grace_seconds)
        self._start_time: Optional[float] = None
        self._last_seen_time: Optional[float] = None
        self._triggered: bool = False

    def update(self, current_posture: GestureType, timestamp: Optional[float] = None) -> Tuple[bool, float]:
        now = timestamp if timestamp is not None else time.monotonic()

        if current_posture == self.target_posture:
            if self._start_time is None:
                self._start_time = now
                self._triggered = False
            self._last_seen_time = now
            elapsed = now - self._start_time
            if elapsed >= self.required_seconds and not self._triggered:
                self._triggered = True
                return True, elapsed
            return False, elapsed
        else:
            # Check if within grace window (e.g. camera dropped a frame or brief jitter)
            if self._last_seen_time is not None and (now - self._last_seen_time) < self.grace_seconds:
                elapsed = now - self._start_time
                if elapsed >= self.required_seconds and not self._triggered:
                    self._triggered = True
                    return True, elapsed
                return False, elapsed
            else:
                self._start_time = None
                self._last_seen_time = None
                self._triggered = False
                return False, 0.0

    def progress(self, timestamp: Optional[float] = None) -> float:
        """Return held progress fraction from 0.0 to 1.0."""
        if self._start_time is None:
            return 0.0
        now = timestamp if timestamp is not None else time.monotonic()
        return min(1.0, (now - self._start_time) / max(self.required_seconds, 1e-4))

    def reset(self) -> None:
        self._start_time = None
        self._last_seen_time = None
        self._triggered = False
