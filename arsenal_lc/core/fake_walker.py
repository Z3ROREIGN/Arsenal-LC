import math
import random

from .trace import TraceSample


class FakeTraceWalker:
    """Fantasma do rastro falso. heading em radianos a partir de +Z (x += sin, z += cos)."""

    def __init__(self, x, y, z, heading_rad, speed, seed):
        self.x, self.y, self.z = x, y, z
        self.heading_rad = heading_rad
        self.speed = speed
        self._rng = random.Random(seed)
        self._turn_timer = 0.8

    def step(self, dt: float, now: float, blocked_ahead: bool) -> TraceSample:
        if blocked_ahead:
            sign = -1.0 if self._rng.random() < 0.5 else 1.0
            self.heading_rad += sign * (1.2 + self._rng.random() * 0.8)
            self._turn_timer = 0.5
        else:
            self._turn_timer -= dt
            if self._turn_timer <= 0.0:
                self.heading_rad += (self._rng.random() - 0.5) * 1.0
                self._turn_timer = 0.6 + self._rng.random() * 0.8
            self.x += math.sin(self.heading_rad) * self.speed * dt
            self.z += math.cos(self.heading_rad) * self.speed * dt
        return TraceSample(now, self.x, self.y, self.z, 1.0 if self.speed >= 5.0 else 0.6, True)
