"""
Veyro — Phase 1b: Live Cursor Control Test
==========================================
Tests index-finger pointer tracking with adaptive velocity smoothing.

Features in this test:
  - Draws a yellow bounding box showing the camera active tracking zone.
    (Moving your fingertip to the edges of this box reaches the edges of your screen).
  - Your Windows mouse cursor follows your index fingertip in real-time.
  - Live HUD displays mapped Screen Coordinates (X, Y) and FPS.

Controls:
  SPACE — Toggle mouse control ON / OFF (useful if you want to pause movement)
  Q     — Quit test

Run with:
  .\\.venv\\Scripts\\python.exe test_cursor.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cv2
import numpy as np

from src.actions.mouse import MouseController
from src.capture.camera import Camera
from src.gestures.config import FRAME_REDUCTION_X, FRAME_REDUCTION_Y
from src.tracking.mediapipe_tracker import HandTracker

# Skeleton connections for 21-landmark hand
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),           # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),           # index
    (0, 9), (9, 10), (10, 11), (11, 12),      # middle
    (0, 13), (13, 14), (14, 15), (15, 16),    # ring
    (0, 17), (17, 18), (18, 19), (19, 20),    # pinky
    (5, 9), (9, 13), (13, 17),                # palm knuckle bar
]


def draw_hand_and_bounds(frame_bgr: np.ndarray, landmarks_2d, width: int, height: int):
    # 1. Draw Active Workspace Bounding Box (yellow)
    x1, y1 = FRAME_REDUCTION_X, FRAME_REDUCTION_Y
    x2, y2 = max(x1 + 10, width - FRAME_REDUCTION_X), max(y1 + 10, height - FRAME_REDUCTION_Y)
    cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 220, 255), 2)
    cv2.putText(frame_bgr, "Active Screen Area", (x1 + 5, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1)

    if not landmarks_2d:
        return None

    pts = [(int(lm.x * width), int(lm.y * height)) for lm in landmarks_2d]

    # Draw connections
    for s, e in HAND_CONNECTIONS:
        cv2.line(frame_bgr, pts[s], pts[e], (0, 180, 255), 2)

    # Draw landmark dots
    for i, pt in enumerate(pts):
        color = (0, 255, 0) if i == 8 else (220, 220, 220)
        cv2.circle(frame_bgr, pt, 6 if i == 8 else 3, color, -1)

    # Return index fingertip camera coordinate
    return pts[8]


def main():
    print("=" * 60)
    print("Veyro — Phase 1b: Live Cursor Movement Test")
    print("=" * 60)
    print("• Point your index finger to steer the mouse cursor.")
    print("• Press [SPACE] to toggle cursor control ON / OFF.")
    print("• Press [Q] to quit.\n")

    tracker = HandTracker()
    mouse = MouseController()
    control_enabled = True
    fps_times = []

    win_name = "Veyro — Phase 1b (Cursor Control)"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, 960, 540)

    with Camera() as cam:
        # Update camera size dynamically based on actual stream dimensions
        mouse.camera_width = cam.width
        mouse.camera_height = cam.height

        for rgb_frame, ts_ms in cam.frames():
            tracker.process_frame(rgb_frame, ts_ms)
            bgr = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

            data = tracker.latest
            cursor_pos = None

            if data and data.landmarks_2d:
                index_pt = draw_hand_and_bounds(bgr, data.landmarks_2d, cam.width, cam.height)
                if index_pt and control_enabled:
                    # Move desktop cursor
                    cursor_pos = mouse.move_to(float(index_pt[0]), float(index_pt[1]))
            else:
                mouse.reset()

            # FPS
            now = time.monotonic()
            fps_times.append(now)
            fps_times = [t for t in fps_times if now - t < 1.0]
            fps = len(fps_times)

            # Top overlay banner
            status_text = "CURSOR: ACTIVE (Move Hand)" if control_enabled else "CURSOR: PAUSED (Press Space)"
            status_color = (0, 255, 0) if control_enabled else (0, 165, 255)
            cv2.putText(bgr, status_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            cv2.putText(bgr, f"FPS: {fps}", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            if cursor_pos:
                cv2.putText(bgr, f"Screen: ({cursor_pos[0]}, {cursor_pos[1]})", (15, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.putText(bgr, "[SPACE] Toggle  |  [Q] Quit", (15, cam.height - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

            cv2.imshow(win_name, bgr)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):
                control_enabled = not control_enabled
                mouse.reset()

    tracker.stop()
    cv2.destroyAllWindows()
    print("\nTest completed.")


if __name__ == "__main__":
    main()
