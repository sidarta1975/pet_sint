# Relatório do brief 011 — Montagem da estrutura, matriz e travas

- Data: 2026-11-21
- Brief: `docs/briefs/brief_011_estrutura_matriz_travas_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.** `test_travas.py` passa no gate, inclusive a recusa da montagem sem bloco obrigatório (parte do critério da Fase 6).

## RELATÓRIO FINAL

- Brief executado: 011 — Montagem da estrutura, matriz e travas (Fase 6).

- Arquivos criados:
  - `docs/briefs/brief_011_estrutura_matriz_travas_2026-11-21.md` — o brief, literal;
  - `fabrica/matriz.py` — avaliação das oito operações (`condicao_vale`), travas violadas (`violacoes`, com os campos que a ficha ainda vai preencher), conferência da escrita de cada trava (`conferir_trava`), visão das travas da ficha e da combinação, sorteio das combinações (`sortear`), combinação do ensaio, sorteio das datas (`sortear_datas`), `termo_final` e `eh_dia_util` (a única contagem de dias úteis do código) e `prazo_da_manifestacao`;
  - `fabrica/estruturas.py` — montagem da estrutura em três níveis (`montar`, `faltando`, `em_markdown`), `trecho_da_tabela` e a preparação (`preparar`);
  - `testes/test_travas.py` — o teste de aceite (os 9 pontos do brief), escrito antes do código, com todos os dados de exemplo dentro do teste;
  - `docs/docs/doc_011_estrutura_matriz_travas_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `fabrica/__main__.py` — o comando `preparar` (com `--semente N` opcional) na lista de comandos;
  - `docs/ARQUITETURA.md` — só a seção 8: a linha do comando `python -m fabrica preparar`, marcada "Construído no brief 011";
  - `docs/PLAN.md` — Resumo; 011 do Backlog para o Done; hash do 010 no Done.

- Arquivos preservados literalmente na área afetada: `fabrica/comum/` (nenhum defeito comprovado), `fabrica/ficticios.py`, `fabrica/conferencia/`, `config/`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `testes/dados/reais_reservados.json` (só lido). `dados/` continua sem existir (nasce no 014).

- Testes rodados e resultado (com a saída colada):

  Primeiro o teste, sem o código (vermelho):

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_travas.py'.
  E   ImportError: cannot import name 'estruturas' from 'fabrica' (/home/user/pet_sint/fabrica/__init__.py)
  ```

  Com o código, os 54 casos passaram; o mypy pediu que a constante "volta para a preparação" fosse marcada como fixa (`Final`). Gate final (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  63 files already formatted
  == mypy fabrica
  Success: no issues found in 18 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 833 items

  testes/test_api_claude.py ...............................                [  3%]
  testes/test_arquivos.py ..................                               [  5%]
  testes/test_config.py .................................................. [ 11%]
  ........................................................................ [ 20%]
  ........................................................................ [ 29%]
  ...............................................................          [ 36%]
  testes/test_congelamento.py .................                            [ 38%]
  testes/test_dados_reais.py ..........................................    [ 43%]
  testes/test_entrega.py .................................                 [ 47%]
  testes/test_estado.py ........................................           [ 52%]
  testes/test_estatistica.py ..........                                    [ 53%]
  testes/test_ficticios.py ..........................                      [ 56%]
  testes/test_formatos.py ................................................ [ 62%]
  ........................................................................ [ 71%]
  ........................................................................ [ 79%]
  ......................................................................   [ 88%]
  testes/test_gasto.py ..............                                      [ 90%]
  testes/test_modelo_local.py ..........................                   [ 93%]
  testes/test_registro.py ...                                              [ 93%]
  testes/test_travas.py .................................................. [ 99%]
  ....                                                                     [100%]

  ============================= 833 passed in 14.95s =============================
  saída=0
  ```

- Comandos executados: `pytest testes/test_travas.py` (vermelho e depois verde); `ruff format`; `ruff check --fix`; `scripts/verificar.sh`; `scripts/entregar.sh 011`. Nenhuma chamada a modelo. O comando `preparar` só rodou dentro do teste, sobre dados de exemplo em pasta temporária.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_011_estrutura_matriz_travas_2026-11-21.md
fabrica/matriz.py
fabrica/estruturas.py
fabrica/__main__.py
testes/test_travas.py
docs/ARQUITETURA.md
docs/docs/doc_011_estrutura_matriz_travas_2026-11-21.md
docs/PLAN.md

Brief 011: estrutura, matriz e travas

matriz.py avalia as travas do Anexo A.5, sorteia as combinações com
semente, teto por matéria e contagens fixas, sorteia as datas de 2026 com
folga no prazo e tem a única contagem de dias úteis. estruturas.py monta a
estrutura em três níveis, recusa bloco obrigatório retirado e forma o
trecho da tabela. O comando preparar valida dados/ e grava a preparação.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Campos que só a ficha preenche** (`valor_causa_centavos`, `alcada_centavos`, `defeito.ancora.argumento_id`, `defeito.trecho_mencao`, `novo_endereco`, `meio_nova_diligencia`): na combinação sorteada ficam vazios e as travas que os **exigem** não são cobradas ainda (`CAMPOS_DA_FICHA`). As travas que **proíbem** valem sempre. `fichas.py` (015) cobra todas as travas sobre a visão da ficha pronta, sem campo pendente.
  2. **Campo vazio não se compara:** sobre um campo vazio, só `vazio` e `preenchido` dão verdadeiro; as outras seis operações dão falso (assim a trava do juizado não alcança o campo que não se aplica ao tipo). Booleano não é número: `true` não é igual a `1`. Operação com valor do tipo errado (lista em `igual`, texto em `maior`) é erro de dado, apontado por `conferir_trava` no `preparar`.
  3. **A combinação sorteada** é um registro de `matriz.py` (`Combinacao`), não um formato de arquivo: não é gravada sozinha. O 015 a transforma em `casa_matriz` e nos campos da ficha. A pessoa física sorteada é sempre capaz e solta (Anexo A.1: a matriz nunca sorteia categoria proibida).
  4. **Prazo em dobro:** `pessoa_juridica_direito_publico` nunca é sorteada, em nenhum tipo (art. 183 do CPC; Anexo A.3). Empresa pública e massa falida ficam a cargo das travas do juizado.
  5. **Intervalos das datas** (decisão tomada por falta de regra no brief, a conferir pelo responsável): ajuizamento num dia útil entre 02/01 e 31/08/2026; nos embargos, decisão de 30 a 150 dias depois e intimação de 0 a 10 dias depois da decisão; na manifestação, juntada do aviso de 20 a 120 dias depois do ajuizamento e intimação da determinação de 0 a 15 dias depois da juntada; o primeiro fato entre 2 anos antes do ajuizamento e a véspera dele. Toda data caída em fim de semana ou feriado vai para o dia útil seguinte; se o termo final cair em 2027, o sorteio tenta de novo. A data da peça é um dia útil depois da intimação que deixa a folga de `dias_uteis_de_folga` antes do termo final; na petição inicial, é o próprio dia do ajuizamento.
  6. **Prazo da manifestação:** a matriz não tem eixo para "o juiz fixou prazo ou não". `sortear_datas` usa 5 dias úteis (art. 218, § 3º) quando não recebe `prazo_fixado`; o 015 passa o prazo da determinação quando a ficha tiver um.
  7. **Trecho da tabela:** a ordem dos diplomas é a ordem da lista `diplomas` da tabela; o artigo é lido como número ("1.023" vale 1023, "4º" vale 4); o parágrafo vai na ordem caput, parágrafo único e parágrafos numerados. Os pares são contados **dentro do trecho do tipo**. O texto do trecho traz, por dispositivo, o id, o diploma, o artigo, o parágrafo, a função, o assunto e o texto vigente; o 016 o usa como está. A estimativa usa o divisor e o teto do `config.toml` (`modelo_local.divisor_caracteres_por_token` e `trecho.teto_tokens`).
  8. **`preparar`:** exige os 11 arquivos fixos de `dados/`, a família e o perfil de cada tipo do catálogo e a matriz de cada tipo; o acréscimo é opcional (muitos tipos não precisam dele, ARQUITETURA §2.2). Confere ainda: teto por matéria até 25% da quantidade, quantidade igual à do catálogo, ids repetidos e diplomas sem cadastro na tabela, feriados fora de 2026. A semente de prova é 2026 (troca com `--semente N`). `testes/dados/reais_reservados.json` fica fora das pastas que `arquivos.py` lê; o `preparar` o lê direto do disco, sem mudar `fabrica/comum/`, e mostra só a contagem.
  9. **Para o brief 023 consolidar:** a pasta nova `saida/preparacao/` (com `<tipo>_estrutura.json`, `<tipo>_estrutura.md` e `resumo.md`). `testes/test_travas.py` já está na árvore da ARQUITETURA.
  10. **Ramo único**, como nos briefs anteriores (pedido de integração #2).

- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim.
