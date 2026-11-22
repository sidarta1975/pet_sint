# Relatório do brief 005 — Gasto, estatística e congelamento

- Data: 2026-11-21
- Brief: `docs/briefs/brief_005_gasto_estatistica_congelamento_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.** Com os briefs 003 e 004, fecha o critério da Fase 3.

## RELATÓRIO FINAL

- Brief executado: 005 — Gasto, estatística e congelamento (Fase 3).

- Arquivos criados:
  - `docs/briefs/brief_005_gasto_estatistica_congelamento_2026-11-21.md` — o brief, literal;
  - `fabrica/comum/estatistica.py` — intervalo de Wilson de 95% (z = 1,96), com taxa e limites; zero em zero e contagem impossível dão erro; `criterio_central_passa` com os dois mínimos recebidos (lidos da configuração por quem chama);
  - `fabrica/comum/gasto.py` — `ControleGasto`: custo previsto (tokens contados mais o teto de saída da tarefa), custo real pelos tokens, total gasto, previsão pessimista, autorização com parada registrada no corte, alerta uma vez, custo marginal por peça aprovada; preço alto do Haiku acima de 100 mil tokens de entrada, na entrada e na saída do pedido;
  - `fabrica/comum/congelamento.py` — impressões digitais de `dados/`, `instrucoes/`, dos dois arquivos de configuração e do código; abre a rodada em `saida/rodadas.json`; confere antes de cada passo e devolve "parar" com a lista, gravando a ocorrência; compara com o ensaio aprovado;
  - `testes/test_estatistica.py`, `testes/test_gasto.py`, `testes/test_congelamento.py` — os testes de aceite, escritos antes do código;
  - `docs/docs/doc_005_gasto_estatistica_congelamento_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `docs/PLAN.md` — Resumo; 005 do Backlog para o Done; hash do 004 (`6802157`) no Done.

- Arquivos preservados literalmente na área afetada: `formatos.py`, `arquivos.py`, `config.py`, `registro.py`, `config/`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`. Nenhum defeito comprovado.

- Testes rodados e resultado (com a saída colada):

  Primeiro os testes, sem o código (vermelho):

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_estatistica.py'.
  E   ModuleNotFoundError: No module named 'fabrica.comum.estatistica'
  ImportError while importing test module '/home/user/pet_sint/testes/test_gasto.py'.
  E   ModuleNotFoundError: No module named 'fabrica.comum.gasto'
  ImportError while importing test module '/home/user/pet_sint/testes/test_congelamento.py'.
  E   ModuleNotFoundError: No module named 'fabrica.comum.congelamento'
  ```

  Com o código, uma falha do próprio teste: o relógio fixo usado em `test_congelamento.py` dava o mesmo carimbo às duas cópias de `rodadas.json` da mesma sessão, e `arquivos.py`, que nunca sobrescreve, recusou a segunda. O relógio do teste passou a andar um segundo por leitura, como o de verdade anda; `arquivos.py` não mudou. Gate final (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  35 files already formatted
  == mypy fabrica
  Success: no issues found in 10 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 614 items

  testes/test_arquivos.py ..................                               [  2%]
  testes/test_config.py .................................................. [ 11%]
  ........................................................................ [ 22%]
  ........................................................................ [ 34%]
  ...............................................................          [ 44%]
  testes/test_congelamento.py .................                            [ 47%]
  testes/test_entrega.py .................................                 [ 52%]
  testes/test_estatistica.py ..........                                    [ 54%]
  testes/test_formatos.py ................................................ [ 62%]
  ........................................................................ [ 74%]
  ........................................................................ [ 85%]
  ......................................................................   [ 97%]
  testes/test_gasto.py ..............                                      [ 99%]
  testes/test_registro.py ...                                              [100%]

  ============================= 614 passed in 5.32s ==============================
  ```

- Comandos executados: `pytest` dos três testes (vermelho e depois verde); `ruff format`; `scripts/verificar.sh`; `scripts/entregar.sh 005`. Os testes de congelamento criam repositório git só na pasta temporária. Nenhuma chamada à API da Claude nem ao modelo local.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_005_gasto_estatistica_congelamento_2026-11-21.md
fabrica/comum/estatistica.py
fabrica/comum/gasto.py
fabrica/comum/congelamento.py
testes/test_estatistica.py
testes/test_gasto.py
testes/test_congelamento.py
docs/docs/doc_005_gasto_estatistica_congelamento_2026-11-21.md
docs/PLAN.md

Brief 005: gasto, estatística e congelamento

gasto.py faz a previsão pessimista, o alerta e o corte (que não sobe), com
custos inteiros em milionésimos de centavo e o preço alto do Haiku acima
de 100 mil tokens. estatistica.py dá o intervalo de Wilson de 95%.
congelamento.py grava as impressões da rodada e para quando algo muda.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Tokens de cache e de raciocínio no custo real.** O `config.toml` não tem preço de cache. Os tokens de cache são cobrados ao preço de entrada (pessimista: a leitura de cache custa menos) e contam para o limite de 100 mil do Haiku. Os de raciocínio não são somados de novo, porque a API já os inclui nos tokens de saída: o brief 006 precisa gravar em `saida` o total de saída que a API informa.
  2. **Alerta.** Dispara uma vez por execução, na primeira autorização em que a previsão pessimista passa de 3000 centavos; se o gasto registrado já passou do alerta quando o programa começa, não repete. Não é ocorrência (a lista fechada de ocorrências não tem "alerta"); quem mostra o aviso é quem chama (brief 008).
  3. **Custo marginal.** Soma as chamadas da rodada (identificador `r..`) das tarefas de ficha, redação, extração, checklist e conferência do Opus, fora as de peças de cópia (nome com `_erro`) e as tarefas de cópia e verificação; divide pelo número de peças aprovadas, com resto descartado (inteiro em milionésimos de centavo). O modelo local não custa.
  4. **Conferência do congelamento.** Além das impressões, conta como mudança qualquer mudança pendente nas pastas congeladas e no código (linha `codigo:mudança pendente`), porque a impressão do código é a da versão sem mudanças pendentes (ADR 001, item 6).
  5. Arquivos de teste novos, para o brief 023 consolidar: nenhum além dos três previstos na ARQUITETURA §2.4.
  6. **Ramo único**, como nos briefs anteriores (pedido de integração #2).

- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim.
