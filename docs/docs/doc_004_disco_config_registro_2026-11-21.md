# Relatório do brief 004 — Disco, configuração e registro

- Data: 2026-11-21
- Brief: `docs/briefs/brief_004_disco_config_registro_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.**

## RELATÓRIO FINAL

- Brief executado: 004 — Disco, configuração e registro (Fase 3).

- Arquivos criados:
  - `docs/briefs/brief_004_disco_config_registro_2026-11-21.md` — o brief, literal;
  - `fabrica/comum/arquivos.py` — único acesso ao disco: lê de `saida/`, `dados/`, `instrucoes/` e `config/`, grava só em `saida/`; gravação atômica (temporário `<nome>.tmp-<aleatório>`, escrita forçada no disco, troca de nome) e nunca sobrescreve; `regravar_rodadas` guarda a cópia anterior em `saida/registro/rodadas_anteriores/rodadas_<carimbo>.json`; JSON validado, texto, linha de `.jsonl` (última linha incompleta ignorada), listagem sem temporários, existência, SHA-256, e a leitura do git do ADR 001, item 6 (`rev-parse HEAD:fabrica`, `rev-parse HEAD:pyproject.toml`, `status --porcelain` com os caminhos explícitos);
  - `fabrica/comum/config.py` — lê os dois arquivos uma vez com `tomllib`, valida por `Configuracao` e `Gasto` e entrega um objeto só (`Config`); erro diz arquivo e chave;
  - `fabrica/comum/registro.py` — `saida/registro/chamadas.jsonl` e `saida/registro/ocorrencias.jsonl`, por `arquivos.py`, com leitura de volta e soma do custo;
  - `testes/test_config.py`, `testes/test_arquivos.py`, `testes/test_registro.py` — os testes de aceite, escritos antes do código;
  - `docs/docs/doc_004_disco_config_registro_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `fabrica/comum/formatos.py` — acrescentados `Configuracao` (e um modelo por tabela do `config.toml`) e `Gasto`, espelho exato das chaves; para isso a linha de importação do Pydantic ganhou `BeforeValidator`. Nenhum modelo existente mudou.
  - `docs/PLAN.md` — Resumo; 004 do Backlog para o Done; hash do 003 (`c54e877`) no Done.

- Arquivos preservados literalmente na área afetada: `config/config.toml`, `config/gasto.toml`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`, os modelos já existentes de `formatos.py`.

- Testes rodados e resultado (com a saída colada):

  Primeiro os testes, sem o código (vermelho):

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_config.py'.
  E   ImportError: cannot import name 'config' from 'fabrica.comum' (/home/user/pet_sint/fabrica/comum/__init__.py)
  ImportError while importing test module '/home/user/pet_sint/testes/test_arquivos.py'.
  E   ImportError: cannot import name 'arquivos' from 'fabrica.comum' (/home/user/pet_sint/fabrica/comum/__init__.py)
  ImportError while importing test module '/home/user/pet_sint/testes/test_registro.py'.
  E   ModuleNotFoundError: No module named 'fabrica.comum.arquivos'
  ```

  Gate final (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  27 files already formatted
  == mypy fabrica
  Success: no issues found in 7 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 573 items

  testes/test_arquivos.py ..................                               [  3%]
  testes/test_config.py .................................................. [ 11%]
  ........................................................................ [ 24%]
  ........................................................................ [ 36%]
  ...............................................................          [ 47%]
  testes/test_entrega.py .................................                 [ 53%]
  testes/test_formatos.py ................................................ [ 62%]
  ........................................................................ [ 74%]
  ........................................................................ [ 87%]
  ......................................................................   [ 99%]
  testes/test_registro.py ...                                              [100%]

  ============================= 573 passed in 2.19s ==============================
  ```

- Comandos executados: `pytest` dos três testes (vermelho e depois verde); `ruff format`; `scripts/verificar.sh`; `scripts/entregar.sh 004`. Os testes usam pasta temporária (o teste do git cria um repositório só dentro dela). Nenhuma chamada à API da Claude nem ao modelo local.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_004_disco_config_registro_2026-11-21.md
fabrica/comum/arquivos.py
fabrica/comum/config.py
fabrica/comum/registro.py
fabrica/comum/formatos.py
testes/test_config.py
testes/test_arquivos.py
testes/test_registro.py
docs/docs/doc_004_disco_config_registro_2026-11-21.md
docs/PLAN.md

Brief 004: disco, configuração e registro

arquivos.py é o único acesso ao disco, com gravação atômica e sem
sobrescrever (só rodadas.json é regravado, com cópia anterior); config.py
lê e valida os dois arquivos de configuração uma vez; registro.py grava
chamadas e ocorrências. Configuracao e Gasto acrescentados a formatos.py.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Acréscimo do método:** `testes/test_arquivos.py` e `testes/test_registro.py` são arquivos de teste novos, para o brief 023 consolidar na árvore da ARQUITETURA.
  2. **Valores pendentes e vazios:** `modelo_local.etiqueta_completa` e `modelo_local.digest` vazios são lidos como ausentes (`None`); o modelo local (brief 007) os trata como indisponível.
  3. **Lista do esforço:** `esforco` aceita `low`, `medium`, `high`, `xhigh` e `max`, os valores que a API aceita hoje; o `config.toml` só usa `low` e `medium`. `api.modo_chamada` fica como texto livre, porque os canônicos não fecham a lista.
  4. **Interrupção da gravação:** quando a gravação falha no meio, o temporário fica no disco (o teste confere isso) e é ignorado na leitura e na listagem; nada apaga temporário sobrado.
  5. **Carimbo da cópia de `rodadas.json`:** ano, mês, dia, hora, minuto, segundo e microssegundo em UTC, tirado do relógio recebido por parâmetro (o relógio de verdade entra na montagem dos serviços, brief 008).
  6. **Ramo único**, como nos briefs anteriores: entrega no ramo `claude/project-thread-t7c3zg`, no pedido de integração #2.

- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim.
