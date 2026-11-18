# /// script
# dependencies = ["pygame-ce"]
# ///
"""Arsenal LC - protótipo em Python (pygame-ce). Roda no PC e no navegador do celular (pygbag)."""
import asyncio

import pygame

from arsenal_lc.game.sim import Game
from arsenal_lc.ui.input_hub import InputHub
from arsenal_lc.ui.menu import Menu
from arsenal_lc.ui.render import Renderer
from arsenal_lc.ui.settings import Settings

W, H = 960, 540


async def main():
    pygame.init()
    pygame.display.set_caption("Arsenal LC - protótipo")
    try:
        screen = pygame.display.set_mode((W, H), pygame.SCALED)
    except Exception:
        screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    settings = Settings().load()
    game = Game()
    hub = InputHub(settings, W, H)
    menu = Menu(game, settings, hub, W, H)
    hub.menu = menu
    renderer = Renderer(screen, W, H)

    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            else:
                hub.handle_event(e)
        game.update(dt, hub.poll(menu_open=menu.open))
        renderer.draw(game, hub, menu, clock.get_fps())
        pygame.display.flip()
        await asyncio.sleep(0)   # obrigatório para o navegador (pygbag)
    pygame.quit()


asyncio.run(main())
