# Brief 004 — Disco, configuração e registro

- Fase: 3 — Base (PLANO §4)
- Objetivo: escrever `arquivos.py` (único acesso ao disco, com gravação atômica e sem sobrescrever), `config.py` (leitura única e validada dos dois arquivos de configuração), `registro.py` (chamadas e ocorrências) e `testes/test_config.py`.
- Seções a ler: AGENTS §3 e §4; PLANO §3 e §4 (Fase 3); ARQUITETURA §2.1 (`config.toml` e `gasto.toml`), §2.5, §4, §7.3 e §7.4; registro de decisão 001 (itens 3 a 6); armadilhas do PLAN: "congelamento.py".
- Arquivos que pode criar:
  - `fabrica/comum/arquivos.py`, `fabrica/comum/config.py`, `fabrica/comum/registro.py`;
  - `testes/test_config.py`, `testes/test_arquivos.py`, `testes/test_registro.py`;
  - `docs/briefs/brief_004_disco_config_registro_2026-11-21.md` (este brief);
  - `docs/docs/doc_004_disco_config_registro_2026-11-21.md` (o relatório).
- Arquivos que pode alterar:
  - `fabrica/comum/formatos.py` — só para acrescentar os modelos `Configuracao` e `Gasto`, espelho exato das chaves de `config/config.toml` e `config/gasto.toml` (mudança de formato declarada por este brief);
  - `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `config/config.toml` e `config/gasto.toml` (conferidos no 002); `scripts/`; `AGENTS.md`; `docs/PLANO.md`; os modelos de `formatos.py` que já existem.
- Teste de aceite (escrito antes do código):
  - `test_config.py`: com cópias dos dois arquivos de configuração em pasta temporária, a leitura entrega todos os valores; tirar qualquer chave obrigatória, trocar o tipo de uma chave ou acrescentar uma chave desconhecida faz `config.py` parar com erro e mensagem que diz a chave, antes de qualquer outra coisa (o teste confere que nenhum cliente falso foi chamado); um valor marcado como pendente e vazio (etiqueta e digest do modelo local) é aceito e lido como "ausente", que o modelo local trata como indisponível;
  - `test_arquivos.py`: a gravação de um arquivo que já existe é recusada; o arquivo final só aparece depois de completo (o teste interrompe a gravação no meio, por um falso, e confere que só ficou o temporário); temporário que sobrar é ignorado na leitura e na listagem; arquivo lido fora do formato é recusado pela validação; `rodadas.json` é regravado com a cópia anterior guardada em `saida/registro/rodadas_anteriores/`; caminho fora da pasta de saída é recusado;
  - `test_registro.py`: cada chamada e cada ocorrência vira uma linha válida; a última linha incompleta é ignorada na leitura; a soma do custo lido bate com a soma gravada.
- Critério de conclusão: `test_config.py`, `test_arquivos.py` e `test_registro.py` passam no gate (parte do critério da Fase 3 no PLANO).
- Fora do escopo: gasto, estatística e congelamento (brief 005); clientes da API e do modelo local (006 e 007); montagem dos clientes em `__main__.py` (008); qualquer comando da fábrica.
- Depende de: 002 (com a conferência do responsável registrada) e 003.

**Regras deste brief**

- `arquivos.py` recebe a raiz do repositório por parâmetro (resolvida em `__main__.py` no brief 008, nunca caminho fixo) e é o único módulo que abre arquivo de `saida/`, `dados/`, `instrucoes/` e `config/`. Funções mínimas: gravar e ler JSON validado por um modelo de `formatos.py`; gravar e ler texto (`.md`); acrescentar linha a um `.jsonl`; listar arquivos de uma pasta por padrão de nome; dizer se um arquivo existe; impressão digital do conteúdo de um arquivo (SHA-256); e a leitura do controle de versão do registro de decisão 001, item 6, só por comandos de leitura do git: o identificador do conteúdo por `git rev-parse HEAD:fabrica` e `git rev-parse HEAD:pyproject.toml`, e a mudança pendente por `git status --porcelain -- fabrica dados instrucoes config pyproject.toml`, com os caminhos passados explicitamente, para que mudanças em `docs/` ou arquivos de `saida/` não contem.
- Os arquivos de teste novos (`test_arquivos.py`, `test_registro.py`) entram no relatório como acréscimo do método; a ARQUITETURA não é alterada aqui (consolidação no brief 023).
- Gravação atômica: grava em `<nome>.tmp-<aleatório>` na mesma pasta, força a escrita no disco e renomeia. Nunca sobrescreve; a única exceção é `saida/rodadas.json`, pela regra do registro de decisão 001, item 4.
- `config.py` lê os dois arquivos uma vez (biblioteca `tomllib`, que vem com o Python 3.12), valida pelos modelos `Configuracao` e `Gasto` e entrega um objeto só aos demais módulos. Nenhum valor tem padrão no código: chave faltando para.
- `registro.py` grava `saida/registro/chamadas.jsonl` (modelo; tokens de entrada, de cache, de raciocínio e de saída; custo em milionésimos de centavo; duração; peça; tarefa) e `saida/registro/ocorrencias.jsonl` (tipo, causa, início, fim, peça), sempre por `arquivos.py`. Lê os dois de volta para os relatórios e para o gasto.
- Os testes usam pasta temporária; nunca `saida/` do repositório.
