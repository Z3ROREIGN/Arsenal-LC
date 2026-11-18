from dataclasses import dataclass
from enum import Enum


class WeaponId(Enum):
    AR09Vektor = 0
    SM4Phantom = 1
    BR21Titan = 2
    SR8Spectre = 3
    SG12Breach = 4
    PX7Pulse = 5


class HitRegion(Enum):
    Body = 0
    Head = 1
    Limb = 2


@dataclass
class WeaponStats:
    id: WeaponId
    display_name: str
    role: str
    damage: float = 20.0              # dano por projétil à queima-roupa
    pellets: int = 1                  # projéteis por disparo (escopeta > 1)
    min_damage_fraction: float = 0.6  # fração do dano mantida além de falloff_end
    falloff_start: float = 20.0       # metros
    falloff_end: float = 50.0
    max_range: float = 120.0
    rounds_per_minute: float = 600.0
    automatic: bool = True
    magazine_size: int = 30
    reload_seconds: float = 2.0
    hip_spread: float = 2.0           # graus (cone) sem mirar
    aim_spread: float = 0.5           # graus (cone) mirando
    spread_per_shot: float = 0.3
    max_spread_bonus: float = 3.0
    spread_recover_per_second: float = 6.0
    recoil_pitch: float = 0.8
    recoil_yaw_range: float = 0.3
    recoil_recover_per_second: float = 4.0
    head_multiplier: float = 2.0
    limb_multiplier: float = 0.75

    @property
    def seconds_between_shots(self) -> float:
        return 60.0 / self.rounds_per_minute


def _build():
    W = WeaponStats
    d = {}
    d[WeaponId.AR09Vektor] = W(
        WeaponId.AR09Vektor, "AR-09 Vektor", "Rifle de assalto",
        damage=22, min_damage_fraction=0.7, falloff_start=25, falloff_end=60, max_range=120,
        rounds_per_minute=600, automatic=True, magazine_size=30, reload_seconds=2.2,
        hip_spread=2.2, aim_spread=0.5, spread_per_shot=0.35, max_spread_bonus=3, spread_recover_per_second=6,
        recoil_pitch=0.9, recoil_yaw_range=0.35, recoil_recover_per_second=4)
    d[WeaponId.SM4Phantom] = W(
        WeaponId.SM4Phantom, "SM-4 Phantom", "Submetralhadora",
        damage=17, min_damage_fraction=0.55, falloff_start=12, falloff_end=35, max_range=80,
        rounds_per_minute=850, automatic=True, magazine_size=25, reload_seconds=1.8,
        hip_spread=2.8, aim_spread=0.9, spread_per_shot=0.3, max_spread_bonus=3.5, spread_recover_per_second=7,
        recoil_pitch=0.55, recoil_yaw_range=0.4, recoil_recover_per_second=5)
    d[WeaponId.BR21Titan] = W(
        WeaponId.BR21Titan, "BR-21 Titan", "Rifle de batalha",
        damage=38, min_damage_fraction=0.75, falloff_start=35, falloff_end=80, max_range=150,
        rounds_per_minute=270, automatic=False, magazine_size=15, reload_seconds=2.6,
        hip_spread=2.5, aim_spread=0.25, spread_per_shot=0.8, max_spread_bonus=2.5, spread_recover_per_second=5,
        recoil_pitch=1.6, recoil_yaw_range=0.3, recoil_recover_per_second=6)
    d[WeaponId.SR8Spectre] = W(
        WeaponId.SR8Spectre, "SR-8 Spectre", "Rifle de precisão",
        damage=95, min_damage_fraction=0.9, falloff_start=80, falloff_end=200, max_range=300,
        rounds_per_minute=55, automatic=False, magazine_size=5, reload_seconds=3.2,
        hip_spread=6, aim_spread=0.02, spread_per_shot=1.5, max_spread_bonus=3, spread_recover_per_second=3,
        recoil_pitch=3.5, recoil_yaw_range=0.4, recoil_recover_per_second=5)
    d[WeaponId.SG12Breach] = W(
        WeaponId.SG12Breach, "SG-12 Breach", "Escopeta",
        damage=11, pellets=8, min_damage_fraction=0.15, falloff_start=6, falloff_end=18, max_range=40,
        rounds_per_minute=75, automatic=False, magazine_size=6, reload_seconds=3,
        hip_spread=5.5, aim_spread=4.5, spread_per_shot=0.5, max_spread_bonus=1, spread_recover_per_second=4,
        recoil_pitch=3, recoil_yaw_range=0.6, recoil_recover_per_second=6)
    d[WeaponId.PX7Pulse] = W(
        WeaponId.PX7Pulse, "PX-7 Pulse", "Pistola",
        damage=20, min_damage_fraction=0.6, falloff_start=15, falloff_end=40, max_range=80,
        rounds_per_minute=420, automatic=False, magazine_size=14, reload_seconds=1.5,
        hip_spread=1.8, aim_spread=0.7, spread_per_shot=0.5, max_spread_bonus=2, spread_recover_per_second=6,
        recoil_pitch=1.1, recoil_yaw_range=0.3, recoil_recover_per_second=7)
    return d


class WeaponCatalog:
    """Os números são PROVISÓRIOS (mesmos do protótipo Unity)."""
    _all = _build()

    @classmethod
    def all(cls):
        return list(cls._all.values())

    @classmethod
    def get(cls, weapon_id: WeaponId) -> WeaponStats:
        return cls._all[weapon_id]
