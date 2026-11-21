# PLANO.md — Petições Sintéticas

**Repositório:** `sidarta1975/pet_sint`, no GitHub (https://github.com/sidarta1975/pet_sint), criado pelo responsável em 2026-11-21. Substitui o nome `peticoes_sinteticas` previsto na arquitetura v10. A construção (os briefs 001 a 023) roda em sessões do Claude Code na nuvem, que clonam o repositório; os testes na máquina do responsável e o ensaio ficam para quando ele estiver no computador.
**Data desta versão:** 2026-11-21
**Responsável:** Sidarta Borges, advogado. Aprova os dados, lê as peças e decide se escala.
**Máquina de produção:** hardware não definido. A construção não depende dela, porque roda na nuvem; o ensaio e a rodada rodam na máquina que o responsável escolher. A arquitetura não depende dela: nada se supõe sobre a máquina, e a válvula de escape do modelo local (ARQUITETURA 5.12.4) cobre a máquina desligada, ocupada, sem memória para o modelo, sem Ollama ou sem `porteiro`.
**Natureza:** programa local em Python, de linha de comando, que chama dois serviços: a API da Claude, pela internet, e um modelo local no Ollama da própria máquina. Saem da máquina só os pedidos à API da Claude, que levam instruções, estruturas, trechos da tabela de normas, fichas fictícias e peças fictícias. Nenhum dado real entra no projeto nem sai dele, porque o projeto nunca recebe dados reais.
**Fontes deste documento, nesta ordem de autoridade:** "arquitetura mvp peticoes sinteticas v10 2026-11-21.md"; "plano peticoes sinteticas v15 2026-11-21.md" (plano de longo prazo, fechado), com as correções de "divergencias com o plano v15 2026-11-21 b.md"; "Lista consolidada pecas processuais 2026 11 21.md" (rótulos exatos).

---

## 1. O que o software é

Uma fábrica de petições fictícias do direito brasileiro, típicas de advogados autônomos, para servir de modelo e de dado de treino de IA. Nesta etapa, ela é o MVP que testa a suposição de que depende todo o plano: **que a conferência automática pega os erros e não reprova as peças boas.** São 3 tipos de peça, um de cada classe de risco, com 10 peças cada: Petição Inicial em Juizado Especial Cível (risco médio), Embargos de Declaração (risco alto) e Manifestação sobre Aviso de Recebimento Negativo (risco baixo).

O MVP precisa responder:
1. **O caminho funciona de ponta a ponta?** Da ficha fictícia à peça publicada, sem intervenção manual no meio.
2. **A conferência pega erros?** Medido com erros plantados, cuja resposta certa se conhece. **É a pergunta central.**
3. **A conferência reprova peças boas por engano?** Comparando o veredito dela com o do responsável, sobre a mesma primeira versão.
4. **Algum dado real proibido escapa para a peça?** Precisa ser zero.
5. **Quanto custa uma peça aprovada?** Medido, não estimado.

**Partes principais e como se alimentam:**
- **Dados aprovados** (`dados/`): catálogo, estruturas em três níveis, matrizes, tabela de normas, travas, lista de conferência, catálogo de erros e listas de fictícios e de reais. Alimentam tudo.
- **Fichas:** programa sorteia a combinação e os dados fictícios; o Haiku escreve o caso fictício; programas conferem a ficha.
- **Redação:** Sonnet (risco médio e alto) ou Haiku (risco baixo) escreve a peça a partir da estrutura, da ficha e do trecho da tabela.
- **Conferência:** programas primeiro, depois a lista de itens respondida pelo Haiku, o modelo local nos itens de coerência e o Opus no risco alto e nos desempates. Reprova e manda refazer até a terceira versão.
- **Revisão humana:** o responsável lê às cegas a primeira versão de cada peça, com a ficha ao lado.
- **Erros plantados:** cópias com erro das peças boas, feitas por programa e pelo Opus, verificadas pelo Sonnet.
- **Teste dos conferentes:** as cópias e as peças boas passam pela conferência às cegas.
- **Publicação e relatório:** pacote das peças publicáveis e relatório com os critérios para escalar.

**Ciclo de ponta a ponta:** dados aprovados → ficha → redação → conferência → (refação → conferência) → revisão humana → erros plantados → teste dos conferentes → relatório → decisão de escalar → dados dos tipos novos.

**Custo estimado do MVP:** cerca de US$ 19 a 25 na API, dentro dos US$ 100 do mês.

| Item | Custo aproximado |
|---|---|
| 30 fichas e 30 peças, com refações | US$ 2 |
| Cerca de 100 cópias com erro feitas pelo Opus, todas verificadas pelo Sonnet, mais as descartadas e refeitas | US$ 11 a 13 |
| Conferência das 30 peças, com o Opus no risco alto e nos desempates | US$ 1,50 |
| Teste dos conferentes (cerca de 150 peças, entre cópias e originais) | US$ 3 a 6 |
| Ensaio de três peças e margem | US$ 1 a 2 |

**Tempo do responsável:** cerca de 10 horas. Aprovar estruturas, matrizes, travas e listas, cerca de 2 horas; ler as 30 primeiras versões com a ficha ao lado, cerca de 7,5 horas (20 minutos por peça de risco médio e alto, 5 por peça de risco baixo); conferir uma amostra de 10 cópias com erro, cerca de 30 minutos; conferir até 5 cópias descartadas por não ver erro, cerca de 15 minutos. Opcional: a leitura de publicação das versões refeitas, que não entra em nenhuma medida. **Quem lê e aprova precisa ser advogado.**

## 2. O que o software NÃO faz

Decisões de escopo, tomadas e fechadas.

- **Não atende caso real nem recebe dado real**, porque as peças são modelo e dado de treino, e um dado real numa peça publicada seria um vazamento.
- **Não usa banco de dados**; o estado são arquivos JSON e Markdown, porque com 30 peças um banco só acrescenta peças móveis. O índice em SQLite entra na onda 1, quando houver milhares de peças.
- **Não manda lote nem usa cache da API**, porque lote e cache só baixam o custo e não mudam o que o MVP mede. As chamadas já são em dois passos e a ordem do pedido já é fixa, para que o lote entre no piloto sem mudar as etapas.
- **Não cita acórdãos, não usa petições-modelo nem notícias**, porque o MVP testa a conferência, e cada fonte nova é mais uma coisa a conferir. Acórdãos e referências entram na onda 2.
- **Não faz auditoria cega de peças aprovadas**, porque a leitura do responsável já cobre as 30 primeiras versões. Entra no piloto.
- **Não atualiza a tabela de normas toda semana**, porque o MVP dura pouco e cada dispositivo tem fonte e data da conferência. Entra na onda 1.
- **Não usa um segundo conferente local**, porque um basta para medir o caminho; o `qwen3:30b` *instruct* entra no piloto como segundo candidato.
- **Não testa erro sutil de tese** (tese equivocada mas plausível), porque os 3 tipos do MVP quase não dão espaço a ele. Fica para o piloto.
- **Não mede os erros naturais da fábrica com erros plantados**; eles só aparecem na leitura do responsável das 30 primeiras versões.
- **Não decide por tipo de erro**, porque com cerca de 10 cópias por tipo a tabela por tipo é diagnóstico qualitativo. A decisão usa só os números do conjunto.
- **Não calibra o limite de semelhança**, porque não há peças suficientes. A semelhança só reprova quase cópias evidentes, e essa reprovação é contada à parte. A calibração fica para o piloto.
- **Não refaz o conjunto idêntico**, porque a semente refaz o sorteio e os dados fictícios, mas não o texto dos modelos.
- **Não julga a omissão parcial nos embargos**; o programa confere só a forma da âncora, porque saber se a menção equivale a enfrentar o argumento é juízo jurídico, que fica com o responsável no cartão.
- **Não conta feriados locais** no prazo em dias úteis, porque `feriados_nacionais.json` traz só os feriados nacionais de 2026; a matriz sorteia a data da peça com pelo menos um dia útil de folga.
- **Não gera ficha fora de 2026**, para que um só salário mínimo valha na alçada; a tabela de salários por ano entra na onda 1.
- **Não gera fatos com mais de 2 anos antes do ajuizamento**, para que nenhuma ficha caia em prescrição, que o MVP não testa.
- **Não gera cópias de treino sem a marca no texto**, porque o MVP não treina nada e uma cópia sem marca não se distingue de uma peça real. Ficam para a Fase 4 do plano, com a regra de guarda já escrita (ARQUITETURA, seção 4).
- **Não usa termos de alerta com contexto**, só os termos inequívocos, porque com 3 tipos e sem acórdãos quase nenhum termo legítimo ambíguo aparece. A lista de alerta entra no piloto.
- **Não reprova por nota de estilo**; as notas são registradas, porque uma regra de reprovação sem calibração se misturaria à medida de peças boas reprovadas, que decide.
- **Não troca de modelo sozinho quando um modelo recusa**, porque cada medida depende de saber qual modelo respondeu.
- **Não agenda nada**; toda execução é disparada pelo responsável, porque nada se supõe sobre quando a máquina está ligada.
- **Não sobe o corte de gasto**, porque US$ 100 é o orçamento do mês; o corte existe só como proteção contra defeito de programa.
- **Não inicia, para nem descarrega o Ollama**, porque ele é compartilhado com outros projetos da máquina.

## 3. Decisões fechadas

| Área | Decisão |
|---|---|
| Linguagem | Python 3.12, pacote `fabrica`, ponto de entrada `python -m fabrica <comando>` |
| Banco | Não há. Arquivos JSON e Markdown em `saida/`, com gravação atômica, nada sobrescrito nem apagado |
| Contratos de dados | Pydantic 2, modelos estritos em `fabrica/comum/formatos.py` (`extra="forbid"` e modo estrito), validados ao gravar e ao ler; os mesmos modelos geram o esquema das respostas estruturadas |
| Inferência / serviços externos | API da Claude (Opus 5.5, Sonnet 5.5 e Haiku 5.5), uma chamada por vez, em dois passos (gravar pedido, coletar resposta), saída estruturada por `output_config.format`, esforço e teto de saída por tarefa. Modelo local `gemma3:27b` no Ollama, porta 11434, sempre com `num_ctx` explícito (16.384 no MVP; 32.768 se o ensaio pedir), consultando o `porteiro` antes de cada uso. Só três arquivos falam com fora: `api_claude.py`, `modelo_local.py` e `arquivos.py` |
| Interface | Linha de comando. `fichas`, `avancar`, `revisar` e `revisar --resumo`, mais um comando por fluxo. Nenhuma porta aberta |
| Agendamento | Não existe. Toda execução é disparada pelo responsável |
| Testes, tipagem e lint | `pytest` em `testes/`; `mypy` em `fabrica/`; `ruff` para lint e formatação. Gate único: `scripts/verificar.sh` |
| Gasto | Alerta em US$ 30; corte em US$ 100 (o orçamento do mês), só como proteção contra defeito; em `config/gasto.toml`, congelado na rodada |
| Volume | 10 peças por tipo; 5 cópias com erro por peça boa (4 do Opus e 1 por programa); plano B escrito antes de rodar |
| Dados fictícios | Nomes e advogado como marcadores fixos ("Nome e Sobrenome da Parte Autora", "Nome e Sobrenome do Advogado" e afins); OAB "OAB/UF nº 000.000"; e-mail em `.example`; DDD inexistente da lista; documentos e número de processo com dígito verificador inválido; contratos com `SINT-`; endereço fictício pela rua |
| Critério central | Pelo menos 80% dos erros pegos nas cópias feitas por IA, com limite inferior de Wilson de 95% em pelo menos 65% |
| Git | Executor autônomo (opção A do método): commit e push ao fim de cada brief, só por `scripts/entregar.sh`, só com o gate verde e só os arquivos do manifesto. **Escolha padrão, que o responsável troca numa linha do `AGENTS.md`, seção 5** |

### 3.1 Roteamento por tarefa

| Tarefa | Modelo | Esforço | Teto de saída | Razão |
|---|---|---|---|---|
| Ficha | Haiku | Baixo | 8 mil tokens | Caso fictício em campos fixos; barato e conferido por programa |
| Redação de risco baixo | Haiku | Baixo | 8 mil tokens | Peça de forma quase fixa; é o caminho barato que o MVP testa |
| Extração e checklist | Haiku | Baixo | 8 mil tokens | Perguntas fechadas, item por item |
| Redação de risco médio | Sonnet | Baixo | 16 mil tokens | Peça juridicamente sensível |
| Redação de risco alto | Sonnet | Médio | 16 mil tokens | Precisa responder com coerência a uma decisão anterior |
| Conferência do risco alto e desempate | Opus | Baixo | 8 mil tokens | Barreira a mais no risco alto e juiz das discordâncias |
| Cópia com erro | Opus | Médio | 8 mil tokens | Erro sutil e convincente exige o modelo mais forte |
| Verificação da cópia | Sonnet | Médio | 8 mil tokens | Quem verifica não pode criar o erro nem ser conferente avaliado |
| Itens de coerência, peças anteriores e texto genérico | `gemma3:27b` local | — | — | Conferente de outra família que não a do Claude, sem custo de API |

Os níveis seguem a seção 8.2 do plano. O roteamento fica declarado em `config/config.toml`, nunca no código.

## 4. Fases

Ordem obrigatória. Cada fase termina com certificação (`AGENTS.md`, seção 11) antes da seguinte começar. As fases seguem a ordem de construção da arquitetura v10, com três correções, feitas na conversão para os documentos canônicos e na revisão da fila de briefs de 2026-11-21:
- **todo o código fica pronto antes do ensaio**, inclusive revisão, publicação, o resto dos erros plantados, o teste dos conferentes e o relatório. O ensaio vai de ficha a cartão e pacote, e o ensaio aprovado grava a impressão digital do código e das instruções (ARQUITETURA 5.12.1): código ou instrução criados depois dele obrigariam a um ensaio novo antes da rodada;
- **o condutor das peças (`estado.py`) vem depois de configuração, registro, gasto, congelamento e dos dois clientes externos**, que ele usa, para não nascer sobre interfaces supostas;
- **a montagem da estrutura (`estruturas.py`) vem antes da proposta dos dados**, para que o responsável aprove a estrutura montada junto com os dados (ARQUITETURA 1.3 e 5.5), sem parada a mais.

A fase 1 é o acréscimo do método de trabalho. Estas fases não são as do plano v15; as do plano começam depois do MVP (seção 4.1).

**Regras que valem para todas as fases:**
- O texto enviado a um modelo fica só no arquivo de `instrucoes/` da tarefa. Cada arquivo de instrução é criado pelo brief que constrói o módulo que o usa, e o código lê o arquivo; nunca embute o texto. Todos existem antes do ensaio, porque o congelamento calcula a impressão digital da pasta.
- Os testes das fases 3 a 6 não leem `dados/`, que só existe depois da fase 7: usam `testes/dados/` e exemplos escritos dentro do próprio teste, em pasta temporária.
- Cada brief que cria um comando acrescenta a sua linha em `fabrica/__main__.py` e registra o nome na ARQUITETURA, seção 8.

### Fase 1 — Fundação do repositório
`AGENTS.md`, os documentos canônicos em `docs/`, `docs/briefs/_modelo.md`, `.gitignore`, `pyproject.toml`, `LEIA-ME.md` inicial, `scripts/verificar.sh`, `scripts/entregar.sh`, a trava de git (`scripts/trava_git.sh` e `.claude/settings.json`), `fabrica/__init__.py`, `fabrica/__main__.py` mínimo (lê o comando e recusa comando desconhecido, sem nenhuma etapa) e `testes/test_entrega.py`.
**Conclui quando:** `scripts/verificar.sh` sai verde; `test_entrega.py` mostra que `entregar.sh` recusa commit com gate vermelho e com arquivo fora do manifesto, e que a trava bloqueia git de escrita digitado; o primeiro commit foi feito por `entregar.sh`.

### Fase 2 — Configuração do MVP travada
`config/config.toml` e `config/gasto.toml` com todos os valores da ARQUITETURA 2.1: modelos, preços e data da conferência; esforço e teto de saída por tarefa; alerta de US$ 30 e corte de US$ 100; 10 peças por tipo; 5 cópias por peça boa (4 do Opus e 1 por programa) e a regra do plano B; limite de semelhança 0,85; `gemma3:27b` com etiqueta, digest e `num_ctx` 16.384; janela da conferência local; salário mínimo de 2026 com o decreto; data da conferência dos DDDs; modo de chamada uma a uma.
**Conclui quando:** os dois arquivos existem com todos esses valores e o responsável os conferiu (registro no relatório do brief). É o que impede o custo de andar sem ninguém perceber.

### Fase 3 — Base
`formatos.py` (com os campos do Anexo A), `arquivos.py` (com a gravação atômica), `config.py`, `registro.py`, `gasto.py`, `estatistica.py` e `congelamento.py`.
**Conclui quando:** `test_formatos.py`, `test_config.py`, `test_gasto.py`, `test_estatistica.py` (com os números de Wilson da ARQUITETURA 2.4) e `test_congelamento.py` passam no gate.

### Fase 4 — Clientes externos e condutor
`api_claude.py` em dois passos, `modelo_local.py` e `estado.py`, com o comando `avancar` e a montagem dos três clientes em `fabrica/__main__.py`. `estado.py` chama cada etapa por uma interface fixa, escrita no brief do condutor: cada módulo de etapa expõe uma função que recebe a peça e os serviços e só grava pedido ou resultado; `estado.py` não importa os módulos de etapa, que lhe são entregues por parâmetro. Os módulos de etapa das fases seguintes seguem essa interface.
**Conclui quando:** `test_api_claude.py`, `test_modelo_local.py` e `test_estado.py` passam no gate, todos com clientes e etapas falsos; `test_estado.py` cobre a retomada depois de interrupção, o arquivo temporário pela metade ignorado, a parada na terceira versão e a regra do modelo local indisponível por classe e por contexto.

### Fase 5 — Dados fictícios e detector
`ficticios.py` e `dados_reais.py`. `testes/dados/reais_reservados.json` é criado no brief de `ficticios.py`, antes e à parte do brief do detector, que não o altera: assim quem escreve o detector não escolhe os nomes que o testam. A garantia não é a cegueira de quem escreve o detector, que roda no mesmo repositório e pode ler o arquivo: é que o teste dos reservados roda com a lista de proibidos vazia, e por isso só passa pela regra de "nome que não é marcador", e que um teste confere que nenhum nome reservado aparece em `fabrica/` nem em `dados/`. Os arquivos de `dados/ficticios/` nascem só na fase 7; aqui os testes usam listas de exemplo em pasta temporária.
**Conclui quando:** `test_ficticios.py` e `test_dados_reais.py` passam no gate, nos dois sentidos, com 100% dos nomes de `reais_reservados.json` pegos.

### Fase 6 — Preparação, travas e regras
`estruturas.py`, `matriz.py`, `normalizacao.py`, `regras.py` e `citacoes.py`, com o comando da preparação. `testes/dados/comparacao_exemplos.json` e `testes/dados/citacoes_50.json` são criados como teste de aceite, antes do código, nos briefs de `regras.py` e de `citacoes.py`, com o conteúdo escrito no próprio brief por quem o redige, e não pelo executor, para que o executor não escreva os exemplos que o seu código precisa passar. Os testes de `estruturas.py`, `matriz.py` e travas usam famílias, perfis, matrizes e travas de exemplo dentro do teste.
**Conclui quando:** `test_travas.py`, `test_regras.py`, `test_comparacao.py` e `test_citacoes.py` passam no gate, com as 50 formas de citação resolvidas em 100% (exigência da Fase 0 do plano); a montagem de uma estrutura de exemplo recusa a falta de bloco obrigatório.

### Fase 7 — Dados dos 3 tipos
A IA propõe todos os arquivos de `dados/`, que nascem aqui e só aqui, inclusive as listas de fictícios, de reais permitidos e de reais proibidos (catálogo, estruturas, matrizes, tabela de normas, travas, lista de conferência, termos inequívocos, palavras ignoradas, feriados nacionais, catálogo de erros, listas de fictícios e de reais), roda a preparação, que grava a estrutura montada de cada tipo, e o responsável aprova.
**Conclui quando:** todos os arquivos passam na validação de `formatos.py`; a matriz de cada tipo sorteia as 10 combinações dentro das travas e do teto por matéria em menos de 1.000 tentativas; o trecho da tabela de cada tipo fica abaixo de 8 mil tokens; a preparação mostra quantos dispositivos de cada tipo têm par; nenhum nome de `testes/dados/reais_reservados.json` está em `reais_proibidos.json` e todo dispositivo citado em `travas.json` está na tabela de normas; o responsável aprovou cada arquivo e a estrutura montada de cada tipo (registro no relatório do brief).

### Fase 8 — Etapas com modelos
`fichas.py` (com a âncora), `redacao.py` e os módulos de `conferencia/` que faltam (`extracao.py`, `checklist.py`, `local.py`, `desempate.py`, `semelhanca.py`, `decisao.py`), com as instruções `ficha.md`, `redacao.md`, `extracao.md`, `checklist.md`, `conferente_local.md` e `opus_desempate.md`, e o comando `fichas`.
**Conclui quando:** `test_ancora.py` e `test_decisao.py` passam no gate, com respostas de modelo falsas; a semelhança se desliga sozinha em modo de teste.

### Fase 9 — Erros por programa
A parte de `erros_plantados.py` que não usa modelo.
**Conclui quando:** `test_erros_programa.py` passa no gate: cada erro de regra é pego no item certo, e valor e data trocados nunca coincidem com valor, soma ou data da ficha.

### Fase 10 — Revisão e publicação
`revisao.py` (cartões em duas etapas e o comando `revisar`, com todos os tipos de cartão da ARQUITETURA, seção 8, inclusive os das duas amostras e o do ensaio) e `publicacao.py`. `revisao.py` é deste brief só; as fases seguintes não o alteram.
**Conclui quando:** `test_publicacao.py` passa no gate (nenhum arquivo sem a marca) e um cartão de exemplo mostra que a segunda etapa só é gerada depois das respostas confirmadas.

### Fase 11 — Resto dos erros plantados, teste dos conferentes e relatório
A parte de `erros_plantados.py` com o Opus e a verificação do Sonnet, com `plantar_erro.md`; o sorteio das duas amostras do responsável, gravado em arquivo que `revisao.py` mostra (os cartões são da fase 10); `teste_conferentes.py`, que recusa começar sem as duas amostras respondidas, porque o banco é fechado antes do teste (ARQUITETURA 5.7); e `relatorios.py`.
**Conclui quando:** com dados falsos, o teste calcula as cinco taxas com margem de Wilson e o relatório traz cada item da ARQUITETURA 5.11, inclusive as marcas de ressalva; o gate passa.

### Fase 12 — Ensaio de três peças
Rodado pelo responsável, porque gasta API. Uma peça de cada tipo, na combinação mais longa, de ficha a cartão e pacote. **Acréscimo da revisão da fila de 2026-11-21:** sobre as três peças do ensaio, o caminho dos erros em miniatura: uma cópia por programa e uma do Opus por peça, a verificação do Sonnet, um cartão de cada amostra, o teste dos conferentes e o relatório. Não mede nada; serve para que um defeito no gabarito, na verificação ou no relatório apareça antes da rodada, e não no relatório final, quando corrigi-lo mudaria o código e invalidaria a rodada pelo congelamento. Custo a mais estimado: menos de US$ 1, dentro da margem do ensaio. A amostra do ensaio é reduzida: todas as cópias do Opus aceitas (até 3) e até 1 descartada por "não viu erro", se houver; as marcas de banco não confiável e filtrado não se aplicam; a amostra cheia (10 e 5) só vale na rodada. O ensaio é também a primeira e única conferência das instruções aos modelos, que não passam pela aprovação dos dados na fase 7: instrução que produza saída ruim é corrigida antes da rodada, com ensaio novo.
**Conclui quando:** o ensaio está registrado como aprovado em `saida/rodadas.json` pela regra da ARQUITETURA 5.12.1, também sem erro de programa no caminho dos erros em miniatura, com o `num_ctx` decidido (16.384 ou 32.768) e os tokens reais de cada tarefa gravados.

### Fase 13 — Rodada do MVP
Rodada `r01`, disparada pelo responsável: fichas, redação e conferência, revisão das 30, erros plantados, teste, publicação e relatório.
**Conclui quando:** `saida/relatorios/relatorio_mvp.md` existe com todos os critérios da ARQUITETURA, seção 6, de uma rodada válida, e o responsável registrou a decisão de escalar ou não.

### 4.1 Depois do MVP

Se o MVP passar nos critérios, o caminho é o do plano v15, com as correções da lista de divergências: **piloto** com 6 tipos (Fase 1 do plano), **onda 1** com 80 tipos (Fase 2), **ondas 2 e 3** (Fase 3) e **publicação** (Fase 4). Escalar é, na maior parte, acrescentar dados:

| Recurso | Etapa | O que muda |
|---|---|---|
| Lote e cache da API | Piloto | `api_claude.py` e o modo de chamada no `config.toml` |
| Auditoria cega pelo Opus | Piloto | Novo `auditoria.py`, que `estado.py` passa a acionar |
| Segundo candidato a conferente local (`qwen3:30b` *instruct*) | Piloto | Só `config.toml` |
| Semelhança por vetores (`bge-m3`) e calibração dos limites | Piloto | Só `semelhanca.py` e `config.toml` |
| Criador de erros que não seja conferente avaliado, se o MVP sair dependente do Opus | Piloto | `plantar_erro.md` e o modelo no `config.toml` |
| Amostragem de dado real com detector diferente | Piloto | Novo passo em `dados_reais.py`, por amostra |
| Termos de alerta com contexto | Piloto | `termos_inequivocos.json` e `regras.py` |
| Notas de estilo reprovando abaixo de 3, se o MVP mostrar que não reprovam peças boas | Piloto | Uma linha de `decisao.py` |
| Erro de tese equivocada mas plausível | Piloto | `catalogo_erros.json` |
| Teste da extração com 20 fichas de formas variadas | Piloto | Novo arquivo de teste |
| Cópias de treino sem a marca, com a regra de guarda | Fase 4 do plano | Nova função em `publicacao.py`, com pasta própria |
| Tipos novos da mesma área | Cada onda | Só arquivos em `dados/` |
| Área nova (penal, trabalho e outras) | Onda 1 | `dados/` e os campos da ficha daquela área em `formatos.py` |
| Data de ajuizamento fora de 2026 | Onda 1 | Tabela de salários mínimos por ano no `config.toml` |
| Atualização semanal da tabela de normas | Onda 1 | Novo `atualizacao_normas.py`, que ainda precisa de desenho próprio |
| Índice das peças em SQLite | Onda 1 | Novo `indice.py`, que só lê `saida/` |
| Base de precedentes verificados | Onda 2 | `dados/precedentes/` e `precedentes.py`; `citacoes.py` passa a conferir acórdãos |
| Petições-modelo e notícias como referência | Onda 2 | Novo `referencias.py`; `dados_reais.py` compara a peça com a fonte |

**Regra que vale também para o piloto:** a leitura às cegas da primeira versão continua. As 30 leituras do piloto são sorteadas entre as primeiras versões, aprovadas ou não pela fábrica, e a medida que decide a reprovação de peça boa é a dessa leitura, não a do teste dos conferentes.

**O que limita a escala não é o código**, e o MVP mede cada ponto: o tempo do responsável para aprovar cada tipo novo; os minutos de leitura por peça; os segundos por conferência no modelo local; a taxa de fichas reprovadas.

**Decisão aberta que não muda a arquitetura:** 20 peças por tipo, em vez de 10, mudaria só a quantidade no `config.toml` e as contagens dos eixos da matriz (Anexo A.6 dobra cada contagem). Custaria cerca de US$ 20 a 25 a mais e cerca de 7,5 horas a mais de leitura. A recomendação é ficar com 10; a escolha está em `docs/PLAN.md`, Decisões em aberto.

## 5. Perfis de hardware e ambiente

- **Máquina de produção:** não definida. A arquitetura não depende dela. O que a máquina precisa ter: Python 3.12 e acesso à internet para a API da Claude, com a chave da API numa variável de ambiente, nunca no repositório. O Ollama com `gemma3:27b` e o `porteiro` são desejáveis, não obrigatórios: sem eles, ou com a máquina desligada ou ocupada, a válvula de escape do modelo local decide o destino de cada peça (ARQUITETURA 5.12.4), e o relatório mede quantas peças ficaram sem o conferente local, com a ressalva "sem conferente local estável" acima de 20% das peças de risco médio e alto.
- **Janela da conferência local:** a que o responsável definir no `config.toml`, de 24 horas ou menos. O plano sugere a noite.
- **Convivência com o Ollama:** ele pode ser compartilhado com outros projetos. A fábrica consulta o `porteiro` (`porteiro cabe <modelo> --porta 11434 --json`) antes de cada uso, segue a resposta e nunca inicia, para ou descarrega o Ollama.
- **Máquina de desenvolvimento:** a mesma regra. Os testes não chamam a API nem o Ollama, e por isso o gate roda em qualquer máquina com Python 3.12.
- **Ambiente de construção:** sessões do Claude Code na nuvem, sobre um clone de `sidarta1975/pet_sint`. Ali rodam o gate e a entrega de cada brief. Os testes na máquina do responsável e o ensaio (Fase 12) ficam para quando ele estiver no computador.
- **Memória:** o MVP não fixa limite, porque não supõe hardware. Quem decide se o modelo local cabe a cada uso é o `porteiro`.

## 6. Governança de documentos

- Documentos canônicos: `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`, `docs/PLAN.md`, `docs/briefs/_modelo.md`. Fora do repositório, cada um é entregue com o nome do projeto e a data no arquivo (por exemplo, "ARQUITETURA peticoes sinteticas 2026-11-21.md").
- Todo `.md` de `docs/` é versionado.
- Numeração única para briefs e relatórios; o brief é gravado em `docs/briefs/` antes de ser executado.
- O relatório de cada brief fica em `docs/docs/`.
- O histórico fica em `docs/historico/` e é consultado por busca.
- Cópia de segurança antes de reorganizar qualquer documento canônico, em `docs/historico/<data>_pre_<brief>/`.
- Todo documento entregue ao responsável tem caminho próprio e permanente; nunca se reaproveita o caminho de uma entrega anterior, nem se apaga uma entrega anterior.
- As versões da arquitetura (v4 a v10), o plano v15 e as listas de divergências ficam intactos no projeto, como histórico. Uma divergência nova com o plano v15 vira uma linha em "divergencias com o plano v15 2026-11-21 b.md".
- Todo documento é escrito em português simples, sem siglas soltas nem jargão sem explicação.

`.gitignore` obrigatório desde o primeiro commit (o projeto não tem dado pessoal nem sigiloso, mas `saida/` é gerada e não entra no git, e a chave da API nunca entra):

```gitignore
saida/
.env
__pycache__/
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

O repositório continua clonável sem arquivos de exemplo: tudo em `dados/` é fictício ou público e versionado.
