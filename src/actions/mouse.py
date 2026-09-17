"""
Veyro — Mouse Action Controller
================================
Translates camera tracking coordinates into smooth OS mouse movements and clicks.

Key Features:
  - Active workspace frame reduction (FRAME_REDUCTION_X / Y) so the user
    can reach all 4 screen corners without extreme physical arm extension.
  - Integration with AdaptiveSmoother to prevent pointer jitter when stationary.
  - Bounded clamping to ensure cursor stays strictly inside screen bounds.
  - Built with pynput for zero-latency, non-blocking native OS input.
"""

from __future__ import annotations

from typing import Optional, Tuple

import pynput
import pyautogui

from src.gestures.config import (
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    FRAME_REDUCTION_X,
    FRAME_REDUCTION_Y,
)
from src.tracking.smoothing import AdaptiveSmoother


class MouseController:
    """
    Controls desktop cursor movement and mouse button actions.

    Usage:
        mouse = MouseController()
        # On each frame with index fingertip landmark:
        screen_pos = mouse.move_to(norm_x * cam_w, norm_y * cam_h)
    """

    def __init__(
        self,
        screen_size: Optional[Tuple[int, int]] = None,
        camera_size: Optional[Tuple[int, int]] = None,
        smoother: Optional[AdaptiveSmoother] = None,
    ) -> None:
        if screen_size is not None:
            self.screen_width, self.screen_height = screen_size
        else:
            scr = pyautogui.size()
            self.screen_width, self.screen_height = int(scr.width), int(scr.height)

        if camera_size is not None:
            self.camera_width, self.camera_height = camera_size
        else:
            self.camera_width = CAMERA_WIDTH
            self.camera_height = CAMERA_HEIGHT

        self.smoother = smoother or AdaptiveSmoother()
        self._mouse = pynput.mouse.Controller()

    def map_camera_to_screen(self, cam_x: float, cam_y: float) -> Tuple[float, float]:
        """
        Map camera pixel coordinates to full screen resolution using
        the bounded active zone defined by FRAME_REDUCTION margins.

        Args:
            cam_x: X coordinate in camera pixel space [0, camera_width]
            cam_y: Y coordinate in camera pixel space [0, camera_height]

        Returns:
            (target_x, target_y): Floating-point screen coordinates clamped
                                  to [0, screen_width - 1], [0, screen_height - 1].
        """
        min_x = float(FRAME_REDUCTION_X)
        max_x = float(max(min_x + 1.0, self.camera_width - FRAME_REDUCTION_X))

        min_y = float(FRAME_REDUCTION_Y)
        max_y = float(max(min_y + 1.0, self.camera_height - FRAME_REDUCTION_Y))

        # Normalized ratio inside active zone [0.0, 1.0]
        tx = (cam_x - min_x) / (max_x - min_x)
        ty = (cam_y - min_y) / (max_y - min_y)

        # Clamp ratio to prevent out-of-bounds overshoot
        tx = max(0.0, min(1.0, tx))
        ty = max(0.0, min(1.0, ty))

        target_x = tx * (self.screen_width - 1)
        target_y = ty * (self.screen_height - 1)

        return target_x, target_y

    def move_to(self, cam_x: float, cam_y: float) -> Tuple[int, int]:
        """
        Map camera coordinates to screen space, smooth the movement,
        and update the OS cursor position.

        Args:
            cam_x: Raw X coordinate from camera frame
            cam_y: Raw Y coordinate from camera frame

        Returns:
            (int_x, int_y): The actual screen coordinate the cursor was set to.
        """
        raw_screen_x, raw_screen_y = self.map_camera_to_screen(cam_x, cam_y)
        smooth_x, smooth_y = self.smoother.update(raw_screen_x, raw_screen_y)

        int_x = int(round(smooth_x))
        int_y = int(round(smooth_y))

        # Clamp strictly to screen bounds
        int_x = max(0, min(self.screen_width - 1, int_x))
        int_y = max(0, min(self.screen_height - 1, int_y))

        try:
            self._mouse.position = (int_x, int_y)
        except Exception:
            # Fallback if pynput encounters desktop context restrictions
            try:
                pyautogui.moveTo(int_x, int_y, _pause=False)
            except Exception:
                pass

        return int_x, int_y

    def click(self, button: str = "left", count: int = 1) -> None:
        """Perform a mouse click (left, right, or middle)."""
        btn = pynput.mouse.Button.left
        if button == "right":
            btn = pynput.mouse.Button.right
        elif button == "middle":
            btn = pynput.mouse.Button.middle

        try:
            self._mouse.click(btn, count)
        except Exception:
            if button == "left":
                pyautogui.click(clicks=count)
            elif button == "right":
                pyautogui.rightClick()

    def press(self, button: str = "left") -> None:
        """Press and hold a mouse button (e.g. for drag)."""
        btn = pynput.mouse.Button.left if button == "left" else pynput.mouse.Button.right
        try:
            self._mouse.press(btn)
        except Exception:
            pyautogui.mouseDown(button=button)

    def release(self, button: str = "left") -> None:
        """Release a held mouse button."""
        btn = pynput.mouse.Button.left if button == "left" else pynput.mouse.Button.right
        try:
            self._mouse.release(btn)
        except Exception:
            pyautogui.mouseUp(button=button)

    def scroll(self, dy: int) -> None:
        """Scroll vertically: positive dy = scroll up, negative dy = scroll down."""
        try:
            self._mouse.scroll(0, dy)
        except Exception:
            pyautogui.scroll(dy)

    def reset(self) -> None:
        """Reset smoother state when tracking is lost or re-acquired."""
        self.smoother.reset()
