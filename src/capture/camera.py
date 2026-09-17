"""
Veyro — Camera Capture
=======================
Wraps OpenCV video capture for DroidCam (or any webcam).

Design:
  - Returns RGB frames (MediaPipe expects RGB; OpenCV gives BGR by default)
  - Uses cv2.CAP_DSHOW on Windows for lowest latency
  - Exposes a simple generator interface: for frame, ts in camera: ...
  - Camera index and resolution come from config — never hardcoded here
"""

from __future__ import annotations

import time
from typing import Generator, Tuple

import cv2
import numpy as np

from src.gestures.config import (
    CAMERA_HEIGHT,
    CAMERA_INDEX,
    CAMERA_WIDTH,
    USE_DSHOW,
)

# Type alias for clarity
RGBFrame = np.ndarray   # shape (H, W, 3), dtype uint8, RGB


class Camera:
    """
    OpenCV capture abstraction for Veyro.

    Works identically with:
      - Built-in webcam (CAMERA_INDEX = 0)
      - DroidCam virtual device (CAMERA_INDEX = 1, confirmed)
      - IP Webcam or any other v4l/DirectShow device

    Usage:
        with Camera() as cam:
            for rgb_frame, timestamp_ms in cam:
                process(rgb_frame, timestamp_ms)
    """

    def __init__(self) -> None:
        backend = cv2.CAP_DSHOW if USE_DSHOW else cv2.CAP_ANY
        self._cap = cv2.VideoCapture(CAMERA_INDEX, backend)

        if not self._cap.isOpened():
            raise RuntimeError(
                f"Could not open camera at index {CAMERA_INDEX}. "
                "Check that DroidCam is connected and the index is correct."
            )

        # Request the configured resolution (DroidCam may override — that's fine)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

        # Actual resolution after device response
        self.width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def read(self) -> tuple[bool, RGBFrame | None]:
        """
        Read one frame. Returns (success, rgb_frame).
        rgb_frame is None if capture failed.
        """
        ret, bgr = self._cap.read()
        if not ret or bgr is None:
            return False, None
        # Flip horizontally so it acts like a mirror (more intuitive for the user)
        bgr = cv2.flip(bgr, 1)
        # Convert BGR → RGB for MediaPipe
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return True, rgb

    def frames(self) -> Generator[tuple[RGBFrame, int], None, None]:
        """
        Generator that yields (rgb_frame, timestamp_ms) continuously.
        Timestamp is monotonic milliseconds since epoch — required by MediaPipe LIVE_STREAM.

        Usage:
            for frame, ts in cam.frames():
                tracker.process_frame(frame, ts)
        """
        while True:
            ok, frame = self.read()
            if not ok:
                continue
            ts_ms = int(time.monotonic() * 1000)
            yield frame, ts_ms

    def release(self) -> None:
        """Release camera resources."""
        if self._cap.isOpened():
            self._cap.release()

    # Context manager support
    def __enter__(self) -> "Camera":
        return self

    def __exit__(self, *_) -> None:
        self.release()
