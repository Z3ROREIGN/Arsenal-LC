# Arsenal LC — protótipo em Python

Versão em **Python (pygame-ce)** do protótipo Unity do Arsenal LC, feita para quem não consegue abrir o Unity
(por exemplo, só tem celular). É **2D, vista de cima**, com a mecânica exclusiva **ECHO TRACE** funcionando.

Roda de dois jeitos:
- **No celular, pelo navegador** (recomendado): o GitHub compila o jogo com *pygbag* e publica no GitHub Pages.
- **No PC**: `pip install -r requirements.txt` e `python main.py`.

> **Honestidade:** a lógica do jogo (`arsenal_lc/core` e `arsenal_lc/game`) tem **46 testes automatizados que passam**.
> A camada de tela/toque (`arsenal_lc/ui`, `main.py`) foi escrita **sem poder abrir uma janela** e testada só com um
> `pygame` de mentira (sem erros de lógica), **mas nunca rodou num pygame real nem num celular**. O primeiro teste
> no aparelho pode revelar ajustes (principalmente toque e escala da tela). Mande o erro/print que corrigimos.

## Jogar no celular (GitHub Pages)
1. Crie um repositório no GitHub e envie estes arquivos (veja "Como enviar pelo celular" abaixo).
2. No repositório: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Faça um *push* na branch `main` (ou **Actions → Deploy web build → Run workflow**).
4. Quando o workflow terminar (verde), o link aparece em **Settings → Pages** (`https://SEU-USUARIO.github.io/NOME-DO-REPO/`).
5. Abra o link no celular, **toque na tela para iniciar** e jogue na horizontal.

## Controles
| Ação | Celular | PC |
|---|---|---|
| Mover | joystick flutuante (metade esquerda); empurrar até o limite = correr | WASD (Shift corre) |
| Mirar | arrastar na metade direita (direção do arrasto) ou arrastar o dedo no botão TIRO | mouse |
| Atirar / Mirar (zoom) | TIRO / MIRA | botão esquerdo / direito |
| Recarregar / Agachar / Trocar arma | RECARGA / AGACHAR / TROCAR | R / C / Q |
| **ECHO SCAN** | ECHO SCAN | E |
| **Rastro falso** | FALSO | G |
| Configurações | CFG | Esc / Tab / F1 |

No **CFG**: ver rastros próprios (debug), receber 25 de dano (testar vida), mover botões, tamanho dos botões e sensibilidade.

## O que existe
- Mapa de teste idêntico ao do Unity: pista de tiro (alvos a 8, 15, 25, 40 e 60 m), sala com portas, coberturas baixas
  (agache atrás delas), plataforma com escada (decorativa em 2D), caixas, 3 patrulheiros.
- Armas: as **6** do catálogo já são equipáveis (AR-09, PX-7, SM-4, BR-21, SR-8, SG-12) — no Unity só 2 eram.
- Dano por distância e por região (cabeça/corpo/perna), dispersão, recuo, recarga, vida com regeneração limitada (teto 60%).
- **ECHO TRACE**: rastro a cada 0,2 s (parado = nenhum; correr = forte; agachado = fraco), duram 12 s.
  **ECHO SCAN** (22 m, 4 s ativo, 12 s de recarga) mostra rastros inimigos com setas de direção e **nunca** pontos com
  menos de 1,5 s (a posição atual nunca aparece). **Rastro falso** (2 cargas, 1 a cada 15 s) cria um fantasma que
  deixa rastros sintéticos idênticos aos reais (magenta só no modo debug).

## O que mudou por ser 2D
- Não existe altura de verdade: a altura do tiro é simulada. A dispersão vertical decide **cabeça/corpo/perna** e se o
  tiro **passa por cima de cobertura baixa** (de pé passa; agachado atrás da cobertura, bloqueia).
- Sem áudio, sem giroscópio, sem modelos 3D. Paredes não escondem os rastros (a vista é de cima).

## Estrutura
```
main.py                     entrada (asyncio, compatível com pygbag)
arsenal_lc/core/            regras puras (armas, dano, vida, ECHO TRACE) - sem pygame
arsenal_lc/game/            mapa, colisão, tiro, bots, scanner, rastro falso - sem pygame
arsenal_lc/ui/              toque/teclado, menu CFG, desenho (pygame)
tests/                      unittest (rode: python -m unittest discover -s tests -v)
.github/workflows/          tests.yml (testes) e pages.yml (build web + GitHub Pages)
.github/copilot-instructions.md   contexto fixo para o GitHub Copilot
COPILOT_PROMPT.md           pedidos prontos para colar no Copilot
docs/STATUS.md              o que está pronto e o que falta
```

## Como enviar pelo celular
- **Pelo site do GitHub (navegador)**: crie o repositório, **Add file → Upload files** e envie o conteúdo da pasta
  (extraia o zip antes; o GitHub não extrai zip sozinho). Pastas começando com ponto (`.github`) podem não aparecer no
  seletor do celular: nesse caso crie os arquivos de `.github/workflows/` com **Add file → Create new file** colando o
  conteúdo e digitando o caminho completo no nome (ex.: `.github/workflows/pages.yml`).
- **Pelo app/Codespaces**: abra o repositório num Codespace, envie o zip e rode `unzip`.
