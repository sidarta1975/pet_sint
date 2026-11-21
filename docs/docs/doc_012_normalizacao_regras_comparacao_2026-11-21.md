# Relatório do brief 012 — Normalização, regras e comparação com a ficha

- Data: 2026-11-21
- Brief: `docs/briefs/brief_012_normalizacao_regras_comparacao_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.** `test_regras.py` e `test_comparacao.py` passam no gate (parte do critério da Fase 6).

## RELATÓRIO FINAL

- Brief executado: 012 — Normalização, regras e comparação com a ficha (Fase 6).

- Arquivos criados:
  - `docs/briefs/brief_012_normalizacao_regras_comparacao_2026-11-21.md` — o brief, literal;
  - `testes/dados/comparacao_exemplos.json` — cópia literal do bloco do brief (versão `2026-11-21-v2`, 88 casos), gravada antes de qualquer código;
  - `fabrica/comum/normalizacao.py` — as normalizações do Anexo D, todas sobre cópias: valor em algarismos para centavos, presença de extenso e de marca de aproximação, CEP, documentos sem pontuação, nome sem tratamento, designação da parte, comarca e juízo (sem "da Comarca de", sem artigos, "JEC" igual a "Juizado Especial Cível"), termo como palavra inteira sem diferença de maiúsculas e acentos;
  - `fabrica/conferencia/regras.py` — os itens `estrutura`, `coerencia_ficha`, `alcada`, `prazo`, `termos_inequivocos` e `marca`, cada um devolvendo um `ResultadoItem` respondido por `programa`, e `conferir`, que roda os itens pedidos na ordem pedida;
  - `testes/test_comparacao.py` — os 86 casos `"verificado_por": "regras"` do arquivo, cada um como uma extração certa mais o elemento do caso; os 2 casos de `"fichas"` ficam para o 015;
  - `testes/test_regras.py` — estrutura, alçada, prazo, termos inequívocos, marca e `conferir`, com exemplos escritos no teste;
  - `docs/docs/doc_012_normalizacao_regras_comparacao_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `docs/PLAN.md` — Resumo; 012 do Backlog para o Done; hash do 011 no Done.

- Arquivos preservados literalmente na área afetada: `fabrica/matriz.py` (só usado: `termo_final`), o resto de `fabrica/comum/` (nenhum defeito comprovado; `Extracao` já tinha todos os campos de que o brief depende), `config/`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`.

- Testes rodados e resultado (com a saída colada):

  Primeiro os dois testes, sem o código (vermelho):

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_regras.py'.
  E   ImportError: cannot import name 'normalizacao' from 'fabrica.comum' (/home/user/pet_sint/fabrica/comum/__init__.py)
  ImportError while importing test module '/home/user/pet_sint/testes/test_comparacao.py'.
  E   ImportError: cannot import name 'regras' from 'fabrica.conferencia' (/home/user/pet_sint/fabrica/conferencia/__init__.py)
  ```

  Com o código, os 112 casos dos dois arquivos passaram; o mypy pediu um tipo explícito no dicionário dos marcadores de nome. Gate final (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  69 files already formatted
  == mypy fabrica
  Success: no issues found in 20 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 945 items

  testes/test_api_claude.py ...............................                [  3%]
  testes/test_arquivos.py ..................                               [  5%]
  testes/test_comparacao.py .............................................. [ 10%]
  ...........................................                              [ 14%]
  testes/test_config.py .................................................. [ 19%]
  ........................................................................ [ 27%]
  ........................................................................ [ 35%]
  ...............................................................          [ 41%]
  testes/test_congelamento.py .................                            [ 43%]
  testes/test_dados_reais.py ..........................................    [ 48%]
  testes/test_entrega.py .................................                 [ 51%]
  testes/test_estado.py ........................................           [ 55%]
  testes/test_estatistica.py ..........                                    [ 56%]
  testes/test_ficticios.py ..........................                      [ 59%]
  testes/test_formatos.py ................................................ [ 64%]
  ........................................................................ [ 72%]
  ........................................................................ [ 79%]
  ......................................................................   [ 87%]
  testes/test_gasto.py ..............                                      [ 88%]
  testes/test_modelo_local.py ..........................                   [ 91%]
  testes/test_registro.py ...                                              [ 91%]
  testes/test_regras.py .......................                            [ 94%]
  testes/test_travas.py .................................................. [ 99%]
  ....                                                                     [100%]

  ============================= 945 passed in 14.64s =============================
  saída=0
  ```

- Comandos executados: cópia do bloco JSON do brief para `testes/dados/comparacao_exemplos.json` (script de uma vez, fora do repositório, que conferiu o JSON e os 88 casos); `pytest testes/test_regras.py testes/test_comparacao.py` (vermelho e depois verde); `ruff format`; `ruff check --fix`; `scripts/verificar.sh`; `scripts/entregar.sh 012`. Nenhuma chamada a modelo.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_012_normalizacao_regras_comparacao_2026-11-21.md
testes/dados/comparacao_exemplos.json
fabrica/comum/normalizacao.py
fabrica/conferencia/regras.py
testes/test_comparacao.py
testes/test_regras.py
docs/docs/doc_012_normalizacao_regras_comparacao_2026-11-21.md
docs/PLAN.md

Brief 012: normalização, regras e comparação com a ficha

normalizacao.py traz as normalizações do Anexo D, sempre sobre cópias.
regras.py confere estrutura, coerência com a ficha, alçada, prazo, termos
inequívocos e marca, cada item com o valor extraído e o da ficha quando
reprova. Os 86 casos de regras de comparacao_exemplos.json passam.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Valor da causa:** um valor no lugar `valor_causa` precisa ser igual ao valor da causa da ficha (não basta ser igual a outro valor de `valores[]`). Nos pedidos, vale a linha do Anexo D: igual a um valor de `valores[]`. Soma, referência legal e arredondamento só valem fora dos pedidos e do valor da causa (soma e referência legal em `fatos` e `outro`; arredondamento só em `fatos`).
  2. **Extenso:** só se procura extenso **depois** dos algarismos (assim "um total de R$ ..." não conta "um" como extenso). Sem extenso, vale o `centavos` da extração.
  3. **Datas da ficha:** todas as datas que a ficha traz, em qualquer campo (fatos, valores, processo, tentativa prévia, decisão, aviso, determinação, prazo, peças anteriores, data da peça). Os CEPs da ficha são os de todos os endereços (partes, escritório, endereço tentado e novo endereço). Os documentos são comparados com os do mesmo tipo na ficha: CPF e CNPJ com os documentos das partes; número do processo com `processo.numero_cnj`; protocolo e contrato com os identificadores das provas, o protocolo da tentativa prévia e o identificador do processo.
  4. **OAB** é comparada como o nome (minúsculas, sem acento), pela linha do Anexo D. A extração a devolve como documento do tipo `oab`.
  5. **Nome do papel `outro`:** passa só se for igual a algum nome da ficha; qualquer outro nome reprova. A designação ("o autor", "a requerida", "a parte ré") é ignorada em qualquer papel. A lista de tratamentos e de designações está em `normalizacao.py`.
  6. **Comarca e juízo ausentes na extração** não são comparados (o Anexo D só reprova diferença). A falta do endereçamento é coberta pelo item `estrutura`.
  7. **Estrutura:** títulos de segundo nível que não são da estrutura são ignorados; todos os blocos achados, obrigatórios ou não, precisam estar na ordem da estrutura. A comparação do título é sem diferença de maiúsculas, acentos e espaços.
  8. **Alçada sem valor da causa** na extração reprova (a alçada não fica demonstrada). Só a petição inicial tem `salario_minimo_referencia`; nos outros tipos, a regra da referência legal fica sem valores e `alcada` recusa ser chamada. O multiplicador 40 vem de `referencias_legais.alcada_em_salarios_minimos` do `config.toml`. **Para o 023:** `matriz.py` (011) ainda escreve o 40 no código para a visão das travas; pode passar a ler a mesma chave.
  9. **Prazo:** a data da peça precisa estar completa; data parcial ou ausente reprova. O termo final é sempre recalculado por `matriz.termo_final` com os feriados recebidos, sem confiar no `termo_final` gravado na ficha. Ficha sem prazo é erro de chamada (`ErroRegras`), porque o item só se aplica aos tipos com prazo.
  10. **Marcas de aproximação** são só as três do Anexo D ("cerca de", "aproximadamente", "mais de"); o sentido da marca não é conferido, como o brief manda.
  11. **Para o brief 023 consolidar:** os arquivos novos `fabrica/comum/normalizacao.py`, `fabrica/conferencia/regras.py`, `testes/dados/comparacao_exemplos.json`, `testes/test_regras.py` e `testes/test_comparacao.py` já estão na árvore da ARQUITETURA.
  12. **Ramo único**, como nos briefs anteriores (pedido de integração #2).

- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim.
