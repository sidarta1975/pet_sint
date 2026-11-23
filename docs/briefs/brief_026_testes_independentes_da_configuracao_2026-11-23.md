# Brief 026 — Testes independentes dos valores do config.toml e conferência da máquina

- Fase: 12 — Ensaio de três peças (PLANO §4), preparação. Roda antes do brief 024.
- Objetivo: fazer os testes deixarem de depender dos valores provisórios do `config/config.toml` real, para que a conferência da máquina feita pelo responsável em 2026-11-23 (etiqueta e digest do `gemma3:27b` e janela de 24 horas) entre no `config.toml` com o gate verde.
- Seções a ler: AGENTS §4, §6 e §10; PLANO §4 (Fase 2 e Fase 12) e §5; ARQUITETURA §5.12.4, §7.2 e §9; brief 002 (seção "Conferência da máquina"); armadilhas do PLAN: "modelo_local.py", "modelo_local.py, estado.py".
- Arquivos que pode criar:
  - `testes/apoio_config.py` — uma função que monta o texto do `config.toml` de teste a partir do real, trocando a linha inteira de cada chave pedida, qualquer que seja o valor atual;
  - `docs/briefs/brief_026_testes_independentes_da_configuracao_2026-11-23.md` (este brief);
  - `docs/briefs/brief_024_ensaio_2026-11-21.md` e `docs/briefs/brief_025_rodada_mvp_2026-11-21.md` — os textos literais dos briefs 024 e 025 da versão 5, gravados antes de serem executados (AGENTS §10);
  - `docs/docs/doc_026_testes_independentes_da_configuracao_2026-11-23.md` (o relatório).
- Arquivos que pode alterar:
  - `config/config.toml` — só `modelo_local.etiqueta_completa`, `modelo_local.digest`, `janela_local.inicio` e `janela_local.fim`, com os valores abaixo;
  - `testes/test_config.py`, `testes/test_estado.py`, `testes/test_modelo_local.py`, `testes/test_integracao.py` e `testes/test_conferencia_etapas.py` — só onde leem o `config.toml` real e supõem os valores provisórios;
  - `docs/docs/doc_002_configuracao_2026-11-21.md` — acrescentar, no fim, a seção "## Conferência da máquina (2026-11-23)";
  - `docs/docs/pendencias_para_o_computador.md` — riscar as linhas resolvidas e acrescentar as duas novas abaixo;
  - `docs/PLAN.md` (Resumo, Doing, Backlog, Done e Pendências de Sidarta Borges).
- Arquivos que não pode tocar: `fabrica/`, `dados/`, `instrucoes/`, `config/gasto.toml`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`; os demais testes.
- Teste de aceite (escrito antes do código): o gate inteiro verde com o `config.toml` já preenchido com os valores abaixo, e verde também com o `config.toml` voltado aos valores provisórios (etiqueta e digest vazios, janela das 22:00 às 06:00), conferido antes da entrega e registrado no relatório. Nenhuma asserção de teste é afrouxada: cada teste continua conferindo o mesmo comportamento, com os valores de que precisa escritos por ele mesmo na configuração de teste.
- Critério de conclusão: gate verde nos dois casos acima; `config.toml` com os valores da conferência e sem `# PENDENTE` nessas quatro chaves.
- Fora do escopo: mudar a regra da janela em `fabrica/estado.py`; rodar o ensaio; qualquer chamada à API ou ao modelo local.
- Depende de: 023.

**Regras deste brief**

- **Valores da conferência da máquina, feita pelo responsável em 2026-11-23, no MacBook Pro M5 (48 GB de memória, 104 GB livres):**
  - `etiqueta_completa = "gemma3:27b"`;
  - `digest = "6be2e2ba6843b9255820e2de2cbbe75cfdef0294ac7a531572e654d6e0eefe7d"`, lido em `/api/tags` do Ollama;
  - janela de 24 horas, escolha do responsável. A regra de `estado.py` trata início igual ao fim como janela vazia, por isso a janela fica `inicio = "00:00"` e `fim = "23:59"`: fica de fora só o último minuto do dia, e uma peça que caia nele espera até o `avancar` seguinte.
- **Causa do defeito:** vários testes copiam o `config.toml` real e trocam `etiqueta_completa = ""` e `digest = ""` por valores de teste, ou supõem a janela das 22h às 6h. Com o arquivo preenchido, a troca não acontece e os testes quebram. O conserto é cada teste escrever na configuração de teste os valores de que precisa, por `testes/apoio_config.py`, sem depender do que está no arquivo real.
- **Resultado da conferência da máquina**, para a seção nova do relatório do 002:
  1. Python 3.12.14 em `/opt/homebrew/bin/python3.12` (o Python padrão do Mac é o 3.14, que não serve);
  2. `gemma3:27b` baixado e listado;
  3. etiqueta e digest como acima;
  4. teste de resposta com `num_ctx` 16.384: respondeu "Ok." em 13,7 segundos, 12,6 deles carregando o modelo;
  5. `porteiro cabe gemma3:27b --porta 11434 --json`: código 0, "ja_carregado";
  e o gate do repositório na máquina: 1.180 testes passando, depois de instalar o Bash 5.3 pelo Homebrew.
- **Pendências novas**, no arquivo único:
  - o Mac precisa do Bash 5 do Homebrew (`brew install bash`): o Bash 3.2 do macOS não tem o recurso que `scripts/entregar.sh` usa, e 4 testes de `test_entrega.py` falham com ele. Provisório em uso: Bash 5.3.20 instalado em 2026-11-23;
  - janela de 24 horas não representável pela regra de `estado.py`. Provisório em uso: 00:00 às 23:59.
- **Linhas resolvidas no arquivo de pendências:** rodar o gate na máquina; os 5 comandos da conferência da máquina; etiqueta e digest; janela da conferência local.
- **PLAN:** o 026 entra no Done; o Backlog mostra que o 026 roda antes do 024; a pendência da conferência da máquina sai das Pendências de Sidarta Borges, e a da chave da API continua.
