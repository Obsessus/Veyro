"""
Veyro — Phase 1b: Upgraded Smooth Cursor & State Activation Test
=================================================================
Incorporates user feedback:
  1. Open Palm (5 fingers up) held for 0.5s -> ACTIVATES tracking.
  2. Fist held for ~3.0s -> DEACTIVATES tracking (freezes cursor).
  3. One-Euro Filter (1€) + Screen-Pixel Deadzone -> Eliminates hand trembling.
  4. Glowing Reticle indicator on active index fingertip.
  5. Ease-in glide -> Eliminates abrupt cursor teleportation/jumping.

Controls:
  [Q] — Quit test
  [SPACE] — Manual override toggle (Activate / Standby)

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
from src.gestures.classifier import GestureClassifier, GestureType, PostureHoldDetector
from src.gestures.config import FRAME_REDUCTION_X, FRAME_REDUCTION_Y


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),           # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),           # index
    (0, 9), (9, 10), (10, 11), (11, 12),      # middle
    (0, 13), (13, 14), (14, 15), (15, 16),    # ring
    (0, 17), (17, 18), (18, 19), (19, 20),    # pinky
    (5, 9), (9, 13), (13, 17),                # palm knuckle bar
]


def draw_glow_circle(img: np.ndarray, center: tuple[int, int], radius: int, color: tuple[int, int, int]):
    """Draw a futuristic dual-ring glowing cursor reticle."""
    # Outer soft glow ring
    cv2.circle(img, center, radius + 6, color, 1, cv2.LINE_AA)
    # Inner solid ring
    cv2.circle(img, center, radius, color, 2, cv2.LINE_AA)
    # Center target dot
    cv2.circle(img, center, 3, (255, 255, 255), -1)


def draw_progress_bar(img: np.ndarray, x: int, y: int, w: int, h: int, progress: float, color: tuple[int, int, int]):
    """Draw a sleek progress indicator bar."""
    cv2.rectangle(img, (x, y), (x + w, y + h), (50, 50, 50), -1)
    fill_w = int(w * min(1.0, max(0.0, progress)))
    if fill_w > 0:
        cv2.rectangle(img, (x, y), (x + fill_w, y + h), color, -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), (180, 180, 180), 1)


def main():
    print("=" * 65)
    print("Veyro — Upgraded Cursor Control & Posture Gating")
    print("=" * 65)
    print("• Show OPEN PALM (held 0.5s) to ACTIVATE tracking.")
    print("• Steer cursor with your INDEX FINGER (butter-smooth 1€ filter).")
    print("• Make a FIST (held ~3.0s) to DEACTIVATE tracking.")
    print("• Press [Q] to quit, or [SPACE] for quick manual toggle.\n")

    classifier = GestureClassifier()
    palm_activator = PostureHoldDetector(GestureType.OPEN_PALM, required_seconds=0.5)
    fist_deactivator = PostureHoldDetector(GestureType.FIST, required_seconds=3.0)

    mouse = MouseController()
    is_active = False
    fps_times = []

    win_name = "Veyro — Smooth Cursor & Posture Control"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, 960, 540)

    # Import tracker here
    from src.tracking.mediapipe_tracker import HandTracker
    tracker = HandTracker()

    with Camera() as cam:
        mouse.camera_width = cam.width
        mouse.camera_height = cam.height

        for rgb_frame, ts_ms in cam.frames():
            now = time.monotonic()
            tracker.process_frame(rgb_frame, ts_ms)
            bgr = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

            # Draw Active Screen Zone boundary
            x1, y1 = FRAME_REDUCTION_X, FRAME_REDUCTION_Y
            x2, y2 = max(x1 + 10, cam.width - FRAME_REDUCTION_X), max(y1 + 10, cam.height - FRAME_REDUCTION_Y)
            boundary_color = (0, 255, 120) if is_active else (80, 80, 80)
            cv2.rectangle(bgr, (x1, y1), (x2, y2), boundary_color, 2)

            data = tracker.latest
            current_posture = GestureType.UNKNOWN
            cursor_pos = None

            if data and data.landmarks_2d and data.landmarks_3d:
                # 1. Classify hand posture
                gesture_res = classifier.classify(data.landmarks_3d, data.landmarks_2d)
                current_posture = gesture_res.label

                # 2. Draw Hand Skeleton
                pts = [(int(lm.x * cam.width), int(lm.y * cam.height)) for lm in data.landmarks_2d]
                for s, e in HAND_CONNECTIONS:
                    cv2.line(bgr, pts[s], pts[e], (180, 150, 50), 1, cv2.LINE_AA)

                for i, pt in enumerate(pts):
                    cv2.circle(bgr, pt, 2, (200, 200, 200), -1)

                index_tip_pt = pts[8]

                # 3. State Transitions:
                if not is_active:
                    # Check for Open Palm activation
                    triggered, elapsed = palm_activator.update(current_posture, now)
                    if triggered:
                        is_active = True
                        mouse.reset()
                        palm_activator.reset()
                else:
                    # Check for Fist deactivation
                    triggered, elapsed = fist_deactivator.update(current_posture, now)
                    if triggered:
                        is_active = False
                        mouse.reset()
                        fist_deactivator.reset()

                    # 4. If Active, steer mouse pointer
                    if is_active:
                        draw_glow_circle(bgr, index_tip_pt, 12, (0, 255, 255))
                        cursor_pos = mouse.move_to(float(index_tip_pt[0]), float(index_tip_pt[1]))
            else:
                mouse.smoother.pause()
                palm_activator.reset()
                fist_deactivator.reset()

            # FPS calculation
            fps_times.append(now)
            fps_times = [t for t in fps_times if now - t < 1.0]
            fps = len(fps_times)

            # ── HUD OVERLAY ──────────────────────────────────────────────
            if is_active:
                status_title = "STATUS: ARMED & TRACKING"
                status_bg = (0, 180, 50)
            else:
                status_title = "STATUS: STANDBY (Show Palm to Arm)"
                status_bg = (50, 50, 180)

            cv2.rectangle(bgr, (10, 10), (420, 110), (20, 20, 20), -1)
            cv2.rectangle(bgr, (10, 10), (420, 110), status_bg, 2)

            cv2.putText(bgr, status_title, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_bg, 2)
            cv2.putText(bgr, f"Posture: {current_posture.value}", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

            # Show activation / deactivation hold progress
            if not is_active and current_posture == GestureType.OPEN_PALM:
                prog = palm_activator.progress(now)
                cv2.putText(bgr, f"Arming... {int(prog * 100)}%", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                draw_progress_bar(bgr, 160, 83, 240, 14, prog, (0, 255, 255))
            elif is_active and current_posture == GestureType.FIST:
                prog = fist_deactivator.progress(now)
                cv2.putText(bgr, f"Disarming... {int(prog * 100)}%", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 80, 255), 1)
                draw_progress_bar(bgr, 160, 83, 240, 14, prog, (0, 80, 255))
            elif cursor_pos:
                cv2.putText(bgr, f"Screen: ({cursor_pos[0]}, {cursor_pos[1]})", (20, 95),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 255, 180), 1)

            cv2.putText(bgr, f"FPS: {fps}", (cam.width - 100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(bgr, "[SPACE] Toggle  |  [Q] Quit", (15, cam.height - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

            cv2.imshow(win_name, bgr)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):
                is_active = not is_active
                mouse.reset()
                palm_activator.reset()
                fist_deactivator.reset()

    tracker.stop()
    cv2.destroyAllWindows()
    print("\nTest completed.")


if __name__ == "__main__":
    main()
