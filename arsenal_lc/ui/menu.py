import pygame


class Menu:
    """Menu CFG: debug de rastros, dano de teste, layout, tamanho dos botões e sensibilidade."""

    def __init__(self, game, settings, hub, width, height):
        self.game, self.settings, self.hub = game, settings, hub
        self.open = False
        self.W, self.H = width, height
        self.panel = pygame.Rect(width // 2 - 240, height // 2 - 215, 480, 430)
        self.rows = []
        self._build_rows()

    def _build_rows(self):
        x, y0, w, h, gap = self.panel.x + 20, self.panel.y + 56, self.panel.w - 40, 44, 8
        names = ["debug", "damage", "edit", "scale", "sens", "reset", "close"]
        self.rows = [(n, pygame.Rect(x, y0 + i * (h + gap), w, h)) for i, n in enumerate(names)]

    def toggle(self):
        self.open = not self.open

    def labels(self):
        g, s = self.game, self.settings
        return {
            "debug": "Ver rastros próprios (debug): " + ("LIGADO" if g.debug_reveal_all else "desligado"),
            "damage": "Receber 25 de dano",
            "edit": "Mover botões",
            "scale": "Tamanho dos botões: %d%%   [-]  [+]" % round(s.button_scale * 100),
            "sens": "Sensibilidade: %.1fx   [-]  [+]" % s.look_sensitivity,
            "reset": "Restaurar posições dos botões",
            "close": "Fechar",
        }

    def handle_tap(self, x, y):
        for name, rect in self.rows:
            if not rect.collidepoint(x, y):
                continue
            left_half = x < rect.centerx
            if name == "debug":
                self.game.debug_reveal_all = not self.game.debug_reveal_all
            elif name == "damage":
                self.game.damage_player(25)
            elif name == "edit":
                self.open = False
                self.hub.edit_mode = True
            elif name == "scale":
                self.settings.change_scale(-0.1 if left_half else 0.1)
                self.settings.save()
            elif name == "sens":
                self.settings.change_sensitivity(-0.1 if left_half else 0.1)
                self.settings.save()
            elif name == "reset":
                self.settings.reset_layout()
                self.settings.save()
            elif name == "close":
                self.open = False
            return
        if not self.panel.collidepoint(x, y):
            self.open = False

    def draw(self, screen, font, small):
        if not self.open:
            return
        pygame.draw.rect(screen, (18, 22, 30), self.panel, border_radius=12)
        pygame.draw.rect(screen, (90, 200, 255), self.panel, 2, border_radius=12)
        t = font.render("CONFIGURAÇÕES", True, (230, 240, 255))
        screen.blit(t, (self.panel.centerx - t.get_width() // 2, self.panel.y + 16))
        labels = self.labels()
        for name, rect in self.rows:
            pygame.draw.rect(screen, (40, 52, 70), rect, border_radius=8)
            s = small.render(labels[name], True, (235, 240, 250))
            screen.blit(s, (rect.x + 12, rect.centery - s.get_height() // 2))
