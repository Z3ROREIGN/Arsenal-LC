class HealthModel:
    """Vida com regeneração passiva LIMITADA (até regen_cap_fraction da vida máxima)."""

    def __init__(self, max_health=100.0, regen_delay=6.0, regen_per_second=6.0, regen_cap_fraction=0.6):
        self.max = max_health
        self.current = max_health
        self.regen_delay = regen_delay
        self.regen_per_second = regen_per_second
        self.regen_cap_fraction = regen_cap_fraction
        self._since_damage = 0.0

    @property
    def is_dead(self) -> bool:
        return self.current <= 0.0

    @property
    def regen_cap(self) -> float:
        return self.max * self.regen_cap_fraction

    def apply_damage(self, amount: float) -> float:
        if self.is_dead or amount <= 0.0:
            return 0.0
        applied = min(amount, self.current)
        self.current -= applied
        self._since_damage = 0.0
        return applied

    def heal(self, amount: float) -> float:
        if self.is_dead or amount <= 0.0:
            return 0.0
        before = self.current
        self.current = min(self.max, self.current + amount)
        return self.current - before

    def tick(self, dt: float):
        if self.is_dead:
            return
        self._since_damage += dt
        if self.regen_per_second <= 0.0 or self._since_damage < self.regen_delay:
            return
        cap = self.regen_cap
        if self.current >= cap:
            return
        self.current = min(cap, self.current + self.regen_per_second * dt)

    def revive(self):
        self.current = self.max
        self._since_damage = 0.0
