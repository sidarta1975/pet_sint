# Relatório do brief 026 — Testes independentes dos valores do config.toml e conferência da máquina

- Data: 2026-11-23
- Brief: `docs/briefs/brief_026_testes_independentes_da_configuracao_2026-11-23.md`, gravado antes da execução.
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-23.**

## RELATÓRIO FINAL

- Brief executado: 026 — Testes independentes dos valores do config.toml e conferência da máquina (Fase 12, preparação).

- Arquivos criados:
  - `testes/apoio_config.py` — `trocar` (troca a linha inteira de cada chave pedida, qualquer que seja o valor atual, e falha se a chave não aparecer exatamente uma vez) e `provisorio` (os valores provisórios do brief 002 mais as trocas do teste);
  - `docs/briefs/brief_026_testes_independentes_da_configuracao_2026-11-23.md` — este brief;
  - `docs/briefs/brief_024_ensaio_2026-11-21.md` e `docs/briefs/brief_025_rodada_mvp_2026-11-21.md` — o bloco de cabeçalho e as regras de cada brief, literais, da "parte 3 de 3" da versão 5;
  - `docs/docs/doc_026_testes_independentes_da_configuracao_2026-11-23.md` — este relatório.

- Arquivos alterados (com resumo da mudança em uma linha cada):
  - `config/config.toml` — etiqueta e digest do `gemma3:27b` conferidos e janela de 24 horas (00:00 às 23:59), sem `# PENDENTE` nessas quatro chaves;
  - `testes/test_estado.py`, `testes/test_integracao.py`, `testes/test_conferencia_etapas.py` e `testes/test_modelo_local.py` — a configuração de teste é montada por `apoio_config.provisorio`, com os valores de que cada teste precisa;
  - `testes/test_config.py` — a janela lida é comparada com a do arquivo, e o teste do pendente vazio escreve os valores vazios na sua cópia;
  - `testes/test_modelo_local.py` — o teste "a configuração do repositório está sem etiqueta" passa a se chamar `test_configuracao_com_etiqueta_e_digest_vazios_fica_indisponivel` e confere a mesma regra numa cópia com os valores vazios;
  - `docs/docs/doc_002_configuracao_2026-11-21.md` — seção nova "Conferência da máquina (2026-11-23)";
  - `docs/docs/pendencias_para_o_computador.md` — quatro linhas riscadas como resolvidas e duas novas (Bash 5 no Mac; janela de 24 horas);
  - `docs/PLAN.md` — Resumo, Backlog (o 026 roda antes do 024), Done (026 e o hash do 023) e Pendências de Sidarta Borges.

- Arquivos preservados literalmente na área afetada: `fabrica/`, `dados/`, `instrucoes/`, `config/gasto.toml`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md` e os demais testes.

- Testes rodados e resultado (com a saída colada):

  Com o `config.toml` preenchido:

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  131 files already formatted
  == mypy fabrica
  Success: no issues found in 34 source files
  == pytest testes
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  collected 1180 items
  ======================= 1180 passed in 61.18s (0:01:01) ========================
  saida=0
  ```

  Com o `config.toml` voltado aos valores provisórios (o arquivo do commit `669b09a`), antes de recolocar os valores da conferência:

  ```text
  ======================= 1180 passed in 66.59s (0:01:06) ========================
  ```

  Antes do conserto, com o `config.toml` preenchido: `7 failed, 1125 passed, 48 errors`. Com só a janela trocada: `2 failed, 1178 passed`.

- Comandos executados: `scripts/verificar.sh` (três vezes), `pytest testes` (diagnóstico), `ruff check --fix --select I` e `ruff format` nos testes alterados, `scripts/entregar.sh 026`. Nenhuma chamada à API da Claude nem ao modelo local.

- Lista de arquivos para `git add` e texto do commit:

```
config/config.toml
testes/apoio_config.py
testes/test_conferencia_etapas.py
testes/test_config.py
testes/test_estado.py
testes/test_integracao.py
testes/test_modelo_local.py
docs/briefs/brief_024_ensaio_2026-11-21.md
docs/briefs/brief_025_rodada_mvp_2026-11-21.md
docs/briefs/brief_026_testes_independentes_da_configuracao_2026-11-23.md
docs/docs/doc_002_configuracao_2026-11-21.md
docs/docs/doc_026_testes_independentes_da_configuracao_2026-11-23.md
docs/docs/pendencias_para_o_computador.md
docs/PLAN.md

Brief 026: testes independentes da configuração e conferência da máquina

Os testes deixam de depender dos valores provisórios do config.toml real:
cada um escreve na sua cópia os valores de que precisa. O config.toml recebe
a conferência da máquina de produção feita em 2026-11-23 (etiqueta e digest
do gemma3:27b e janela de 24 horas). Os textos dos briefs 024 e 025 ficam
gravados em docs/briefs/.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMeEMtQ7KS1eTbUzNX
```

- Pendências e decisões que ficaram abertas:
  1. **Janela de 24 horas:** a regra de `estado.py` não representa início igual ao fim; ficou 00:00 às 23:59, e só o último minuto do dia fica de fora. Mudar a regra exigiria um brief que toque `fabrica/`; não parece necessário.
  2. **Bash 5 no Mac:** exigência da máquina, registrada no arquivo de pendências e a levar ao roteiro do ensaio.
  3. **Numeração:** o 026 tem número maior que o 024 e o 025 porque foi escrito depois deles (AGENTS §10), mas roda antes.
  4. Chave da API, integração do pedido #2 em `main`, conferência dos textos de lei e das faixas de CEP: continuam com o responsável (PLAN, Pendências de Sidarta Borges).

- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim.
