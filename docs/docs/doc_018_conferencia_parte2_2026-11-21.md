# Relatório do brief 018 — Conferência, parte 2: desempate, semelhança e decisão

- Data: 2026-11-21
- Brief: `docs/briefs/brief_018_conferencia_parte2_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.** `test_ancora.py`, `test_decisao.py` e `test_integracao.py` passam no gate, com respostas falsas, e a semelhança se desliga sozinha em modo de teste: o critério da Fase 8 está cumprido.

## RELATÓRIO FINAL

- Brief executado: 018 — Conferência, parte 2 (Fase 8).

- Arquivos criados:
  - `docs/briefs/brief_018_conferencia_parte2_2026-11-21.md` — o brief, literal;
  - `testes/test_decisao.py` — os 8 pontos do aceite, com resultados de conferência escritos no teste (17 testes);
  - `testes/test_integracao.py` — o primeiro teste de integração, com 4 cenários, cada um com a sua pasta temporária (repositório git próprio com cópias de `fabrica/`, `pyproject.toml`, `dados/`, `instrucoes/` e `config/`);
  - `instrucoes/opus_desempate.md`;
  - `fabrica/conferencia/desempate.py` — `EtapaDesempate`, `perguntas` e `respostas_locais`;
  - `fabrica/conferencia/semelhanca.py` — `EtapaSemelhanca`, `limpar`, `trechos`, `jaccard` (com frações, exato) e `indice`;
  - `fabrica/conferencia/decisao.py` — `Entradas`, `decidir`, `EtapaDecisao` e `veredito_de_formato`;
  - `docs/docs/doc_018_conferencia_parte2_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `fabrica/__main__.py` — `ETAPAS` com a ordem completa: ficha, retorno, redação, extração, programas, checklist, conferente local, desempate, semelhança, decisão;
  - `fabrica/conferencia/local.py` — **defeito comprovado** (registro de decisão 001, item 19), achado pelo teste de integração: `EtapaLocal.aplica` não esperava o checklist, e a peça de risco médio cuja ficha foi descartada (sem rascunho) caía no pedido do conferente local e quebrava o `avancar`. Agora `aplica` exige o checklist gravado, e a regra do sorteio ficou em `se_aplica`;
  - `testes/test_conferencia_etapas.py` — os dois testes do conferente local seguem a correção: o do sorteio chama `se_aplica`, e o do envio grava o checklist antes;
  - `docs/docs/pendencias_para_o_computador.md` — cinco linhas do 018;
  - `docs/PLAN.md` — Resumo; 018 do Backlog para o Done; hash do 017 no Done.

- Arquivos preservados literalmente na área afetada: `docs/ARQUITETURA.md` (o `test_integracao.py` fica para o 023 consolidar), `fabrica/estado.py`, `dados/`, `config/`, os demais módulos, `scripts/`, `AGENTS.md`, `docs/PLANO.md`.

- Testes rodados e resultado (com a saída colada):

  Primeiro o teste, sem o código (vermelho). O esboço dos três módulos foi escrito antes do teste; para o vermelho, os três arquivos foram tirados da árvore e o teste rodou sem eles:

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_decisao.py'.
  E   ImportError: cannot import name 'decisao' from 'fabrica.conferencia' (/home/user/pet_sint/fabrica/conferencia/__init__.py)
  ```

  Gate (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  104 files already formatted
  == mypy fabrica
  Success: no issues found in 29 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 1088 items

  testes/test_ancora.py ..........................                         [  2%]
  testes/test_api_claude.py ...............................                [  5%]
  testes/test_arquivos.py ..................                               [  6%]
  testes/test_citacoes.py ................................................ [ 11%]
  ............                                                             [ 12%]
  testes/test_comparacao.py .............................................. [ 16%]
  ..............................................                           [ 20%]
  testes/test_conferencia_etapas.py ..............                         [ 22%]
  testes/test_config.py .................................................. [ 26%]
  ........................................................................ [ 33%]
  ........................................................................ [ 39%]
  ...............................................................          [ 45%]
  testes/test_congelamento.py .................                            [ 47%]
  testes/test_dados_reais.py ..........................................    [ 51%]
  testes/test_decisao.py .................                                 [ 52%]
  testes/test_entrega.py .................................                 [ 55%]
  testes/test_estado.py ........................................           [ 59%]
  testes/test_estatistica.py ..........                                    [ 60%]
  testes/test_fichas.py .............                                      [ 61%]
  testes/test_ficticios.py ..........................                      [ 63%]
  testes/test_formatos.py ................................................ [ 68%]
  ........................................................................ [ 75%]
  ........................................................................ [ 81%]
  ......................................................................   [ 88%]
  testes/test_gasto.py ..............                                      [ 89%]
  testes/test_integracao.py ....                                           [ 89%]
  testes/test_modelo_local.py ..........................                   [ 92%]
  testes/test_redacao.py ......                                            [ 92%]
  testes/test_registro.py ...                                              [ 92%]
  testes/test_regras.py .......................                            [ 95%]
  testes/test_travas.py .................................................. [ 99%]
  ....                                                                     [100%]

  ============================ 1088 passed in 25.97s =============================
  saída=0
  ```

- Comandos executados: `pytest testes/test_decisao.py` (vermelho e depois verde); `pytest testes/test_integracao.py testes/test_conferencia_etapas.py testes/test_decisao.py`; `ruff format`; `ruff check --fix`; `scripts/verificar.sh`; `scripts/entregar.sh 018`. Nenhuma chamada a modelo: nos testes, a API e o modelo local são falsos, e o bloqueio de rede não foi acionado.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_018_conferencia_parte2_2026-11-21.md
testes/test_decisao.py
testes/test_integracao.py
testes/test_conferencia_etapas.py
instrucoes/opus_desempate.md
fabrica/conferencia/desempate.py
fabrica/conferencia/semelhanca.py
fabrica/conferencia/decisao.py
fabrica/conferencia/local.py
fabrica/__main__.py
docs/docs/pendencias_para_o_computador.md
docs/docs/doc_018_conferencia_parte2_2026-11-21.md
docs/PLAN.md

Brief 018: conferência, parte 2, e o primeiro teste de integração

Desempate pelo Opus nas três situações (um pedido por peça), semelhança
por Jaccard exato de trechos de cinco palavras (desligada em modo de
teste), decisão pelo Anexo B.3 com o caminho de cada item e as quatro
categorias do motivo, e a ordem completa das etapas em __main__.py.
O teste de integração leva as três peças do ensaio de ficha a veredito
com clientes falsos e achou um defeito no conferente local (corrigido).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Categoria formato.** Quando a extração, o checklist ou o desempate falham duas vezes no formato, o condutor (`estado.py`) grava o destino `reprovada_formato` e encerra a versão antes da etapa de decisão, e por isso nenhum veredito é gravado. `decisao.decidir` cobre a categoria (descartada, sem refação) e `decisao.veredito_de_formato` monta o veredito para quem lê o destino; `estado.py` não foi mudado, porque o brief não o lista e não é defeito: o destino já tem o efeito pedido. O relatório do 023 lê o destino.
  2. **Partes do pedido ao Opus:** instruções; a lista dos itens (JSON na parte `estrutura`), cada um com a pergunta e a situação (`discordancia`, `risco_alto`, `medio_sem_local`); o trecho da tabela; a ficha; o rascunho. Só na discordância o pedido leva as respostas e os trechos do Haiku e do modelo local; no risco alto o Opus responde sozinho, como barreira à parte. A resposta que não traz exatamente os itens pedidos volta "fora do formato".
  3. **Quando há pedido ao Opus:** risco alto, sempre (todos os itens do conferente do tipo); baixo e médio, nos itens do conferente local em que o Haiku e o local discordam; médio, nos itens do conferente local sem resposta dele (gravada como indisponível pela válvula depois de 72 horas, ou pedido que não coube). No baixo sem resposta do local, vale o Haiku, sem Opus.
  4. **Citações não resolvidas:** a resposta do checklist a cada pergunta entra no caminho do item `citacao_fora_da_tabela`, ao lado da do programa; um "não passa" reprova pelo item.
  5. **Motivo:** os itens reprovados, cada um com o trecho de quem decidiu, separados por ponto e vírgula; a reprovação por semelhança leva a marca `[semelhança]` no começo do motivo, além da categoria; a de formato, `[formato]`.
  6. **Semelhança:** compara com cada aprovada do mesmo tipo e da mesma rodada, menos as versões da própria peça, e vale o maior índice; sem aprovada para comparar, o valor fica vazio e o item passa. São tiradas as linhas da marca, as linhas de título (começadas por `#`) e as linhas iguais a um título da estrutura; os marcadores de nome e de OAB são tirados do texto. Texto com menos de cinco palavras vira um trecho só. O limite é o do `config.toml` (0,85), comparado em fração exata.
  7. **Modo de teste:** a semelhança grava `desligada` e o veredito traz o alerta "desligada em modo de teste"; a peça aprovada em modo de teste não vai para `saida/aprovadas/`.
  8. **O teste de integração** (cenários 9 a 15 do brief) mostrou que a interface do registro de decisão 002 basta: nenhuma mudança de interface. As respostas falsas são escolhidas pela instrução que abre o pedido e pelo tipo da peça; a extração falsa acha a peça pelo rascunho que a redação falsa escreveu.
  9. **Para o brief 023 consolidar:** os três módulos, `instrucoes/opus_desempate.md`, `testes/test_decisao.py` e `testes/test_integracao.py` na ARQUITETURA.
