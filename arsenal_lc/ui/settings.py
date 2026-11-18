"""Configurações do jogador (tamanho/posição dos botões, sensibilidade). Sem pygame."""
import json
import os

# nome -> (rótulo, centro x, centro y (0..1 da tela), raio base em px numa tela de 540 px de altura)
BUTTON_DEFS = {
    "fire":   ("TIRO",      0.88, 0.70, 62),
    "aim":    ("MIRA",      0.73, 0.85, 40),
    "reload": ("RECARGA",   0.74, 0.62, 34),
    "crouch": ("AGACHAR",   0.96, 0.44, 32),
    "switch": ("TROCAR",    0.85, 0.44, 32),
    "scan":   ("ECHO SCAN", 0.61, 0.85, 40),
    "decoy":  ("FALSO",     0.60, 0.66, 34),
    "cfg":    ("CFG",       0.95, 0.07, 26),
}
SETTINGS_FILE = "arsenal_lc_settings.json"


class Settings:
    def __init__(self, path: str = SETTINGS_FILE):
        self.path = path
        self.button_scale = 1.0
        self.look_sensitivity = 1.0
        self.layout = {}  # nome -> [x, y] normalizados (substitui o padrão)

    def position(self, name):
        if name in self.layout:
            return tuple(self.layout[name])
        d = BUTTON_DEFS[name]
        return d[1], d[2]

    def set_position(self, name, x, y):
        self.layout[name] = [min(max(x, 0.03), 0.97), min(max(y, 0.05), 0.95)]

    def reset_layout(self):
        self.layout = {}

    def change_scale(self, delta):
        self.button_scale = round(min(1.6, max(0.6, self.button_scale + delta)), 2)

    def change_sensitivity(self, delta):
        self.look_sensitivity = round(min(3.0, max(0.3, self.look_sensitivity + delta)), 2)

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"button_scale": self.button_scale, "look_sensitivity": self.look_sensitivity,
                           "layout": self.layout}, f)
        except Exception:
            pass  # no navegador o armazenamento pode não persistir; não é erro grave

    def load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.button_scale = float(d.get("button_scale", 1.0))
                self.look_sensitivity = float(d.get("look_sensitivity", 1.0))
                self.layout = dict(d.get("layout", {}))
        except Exception:
            pass
        return self
