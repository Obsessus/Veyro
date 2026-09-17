"""
Veyro — Adaptive One-Euro Smoothing & Jitter Elimination
=========================================================
Implements the 1€ (One-Euro) Filter with pixel-scale deadzone and ease-in glide.

Why the 1€ Filter?
  - At low/zero speed (stationary hand):
    Cutoff frequency drops to MIN_CUTOFF (~0.4 Hz), heavily attenuating
    human physiological hand tremors (~8-12 Hz). The pointer locks solidly in place.
  - At high speed (deliberate sweep):
    Cutoff frequency dynamically scales up via BETA * velocity, providing
    instantaneous, zero-lag pointer tracking.

Additionally:
  - SMOOTH_DEADZONE_PIXELS: suppresses micro-tremors below threshold.
  - Ease-in tracking: when hand appears, smoothly glides cursor instead
    of abruptly teleporting/jumping across the screen.
"""

from __future__ import annotations

import math
import time
from typing import Optional, Tuple

from src.gestures.config import (
    ONE_EURO_BETA,
    ONE_EURO_D_CUTOFF,
    ONE_EURO_MIN_CUTOFF,
    SMOOTH_DEADZONE_PIXELS,
    SMOOTH_EASE_IN_RATE,
)


class LowPassFilter:
    """First-order low-pass exponential smoothing filter."""

    def __init__(self, alpha: float = 0.5) -> None:
        self._alpha = alpha
        self._y: Optional[float] = None

    def filter(self, x: float, alpha: Optional[float] = None) -> float:
        if alpha is not None:
            self._alpha = alpha
        if self._y is None:
            self._y = x
        else:
            self._y = self._alpha * x + (1.0 - self._alpha) * self._y
        return self._y

    def reset(self) -> None:
        self._y = None


class OneEuroFilter1D:
    """1D implementation of the 1€ filter by Géry Casiez et al."""

    def __init__(
        self,
        min_cutoff: float = ONE_EURO_MIN_CUTOFF,
        beta: float = ONE_EURO_BETA,
        d_cutoff: float = ONE_EURO_D_CUTOFF,
    ) -> None:
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)

        self._x_filter = LowPassFilter()
        self._dx_filter = LowPassFilter()
        self._t_prev: Optional[float] = None
        self._x_prev: Optional[float] = None

    @staticmethod
    def _compute_alpha(rate: float, cutoff: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        te = 1.0 / rate
        return 1.0 / (1.0 + tau / te)

    def filter(self, x: float, t: float) -> float:
        if self._t_prev is None:
            self._t_prev = t
            self._x_prev = x
            return self._x_filter.filter(x, 1.0)

        dt = t - self._t_prev
        if dt <= 0.0:
            dt = 1e-4

        rate = 1.0 / dt

        # Estimate derivative of the signal
        dx = (x - self._x_prev) * rate
        edx = self._dx_filter.filter(dx, self._compute_alpha(rate, self.d_cutoff))

        # Adaptive cutoff based on rate of change
        cutoff = self.min_cutoff + self.beta * abs(edx)
        alpha = self._compute_alpha(rate, cutoff)

        x_filtered = self._x_filter.filter(x, alpha)

        self._t_prev = t
        self._x_prev = x_filtered
        return x_filtered

    def reset(self) -> None:
        self._x_filter.reset()
        self._dx_filter.reset()
        self._t_prev = None
        self._x_prev = None


class AdaptiveSmoother:
    """
    2D cursor position stabilizer combining One-Euro filtering,
    pixel deadzone, and smooth ease-in glide.
    """

    def __init__(
        self,
        min_cutoff: float = ONE_EURO_MIN_CUTOFF,
        beta: float = ONE_EURO_BETA,
        d_cutoff: float = ONE_EURO_D_CUTOFF,
        deadzone_pixels: float = SMOOTH_DEADZONE_PIXELS,
    ) -> None:
        self.filter_x = OneEuroFilter1D(min_cutoff, beta, d_cutoff)
        self.filter_y = OneEuroFilter1D(min_cutoff, beta, d_cutoff)
        self.deadzone_pixels = float(deadzone_pixels)

        self._current_x: Optional[float] = None
        self._current_y: Optional[float] = None
        self._is_tracking: bool = False

    def update(
        self,
        raw_x: float,
        raw_y: float,
        timestamp_s: Optional[float] = None,
    ) -> Tuple[float, float]:
        """
        Smooth a 2D position input.

        Args:
            raw_x, raw_y: Target coordinates (in screen pixels).
            timestamp_s: Optional monotonic timestamp in seconds.

        Returns:
            (smooth_x, smooth_y): Rock-steady smoothed coordinates.
        """
        t = timestamp_s if timestamp_s is not None else time.monotonic()

        # 1. Initial frame or recovery from tracking loss
        if self._current_x is None or self._current_y is None:
            self._current_x = raw_x
            self._current_y = raw_y
            self.filter_x.filter(raw_x, t)
            self.filter_y.filter(raw_y, t)
            self._is_tracking = True
            return raw_x, raw_y

        # If tracking was briefly paused, smoothly glide towards new target
        if not self._is_tracking:
            self._current_x += (raw_x - self._current_x) * SMOOTH_EASE_IN_RATE
            self._current_y += (raw_y - self._current_y) * SMOOTH_EASE_IN_RATE
            self.filter_x.reset()
            self.filter_y.reset()
            self.filter_x.filter(self._current_x, t)
            self.filter_y.filter(self._current_y, t)
            self._is_tracking = True
            return self._current_x, self._current_y

        # 2. Pixel deadzone: ignore micro-tremors below threshold
        dist = math.hypot(raw_x - self._current_x, raw_y - self._current_y)
        if dist < self.deadzone_pixels:
            return self._current_x, self._current_y

        # 3. One-Euro dynamic filter
        smooth_x = self.filter_x.filter(raw_x, t)
        smooth_y = self.filter_y.filter(raw_y, t)

        self._current_x = smooth_x
        self._current_y = smooth_y
        return smooth_x, smooth_y

    def pause(self) -> None:
        """Mark tracking as briefly paused so next update eases in rather than jumping."""
        self._is_tracking = False

    def reset(self) -> None:
        """Completely reset all smoother history."""
        self._current_x = None
        self._current_y = None
        self._is_tracking = False
        self.filter_x.reset()
        self.filter_y.reset()
