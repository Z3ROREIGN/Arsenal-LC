"""Entrada: toque (multitoque) e teclado/mouse -> InputState. Pointers: dedos ou mouse."""
import math

import pygame

from ..game.sim import InputState
from .settings import BUTTON_DEFS

MOVE_RADIUS_PX = 70.0
LOOK_DEADZONE_PX = 14.0
DRAG_TO_RADIANS = 0.0055


class InputHub:
    def __init__(self, settings, width, height):
        self.settings = settings
        self.W, self.H = width, height
        self.pointers = {}      # id -> dict(x,y,sx,sy,role,last_x)
        self.touch_mode = False
        self.edit_mode = False
        self.menu = None        # definido pelo main (objeto Menu)
        self.mouse_pos = None
        self.mouse_moved = False
        self.keys_edge = set()
        self._edges = set()     # botões que "desceram" neste frame
        self._aim_delta = 0.0
        self._held = {}         # botão -> contagem de dedos
        self.done_rect = pygame.Rect(width // 2 - 110, 20, 220, 44)

    # ---------- layout ----------
    def button_geometry(self, name):
        x, y = self.settings.position(name)
        base = BUTTON_DEFS[name][3]
        r = base * self.settings.button_scale * (self.H / 540.0)
        return x * self.W, y * self.H, r

    def hit_button(self, x, y):
        best = None
        for name in BUTTON_DEFS:
            cx, cy, r = self.button_geometry(name)
            d = math.hypot(x - cx, y - cy)
            if d <= r * 1.1 and (best is None or d < best[1]):
                best = (name, d)
        return best[0] if best else None

    # ---------- eventos ----------
    def handle_event(self, e):
        t = e.type
        if t == pygame.FINGERDOWN:
            self.touch_mode = True
            self.pointers.pop("mouse", None)
            self._down(("f", e.finger_id), e.x * self.W, e.y * self.H)
        elif t == pygame.FINGERMOTION:
            self._move(("f", e.finger_id), e.x * self.W, e.y * self.H)
        elif t == pygame.FINGERUP:
            self._up(("f", e.finger_id))
        elif t == pygame.MOUSEBUTTONDOWN and not self.touch_mode:
            if getattr(e, "button", 1) == 3:
                self._held["aim"] = self._held.get("aim", 0) + 1
                self.pointers["mouse_rmb"] = {"x": e.pos[0], "y": e.pos[1], "role": "rmb"}
            elif getattr(e, "button", 1) == 1:
                self._down("mouse", e.pos[0], e.pos[1])
        elif t == pygame.MOUSEMOTION and not self.touch_mode:
            self.mouse_pos = e.pos
            self.mouse_moved = True
            self._move("mouse", e.pos[0], e.pos[1])
        elif t == pygame.MOUSEBUTTONUP and not self.touch_mode:
            if getattr(e, "button", 1) == 3:
                if self.pointers.pop("mouse_rmb", None):
                    self._held["aim"] = max(0, self._held.get("aim", 0) - 1)
            elif getattr(e, "button", 1) == 1:
                self._up("mouse")
        elif t == pygame.KEYDOWN:
            k = e.key
            if k == pygame.K_r: self._edges.add("reload")
            elif k == pygame.K_c: self._edges.add("crouch")
            elif k == pygame.K_q: self._edges.add("switch")
            elif k == pygame.K_e: self._edges.add("scan")
            elif k == pygame.K_g: self._edges.add("decoy")
            elif k in (pygame.K_ESCAPE, pygame.K_F1, pygame.K_TAB) and self.menu is not None:
                self.menu.toggle()

    def _down(self, pid, x, y):
        if self.menu is not None and self.menu.open:
            self.menu.handle_tap(x, y)
            return
        if self.edit_mode:
            if self.done_rect.collidepoint(x, y):
                self.edit_mode = False
                self.settings.save()
                return
            name = self.hit_button(x, y)
            if name:
                self.pointers[pid] = {"x": x, "y": y, "role": "edit:" + name}
            return
        name = self.hit_button(x, y)
        if name == "cfg":
            if self.menu is not None:
                self.menu.toggle()
            return
        if name:
            self.pointers[pid] = {"x": x, "y": y, "sx": x, "sy": y, "role": "btn:" + name, "last_x": x}
            self._held[name] = self._held.get(name, 0) + 1
            self._edges.add(name)
            return
        if pid == "mouse":   # desktop: clicar no mapa = atirar e mirar no cursor
            self.pointers[pid] = {"x": x, "y": y, "sx": x, "sy": y, "role": "mouse_fire"}
            self._held["fire"] = self._held.get("fire", 0) + 1
            self._edges.add("fire")
            return
        role = "move" if x < self.W * 0.5 else "look"
        self.pointers[pid] = {"x": x, "y": y, "sx": x, "sy": y, "role": role}

    def _move(self, pid, x, y):
        p = self.pointers.get(pid)
        if not p:
            return
        if p["role"].startswith("edit:"):
            self.settings.set_position(p["role"][5:], x / self.W, y / self.H)
        elif p["role"] == "btn:fire":
            self._aim_delta += (x - p["last_x"]) * DRAG_TO_RADIANS * self.settings.look_sensitivity
            p["last_x"] = x
        p["x"], p["y"] = x, y

    def _up(self, pid):
        p = self.pointers.pop(pid, None)
        if not p:
            return
        role = p["role"]
        if role.startswith("btn:"):
            n = role[4:]
            self._held[n] = max(0, self._held.get(n, 0) - 1)
        elif role == "mouse_fire":
            self._held["fire"] = max(0, self._held.get("fire", 0) - 1)
        elif role.startswith("edit:"):
            self.settings.save()

    # ---------- por quadro ----------
    def poll(self, menu_open=False) -> InputState:
        st = InputState()
        edges, self._edges = self._edges, set()
        aim_delta, self._aim_delta = self._aim_delta, 0.0
        if menu_open or self.edit_mode:
            return st
        mx = mz = 0.0
        for p in self.pointers.values():
            r = p["role"]
            if r == "move":
                dx, dy = p["x"] - p["sx"], p["y"] - p["sy"]
                rad = MOVE_RADIUS_PX * (self.H / 540.0)
                vx, vz = dx / rad, -dy / rad
                m = math.hypot(vx, vz)
                if m > 0.12:
                    if m > 1.0:
                        vx, vz, m = vx / m, vz / m, 1.0
                    mx, mz = vx, vz
            elif r == "look":
                dx, dy = p["x"] - p["sx"], p["y"] - p["sy"]
                if math.hypot(dx, dy) > LOOK_DEADZONE_PX:
                    st.aim_angle = math.atan2(dx, -dy)
            elif r == "mouse_fire":
                st.aim_angle = self._mouse_angle(p["x"], p["y"])
        if not self.touch_mode:
            k = pygame.key.get_pressed()
            kx = (1 if (k[pygame.K_d] or k[pygame.K_RIGHT]) else 0) - (1 if (k[pygame.K_a] or k[pygame.K_LEFT]) else 0)
            kz = (1 if (k[pygame.K_w] or k[pygame.K_UP]) else 0) - (1 if (k[pygame.K_s] or k[pygame.K_DOWN]) else 0)
            if kx or kz:
                n = math.hypot(kx, kz)
                mx, mz = kx / n, kz / n
            st.sprint_held = bool(k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT])
            if st.aim_angle is None and self.mouse_moved and self.mouse_pos:
                st.aim_angle = self._mouse_angle(*self.mouse_pos)
        st.move_x, st.move_z = mx, mz
        st.aim_delta = aim_delta
        st.fire_held = self._held.get("fire", 0) > 0
        st.fire_down = "fire" in edges
        st.aim_held = self._held.get("aim", 0) > 0
        st.reload_down = "reload" in edges
        st.crouch_down = "crouch" in edges
        st.switch_down = "switch" in edges
        st.scan_down = "scan" in edges
        st.decoy_down = "decoy" in edges
        return st

    def _mouse_angle(self, x, y):
        return math.atan2(x - self.W / 2.0, -(y - self.H / 2.0))

    def stick_visuals(self):
        """[(origem, ponteiro, é_movimento)] para desenhar os joysticks flutuantes."""
        out = []
        for p in self.pointers.values():
            if p["role"] in ("move", "look"):
                out.append(((p["sx"], p["sy"]), (p["x"], p["y"]), p["role"] == "move"))
        return out
