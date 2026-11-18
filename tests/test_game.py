import math
import unittest

from arsenal_lc.core import TraceRules, WeaponId
from arsenal_lc.game.entities import Dummy
from arsenal_lc.game.sim import Game, InputState
from arsenal_lc.game.world import World, Box, build_test_map, SPAWN_POINT

DT = 1 / 60


def run(game, seconds, inp=None):
    inp = inp or InputState()
    for _ in range(int(seconds / DT)):
        game.update(DT, inp)


def empty_game(w=None):
    return Game(world=w or World([], bounds=(-100, 100, -100, 100)), with_targets=False)


class WorldTests(unittest.TestCase):
    def test_player_cannot_walk_through_walls(self):
        g = Game(with_targets=False)
        g.player.x, g.player.z = -30.0 + 1.0, 0.0
        run(g, 2.0, InputState(move_x=-1.0))
        self.assertGreaterEqual(g.player.x, -30.0 + 0.3)

    def test_collision_with_box(self):
        w = World([Box("b", 0, 5, 4, 2, 3, "wall")], bounds=(-50, 50, -50, 50))
        g = empty_game(w)
        g.player.x, g.player.z = 0.0, 0.0
        run(g, 3.0, InputState(move_z=1.0))
        self.assertLess(g.player.z, 5 - 1 + 0.01)

    def test_test_map_has_expected_parts(self):
        w = build_test_map()
        names = {b.name for b in w.boxes}
        for n in ("Muro_N", "Pista_O", "Sala_O", "Plataforma", "Degrau_6", "Caixa_4"):
            self.assertIn(n, names)

    def test_spawn_is_free(self):
        w = build_test_map()
        x, z = w.move_circle(SPAWN_POINT[0], SPAWN_POINT[1], 0, 0, 0.35)
        self.assertAlmostEqual(SPAWN_POINT[0], x)
        self.assertAlmostEqual(SPAWN_POINT[1], z)


class MovementTests(unittest.TestCase):
    def test_sprint_faster_than_walk_faster_than_crouch(self):
        def dist(inp, crouch=False):
            g = empty_game()
            g.player.x = g.player.z = 0.0
            g.player.crouched = crouch
            run(g, 1.0, inp)
            return math.hypot(g.player.x, g.player.z)
        walk = dist(InputState(move_z=0.5))
        sprint = dist(InputState(move_z=1.0))
        crouch = dist(InputState(move_z=0.5), crouch=True)
        self.assertTrue(crouch < walk < sprint)

    def test_aiming_slows_down(self):
        a, b = empty_game(), empty_game()
        run(a, 1.0, InputState(move_z=0.5))
        run(b, 1.0, InputState(move_z=0.5, aim_held=True))
        self.assertGreater(a.player.z, b.player.z)


class ShootingTests(unittest.TestCase):
    def one_target(self, dist, face_target=True):
        g = empty_game()
        g.player.x = g.player.z = 0.0
        g.player.aim = 0.0
        d = Dummy("t", 0.0, dist, (255, 0, 0))
        g.dummies.append(d)
        return g, d

    def test_close_shot_applies_full_body_damage(self):
        g, d = self.one_target(8)
        g.update(DT, InputState(fire_down=True, fire_held=True, aim_held=True))
        self.assertAlmostEqual(100.0 - 22.0, d.health.current, places=3)   # AR-09 a ~8 m, corpo, sem queda

    def test_far_shot_damage_is_reduced_by_falloff(self):
        from arsenal_lc.core import DamageModel, HitRegion, WeaponCatalog
        ar = WeaponCatalog.get(WeaponId.AR09Vektor)
        near = DamageModel.compute(ar, 8, HitRegion.Body)
        far = DamageModel.compute(ar, 59.6, HitRegion.Body)
        self.assertLess(far, near)

    def test_tall_wall_blocks_bullets(self):
        w = World([Box("w", 0, 4, 6, 0.4, 3, "wall")], bounds=(-100, 100, -100, 100))
        g = empty_game(w)
        g.player.x = g.player.z = 0.0
        d = Dummy("t", 0.0, 10.0, (255, 0, 0))
        g.dummies.append(d)
        run(g, 1.0, InputState(fire_held=True, aim_held=True))
        self.assertEqual(100.0, d.health.current)

    def test_low_cover_blocks_crouched_shooter_but_not_standing(self):
        def trial(crouched):
            w = World([Box("c", 0, 2, 4, 0.6, 1.1, "cover")], bounds=(-100, 100, -100, 100))
            g = empty_game(w)
            g.player.x = g.player.z = 0.0
            g.player.crouched = crouched
            d = Dummy("t", 0.0, 12.0, (255, 0, 0))
            g.dummies.append(d)
            run(g, 0.5, InputState(fire_held=True, aim_held=True))
            return d.health.current
        self.assertEqual(100.0, trial(True))
        self.assertLess(trial(False), 100.0)

    def test_target_dies_and_respawns(self):
        g, d = self.one_target(6)
        run(g, 3.0, InputState(fire_held=True, aim_held=True))
        self.assertTrue(d.health.is_dead or d.health.current < 100.0)
        d.take_damage(1000.0, g.now)
        self.assertFalse(d.alive)
        run(g, d.respawn_seconds + 0.2)
        self.assertTrue(d.alive)
        self.assertEqual(100.0, d.health.current)

    def test_empty_magazine_auto_reloads(self):
        g = empty_game()
        run(g, 6.0, InputState(fire_held=True))
        self.assertGreater(g.weapon.ammo, 0)

    def test_switch_weapon_cycles(self):
        g = empty_game()
        first = g.weapon.stats.id
        g.update(DT, InputState(switch_down=True))
        self.assertNotEqual(first, g.weapon.stats.id)
        self.assertEqual(WeaponId.PX7Pulse, g.weapon.stats.id)

    def test_shotgun_fires_multiple_pellets(self):
        g = empty_game()
        g.weapon_index = 5
        g.update(DT, InputState(fire_down=True, fire_held=True))
        self.assertEqual(8, len(g.tracers))


class EchoTraceTests(unittest.TestCase):
    def test_standing_still_player_trace_does_not_grow(self):
        g = empty_game()
        run(g, 15.0)
        self.assertEqual(0, g.player.emitter.buffer.count)

    def test_moving_player_leaves_trace(self):
        g = empty_game()
        run(g, 3.0, InputState(move_z=0.5))
        self.assertGreater(g.player.emitter.buffer.count, 5)

    def test_scan_shows_enemy_trail_never_current_position(self):
        g = empty_game()
        bot = Dummy("p", 0, 0, (1, 2, 3), [(5, 0), (5, 30)], 3.2, 5.6, 1)
        g.dummies.append(bot)
        g.player.x, g.player.z = 0.0, 10.0
        run(g, 6.0)
        g.update(DT, InputState(scan_down=True))
        self.assertTrue(g.strands, "o scan deveria achar rastro do patrulheiro")
        newest = max(s.time for st in g.strands for s in st.samples)
        self.assertGreaterEqual(g.now - newest, TraceRules.REVEAL_DELAY - 1e-6)
        for st in g.strands:
            for s in st.samples:
                self.assertGreater(math.hypot(s.x - bot.x, s.z - bot.z), 0.5)

    def test_scan_cooldown_blocks_second_use(self):
        g = empty_game()
        g.update(DT, InputState(scan_down=True))
        self.assertAlmostEqual(TraceRules.SCAN_COOLDOWN, g.scan_cooldown)
        g.update(DT, InputState(scan_down=True))
        self.assertLess(g.scan_cooldown, TraceRules.SCAN_COOLDOWN)       # só desceu 1 frame, não reiniciou
        self.assertTrue(any("RECARREGANDO" in t[0] for t in g.toasts))

    def test_scan_ignores_own_team_unless_debug(self):
        g = empty_game()
        run(g, 6.0, InputState(move_z=0.5))
        g.update(DT, InputState(scan_down=True))
        self.assertEqual([], g.strands)
        g2 = empty_game()
        g2.debug_reveal_all = True
        run(g2, 6.0, InputState(move_z=0.5))
        g2.update(DT, InputState(scan_down=True))
        self.assertTrue(g2.strands)

    def test_decoy_creates_synthetic_trace_visible_in_debug(self):
        g = empty_game()
        g.debug_reveal_all = True
        g.update(DT, InputState(decoy_down=True))
        self.assertEqual(1, g.decoy_charges)
        run(g, 6.0)
        g.update(DT, InputState(scan_down=True))
        self.assertTrue(any(st.synthetic for st in g.strands))

    def test_decoy_charges_and_recharge(self):
        g = empty_game()
        g.update(DT, InputState(decoy_down=True))
        g.update(DT, InputState(decoy_down=True))
        self.assertEqual(0, g.decoy_charges)
        g.update(DT, InputState(decoy_down=True))
        self.assertEqual(0, g.decoy_charges)
        run(g, 15.1)
        self.assertEqual(1, g.decoy_charges)

    def test_decoy_removed_after_lifetime(self):
        g = empty_game()
        g.update(DT, InputState(decoy_down=True))
        run(g, 0.6 + 7 + TraceRules.LIFETIME + 1.5)
        self.assertEqual(0, len(g.decoys))


class PlayerHealthTests(unittest.TestCase):
    def test_damage_then_regen_to_cap_and_respawn(self):
        g = empty_game()
        g.damage_player(25)
        self.assertAlmostEqual(75.0, g.player.health.current)
        g.damage_player(60)
        run(g, 20.0)
        self.assertAlmostEqual(60.0, g.player.health.current, places=1)
        g.damage_player(500)
        self.assertTrue(g.player.health.is_dead)
        run(g, 3.2)
        self.assertFalse(g.player.health.is_dead)
        self.assertEqual(SPAWN_POINT, (g.player.x, g.player.z))


class PatrolTests(unittest.TestCase):
    def test_patrol_moves_along_route_and_leaves_trace(self):
        g = Game()
        run(g, 12.0)
        bots = [d for d in g.dummies if d.route]
        self.assertEqual(3, len(bots))
        for b in bots:
            self.assertGreater(b.emitter.buffer.count, 3)


if __name__ == "__main__":
    unittest.main()
