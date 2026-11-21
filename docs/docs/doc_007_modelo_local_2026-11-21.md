# Relatório do brief 007 — Modelo local

- Data: 2026-11-21
- Brief: `docs/briefs/brief_007_modelo_local_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.**

## RELATÓRIO FINAL

- Brief executado: 007 — Modelo local (Fase 4).

- Arquivos criados:
  - `docs/briefs/brief_007_modelo_local_2026-11-21.md` — o brief, literal;
  - `fabrica/comum/modelo_local.py` — `ModeloLocal` com `consultar_porteiro`, `estimar_tokens` e `conferir`; o processo do `porteiro` e o HTTP do Ollama chegam por parâmetro (por padrão: `subprocess` e `urllib` da biblioteca padrão, sem biblioteca nova);
  - `testes/test_modelo_local.py` — o teste de aceite, com o `porteiro` e o Ollama falsos, escrito antes do código (os 6 pontos do brief);
  - `docs/docs/doc_007_modelo_local_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `docs/PLAN.md` — Resumo; 007 do Backlog para o Done; hash do 006 no Done.

- Arquivos preservados literalmente na área afetada: os módulos de `fabrica/comum/` já prontos, `config/`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`. Nenhum defeito comprovado.

- Testes rodados e resultado (com a saída colada):

  Primeiro o teste, sem o código (vermelho):

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_modelo_local.py'.
  E   ModuleNotFoundError: No module named 'fabrica.comum.modelo_local'
  ```

  Gate final (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  44 files already formatted
  == mypy fabrica
  Success: no issues found in 12 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 671 items

  testes/test_api_claude.py ...............................                [  4%]
  testes/test_arquivos.py ..................                               [  7%]
  testes/test_config.py .................................................. [ 14%]
  ........................................................................ [ 25%]
  ........................................................................ [ 36%]
  ...............................................................          [ 45%]
  testes/test_congelamento.py .................                            [ 48%]
  testes/test_entrega.py .................................                 [ 53%]
  testes/test_estatistica.py ..........                                    [ 54%]
  testes/test_formatos.py ................................................ [ 61%]
  ........................................................................ [ 72%]
  ........................................................................ [ 83%]
  ......................................................................   [ 93%]
  testes/test_gasto.py ..............                                      [ 95%]
  testes/test_modelo_local.py ..........................                   [ 99%]
  testes/test_registro.py ...                                              [100%]

  ============================= 671 passed in 6.32s ==============================
  ```

- Comandos executados: `pytest testes/test_modelo_local.py` (vermelho e depois verde); `ruff check --fix` (ordem de uma importação); `ruff format`; `scripts/verificar.sh`; `scripts/entregar.sh 007`. Nenhum processo `porteiro` nem `ollama` de verdade; nenhuma chamada à API.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_007_modelo_local_2026-11-21.md
fabrica/comum/modelo_local.py
testes/test_modelo_local.py
docs/docs/doc_007_modelo_local_2026-11-21.md
docs/PLAN.md

Brief 007: modelo local

modelo_local.py consulta o porteiro (0 rodou; 1 espera a cada minuto por
até 15; o resto indisponível), estima o tamanho de forma pessimista, manda
o num_ctx sempre explícito e o esquema no formato do Ollama, e só informa
o resultado. Nunca inicia, para ou descarrega o Ollama.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Nome do modelo:** o `porteiro` e o Ollama recebem a `etiqueta_completa` do `config.toml` (a versão exata). Enquanto ela ou o digest estiverem vazios, o resultado é indisponível sem chamar nada, com a causa `falha` (a lista fechada de causas não tem "sem configuração"). O digest não é conferido contra o Ollama, porque o brief só permite o comando do `porteiro` e o pedido de conversa.
  2. **Pedido ao Ollama:** `POST http://127.0.0.1:11434/api/chat`, com `model`, `messages` (as partes do pedido juntas, na ordem gravada), `format` (o esquema), `options` (`num_ctx` da configuração e `num_predict` igual ao teto de saída do pedido) e `stream` falso. O acesso padrão ignora qualquer proxy da máquina, para que o pedido vá direto ao Ollama local.
  3. **Sem tempo-limite no HTTP:** a ARQUITETURA não dá valor para o tempo máximo de uma resposta do Ollama; o acesso padrão espera sem limite. Se o responsável quiser um limite, ele entra no `config.toml` (pendência para depois do ensaio, que mede o tempo real).
  4. **Ordem das conferências em `conferir`:** primeiro a configuração, depois o `porteiro`, depois o tamanho; o resultado sempre leva a fração do `num_ctx` (estimativa dividida pelo `num_ctx`), para `estado.py` aplicar a regra dos 75% no ensaio.
  5. **Falha do Ollama** (erro de conexão, resposta sem conteúdo) vira indisponível com a causa `falha`; resposta encerrada por tamanho (`done_reason` `length`) ou fora do esquema vira fora do formato, gravada como chegou.
  6. **Registro:** cada conversa com o Ollama vira uma linha em `chamadas.jsonl` com a tarefa `conferente_local` e custo zero, para o relatório ter a duração.
  7. **Ramo único**, como nos briefs anteriores (pedido de integração #2).

- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim.
