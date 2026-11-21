# Relatório do brief 002 — Configuração do MVP travada

- Data: 2026-11-21
- Brief: `docs/briefs/brief_002_configuracao_2026-11-21.md` (texto da versão 5 dos briefs, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21**, com a conferência do responsável registrada na seção "Conferência do responsável" (no fim). A conferência da máquina continua pendente, porque só roda no computador dele.

## RELATÓRIO FINAL

- Brief executado: 002 — Configuração do MVP travada (Fase 2), até a parada.

- Arquivos criados:
  - `docs/briefs/brief_002_configuracao_2026-11-21.md` — o brief, gravado antes de ser executado: o bloco de cabeçalho e o restante da seção do brief 002 da versão 5, literais;
  - `config/config.toml` — as chaves e os valores do brief, literais, com o comentário de origem acrescentado em cada valor que ainda não o tinha;
  - `config/gasto.toml` — alerta de 3000 e corte de 10000 centavos de dólar (US$ 30 e US$ 100), literais;
  - `docs/docs/doc_002_configuracao_2026-11-21.md` — este relatório.

- Arquivos alterados (com resumo da mudança em uma linha cada):
  - `docs/PLAN.md` — Resumo com o 002 parado e o hash `2fb2f12` do 001; 002 do Backlog para o Doing; hash do 001 no Done; pendência da conferência nas Pendências de Sidarta Borges.

- Arquivos preservados literalmente na área afetada: `fabrica/`, `testes/`, `AGENTS.md`, `docs/ARQUITETURA.md`, `docs/PLANO.md` e todos os demais arquivos do brief 001.

- Testes rodados e resultado (com a saída colada):

  Os valores dos dois arquivos foram conferidos contra os blocos do brief por programa (leitor de TOML do Python 3.12, `tomllib`): os dois arquivos leem sem erro, e os valores lidos são idênticos aos dos blocos do brief (só os comentários diferem):

  ```text
  19 ['amostras', 'ancora', 'api', 'comparacao', 'criterios', 'ddds', 'erros', 'fichas', 'janela_local', 'matriz', 'modelo_local', 'modelos', 'plano_b', 'referencias_legais', 'semelhanca', 'tarefas', 'trecho', 'valvula', 'volume'] {'alerta_centavos': 3000, 'corte_centavos': 10000}
  valores iguais aos do brief
  ```

  Gate (`scripts/verificar.sh`), que o brief não pode quebrar:

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  13 files already formatted
  == mypy fabrica
  Success: no issues found in 2 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 33 items

  testes/test_entrega.py .................................                 [100%]

  ============================== 33 passed in 1.43s ==============================
  saída=0
  ```

- Comandos executados: extração dos blocos do brief e conferência dos valores com `tomllib` (script de uma vez, fora do repositório); `scripts/verificar.sh`; `scripts/entregar.sh 002`. Nenhuma chamada à API da Claude nem ao modelo local.

- Lista de arquivos para `git add` e texto do commit:

```
docs/docs/doc_002_configuracao_2026-11-21.md
docs/PLAN.md

Brief 002: conferência do responsável registrada

O responsável aprovou a configuração como está escrita e autorizou seguir
a fila. Valores sem resposta ficam com o provisório, registrado como
decisão por falta de resposta. A conferência da máquina continua pendente.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

  (Primeira entrega deste brief: commit `5a59957`, com `config/config.toml`, `config/gasto.toml`, o brief, este relatório e `docs/PLAN.md`.)

- Pendências e decisões que ficaram abertas:
  1. **Conferência do responsável** (abaixo): todos os valores, os dois preços do Haiku acima de 100 mil tokens, a janela da conferência local, a etiqueta e o digest do `gemma3:27b`, a data da conferência dos DDDs, e a conferência da máquina.
  2. Valores marcados `# PENDENTE` no `config.toml`: `modelo_local.etiqueta_completa` e `modelo_local.digest` (vazios); `janela_local.inicio` e `janela_local.fim` (provisórios, 22:00 a 06:00); `ddds.data_conferencia` (2026-11-21, a confirmar).
  3. **10 ou 20 peças por tipo** continua em aberto (PLAN, Decisões em aberto); vale 10. Se ele escolher 20, muda só `volume.pecas_por_tipo`.
  4. **Ramo único.** Como no brief 001, esta sessão só pode enviar ao ramo `claude/project-thread-t7c3zg`: o 002 vai num commit próprio, no mesmo pedido de integração do 001.
  5. Comentários de origem: onde o brief não deu a seção exata de um valor, o comentário cita a seção da ARQUITETURA ou do PLANO que trata do grupo (por exemplo, `[criterios]` cita §5.1, §5.7 e §6). O responsável pode pedir a seção exata de qualquer valor na conferência.
  6. Auditoria independente da Fase 2 (AGENTS §11), a pedir pelo responsável depois da conferência.

- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim (na primeira entrega, o 002 ficou no Doing; nesta, vai para o Done).

## O que foi pedido ao responsável na parada (registro da primeira entrega)

O que o responsável faz, no computador:

**A. Conferir os valores** de `config/config.toml` e `config/gasto.toml`, um a um, inclusive os dois preços do Haiku acima de 100 mil tokens de entrada (50 centavos de dólar por milhão na entrada e 250 na saída, tirados da página oficial de preços da Anthropic em 2026-11-21), e dizer o que corrige.

**B. Informar** a janela da conferência local (24 horas ou menos; provisória: das 22h às 6h) e a data da conferência da lista de DDDs.

**C. Conferência da máquina** (cerca de 15 minutos, sem gastar API). O executor está na nuvem, sem o Ollama e sem a máquina do responsável: não roda nenhum destes comandos, e a ausência do Ollama na nuvem não é defeito. O responsável roda cada um e devolve o resultado, a etiqueta e o digest:

1. `python3.12 --version` responde 3.12;
2. `ollama list` mostra `gemma3:27b` (se não mostrar: `ollama pull gemma3:27b`, cerca de 17,5 GB);
3. `ollama show gemma3:27b` e anotar a etiqueta completa e o digest, que vão para o `config.toml`;
4. `curl -s http://localhost:11434/api/generate -d '{"model":"gemma3:27b","prompt":"Responda só: ok","stream":false,"options":{"num_ctx":16384}}'` responde, e `ollama ps` mostra o modelo carregado; anotar quanto tempo levou (o modelo pede memória folgada, na prática 32 GB);
5. `porteiro cabe gemma3:27b --porta 11434 --json` responde, se ele usar o `porteiro`.

Quando ele responder, uma sessão seguinte deste mesmo brief: troca os valores corrigidos e tira o `# PENDENTE` dos informados (etiqueta e digest podem ficar vazios se a máquina não tiver o Ollama: vale a válvula de escape, ARQUITETURA §5.12.4); se o `gemma3:27b` não rodar na máquina, registra no `docs/PLAN.md` a decisão que ele precisa tomar antes do ensaio (outra máquina, ou mudar a regra do risco alto na ARQUITETURA §5.12.4); acrescenta aqui a seção "## Conferência do responsável" com a data e o que ele conferiu, corrigiu ou deixou pendente; atualiza o manifesto e entrega de novo.

## Conferência do responsável

- Data: 2026-11-21.
- Resposta do responsável, Sidarta Borges, na conversa do projeto: "Aprovo pode seguir até o fim de todos os briefs sem mais aprovação futuras".
- **A. Valores:** aprovados como estão escritos em `config/config.toml` e `config/gasto.toml`, inclusive os dois preços do Haiku acima de 100 mil tokens de entrada (50 e 250 centavos de dólar por milhão). Nenhum valor foi corrigido.
- **B. Janela da conferência local e data da lista de DDDs:** o responsável não informou. **Decisão tomada por falta de resposta:** ficam os valores provisórios já escritos (janela das 22:00 às 06:00; data da conferência dos DDDs 2026-11-21). Os comentários `# PENDENTE` continuam no arquivo, para que a troca seja fácil antes do ensaio.
- **C. Conferência da máquina:** pendente. Os cinco comandos só rodam no computador do responsável, e a sessão na nuvem não os roda. Etiqueta e digest do `gemma3:27b` continuam vazios: enquanto estiverem vazios, o modelo local é tratado como indisponível e vale a válvula de escape (ARQUITETURA §5.12.4). Se a conferência mostrar que o `gemma3:27b` não roda na máquina, ele precisa decidir, antes do ensaio, entre outra máquina ou mudar a regra do risco alto (sem o modelo local, as peças de risco alto ficam em pausa e nem o ensaio nem a rodada fecham); a pendência está no `docs/PLAN.md`.
- **10 ou 20 peças por tipo:** sem resposta; fica 10, o adotado.
