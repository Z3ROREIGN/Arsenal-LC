"""Desenho 2D (vista de cima, câmera seguindo o jogador)."""
import math

import pygame

from ..core import TraceRules
from .settings import BUTTON_DEFS

PPM = 12.0   # pixels por metro
BG = (20, 22, 28)
FLOOR = (44, 48, 57)
GRID = (58, 63, 74)
KIND_COLORS = {"wall": (86, 94, 110), "cover": (150, 112, 66), "platform": (58, 96, 124),
               "step": (84, 130, 160), "line": (230, 205, 50)}
CYAN = (64, 230, 255)
MAGENTA = (255, 77, 230)


def _mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


class Renderer:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.W, self.H = width, height
        self.font = pygame.font.Font(None, 34)
        self.small = pygame.font.Font(None, 24)
        self.tiny = pygame.font.Font(None, 20)
        self.cam = (0.0, 0.0)

    def w2s(self, x, z):
        return (self.W / 2.0 + (x - self.cam[0]) * PPM, self.H / 2.0 - (z - self.cam[1]) * PPM)

    def _rect(self, b):
        x0, y0 = self.w2s(b.x0, b.z1)
        return pygame.Rect(int(x0), int(y0), max(1, int(b.sx * PPM)), max(1, int(b.sz * PPM)))

    # ---------- quadro completo ----------
    def draw(self, game, hub, menu, fps):
        scr = self.screen
        p = game.player
        self.cam = (p.x, p.z)
        scr.fill(BG)
        self._draw_floor(game)
        self._draw_boxes(game)
        self._draw_strands(game)
        self._draw_decoys(game)
        self._draw_dummies(game)
        self._draw_player(game)
        self._draw_tracers(game)
        self._draw_floaters(game)
        self._draw_hud(game, fps)
        self._draw_controls(game, hub)
        if hub.edit_mode:
            self._draw_edit_banner(hub)
        if p.health.is_dead:
            t = self.font.render("VOCÊ CAIU - RENASCENDO...", True, (255, 120, 120))
            scr.blit(t, (self.W // 2 - t.get_width() // 2, self.H // 2 - 80))
        menu.draw(scr, self.font, self.small)

    # ---------- mundo ----------
    def _draw_floor(self, game):
        x0, x1, z0, z1 = game.world.bounds
        a = self.w2s(x0, z1)
        b = self.w2s(x1, z0)
        pygame.draw.rect(self.screen, FLOOR, pygame.Rect(int(a[0]), int(a[1]), int(b[0] - a[0]), int(b[1] - a[1])))
        gx = int(math.ceil(x0 / 5.0)) * 5
        while gx <= x1:
            sx = self.w2s(gx, 0)[0]
            if 0 <= sx <= self.W:
                pygame.draw.line(self.screen, GRID, (sx, max(0, a[1])), (sx, min(self.H, b[1])))
            gx += 5
        gz = int(math.ceil(z0 / 5.0)) * 5
        while gz <= z1:
            sy = self.w2s(0, gz)[1]
            if 0 <= sy <= self.H:
                pygame.draw.line(self.screen, GRID, (max(0, a[0]), sy), (min(self.W, b[0]), sy))
            gz += 5

    def _draw_boxes(self, game):
        order = {"platform": 0, "step": 1, "line": 2, "cover": 3, "wall": 4}
        for b in sorted(game.world.boxes, key=lambda b: order.get(b.kind, 3)):
            r = self._rect(b)
            if r.right < 0 or r.left > self.W or r.bottom < 0 or r.top > self.H:
                continue
            col = KIND_COLORS.get(b.kind, (120, 120, 120))
            if b.kind == "step":
                col = _mix(col, (255, 255, 255), b.h / 6.0)
            pygame.draw.rect(self.screen, col, r)
            if b.kind in ("wall", "cover"):
                pygame.draw.rect(self.screen, _mix(col, (255, 255, 255), 0.35), r, 1)

    def _draw_strands(self, game):
        if game.scan_active > 0.0:
            c = self.w2s(game.player.x, game.player.z)
            pygame.draw.circle(self.screen, _mix(FLOOR, CYAN, 0.35), (int(c[0]), int(c[1])),
                               int(TraceRules.SCAN_RADIUS * PPM), 1)
        if not game.strands:
            return
        now = game.now
        for st in game.strands:
            base = MAGENTA if (game.debug_reveal_all and st.synthetic) else CYAN
            pts = [self.w2s(s.x, s.z) for s in st.samples]
            for i in range(len(pts) - 1):
                age = now - st.samples[i].time
                alpha = 0.9 - 0.8 * min(1.0, age / TraceRules.LIFETIME)
                col = _mix(FLOOR, base, alpha)
                width = 2 + int(round(st.samples[i].intensity * 2))
                pygame.draw.line(self.screen, col, pts[i], pts[i + 1], width)
                if i % 3 == 1:   # seta de direção
                    dx, dy = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
                    n = math.hypot(dx, dy) or 1.0
                    ux, uy = dx / n, dy / n
                    mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
                    tip = (mx + ux * 5, my + uy * 5)
                    l = (mx - ux * 3 - uy * 4, my - uy * 3 + ux * 4)
                    r = (mx - ux * 3 + uy * 4, my - uy * 3 - ux * 4)
                    pygame.draw.polygon(self.screen, col, (tip, l, r))

    def _draw_decoys(self, game):
        t = game.now
        for d in game.decoys:
            x, y = self.w2s(d.x, d.z)
            pulse = 0.5 + 0.5 * abs(math.sin(t * 6))
            pygame.draw.rect(self.screen, _mix((20, 80, 100), CYAN, pulse), pygame.Rect(int(x) - 4, int(y) - 4, 8, 8))
        if game.scan_ring_t <= 0.6:
            c = self.w2s(game.player.x, game.player.z)
            rad = int(TraceRules.SCAN_RADIUS * PPM * (game.scan_ring_t / 0.6))
            if rad > 2:
                pygame.draw.circle(self.screen, CYAN, (int(c[0]), int(c[1])), rad, 3)

    def _draw_dummies(self, game):
        for d in game.dummies:
            x, y = self.w2s(d.x, d.z)
            if x < -20 or x > self.W + 20 or y < -20 or y > self.H + 20:
                continue
            if not d.alive:
                pygame.draw.line(self.screen, (120, 120, 120), (x - 6, y - 6), (x + 6, y + 6), 2)
                pygame.draw.line(self.screen, (120, 120, 120), (x - 6, y + 6), (x + 6, y - 6), 2)
                continue
            col = (255, 255, 255) if game.now < d.flash_until else d.color
            pygame.draw.circle(self.screen, col, (int(x), int(y)), 8)
            fx, fy = math.sin(d.facing), -math.cos(d.facing)
            pygame.draw.line(self.screen, (20, 20, 20), (x, y), (x + fx * 11, y + fy * 11), 3)
            pygame.draw.circle(self.screen, _mix(col, (255, 255, 255), 0.5), (int(x + fx * 3), int(y + fy * 3)), 3)
            if d.health.current < d.health.max:
                w = 22
                pygame.draw.rect(self.screen, (60, 20, 20), (x - w / 2, y - 16, w, 4))
                pygame.draw.rect(self.screen, (80, 220, 90), (x - w / 2, y - 16, w * d.health.current / d.health.max, 4))

    def _draw_player(self, game):
        p = game.player
        x, y = self.w2s(p.x, p.z)
        if p.health.is_dead:
            return
        ax, ay = math.sin(p.aim), -math.cos(p.aim)
        st = game.weapon
        spread = st.current_spread_degrees(p.aiming, p.speed_factor, p.crouched)
        L = 14 * PPM if p.aiming else 8 * PPM
        for sgn in (-1, 1):
            a = p.aim + sgn * math.radians(spread)
            pygame.draw.line(self.screen, (120, 130, 150), (x, y), (x + math.sin(a) * L, y - math.cos(a) * L), 1)
        if p.aiming:
            pygame.draw.line(self.screen, (255, 80, 80), (x, y), (x + ax * L, y + ay * L), 1)
        r = 6 if p.crouched else 8
        col = (60, 140, 220) if p.crouched else (80, 170, 255)
        pygame.draw.circle(self.screen, col, (int(x), int(y)), r)
        pygame.draw.line(self.screen, (230, 230, 230), (x, y), (x + ax * 14, y + ay * 14), 3)
        if p.sprinting:
            pygame.draw.circle(self.screen, (255, 255, 255), (int(x), int(y)), r + 3, 1)

    def _draw_tracers(self, game):
        for x0, z0, x1, z1, born in game.tracers:
            a, b = self.w2s(x0, z0), self.w2s(x1, z1)
            pygame.draw.line(self.screen, (255, 235, 140), a, b, 1)

    def _draw_floaters(self, game):
        for f in game.floaters:
            age = game.now - f["born"]
            x, y = self.w2s(f["x"], f["z"])
            t = self.small.render(f["text"], True, f["color"])
            self.screen.blit(t, (x - t.get_width() / 2, y - 22 - age * 40))

    # ---------- HUD ----------
    def _draw_hud(self, game, fps):
        scr, p = self.screen, game.player
        # vida
        w = 220
        pygame.draw.rect(scr, (50, 20, 20), (16, 16, w, 18), border_radius=4)
        frac = p.health.current / p.health.max
        pygame.draw.rect(scr, (90, 220, 110) if frac > 0.4 else (230, 90, 70), (16, 16, w * frac, 18), border_radius=4)
        cap_x = 16 + w * p.health.regen_cap_fraction
        pygame.draw.line(scr, (255, 255, 255), (cap_x, 14), (cap_x, 36), 1)   # teto da regeneração
        scr.blit(self.small.render("VIDA %d" % round(p.health.current), True, (240, 240, 240)), (20, 17))
        # arma / munição
        st = game.weapon
        ammo = "RECARREGANDO" if st.is_reloading else "%d / %d" % (st.ammo, st.stats.magazine_size)
        scr.blit(self.font.render(st.stats.display_name, True, (255, 255, 255)), (16, 42))
        scr.blit(self.font.render(ammo, True, (255, 220, 120) if not st.is_reloading else (255, 140, 100)), (16, 68))
        if st.is_reloading:
            pygame.draw.rect(scr, (90, 60, 40), (16, 96, 160, 6))
            pygame.draw.rect(scr, (255, 170, 80), (16, 96, 160 * st.reload_progress, 6))
        scr.blit(self.tiny.render("ABATES %d" % game.kills, True, (200, 210, 225)), (16, 108))
        # FPS
        scr.blit(self.tiny.render("FPS %d" % round(fps), True, (200, 210, 225)), (self.W - 120, 12))
        # avisos
        for i, (text, _) in enumerate(game.toasts):
            t = self.font.render(text, True, (255, 255, 255))
            scr.blit(t, (self.W // 2 - t.get_width() // 2, 70 + i * 32))

    # ---------- controles de toque ----------
    def _draw_controls(self, game, hub):
        scr = self.screen
        for origin, cur, is_move in hub.stick_visuals():
            rad = int(70 * hub.H / 540.0)
            col = (200, 220, 255) if is_move else (255, 210, 160)
            pygame.draw.circle(scr, col, (int(origin[0]), int(origin[1])), rad, 2)
            pygm = (cur[0] - origin[0], cur[1] - origin[1])
            n = math.hypot(*pygm)
            if n > rad:
                pygm = (pygm[0] / n * rad, pygm[1] / n * rad)
            pygame.draw.circle(scr, col, (int(origin[0] + pygm[0]), int(origin[1] + pygm[1])), 14)
        for name, (label, _, _, _) in BUTTON_DEFS.items():
            cx, cy, r = hub.button_geometry(name)
            held = hub._held.get(name, 0) > 0
            base = (255, 90, 80) if name == "fire" else (70, 90, 120)
            if name == "scan" and game.scan_cooldown > 0:
                base = (50, 60, 76)
            if name == "decoy" and game.decoy_charges == 0:
                base = (50, 60, 76)
            col = _mix(base, (255, 255, 255), 0.35 if held else 0.0)
            pygame.draw.circle(scr, col, (int(cx), int(cy)), int(r))
            pygame.draw.circle(scr, (220, 230, 245), (int(cx), int(cy)), int(r), 2)
            text = label
            if name == "scan" and game.scan_cooldown > 0:
                text = "%ds" % math.ceil(game.scan_cooldown)
            if name == "decoy":
                text = "FALSO x%d" % game.decoy_charges
            if name == "crouch" and game.player.crouched:
                text = "AGACHADO"
            f = self.tiny if r < 45 else self.small
            t = f.render(text, True, (255, 255, 255))
            scr.blit(t, (cx - t.get_width() / 2, cy - t.get_height() / 2))
            if name == "scan" and game.scan_active > 0:
                pygame.draw.circle(scr, CYAN, (int(cx), int(cy)), int(r) + 4, 3)

    def _draw_edit_banner(self, hub):
        pygame.draw.rect(self.screen, (40, 120, 60), hub.done_rect, border_radius=8)
        t = self.small.render("CONCLUIR EDIÇÃO", True, (255, 255, 255))
        self.screen.blit(t, (hub.done_rect.centerx - t.get_width() // 2, hub.done_rect.centery - t.get_height() // 2))
        h = self.tiny.render("Arraste os botões para onde preferir", True, (230, 240, 255))
        self.screen.blit(h, (self.W // 2 - h.get_width() // 2, 72))
