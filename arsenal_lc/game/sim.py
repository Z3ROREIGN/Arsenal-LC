"""Simulação do protótipo: jogador, armas, alvos, ECHO SCAN e rastro falso. Sem pygame."""
import math
from dataclasses import dataclass
from typing import List, Optional

from ..core import (DamageModel, FireResult, HealthModel, HitRegion, TraceRules, TraceScanner,
                    WeaponCatalog, WeaponId, WeaponState)
from .entities import DUMMY_RADIUS, Decoy, Dummy, Emitter
from .world import SPAWN_POINT, World, build_test_map, ray_circle

PLAYER_RADIUS = 0.35
WALK_SPEED, SPRINT_SPEED, CROUCH_SPEED, AIM_SPEED_FACTOR = 4.2, 6.6, 2.3, 0.6
EYE_STAND, EYE_CROUCH = 1.55, 1.05      # altura do olho (decide se o tiro passa por cima de cobertura baixa)
AIM_HEIGHT_HIP, AIM_HEIGHT_ADS = 1.10, 1.25
HEAD_MIN, LIMB_MAX, TARGET_MAX_H = 1.45, 0.75, 1.9
PLAYER_RESPAWN_SECONDS = 3.0


@dataclass
class InputState:
    move_x: float = 0.0           # -1..1 (leste positivo)
    move_z: float = 0.0           # -1..1 (norte positivo)
    aim_angle: Optional[float] = None   # radianos a partir de +Z (norte), sentido horário; None = manter
    aim_delta: float = 0.0        # rotação relativa (arrastar no botão de tiro)
    fire_held: bool = False
    fire_down: bool = False
    aim_held: bool = False
    sprint_held: bool = False
    reload_down: bool = False
    crouch_down: bool = False
    switch_down: bool = False
    scan_down: bool = False
    decoy_down: bool = False


class Player:
    def __init__(self):
        self.x, self.z = SPAWN_POINT
        self.aim = 0.0
        self.team_id = 0
        self.health = HealthModel(100.0, 6.0, 6.0, 0.6)
        self.emitter = Emitter(0, 0)
        self.crouched = self.sprinting = self.aiming = False
        self.speed_factor = 0.0
        self.dead_until = 0.0
        self.recoil_vis = 0.0   # só visual (tremor/mira abrindo)


class Game:
    def __init__(self, seed: int = 1, world: Optional[World] = None, with_targets: bool = True):
        self.world = world or build_test_map()
        self.now = 0.0
        self.player = Player()
        order = [WeaponId.AR09Vektor, WeaponId.PX7Pulse, WeaponId.SM4Phantom,
                 WeaponId.BR21Titan, WeaponId.SR8Spectre, WeaponId.SG12Breach]
        self.slots = [WeaponState(WeaponCatalog.get(w), 101 + i * 101 + seed) for i, w in enumerate(order)]
        self.weapon_index = 0
        self.dummies: List[Dummy] = []
        self.decoys: List[Decoy] = []
        # ECHO SCAN
        self.scan_cooldown = 0.0
        self.scan_active = 0.0
        self.scan_ring_t = 99.0
        self.strands = []
        self._next_scan_refresh = 0.0
        self.debug_reveal_all = False
        # ECHO fake
        self.decoy_charges = 2
        self.decoy_max = 2
        self.decoy_recharge = 0.0
        self._decoy_counter = 0
        # efeitos para a camada visual
        self.tracers = []      # [x0, z0, x1, z1, nascimento]
        self.floaters = []     # dict(x,z,text,color,born)
        self.toasts = []       # (texto, expira)
        self.kills = 0
        if with_targets:
            self._build_targets()

    # ---------- construção ----------
    def _build_targets(self):
        for z in (-26, -19, -9, 6, 26):
            self.dummies.append(Dummy("Alvo_%dm" % (z + 34), 14.0, float(z), (230, 90, 64)))
        self.dummies.append(Dummy("Patrulheiro_Sala", 0, 0, (217, 179, 51),
                                  [(-21, -9), (-21, 5), (-10, 5), (-10, -9)], 3.2, 5.6, 1))
        self.dummies.append(Dummy("Patrulheiro_Patio", 0, 0, (179, 77, 217),
                                  [(-6, -18), (8, -18), (8, 22), (-6, 22)], 3.2, 5.6, 2))
        self.dummies.append(Dummy("Patrulheiro_Norte", 0, 0, (77, 204, 179),
                                  [(-6, 34), (24, 34), (24, 40), (-6, 40)], 3.2, 5.6, 3))

    # ---------- utilidades ----------
    @property
    def weapon(self) -> WeaponState:
        return self.slots[self.weapon_index]

    def toast(self, text: str, seconds: float = 1.6):
        self.toasts.append((text, self.now + seconds))

    def all_buffers(self):
        bufs = [self.player.emitter.buffer]
        for d in self.dummies:
            if d.emitter:
                bufs.append(d.emitter.buffer)
        for dc in self.decoys:
            if dc.buffer is not None:
                bufs.append(dc.buffer)
        return bufs

    @staticmethod
    def _dir(angle: float):
        return math.sin(angle), math.cos(angle)

    # ---------- atualização ----------
    def update(self, dt: float, inp: InputState):
        self.now += dt
        p = self.player
        dead = p.health.is_dead
        if dead:
            if self.now >= p.dead_until:
                self._respawn_player()
            inp = InputState()
        p.health.tick(dt)

        # mira
        if inp.aim_angle is not None:
            p.aim = inp.aim_angle
        p.aim += inp.aim_delta
        if inp.crouch_down:
            p.crouched = not p.crouched

        # movimento
        mag = min(1.0, math.hypot(inp.move_x, inp.move_z))
        p.aiming = inp.aim_held
        firing = inp.fire_held
        p.sprinting = (not p.crouched and not p.aiming and not firing and mag > 0.2
                       and (inp.sprint_held or mag >= 0.95))
        speed = CROUCH_SPEED if p.crouched else (SPRINT_SPEED if p.sprinting else WALK_SPEED)
        if p.aiming:
            speed *= AIM_SPEED_FACTOR
        if mag > 1e-4:
            ux, uz = inp.move_x / max(1e-9, math.hypot(inp.move_x, inp.move_z)), inp.move_z / max(1e-9, math.hypot(inp.move_x, inp.move_z))
            vx, vz = ux * speed * mag, uz * speed * mag
        else:
            vx = vz = 0.0
        p.x, p.z = self.world.move_circle(p.x, p.z, vx * dt, vz * dt, PLAYER_RADIUS)
        p.speed_factor = min(1.0, math.hypot(vx, vz) / SPRINT_SPEED)
        p.emitter.crouched, p.emitter.sprinting = p.crouched, p.sprinting
        p.emitter.update(self.now, p.x, p.z)
        p.recoil_vis = max(0.0, p.recoil_vis - 6.0 * dt)

        # arma
        st = self.weapon
        st.tick(dt, self.now)
        if not dead:
            if inp.switch_down:
                st.cancel_reload()
                self.weapon_index = (self.weapon_index + 1) % len(self.slots)
                st = self.weapon
            if inp.reload_down:
                st.start_reload(self.now)
            wants = inp.fire_held if st.stats.automatic else inp.fire_down
            if wants and not p.sprinting:
                self._shoot()

        # dispositivos
        self._update_scanner(dt, inp.scan_down and not dead)
        self._update_decoys(dt, inp.decoy_down and not dead)

        # alvos
        for d in self.dummies:
            d.update(dt, self.now)

        # limpeza de efeitos
        self.tracers = [t for t in self.tracers if self.now - t[4] < 0.08]
        self.floaters = [f for f in self.floaters if self.now - f["born"] < 0.9]
        self.toasts = [t for t in self.toasts if t[1] > self.now][-3:]

    def _respawn_player(self):
        p = self.player
        p.health.revive()
        p.x, p.z = SPAWN_POINT
        p.aim = 0.0
        p.emitter.reset()

    def damage_player(self, amount: float):
        p = self.player
        p.health.apply_damage(amount)
        if p.health.is_dead:
            p.dead_until = self.now + PLAYER_RESPAWN_SECONDS
            self.toast("VOCÊ CAIU - RENASCENDO")

    # ---------- tiro ----------
    def _shoot(self):
        p, st = self.player, self.weapon
        spread = st.current_spread_degrees(p.aiming, p.speed_factor, p.crouched)  # antes do disparo somar dispersão
        res, kick_pitch, kick_yaw = st.try_fire(self.now)
        if res == FireResult.EmptyMagazine:
            st.start_reload(self.now)
            return
        if res != FireResult.Fired:
            return
        p.aim += math.radians(kick_yaw)
        p.recoil_vis = min(3.0, p.recoil_vis + kick_pitch)
        ox, oz = p.x, p.z
        eye = EYE_CROUCH if p.crouched else EYE_STAND
        aim_h = AIM_HEIGHT_ADS if p.aiming else AIM_HEIGHT_HIP
        per_target = {}
        for _ in range(st.stats.pellets):
            yaw_deg, pitch_deg = st.sample_spread_offset(spread)
            ang = p.aim + math.radians(yaw_deg)
            dx, dz = self._dir(ang)
            self._fire_ray(ox, oz, dx, dz, math.tan(math.radians(pitch_deg)), eye, aim_h, st.stats, per_target)
        for dummy, (amount, region, dist, killed) in per_target.items():
            color = (255, 230, 60) if region == HitRegion.Head else ((255, 255, 255) if region == HitRegion.Body else (255, 160, 80))
            self.floaters.append({"x": dummy.x, "z": dummy.z, "text": "%d (%dm)" % (round(amount), round(dist)),
                                  "color": color, "born": self.now})
            if killed:
                self.kills += 1
                self.toast("ABATE")

    def _fire_ray(self, ox, oz, dx, dz, slope, eye, aim_h, stats, per_target):
        max_t = stats.max_range
        # alvo mais próximo cuja altura de impacto esteja dentro do corpo
        best = None
        for d in self.dummies:
            if not d.alive:
                continue
            t = ray_circle(ox, oz, dx, dz, d.x, d.z, DUMMY_RADIUS)
            if t is None or t > max_t:
                continue
            h_target = aim_h + t * slope
            if h_target < 0.0 or h_target > TARGET_MAX_H:
                continue  # a bala passa por cima/por baixo
            if best is None or t < best[0]:
                best = (t, d, h_target)

        t_target = best[0] if best else max_t
        end_t = t_target
        blocked = False
        for t_wall, box in self.world.raycast(ox, oz, dx, dz, t_target):
            if box.h > 1.2:
                blocked, end_t = True, t_wall
                break
            # cobertura baixa: a bala só passa se estiver acima dela naquele ponto
            if best:
                h_bullet = eye + (best[2] - eye) * (t_wall / max(t_target, 1e-6))
            else:
                h_bullet = eye + t_wall * slope
            if h_bullet < box.h:
                blocked, end_t = True, t_wall
                break

        self.tracers.append([ox + dx * 0.5, oz + dz * 0.5, ox + dx * end_t, oz + dz * end_t, self.now])
        if blocked or not best:
            return
        t, dummy, h = best
        region = HitRegion.Head if h > HEAD_MIN else (HitRegion.Limb if h < LIMB_MAX else HitRegion.Body)
        dmg = DamageModel.compute(stats, t, region)
        if dmg <= 0.0:
            return
        killed = dummy.take_damage(dmg, self.now)
        prev = per_target.get(dummy)
        if prev is None:
            per_target[dummy] = (dmg, region, t, killed)
        else:
            best_region = region if region == HitRegion.Head else prev[1]
            per_target[dummy] = (prev[0] + dmg, best_region, t, prev[3] or killed)

    # ---------- ECHO SCAN ----------
    def _update_scanner(self, dt: float, pressed: bool):
        if self.scan_cooldown > 0.0:
            self.scan_cooldown = max(0.0, self.scan_cooldown - dt)
        if pressed:
            if self.scan_active > 0.0 or self.scan_cooldown > 0.0:
                self.toast("SCANNER RECARREGANDO")
            else:
                self.scan_active = TraceRules.SCAN_DURATION
                self.scan_cooldown = TraceRules.SCAN_COOLDOWN
                self.scan_ring_t = 0.0
                self._refresh_scan()
                self._next_scan_refresh = self.now + 0.1
                n = len(self.strands)
                self.toast("ECHO SCAN: %d RASTRO(S)" % n if n else "ECHO SCAN: NENHUM RASTRO RECENTE")
        if self.scan_active > 0.0:
            self.scan_active -= dt
            if self.now >= self._next_scan_refresh:
                self._refresh_scan()
                self._next_scan_refresh = self.now + 0.1
            if self.scan_active <= 0.0:
                self.strands = []
        if self.scan_ring_t <= 0.6:
            self.scan_ring_t += dt

    def _refresh_scan(self):
        p = self.player
        ignore = -1 if self.debug_reveal_all else 0
        self.strands = TraceScanner.scan(self.all_buffers(), self.now, p.x, p.z, TraceRules.SCAN_RADIUS, ignore)

    @property
    def scan_cooldown_fraction(self) -> float:
        return min(1.0, self.scan_cooldown / TraceRules.SCAN_COOLDOWN)

    # ---------- rastro falso ----------
    def _update_decoys(self, dt: float, pressed: bool):
        if self.decoy_charges < self.decoy_max:
            self.decoy_recharge += dt
            if self.decoy_recharge >= 15.0:
                self.decoy_charges += 1
                self.decoy_recharge = 0.0
        else:
            self.decoy_recharge = 0.0
        if pressed:
            self._deploy_decoy()
        for dc in self.decoys:
            dc.update(self.now, self.world)
        self.decoys = [d for d in self.decoys if not d.finished]

    def _deploy_decoy(self):
        if self.decoy_charges <= 0:
            self.toast("SEM CARGAS DE RASTRO FALSO")
            return
        p = self.player
        dx, dz = self._dir(p.aim)
        throw = 18.0
        hits = self.world.raycast(p.x, p.z, dx, dz, throw)
        t = max(0.0, hits[0][0] - 0.4) if hits else throw
        x, z = p.x + dx * t, p.z + dz * t
        heading = p.aim + (self._decoy_rand() - 0.5) * 0.8
        self.decoys.append(Decoy(x, z, -(100 + self._decoy_counter), 0, heading, 5.2, 7.0, 0.6, self.now))
        self._decoy_counter += 1
        self.decoy_charges -= 1
        self.decoy_recharge = 0.0
        self.toast("RASTRO FALSO ATIVO")

    def _decoy_rand(self) -> float:
        # pseudo-aleatório determinístico simples (mantém testes reprodutíveis)
        v = math.sin(self._decoy_counter * 12.9898 + 78.233) * 43758.5453
        return v - math.floor(v)
