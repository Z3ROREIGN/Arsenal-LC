from dataclasses import dataclass, field
from typing import List, Optional


class TraceRules:
    """Regras do ECHO TRACE (constantes compartilhadas cliente/servidor)."""
    SAMPLE_INTERVAL = 0.2
    LIFETIME = 12.0
    REVEAL_DELAY = 1.5            # o scanner NUNCA mostra pontos mais novos que isto
    SCAN_RADIUS = 22.0
    SCAN_DURATION = 4.0
    SCAN_COOLDOWN = 12.0
    MIN_SPEED_TO_LEAVE_TRACE = 0.6
    STRAND_BREAK_TIME = 0.6
    STRAND_BREAK_DISTANCE = 4.0

    @staticmethod
    def intensity_from_movement(speed: float, crouched: bool, sprinting: bool) -> float:
        if speed < TraceRules.MIN_SPEED_TO_LEAVE_TRACE:
            return 0.0
        if crouched:
            return 0.3
        return 1.0 if sprinting else 0.6


@dataclass
class TraceSample:
    time: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    intensity: float = 0.0
    synthetic: bool = False  # rastro falso: só servidor/debug deve ler


class TraceBuffer:
    """Buffer circular de rastros de um dono (jogador ou dispositivo falso)."""

    def __init__(self, owner_id: int, team_id: int, capacity: int = 80, synthetic: bool = False):
        self.owner_id = owner_id
        self.team_id = team_id
        self.synthetic = synthetic
        self._items: List[Optional[TraceSample]] = [None] * max(2, capacity)
        self._start = 0
        self._count = 0

    @property
    def count(self) -> int:
        return self._count

    @property
    def capacity(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> TraceSample:  # 0 = mais antigo
        return self._items[(self._start + index) % len(self._items)]

    def record(self, s: TraceSample):
        cap = len(self._items)
        if self._count < cap:
            self._items[(self._start + self._count) % cap] = s
            self._count += 1
        else:
            self._items[self._start] = s
            self._start = (self._start + 1) % cap

    def clear(self):
        self._start = 0
        self._count = 0


@dataclass
class TraceStrand:
    owner_id: int = 0
    team_id: int = 0
    synthetic: bool = False
    samples: List[TraceSample] = field(default_factory=list)


class TraceScanner:
    """Garantias (testadas): nunca devolve pontos < REVEAL_DELAY nem > LIFETIME;
    só pontos dentro do raio; ignora a equipe do scanner."""

    @staticmethod
    def scan(buffers, now, cx, cz, radius, ignore_team_id) -> List[TraceStrand]:
        result: List[TraceStrand] = []
        r2 = radius * radius
        break_d2 = TraceRules.STRAND_BREAK_DISTANCE ** 2
        for buf in buffers:
            if ignore_team_id >= 0 and buf.team_id == ignore_team_id:
                continue
            strand = None
            for i in range(buf.count):
                s = buf[i]
                age = now - s.time
                if age > TraceRules.LIFETIME:
                    continue
                if age < TraceRules.REVEAL_DELAY:
                    break  # o resto é mais novo ainda
                dx, dz = s.x - cx, s.z - cz
                if dx * dx + dz * dz > r2:
                    strand = None
                    continue
                if strand is not None:
                    prev = strand.samples[-1]
                    ddx, ddz = s.x - prev.x, s.z - prev.z
                    if s.time - prev.time > TraceRules.STRAND_BREAK_TIME or ddx * ddx + ddz * ddz > break_d2:
                        strand = None
                if strand is None:
                    strand = TraceStrand(buf.owner_id, buf.team_id, buf.synthetic)
                    result.append(strand)
                strand.samples.append(s)
        return [st for st in result if len(st.samples) >= 2]
