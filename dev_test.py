"""
Veyro — Dev Test: Camera + Hand Landmark Visualizer
=====================================================
Run this to confirm the full tracking pipeline works end-to-end.

What you should see:
  - Your DroidCam feed (mirrored, so it feels natural)
  - Green dots on your 21 hand landmarks
  - Blue lines connecting the skeleton
  - Top-left overlay showing: FPS, landmark count, index fingertip XYZ

Controls:
  Q  — quit

Usage:
    .venv\\Scripts\\python.exe dev_test.py
"""

import sys
import time
from pathlib import Path

# Make sure src/ is importable when running from repo root
sys.path.insert(0, str(Path(__file__).parent))

import cv2
import numpy as np

from src.capture.camera import Camera
from src.tracking.mediapipe_tracker import HandTracker

import mediapipe as mp

# Hand skeleton connections — fixed for 21-landmark MediaPipe hand model
# (palm, thumb, index, middle, ring, pinky chains)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),           # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),           # index
    (0, 9), (9, 10), (10, 11), (11, 12),      # middle
    (0, 13), (13, 14), (14, 15), (15, 16),    # ring
    (0, 17), (17, 18), (18, 19), (19, 20),    # pinky
    (5, 9), (9, 13), (13, 17),                # palm knuckle bar
]


def draw_landmarks_manual(frame_bgr: np.ndarray, landmarks_2d, width: int, height: int) -> None:
    """Draw hand skeleton on a BGR frame using 2D normalised landmarks."""
    if not landmarks_2d:
        return

    # Convert normalised (0-1) to pixel coords
    pts = [
        (int(lm.x * width), int(lm.y * height))
        for lm in landmarks_2d
    ]

    # Draw connections
    for start_idx, end_idx in HAND_CONNECTIONS:
        cv2.line(frame_bgr, pts[start_idx], pts[end_idx], (0, 180, 255), 2)

    # Draw landmark dots
    for i, pt in enumerate(pts):
        color = (0, 255, 0) if i == 8 else (255, 255, 255)  # index tip = green
        cv2.circle(frame_bgr, pt, 5 if i == 8 else 3, color, -1)

    # Label index fingertip (landmark 8) prominently
    cv2.putText(frame_bgr, "INDEX TIP", pts[8],
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)


def main() -> None:
    print("Starting Veyro dev test...")
    print("Press Q in the preview window to quit.\n")

    tracker = HandTracker()
    fps_times: list[float] = []

    window_name = "Veyro — Dev Test (Hand Tracker)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 960, 540)

    with Camera() as cam:
        print(f"Camera opened: {cam.width}x{cam.height}")
        print("Waiting for hand landmarks...\n")

        for rgb_frame, ts_ms in cam.frames():
            # Send frame to MediaPipe (async — result arrives via callback)
            tracker.process_frame(rgb_frame, ts_ms)

            # Convert RGB back to BGR for OpenCV display
            bgr = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

            # Get latest landmark result (may be None if no hand detected)
            data = tracker.latest

            if data is not None:
                draw_landmarks_manual(bgr, data.landmarks_2d, cam.width, cam.height)

                # Print 3D world coords of index fingertip (landmark 8) to console
                lm8_3d = data.landmarks_3d[8]
                print(
                    f"\rIndex tip 3D (m): "
                    f"x={lm8_3d.x:+.4f}  y={lm8_3d.y:+.4f}  z={lm8_3d.z:+.4f}  "
                    f"hand={data.handedness}",
                    end="", flush=True
                )
            else:
                print("\rNo hand detected          ", end="", flush=True)

            # FPS calculation
            now = time.monotonic()
            fps_times.append(now)
            fps_times = [t for t in fps_times if now - t < 1.0]
            fps = len(fps_times)

            # Overlay: FPS + status
            status = f"HAND DETECTED ({data.handedness})" if data else "No hand"
            cv2.putText(bgr, f"FPS: {fps}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(bgr, status, (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 255, 0) if data else (0, 0, 255), 2)
            cv2.putText(bgr, "Press Q to quit", (10, cam.height - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

            cv2.imshow("Veyro — Dev Test (Hand Tracker)", bgr)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    tracker.stop()
    cv2.destroyAllWindows()
    print("\n\nDev test complete.")


if __name__ == "__main__":
    main()
