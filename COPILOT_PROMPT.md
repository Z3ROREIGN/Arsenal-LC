# Pedidos prontos para o GitHub Copilot

Cole um de cada vez (Copilot Chat ou agente de codificação). O contexto fixo já está em `.github/copilot-instructions.md`.

## 1) Primeiro: validar
```
Leia o README.md e docs/STATUS.md. Rode `python -m unittest discover -s tests -v` e corrija o que falhar.
Depois confira se `python main.py` abre sem erro e se o workflow .github/workflows/pages.yml gera o build pygbag.
Não mude regras do core sem atualizar os testes.
```

## 2) Áudio simples (compatível com pygbag)
```
Adicione áudio: tiro por arma, recarga, ping do ECHO SCAN, bip do rastro falso e "negado".
Gere os sons com pygame.mixer a partir de bytes/ondas simples SEM numpy (ex.: array('h') + pygame.mixer.Sound(buffer=...)).
Crie arsenal_lc/ui/audio.py, toque os sons a partir de eventos do Game (adicione uma lista game.sound_events
consumida pela UI a cada quadro). Respeite que no navegador o áudio só inicia após o primeiro toque.
```

## 3) Operadores e habilidades
```
Implemente os operadores SENTINELA, BREAKER, MEDIC e ENGENHEIRO em arsenal_lc/game/ com uma habilidade ativa cada,
mantendo a lógica sem pygame e com testes. Adicione um botão de habilidade no layout (BUTTON_DEFS) e uma tela simples
de escolha do operador antes de começar. Atualize docs/STATUS.md.
```

## 4) Bots inimigos que atiram (modo 1x1 offline)
```
Faça os patrulheiros poderem atirar no jogador usando a mesma WeaponState do core, com tempo de reação e dispersão
razoáveis, linha de visão (use World.raycast) e dano ao jogador via Game.damage_player. Adicione o modo "Eliminação 4v4
offline" (4 aliados bots vs 4 inimigos bots) com contagem de rodadas. Mantenha o scanner mostrando só rastros inimigos.
```

## 5) Multiplayer (etapa futura)
```
Crie um servidor autoritativo em Python (asyncio + websockets) em server/ que reutilize arsenal_lc/core e arsenal_lc/game.
Cliente envia só entrada (move/aim/fire/ability) numerada; servidor simula a 30 Hz e envia snapshots. A consulta do
ECHO SCAN roda no servidor e o cliente nunca recebe rastros brutos nem a posição de inimigos fora da linha de visão.
Comece por um protocolo e testes locais antes de qualquer interface.
```
