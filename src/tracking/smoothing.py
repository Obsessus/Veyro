"""
Veyro — Fluid Damped Glide & Jitter Elimination
=================================================
Combines exponential continuous spring damping with Hermite soft-deadzone attenuation.

Why this beats fixed deadzones and box filters:
  - Box filters introduce a 100ms phase delay (lag/sluggishness).
  - Hard deadzones create a "sticky" threshold barrier where cursor is glued in mud.
  - Fluid Damping uses continuous exponential relaxation (1 - exp(-damping * dt)),
    giving that cinematic, butter-smooth "Codex"-style glide while reaching targets in 2-3 frames.
  - Hermite soft deadzone attenuates micro-tremors with a smooth cubic S-curve,
    completely absorbing human physiological hand shake without sudden friction jerks.
"""

from __future__ import annotations

import math
import time
from typing import Optional, Tuple

from src.gestures.config import (
    FLUID_BASE_DAMPING,
    FLUID_MAX_DAMPING,
    FLUID_SOFT_DEADZONE,
    SMOOTH_EASE_IN_RATE,
)


class AdaptiveSmoother:
    """
    Fluid-damped pointer stabilizer.
    """

    def __init__(
        self,
        base_damping: float = FLUID_BASE_DAMPING,
        max_damping: float = FLUID_MAX_DAMPING,
        soft_deadzone: float = FLUID_SOFT_DEADZONE,
    ) -> None:
        self.base_damping = float(base_damping)
        self.max_damping = float(max_damping)
        self.soft_deadzone = float(soft_deadzone)

        self._current_x: Optional[float] = None
        self._current_y: Optional[float] = None
        self._prev_time: Optional[float] = None
        self._is_tracking: bool = False

    def update(
        self,
        raw_x: float,
        raw_y: float,
        timestamp_s: Optional[float] = None,
    ) -> Tuple[float, float]:
        """
        Smooth a 2D position input using continuous exponential damping
        and cubic Hermite soft-deadzone attenuation.

        Args:
            raw_x, raw_y: Target coordinates (in screen pixels).
            timestamp_s: Optional monotonic timestamp in seconds.

        Returns:
            (smooth_x, smooth_y): Liquid-smooth coordinates.
        """
        t = timestamp_s if timestamp_s is not None else time.monotonic()

        # 1. Initial frame
        if self._current_x is None or self._current_y is None or self._prev_time is None:
            self._current_x = raw_x
            self._current_y = raw_y
            self._prev_time = t
            self._is_tracking = True
            return raw_x, raw_y

        dt = max(1e-4, min(0.08, t - self._prev_time))
        self._prev_time = t

        # Recovery from pause (smooth ease-in rather than jumping)
        if not self._is_tracking:
            self._current_x += (raw_x - self._current_x) * SMOOTH_EASE_IN_RATE
            self._current_y += (raw_y - self._current_y) * SMOOTH_EASE_IN_RATE
            self._is_tracking = True
            return self._current_x, self._current_y

        dx = raw_x - self._current_x
        dy = raw_y - self._current_y
        dist = math.hypot(dx, dy)

        # 2. Soft Hermite attenuation (kills micro-tremor without sticky threshold)
        if dist < self.soft_deadzone:
            s = dist / max(self.soft_deadzone, 1e-4)
            atten = s * s * (3.0 - 2.0 * s)  # Smooth cubic S-curve
            dx *= atten
            dy *= atten

        # 3. Velocity-adaptive damping: faster sweeps get higher damping to eliminate lag
        speed_factor = min(1.0, dist / 80.0)
        damping = self.base_damping + (self.max_damping - self.base_damping) * speed_factor

        # 4. Continuous exponential glide
        decay = 1.0 - math.exp(-damping * dt)
        self._current_x += dx * decay
        self._current_y += dy * decay

        return self._current_x, self._current_y

    def pause(self) -> None:
        """Mark tracking as briefly paused so next update eases in rather than jumping."""
        self._is_tracking = False

    def reset(self) -> None:
        """Completely reset all smoother history."""
        self._current_x = None
        self._current_y = None
        self._prev_time = None
        self._is_tracking = False
