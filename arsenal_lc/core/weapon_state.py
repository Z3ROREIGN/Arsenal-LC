import math
import random
from enum import Enum

from .weapons import WeaponStats


class FireResult(Enum):
    Fired = 0
    Cooldown = 1
    EmptyMagazine = 2
    Reloading = 3


def _clamp01(v: float) -> float:
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


class WeaponState:
    """Munição, cadência, recarga, dispersão e recuo. O tempo (now) vem do chamador."""

    def __init__(self, stats: WeaponStats, seed: int = 1):
        self.stats = stats
        self._rng = random.Random(seed)
        self.ammo = stats.magazine_size
        self.is_reloading = False
        self.reload_progress = 0.0
        self.spread_bonus = 0.0
        self._next_fire_time = 0.0
        self._reload_start = 0.0
        self._reload_end = 0.0

    def current_spread_degrees(self, aiming: bool, move_factor: float, crouched: bool) -> float:
        base = self.stats.aim_spread if aiming else self.stats.hip_spread
        move = 1.0 + 0.8 * _clamp01(move_factor)
        stance = 0.7 if crouched else 1.0
        return base * move * stance + self.spread_bonus

    def try_fire(self, now: float):
        """Retorna (FireResult, kick_pitch, kick_yaw)."""
        if self.is_reloading:
            return FireResult.Reloading, 0.0, 0.0
        if self.ammo <= 0:
            return FireResult.EmptyMagazine, 0.0, 0.0
        if now < self._next_fire_time:
            return FireResult.Cooldown, 0.0, 0.0
        s = self.stats
        self.ammo -= 1
        self._next_fire_time = now + s.seconds_between_shots
        self.spread_bonus = min(s.max_spread_bonus, self.spread_bonus + s.spread_per_shot)
        kick_pitch = s.recoil_pitch * (0.85 + 0.3 * self._rng.random())
        kick_yaw = s.recoil_yaw_range * (self._rng.random() * 2.0 - 1.0)
        return FireResult.Fired, kick_pitch, kick_yaw

    def start_reload(self, now: float) -> bool:
        if self.is_reloading or self.ammo >= self.stats.magazine_size:
            return False
        self.is_reloading = True
        self._reload_start = now
        self._reload_end = now + self.stats.reload_seconds
        self.reload_progress = 0.0
        return True

    def cancel_reload(self):
        self.is_reloading = False
        self.reload_progress = 0.0

    def tick(self, dt: float, now: float):
        if self.is_reloading:
            self.reload_progress = _clamp01((now - self._reload_start) / self.stats.reload_seconds)
            if now >= self._reload_end:
                self.ammo = self.stats.magazine_size  # reserva infinita no treino
                self.is_reloading = False
                self.reload_progress = 0.0
        self.spread_bonus = max(0.0, self.spread_bonus - self.stats.spread_recover_per_second * dt)

    def sample_spread_offset(self, cone_degrees: float):
        """Desvio uniforme dentro do cone. Retorna (yaw_deg, pitch_deg)."""
        a = self._rng.random() * math.pi * 2.0
        r = math.sqrt(self._rng.random()) * cone_degrees
        return math.cos(a) * r, math.sin(a) * r
