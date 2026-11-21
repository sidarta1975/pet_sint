# PLAN.md — estado vivo de Petições Sintéticas

> Atualizado ao fim de todo brief. A leitura obrigatória termina em `## Dívidas conhecidas`.
> Tudo que for histórico vai para `docs/historico/PLAN_historico_<data>.md`, literalmente, e é consultado por busca.
> Formato de linha em Doing, Backlog e Done:
> `- NNN · título curto · estado (concluído / sem commit / não iniciado) · commit (hash curto ou —) · data`

---

## Resumo

- Fase atual: Fase 8 — Etapas com modelos (PLANO, seção 4). As Fases 1 a 7 terminaram com os briefs 001 a 014.
- Repositório: `sidarta1975/pet_sint` (https://github.com/sidarta1975/pet_sint), criado pelo responsável em 2026-11-21. A construção (os briefs 001 a 023) roda em sessões do Claude Code na nuvem, que clonam o repositório; os testes na máquina do responsável e o ensaio ficam para quando ele estiver no computador.
- Último brief concluído: 016 · Redação (2026-11-21), entregue por `scripts/entregar.sh 016` no ramo `claude/project-thread-t7c3zg`, no mesmo pedido de integração para `main` (#2).
- Em execução: nada.
- Próximos três: 017 · Conferência, parte 1; 018 · Conferência, parte 2; 019 · Erros por programa.
- Último commit: `6badff5` (brief 015). O do 016 entra no Done pelo brief seguinte.
- Bloqueios: nenhum. O responsável autorizou, em 2026-11-21, seguir até o fim da fila sem novas aprovações; onde um brief pede resposta dele e ela não veio, vale o provisório escrito, registrado no relatório como decisão por falta de resposta.
- Documentos de origem: arquitetura do MVP, versão 10 (2026-11-21); plano v15 (fechado); lista consolidada de peças. Arquitetura dada como pronta para virar instruções na revisão de 2026-11-21. Fila de briefs revista em 2026-11-21 (de 19 para 25 briefs).

## Doing

(nenhum brief em execução)

## Backlog

Briefs previstos pela ordem de construção (PLANO, seção 4). Ainda não escritos: cada um é escrito e gravado em `docs/briefs/` antes de ser executado, e a numeração pode mudar se um brief for dividido. Fila revista em 2026-11-21.

- Nenhum brief gasta API: o executor nunca roda comando que gaste (AGENTS, seção 6). Só gastam o ensaio (024) e a rodada (025), rodados pelo responsável.
- O gate roda em qualquer máquina com Python 3.12. Só 024 e 025 dependem da máquina de produção.
- Param pelo responsável: 002 (conferir a configuração), 014 (aprovar os dados e a estrutura montada), 024 (ensaio) e 025 (rodada). Dentro do 024 e do 025 há ainda a resposta às amostras pelo comando `revisar`, antes do teste dos conferentes; os briefs 021 e 022 só constroem o código, com dados falsos, e não esperam por ele.
- Depois do ensaio aprovado, qualquer mudança em código, dados, instruções, `config.toml` ou `gasto.toml` obriga a um ensaio novo (ARQUITETURA 5.12.1): o comando `fichas` recusa a rodada. A conferência da configuração no 002 vale, portanto, para a rodada inteira.

- 017 · Conferência, parte 1: extração, checklist e conferente local, com extracao.md, checklist.md e conferente_local.md (Fase 8) · não iniciado · — · —
- 018 · Conferência, parte 2: desempate, semelhança e decisão, com opus_desempate.md e test_decisao (Fase 8) · não iniciado · — · —
- 019 · Erros por programa, com test_erros_programa (Fase 9) · não iniciado · — · —
- 020 · Revisão em duas etapas e publicação: revisao.py com todos os tipos de cartão, inclusive os das amostras, publicacao.py, comando `revisar` e test_publicacao (Fase 10) · não iniciado · — · —
- 021 · Erros plantados pelo Opus e verificação do Sonnet, com plantar_erro.md e o sorteio das duas amostras, sem alterar revisao.py (Fase 11) · não iniciado · — · —
- 022 · Teste dos conferentes, que recusa começar sem as duas amostras respondidas (Fase 11) · não iniciado · — · —
- 023 · Relatório do MVP: relatorios.py, com todos os itens da ARQUITETURA 5.11 (Fase 11) · não iniciado · — · —
- 024 · Ensaio de três peças, com o caminho dos erros em miniatura e a amostra reduzida; primeira conferência das instruções aos modelos: roteiro para o responsável e leitura do resultado (Fase 12) · não iniciado · — · —
- 025 · Rodada do MVP: roteiro para o responsável e leitura do relatório (Fase 13) · não iniciado · — · —

## Done — últimos 30 dias

- 016 · Redação: redacao.py e instrucoes/redacao.md, com o trecho da tabela (Fase 8) · concluído · — · 2026-11-21
- 015 · Fichas com âncora: fichas.py, instrucoes/ficha.md, comando `fichas` e test_ancora (Fase 8) · concluído · 6badff5 · 2026-11-21
- 014 · Proposta de todos os arquivos de dados/, com a estrutura montada de cada tipo e as conferências cruzadas, para aprovação do responsável (Fase 7) · concluído · 2c6b92b · 2026-11-21
- 013 · Citações de lei: citacoes.py, citacoes_50.json (conteúdo escrito no brief) e test_citacoes (Fase 6) · concluído · 3dfa32c · 2026-11-21
- 012 · Normalização, regras e comparação com a ficha: normalizacao.py, regras.py, comparacao_exemplos.json (conteúdo escrito no brief), test_regras e test_comparacao (Fase 6) · concluído · 96a44ad · 2026-11-21
- 011 · Montagem da estrutura, matriz e travas: estruturas.py, matriz.py, comando da preparação e test_travas, com exemplos dentro do teste (Fase 6) · concluído · 41ab742 · 2026-11-21
- 010 · Detector de dado real: dados_reais.py e test_dados_reais, com o teste dos reservados sobre a lista de proibidos vazia e a busca de nome reservado no código (Fase 5) · concluído · dbb70ce · 2026-11-21
- 009 · Dados fictícios e nomes reservados do teste: ficticios.py, test_ficticios (com listas de exemplo) e testes/dados/reais_reservados.json (Fase 5) · concluído · 14fe5f2 · 2026-11-21
- 008 · Condutor das peças: estado.py com a interface fixa das etapas, comando `avancar` e montagem dos três clientes, test_estado (Fase 4) · concluído · 3763577 · 2026-11-21
- 007 · Modelo local: modelo_local.py e test_modelo_local (Fase 4) · concluído · 8cd6655 · 2026-11-21
- 006 · API da Claude em dois passos: api_claude.py e test_api_claude (Fase 4) · concluído · 5ab94b1 · 2026-11-21
- 005 · Gasto, estatística e congelamento: gasto.py, estatistica.py, congelamento.py, test_gasto, test_estatistica e test_congelamento (Fase 3) · concluído · 52ac72a · 2026-11-21
- 004 · Disco, configuração e registro: arquivos.py, config.py, registro.py e test_config (Fase 3) · concluído · 6802157 · 2026-11-21
- 003 · Contratos de dados: formatos.py com o Anexo A e test_formatos (Fase 3) · concluído · c54e877 · 2026-11-21
- 001 · Fundação do repositório: AGENTS, docs, modelo de brief, gate, script de entrega, trava de git, .gitignore, pyproject, LEIA-ME inicial, pacote `fabrica` com `__main__.py` mínimo, test_entrega (Fase 1) · concluído · 2fb2f12 · 2026-11-21
- 002 · Configuração do MVP travada: config.toml e gasto.toml, conferidos pelo responsável (Fase 2) · concluído · 5a59957 e f803483 (conferência) · 2026-11-21

## Pendências de Sidarta Borges

- **Conferência da máquina do brief 002 (antes do ensaio).** No computador, rodar os cinco passos (no relatório `docs/docs/doc_002_configuracao_2026-11-21.md`) e informar o resultado de cada um, a etiqueta completa e o digest do `gemma3:27b`, e a janela da conferência local (provisória: 22h às 6h). Se o `gemma3:27b` não rodar na máquina, decidir antes do ensaio: outra máquina que rode o modelo, ou mudar a regra do risco alto na ARQUITETURA §5.12.4 (sem o modelo local, as peças de risco alto ficam em pausa e nem o ensaio nem a rodada fecham).
- **Quando estiver no computador, rodar o gate na sua máquina** (`scripts/verificar.sh`, num clone de `sidarta1975/pet_sint` com Python 3.12), para confirmar que ele também passa ali. Não bloqueia os briefs de construção, que rodam na nuvem; precisa estar feito antes do ensaio (brief 024).
- **Definir a janela da conferência local** (de 24 horas ou menos; o plano sugere a noite), para o `config.toml` do brief 002. Sem ela, o brief 002 usa a noite como valor e o registra como provisório.
- **Deixar a chave da API da Claude numa variável de ambiente** da máquina que vai rodar a fábrica, antes do ensaio (brief 024). Nunca no repositório.
- **Dizer se a máquina que vai rodar a fábrica tem o Ollama com `gemma3:27b` e o `porteiro`.** Não é obrigatório: sem eles, a válvula de escape cobre a ausência, mas o resultado tende a sair com a ressalva "sem conferente local estável".
- Mais adiante, só ele pode: conferir os dois arquivos de configuração (brief 002); aprovar os dados e a estrutura montada de cada tipo (brief 014); rodar o ensaio, com o caminho dos erros em miniatura, e confirmar o formato nos cartões (brief 024); rodar a rodada do MVP, ler as 30 primeiras versões e conferir as duas amostras de cópias, cerca de 10 horas no total (brief 025); decidir se escala. Quem lê e aprova precisa ser advogado.

## Decisões em aberto

- **10 ou 20 peças por tipo.** Adotado por ora: 10, a recomendação da arquitetura. Ampliar para 20 não muda a arquitetura, só a contagem: a quantidade no `config.toml` e as contagens dos eixos da matriz (Anexo A.6 dobra cada uma). Custaria cerca de US$ 20 a 25 a mais (cabe no mês) e cerca de 7,5 horas a mais de leitura. A pergunta está num cartão no chat do projeto, ainda sem resposta. Precisa estar decidida antes do brief 002.
- **Quem roda o git.** Adotado como padrão: o executor autônomo, que commita e faz push ao fim de cada brief só por `scripts/entregar.sh`, só com o gate verde e só os arquivos do manifesto (opção A do método). O responsável pode trocar pela opção B (ele roda o git) numa linha do `AGENTS.md`, seção 5. Vale o padrão enquanto ele não trocar.

## Dívidas conhecidas

(nenhuma)

## Armadilhas já identificadas — não redescobrir

(texto literal, nunca reescrito. Cada brief cita no cabeçalho, em "Seções a ler", as armadilhas da área que toca. Sem citação, o executor procura aqui, por busca, o nome do módulo que vai editar.)

- **api_claude.py** — Parece certo limitar o raciocínio com um teto de tokens de raciocínio, como o plano v15 previa. Nos modelos 5.5 (Opus, Sonnet e Haiku), o pedido que traz esse teto volta com erro; no Opus 5.5 e no Sonnet 5.5 o raciocínio também não pode ser desligado. Em vez disso: nível de esforço explícito por tarefa (`output_config.effort`) mais o teto de saída (`max_tokens`), que limita raciocínio e texto juntos. Origem: revisão da arquitetura, versão 6.
- **api_claude.py** — Parece certo obter JSON forçando o uso de uma ferramenta. O Opus 5.5 e o Sonnet 5.5 recusam o uso forçado de ferramenta com erro. Em vez disso: saída estruturada pelo parâmetro de formato da resposta (`output_config.format`), com o esquema gerado por `formatos.py`. Origem: revisão da arquitetura, versão 6.
- **api_claude.py** — Parece certo omitir o nível de esforço e ficar com o padrão. O padrão muda de modelo para modelo (no Opus 5.5 e no Haiku 5.5 é médio, no Sonnet 5.5 é alto), e a tarefa sairia com um esforço que a tabela não fixou. Em vez disso: mandar sempre o nível da tabela de roteamento. Origem: conversão para os documentos canônicos, 2026-11-21, conferida na documentação da API.
- **api_claude.py** — Parece certo ligar a troca automática de modelo que a API oferece quando um modelo recusa. A peça passaria a ser respondida por outro modelo sem aviso, e as medidas por conferente perderiam o sentido. Em vez disso: recusa é tratada como resposta fora do formato (novo pedido igual; na segunda, o destino de 5.12.8). Origem: revisão da arquitetura, versão 6.
- **api_claude.py** — Parece certo mandar temperatura ou começar a resposta do assistente para forçar o formato. Os modelos 5.5 recusam esses parâmetros e a resposta pré-escrita. Em vez disso: só saída estruturada e instrução. Origem: conversão para os documentos canônicos, 2026-11-21, conferida na documentação da API.
- **api_claude.py** — Parece certo consertar com expressão regular uma resposta que chegou quase no formato. O conserto esconde a falha e muda o que o modelo respondeu. Em vez disso: novo pedido igual; resposta guardada como chegou. Origem: método de trabalho e revisão da arquitetura.
- **ficticios.py** — Parece certo usar `exemplo.com` nos e-mails, como o plano v15 diz. `exemplo.com` não é domínio reservado e pode pertencer a alguém. Em vez disso: domínio terminado em `.example`, reservado para exemplos pela RFC 2606. Origem: revisão da arquitetura, versão 5.
- **ficticios.py** — Parece certo usar um CEP "fora das faixas usadas" para tornar o endereço fictício. Não existe faixa de CEP livre no país: todas estão distribuídas entre os estados. Em vez disso: CEP da faixa da cidade real; o que torna o endereço fictício é a rua inventada; o detector não confere CEP. Origem: revisão da arquitetura, versão 5.
- **ficticios.py** — Parece certo gerar número de processo com código de tribunal inexistente. Isso contradiz o juízo real escrito na peça. Em vez disso: ramo e tribunal coerentes com o juízo da ficha, e só o dígito verificador inválido (o oficial é pelo resto da divisão por 97). Origem: revisão da arquitetura, versão 5.
- **ficticios.py, dados_reais.py** — Parece certo calcular o dígito verificador do CNPJ só com números. A Receita emite CNPJ com letras desde 31/07/2026, e um detector só numérico deixaria esse formato passar. Em vez disso: cada caractere vale o seu código ASCII menos 48, com os mesmos pesos e o mesmo resto da divisão por 11. Origem: revisão da arquitetura, versão 6.
- **ficticios.py** — Parece certo sortear nomes de listas de nomes e sobrenomes, como o plano v15 diz. Um nome sorteado pode coincidir com o de uma pessoa real. Em vez disso: marcadores fixos por papel ("Nome e Sobrenome da Parte Autora" e afins) e OAB "OAB/UF nº 000.000"; o detector reprova todo nome que não seja marcador nem esteja na lista de permitidos. Origem: decisão do responsável, revisão da arquitetura, versão 9.
- **ficticios.py** — Parece certo inventar um DDD qualquer fora dos conhecidos. Sem a lista escrita, gerador e detector divergem. Em vez disso: só os 15 DDDs da lista (20, 23, 25, 26, 29, 36, 39, 52, 56, 57, 58, 59, 72, 76 e 78), conferidos contra os 67 em uso. Origem: revisão da arquitetura, versão 6.
- **dados_reais.py, test_dados_reais.py** — Parece certo testar o detector com os nomes da própria lista dele. O teste só provaria que o programa lê a própria lista. Em vez disso: nomes guardados à parte em `testes/dados/reais_reservados.json`, que não estão em `reais_proibidos.json` e que quem escreve o detector não usa. Origem: revisão da arquitetura, versão 5.
- **teste_conferentes.py** — Parece certo contar como pego todo erro em que a conferência reprova a cópia num item aceito. Se a conferência já reprova esse item na original, a reprovação na cópia não mostra que ela viu o erro plantado, e a taxa sai inflada. Em vez disso: o erro só conta como pego se o item aceito reprovou na cópia e passou na original, conferida de novo no mesmo teste. Origem: revisão da arquitetura, versão 6.
- **normalizacao.py, fichas.py (âncora)** — Parece certo que cortar as palavras nas 6 primeiras letras só erra para o lado seguro. Erra nos dois sentidos: junta palavras diferentes ("contrato" e "contrário"), o que só descarta a ficha, e separa formas da mesma palavra ("omissão" e "omitido", "nulidade" e "nulo"), o que pode deixar passar uma omissão que a decisão enfrentou. Em vez disso: manter o corte simples, cobrir os dois sentidos em `test_ancora.py` e deixar o sentido perigoso com a conferência da ficha pelo responsável, no cartão. Um radicalizador pronto (como o RSLP) não resolve a derivação. Origem: revisão da arquitetura, versão 7.
- **modelo_local.py** — Parece certo deixar o Ollama usar o contexto padrão. O padrão é pequeno e o Ollama corta o texto sem avisar, e a peça seria conferida pela metade. Em vez disso: `num_ctx` sempre explícito (16.384 no MVP) e pedido maior que ele, pela estimativa pessimista, não é enviado. Origem: revisão da arquitetura, versão 7.
- **modelo_local.py, estado.py** — Parece certo bloquear na rodada todo pedido acima de 75% do contexto, ou subir o contexto de novo depois de 32.768. Os 75% valem só no ensaio; na rodada só bloqueia o pedido que não cabe, e não há terceiro valor: com 32.768, a rodada segue e a válvula cobre o resto. Origem: revisão da arquitetura, versão 10.
- **modelo_local.py** — Parece certo supor que a máquina tem o Ollama e o `porteiro`. Nada se supõe sobre a máquina. Em vez disso: `porteiro` ausente ou com erro é "indisponível", e vale a válvula de escape. Origem: conversão para os documentos canônicos, 2026-11-21.
- **erros_plantados.py** — Parece certo dar o motivo "outro problema" quando o Sonnet não aponta item nenhum mas descreve um problema. Isso esconde a filtragem que tira do banco os erros que o verificador não vê. Em vez disso: sem item apontado, o motivo é sempre "não viu erro". Origem: revisão da arquitetura, versão 10.
- **semelhanca.py, teste_conferentes.py** — Parece certo desligar a semelhança no `config.toml` durante o teste dos conferentes. Alguém esquece de religar. Em vez disso: o teste chama a conferência em modo de teste, que ignora a semelhança sozinha. Origem: revisão da arquitetura, versão 3.
- **fichas.py, regras.py** — Parece inofensivo uma ficha ter valor igual ao salário mínimo (R$ 1.621,00) ou à alçada (R$ 64.840,00). A comparação passaria esse valor como referência legal quando ele está nos fatos. Em vez disso: `fichas.py` recusa ficha com valor igual a um dos dois; `test_comparacao.py` tem o exemplo. Origem: revisão da arquitetura, versão 10.
- **extracao.md, regras.py** — Parece certo que a extração liste prazos, quantidades e "40 salários mínimos" como valores. Não são quantias em dinheiro, e reprovariam peças boas na comparação. Em vez disso: só quantias em dinheiro, cada uma com o lugar (`fatos`, `pedido`, `valor_causa` ou `outro`). Origem: revisão da arquitetura, versões 7 e 10.
- **estatistica.py, plano B** — Parece certo que cerca de 36 cópias bastam para o limite inferior de 65% com 80% de acerto. Pelo método de Wilson, são 40 (32 de 40 dá 65,2%; 28 de 35 dá 64,1%). Origem: revisão da arquitetura, versão 6.
- **matriz.py, travas.json** — Parece certo gerar Embargos de Declaração em juizado. A lista consolidada tem rótulo próprio ("Embargos de Declaração em Juizado Especial"). Em vez disso: trava que proíbe o rito de juizado nesse tipo. Origem: revisão da arquitetura.
- **travas.json** — Parece útil a trava de advogado constituído acima de 20 salários mínimos (art. 9º da Lei 9.099/1995). Toda peça da fábrica é escrita por advogado, e a trava nunca agiria. Em vez disso: a trava que exige o novo endereço na manifestação. Origem: revisão da arquitetura, versão 5.
- **congelamento.py** — Parece certo começar a rodada com mudança de código ainda não commitada. A impressão digital do código é a do controle de versão, que precisa estar sem mudanças pendentes; a rodada não começa ou para. Em vez disso: commit por `entregar.sh` antes de qualquer ensaio ou rodada. Origem: revisão da arquitetura (congelamento).
- **Estrutura do pacote** — Parece natural ter um `fabrica.py` na raiz. Ele entra em conflito de nome com a pasta `fabrica/`. Em vez disso: ponto de entrada em `fabrica/__main__.py`, chamado com `python -m fabrica`. Origem: revisão da arquitetura, versão 2.
- **Ordem de construção** — Parece certo construir revisão e publicação depois do ensaio, como a ordem da v10 dizia. O ensaio vai de ficha a cartão e pacote e não passaria sem eles. Em vez disso: `revisao.py` e `publicacao.py` na Fase 10, antes do ensaio (hoje na Fase 12). Origem: conversão para os documentos canônicos, 2026-11-21.
- **Ordem de construção** — Parece certo construir o resto dos erros plantados, o teste dos conferentes e o relatório depois do ensaio, porque o ensaio não os usa. O ensaio aprovado grava a impressão digital do código e de `instrucoes/`, e qualquer código ou instrução criados depois dele faz o comando `fichas` recusar a rodada até um ensaio novo. Em vez disso: todo o código e todas as instruções prontos antes do ensaio (Fase 11, ensaio na Fase 12). Origem: revisão da fila de briefs, 2026-11-21.
- **dados_reais.py, test_dados_reais.py** — Parece que gravar os nomes reservados num brief anterior ao do detector deixa quem escreve o detector cego a eles. Os dois briefs rodam no mesmo repositório, e o executor do detector pode ler o arquivo. Em vez disso: o teste dos reservados roda com a lista de proibidos vazia, e outro teste confere que nenhum nome reservado aparece em `fabrica/` nem em `dados/`. Origem: segunda revisão da fila de briefs, 2026-11-21.
- **estado.py** — Parece certo construir o condutor logo depois dos contratos de dados. Ele usa configuração, registro, gasto, congelamento e os clientes externos, e nasceria sobre interfaces supostas. Em vez disso: `estado.py` na Fase 4, depois deles, chamando as etapas por uma interface fixa, sem importar os módulos de etapa. Origem: revisão da fila de briefs, 2026-11-21.
- **instrucoes/** — Parece prático escrever o texto enviado ao modelo dentro do módulo que faz o pedido. O texto escaparia do congelamento, que só calcula a impressão digital da pasta `instrucoes/`, e a versão gravada em cada peça não diria nada. Em vez disso: cada instrução num arquivo de `instrucoes/`, criado pelo brief do módulo que a usa, e lido pelo código. Origem: revisão da fila de briefs, 2026-11-21.

---

Histórico de decisões e atualizações: `docs/historico/` (consultar por busca, não ler inteiro).
