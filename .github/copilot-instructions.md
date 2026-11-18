# Instruções para o GitHub Copilot — Arsenal LC (Python)

Projeto: protótipo de shooter tático 4v4 (mobile) em **Python 3.12 + pygame-ce**, vista de cima 2D, com a mecânica
exclusiva **ECHO TRACE**. É o porte do protótipo Unity (C#) original. Responda e comente em **português do Brasil**.

## Arquitetura (respeite as camadas)
- `arsenal_lc/core/`: regras puras, **proibido importar pygame**. Reutilizável no futuro servidor dedicado.
- `arsenal_lc/game/`: simulação (mapa, colisão, tiro, bots, scanner, rastro falso), **sem pygame**. Todo o resultado
  do jogo (dano, munição, cadência, vida, rastros) é decidido aqui e no core, nunca na UI.
- `arsenal_lc/ui/` e `main.py`: pygame (entrada, menu, desenho). Só lê o estado do `Game` e produz `InputState`.
- Coordenadas: x = leste, z = norte; ângulo/heading em radianos a partir de +Z, sentido horário
  (`x += sin(a)`, `z += cos(a)`). Tela: y cresce para baixo (`sy = H/2 - (z - cam_z) * PPM`).

## Regras inegociáveis do ECHO TRACE
- Parado não deixa rastro; correr = forte (1.0), andar = 0.6, agachado = 0.3. Amostra a cada 0,2 s, vida de 12 s.
- O scanner **nunca** devolve pontos com menos de `TraceRules.REVEAL_DELAY` (1,5 s): a posição atual do inimigo
  jamais é revelada. Não enfraqueça isso nem os testes que o garantem.
- O campo `synthetic` (rastro falso) só pode aparecer na UI no modo debug.

## Compatibilidade web (pygbag / celular)
- `main.py` usa `asyncio` e `await asyncio.sleep(0)` em cada quadro. Não use `time.sleep`, threads, `input()`
  nem bibliotecas fora do pygame-ce/stdlib. Sem numpy. Sem arquivos grandes.
- Entrada de toque é multitoque (`FINGERDOWN/MOTION/UP`); o mouse só vale quando nenhum toque foi detectado.
- Tela lógica 960x540. Botões em coordenadas normalizadas (0..1) para caber em qualquer celular.

## Qualidade
- Rode `python -m unittest discover -s tests -v` antes de concluir. Toda regra nova do core/game ganha teste.
- Números de balanceamento são provisórios; mantenha-os em `core/weapons.py` e `core/trace.py`.
- Não finja funcionalidades: o que não existe (multiplayer, ranqueado, mapas finais, operadores) não deve aparecer
  na interface como se funcionasse. Atualize `docs/STATUS.md` ao entregar algo.
