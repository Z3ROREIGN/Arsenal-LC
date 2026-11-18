"""Mapa 2D (vista de cima). Coordenadas em metros: x = leste, z = norte (mesma convenção do Unity)."""
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

SPAWN_POINT = (0.0, -38.0)


@dataclass(frozen=True)
class Box:
    name: str
    cx: float
    cz: float
    sx: float
    sz: float
    h: float          # altura em metros (cobertura baixa <= 1.2 pode ser vencida por tiro de pé)
    kind: str         # wall | cover | platform | step | line

    @property
    def solid(self) -> bool:
        return self.kind in ("wall", "cover")

    @property
    def x0(self): return self.cx - self.sx / 2.0
    @property
    def x1(self): return self.cx + self.sx / 2.0
    @property
    def z0(self): return self.cz - self.sz / 2.0
    @property
    def z1(self): return self.cz + self.sz / 2.0


def ray_aabb(ox, oz, dx, dz, b: Box) -> Optional[float]:
    """Distância t (direção normalizada) onde o raio entra na caixa, ou None."""
    tmin, tmax = -math.inf, math.inf
    for o, d, lo, hi in ((ox, dx, b.x0, b.x1), (oz, dz, b.z0, b.z1)):
        if abs(d) < 1e-9:
            if o < lo or o > hi:
                return None
        else:
            t1, t2 = (lo - o) / d, (hi - o) / d
            if t1 > t2:
                t1, t2 = t2, t1
            tmin, tmax = max(tmin, t1), min(tmax, t2)
            if tmin > tmax:
                return None
    if tmax < 0.0:
        return None
    return max(tmin, 0.0)


def ray_circle(ox, oz, dx, dz, cx, cz, r) -> Optional[float]:
    fx, fz = ox - cx, oz - cz
    b = fx * dx + fz * dz
    c = fx * fx + fz * fz - r * r
    disc = b * b - c
    if disc < 0.0:
        return None
    s = math.sqrt(disc)
    t = -b - s
    if t < 0.0:
        t = -b + s
    return t if t >= 0.0 else None


class World:
    def __init__(self, boxes: List[Box], bounds=(-30.0, 30.0, -46.0, 46.0)):
        self.boxes = boxes
        self.solids = [b for b in boxes if b.solid]
        self.bounds = bounds  # x0, x1, z0, z1

    def move_circle(self, x, z, dx, dz, r) -> Tuple[float, float]:
        x += dx
        z += dz
        for _ in range(2):
            for b in self.solids:
                cx = min(max(x, b.x0), b.x1)
                cz = min(max(z, b.z0), b.z1)
                ddx, ddz = x - cx, z - cz
                d2 = ddx * ddx + ddz * ddz
                if d2 >= r * r:
                    continue
                if d2 > 1e-12:
                    d = math.sqrt(d2)
                    push = r - d
                    x += ddx / d * push
                    z += ddz / d * push
                else:  # centro dentro da caixa: empurra pelo lado mais raso
                    opts = [(x - b.x0, -1, 0), (b.x1 - x, 1, 0), (z - b.z0, 0, -1), (b.z1 - z, 0, 1)]
                    pen, nx, nz = min(opts, key=lambda o: o[0])
                    x += nx * (pen + r)
                    z += nz * (pen + r)
        x0, x1, z0, z1 = self.bounds
        return min(max(x, x0 + r), x1 - r), min(max(z, z0 + r), z1 - r)

    def raycast(self, ox, oz, dx, dz, max_t) -> List[Tuple[float, Box]]:
        """Caixas sólidas atingidas pelo raio (ordenadas por distância), até max_t."""
        hits = []
        for b in self.solids:
            t = ray_aabb(ox, oz, dx, dz, b)
            if t is not None and t <= max_t:
                hits.append((t, b))
        hits.sort(key=lambda h: h[0])
        return hits

    def blocked_ahead(self, x, z, heading_rad, dist) -> bool:
        dx, dz = math.sin(heading_rad), math.cos(heading_rad)
        return bool(self.raycast(x, z, dx, dz, dist))


def _wall_x(name, z, x0, x1, h, t):   # parede ao longo de X, em z fixo
    return Box(name, (x0 + x1) / 2.0, z, x1 - x0, t, h, "wall")


def _wall_z(name, x, z0, z1, h, t):   # parede ao longo de Z, em x fixo
    return Box(name, x, (z0 + z1) / 2.0, t, z1 - z0, h, "wall")


def _box(name, cx, cz, sx, h, sz, kind="cover"):
    return Box(name, cx, cz, sx, sz, h, kind)


def build_test_map() -> World:
    """Mesmo mapa de teste do protótipo Unity (60 x 92 m)."""
    B = []
    # Perímetro
    B += [_box("Muro_N", 0, 46.5, 62, 5, 1, "wall"), _box("Muro_S", 0, -46.5, 62, 5, 1, "wall"),
          _box("Muro_O", -30.5, 0, 1, 5, 94, "wall"), _box("Muro_L", 30.5, 0, 1, 5, 94, "wall")]
    # Coberturas perto do spawn (baixas: agache atrás delas)
    B += [_box("Cobertura_1", -5, -30, 4, 1.1, 0.6), _box("Cobertura_2", 5, -28, 4, 1.1, 0.6),
          _box("Caixa_1", 0, -24, 1.6, 1.6, 1.6)]
    # Pista de tiro (x = 14), linha de tiro em z = -34
    B += [_wall_z("Pista_O", 10.5, -36, 28, 2.5, 0.4), _wall_z("Pista_L", 17.5, -36, 28, 2.5, 0.4),
          _wall_x("Pista_Fundo", 30, 10.5, 17.5, 3, 0.4),
          _box("Linha_de_Tiro", 14, -34, 5, 0.04, 2, "line")]
    # Sala estilo laboratório (x -24..-8, z -12..8) com portas de 3 m
    B += [_wall_z("Sala_O", -24, -12, 8, 4, 0.6),
          _wall_x("Sala_S1", -12, -24, -18.5, 4, 0.6), _wall_x("Sala_S2", -12, -15.5, -8, 4, 0.6),
          _wall_x("Sala_N1", 8, -24, -13, 4, 0.6), _wall_x("Sala_N2", 8, -10, -8, 4, 0.6),
          _wall_z("Sala_L1", -8, -12, -4, 4, 0.6), _wall_z("Sala_L2", -8, -1, 8, 4, 0.6),
          _box("Sala_Pilar", -16, -2, 1.2, 4, 1.2, "wall"),
          _box("Sala_Cobertura_1", -18, 3, 3, 1.1, 0.6), _box("Sala_Cobertura_2", -12, -6, 3, 1.1, 0.6)]
    # Plataforma (decorativa em 2D: sem altura) com escada de 6 degraus
    B += [_box("Plataforma", 0, 10, 10, 2.4, 8, "platform")]
    for k in range(1, 7):
        B.append(_box("Degrau_%d" % k, 0, 5.6 - 0.8 * (6 - k), 3, 0.4 * k, 0.8, "step"))
    B.append(_box("Plataforma_Cobertura", 2, 12, 2, 1.1, 0.5))
    # Caixas espalhadas
    B += [_box("Caixa_2", 4, -6, 1.6, 1.6, 1.6), _box("Caixa_3", -4, 18, 1.6, 1.6, 1.6),
          _box("Caixa_4", 6, 20, 1.6, 1.6, 1.6)]
    return World(B)
