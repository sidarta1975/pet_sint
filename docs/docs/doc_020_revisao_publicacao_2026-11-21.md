# Relatório do brief 020 — Revisão em duas etapas e publicação

- Data: 2026-11-21
- Brief: `docs/briefs/brief_020_revisao_publicacao_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.** `test_publicacao.py` passa no gate (nenhum arquivo sem a marca) e `test_revisao.py` mostra que a segunda etapa só é gerada depois das respostas confirmadas (critério da Fase 10).

## RELATÓRIO FINAL

- Brief executado: 020 — Revisão em duas etapas e publicação (Fase 10).

- Arquivos criados:
  - `docs/briefs/brief_020_revisao_publicacao_2026-11-21.md` — o brief, literal;
  - `testes/test_revisao.py` — os 8 pontos do aceite (10 testes); as peças de exemplo saem do fluxo de verdade com os clientes falsos do teste de integração (ensaio `e01` e a rodada `r01` com 10 manifestações, uma refeita), rodado uma vez por módulo e copiado para cada teste;
  - `testes/test_publicacao.py` — o aceite da publicação (7 testes), com o `.docx` aberto pela biblioteca;
  - `fabrica/revisao.py` — os cinco cartões, as perguntas com correção antes da confirmação, `pendente`, `revisar`, `resumo`, `concordancia` e `destino_das_respostas`;
  - `fabrica/publicacao.py` — `publicaveis`, `metadados`, `documento` (o `.docx`) e `publicar`;
  - `docs/docs/doc_020_revisao_publicacao_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `fabrica/comum/formatos.py` — só o modelo `Amostras` (rodada, cópias, descartadas, data do sorteio), como o brief declara;
  - `fabrica/comum/arquivos.py` — **defeito comprovado** (registro de decisão 001, item 19): o único acesso ao disco não gravava arquivo binário, e o `.docx` do pacote (ARQUITETURA §5.10) não tinha como ser gravado. Acrescentado `gravar_bytes`, com as mesmas regras (só em `saida/`, gravação atômica, nunca sobrescreve); nada mais mudou;
  - `fabrica/__main__.py` — os comandos `revisar`, `revisar --resumo` e `publicar --rodada <rodada>`;
  - `docs/ARQUITETURA.md` — seção 8: a linha de `publicar` e "Construído no brief 020" nas de `revisar`;
  - `docs/docs/pendencias_para_o_computador.md` — cinco linhas do 020;
  - `docs/PLAN.md` — Resumo; 020 do Backlog para o Done; hash do 019 no Done.

- Arquivos preservados literalmente na área afetada: `dados/`, `config/`, os demais módulos, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `testes/test_integracao.py` (só o 023 o estende; os testes deste brief usam as suas classes sem mudá-lo).

- Testes rodados e resultado (com a saída colada):

  Primeiro os testes, sem o código (vermelho):

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_revisao.py'.
  E   ImportError: cannot import name 'revisao' from 'fabrica' (/home/user/pet_sint/fabrica/__init__.py)
  ImportError while importing test module '/home/user/pet_sint/testes/test_publicacao.py'.
  ```

  Gate (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  114 files already formatted
  == mypy fabrica
  Success: no issues found in 32 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 1119 items

  testes/test_ancora.py ..........................                         [  2%]
  testes/test_api_claude.py ...............................                [  5%]
  testes/test_arquivos.py ..................                               [  6%]
  testes/test_citacoes.py ................................................ [ 10%]
  ............                                                             [ 12%]
  testes/test_comparacao.py .............................................. [ 16%]
  ..............................................                           [ 20%]
  testes/test_conferencia_etapas.py ..............                         [ 21%]
  testes/test_config.py .................................................. [ 26%]
  ........................................................................ [ 32%]
  ........................................................................ [ 38%]
  ...............................................................          [ 44%]
  testes/test_congelamento.py .................                            [ 46%]
  testes/test_dados_reais.py ..........................................    [ 49%]
  testes/test_decisao.py .................                                 [ 51%]
  testes/test_entrega.py .................................                 [ 54%]
  testes/test_erros_programa.py ..............                             [ 55%]
  testes/test_estado.py ........................................           [ 59%]
  testes/test_estatistica.py ..........                                    [ 59%]
  testes/test_fichas.py .............                                      [ 61%]
  testes/test_ficticios.py ..........................                      [ 63%]
  testes/test_formatos.py ................................................ [ 67%]
  ........................................................................ [ 74%]
  ........................................................................ [ 80%]
  ......................................................................   [ 86%]
  testes/test_gasto.py ..............                                      [ 88%]
  testes/test_integracao.py ....                                           [ 88%]
  testes/test_modelo_local.py ..........................                   [ 90%]
  testes/test_publicacao.py ........                                       [ 91%]
  testes/test_redacao.py ......                                            [ 92%]
  testes/test_registro.py ...                                              [ 92%]
  testes/test_regras.py .......................                            [ 94%]
  testes/test_revisao.py .........                                         [ 95%]
  testes/test_travas.py .................................................. [ 99%]
  ....                                                                     [100%]

  ============================ 1119 passed in 37.34s =============================
  saída=0
  ```

- Comandos executados: `pytest testes/test_revisao.py testes/test_publicacao.py` (vermelho e depois verde); `ruff format`; `ruff check --fix`; `mypy fabrica`; `scripts/verificar.sh`; `scripts/entregar.sh 020`. Nenhuma chamada a modelo.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_020_revisao_publicacao_2026-11-21.md
testes/test_revisao.py
testes/test_publicacao.py
fabrica/revisao.py
fabrica/publicacao.py
fabrica/comum/formatos.py
fabrica/comum/arquivos.py
fabrica/__main__.py
docs/ARQUITETURA.md
docs/docs/pendencias_para_o_computador.md
docs/docs/doc_020_revisao_publicacao_2026-11-21.md
docs/PLAN.md

Brief 020: revisão em duas etapas e publicação

Cartões de revisão (primeira etapa sem o veredito; segunda só depois da
confirmação), do ensaio, das duas amostras e da leitura de publicação;
comando revisar, com correção antes de confirmar e respostas imutáveis,
e revisar --resumo; concordância nos dois sentidos e destino de 5.12.7.
Publicação com .md, .json, .docx e índice, todos com a marca, e recusa
da peça sem a marca. Arquivos ganha gravar_bytes para o .docx.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Ids e nomes dos cartões.** Revisão: id da peça, `saida/cartoes/<peça>_etapa1.md` e `_etapa2.md`. Ensaio: id da peça, `<peça>_ensaio.md`. Amostras: `<rodada>_amostra_copias` e `<rodada>_amostra_descartadas`. Leitura: `<peça>_v<k>_leitura_publicacao`. As respostas vão sempre para `<id>_respostas.json`. As amostras sorteadas são lidas de `saida/erros/<rodada>_amostras.json` (`revisao.caminho_amostras`), que o 021 grava.
  2. **Quando o cartão fica pendente:** o do ensaio e o de revisão, quando a primeira versão tem veredito (a conferência terminou); a amostra, quando o arquivo de amostras traz cópias; a leitura, quando a fábrica aprovou uma v2 ou v3 e o responsável aprovou a ficha.
  3. **Perguntas.** Revisão: ficha, peça, dado real (com o trecho, se sim) e as citações que escaparam da lista (separadas por ponto e vírgula). Ensaio: formato certo (e o que saiu errado, se não) e dado real. Amostra de cópias: para cada cópia, se o erro existe e, se existe, se é o do gabarito. Descartadas: se o erro pedido existe. Leitura: se a versão pode ser publicada e dado real. Resposta fora das opções é perguntada de novo; antes de confirmar, o número da pergunta a corrige.
  4. **Alertas da segunda etapa:** cada resposta "não passa" do caminho de cada item, com a origem (programa de regras, citações, dados reais, semelhança, checklist do Haiku, conferente local ou Opus), e os alertas gravados no veredito. "Aprovou por pouco" não tem medida na conferência e fica fora.
  5. **Concordância:** gravada em `saida/cartoes/<peça>_concordancia.json` na confirmação: o sentido (`concordam`, `so_a_fabrica_aprovou`, `so_o_responsavel_aprovou`, vazio com a ficha reprovada), o destino de 5.12.7 e, à parte, a versão e o destino final da fábrica.
  6. **Publicação:** peça com "sim" na pergunta de dado real não é publicada; o índice é `saida/pacotes/<tipo>/indice_<rodada>.md` (no ensaio, `indice.md`); rodar de novo não regrava nada; a marca é conferida em todas as peças antes de gravar o primeiro arquivo. No ensaio vai a versão aprovada pela fábrica ou, sem ela, a primeira.
  7. **Para o brief 023 consolidar:** `revisao.py`, `publicacao.py`, `test_revisao.py` e `test_publicacao.py` na ARQUITETURA.
