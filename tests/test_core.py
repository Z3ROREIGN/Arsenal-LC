import math
import unittest

from arsenal_lc.core import (DamageModel, FakeTraceWalker, FireResult, HealthModel, HitRegion,
                             TraceBuffer, TraceRules, TraceSample, TraceScanner, WeaponCatalog,
                             WeaponId, WeaponState)


def walk(owner, team, samples, start_x=0.0, start_time=0.0):
    buf = TraceBuffer(owner, team, 200)
    for i in range(samples):
        buf.record(TraceSample(start_time + i * 0.2, start_x + i, 0.0, 0.0, 0.6))
    return buf


def scan(buf, now, cx=0.0, radius=1000.0, ignore=-1):
    return TraceScanner.scan([buf], now, cx, 0.0, radius, ignore)


class TraceTests(unittest.TestCase):
    def test_never_reveals_samples_younger_than_reveal_delay(self):
        strands = scan(walk(1, 1, 50), 10.0)
        self.assertTrue(strands)
        for st in strands:
            for s in st.samples:
                self.assertGreaterEqual(10.0 - s.time, TraceRules.REVEAL_DELAY - 0.001)

    def test_never_reveals_expired_samples(self):
        strands = scan(walk(1, 1, 50), 20.0)
        self.assertTrue(strands)
        for st in strands:
            for s in st.samples:
                self.assertLessEqual(20.0 - s.time, TraceRules.LIFETIME + 0.001)

    def test_ignores_samples_outside_radius(self):
        self.assertEqual([], scan(walk(1, 1, 30, start_x=100.0), 10.0, 0.0, TraceRules.SCAN_RADIUS))

    def test_ignores_own_team(self):
        res = TraceScanner.scan([walk(1, 0, 30), walk(2, 1, 30)], 10.0, 0.0, 0.0, 1000.0, 0)
        self.assertTrue(res)
        self.assertTrue(all(st.team_id == 1 for st in res))

    def test_time_gap_splits_strands(self):
        buf = TraceBuffer(1, 1, 50)
        for i in range(5):
            buf.record(TraceSample(i * 0.2, float(i), 0, 0, 0.6))
        for i in range(5):
            buf.record(TraceSample(3.0 + i * 0.2, 10.0 + i, 0, 0, 0.6))
        self.assertEqual(2, len(scan(buf, 6.0)))

    def test_standing_still_leaves_no_trace(self):
        self.assertEqual(0.0, TraceRules.intensity_from_movement(0.1, False, False))

    def test_sprint_stronger_than_walk_stronger_than_crouch(self):
        c = TraceRules.intensity_from_movement(2, True, False)
        w = TraceRules.intensity_from_movement(4, False, False)
        s = TraceRules.intensity_from_movement(6, False, True)
        self.assertTrue(0 < c < w < s)

    def test_buffer_overwrites_oldest_when_full(self):
        buf = TraceBuffer(1, 1, 4)
        for i in range(6):
            buf.record(TraceSample(float(i)))
        self.assertEqual(4, buf.count)
        self.assertEqual(2.0, buf[0].time)
        self.assertEqual(5.0, buf[3].time)

    def test_fake_walker_covers_expected_distance_and_is_synthetic(self):
        w = FakeTraceWalker(0, 0, 0, 0.0, 5.0, 1)
        px = pz = total = 0.0
        for i in range(10):
            s = w.step(0.2, i * 0.2, False)
            self.assertTrue(s.synthetic)
            total += math.hypot(s.x - px, s.z - pz)
            px, pz = s.x, s.z
        self.assertAlmostEqual(10.0, total, places=2)

    def test_fake_walker_turns_when_blocked(self):
        w = FakeTraceWalker(3, 0, 4, 0.0, 5.0, 2)
        h = w.heading_rad
        w.step(0.2, 0.0, True)
        self.assertAlmostEqual(3.0, w.x)
        self.assertAlmostEqual(4.0, w.z)
        self.assertNotEqual(h, w.heading_rad)


class DamageTests(unittest.TestCase):
    def test_full_until_falloff_start_and_min_beyond_end(self):
        ar = WeaponCatalog.get(WeaponId.AR09Vektor)
        self.assertAlmostEqual(1.0, DamageModel.distance_factor(ar, ar.falloff_start))
        self.assertAlmostEqual(ar.min_damage_fraction, DamageModel.distance_factor(ar, ar.falloff_end + 10))

    def test_damage_never_increases_with_distance(self):
        for w in WeaponCatalog.all():
            prev = float("inf")
            for d in range(0, int(w.max_range) + 1):
                dmg = DamageModel.compute(w, float(d), HitRegion.Body)
                self.assertLessEqual(dmg, prev + 1e-4)
                prev = dmg

    def test_head_gt_body_gt_limb(self):
        ar = WeaponCatalog.get(WeaponId.AR09Vektor)
        h = DamageModel.compute(ar, 10, HitRegion.Head)
        b = DamageModel.compute(ar, 10, HitRegion.Body)
        l = DamageModel.compute(ar, 10, HitRegion.Limb)
        self.assertTrue(h > b > l)

    def test_zero_beyond_max_range(self):
        ar = WeaponCatalog.get(WeaponId.AR09Vektor)
        self.assertEqual(0.0, DamageModel.compute(ar, ar.max_range + 1, HitRegion.Body))


class WeaponStateTests(unittest.TestCase):
    def make(self, wid=WeaponId.AR09Vektor):
        return WeaponState(WeaponCatalog.get(wid), 5)

    def test_fire_consumes_ammo_and_respects_cadence(self):
        st = self.make()
        r, _, _ = st.try_fire(0.0)
        self.assertEqual(FireResult.Fired, r)
        self.assertEqual(st.stats.magazine_size - 1, st.ammo)
        r, _, _ = st.try_fire(0.01)
        self.assertEqual(FireResult.Cooldown, r)
        r, _, _ = st.try_fire(st.stats.seconds_between_shots + 0.001)
        self.assertEqual(FireResult.Fired, r)

    def test_empty_magazine_then_reload_refills(self):
        st = self.make(WeaponId.PX7Pulse)
        t = 0.0
        for _ in range(st.stats.magazine_size):
            self.assertEqual(FireResult.Fired, st.try_fire(t)[0])
            t += 1.0
        self.assertEqual(FireResult.EmptyMagazine, st.try_fire(t)[0])
        self.assertTrue(st.start_reload(t))
        self.assertEqual(FireResult.Reloading, st.try_fire(t + 0.1)[0])
        st.tick(0.1, t + st.stats.reload_seconds + 0.01)
        self.assertEqual(st.stats.magazine_size, st.ammo)
        self.assertFalse(st.is_reloading)

    def test_cannot_reload_full_magazine(self):
        self.assertFalse(self.make().start_reload(0.0))

    def test_aiming_and_crouching_tighten_spread_moving_widens(self):
        st = self.make()
        hip = st.current_spread_degrees(False, 0.0, False)
        self.assertLess(st.current_spread_degrees(True, 0.0, False), hip)
        self.assertLess(st.current_spread_degrees(False, 0.0, True), hip)
        self.assertGreater(st.current_spread_degrees(False, 1.0, False), hip)

    def test_spread_bonus_grows_with_shots_and_recovers(self):
        st = self.make()
        st.try_fire(0.0)
        self.assertGreater(st.spread_bonus, 0.0)
        st.tick(5.0, 5.0)
        self.assertEqual(0.0, st.spread_bonus)

    def test_spread_offset_inside_cone(self):
        st = self.make()
        for _ in range(200):
            y, p = st.sample_spread_offset(2.0)
            self.assertLessEqual(math.hypot(y, p), 2.0 + 1e-9)


class HealthTests(unittest.TestCase):
    def test_regen_only_after_delay_and_up_to_cap(self):
        h = HealthModel(100, 6, 6, 0.6)
        h.apply_damage(70)
        h.tick(3.0)
        self.assertAlmostEqual(30.0, h.current)
        h.tick(3.0)          # delay atingido
        h.tick(30.0)
        self.assertAlmostEqual(60.0, h.current)   # teto de 60%

    def test_death_and_revive(self):
        h = HealthModel()
        h.apply_damage(500)
        self.assertTrue(h.is_dead)
        h.revive()
        self.assertEqual(100.0, h.current)


if __name__ == "__main__":
    unittest.main()
