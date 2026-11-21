# Relatório do brief 003 — Contratos de dados

- Data: 2026-11-21
- Brief: `docs/briefs/brief_003_contratos_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.**

## RELATÓRIO FINAL

- Brief executado: 003 — Contratos de dados (Fase 3).

- Arquivos criados:
  - `docs/briefs/brief_003_contratos_2026-11-21.md` — o brief, literal;
  - `docs/adr/adr_001_convencoes_da_construcao_2026-11-21.md` — o registro de decisões, com o conteúdo literal do brief;
  - `fabrica/comum/__init__.py` — o pacote das partes comuns;
  - `fabrica/comum/formatos.py` — todos os contratos de dados (Pydantic, base com campo a mais proibido, tipos estritos e objetos imutáveis), as listas fechadas do brief e a função `esquema_resposta(modelo)`;
  - `testes/test_formatos.py` — o teste de aceite, escrito antes do código;
  - `docs/docs/doc_003_contratos_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `pyproject.toml` — acrescentada só a seção `[tool.pytest.ini_options]` com `pythonpath = ["."]` e `testpaths = ["testes"]`. **Registro pedido pelo brief:** o `pyproject.toml` entregue pelo 001 estava incompleto nesse ponto (sem a seção, o `pytest testes` do gate não acha o pacote `fabrica`). Nenhuma outra linha mudou.
  - `docs/PLAN.md` — Resumo; 003 do Backlog para o Done; hash do 002 (`5a59957` e `f803483`) no Done.

- Arquivos preservados literalmente na área afetada: `config/`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`, `fabrica/__main__.py`, `testes/test_entrega.py`.

- Testes rodados e resultado (com a saída colada):

  Primeiro o teste, sem o código (vermelho, como manda o AGENTS):

  ```text
  E   ImportError: cannot import name 'formatos' from 'fabrica.comum' (/home/user/pet_sint/fabrica/comum/__init__.py)
  =========================== short test summary info ============================
  ERROR testes/test_formatos.py
  !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
  1 error in 0.12s
  ```

  Com o código, a primeira rodada achou um caso do próprio teste: o campo `valor` da `Condicao` aceita texto, número, sim/não ou vazio por desenho (é o valor comparado na trava, ARQUITETURA §2.2), então a troca de tipo não vale para ele. O teste passou a declarar essa exceção (`CAMPOS_LIVRES`) e a trocar também números com casas (`semelhanca`, `limite`) por texto. Gate final (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  19 files already formatted
  == mypy fabrica
  Success: no issues found in 4 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 295 items
  
  testes/test_entrega.py .................................                 [ 11%]
  testes/test_formatos.py ................................................ [ 27%]
  ........................................................................ [ 51%]
  ........................................................................ [ 76%]
  ......................................................................   [100%]
  
  ============================= 295 passed in 1.83s ==============================
  ```

- Comandos executados: `pytest testes/test_formatos.py` (vermelho e depois verde); `ruff format`; `scripts/verificar.sh`; `scripts/entregar.sh 003`. Nenhuma chamada à API da Claude nem ao modelo local.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_003_contratos_2026-11-21.md
docs/adr/adr_001_convencoes_da_construcao_2026-11-21.md
fabrica/comum/__init__.py
fabrica/comum/formatos.py
testes/test_formatos.py
pyproject.toml
docs/docs/doc_003_contratos_2026-11-21.md
docs/PLAN.md

Brief 003: contratos de dados

Todos os formatos da fábrica em fabrica/comum/formatos.py, com campo a
mais proibido, tipos estritos e as listas fechadas dos canônicos; esquema
das respostas estruturadas por esquema_resposta(). Teste de aceite em
testes/test_formatos.py. pyproject.toml ganha a seção do pytest.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Formatos intermediários antecipados.** Os briefs seguintes, quase todos, não podem tocar em `formatos.py` (só 004, 015, 020 e 022 acrescentam). Por isso este brief já cria os formatos dos arquivos intermediários que os canônicos descrevem e que os módulos seguintes vão gravar: `EstruturaMontada` (ARQUITETURA §2.3), `ResultadoProgramas`, `Alerta`, `Divergencia`, `CitacaoResolvida` e `CitacaoNaoResolvida` (§5.6 e §5.7), `ResultadoConferenteLocal` (§5.12.4), `ResultadoSemelhanca` (§5.9), `CaminhoItem` (Anexo B.3), `NotasEstilo`, `Tokens`, `ParteDoPedido`, `ItemMetadados` e `RespostaAmostra`. Os campos saem das seções citadas; se um brief seguinte precisar de campo que falta, é defeito comprovado (ADR 001, item 19) ou pendência.
  2. **`Condicao.valor`** aceita texto, número inteiro, sim/não ou vazio, porque a trava compara campos de tipos diferentes (rito, valor em centavos, capaz ou preso). É a única exceção à troca de tipo do teste.
  3. **Rodada.id** segue o ADR 001 (`e01` para ensaio, `r01` para rodada): padrão `^[er]\d{2}$`.
  4. **`salario_minimo_referencia`** só existe na ficha da inicial (Anexo A.2, alçada do juizado); está em centavos.
  5. **Ramo único**: como nos briefs anteriores, a entrega vai no ramo `claude/project-thread-t7c3zg`, no mesmo pedido de integração para `main` (#2).
  6. Arquivos de teste e pastas novos deste brief, para o 023 consolidar na árvore: `fabrica/comum/` e `testes/test_formatos.py`.

- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim.
