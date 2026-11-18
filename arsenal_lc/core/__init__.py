"""Núcleo puro (sem pygame): regras de armas, dano, vida e ECHO TRACE.

Pode rodar no servidor dedicado no futuro. Não importe pygame aqui.
"""
from .weapons import WeaponId, HitRegion, WeaponStats, WeaponCatalog
from .weapon_state import WeaponState, FireResult
from .damage import DamageModel
from .health import HealthModel
from .trace import TraceRules, TraceSample, TraceBuffer, TraceStrand, TraceScanner
from .fake_walker import FakeTraceWalker

__all__ = [
    "WeaponId", "HitRegion", "WeaponStats", "WeaponCatalog", "WeaponState", "FireResult",
    "DamageModel", "HealthModel", "TraceRules", "TraceSample", "TraceBuffer",
    "TraceStrand", "TraceScanner", "FakeTraceWalker",
]
