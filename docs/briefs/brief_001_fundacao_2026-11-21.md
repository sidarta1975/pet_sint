# Brief 001 — Fundação do repositório

- Fase: 1 — Fundação do repositório (PLANO §4)
- Objetivo: deixar o repositório com as regras, os documentos canônicos, o gate, o script de entrega, a trava de git e o ponto de entrada mínimo, e fazer o primeiro commit por `scripts/entregar.sh`.
- Seções a ler: AGENTS §2, §3, §5, §6, §9 e §10; PLANO §3, §4 (Fase 1), §5 e §6; ARQUITETURA §2, §2.1 e §2.4 (`test_entrega.py`), §5.2 e §5.12.3 (para o LEIA-ME), §8; armadilhas do PLAN: "Estrutura do pacote".
- Arquivos que pode criar:
  - `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`, `docs/PLAN.md` — cópias literais dos canônicos da pasta do projeto, com data de 2026-11-21 e já atualizados para a etapa de construção;
  - `docs/briefs/_modelo.md` — com o conteúdo literal do AGENTS §10;
  - `docs/briefs/brief_001_fundacao_2026-11-21.md` (este brief);
  - `docs/docs/doc_001_fundacao_2026-11-21.md` (o relatório);
  - `.gitignore` — o bloco literal do PLANO §6;
  - `pyproject.toml` — Python 3.12; dependências com versão fixa: `anthropic==2.12.0`, `pydantic==2.14.4`, `python-docx==1.2.0`; desenvolvimento: `pytest==9.2.0`, `ruff==0.17.6`, `mypy==2.4.1`; configuração de `ruff` e de `mypy` (modo estrito) no próprio arquivo;
  - `LEIA-ME.md` — inicial, com os itens da ARQUITETURA §2.1, apontando para as seções dos canônicos onde houver detalhe;
  - `scripts/verificar.sh` — o gate, na ordem `ruff check`, `ruff format --check`, `mypy fabrica`, `pytest testes`, parando na primeira falha;
  - `scripts/entregar.sh` — como na ARQUITETURA §2.1;
  - `scripts/trava_git.sh` e `.claude/settings.json` — a trava, como na ARQUITETURA §2.1;
  - `fabrica/__init__.py` e `fabrica/__main__.py` — o ponto de entrada mínimo: lê o comando e recusa comando desconhecido (saída com erro e mensagem), sem nenhuma etapa e sem nenhum comando registrado ainda;
  - `testes/test_entrega.py`.
- Arquivos que pode alterar: nenhum.
- Arquivos que não pode tocar: `README.md` (do commit inicial do responsável); tudo fora do repositório `pet_sint`.
- Formato do manifesto (fixado por este brief, porque os canônicos não fixam o delimitador): no relatório, logo depois da linha "- Lista de arquivos para `git add` e texto do commit:", um bloco de código cercado por três crases. Dentro do bloco: uma linha por arquivo (caminho relativo à raiz), `remover: <caminho>` nas remoções, uma linha em branco e o texto do commit. `entregar.sh` lê o primeiro bloco cercado depois dessa linha.
- Regras de `entregar.sh` além da ARQUITETURA §2.1: recebe o número com três dígitos; acha a raiz pelo próprio git, sem caminho fixo; exige exatamente um relatório `docs/docs/doc_<NNN>_*.md`; recusa manifesto vazio, sem texto de commit ou com caminho que não tenha mudança; envia o ramo atual (`git push -u origin HEAD`) só se houver remoto, com até 4 tentativas.
- Regras de `trava_git.sh`: lê o pedido de comando que o Claude Code entrega ao gancho (JSON na entrada padrão, campo `tool_input.command`); divide o comando nos separadores de terminal (`;`, `&&`, `||`, `|`, quebra de linha); bloqueia, com saída 2 e mensagem que manda usar `scripts/entregar.sh`, todo trecho que seja git de escrita da lista da ARQUITETURA §2.1, inclusive com opções antes do subcomando (`git -C <pasta> commit`); `branch` só é bloqueado com opção de troca ou remoção (`-d`, `-D`, `-m`, `-M`, `-c`, `-C`, `--delete`, `--move`, `--copy`, `-f`, `--force`). Todo o resto passa com saída 0.
- Teste de aceite (escrito antes do código): `testes/test_entrega.py`, num repositório git temporário, com um `scripts/verificar.sh` falso (verde ou vermelho) e os `entregar.sh` e `trava_git.sh` verdadeiros copiados para ele:
  1. `entregar.sh` recusa commit com o gate vermelho, e nenhum commit novo é feito;
  2. `entregar.sh` recusa quando há arquivo alterado ou novo fora do manifesto;
  3. `entregar.sh` commita só os arquivos do manifesto, com o texto do manifesto, e faz a remoção pedida por `remover:`;
  4. `trava_git.sh` bloqueia `git add`, `git commit` e `git push` digitados (e `git -C x commit`, e git de escrita depois de `&&`) e deixa passar `git status`, `git log` e `scripts/entregar.sh 001`.
- Critério de conclusão: o da Fase 1 no PLANO — `scripts/verificar.sh` sai verde; `test_entrega.py` mostra as recusas e a trava; o primeiro commit do brief foi feito por `entregar.sh`.
- Fora do escopo: `config/`, `dados/`, `instrucoes/`, `fabrica/comum/` e todo módulo de etapa; qualquer comando da fábrica; `docs/adr/` e `docs/historico/` (nascem no primeiro brief que gravar algo neles); chamada à API da Claude ou ao modelo local.
- Depende de: nenhum. Repositório `sidarta1975/pet_sint` criado pelo responsável.
