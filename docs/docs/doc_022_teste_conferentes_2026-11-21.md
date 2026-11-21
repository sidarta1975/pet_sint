# Relatório do brief 022 — Teste dos conferentes

- Data: 2026-11-21
- Brief: `docs/briefs/brief_022_teste_conferentes_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.** `test_teste_conferentes.py` passa no gate, com dados falsos, e calcula as cinco taxas com a margem de Wilson. O critério da Fase 11 fecha no brief 023.

## RELATÓRIO FINAL

- Brief executado: 022 — Teste dos conferentes (Fase 11).

- Arquivos criados:
  - `docs/briefs/brief_022_teste_conferentes_2026-11-21.md` — o brief, literal;
  - `testes/test_teste_conferentes.py` — os 8 pontos do aceite (10 testes). O banco, as respostas das amostras e as conferências do teste são falsos, escritos no teste nos formatos do 019, 020, 021 e 018;
  - `fabrica/teste_conferentes.py` — `faltas`, `fechar_banco`, `registrar`, `refs_do_teste`, `coletar` (a parte do `avancar`), `avaliar` (a regra do pego), `calcular` (as taxas) e `testar` (o comando, retomável);
  - `docs/docs/doc_022_teste_conferentes_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `fabrica/comum/formatos.py` — o modelo `ResultadoTeste`, com as partes dele (`TaxaTeste`, `BancoTeste` e `CopiaTeste`), como o brief declara;
  - `fabrica/__main__.py`:
    - o comando `testar --rodada <rodada>`;
    - **fora da parte que o brief libera:** o `avancar` também chama `teste_conferentes.coletar`, com a mesma lista `ETAPAS`. É o que o brief pede ("registra as peças do teste para o `avancar`"), e o condutor só descobre sozinho as peças com pedido de ficha. `estado.py` não mudou;
  - `docs/ARQUITETURA.md` — seção 8: a linha de `testar`;
  - `docs/docs/pendencias_para_o_computador.md` — sete linhas do 022;
  - `docs/PLAN.md` — Resumo; 022 do Backlog para o Done; hash do 021 no Done.

- Arquivos preservados literalmente na área afetada: `fabrica/revisao.py`, `fabrica/estado.py`, os módulos de `conferencia/`, `dados/`, `config/`, `scripts/`, `AGENTS.md` e `docs/PLANO.md`.

- Como funciona:
  1. **Recusa.** Sem `saida/erros/<rodada>_amostras.json`, o `testar` recusa e manda rodar `erros` e `avancar`. Também recusa, dizendo qual falta, sem as respostas confirmadas da amostra de cópias ou da amostra das descartadas, quando a amostra tem alguma cópia.
  2. **Fechamento do banco**, uma vez:
     - `saida/erros/<rodada>_gabarito.json` guarda todos os gabaritos da rodada (programa e Opus), com `amostra` igual a `aceita` (o erro existe e é o do gabarito) ou `rejeitada`, ou vazio fora da amostra;
     - `<rodada>_descartadas.json` guarda as descartadas, com `erro_existe` ou `erro_nao_existe` nas da amostra;
     - a rejeitada sai do banco, e as descartadas não voltam;
     - na rodada, o banco é marcado não confiável com 2 ou mais rejeitadas (`criterios.rejeitadas_para_banco_nao_confiavel`), e filtrado pelo verificador com o erro existindo em 2 ou mais descartadas (`criterios.existentes_para_banco_filtrado`); no ensaio, as marcas não se aplicam;
     - as chamadas seguintes só leem os dois arquivos.
  3. **Peças do teste.**
     - Cada cópia do banco e cada original, conferida de novo, ganha o texto em `saida/rascunhos/teste_<cópia ou peça>_v1.md`.
     - A referência do condutor tem a rodada, o tipo e o número da original, para que a ficha e o sorteio do conferente local sejam os dela, e o id `teste_<nome>`. Assim, todos os arquivos da conferência levam o prefixo (`saida/conferencias/teste_<nome>_v1_<etapa>.json`).
     - O `avancar` leva essas peças pela mesma lista `ETAPAS` (018), com os serviços em modo de teste (`servicos_do_teste`): a semelhança grava "desligada" sem ninguém mexer no `config.toml`, o veredito "refazer" encerra a peça (sem refação) e a ficha, a redação e o retorno não se aplicam a cópias.
     - É às cegas: o pedido leva o texto e a ficha, e nenhum nome de cópia ou de peça.
  4. **Pego** (ARQUITETURA §5.1). Uma cópia só conta como pega quando três coisas acontecem juntas:
     - a cópia não foi aprovada;
     - um item aceito do gabarito tem resposta final "não passa" na cópia;
     - esse mesmo item tem resposta final "passa" na original, conferida de novo no teste.

     A cópia sem veredito, porque o condutor a encerrou por formato, conta como não pega e vai para `nao_pegas_formato`. A original sem veredito não dá item que passou, e as cópias dela ficam não pegas.
  5. **As cinco taxas**, cada uma com `wilson` de `estatistica.py`:
     - **critério central:** as cópias do Opus no banco. A decisão é:
       - `nao_decide` quando o banco não é confiável;
       - `inconclusivo` sem cópias do Opus ou quando o 021 marcou a rodada como inconclusiva (plano B);
       - nos demais casos, `passa` ou `nao_passa` por `criterio_central_passa`;
     - **sem o Opus:** mesmo denominador. Conta a cópia pega em que programa, Haiku ou modelo local também marcou "não passa" num item pego. Como é um subconjunto, nunca passa da completa;
     - **julgamento por programa:** inconclusiva com menos de `criterios.minimo_copias_julgamento` (5);
     - **regra por programa:** `regra_sanidade_ok` só com 100%;
     - **reprovação das peças boas no teste:** só descreve. A original sem veredito conta como reprovada.
  6. **Diagnóstico.**
     - Por conferente: das cópias do banco, em quantas ele marcou "não passa" num item pego.
     - Por tipo de erro e por origem: pegas sobre o total.
  7. **Dependente do Opus:** a taxa sem o Opus fica mais de `criterios.pontos_dependencia_opus` (15) pontos abaixo da completa.
  8. **Retomada.**
     - A primeira chamada fecha o banco, registra as peças e diz quantas faltam.
     - As chamadas seguintes dizem quantas ainda faltam.
     - A última grava o resultado.
     - Depois disso, o `testar` só mostra o resultado gravado.

- Testes rodados e resultado (com a saída colada):

  Primeiro o teste, sem o código (vermelho):

  ```text
    ImportError while importing test module '/home/user/pet_sint/testes/test_teste_conferentes.py'.
  E   ImportError: cannot import name 'teste_conferentes' from 'fabrica' (/home/user/pet_sint/fabrica/__init__.py)
  ```

  Gate (`scripts/verificar.sh`):

  ```text
    == ruff check
  All checks passed!
  == ruff format --check
  122 files already formatted
  == mypy fabrica
  Success: no issues found in 33 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 1150 items

  testes/test_ancora.py ..........................                         [  2%]
  testes/test_api_claude.py ...............................                [  4%]
  testes/test_arquivos.py ..................                               [  6%]
  testes/test_citacoes.py ................................................ [ 10%]
  ............                                                             [ 11%]
  testes/test_comparacao.py .............................................. [ 15%]
  ..............................................                           [ 19%]
  testes/test_conferencia_etapas.py ..............                         [ 20%]
  testes/test_config.py .................................................. [ 25%]
  ........................................................................ [ 31%]
  ........................................................................ [ 37%]
  ...............................................................          [ 43%]
  testes/test_congelamento.py .................                            [ 44%]
  testes/test_dados_reais.py ..........................................    [ 48%]
  testes/test_decisao.py .................                                 [ 49%]
  testes/test_entrega.py .................................                 [ 52%]
  testes/test_erros_opus.py .....................                          [ 54%]
  testes/test_erros_programa.py ..............                             [ 55%]
  testes/test_estado.py ........................................           [ 59%]
  testes/test_estatistica.py ..........                                    [ 60%]
  testes/test_fichas.py .............                                      [ 61%]
  testes/test_ficticios.py ..........................                      [ 63%]
  testes/test_formatos.py ................................................ [ 67%]
  ........................................................................ [ 74%]
  ........................................................................ [ 80%]
  ......................................................................   [ 86%]
  testes/test_gasto.py ..............                                      [ 87%]
  testes/test_integracao.py ....                                           [ 87%]
  testes/test_modelo_local.py ..........................                   [ 90%]
  testes/test_publicacao.py ........                                       [ 90%]
  testes/test_redacao.py ......                                            [ 91%]
  testes/test_registro.py ...                                              [ 91%]
  testes/test_regras.py .......................                            [ 93%]
  testes/test_revisao.py .........                                         [ 94%]
  testes/test_teste_conferentes.py ..........                              [ 95%]
  testes/test_travas.py .................................................. [ 99%]
  ....                                                                     [100%]

  ============================ 1150 passed in 47.25s =============================
  saída=0
  ```

- Comandos executados: `pytest testes/test_teste_conferentes.py` (vermelho e depois verde); `ruff format`; `ruff check --fix`; `scripts/verificar.sh`; `scripts/entregar.sh 022`. Nenhuma chamada a modelo.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_022_teste_conferentes_2026-11-21.md
testes/test_teste_conferentes.py
fabrica/teste_conferentes.py
fabrica/comum/formatos.py
fabrica/__main__.py
docs/ARQUITETURA.md
docs/docs/pendencias_para_o_computador.md
docs/docs/doc_022_teste_conferentes_2026-11-21.md
docs/PLAN.md

Brief 022: teste dos conferentes

Comando testar, retomável: recusa sem as duas amostras respondidas, fecha
o banco uma vez (gabarito e descartadas com a amostra; marcas de banco não
confiável e filtrado, fora do ensaio), registra as cópias e as originais
para o avancar levar pela conferência em modo de teste, às cegas, e grava
as cinco taxas com a margem de Wilson, o diagnóstico e a marca de
dependente do Opus. Modelo ResultadoTeste em formatos.py.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **O `avancar` leva as peças do teste**, fora da parte de `__main__.py` que o brief libera (mesma razão do 021).
  2. **Nomes por rodada.** Os arquivos consolidados são `saida/erros/<rodada>_gabarito.json` e `<rodada>_descartadas.json`, porque o ensaio e a rodada fecham bancos diferentes e nada se sobrescreve. O resultado da rodada é `saida/relatorios/teste_conferentes.json`, como manda a ARQUITETURA; o do ensaio é `teste_conferentes_ensaio_<rodada>.json`.
  3. **Os modelos dos dois consolidados** (listas de `Gabarito` e de `Descartada`) ficam em `teste_conferentes.py`, porque o brief só libera `ResultadoTeste` em `formatos.py`. O 023 pode levá-los para `formatos.py`.
  4. **Amostra rejeitada:** a cópia em que o erro não existe, ou existe mas não é o do gabarito.
  5. **Original sem veredito no teste** (encerrada por formato): as cópias dela ficam não pegas, e ela conta como reprovada na taxa das peças boas.
  6. **Diagnóstico por conferente:** conta "não passa" do conferente num item pego, sobre todas as cópias do banco.
  7. **Às cegas:** o pedido não leva nomes, mas os arquivos em `saida/` levam o nome da cópia, para que o resultado ligue cada cópia ao gabarito.
  8. **Para o brief 023 consolidar:** `teste_conferentes.py` e `test_teste_conferentes.py` na ARQUITETURA; a coleta do teste no `avancar`.
