# Relatório do brief 017 — Conferência, parte 1: extração, checklist e conferente local

- Data: 2026-11-21
- Brief: `docs/briefs/brief_017_conferencia_parte1_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.** `test_conferencia_etapas.py` passa no gate. O critério da Fase 8 fecha no brief 018.

## RELATÓRIO FINAL

- Brief executado: 017 — Conferência, parte 1 (Fase 8).

- Arquivos criados:
  - `docs/briefs/brief_017_conferencia_parte1_2026-11-21.md` — o brief, literal;
  - `testes/test_conferencia_etapas.py` — os 5 pontos do aceite, com fichas prontas das três peças do ensaio, rascunhos de exemplo e os clientes falsos;
  - `instrucoes/extracao.md`, `instrucoes/checklist.md`, `instrucoes/conferente_local.md`;
  - `fabrica/conferencia/extracao.py` — `EtapaExtracao` e os caminhos comuns da conferência;
  - `fabrica/conferencia/checklist.py` — `EtapaChecklist` e `itens_do_tipo`;
  - `fabrica/conferencia/local.py` — `EtapaLocal` e `sorteadas`;
  - `docs/docs/doc_017_conferencia_parte1_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `fabrica/conferencia/regras.py` — só acrescentado, no fim: `EtapaProgramas`, `dado_real` e os textos da ficha para o detector; as regras já testadas não mudaram;
  - `docs/docs/pendencias_para_o_computador.md` — três linhas do 017;
  - `docs/PLAN.md` — Resumo; 017 do Backlog para o Done; hash do 016 no Done.

- Arquivos preservados literalmente na área afetada: `docs/ARQUITETURA.md`, `fabrica/__main__.py`, `dados/`, `config/`, os demais módulos, `scripts/`, `AGENTS.md`, `docs/PLANO.md`.

- Testes rodados e resultado (com a saída colada):

  Primeiro o teste, sem o código (vermelho):

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_conferencia_etapas.py'.
  E   ImportError: cannot import name 'checklist' from 'fabrica.conferencia' (/home/user/pet_sint/fabrica/conferencia/__init__.py)
  ```

  Gate (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  96 files already formatted
  == mypy fabrica
  Success: no issues found in 26 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 1067 items

  testes/test_ancora.py ..........................                         [  2%]
  testes/test_api_claude.py ...............................                [  5%]
  testes/test_arquivos.py ..................                               [  7%]
  testes/test_citacoes.py ................................................ [ 11%]
  ............                                                             [ 12%]
  testes/test_comparacao.py .............................................. [ 16%]
  ..............................................                           [ 21%]
  testes/test_conferencia_etapas.py ..............                         [ 22%]
  testes/test_config.py .................................................. [ 27%]
  ........................................................................ [ 34%]
  ........................................................................ [ 40%]
  ...............................................................          [ 46%]
  testes/test_congelamento.py .................                            [ 48%]
  testes/test_dados_reais.py ..........................................    [ 52%]
  testes/test_entrega.py .................................                 [ 55%]
  testes/test_estado.py ........................................           [ 59%]
  testes/test_estatistica.py ..........                                    [ 59%]
  testes/test_fichas.py .............                                      [ 61%]
  testes/test_ficticios.py ..........................                      [ 63%]
  testes/test_formatos.py ................................................ [ 68%]
  ........................................................................ [ 74%]
  ........................................................................ [ 81%]
  ......................................................................   [ 88%]
  testes/test_gasto.py ..............                                      [ 89%]
  testes/test_modelo_local.py ..........................                   [ 91%]
  testes/test_redacao.py ......                                            [ 92%]
  testes/test_registro.py ...                                              [ 92%]
  testes/test_regras.py .......................                            [ 94%]
  testes/test_travas.py .................................................. [ 99%]
  ....                                                                     [100%]

  ============================ 1067 passed in 18.93s =============================
  saída=0
  ```

- Comandos executados: `pytest testes/test_conferencia_etapas.py` (vermelho e depois verde); `ruff format`; `ruff check --fix`; `scripts/verificar.sh`; `scripts/entregar.sh 017`. Nenhuma chamada a modelo.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_017_conferencia_parte1_2026-11-21.md
testes/test_conferencia_etapas.py
instrucoes/extracao.md
instrucoes/checklist.md
instrucoes/conferente_local.md
fabrica/conferencia/extracao.py
fabrica/conferencia/checklist.py
fabrica/conferencia/local.py
fabrica/conferencia/regras.py
docs/docs/pendencias_para_o_computador.md
docs/docs/doc_017_conferencia_parte1_2026-11-21.md
docs/PLAN.md

Brief 017: conferência, parte 1

Etapas de extração (Haiku, esquema Extracao), programas (regras,
citações e dado real sobre o rascunho), checklist (itens do tipo pelo
catálogo, com as citações não resolvidas como pergunta) e conferente
local (médio e alto, e 2 das 10 de risco baixo pela semente da rodada).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Partes dos pedidos.** Extração: instruções, a lista de naturezas de pedido do tipo (na parte `estrutura`) e o rascunho (`conteudo`); a extração não vê a ficha. Checklist: instruções, a lista de itens com pergunta e eliminatório e as perguntas das citações não resolvidas (em JSON, na parte `estrutura`), o trecho da tabela, a ficha e o rascunho. Conferente local: instruções, os itens do tipo, a ficha e o rascunho.
  2. **Checklist incompleto:** a resposta que não traz exatamente os itens pedidos volta "fora do formato" (o condutor faz o `t2` e, depois, reprova por formato).
  3. **Itens da etapa programas:** os do catálogo do tipo, na ordem do catálogo, menos `semelhanca` (brief 018). `dado_real` usa o detector com os marcadores fixos, as ruas e os textos de endereço e de processo da ficha, os reais permitidos e proibidos, os títulos da estrutura e os DDDs inexistentes; a lista oficial de códigos de banco fica vazia.
  4. **Sorteio do conferente local no risco baixo:** `round(fracao_pecas_risco_baixo × quantidade)` casas entre 1 e a quantidade, com `random.Random("<semente>:<tipo>:conferente_local")`. A ficha nova de uma casa herda a casa (lida da base); a cópia do teste dos conferentes usa a casa da original.
  5. **Teto de saída do conferente local:** 2000 tokens, constante provisória (a configuração não traz essa tarefa). O `num_ctx` é o da configuração, enviado por `modelo_local.py`.
  6. **A ficha da cópia** do teste dos conferentes é a da original (`caminho_ficha` usa rodada, tipo e número).
  7. **Para o brief 023 consolidar:** os três módulos, as três instruções e `testes/test_conferencia_etapas.py` na árvore da ARQUITETURA.
