from .weapons import WeaponStats, HitRegion


class DamageModel:
    @staticmethod
    def distance_factor(s: WeaponStats, distance: float) -> float:
        if distance <= s.falloff_start:
            return 1.0
        if distance >= s.falloff_end:
            return s.min_damage_fraction
        t = (distance - s.falloff_start) / (s.falloff_end - s.falloff_start)
        return 1.0 + (s.min_damage_fraction - 1.0) * t

    @staticmethod
    def region_multiplier(s: WeaponStats, region: HitRegion) -> float:
        if region == HitRegion.Head:
            return s.head_multiplier
        if region == HitRegion.Limb:
            return s.limb_multiplier
        return 1.0

    @staticmethod
    def compute(s: WeaponStats, distance: float, region: HitRegion) -> float:
        """Dano de UM projétil. Além do alcance máximo é zero."""
        if distance > s.max_range:
            return 0.0
        return s.damage * DamageModel.distance_factor(s, distance) * DamageModel.region_multiplier(s, region)
