"""
Veyro — Adaptive Velocity-Based Smoothing
==========================================
Eliminates cursor jitter without sacrificing responsiveness.

Problem with fixed EMA (what every other repo uses):
  High smoothing → laggy feel when moving fast
  Low smoothing  → jittery when hand is still
  You cannot win with a fixed alpha.

Solution — velocity-weighted alpha:
  Slow/still hand → alpha near MIN → heavy smoothing → stable cursor
  Fast hand       → alpha near MAX → light smoothing  → responsive cursor

Borrowed from: Lumina AirMouse (Kisses99) — the only production-shipped
gesture mouse that got smoothing right.
"""

from __future__ import annotations

import math

from src.gestures.config import (
    SMOOTH_ALPHA_MAX,
    SMOOTH_ALPHA_MIN,
    SMOOTH_DEADZONE,
    SMOOTH_SPEED_THRESHOLD,
)


class AdaptiveSmoother:
    """
    Velocity-adaptive exponential moving average for 2D cursor coordinates.

    Usage:
        smoother = AdaptiveSmoother()
        smooth_x, smooth_y = smoother.update(raw_x, raw_y)
    """

    def __init__(self) -> None:
        self._prev_x: float = 0.0
        self._prev_y: float = 0.0
        self._initialized: bool = False

    def update(self, raw_x: float, raw_y: float) -> tuple[float, float]:
        """
        Apply adaptive EMA to a new raw position.

        Args:
            raw_x, raw_y : new raw position in any consistent unit
                           (normalised [0,1] or screen pixels both work)

        Returns:
            (smooth_x, smooth_y) — smoothed position in same units
        """
        if not self._initialized:
            # First frame — accept the raw position directly
            self._prev_x = raw_x
            self._prev_y = raw_y
            self._initialized = True
            return raw_x, raw_y

        # Instantaneous displacement since last frame
        dx = raw_x - self._prev_x
        dy = raw_y - self._prev_y
        speed = math.hypot(dx, dy)

        # Deadzone: ignore micro-tremors below threshold
        if speed < SMOOTH_DEADZONE:
            return self._prev_x, self._prev_y

        # Velocity-weighted alpha:
        #   t = clamp(speed / speed_threshold, 0, 1)
        #   alpha = lerp(MIN_ALPHA, MAX_ALPHA, t)
        t = min(speed / SMOOTH_SPEED_THRESHOLD, 1.0)
        alpha = SMOOTH_ALPHA_MIN + t * (SMOOTH_ALPHA_MAX - SMOOTH_ALPHA_MIN)

        # EMA: new = alpha * raw + (1 - alpha) * prev
        smooth_x = alpha * raw_x + (1.0 - alpha) * self._prev_x
        smooth_y = alpha * raw_y + (1.0 - alpha) * self._prev_y

        self._prev_x = smooth_x
        self._prev_y = smooth_y
        return smooth_x, smooth_y

    def reset(self) -> None:
        """Reset state — call when hand disappears and reappears."""
        self._initialized = False
