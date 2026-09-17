"""
Veyro — MediaPipe Hand Tracker
================================
Wraps the MediaPipe Tasks HandLandmarker API.

Outputs per frame:
  - hand_landmarks      : 21 normalised 2D points (for cursor mapping)
  - world_landmarks     : 21 3D points in metres, wrist-relative (for gesture thresholds)
  - handedness          : 'Left' | 'Right'

Key design decisions:
  - Uses LIVE_STREAM running mode for async, non-blocking processing.
  - world_landmarks are used for ALL gesture distance checks (scale-invariant).
  - hand_landmarks (2D normalised) are used ONLY for cursor position mapping.
  - Single hand (MAX_NUM_HANDS=1) — sufficient for MVP, lower CPU.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.components.containers import landmark as mp_landmark

from src.gestures.config import (
    MAX_NUM_HANDS,
    MEDIAPIPE_MODEL_PATH,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
)


@dataclass
class HandData:
    """
    All landmark data for one detected hand in one frame.

    Attributes:
        landmarks_2d   : 21 NormalizedLandmark (x, y in [0,1], z relative)
        landmarks_3d   : 21 Landmark in metres, wrist at origin
        handedness     : 'Left' or 'Right' as seen by the camera
        timestamp_ms   : frame timestamp in milliseconds
    """
    landmarks_2d: list = field(default_factory=list)
    landmarks_3d: list = field(default_factory=list)
    handedness: str = "Unknown"
    timestamp_ms: int = 0


class HandTracker:
    """
    MediaPipe HandLandmarker wrapper for Veyro.

    Usage:
        tracker = HandTracker()
        tracker.start()
        ...
        tracker.process_frame(rgb_frame, timestamp_ms)
        data = tracker.latest          # HandData | None
        ...
        tracker.stop()
    """

    def __init__(self) -> None:
        model_path = Path(MEDIAPIPE_MODEL_PATH)
        if not model_path.exists():
            raise FileNotFoundError(
                f"MediaPipe model not found at '{model_path}'. "
                "Run: python -m src.tracking.download_model"
            )

        self._latest: Optional[HandData] = None
        self._lock = threading.Lock()

        base_options = mp_python.BaseOptions(
            model_asset_path=str(model_path)
        )
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.LIVE_STREAM,
            num_hands=MAX_NUM_HANDS,
            min_hand_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=MIN_TRACKING_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
            result_callback=self._on_result,
        )
        self._detector = mp_vision.HandLandmarker.create_from_options(options)

    # ── public ────────────────────────────────────────────────────────────

    def process_frame(self, rgb_frame, timestamp_ms: int) -> None:
        """
        Submit an RGB frame for async landmark detection.
        Results arrive via _on_result() and are stored in self.latest.

        Args:
            rgb_frame    : numpy array, shape (H, W, 3), dtype uint8, RGB order
            timestamp_ms : monotonic timestamp in milliseconds (must be increasing)
        """
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )
        self._detector.detect_async(mp_image, timestamp_ms)

    @property
    def latest(self) -> Optional[HandData]:
        """Thread-safe access to the most recent detection result."""
        with self._lock:
            return self._latest

    def stop(self) -> None:
        """Release the detector and free resources."""
        self._detector.close()

    # ── private ───────────────────────────────────────────────────────────

    def _on_result(
        self,
        result: mp_vision.HandLandmarkerResult,
        output_image: mp.Image,
        timestamp_ms: int,
    ) -> None:
        """
        Callback invoked by MediaPipe on each processed frame.
        Runs on MediaPipe's internal thread — uses a lock for thread safety.
        """
        with self._lock:
            if not result.hand_landmarks:
                # No hand detected — clear latest so state machine sees absence
                self._latest = None
                return

            # Take the first detected hand only (MAX_NUM_HANDS=1)
            lm_2d = result.hand_landmarks[0]
            lm_3d = result.hand_world_landmarks[0]
            cat = result.handedness[0][0]
            hand_side = getattr(cat, "category_name", "") or getattr(cat, "display_name", "") or "Unknown"

            self._latest = HandData(
                landmarks_2d=lm_2d,
                landmarks_3d=lm_3d,
                handedness=hand_side,
                timestamp_ms=timestamp_ms,
            )
