# Relatório do brief 006 — API da Claude em dois passos

- Data: 2026-11-21
- Brief: `docs/briefs/brief_006_api_claude_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.**

## RELATÓRIO FINAL

- Brief executado: 006 — API da Claude em dois passos (Fase 4).

- Arquivos criados:
  - `docs/briefs/brief_006_api_claude_2026-11-21.md` — o brief, literal;
  - `fabrica/comum/api_claude.py` — `ApiClaude` com `gravar_pedido`, `gravar_pedido_igual` (só `t2`), `contar_tokens` e `coletar`; o cliente chega pronto por parâmetro;
  - `testes/test_api_claude.py` — o teste de aceite, com cliente falso, escrito antes do código (os 11 pontos do brief);
  - `testes/conftest.py` — o bloqueio de rede de todos os testes;
  - `docs/docs/doc_006_api_claude_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `docs/PLAN.md` — Resumo; 006 do Backlog para o Done; hash do 005 (`52ac72a`) no Done.

- Arquivos preservados literalmente na área afetada: os módulos de `fabrica/comum/` já prontos, `config/`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`. Nenhum defeito comprovado.

- **Nomes da API conferidos na versão fixada** (`anthropic==2.12.0`, no pacote instalado): `messages.create` aceita `max_tokens` e `output_config`; `output_config` tem `effort` (`low`, `medium`, `high`, `xhigh`, `max`) e `format` (`{"type": "json_schema", "schema": ...}`); `messages.count_tokens` aceita `model`, `messages` e `output_config`. Os três nomes dos canônicos existem; nada foi trocado.

- Testes rodados e resultado (com a saída colada):

  Primeiro o teste, sem o código (vermelho):

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_api_claude.py'.
  E   ModuleNotFoundError: No module named 'fabrica.comum.api_claude'
  ```

  Com o código, uma falha do próprio teste: esta máquina não tem IPv6, e abrir um soquete IPv6 de verdade falha antes do bloqueio. O teste do IPv6 passou a chamar o bloqueio com um objeto que diz ser IPv6, sem abrir soquete; o bloqueio olha só a família do endereço. Gate final (`scripts/verificar.sh`), inteiro verde com o bloqueio de rede ligado:

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  40 files already formatted
  == mypy fabrica
  Success: no issues found in 11 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 645 items

  testes/test_api_claude.py ...............................                [  4%]
  testes/test_arquivos.py ..................                               [  7%]
  testes/test_config.py .................................................. [ 15%]
  ........................................................................ [ 26%]
  ........................................................................ [ 37%]
  ...............................................................          [ 47%]
  testes/test_congelamento.py .................                            [ 50%]
  testes/test_entrega.py .................................                 [ 55%]
  testes/test_estatistica.py ..........                                    [ 56%]
  testes/test_formatos.py ................................................ [ 64%]
  ........................................................................ [ 75%]
  ........................................................................ [ 86%]
  ......................................................................   [ 97%]
  testes/test_gasto.py ..............                                      [ 99%]
  testes/test_registro.py ...                                              [100%]

  ============================= 645 passed in 6.53s ==============================
  ```

- Comandos executados: conferência dos nomes no pacote instalado (leitura dos arquivos de `anthropic/`); `pytest testes/test_api_claude.py` (vermelho e depois verde); `ruff format`; `scripts/verificar.sh`; `scripts/entregar.sh 006`. Nenhuma chamada à API da Claude nem ao modelo local.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_006_api_claude_2026-11-21.md
fabrica/comum/api_claude.py
testes/test_api_claude.py
testes/conftest.py
docs/docs/doc_006_api_claude_2026-11-21.md
docs/PLAN.md

Brief 006: API da Claude em dois passos

api_claude.py grava o pedido e só depois coleta: conta os tokens, pede
autorização ao gasto, envia com até 3 novas tentativas (30, 120 e 480 s),
grava a resposta como chegou e registra a chamada. testes/conftest.py
bloqueia a rede em todos os testes.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Para o brief 008 (montagem do cliente):** o pacote `anthropic` faz novas tentativas sozinho por padrão. O cliente precisa ser montado com `max_retries=0`, para que valham só as três novas tentativas deste módulo (30, 120 e 480 segundos).
  2. **Forma do envio:** as partes vão como blocos de texto de uma única mensagem do usuário, na ordem fixa (instruções, estrutura, trecho, ficha; depois motivo e conteúdo, que as etapas de refação e de conferência usam). Não há instrução de sistema separada, porque os canônicos não pedem e o cache está fora do MVP.
  3. **Situações:** recusa (`refusal`) e cortada (`max_tokens` ou `model_context_window_exceeded`) voltam com o próprio nome; `fora_do_formato(situação)` diz sim para as três (fora do formato, recusa, cortada), para `estado.py` (008) decidir o `t2`.
  4. **Erro que não é de rede, de limite nem de sobrecarga** (por exemplo, pedido mal formado): não se repete; `coletar` para com `ErroApi`, cuja mensagem leva só o tipo do erro e a situação HTTP, nunca o texto da API.
  5. **Pedidos pendentes no gasto:** no modo `uma_a_uma`, nenhum pedido fica enviado e não coletado; `coletar` passa a lista vazia a `gasto.py`.
  6. **Coleta repetida:** se a resposta já está gravada, `coletar` devolve a situação gravada e não envia de novo.
  7. **Cache e raciocínio nos tokens:** cache soma leitura e criação; raciocínio vem de `output_tokens_details.thinking_tokens` (zero quando a API não informa); `saida` é o total de saída da API, que já inclui o raciocínio (como `gasto.py` espera).
  8. Arquivo de teste novo para o 023 consolidar: `testes/conftest.py`.
  9. **Ramo único**, como nos briefs anteriores (pedido de integração #2).

- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim.
