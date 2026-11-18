import math
from typing import List, Optional, Tuple

from ..core import HealthModel, TraceBuffer, TraceRules, TraceSample, FakeTraceWalker

DUMMY_RADIUS = 0.4
DUMMY_HEIGHT = 1.8


class Emitter:
    """Grava o rastro de movimento (porte do EchoTraceEmitter). Parado não deixa rastro."""

    def __init__(self, owner_id: int, team_id: int):
        self.buffer = TraceBuffer(owner_id, team_id, 80, False)
        self.crouched = False
        self.sprinting = False
        self._next_sample = 0.0
        self._last_time = 0.0
        self._last_pos = (0.0, 0.0)
        self._has_last = False

    def reset(self):
        self.buffer.clear()
        self._has_last = False

    def update(self, now: float, x: float, z: float):
        if now < self._next_sample:
            return
        self._next_sample = now + TraceRules.SAMPLE_INTERVAL
        if self._has_last:
            dt = now - self._last_time
            speed = (math.hypot(x - self._last_pos[0], z - self._last_pos[1]) / dt) if dt > 1e-4 else 0.0
            if speed < 14.0:  # acima disso foi teleporte (respawn)
                inten = TraceRules.intensity_from_movement(speed, self.crouched, self.sprinting)
                if inten > 0.0:
                    self.buffer.record(TraceSample(now, x, 0.05, z, inten, False))
        self._last_pos = (x, z)
        self._last_time = now
        self._has_last = True


class Dummy:
    """Alvo de treino (equipe 1). Com `route` vira patrulheiro e deixa rastros reais."""

    def __init__(self, name, x, z, color, route: Optional[List[Tuple[float, float]]] = None,
                 walk=3.2, run=5.6, owner_id=1):
        self.name = name
        self.x, self.z = x, z
        self.color = color
        self.team_id = 1
        self.facing = math.pi            # olha para -Z (o spawn)
        self.health = HealthModel(100.0, 0.0, 0.0, 0.0)
        self.respawn_seconds = 3.5
        self.dead_until = 0.0
        self.flash_until = 0.0
        self.route = route
        self.walk, self.run = walk, run
        self.idx = 1 if route and len(route) > 1 else 0
        self.running = False
        self.pause_until = 0.0
        self.emitter = Emitter(owner_id, 1) if route else None
        if route:
            self.x, self.z = route[0]

    @property
    def alive(self) -> bool:
        return not self.health.is_dead

    def take_damage(self, amount: float, now: float) -> bool:
        """Retorna True se este dano matou o alvo."""
        applied = self.health.apply_damage(amount)
        if applied > 0.0:
            self.flash_until = now + 0.06
        if self.health.is_dead:
            self.dead_until = now + self.respawn_seconds
            if self.emitter:
                self.emitter.sprinting = False
            return True
        return False

    def update(self, dt: float, now: float):
        if not self.alive:
            if now >= self.dead_until:
                self.health.revive()
            return
        if self.route and len(self.route) >= 2 and now >= self.pause_until:
            tx, tz = self.route[self.idx]
            dx, dz = tx - self.x, tz - self.z
            dist = math.hypot(dx, dz)
            if dist < 0.25:
                self.idx = (self.idx + 1) % len(self.route)
                self.running = (self.idx % 2 == 0)
                self.pause_until = now + (0.3 if self.running else 1.2)
            else:
                speed = self.run if self.running else self.walk
                step = min(dist, speed * dt)
                self.x += dx / dist * step
                self.z += dz / dist * step
                self.facing = math.atan2(dx, dz)
                if self.emitter:
                    self.emitter.sprinting = self.running
        if self.emitter:
            self.emitter.update(now, self.x, self.z)


class Decoy:
    """Dispositivo de rastro falso: após `delay`, um fantasma caminha e grava rastros SINTÉTICOS."""

    def __init__(self, x, z, owner_id, team_id, heading, speed, duration, delay, now):
        self.x, self.z = x, z
        self.owner_id, self.team_id = owner_id, team_id
        self.heading, self.speed, self.duration, self.delay = heading, speed, duration, delay
        self.t0 = now
        self.started = False
        self.walking = False
        self.walker: Optional[FakeTraceWalker] = None
        self.buffer: Optional[TraceBuffer] = None
        self.next_step = 0.0
        self.end_walk = 0.0
        self.finished = False

    def update(self, now: float, world):
        if not self.started:
            if now < self.t0 + self.delay:
                return
            self.started = True
            self.walking = True
            self.walker = FakeTraceWalker(self.x, 0.0, self.z, self.heading, self.speed, self.owner_id * 31 + 7)
            self.buffer = TraceBuffer(self.owner_id, self.team_id, 80, True)
            self.next_step = now
            self.end_walk = now + self.duration
        if self.walking:
            while now >= self.next_step:
                blocked = world.blocked_ahead(self.walker.x, self.walker.z, self.walker.heading_rad, 1.0)
                self.buffer.record(self.walker.step(TraceRules.SAMPLE_INTERVAL, self.next_step, blocked))
                self.next_step += TraceRules.SAMPLE_INTERVAL
            if now >= self.end_walk:
                self.walking = False
        elif now > self.end_walk + TraceRules.LIFETIME + 0.5:
            self.finished = True
