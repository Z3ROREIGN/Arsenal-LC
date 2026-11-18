# Sessão única do Copilot — Arsenal LC (tudo de uma vez, em fases)

Cole o bloco abaixo inteiro no Copilot (agente de codificação / Copilot Chat em modo agente).
O contexto fixo já está em `.github/copilot-instructions.md`.

```
Você vai evoluir o protótipo Arsenal LC (Python 3.12 + pygame-ce, 2D vista de cima) em UMA sessão, em fases.
Leia antes: README.md, docs/STATUS.md, .github/copilot-instructions.md e todo o código de arsenal_lc/.

REGRAS GERAIS
- Responda e comente em português do Brasil.
- Faça UMA FASE POR VEZ. Ao fim de cada fase: rode `python -m unittest discover -s tests -v`, corrija o que falhar,
  atualize docs/STATUS.md e faça um commit com a mensagem "Fase N: <título>". Só então comece a próxima.
- Respeite as camadas: core/ e game/ sem pygame (testáveis); ui/ e main.py com pygame.
- Compatível com pygbag (celular): asyncio, sem threads, sem numpy, sem bibliotecas extras, sem time.sleep.
- Controles de toque novos entram em BUTTON_DEFS (arsenal_lc/ui/settings.py) com layout editável. Não cubra o joystick
  nem o botão de tiro.
- NUNCA enfraqueça a regra do ECHO TRACE: o scanner jamais revela pontos com menos de 1,5 s (posição atual).
- Não finja funcionalidades: se algo não ficar pronto, deixe fora da interface e registre em docs/STATUS.md.
- Cada regra nova de core/game ganha teste unittest. Números de balanceamento ficam em um só lugar e são provisórios.
- Se uma fase travar, registre o motivo em docs/STATUS.md e siga para a próxima em vez de parar.

FASE 1 — Bots inimigos que atiram
- Patrulheiros passam a atirar no jogador usando a mesma WeaponState do core: tempo de reação, dispersão, linha de visão
  (World.raycast), dano via Game.damage_player. Estados: patrulhar, investigar (vão até o último ponto onde ouviram/viram),
  atacar, recuar quando a vida está baixa. Dificuldade ajustável (facil/normal/dificil).
- Testes: bot não atira através de parede alta; atira por cima de cobertura baixa só se o jogador estiver de pé; dano cai
  com a distância.

FASE 2 — Feedback e polimento
- Indicador de dano (flash vermelho + seta da direção do tiro), kill feed, mini-mapa pequeno (cantos que não cubram botões),
  partículas (faísca na parede, flash no alvo), tremor de tela proporcional ao recuo.
- Áudio sem numpy: gerar ondas simples com array('h') + pygame.mixer.Sound(buffer=...). Sons: tiro (um por arma), recarga,
  ping do scan, bip do rastro falso, "negado". Criar arsenal_lc/ui/audio.py e uma lista game.sound_events consumida pela UI
  a cada quadro. No navegador o áudio só inicia após o primeiro toque; trate isso sem travar o jogo.

FASE 3 — Tela inicial, tutorial e progresso
- Menu inicial (Jogar, Treino, Configurações), escolha de modo/mapa/operador depois que existirem, tutorial guiado no mapa de
  treino (andar, atirar, agachar atrás da cobertura, ECHO SCAN, rastro falso) com checklist na tela.
- Progresso local (XP, nível, armas desbloqueadas) em arquivo JSON via Settings-like store, com try/except (no navegador
  pode não persistir; avise isso na interface).

FASE 4 — Operadores e habilidades
- SENTINELA, BREAKER, MEDIC, ENGENHEIRO em arsenal_lc/game/operators.py, um botão de habilidade no layout.
  SENTINELA: "analisar autenticidade" — o próximo scan marca cada rastro como REAL ou FALSO (isso só vale para essa
  habilidade; o campo synthetic continua oculto no resto do jogo). BREAKER: arrombar/derrubar cobertura baixa. MEDIC: cura
  acima do teto de regeneração. ENGENHEIRO: torreta curta que atira em inimigos.
- Escolha de operador antes da partida. Testes para cada habilidade (recarga, efeito, limites).

FASE 5 — Granadas e dispositivos
- Fumaça (bloqueia linha de visão dos bots e a mira, e NÃO bloqueia o scan), granada de efeito (flash), mina de
  proximidade. Cargas e recargas em game/, botões no layout, testes.

FASE 6 — Mecânicas novas de rastro
- Superfícies no mapa: metal (rastro mais forte), grama/tapete (mais fraco) — multiplicam a intensidade em
  TraceRules/Emitter. Bots investigam rastros falsos (enganáveis). Aviso "VOCÊ FOI ESCANEADO" quando um bot inimigo usa scan.
  Cor do rastro por idade (quente -> frio) no desenho.

FASE 7 — Modos de jogo e mapas
- Modos offline com bots: Eliminação 4v4 (aliados bots vs inimigos bots, rodadas, placar), Dominação (3 pontos) e Duelo 1x1.
  Reaparecimento, fim de partida e tela de resultado.
- Mapas BLACKSITE, NEON DISTRICT e DUST CORE como funções em world.py (lista de Box + superfícies + pontos de spawn),
  escolhidos no menu inicial. Cada mapa deve ter teste de que o spawn é livre e que não há spawn dentro de parede.

FASE 8 — Preparação para multiplayer (SEM implementar rede ainda)
- Separe em game/ uma interface clara de "entrada numerada -> estado": Game.step(inputs) determinístico, snapshots do
  estado serializáveis (dict/JSON), e a consulta do scanner isolada em uma função que receba só buffers e posição.
- Escreva docs/MULTIPLAYER.md com o protocolo proposto (mensagens, 30 Hz, lag compensation, o cliente nunca recebe rastros
  brutos nem a posição de inimigos fora da linha de visão). Não adicione dependências de rede.

AO FINAL
- Rode todos os testes, confira que `python main.py` abre sem erro e que o workflow .github/workflows/pages.yml continua
  válido (só main.py e arsenal_lc/ vão para o build web).
- Atualize README.md (controles novos) e docs/STATUS.md (o que está pronto, o que foi testado, o que NÃO foi testado em
  celular real). Liste no resumo final tudo que ficou de fora e por quê.
```

## Dicas para usar no celular
- Se a sessão for longa e o agente parar no meio, responda: "Continue da fase N a partir do último commit".
- Se o build web falhar, abra a aba **Actions**, copie o erro do passo que ficou vermelho e cole no Copilot.
- Depois de cada fase, abra o link do GitHub Pages no celular e confira o toque antes de pedir a próxima.
