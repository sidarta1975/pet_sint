# ARQUITETURA.md — Petições Sintéticas

Uma etapa, um módulo: cada módulo lê o que o anterior gravou em `saida/` e grava o seu resultado ali; nenhum módulo chama outro por dentro. Só três arquivos falam com o mundo de fora (`fabrica/comum/api_claude.py`, `fabrica/comum/modelo_local.py` e `fabrica/comum/arquivos.py`), e os três são montados num só lugar, `fabrica/__main__.py`, e entregues aos módulos por parâmetro. Não há banco de dados: arquivos JSON e Markdown em pastas.

> Cada afirmação deste documento tem de ser verdadeira hoje. Afirmação superada é corrigida ou removida, nunca deixada como atual.
> Fonte: "arquitetura mvp peticoes sinteticas v10 2026-11-21.md". Onde este documento acrescenta algo à v10, o acréscimo vem marcado como **acréscimo do método**: são as peças do método de trabalho (gate, script de entrega, trava, testes que faltavam) e uma correção de ordem (seção 1.4).
> Rótulos de tipo de peça: sempre os exatos da "Lista consolidada pecas processuais 2026 11 21.md".

---

## 1. Fluxo

### 1.1 Visão geral

```
Preparação ─► Ensaio de três peças ─► Fichas ─► Redação ─► Conferência ─┬─► Revisão humana (30 primeiras versões, às cegas)
                                                ▲                     │                │
                                                └──── Refação ◄───────┘                ▼
                                                                        Erros plantados ─► Teste dos conferentes
                                                                                                   │
   Estado (conduz cada peça e coleta respostas), congelamento e controle de gasto em todos os fluxos ▼
                                                                         Publicação ◄──── Relatório do MVP
```

Toda trilha é disparada pelo responsável, por um comando (`python -m fabrica <comando>`, seção 8). Não há nada automático fora de um comando: dentro dele, `estado.py` leva cada peça ao próximo passo possível, coleta as respostas prontas e aplica as regras fixas. As únicas esperas por pessoa são a aprovação da preparação, os vereditos nos cartões, as duas amostras de cópias com erro e a leitura de publicação, todas pelo comando `revisar`.

Acoplamento entre trilhas: só por arquivo. A revisão humana lê as primeiras versões e as conferências; os erros plantados partem só das peças boas (seção 5.12.7), que dependem dos vereditos do responsável; o teste dos conferentes lê as cópias, o gabarito e as peças boas; o relatório lê o registro, as ocorrências, as conferências, os cartões e o resultado do teste.

### 1.2 Arquivos usados em cada fluxo

| Fluxo | Código | Dados e instruções |
|---|---|---|
| **Preparação** | `estruturas.py`, `matriz.py`, `formatos.py` | `tipos.json`, `familias/`, `perfis/`, `acrescimos/`, `matrizes/`, `tabela_normas.json`, `travas.json`, `conferencia/`, `catalogo_erros.json`, `reais_permitidos.json`, `reais_proibidos.json` |
| **Ensaio de três peças** | Todos os fluxos abaixo, com uma peça de cada classe | Os mesmos |
| **Fichas** | `matriz.py`, `ficticios.py`, `fichas.py`, `normalizacao.py`, `api_claude.py`, `gasto.py`, `registro.py`, `estado.py` | `matrizes/`, `travas.json`, `listas_ficticias.json`, `palavras_ignoradas.json`, `ficha.md` |
| **Redação e refação** | `redacao.py`, `api_claude.py`, `gasto.py`, `registro.py`, `estado.py` | Estrutura montada, `tabela_normas.json`, `redacao.md` |
| **Conferência** | Os módulos de `conferencia/`, `normalizacao.py`, `api_claude.py`, `modelo_local.py`, `estado.py` | `tabela_normas.json`, `lista_conferencia.json`, `termos_inequivocos.json`, `feriados_nacionais.json`, `reais_permitidos.json`, `reais_proibidos.json`, `extracao.md`, `checklist.md`, `conferente_local.md`, `opus_desempate.md` |
| **Revisão humana** | `revisao.py` | Primeiras versões, extrações, fichas, conferências |
| **Erros plantados** | `erros_plantados.py`, `api_claude.py`, `gasto.py` | Peças boas, `catalogo_erros.json`, `plantar_erro.md`, `tabela_normas.json` |
| **Teste dos conferentes** | `teste_conferentes.py`, `estatistica.py` e os módulos de `conferencia/`, em modo de teste (semelhança desligada automaticamente) | Cópias com erro, gabarito, peças boas |
| **Publicação** | `publicacao.py` | Peças publicáveis (5.10) |
| **Estado, congelamento e gasto** | `estado.py`, `congelamento.py`, `gasto.py`, `registro.py`, `api_claude.py` | `config.toml`, `gasto.toml`, `saida/rodadas.json`, `saida/pedidos/`, `saida/respostas/` |
| **Relatório do MVP** | `relatorios.py`, `estatistica.py` | Registro, ocorrências, conferências, cartões, resultado do teste |

### 1.3 Entradas e saídas de cada fluxo

| Fluxo | Entrada | Saída | Quem decide |
|---|---|---|---|
| **Preparação** | Rótulos da lista consolidada; propostas da IA de estrutura, matriz, normas, travas, lista de conferência, catálogo de erros, termos e listas de reais | Estrutura montada e aprovada de cada tipo; matriz, tabela, travas, listas e catálogo validados | O responsável aprova |
| **Ensaio de três peças** | Uma combinação de cada tipo, a que gera a peça mais longa (1.4) | Três peças percorrendo todas as etapas, de ficha a cartão e pacote, inclusive o caminho com decisão anterior e o caminho do Haiku | O responsável confere se tudo saiu no formato certo; o programa registra o ensaio aprovado (5.12.1) |
| **Fichas** | Matriz e travas; listas fictícias; semente | `saida/fichas/<rodada>_<tipo>_<n>.json`: caso fictício, e decisão anterior quando o tipo exige | Programa confere formato, coerência e âncora |
| **Redação** | Estrutura montada; ficha; trecho da tabela | `saida/pedidos/...` e, depois, `saida/rascunhos/<rodada>_<tipo>_<n>_v1.md` com metadados | — |
| **Conferência** | Rascunho; ficha; tabela; listas | `saida/conferencias/<rodada>_<tipo>_<n>_v1.json`: extração, resultado item por item, notas de estilo e veredito com a categoria do motivo | `decisao.py`, por regra fixa |
| **Refação** | Rascunho reprovado e motivo | `..._v2.md` e, no máximo, `..._v3.md`; depois disso, descarte registrado | `estado.py` e `decisao.py` |
| **Revisão humana** | Primeira versão das 30 peças, aprovadas ou não, e as fichas | `saida/cartoes/<rodada>_<tipo>_<n>_etapa1.md`; os vereditos da ficha e da peça e a resposta sobre dado real gravados pelo comando `revisar`; depois `..._etapa2.md`, com o veredito da fábrica sobre a mesma versão; concordância nos dois sentidos | O responsável dá os vereditos |
| **Erros plantados** | Peças boas | `saida/erros/<rodada>_<tipo>_<n>_erro<k>.md` (5 por peça, ou 7 pelo plano B) e `gabarito.json` | Programa (região e gabarito) e Sonnet como verificador; o responsável confere 10 aceitas e até 5 descartadas, por amostra |
| **Teste dos conferentes** | Cópias com erro, peças boas e gabarito, em modo de teste | `saida/relatorios/teste_conferentes.json`: taxa das cópias de IA (critério central), taxa sem o Opus, taxa nos erros de julgamento por programa, taxa nos erros de regra (sanidade) e taxa de reprovação no teste, com margem de Wilson e diagnóstico por conferente e tipo de erro | — |
| **Publicação** | Peças publicáveis | `saida/pacotes/<tipo>/`: `.md`, `.json`, `.docx` e índice | — |
| **Estado, congelamento e gasto** | Arquivos de `saida/`; registro; tetos; impressões digitais | Próximo passo de cada peça; respostas coletadas; envio autorizado ou bloqueado; rodada parada se um arquivo congelado mudou | Programa, por regra fixa |
| **Relatório do MVP** | Registro, ocorrências, conferências, cartões e teste | `saida/relatorios/relatorio_mvp.md`: critérios com resultado e margem, e tabela de erros não pegos | O responsável decide se escala |

### 1.4 Ordem de execução no MVP

1. **Preparação:** a IA propõe, e o responsável aprova estruturas, matrizes, normas, travas, lista de conferência, catálogo de erros, termos inequívocos, palavras ignoradas e listas de reais dos 3 tipos. É a única etapa que espera pelo responsável antes de gastar API.
2. **Ensaio de três peças:** uma de cada tipo percorre todo o caminho, de ficha a cartão e pacote. Em cada tipo, o ensaio usa a combinação que gera a peça mais longa: complexidade `media` e estilo `detalhado` e, nos embargos, sentença (que tem relatório) com omissão parcial. Assim o ensaio mede o pedido ao modelo local perto do maior tamanho esperado. Pega erro de formato, de campo ou de leitura em cada caminho (médio, com decisão anterior e do Haiku) antes que ele contamine as 30. O ensaio não é às cegas: o cartão mostra as duas etapas juntas, com o veredito da fábrica, porque o objetivo é depurar o formato, não medir. As três peças ficam numa rodada própria (`e01`, ou `e02` e seguintes se for refeito) e não entram nos números do MVP. A rodada do MVP só começa depois de um ensaio aprovado (5.12.1).
3. **Fichas:** 30 fichas, 10 por tipo.
4. **Redação e conferência:** cada peça segue até ser aprovada ou descartada, conduzida pelo módulo de estado.
5. **Revisão humana:** o responsável lê a primeira versão das 30, sem ver o veredito da fábrica.
6. **Erros plantados:** cinco cópias com erro para cada peça boa, ou sete pelo plano B. A regra do plano B é aplicada aqui, pela contagem de peças boas, sem decisão nova.
7. **Teste dos conferentes:** cópias e peças boas passam pela conferência às cegas.
8. **Publicação:** as peças publicáveis viram pacote.
9. **Relatório do MVP:** resultado de cada critério e tabela de erros não pegos.

**Consequência para a construção (correção de ordem, acréscimo do método):** como o ensaio precisa chegar a cartão e pacote, `revisao.py` e `publicacao.py` ficam prontos **antes** do ensaio. A ordem de construção da v10 punha os dois depois dele. Pela mesma razão, e porque o ensaio aprovado grava a impressão digital do código e de `instrucoes/` (5.12.1), o resto dos erros plantados, o teste dos conferentes e o relatório também ficam prontos antes do ensaio. Sobre as três peças do ensaio corre ainda o caminho dos erros em miniatura: uma cópia por programa e uma do Opus por peça, a verificação do Sonnet, uma amostra reduzida (todas as cópias do Opus aceitas, até 3, e até 1 descartada por "não viu erro", se houver, sem as marcas de banco não confiável ou filtrado, que só valem com a amostra cheia da rodada), o teste dos conferentes e o relatório, sem valor de medida. O PLANO (fases 10 e 11, antes do ensaio na fase 12) traz a ordem corrigida.

---

## 2. Estrutura do repositório

```
pet_sint/
├── AGENTS.md                      (regras do executor; acréscimo do método)
├── LEIA-ME.md
├── pyproject.toml
├── .gitignore                     (acréscimo do método)
├── .claude/
│   └── settings.json              (trava de git; acréscimo do método)
├── docs/                          (acréscimo do método)
│   ├── PLANO.md
│   ├── ARQUITETURA.md
│   ├── PLAN.md
│   ├── adr/                       (decisões arquiteturais, uma por arquivo)
│   ├── briefs/                    (briefs numerados, com _modelo.md)
│   ├── docs/                      (relatórios, um por brief)
│   └── historico/                 (fora da leitura obrigatória; consulta por busca)
├── scripts/                       (acréscimo do método)
│   ├── verificar.sh               (o gate)
│   ├── entregar.sh                (único caminho de commit)
│   └── trava_git.sh               (chamado pela trava de .claude/settings.json)
├── config/
│   ├── config.toml
│   └── gasto.toml                 (alerta e corte de gasto; congelado como os demais)
├── dados/
│   ├── catalogo/tipos.json
│   ├── estruturas/familias/<familia>.json
│   ├── estruturas/perfis/<perfil>.json
│   ├── estruturas/acrescimos/<tipo>.json
│   ├── matrizes/<tipo>.json
│   ├── normas/tabela_normas.json
│   ├── travas/travas.json
│   ├── conferencia/
│   │   ├── lista_conferencia.json
│   │   ├── termos_inequivocos.json
│   │   ├── palavras_ignoradas.json
│   │   └── feriados_nacionais.json
│   ├── erros/catalogo_erros.json
│   └── ficticios/
│       ├── listas_ficticias.json
│       ├── reais_permitidos.json
│       └── reais_proibidos.json
├── instrucoes/                    (uma instrução por tipo de saída de modelo)
│   ├── ficha.md
│   ├── redacao.md
│   ├── extracao.md
│   ├── checklist.md
│   ├── conferente_local.md
│   ├── opus_desempate.md
│   └── plantar_erro.md
├── fabrica/
│   ├── __main__.py
│   ├── estado.py
│   ├── comum/
│   │   ├── config.py
│   │   ├── formatos.py            (todos os contratos de dados)
│   │   ├── arquivos.py
│   │   ├── congelamento.py
│   │   ├── normalizacao.py
│   │   ├── estatistica.py
│   │   ├── registro.py
│   │   ├── api_claude.py
│   │   ├── modelo_local.py
│   │   └── gasto.py
│   ├── estruturas.py
│   ├── matriz.py
│   ├── ficticios.py
│   ├── fichas.py
│   ├── redacao.py
│   ├── conferencia/
│   │   ├── extracao.py
│   │   ├── regras.py
│   │   ├── citacoes.py
│   │   ├── dados_reais.py
│   │   ├── checklist.py
│   │   ├── local.py
│   │   ├── desempate.py
│   │   ├── semelhanca.py
│   │   └── decisao.py
│   ├── erros_plantados.py
│   ├── teste_conferentes.py
│   ├── revisao.py
│   ├── publicacao.py
│   └── relatorios.py
├── testes/
│   ├── dados/
│   │   ├── citacoes_50.json
│   │   ├── reais_reservados.json
│   │   └── comparacao_exemplos.json
│   ├── test_regras.py
│   ├── test_travas.py
│   ├── test_ancora.py
│   ├── test_comparacao.py
│   ├── test_citacoes.py
│   ├── test_ficticios.py
│   ├── test_dados_reais.py
│   ├── test_estado.py
│   ├── test_congelamento.py
│   ├── test_erros_programa.py
│   ├── test_formatos.py
│   ├── test_entrega.py            (acréscimo do método)
│   ├── test_config.py             (acréscimo do método)
│   ├── test_estatistica.py        (acréscimo do método)
│   ├── test_gasto.py              (acréscimo do método)
│   ├── test_api_claude.py         (acréscimo do método)
│   ├── test_modelo_local.py       (acréscimo do método)
│   ├── test_decisao.py            (acréscimo do método)
│   └── test_publicacao.py         (acréscimo do método)
└── saida/                         (gerada; fora do controle de versão)
    ├── rodadas.json
    ├── pedidos/
    ├── respostas/
    ├── fichas/
    ├── rascunhos/
    ├── conferencias/
    ├── aprovadas/
    ├── erros/
    ├── cartoes/
    ├── pacotes/
    ├── registro/
    │   ├── chamadas.jsonl
    │   └── ocorrencias.jsonl
    └── relatorios/
```

O repositório é `sidarta1975/pet_sint`, no GitHub; o nome `peticoes_sinteticas` da v10 não é usado. O pacote se chama sempre `fabrica`. Não há o arquivo `fabrica.py` na raiz: o ponto de entrada é `fabrica/__main__.py`, chamado com `python -m fabrica`. Isso evita o conflito de nome entre um arquivo e uma pasta chamados `fabrica`. A pasta de testes se chama `testes/`, e não `tests/`.

O que muda por tipo de peça fica em `dados/`, e o responsável aprova. O que é igual para todos fica em `fabrica/`.

### 2.1 Raiz, método e configuração

**`AGENTS.md`** — Regras do executor. O Claude Code o carrega no início da sessão. Não existe `CLAUDE.md` nem `CLAUDE.local.md` no repositório.

**`LEIA-ME.md`** — Explica em linguagem simples:
- o que é a fábrica, que ela só gera peças fictícias e nunca recebe dados reais;
- o que pode e o que não pode ser real (5.2);
- como rodar cada comando;
- a regra de convivência com o Ollama, copiada da seção 9 do plano: consultar o `porteiro` antes de usar o modelo local, seguir a resposta (5.12.4) e nunca iniciar, parar ou descarregar o Ollama;
- que a semente refaz o sorteio e os dados fictícios, mas não o texto dos modelos, e que por isso o conjunto publicado não pode ser refeito idêntico;
- que quem aprova e lê as peças precisa ser advogado;
- o que é operação normal e o que é intervenção manual numa rodada (5.12.3).

**`pyproject.toml`** — A versão do Python (3.12) e as poucas bibliotecas usadas, com versões fixas:
- cliente da API da Claude (o pacote oficial `anthropic`);
- validação de formato (Pydantic, versão 2);
- geração de `.docx`;
- testes (`pytest`).

Ferramentas só de desenvolvimento, também com versão fixa: `ruff` (lint e formatação) e `mypy` (tipagem). Não entram no código da fábrica.

**`.gitignore`** — Desde o primeiro commit:

```gitignore
saida/
.env
__pycache__/
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

Não há `*.db` porque não há banco. `dados/` é versionado: tudo nele é fictício ou público e aprovado pelo responsável.

**`.claude/settings.json`** — A trava: um gancho que roda antes de cada comando de terminal do executor e chama `scripts/trava_git.sh`. O script lê o comando pedido e o bloqueia se for git de escrita (`add`, `commit`, `push`, `rm`, `mv`, `reset`, `checkout`, `switch`, `restore`, `rebase`, `merge`, `tag`, `stash`, `branch` com troca ou remoção) digitado direto. Leitura (`status`, `diff`, `log`, `show`) passa. `scripts/entregar.sh` passa.

**`scripts/verificar.sh`** — O gate, na ordem: `ruff check`, `ruff format --check`, `mypy fabrica`, `pytest testes`. Sai com erro na primeira falha. Nenhum teste chama a API da Claude ou o Ollama de verdade: os três clientes externos são trocados por falsos.

**`scripts/entregar.sh <NNN>`** — O único caminho de commit. Lê o relatório `docs/docs/doc_<NNN>_*.md`, tira dele o bloco "Lista de arquivos para `git add` e texto do commit" (o manifesto, com uma linha por arquivo, e a palavra `remover:` antes do caminho de arquivo a remover), roda `scripts/verificar.sh` e para se o gate não estiver verde, roda `git status --porcelain` e para se houver arquivo alterado ou novo fora do manifesto, adiciona arquivo por arquivo (`git add <arquivo>`; `git rm <arquivo>` nas remoções), commita com o texto do manifesto e faz push se o repositório tiver remoto. Nunca usa `git add -A` nem `git add .`.

**`config/config.toml`** — Todos os valores que mudam sem mexer no código, exceto os tetos de gasto:
- nomes dos modelos e preços conferidos, com a data da conferência (seção 7);
- nível de esforço e teto de saída por tarefa (seção 7);
- quantidade de peças por tipo (10) e de cópias com erro por peça boa (4 do Opus e 1 por programa), com a regra do plano B (5.12.6);
- limite de semelhança (0,85, 5.6);
- modelo local, com a etiqueta completa e o digest (a impressão digital que fixa a versão exata do modelo), e seus parâmetros. O tamanho de contexto (`num_ctx`, quantos tokens o modelo lê de uma vez) fica escrito de forma explícita, como o plano manda ("grande o bastante para a peça inteira mais a ficha"). O valor de 16.384 tokens é do MVP, e não do plano. Sem ele, o Ollama usa um valor padrão pequeno e corta o texto sem avisar. O ensaio mede o tamanho real dos pedidos e decide se o valor sobe para 32.768 antes da rodada (5.12.4);
- janela de horário da conferência local, que o responsável define (de 24 horas ou menos; o plano sugere a noite);
- valor do salário mínimo de 2026, com o decreto que o fixou e a data da conferência: R$ 1.621,00, pelo Decreto 12.797, de 23/12/2025, conferido em 21/11/2026. A alçada do juizado fica em R$ 64.840,00;
- a data da conferência da lista de DDDs inexistentes;
- modo de chamada: uma a uma ou em lote (no MVP, uma a uma).

Mudar do MVP para o piloto é, em grande parte, mudar valores aqui.

**`config/gasto.toml`** — Só os valores de gasto: alerta de US$ 30 e corte de US$ 100, sendo US$ 100 o orçamento do mês. Fica num arquivo à parte para ser fácil de achar, e é congelado durante a rodada como os demais (5.12.2).

### 2.2 Dados que o responsável aprova

**`dados/catalogo/tipos.json`** — A lista de tipos de peça que a fábrica produz. Cada tipo tem:
- o rótulo exato da lista consolidada;
- família, perfil processual e classe de risco;
- modelo redator e quantidade de peças;
- se depende de uma peça ou decisão anterior, o que muda o cartão de revisão (5.9);
- os itens da lista de conferência que se aplicam a ele (Anexo B).

No MVP, três entradas:

| Tipo | Classe | O que testa |
|---|---|---|
| Petição Inicial em Juizado Especial Cível | Médio | Ficha, fatos, pedidos, valor e alçada |
| Embargos de Declaração | Alto | Coerência com uma decisão anterior fictícia. O rótulo é o dos embargos fora do juizado: a lista consolidada tem rótulo próprio para "Embargos de Declaração em Juizado Especial", e por isso a matriz nunca gera estes embargos em juizado (trava no Anexo A) |
| Manifestação sobre Aviso de Recebimento Negativo | Baixo | O caminho barato (Haiku), restrito a pedidos simples: informar novo endereço, pedir renovação da diligência no mesmo endereço ou dar ciência e pedir prazo. A matriz não gera pedido de citação por edital nem de pesquisa de endereço em sistemas |

**`dados/estruturas/familias/<familia>.json`** — O esqueleto comum de uma família de peças. Exemplo: toda petição inicial tem endereçamento, qualificação, fatos, fundamentos, pedidos e valor da causa. Cada bloco tem nome, ordem, se é obrigatório e uma descrição curta. É o primeiro nível da estrutura.

**`dados/estruturas/perfis/<perfil>.json`** — O que muda conforme o rito ou o juízo dentro da família. Exemplo: a inicial no Juizado Especial Cível não pede citação por edital e tem limite de valor. Acrescenta, retira ou ajusta blocos da família. É o segundo nível. Cada perfil também lista os **pedidos acessórios padrão** admitidos (por exemplo, `citacao_reu` e `producao_provas`), que a comparação com a ficha aceita mesmo sem estarem na ficha (Anexo D).

**`dados/estruturas/acrescimos/<tipo>.json`** — O que é próprio de um único tipo. Exemplo: os embargos de declaração apontam a omissão, a contradição, a obscuridade ou o erro material da decisão. É o terceiro nível, e muitos tipos não precisam dele.

**`dados/matrizes/<tipo>.json`** — As variações que se quer cobrir no tipo: matéria e tese principal; polo e tipo de parte; complexidade; momento processual; estilo. Também o teto por matéria (nenhuma matéria passa de 25% das peças do tipo, isto é, de 2 em 10) e, nos embargos, a distribuição dos defeitos: 2 omissões totais, 3 omissões parciais, 2 contradições, 2 obscuridades e 1 erro material. Os valores possíveis e a distribuição de cada eixo são os do Anexo A.6.

**`dados/normas/tabela_normas.json`** — Os dispositivos de lei que as peças podem citar. Cada um tem:
- texto vigente;
- diploma e assunto (o assunto permite ao programa achar um dispositivo do mesmo assunto com função diferente, para o erro de função trocada);
- função: requisito, prazo, competência, exceção, consequência ou definição;
- os tipos de peça em que se aplica (campo `tipos`);
- fonte e data da conferência.

Peça que cita algo fora da tabela é reprovada. Na preparação, o programa mostra, para cada tipo, quantos dispositivos do trecho da tabela têm par (mesmo diploma, mesmo assunto, função diferente), para que o responsável saiba antes de rodar se o tipo pode receber a função trocada (5.1).

**`dados/travas/travas.json`** — As regras que impedem combinações impossíveis, uma por linha. Cada trava tem:
- a condição, escrita como uma lista de condições simples que precisam valer todas juntas. Cada condição tem um campo da visão das travas (Anexo A.5), uma operação (`igual`, `diferente`, `maior`, `menor`, `na_lista`, `fora_da_lista`, `vazio` ou `preenchido`) e um valor, uma lista de valores ou outro campo para comparar (`vazio` e `preenchido` não levam valor). Exemplo: `[{"campo": "processo.rito", "op": "igual", "valor": "juizado_especial_civel"}, {"campo": "autor.categoria", "op": "fora_da_lista", "valor": ["pessoa_fisica", "mei", "microempresa", "empresa_pequeno_porte"]}]`. Uma condição com "ou" vira duas travas. Uma função curta avalia essas listas, sem executar texto como código e sem linguagem própria;
- o efeito: `proibe` ou `exige` e, no segundo caso, o campo exigido, que precisa estar `preenchido`;
- a base legal;
- os dispositivos da tabela a que se liga.

Há pelo menos uma trava que **proíbe** uma combinação cruzando campos (juizado especial cível com pessoa jurídica de direito público no polo ativo, art. 8º, § 1º, da Lei 9.099/1995) e uma que **exige** um campo quando outro tem certo valor (se o pedido da manifestação sobre aviso de recebimento negativo for informar novo endereço, a ficha precisa ter o novo endereço). A lista completa está no Anexo A.5.

**`dados/conferencia/lista_conferencia.json`** — A lista de conferência do Anexo B: cada item com nome, pergunta, quem confere, se é eliminatório e a que tipos se aplica.

**`dados/conferencia/termos_inequivocos.json`** — Os termos que reprovam direto, cada um com o motivo e a norma de hoje. Ponto de partida, da seção 6.1 do plano: prazo em quádruplo para contestar ou recorrer, exceção de incompetência no processo civil e pedido juridicamente impossível como causa de inépcia. A IA pode propor outros termos para os 3 tipos, e só entram os que forem erro em qualquer contexto.

**`dados/conferencia/palavras_ignoradas.json`** — As palavras que a âncora da omissão não conta como termos principais (Anexo E).

**`dados/conferencia/feriados_nacionais.json`** — Os feriados nacionais de 2026, para a contagem de prazo em dias úteis.

**`dados/erros/catalogo_erros.json`** — O catálogo de erros plantados do Anexo C: cada tipo de erro com a origem, os tipos de peça a que se aplica, o item principal e os itens aceitos.

**`dados/ficticios/listas_ficticias.json`** — As listas de onde os dados fictícios são sorteados: ruas e bairros inventados; cidades reais com a faixa de CEP de cada uma; profissões. Documentos, números de processo, telefones e e-mails não vêm daqui: são criados por programa. Nomes e OAB são marcadores fixos (5.2).

**`dados/ficticios/reais_permitidos.json`** — Os nomes reais que podem aparecer na peça: tribunais, juizados e comarcas; cidades e estados; entes públicos; sistemas e cadastros do processo; órgãos e siglas institucionais; nomes de leis e códigos; cargos e formas de tratamento forense; expressões latinas de uso jurídico. Nome de pessoa ou de empresa que não estiver aqui nem for um marcador de nome não pode aparecer.

**`dados/ficticios/reais_proibidos.json`** — Nomes de bancos, companhias aéreas, operadoras de telefonia, varejistas e outras empresas reais que costumam aparecer em processos. Serve para o detector reprovar a peça em que o modelo, por hábito, escreveu uma marca real. Não contém nenhum nome de `testes/dados/reais_reservados.json` (5.2).

### 2.3 Instruções aos modelos

**`instrucoes/ficha.md`** — O texto enviado ao Haiku para criar o caso fictício de uma combinação: fatos, datas, valores e documentos mencionados, nos campos do Anexo A. Nos tipos que dependem de peça anterior, cria também a decisão fictícia que a peça vai atacar, com o defeito que a matriz pediu e a âncora (Anexo E). Proíbe dados reais e nomes de juiz ou servidor (só o cargo), manda registrar na ficha todo valor que a peça vá usar, inclusive somas e dobros, e exige o formato JSON.

**`instrucoes/redacao.md`** — O texto enviado ao redator para escrever a peça a partir da estrutura, da ficha e do trecho da tabela. Manda seguir os blocos na ordem, citar só o que está na tabela, não inventar fatos fora da ficha, não calcular valores novos (usar só os valores da ficha) e não usar nenhum nome de pessoa ou de empresa além dos marcadores da ficha. A versão do arquivo é gravada em cada peça.

**`instrucoes/extracao.md`** — O texto enviado ao Haiku para extrair da peça, em formato estruturado:
- nomes, com o papel de cada um;
- documentos e números (CPF, CNPJ, OAB, número do processo, protocolos);
- valores, cada um com o texto como aparece na peça, o valor em centavos, inclusive os escritos por extenso, e o **lugar** em que aparece: `fatos` (a narrativa), `pedido` (com o pedido a que pertence), `valor_causa` ou `outro` (por exemplo, a fundamentação da competência). `valor_causa` é só o bloco formal do valor da causa, e `pedido`, só o bloco dos pedidos; um valor citado na fundamentação, mesmo o valor da causa ou o teto de 40 salários mínimos, é `outro`. Entram só quantias em dinheiro. Prazos ("5 dias úteis"), quantidades ("2 parcelas") e limites escritos em salários mínimos ("40 salários mínimos") não são valores e não entram na lista. O lugar é o que permite ao programa aplicar as regras do Anexo D sem julgar o papel do número no texto;
- datas, cada uma com o texto como aparece e a data completa ou parcial;
- comarca e juízo, com o texto como aparece;
- pedidos, cada um classificado na lista de naturezas do tipo (Anexo A) ou, quando não cabe em nenhuma, como `outro`, com o texto do pedido;
- peças anteriores mencionadas;
- data da peça.

O programa de regras compara essa extração com a ficha, pelas regras do Anexo D. No cartão de revisão, ela é só um auxílio: a referência é a ficha, mostrada ao lado.

**`instrucoes/checklist.md`** — A lista de itens de passa ou não passa do Anexo B respondida pelo Haiku, com os itens eliminatórios marcados e só os itens que se aplicam ao tipo. A resposta sai em JSON, item por item, com o trecho que justifica. Na mesma resposta, as notas de estilo de 1 a 5 (clareza, concisão, linguagem técnica), que só são registradas.

**`instrucoes/conferente_local.md`** — O texto curto enviado ao modelo local para responder os itens de coerência, peças anteriores e texto genérico (Anexo B). Pede resposta em JSON curto.

**`instrucoes/opus_desempate.md`** — O texto enviado ao Opus em três situações: quando o Haiku e o modelo local discordam num item; para conferir todos os itens das peças de risco alto; e para responder os itens do conferente local numa peça de risco médio que esperou mais de 72 horas (5.12.4). Pede decisão por item com justificativa.

**`instrucoes/plantar_erro.md`** — Dois textos:
- um enviado ao Opus para criar uma cópia da peça com um erro do tipo pedido (Anexo C), sutil ou direto conforme o pedido. O Opus não devolve a peça inteira: devolve o trecho original, copiado literalmente, e o trecho novo que o substitui. O programa faz a troca;
- outro enviado ao Sonnet, que não sabe qual erro foi pedido, com a original e a cópia, para dizer, escolhendo entre os itens da lista de conferência que se aplicam ao tipo (Anexo B, menos `semelhanca` e `marca`), que item o erro viola, descrever o erro e dizer se a troca criou algum outro problema.

### 2.4 Testes

Todos os testes precisam passar antes do ensaio. Nenhum teste chama a API ou o Ollama de verdade.

- **`test_regras.py`** — com peças de exemplo, cada regra reprova o que deve e aprova o que deve, inclusive alçada, prazo em dias úteis e termos inequívocos.
- **`test_travas.py`** — as condições das travas, inclusive as que cruzam campos, proíbem e permitem as combinações certas, nos dois efeitos (proíbe e exige); cada operação, inclusive `fora_da_lista`, `vazio` e `preenchido`; e a montagem da visão das travas a partir de fichas de exemplo.
- **`test_ancora.py`** — a âncora do defeito nas fichas de embargos, com fichas de exemplo certas e erradas para cada tipo de defeito, inclusive omissão total e parcial, e a extração dos termos principais, com exemplos em que o corte em 6 letras junta palavras diferentes e em que separa formas da mesma palavra (Anexo E).
- **`test_comparacao.py`** — as regras de tolerância do Anexo D com os exemplos de `testes/dados/comparacao_exemplos.json`: cada forma aceita passa, cada diferença real reprova. Inclui o caso da alçada e do salário mínimo em cada lugar (`fatos`, `outro`, `pedido` e `valor_causa`) e uma ficha com valor igual ao salário mínimo ou à alçada, que `fichas.py` recusa.
- **`test_citacoes.py`** — as formas compostas de citação (múltipla, com parte do artigo, por intervalo e elíptica) e o conjunto de 50 formas de `testes/dados/citacoes_50.json`, resolvido em 100%.
- **`test_ficticios.py`** — gera milhares de documentos, contatos e empresas fictícios: nenhum documento com dígito verificador válido, nenhum telefone com DDD existente, todo e-mail em `.example`, toda OAB e todo nome iguais aos marcadores fixos.
- **`test_dados_reais.py`** — planta dados reais de exemplo numa peça (documento válido, banco real, empresa aérea real, número de processo válido, OAB diferente do marcador, nome de pessoa que não é marcador, DDD real) e confere que o detector pega todos; planta os nomes de `testes/dados/reais_reservados.json`, que o detector não conhece, com a lista de proibidos vazia, e confere 100% pela regra de nome que não é marcador; confere também que nenhum nome reservado aparece em `fabrica/` nem em `dados/`; confere o contrário: termos jurídicos e nomes permitidos (SISBAJUD, Serasa, CNJ, expressões latinas, nomes de tribunais) não são acusados.
- **`test_estado.py`** — peças em cada estado, inclusive interrompidas no meio e com arquivo temporário deixado pela metade: o condutor decide o próximo passo certo, ignora o arquivo incompleto, para na terceira versão e aplica a regra do modelo local indisponível por classe, inclusive o pedido que não cabe no contexto (5.12.4).
- **`test_congelamento.py`** — muda uma letra num arquivo congelado e confere que a rodada para antes do passo seguinte; o mesmo com o `gasto.toml`.
- **`test_erros_programa.py`** — gera cada erro de regra feito por programa em peças de exemplo e confere que os programas de regra o pegam no item certo, e que o valor e a data trocados nunca coincidem com um valor, uma soma ou uma data da ficha (Anexo C.1).
- **`test_formatos.py`** — arquivos fora do formato são recusados: campo faltando, campo a mais, tipo errado.

Acréscimos do método, para que cada fase tenha critério verificável:
- **`test_entrega.py`** — num repositório git temporário: `entregar.sh` recusa commit com o gate vermelho, recusa quando há arquivo alterado fora do manifesto, commita só os arquivos do manifesto; `trava_git.sh` bloqueia `git add`, `git commit` e `git push` digitados e deixa passar `git status` e `entregar.sh`.
- **`test_config.py`** — falta de um valor obrigatório em `config.toml` ou `gasto.toml` para o programa antes de qualquer chamada.
- **`test_estatistica.py`** — o intervalo de Wilson de 95% bate com os números da v10: 80 em 100 dá de 71% a 87%; 32 em 40 dá limite inferior de 65,2%; 28 em 35 dá 64,1%; 5 em 5 dá de 57% a 100%; 2 em 25 dá de 2% a 25%.
- **`test_gasto.py`** — a previsão pessimista soma o gasto registrado, os pedidos enviados e não coletados e o pedido novo; o pedido que faria passar do corte não é enviado; o alerta dispara no valor do `gasto.toml`.
- **`test_api_claude.py`** — com cliente falso: todo pedido leva o formato de saída estruturada, o nível de esforço e o teto de saída da tarefa; nenhum pedido leva teto de tokens de raciocínio, uso forçado de ferramenta, parâmetros de amostragem nem troca automática de modelo; as três novas tentativas seguem as esperas de 30 segundos, 2 minutos e 8 minutos; resposta recusada ou cortada vira resposta fora do formato; o pedido é gravado antes de ser enviado.
- **`test_modelo_local.py`** — a tradução das respostas do `porteiro` (0, 1, 2, 3, falha e comando ausente); o pedido maior que o `num_ctx` pela estimativa pessimista não é enviado; o `num_ctx` vai sempre explícito.
- **`test_decisao.py`** — as regras do Anexo B.3, item por item, inclusive o caso do risco alto em que Haiku e modelo local concordam em "não passa" e o Opus diz "passa"; as quatro categorias do motivo; as notas de estilo fora do veredito.
- **`test_publicacao.py`** — nenhum arquivo sai de `publicacao.py` sem a marca "DOCUMENTO SINTÉTICO — FICTÍCIO" (no texto, no `.json` e no rodapé e nas propriedades do `.docx`).

### 2.5 Saída

**`saida/`** — Tudo que a fábrica produz, por etapa: pedidos, respostas, fichas, rascunhos, conferências, aprovadas, erros, cartões, pacotes, registro e relatórios. Fica fora do controle de versão e nada é apagado, para que qualquer resultado possa ser rastreado até a origem.

---

## 3. Contratos de dados

Todos os contratos ficam em `fabrica/comum/formatos.py`, como modelos do Pydantic 2 estritos: `extra="forbid"` e modo estrito, de modo que campo faltando, campo a mais e tipo errado são recusados. Todo arquivo é validado ao gravar e ao ler. Os mesmos modelos geram o esquema JSON enviado à API e ao Ollama para as respostas estruturadas. Valores em dinheiro sempre em centavos, como número inteiro; datas sempre ano-mês-dia.

```
Ficha            campos do Anexo A: comuns (A.1), da Petição Inicial em Juizado Especial Cível (A.2),
                 dos Embargos de Declaração (A.3), da Manifestação sobre Aviso de Recebimento Negativo (A.4)
VisaoTravas      tipo, processo.rito, materia, autor.categoria, autor.capaz, autor.preso, reu.categoria,
                 reu.capaz, reu.preso, valor_causa_centavos, alcada_centavos, defeito.tipo,
                 defeito.ancora.argumento_id, defeito.trecho_mencao, pedido_ar,
                 aviso_recebimento.motivo_devolucao, novo_endereco, meio_nova_diligencia, nova_diligencia (Anexo A.5)
Trava            condicoes[] (campo, op, valor | lista de valores | outro campo), efeito (proibe | exige),
                 campo_exigido, base_legal, dispositivos[]
Dispositivo      id, diploma, artigo, paragrafo, assunto, funcao, texto_vigente, tipos[], fonte, data_conferencia
Pedido (à API)   rodada, peca, tarefa, modelo, esforco, teto_saida, partes do pedido na ordem fixa (seção 7),
                 esquema de saída quando a resposta é JSON
Resposta         pedido de origem, modelo, conteúdo como chegou, motivo de parada, tokens
Rascunho         texto .md e metadados de origem: ficha, estrutura, versão das instruções, modelo, versão (v1 a v3)
Extracao         nomes[] (papel), documentos[], valores[] (texto, centavos, lugar: fatos | pedido | valor_causa | outro,
                 pedido a que pertence), datas[] (texto, data completa ou parcial), comarca, juizo, pedidos[]
                 (natureza ou outro, texto), pecas_anteriores[], data_peca
Conferencia      extração, resultado por item (resposta, quem respondeu, trecho), caminho de cada item até a resposta
                 final (Anexo B.3), notas de estilo, alertas, veredito (aprovada | refazer | descartada),
                 categoria do motivo (conteudo | semelhanca | ambos | formato)
CopiaComErro     copia, original, trecho original, trecho novo, tipo_erro, sutil, criador
Gabarito         copia, original, origem (programa_regra | programa_julgamento | opus), tipo_erro, sutil,
                 item_principal, itens_aceitos, criador, verificador, item_apontado_pelo_verificador,
                 amostra (vazio | aceita | rejeitada) (Anexo C.4)
Descartada       copia, original, tipo_erro, sutil, criador, conferencia_que_falhou (programa | verificador),
                 item_apontado_pelo_verificador, outro_problema, motivo (outro_problema | outro_item | nao_viu_erro),
                 amostra (vazio | erro existe | erro não existe) (Anexo C.4)
Cartao           id, tipo de cartão (revisão, ensaio, amostra de 10 cópias, amostra das descartadas,
                 leitura de publicação), etapa (1 ou 2), conteúdo mostrado
RespostasCartao  id do cartão, veredito da ficha, veredito da peça, dado real (sim ou não, trecho),
                 citações marcadas como não resolvidas, data da confirmação
Rodada           id (e01... para ensaios, r01... para rodadas), semente, impressões digitais congeladas,
                 ensaio aprovado de origem, estado (aberta, parada, encerrada, inválida)
Chamada          modelo, tokens de entrada, de cache, de raciocínio e de saída, custo, duração, peça
Ocorrencia       tipo (pausa, parada, intervenção, contexto), causa, início, fim, peça
Metadados (.json do pacote)
                 tipo (rótulo exato), classe de risco, família, perfil, matéria, tese, polo, complexidade, estilo;
                 ficha completa, identificador do processo fictício e semente; modelo redator, nível de esforço,
                 versão das instruções e custo; versão da tabela de normas; resultado de cada conferência, item por
                 item, e se a conferência local rodou; marca de sintético
```

Os campos da ficha ficam em `formatos.py` exatamente como no Anexo A. Por isso, uma área nova do direito muda este arquivo além dos dados.

---

## 4. Esquema de dados — pontos que não são óbvios

**Não há banco de dados.** O estado da fábrica são os arquivos de `saida/`. `estado.py` não guarda nada próprio: descobre o ponto de cada peça olhando os arquivos. Se o programa for interrompido, a próxima execução retoma do ponto certo.

**Gravação atômica.** Todo arquivo é gravado primeiro num arquivo temporário e só depois renomeado para o nome final. Um arquivo pela metade nunca aparece com o nome final, e por isso `estado.py` pode confiar nos arquivos; o temporário que sobrar é ignorado.

**Nada é sobrescrito nem apagado.** Uma refação gera arquivo novo (`_v2`, `_v3`). Gerar de novo, com a mesma semente ou com outra, abre uma rodada nova.

**Nomes padronizados.** Rodada, tipo, número da peça e versão no nome: `r01_embargos_declaracao_007_v2.md`. Cada execução das 30 peças é uma rodada, com identificador e semente próprios em `saida/rodadas.json`. Os ensaios usam `e01`, `e02`... e a rodada do MVP começa em `r01`. O relatório sempre diz de qual rodada são os números.

**Resposta de modelo é guardada como chegou.** `saida/respostas/` guarda a resposta sem conserto. Resposta fora do formato nunca é corrigida com expressão regular: faz-se um novo pedido (seção 7). A normalização do Anexo D e do Anexo E roda sobre cópias, na hora da comparação, e nunca sobre o texto guardado.

**Respostas do responsável não mudam depois de confirmadas.** O comando `revisar` grava `saida/cartoes/<id>_respostas.json` só depois da confirmação, e a segunda etapa do cartão, com o veredito da fábrica, só é gerada a partir desse momento. Mudar depois quebraria a leitura às cegas. Nenhum arquivo de `saida/` é editado à mão (5.12.3).

**Origem obrigatória.** Toda peça guarda a origem: ficha, estrutura, versão das instruções e modelo. Toda chamada é registrada com custo em `chamadas.jsonl`, que é a fonte única do controle de gasto e dos relatórios.

**Congelamento.** No início de cada rodada, `congelamento.py` grava em `saida/rodadas.json` a impressão digital (um código tirado do conteúdo, que muda se uma letra mudar) de cada arquivo de `dados/`, de `instrucoes/`, de `config/config.toml` e `config/gasto.toml`, e da versão do código (a do controle de versão, que precisa estar sem mudanças pendentes). Detalhe em 5.12.2.

**Cópias de treino sem a marca não existem no MVP.** Nenhum arquivo sai da fábrica sem a marca. Quando existirem (Fase 4 do plano), ficam numa pasta própria fora de `saida/pacotes/` e de qualquer pasta sincronizada ou compartilhada, só o dono do projeto tem acesso, a origem sintética fica nos metadados de cada arquivo, nunca são publicadas nem entregues a terceiros e são apagadas quando o conjunto de treino que as usou for descartado.

---

## 5. Lógica central

### 5.1 O critério central e o volume do teste

**A conferência precisa pegar pelo menos 80% dos erros plantados nas cópias feitas por IA, e o limite inferior do intervalo de confiança de 95% dessa taxa precisa ficar em pelo menos 65%.**

- O intervalo é calculado pelo **método de Wilson** (`estatistica.py`). Com 100 cópias, o critério exige pelo menos 80 erros pegos; com 80 de 100, a faixa vai de 71% a 87%. A partir de 40 cópias, quem decide é a taxa observada de 80%: o limite inferior de 65% já vem junto.
- Um erro só conta como pego quando a conferência reprova a cópia **e** reprova um dos itens que o gabarito aceita para aquele erro (Anexo C). Reprovar a cópia por outro motivo não conta.
- Esse item aceito precisa ter **passado na original** da cópia, que o teste confere de novo junto com as cópias (5.8). Se a conferência já reprova o item na original, reprová-lo na cópia não mostra que ela viu o erro plantado.

**Viés do Opus, medido.** O Opus cria quatro quintos das cópias com erro e é também conferente avaliado (confere todas as peças de risco alto e desempata as demais). O relatório registra, ao lado do critério central:
1. **Taxa sem o Opus:** mesmo denominador do critério central (as cópias feitas por IA no banco). No numerador, só os erros pegos pelo critério central em que algum conferente que não é o Opus (programas, Haiku ou modelo local) também marcou "não passa" num item aceito que passou na original. Por construção, nunca passa da taxa completa.
2. **Taxa nos erros de julgamento feitos por programa:** erros criados sem nenhum modelo (Anexo C.2). O relatório mostra a contagem ao lado da taxa. Com menos de 5 cópias de julgamento, a taxa é **inconclusiva** e só os casos são listados.

Se a taxa sem o Opus ficar mais de 15 pontos abaixo da taxa completa, o resultado é marcado **dependente do Opus**: o critério continua decidindo, a decisão de escalar registra a ressalva e o piloto passa a exigir um criador de erros que não seja conferente avaliado. Os 15 pontos são escolha declarada antes de rodar, não teste estatístico.

**Volume: cinco cópias com erro para cada peça boa** (ficha e peça aprovadas pelo responsável, 5.12.7): uma feita por programa e quatro pelo Opus, cada uma com um tipo de erro diferente. Todas partem da primeira versão da peça boa. O Sonnet não cria cópias: ele verifica 100% das cópias do Opus, e quem verifica não pode ser criador nem conferente avaliado.

**As cópias por programa se dividem em dois grupos:**
- **erros de regra** (Anexo C.1): os programas de regra precisam pegar 100%; servem de conferência de sanidade;
- **erro de julgamento** (dispositivo com função trocada, Anexo C.2): existe com certeza, mas só um conferente de IA o pega; serve de diagnóstico e de controle do viés do Opus e não entra no critério central.

Cada peça boa recebe um erro de programa, sorteado pela semente da rodada. A função trocada vai para metade das peças boas, arredondada para baixo, escolhidas primeiro entre as que citam algum dispositivo com par na tabela; as outras recebem um erro de regra. Se menos da metade tiver dispositivo com par, todas as que têm recebem a função trocada. Se nenhuma peça de um tipo tiver par, esse tipo fica com zero cópias de julgamento: a medida cobre só os tipos com par, e o relatório mostra quantas cópias de julgamento houve em cada tipo.

**Conta:** com cerca de 25 peças boas, são cerca de 125 cópias, 100 delas feitas por IA. A conta supõe cópias independentes; quatro cópias da mesma original não são de todo, e por isso a faixa real é um pouco mais larga. Com bem menos de 25 peças boas, vale o plano B (5.12.6).

### 5.2 Dados fictícios e o detector de dado real

**Pode ser real, porque é público ou necessário** (lista em `dados/ficticios/reais_permitidos.json`): tribunais, varas, juizados e comarcas; cidades e estados, inclusive o CEP da cidade; entes públicos (União, estados, municípios, INSS e outros da lista); sistemas e cadastros usados no processo (SISBAJUD, RENAJUD, INFOJUD, Serasa, SPC e outros da lista); órgãos e siglas institucionais (CNJ, OAB, Ministério Público, Defensoria); leis, códigos, dispositivos e expressões latinas de uso jurídico; cargos e formas de tratamento forense (Juiz de Direito, Excelentíssimo Senhor Doutor, Meritíssimo); o salário mínimo.

**Nunca pode ser real, e é criado por programa** (`ficticios.py`):

| Dado | Regra | Como o detector confere |
|---|---|---|
| Nome das partes | Marcador evidente, fixo por papel e categoria: "Nome e Sobrenome da Parte Autora" e "Nome e Sobrenome da Parte Ré" para pessoa física; "Razão Social da Parte Autora" e "Razão Social da Parte Ré" para empresa (inclusive bancos, companhias aéreas, operadoras e lojas) | Todo nome com aparência de pessoa ou de empresa que não seja um marcador nem esteja na lista de reais permitidos reprova; coincidência com a lista de reais proibidos também |
| Nome do advogado | Marcador "Nome e Sobrenome do Advogado" | A mesma regra dos nomes das partes |
| CPF e CNPJ | Formato correto, dígito verificador propositalmente inválido | Todo CPF ou CNPJ com dígito verificador válido reprova. O detector calcula o dígito também no formato de CNPJ com letras (cada caractere vale o seu código ASCII menos 48, com os mesmos pesos e o mesmo resto da divisão por 11). A Receita emite CNPJ com letras desde 31/07/2026 (Instrução Normativa RFB 2.229/2024) |
| Número do processo | Padrão do CNJ (sete dígitos, dígito verificador, ano, ramo, tribunal e unidade), com o ramo e o tribunal coerentes com o juízo da ficha e o **dígito verificador propositalmente inválido** (o cálculo oficial é pelo resto da divisão por 97) | Todo número no padrão do CNJ com dígito verificador válido reprova |
| OAB | Marcador "OAB/UF nº 000.000", igual em todas as peças | Qualquer número de OAB diferente do marcador reprova |
| Telefone | DDD inexistente, sorteado da lista 20, 23, 25, 26, 29, 36, 39, 52, 56, 57, 58, 59, 72, 76 e 78. O país usa 67 DDDs (11 a 19, 21, 22, 24, 27, 28, 31 a 35, 37, 38, 41 a 49, 51, 53 a 55, 61 a 69, 71, 73 a 75, 77, 79, 81 a 89 e 91 a 99), e nenhum dos 15 da lista está entre eles. A data da conferência fica no `config.toml` | Telefone com DDD existente reprova |
| E-mail | Domínio terminado em `.example`, reservado para exemplos pela norma da internet (RFC 2606) | E-mail com qualquer outro final reprova |
| Endereço | Rua e número fictícios, de listas inventadas, em cidade real, com o CEP da faixa daquela cidade. Todas as faixas de CEP do país estão distribuídas entre os estados, e um CEP sozinho não identifica ninguém: o que torna o endereço fictício é a rua | O nome da rua precisa estar na ficha. O CEP não é conferido |
| Dados bancários | Código de banco inexistente, fora da lista oficial de participantes do sistema de pagamentos, e banco com nome fictício. Nenhum dos 3 tipos do MVP usa dados bancários; a regra fica pronta em `ficticios.py` | Código de banco da lista oficial reprova |
| Contratos, protocolos e outros números do caso | Prefixo `SINT-` | Número de contrato ou de protocolo sem o prefixo reprova |
| Valores e datas | Sorteados pela matriz | Não se aplica: valores e datas não identificam ninguém |

**Como se confere:**
1. **Por construção:** os dados acima nascem fictícios no programa, sem passar por modelo.
2. **Por detecção:** `dados_reais.py` aplica a coluna da direita. Para os nomes, só procura nomes com aparência de pessoa ou de empresa, para não acusar falsamente termos jurídicos. Conta como nome: duas ou mais palavras com inicial maiúscula fora do início de frase; palavra acompanhada de tratamento (Sr., Sra., Dr.); palavra acompanhada de forma societária (Ltda., S.A., ME, EIRELI); palavra acompanhada de "Banco", "Companhia" ou similar. Todo nome encontrado precisa ser um dos marcadores de nome da ficha ou estar na lista de reais permitidos. O detector ignora os títulos dos blocos da estrutura montada e a marca de documento sintético. A decisão fictícia e a peça não dão nome a juiz, servidor ou membro do Ministério Público, só o cargo; um nome assim, que não é marcador, reprova como qualquer outro. Qualquer achado reprova.
3. **Verificação independente do detector:**
   - **teste com nomes guardados à parte:** `test_dados_reais.py` planta nomes de empresas reais de `testes/dados/reais_reservados.json`, que **não** está em `reais_proibidos.json` e que quem escreve o detector não usa. O detector precisa pegar 100% deles pela regra de "nome que não é marcador"; A garantia não é a cegueira de quem escreve o detector, que roda no mesmo repositório e pode ler o arquivo: é que o teste dos reservados roda com a lista de proibidos vazia, e por isso só passa pela regra de "nome que não é marcador", e que um teste confere que nenhum nome reservado aparece em `fabrica/` nem em `dados/`;
   - **leitura do responsável:** o cartão de cada uma das 30 primeiras versões tem a pergunta fixa "há algum nome, número ou dado que pareça real?", com resposta sim ou não e o trecho. O cartão da leitura de publicação repete a pergunta.

**Como se apura o critério "zero":** não pode haver dado real em nenhuma peça que o responsável leu e que a fábrica aprovou, nem em nenhuma peça publicada. Conta como dado real tudo o que o responsável marcar no cartão e se confirmar, e tudo o que o teste com nomes guardados à parte deixar passar. O que o detector pega e reprova não conta como escape.

### 5.3 O condutor das peças (`estado.py`)

Olhando os arquivos em `saida/`, descobre em que ponto cada peça está: ficha pronta; pedido de redação enviado; rascunho pronto; em conferência; esperando o modelo local; reprovada com refação pendente; aprovada; revisada pelo responsável; publicada. Com isso, decide o próximo passo. Coleta as respostas da API que estão prontas, entrega cada uma à etapa seguinte e conta as refações, parando na terceira versão. Antes de cada passo, pede a `congelamento.py` que confira os arquivos da rodada (5.12.2).

Os módulos de etapa nunca esperam resposta: gravam o pedido e terminam. A coleta é de `estado.py`.

É também em `estado.py` que fica a regra única do que acontece com a peça quando o modelo local não está disponível (5.12.4).

### 5.4 Fichas (`matriz.py`, `ficticios.py`, `fichas.py`)

`matriz.py` sorteia as combinações da matriz respeitando as travas e o teto por matéria, com uma semente gravada, para refazer o mesmo sorteio. Avalia as condições das travas que cruzam campos sobre a visão das travas (Anexo A.5). Sorteia também a data da peça nos tipos com prazo, com pelo menos um dia útil de folga antes do fim do prazo. Os eixos com número fixo são cruzados pelo sorteio; se o sorteio não achar combinação que respeite as travas e o teto em 1.000 tentativas, a matriz volta para a preparação.

`ficticios.py` gera, pelas regras de 5.2: CPF e CNPJ com dígito inválido; número de processo no padrão do CNJ, coerente com o juízo, com dígito inválido; os marcadores de nome e de OAB; telefone com DDD inexistente e e-mail em `.example`; endereço com rua inventada em cidade real e CEP da faixa da cidade; código de banco inexistente; números de contrato e de protocolo com `SINT-`.

`fichas.py` junta, para cada combinação, os dados fictícios e grava o pedido ao Haiku dos fatos do caso, e da decisão anterior quando o tipo depende dela. Quando a resposta chega, confere formato e coerência básica e grava a ficha:
- datas em ordem;
- valor da causa igual à soma dos valores dos pedidos (art. 292, VI, do CPC), e no dano moral, o valor pretendido (art. 292, V);
- alçada respeitada no juizado (até R$ 64.840,00);
- nenhum valor da ficha igual a R$ 1.621,00 ou a R$ 64.840,00;
- fundamentos da ficha todos dentro do trecho da tabela do tipo (5.5);
- travas respeitadas, sobre a visão das travas da ficha pronta;
- nos tipos que dependem de decisão anterior, a **âncora do defeito**, pelas regras do Anexo E.

**Ficha que falha** no formato, em qualquer item acima ou na âncora volta para o Haiku uma vez, com o motivo. Se falhar de novo, é descartada e registrada, e a mesma casa da matriz recebe uma ficha nova, com dados fictícios novos tirados da semente. Como a casa é a mesma, a distribuição da matriz, inclusive a dos defeitos, se mantém. Uma casa recebe no máximo duas fichas novas; depois fica vazia, registrada, e o tipo segue com menos de 10 peças. Tudo isso é operação normal.

**Datas do MVP:** todas as fichas têm data de ajuizamento em 2026, e todas as datas posteriores aos fatos (decisão, intimação, juntada do aviso, termo final do prazo e data da peça) ficam em 2026; a matriz não sorteia data que leve o prazo para 2027. Fatos até 2 anos antes do ajuizamento.

### 5.5 Redação e o trecho da tabela (`redacao.py`)

Monta o pedido na ordem fixa (seção 7), com estrutura, ficha e trecho da tabela, e o grava para o redator indicado no catálogo. Quando a resposta chega, grava o rascunho com os metadados de origem. Na refação, acrescenta o motivo da reprovação e gera nova versão.

**Regra do trecho:** o trecho é formado por todos os dispositivos da tabela cujo campo `tipos` inclui o tipo da peça, em ordem fixa (diploma, artigo, parágrafo). É o mesmo para todas as peças do tipo, o que o deixa pronto para o cache na escala. Se o trecho de um tipo passar de 8 mil tokens, a tabela daquele tipo é grande demais e volta para a preparação. A ficha só pode listar fundamentos de dentro do trecho.

`estruturas.py` monta antes a estrutura completa de um tipo, juntando família, perfil e acréscimos, confere que nenhum bloco obrigatório sumiu e grava a estrutura montada para o responsável aprovar.

### 5.6 Conferência (`fabrica/conferencia/`)

- **`extracao.py`** grava o pedido ao Haiku com a instrução de extração e, quando a resposta chega, grava a extração estruturada da peça.
- **`regras.py`** confere por programa: blocos obrigatórios presentes e na ordem; extração igual à ficha, com as tolerâncias do Anexo D; alçada; prazo; termos inequívocos; marca "DOCUMENTO SINTÉTICO — FICTÍCIO". É a primeira barreira, a mais barata. As travas não são conferidas aqui: valem sobre a ficha, e a extração da peça não lê os campos delas. Uma peça que se afasta da ficha em partes, juízo ou pedidos é reprovada por `coerencia_ficha`.
- **`citacoes.py`** encontra cada citação de lei, inclusive as compostas (múltipla, com parte do artigo, por intervalo e elíptica), e confere se está na tabela. Citação fora da tabela reprova; citação não reconhecida vira alerta e vai para o checklist como pergunta, nunca é aprovada sem conferência.
- **`dados_reais.py`** aplica a detecção de 5.2. Qualquer achado reprova.
- **`checklist.py`** grava o pedido ao Haiku com os itens que se aplicam ao tipo e, quando a resposta chega, grava o resultado item por item e as notas de estilo.
- **`local.py`** envia a peça ao modelo local pelos serviços de `modelo_local.py` e grava a resposta, ou o resultado "indisponível". Não decide o que acontece depois: isso é de `estado.py`. O modelo local confere todas as peças de risco médio e alto e 20% das de risco baixo: 2 das 10 manifestações, sorteadas pela semente. No teste dos conferentes, cada cópia segue a sua original: se a original passou pelo modelo local, a cópia também passa.
- **`desempate.py`** grava o pedido ao Opus e, depois, a decisão, nas três situações de `opus_desempate.md`. Numa mesma peça, todas as perguntas ao Opus vão num pedido só.
- **`semelhanca.py`** compara a peça nova com as já aprovadas do mesmo tipo e reprova a quase cópia. A comparação é só textual: a proporção de trechos de cinco palavras seguidas em comum entre as duas peças (índice de Jaccard, calculado exatamente), depois de tirar a marca, os títulos dos blocos e os marcadores de nome e de OAB e de passar o texto a minúsculas sem acento. Reprova a partir de 0,85, o limite inicial do plano. O limite não é calibrado e fica registrado. A reprovação por semelhança é gravada com marca própria. Fica desligado no teste dos conferentes de forma automática: o teste chama a conferência em modo de teste, que ignora este módulo sem que ninguém mexa no `config.toml`.
- **`decisao.py`** junta todas as conferências e decide: aprovada, refazer com o motivo, ou descartada. A regra é uma só: "não passa" em item eliminatório reprova a peça. Como cada item chega à resposta final está no Anexo B.3. Grava o veredito com o caminho de cada item e separa o motivo em quatro categorias: **conteúdo** (qualquer item eliminatório que não seja semelhança), **semelhança**, **ambos** e **formato** (5.12.8). As notas de estilo ficam gravadas e não entram no veredito.

### 5.7 Erros plantados (`erros_plantados.py`)

Cria cinco cópias com erro para cada peça boa, ou mais pelo plano B (5.12.6):
- uma por programa, de um tipo de erro sorteado entre os erros de regra e os de julgamento do Anexo C, com a resposta certa conhecida. O programa acha o trecho a trocar pelo texto que a extração da original devolveu;
- quatro pelo Opus, de tipos diferentes entre si, sorteados do catálogo do Anexo C entre os que se aplicam ao tipo da peça, metade sutis.

O sorteio equilibra os tipos de erro no conjunto e usa a semente da rodada.

Cada cópia feita por IA passa por três conferências:
1. **programa:** o trecho original devolvido pelo Opus aparece exatamente uma vez na peça, a troca muda uma única região contínua, essa região não passa de um quarto do texto, e o resto ficou idêntico. Além disso, os itens de programa do Anexo B.1 (menos `semelhanca`), rodados na cópia, não reprovam nenhum item fora dos itens aceitos do tipo de erro; se reprovarem, a troca criou outro problema e a cópia segue a regra de descarte;
2. **verificador:** o Sonnet, sem saber qual erro foi pedido, diz que item da lista o erro viola e se a troca criou outro problema. A cópia só passa se o item que ele apontar estiver entre os itens aceitos do gabarito e não houver outro problema. O verificador nunca é um dos conferentes avaliados;
3. **programa:** o gabarito aponta o item principal e os itens aceitos do tipo de erro, tirados do catálogo.

**Descarte.** A cópia que não passar é descartada e refeita uma vez; se falhar de novo, sorteia-se outro tipo de erro para aquela vaga. O custo das descartadas é registrado à parte. Cada descarte fica em `saida/erros/descartadas.json` (Anexo C.4), com o **motivo**, decidido por programa. Se o Sonnet não apontar item nenhum, o motivo é sempre **não viu erro**, mesmo que ele descreva outro problema. Fora esse caso:
- **outro problema:** o Sonnet disse que a troca criou outro problema. Descarte correto;
- **outro item:** o Sonnet viu um erro, mas o ligou a um item fora dos itens aceitos;
- **não viu erro:** o Sonnet disse que a cópia não tem erro.

**Amostra de 10 cópias:** sorteadas entre as cópias feitas por IA que passaram nas três conferências. Para cada uma, o responsável diz se o erro existe e se é o do gabarito. Cópia rejeitada sai do banco. Com 2 ou mais rejeitadas, o banco é marcado **não confiável**: o critério central é calculado e registrado, mas não decide, e a verificação precisa ser corrigida antes de um novo teste.

**Amostra das descartadas:** até 5 cópias sorteadas entre as descartadas por **não viu erro** (todas, se forem menos de 5), sem mostrar o que o Sonnet respondeu. Para cada uma, o responsável diz se o erro pedido existe na cópia. Se existir em 2 ou mais, o banco é marcado **filtrado pelo verificador**: o critério central continua decidindo, mas a decisão de escalar registra a ressalva, ao lado da taxa de descarte por motivo, por tipo de erro e por sutileza. Os descartes por **outro item** são listados no relatório por tipo de erro, com o item que o Sonnet apontou. As cópias descartadas não voltam ao banco, porque o banco é fechado antes do teste, pela mesma regra para todas as cópias.

### 5.8 Teste dos conferentes (`teste_conferentes.py`)

Passa as cópias com erro e as peças boas por toda a conferência, sem que ela saiba quais são quais, com a semelhança desligada. É uma passagem só, sem refação. Um erro só conta como pego pela regra de 5.1. Cópia cuja conferência termina na categoria "formato" conta como não pega, e é listada. Calcula, todos com a margem de Wilson:
- a **taxa de erros pegos nas cópias feitas por IA**, que é o critério central;
- a **taxa sem o Opus** e a **taxa nos erros de julgamento feitos por programa** (5.1), esta com a contagem de cópias ao lado e inconclusiva com menos de 5;
- a taxa nos erros de regra feitos por programa, como conferência de sanidade (precisa ser 100%);
- a **taxa de reprovação no teste**: a proporção das peças boas que a conferência reprovou ao passarem de novo por ela. Só descreve; a medida que decide é a da primeira versão (seção 6);
- esses números separados por conferente, por tipo de erro e por origem do erro, como diagnóstico qualitativo.

### 5.9 Revisão humana (`revisao.py`)

Gera o cartão de revisão para a primeira versão de cada uma das 30 peças, aprovada ou não pela fábrica, sem mostrar o veredito dela.

1. **Primeira etapa:** a peça; a ficha, sempre, com partes, datas, valores, comarca e pedidos (nos tipos que dependem de peça anterior, inclui a decisão fictícia, com o trecho da âncora destacado); os fatos e valores tirados da extração, como auxílio; o texto dos dispositivos citados e a lista de todas as citações que o programa resolveu (citação no texto e fora da lista é marcada pelo responsável, porque escapou do programa). O responsável responde:
   - o veredito da **ficha**: o caso fictício faz sentido e, nos embargos, o defeito existe na decisão;
   - o veredito da **peça**, por um critério só, escrito no cartão: **a peça pode virar modelo como está, na forma e no conteúdo.** Peça com bloco obrigatório faltando é reprovada mesmo que o conteúdo seja bom;
   - a pergunta fixa de dado real: **há algum nome, número ou dado que pareça real?**
2. **Segunda etapa:** só depois de as respostas gravadas, a segunda parte, com o veredito da fábrica **sobre a mesma primeira versão**, a categoria do motivo e os alertas (os itens que algum conferente reprovou ou aprovou por pouco, cada um com a origem: programa de regras, citações, dados reais, checklist do Haiku, conferente local ou Opus).

Registra a concordância sobre a primeira versão, nos dois sentidos. O destino final da peça depois das refações fica registrado à parte. O destino de cada peça conforme os dois vereditos está em 5.12.7.

### 5.10 Publicação (`publicacao.py`)

Monta o pacote com as peças publicáveis: `.md`; `.json` com os metadados (seção 3); `.docx` com a marca no rodapé e nas propriedades do arquivo; e o índice.

É publicável a peça cuja ficha o responsável aprovou e cuja versão aprovada pela fábrica ele leu e aprovou. Na maior parte dos casos é a primeira versão. Quando a fábrica aprovou uma versão refeita (v2 ou v3), essa versão só é publicada depois da **leitura de publicação**: um cartão simples, não às cegas, que não entra em nenhuma medida, salvo a pergunta fixa de dado real, que ele repete. Sem essa leitura, a peça fica registrada como aprovada pela fábrica e não publicada. Nenhum arquivo sai sem a marca.

### 5.11 Relatório do MVP (`relatorios.py`)

Escreve `saida/relatorios/relatorio_mvp.md` com:
- cada critério da seção 6, o resultado e a margem de Wilson, com o critério central em primeiro lugar, acompanhado da taxa sem o Opus e da taxa nos erros de julgamento feitos por programa;
- reprovações de peças boas separadas por conteúdo e por semelhança;
- o que a regra de estilo teria reprovado;
- custo por peça, custo marginal por peça aprovada e custos únicos separados, incluindo o das cópias descartadas;
- tempo do modelo local e janelas sem conferência local, com a marca de **sem conferente local estável**, se for o caso (5.12.4);
- causas de reprovação; fichas reprovadas pelo responsável e as causas;
- pausas e intervenções da rodada, de `ocorrencias.jsonl`;
- quantas peças cada tipo fechou (por exemplo, 10 de 10 ou 9 de 10) e as casas vazias, com a causa;
- as cópias descartadas, por conferência, por motivo, por tipo de erro e por sutileza, com o resultado da amostra das descartadas e, se for o caso, a marca de banco filtrado; os descartes por outro item, com o item que o Sonnet apontou;
- os tipos de erro do banco final, contados ao lado dos planejados pelo sorteio, e quantas vagas trocaram de tipo depois de duas falhas;
- os pedidos ao modelo local que não couberam no contexto, se houver;
- os tokens reais de cada tarefa, medidos no ensaio;
- cada reprovação por `coerencia_ficha` com o valor extraído e o da ficha, para separar erro da peça de erro da extração;
- uma tabela de erros não pegos por conferente e por tipo de erro (cabimento, prazo, valor, dispositivo com função trocada e outros), como diagnóstico qualitativo. É ela que mostra em que módulo está a falha quando um critério não é atingido.

### 5.12 Regras de operação da rodada

Estas regras ficam escritas antes de rodar, para que nenhuma decisão seja tomada depois de ver o resultado.

#### 5.12.1 Ensaio de três peças: passa ou para

**O ensaio passa** quando as três peças percorrem todas as etapas, de ficha a cartão e pacote, e o caminho dos erros em miniatura (1.4), sem erro de programa (exceção, arquivo recusado pelo formato, passo que não avança) e o responsável confirma, no cartão, que tudo saiu no formato certo. O veredito da fábrica sobre a qualidade da peça não conta.

**Se o ensaio falhar, o programa para.** O comando `fichas` da rodada do MVP recusa começar sem um ensaio aprovado registrado em `saida/rodadas.json`. Corrige-se a causa e faz-se um ensaio novo (`e02`, `e03`...), com o custo registrado. O ensaio aprovado grava as impressões digitais dos arquivos; a rodada do MVP só começa se os arquivos forem os mesmos do ensaio aprovado. Se algo mudar depois do ensaio, é preciso um ensaio novo.

#### 5.12.2 Congelamento durante a rodada

No início de cada rodada, `congelamento.py` grava a impressão digital de cada arquivo de `dados/`, de `instrucoes/`, de `config/config.toml` e `config/gasto.toml` e da versão do código (a do controle de versão, sem mudanças pendentes). Antes de cada passo, `estado.py` confere essas impressões. **Se alguma mudou, a rodada para** antes do passo seguinte e grava a ocorrência. Há só duas saídas: desfazer a mudança e seguir; ou encerrar a rodada como inválida para o critério de ponta a ponta e abrir outra. Nenhum arquivo de governo fica fora do congelamento.

#### 5.12.3 O que é intervenção manual

| Situação | Classificação | Efeito |
|---|---|---|
| Rodar os comandos previstos, inclusive `avancar` de novo depois de uma interrupção, falta de energia ou reinício da máquina | Operação normal | Nenhum |
| Dar os vereditos nos cartões, conferir a amostra de 10 cópias e a amostra das descartadas, fazer a leitura de publicação, sempre pelo comando `revisar` | Operação normal | Nenhum |
| Ficha nova na mesma casa da matriz, ou casa vazia, pela regra de `fichas.py` (5.4); destino por formato de 5.12.8 | Operação normal | Registrado. Nenhum |
| Aprovar os dados na preparação, antes da rodada | Operação normal | Nenhum |
| Novas tentativas automáticas de `api_claude.py` (seção 7) e esperas do `porteiro` | Operação normal | Nenhum |
| Peça parada porque a API ou o modelo local ficou indisponível, depois das tentativas automáticas | Pausa | Registrada em `ocorrencias.jsonl`, com causa, início e fim. Não invalida. O próximo `avancar` retoma |
| Corte de gasto atingido (5.12.5) | Parada | Registrada. A rodada termina ali; os critérios que dependem do que não foi feito ficam inconclusivos |
| Peça de risco alto esperando o modelo local por mais de 7 dias (5.12.4) | Pausa | Registrada. Não invalida |
| Abrir um arquivo de `saida/` só para ler | Operação normal | Nenhum |
| Editar à mão qualquer arquivo de `saida/` (ficha, rascunho, conferência, veredito, gabarito) | Intervenção | Invalida o critério de ponta a ponta da rodada |
| Mudar arquivo congelado (5.12.2), inclusive para corrigir um defeito do código | Intervenção | Invalida. Corrige-se, faz-se um ensaio novo e abre-se uma rodada nova |
| Forçar uma peça a mudar de etapa, pular uma etapa, reenviar um pedido à mão, escolher quais peças entram ou descartar peça fora das regras | Intervenção | Invalida |

Uma rodada invalidada para o critério de ponta a ponta continua tendo os outros números registrados, mas o relatório diz que vieram de uma rodada com intervenção, e a decisão de escalar usa uma rodada válida. O gasto de todas as rodadas entra no gasto total do MVP.

#### 5.12.4 Modelo local indisponível: a válvula de escape

`modelo_local.py` informa o resultado do `porteiro` (seção 7); `estado.py` decide o destino da peça, numa regra só:

| Classe | O que acontece quando o modelo local está indisponível |
|---|---|
| Baixo | Segue com a conferência do Haiku, com a ausência registrada na peça |
| Médio | Espera a próxima janela da conferência local. Se esperar mais de 72 horas, o Opus responde os itens do conferente local no lugar dele, o custo entra no controle de gasto e a substituição fica registrada na peça |
| Alto | Espera a próxima janela, porque o Opus já confere todos os itens dessas peças e o plano quer a conferência de uma família diferente. Se esperar mais de 7 dias, a rodada fica em pausa registrada, que não invalida, até o modelo voltar |

**Pedido que não cabe no contexto.** Esperar não resolve, e por isso a peça não espera a janela: no risco baixo, segue com o Haiku; no médio, o Opus responde na hora os itens do conferente local; no alto, vale a resposta do Opus nesses itens, sem a do modelo local. A ocorrência é registrada na peça e no relatório. **No ensaio**, um único caso assim reprova o ensaio, e também o reprova um pedido que passe de 75% do `num_ctx` pela estimativa pessimista. Nos dois casos, o `num_ctx` sobe para 32.768 no `config.toml` e faz-se um ensaio novo. Não há terceiro valor: se, com 32.768, um pedido ainda passar de 75%, o ensaio passa nesse ponto, a rodada segue com 32.768, e o pedido que não couber cai na regra acima. **Na rodada**, só o pedido que não cabe é bloqueado; um pedido entre 75% e 100% é conferido normalmente. Se o modelo não couber na máquina com esse contexto, o `porteiro` responde indisponível e vale a regra desta seção.

A janela da conferência local é a que o responsável definir no `config.toml`, de 24 horas ou menos. Nada se supõe sobre quantas horas o computador fica ligado, nem sobre o computador: as horas fora da janela, ou com o computador desligado, ocupado, sem o Ollama ou sem o `porteiro`, caem nesta regra. Se mais de 20% das peças de risco médio e alto ficarem sem a resposta do modelo local, por qualquer motivo, o relatório marca o resultado como **sem conferente local estável**: os critérios continuam decidindo, mas a decisão de escalar registra a ressalva. Os 20%, os 75% e os 7 dias são escolhas declaradas antes de rodar.

#### 5.12.5 Corte de gasto

- **Alerta em US$ 30:** só avisa. A rodada continua.
- **Corte em US$ 100, o orçamento do mês:** `gasto.py` não envia nenhum pedido que faça o total passar do corte. As peças no meio do caminho ficam paradas no passo em que estão, com tudo gravado; nada se perde. A rodada para, com a parada registrada.
- **Efeito nos critérios:** o corte não é intervenção e não invalida o critério de ponta a ponta das peças que chegaram ao fim. Os critérios que dependem do que ficou por fazer são registrados como inconclusivos, e o relatório mostra em que passo cada peça parou e o que consumiu o gasto.
- **Sem retomada acima do limite:** o corte não sobe. Chegar a ele indica defeito, e não volume: corrige-se a causa, faz-se um ensaio novo e, se ainda houver saldo dentro do limite, abre-se uma rodada nova com um corte menor, igual ao saldo.

#### 5.12.6 Plano B: se o responsável aprovar bem menos de 25 peças boas

Com a taxa observada exatamente em 80%, o limite inferior de Wilson só chega a 65% a partir de 40 cópias (32 de 40 dá 65,2%; 28 de 35 dá 64,1%).

| Peças boas | O que se faz |
|---|---|
| 20 ou mais | Segue normal: 4 cópias do Opus por peça boa (80 ou mais) |
| De 14 a 19 | Sobe para 6 cópias do Opus por peça boa (84 a 114), sem gerar peças novas. A cópia feita por programa continua uma só. O relatório registra que cópias da mesma original não são independentes entre si |
| Menos de 14 | O critério central é registrado como **inconclusivo**, e não se escala. O relatório mostra as causas das reprovações, e a correção vai para o módulo responsável antes de uma nova rodada |

Não há reposição com peças novas. O critério de peças boas reprovadas, escrito em proporção (no máximo 10%, arredondado para baixo), se ajusta sozinho: 2 com 20 a 29 peças boas, 1 com 14 a 19.

#### 5.12.7 Destino da peça conforme os dois vereditos do responsável

| Ficha | Peça | Destino | Entra em |
|---|---|---|---|
| Aprovada | Aprovada | **Peça boa** | Denominador de peças boas reprovadas; base dos erros plantados; teste dos conferentes; concordância; pode ser publicada |
| Aprovada | Reprovada | Peça ruim | Concordância (a fábrica deveria tê-la reprovado); não é publicada |
| Reprovada | Aprovada | **Fora das medidas de conferência** | Só na linha "fichas reprovadas" do relatório. Não recebe cópias com erro e não é publicada |
| Reprovada | Reprovada | Fora das medidas de conferência | Só na linha "fichas reprovadas" do relatório, com a causa |

Se a taxa de fichas reprovadas passar de 20% num tipo, o relatório aponta `ficha.md` e `fichas.py` daquele tipo como o módulo a corrigir.

#### 5.12.8 Resposta fora do formato: o destino de cada coisa

Vale quando a segunda resposta de um pedido também sai fora do formato, é recusada ou é cortada (seção 7).

| Pedido que falhou | Destino |
|---|---|
| Ficha | A regra de ficha que falha (5.4) |
| Redação da primeira versão | A casa da matriz recebe uma ficha nova, pela mesma regra; a peça não chega a existir e não entra na leitura |
| Redação de uma refação | Conta como uma das três versões; a peça segue para a refação seguinte ou para o descarte |
| Extração, checklist ou desempate de uma peça | A peça é reprovada na categoria **formato**, sem refação. Se for a primeira versão de uma peça boa, conta como peça boa reprovada, e aparece numa linha própria do relatório |
| Conferente local | Não é formato: é modelo local indisponível, com a regra de 5.12.4 |
| Cópia com erro ou verificação, na criação do banco | A regra de descarte e refação de 5.7 |
| Extração, checklist ou desempate de uma cópia, no teste | A cópia conta como não pega e é listada |

---

## 6. Regras de decisão: critérios para escalar

| Critério | Exigência no MVP | Papel |
|---|---|---|
| **Erros plantados pegos (critério central)** | Só as cópias feitas por IA (cerca de 100): taxa observada de pelo menos 80%, com o limite inferior do intervalo de 95% (Wilson) em pelo menos 65%. Ao lado, a taxa sem o Opus, a taxa nos erros de julgamento feitos por programa e o resultado da amostra das descartadas. As cópias com erro de regra feitas por programa precisam ser 100% pegas; abaixo de 100%, o critério central é calculado e registrado, mas não decide, e a falha vai para o programa de regra responsável | Decide |
| Ponta a ponta | As peças da rodada (30, menos as casas vazias pela regra de `fichas.py`) sem intervenção manual (5.12.3), e cada tipo fechando pelo menos 8 das 10 peças. Abaixo do piso, a falha vai para `ficha.md` e `fichas.py` daquele tipo | Decide |
| Peças boas reprovadas por engano na primeira versão | Entre as peças boas, as que a fábrica reprovou **por conteúdo** na primeira versão (inclusive as das categorias "ambos" e "formato"): no máximo 10% delas, arredondado para baixo. Reprovações só por semelhança ficam fora desta conta | Decide; margem de Wilson registrada (com 2 em 25, de 2% a 25%) |
| Reprovação só por semelhança | Peças boas reprovadas na primeira versão apenas pela semelhança, listadas. Se houver alguma, o limite é revisto antes do piloto | Indicador |
| Dado real proibido | Zero, apurado como em 5.2 | Decide |
| Custo marginal por peça aprovada | Custo de ficha, redação, refações e conferência de todas as peças da rodada válida, inclusive descartadas e fichas substituídas, dividido pelo número de peças aprovadas pela fábrica, em qualquer versão. Fora ficam ensaio, cópias com erro e teste. Acima de US$ 0,15, rever antes de escalar | Decide |
| Gasto total do MVP | Somando todas as rodadas, inclusive ensaios, comparado com a estimativa (US$ 19 a 25) | Indicador |
| Concordância entre a fábrica e o responsável | Sobre a mesma primeira versão, só nas peças cuja ficha foi aprovada. Números brutos e cada peça em disputa, com a causa | Indicador |
| Notas de estilo | Quantas peças a regra do plano (média abaixo de 3) teria reprovado, e quantas delas o responsável aprovou | Indicador |

**Ressalvas que o relatório pode marcar** (os critérios continuam decidindo, e a decisão de escalar registra a ressalva): **dependente do Opus** (5.1); **filtrado pelo verificador** (5.7); **sem conferente local estável** (5.12.4). **Banco não confiável** (5.7) é diferente: com ele, o critério central não decide.

**Por que US$ 0,15 aqui e US$ 0,08 no plano não se contradizem:** os US$ 0,08 do plano são o gatilho semanal da produção, que usa processamento em lote, a metade do preço. Sem lote, o mesmo limite é 0,08 × 2 = 0,16, arredondado para baixo para errar do lado mais rígido.

---

## 7. Camada de integração externa

Três clientes, montados em `fabrica/__main__.py` e entregues aos módulos por parâmetro; nenhum outro módulo fala com o mundo de fora. Nos testes, os três são trocados por falsos.

### 7.1 API da Claude (`api_claude.py`)

**Dois passos em toda chamada:** gravar o pedido em `saida/pedidos/` e, quando chamado para coletar, gravar a resposta em `saida/respostas/` e passar o custo ao registro. No MVP, a coleta acontece logo depois do envio; no modo lote da escala, horas depois. As etapas não percebem a diferença.

**Modelos e preços** (no `config.toml`, com a data da conferência; tabela oficial de modelos consultada em 21/11/2026):

| Modelo | Identificador | Entrada, por milhão de tokens | Saída, por milhão de tokens |
|---|---|---|---|
| Opus 5.5 | `claude-opus-5-5` | US$ 4 | US$ 20 |
| Sonnet 5.5 | `claude-sonnet-5-5` | US$ 2 | US$ 10 |
| Haiku 5.5 | `claude-haiku-5-5` | US$ 0,10 (até 100 mil tokens de entrada) | US$ 0,50 |

**Em toda chamada, obrigatoriamente:**
- **saída estruturada** nas respostas que precisam ser JSON (ficha, extração, checklist, desempate, cópia com erro, verificação): o parâmetro de formato da resposta, `output_config.format`, com o esquema gerado por `formatos.py`. Nunca o uso forçado de ferramenta: o Opus 5.5 e o Sonnet 5.5 recusam esse pedido com erro;
- **nível de esforço explícito** (`output_config.effort`) e **teto de saída** (`max_tokens`), que limita raciocínio e texto juntos. Nunca teto de tokens de raciocínio: nos modelos 5.5 o pedido que o traz volta com erro, e no Opus 5.5 e no Sonnet 5.5 o raciocínio não pode ser desligado;
- nenhum parâmetro de amostragem (temperatura e semelhantes) e nenhuma resposta pré-escrita do assistente, que os modelos 5.5 recusam;
- nenhuma troca automática de modelo em caso de recusa, embora a API a ofereça: cada medida depende de saber qual modelo respondeu.

| Tarefa | Modelo | Esforço | Teto de saída |
|---|---|---|---|
| Ficha | Haiku | Baixo | 8 mil tokens |
| Redação de risco baixo | Haiku | Baixo | 8 mil tokens |
| Extração e checklist | Haiku | Baixo | 8 mil tokens |
| Redação de risco médio | Sonnet | Baixo | 16 mil tokens |
| Redação de risco alto | Sonnet | Médio | 16 mil tokens |
| Conferência do risco alto e desempate | Opus | Baixo | 8 mil tokens |
| Cópia com erro | Opus | Médio | 8 mil tokens |
| Verificação da cópia | Sonnet | Médio | 8 mil tokens |

O ensaio mede os tokens reais de cada tarefa e os grava no relatório.

**Ordem fixa de montagem do pedido**, para que o cache funcione na escala sem mudar as etapas: 1. instruções gerais; 2. estrutura; 3. trecho da tabela de normas; 4. ficha.

**Falhas:**
- erro de rede, limite de uso ou serviço sobrecarregado: nova tentativa automática até 3 vezes, com espera crescente (30 segundos, 2 minutos, 8 minutos). Depois disso, a peça fica parada naquele passo, a pausa é registrada, e o próximo `avancar` tenta de novo;
- resposta fora do formato: um novo pedido igual. Se a segunda também vier fora do formato, o destino segue 5.12.8, com a causa "formato" registrada;
- resposta recusada pelo modelo (motivo de parada "recusa") ou cortada pelo teto de saída: tratada como resposta fora do formato.

Nunca se conserta saída malformada com expressão regular.

A chave da API vem de variável de ambiente da máquina que roda a fábrica; nunca fica no repositório.

### 7.2 Modelo local (`modelo_local.py`)

O único arquivo que fala com o Ollama, na porta 11434 da própria máquina. **Modelo do MVP: `gemma3:27b`**, com a etiqueta completa e o digest no `config.toml` e sempre com o `num_ctx` explícito. Escolhido por ser bom em português, ser de outra família que não a do Claude e ser o modelo com que o plano estimou os tempos.

Antes de cada uso, consulta o `porteiro` com `porteiro cabe <modelo> --porta 11434 --json` e traduz a resposta em três resultados: **rodou** (resposta 0); **esperou e rodou** ou **indisponível** (resposta 1: tenta de novo a cada minuto por até 15 minutos; se não couber, indisponível); **indisponível** (resposta 2 ou 3, falha do modelo, ou o comando `porteiro` ausente ou com erro). Não decide o que acontece com a peça: só informa o resultado. Nunca inicia, para ou descarrega o Ollama.

**Contexto:** antes de enviar, estima o tamanho do pedido de forma pessimista (o número de caracteres dividido por 3) e soma o teto de saída. Se passar do `num_ctx`, não envia, e o resultado é **indisponível, por contexto** (5.12.4). Resposta que o Ollama encerra por tamanho é tratada como resposta fora do formato. Nenhuma peça é conferida pela metade sem aviso. O esquema JSON vai no parâmetro de formato do Ollama.

### 7.3 Disco (`arquivos.py`)

Lê e grava os arquivos de `saida/`, com os nomes padronizados e a gravação atômica da seção 4. Nunca sobrescreve.

### 7.4 Controle de gasto e registro

**`gasto.py`** — Antes de cada pedido, soma o gasto já registrado com o custo previsto dos pedidos enviados e ainda não coletados, mais o do pedido novo. O custo previsto é pessimista: os tokens de entrada contados mais o teto de saída da tarefa, ao preço do modelo. Se passar do corte, não envia (5.12.5). Calcula também o custo marginal por peça aprovada, sem os custos únicos do MVP, e alerta no gatilho.

**`registro.py`** — Anota cada chamada em `saida/registro/chamadas.jsonl` (modelo; tokens de entrada, de cache, de raciocínio e de saída; custo e duração; peça) e cada pausa, parada e intervenção em `saida/registro/ocorrencias.jsonl`, com causa, início e fim.

**`config.py`** — Lê o `config.toml` e o `gasto.toml` uma vez e entrega os valores aos demais módulos. Se faltar um valor obrigatório, para antes de gastar qualquer chamada.

---

## 8. Interface: comandos

Um só ponto de entrada: `python -m fabrica <comando>`. `fabrica/__main__.py` não tem lógica de etapa: lê o comando, monta os três clientes da seção 7 e chama o módulo.

| Comando | Função |
|---|---|
| `python -m fabrica fichas --tipo <tipo>` | Sorteia as combinações e grava os pedidos de ficha do tipo. Na rodada do MVP, recusa começar sem ensaio aprovado em `saida/rodadas.json` |
| `python -m fabrica avancar` | Pede a `estado.py` que leve cada peça à próxima etapa possível, coletando as respostas prontas. Pode ser repetido a qualquer momento; retoma de onde parou. Construído no brief 008 |
| `python -m fabrica preparar` | Preparação, sem gastar API: valida todos os arquivos de `dados/` pelos modelos de `formatos.py`, monta e grava a estrutura de cada tipo (`saida/preparacao/<tipo>_estrutura.json` e `.md`), sorteia para conferir as combinações de cada tipo com uma semente de prova (`--semente N` troca a semente), mede o trecho da tabela e conta os pares de cada tipo, confere os dispositivos das travas e os nomes reservados (só a contagem), grava `saida/preparacao/resumo.md` e sai com erro se alguma conferência falhar. Construído no brief 011 |
| `python -m fabrica revisar` | Única entrada das respostas do responsável. Mostra o próximo cartão pendente (da revisão, do ensaio, da amostra de 10 cópias, da amostra das descartadas ou da leitura de publicação), faz as perguntas, mostra as respostas juntas e pede confirmação; só depois grava `saida/cartoes/<id>_respostas.json`. Antes de confirmar, qualquer resposta pode ser corrigida; depois, não muda |
| `python -m fabrica revisar --resumo` | Só lista os cartões já respondidos, com as respostas e a data, sem mudar nada |
| Um comando para cada um dos demais fluxos de 1.4 | Preparação, ensaio, erros plantados, teste dos conferentes, publicação e relatório. O nome de cada um é fixado no brief da fase que constrói o módulo e registrado aqui no mesmo brief |

**Rede:** a fábrica não escuta em nenhuma porta. Só faz conexões de saída para a API da Claude e para o Ollama em `127.0.0.1:11434`.

---

## 9. Agendamento

Não existe agendamento. Toda execução é disparada pelo responsável, por um comando. A janela da conferência local não é agendamento: é um horário que `estado.py` consulta quando roda, e fora dele a peça segue a regra de 5.12.4. Os prazos de 72 horas e de 7 dias são contados a partir dos horários gravados, a cada `avancar`. O progresso é retomável porque está todo nos arquivos; interromper um comando é seguro e não é intervenção. Não há arquivo sentinela de parada: parar é interromper o comando.

---

## 10. Lacunas conhecidas

Nenhuma.

---
## Anexo A — Campos da ficha dos 3 tipos

Adotados da seção 4.3 do plano. O plano lista campos próprios só para previdenciário, família, trabalho e penal; os 3 tipos do MVP são cíveis e usam os campos comuns do plano mais os do tipo. A última coluna diz para que serve cada campo: **trava**, **comparação** (extração contra ficha), **alçada**, **prazo**, **âncora** ou **cartão** (só para o responsável ler).

Os valores em dinheiro ficam sempre em centavos, como número inteiro, para não haver erro de arredondamento. As datas ficam no formato ano-mês-dia.

### A.1 Campos comuns a todos os tipos

| Campo | O que é | Regra | Serve para |
|---|---|---|---|
| `id` | Identificador da ficha | `<rodada>_<tipo>_<n>` | Todos os arquivos |
| `tipo` | Rótulo exato da lista consolidada | Um dos 3 rótulos | Trava |
| `classe_risco` | Baixo, médio ou alto | Do catálogo | Conferência |
| `casa_matriz` | Matéria, tese principal, polo de quem peticiona, complexidade, momento e estilo sorteados | Valores da matriz aprovada | Trava, relatório |
| `semente` | Semente da rodada | Gravada | Refazer o sorteio |
| `processo.identificador_ficticio` | Identificador interno do processo fictício | Único | Futuro processo completo |
| `processo.numero_cnj` | Número do processo | Regra de 5.2; vazio na petição inicial, que ainda não tem número | Comparação, dado real |
| `processo.rito` | `juizado_especial_civel` ou `procedimento_comum` | Lista fechada | Trava, alçada |
| `processo.comarca`, `processo.uf` | Comarca real e estado | Da lista de comarcas | Comparação |
| `processo.juizo` | Juízo a que a peça se dirige (por exemplo, "Juizado Especial Cível da Comarca de X" ou "2ª Vara Cível da Comarca de X") | Coerente com o rito | Comparação, competência |
| `processo.data_ajuizamento` | Data em que a ação foi ou será proposta | Em 2026, como todas as datas posteriores aos fatos (5.4) | Alçada |
| `partes[]` | No MVP, exatamente uma parte autora e uma ré. Lista das partes: `id`, `papel` (autor ou réu), `categoria`, `nome` (o marcador do papel e da categoria, 5.2), `documento`, `estado_civil` e `profissao` (pessoa física), `endereco` (rua, número, complemento, bairro, cidade, estado, CEP), `email`, `telefone`, `capaz` e `preso` (pessoa física) | Dados de 5.2. `categoria` é uma de: `pessoa_fisica`, `mei`, `microempresa`, `empresa_pequeno_porte`, `pessoa_juridica_privada`, `pessoa_juridica_direito_publico`, `empresa_publica_uniao`, `massa_falida`. As categorias proibidas existem na lista para que as travas possam ser testadas, mas a matriz nunca as sorteia onde são proibidas | Trava, comparação, dado real |
| `advogado` | `nome` ("Nome e Sobrenome do Advogado"), `oab` ("OAB/UF nº 000.000"), `email`, `telefone`, `endereco_escritorio`, `representa` (id da parte) | Dados de 5.2 | Comparação, dado real |
| `fatos[]` | Lista em ordem: `data`, `descricao`, `valores` (ids de `valores[]`) | Datas em ordem; nenhuma mais de 2 anos antes do ajuizamento | Comparação |
| `valores[]` | Todo valor que a peça pode usar: `id`, `descricao`, `centavos`, `data_referencia`. Inclui somas, dobros e totais que a peça vá escrever | A peça não pode usar valor que não esteja aqui (Anexo D) | Comparação, alçada |
| `provas[]` | Documentos mencionados: `id`, `descricao`, `identificador` | Identificador com `SINT-` | Comparação, dado real |
| `pedidos[]` | `id`, `natureza`, `descricao`, `valor` (id de `valores[]`, ou vazio) | `natureza` de uma lista fechada por tipo (abaixo) | Comparação, pedidos |
| `valor_causa` | Id de `valores[]` | Soma dos valores dos pedidos (art. 292, VI, do CPC); no dano moral, o valor pretendido (art. 292, V). Não se aplica nos embargos nem na manifestação | Alçada, comparação |
| `fundamentos[]` | Ids de dispositivos da tabela de normas | Todos dentro do trecho do tipo (5.5) | Fundamento |
| `momento_processual` | `fase`, `ultima_decisao` (resumo) e `prazo` (`inicio`, `dias_uteis`, `termo_final`), quando houver | Termo final calculado pelo programa em dias úteis, sem o dia do início (art. 224 do CPC) | Prazo |
| `pecas_anteriores[]` | `tipo`, `data`, `resumo` e, quando a peça depende dela, o texto | — | Peças anteriores |
| `data_peca`, `local_peca` | Data e cidade da assinatura | Dentro do prazo, com um dia útil de folga | Prazo, comparação |

### A.2 Petição Inicial em Juizado Especial Cível

| Campo | O que é | Regra | Serve para |
|---|---|---|---|
| `processo.rito` | — | Sempre `juizado_especial_civel` | Trava |
| `materia` | Matéria do caso | Ponto de partida, a confirmar na matriz: negativação indevida, voo atrasado ou cancelado, vício de produto, cobrança indevida em serviço de telefonia ou internet, falha em serviço bancário. Nenhuma das matérias excluídas do juizado (art. 3º, § 2º, da Lei 9.099/1995). No máximo 2 peças por matéria | Trava, matriz |
| `relacao_consumo` | Se há relação de consumo | Sim ou não | Fundamento |
| `inversao_onus_pedida` | Se a peça pede inversão do ônus da prova (art. 6º, VIII, do CDC) | Só com relação de consumo | Pedidos |
| `tutela_urgencia` | `pedida` (sim ou não) e `fundamento` | Só na complexidade média | Pedidos |
| `tentativa_previa` | `data` e `protocolo`, se a parte tentou resolver antes | Protocolo com `SINT-` | Comparação |
| `salario_minimo_referencia` | Valor do salário mínimo de 2026 em centavos, copiado do `config.toml` | — | Alçada |
| Naturezas de pedido | `citacao_reu`, `inversao_onus`, `tutela_urgencia`, `danos_morais`, `danos_materiais`, `restituicao_simples`, `restituicao_em_dobro`, `obrigacao_fazer`, `declaracao_inexistencia_debito`, `exclusao_cadastro`, `producao_provas` | Lista fechada | Comparação, pedidos |

**Alçada:** o valor da causa não passa de 40 salários mínimos (art. 3º, I, da Lei 9.099/1995), isto é, R$ 64.840,00 com o salário mínimo de 2026. A matriz nunca gera valor acima disso, e por isso não há renúncia ao excedente (art. 3º, § 3º) no MVP. Nenhum valor da ficha é igual a R$ 1.621,00 ou a R$ 64.840,00, para que esses números, quando aparecem na peça, sejam sempre referência legal (Anexo D).

### A.3 Embargos de Declaração

| Campo | O que é | Regra | Serve para |
|---|---|---|---|
| `processo.rito` | — | Sempre `procedimento_comum`. Os embargos no juizado têm rótulo próprio na lista consolidada | Trava |
| `embargante` | Id da parte que embarga | Autor ou réu, metade de cada | Legitimidade |
| `decisao_embargada` | `tipo` (`sentenca` ou `decisao_interlocutoria`), `data`, `data_intimacao`, `juizo`, `relatorio` (só na sentença), `fundamentacao` e `dispositivo`, em texto fictício | Decisão de primeiro grau; 7 sentenças e 3 decisões interlocutórias | Peças anteriores, âncora |
| `argumentos_das_partes[]` | `id`, `parte`, `peca_de_origem` (inicial, contestação, réplica ou manifestação) e `texto` de cada argumento apresentado antes da decisão | Pelo menos 3 argumentos | Âncora da omissão |
| `defeito.tipo` | `omissao_total`, `omissao_parcial`, `contradicao`, `obscuridade` ou `erro_material` (art. 1.022 do CPC; a omissão parcial é a do art. 1.022, parágrafo único, II, combinado com o art. 489, § 1º, IV) | Distribuição da matriz (2.2) | Âncora |
| `defeito.ancora` | `origem` (`decisao` ou `argumento`), `argumento_id` (na omissão) e `trecho_literal` | Regras do Anexo E | Âncora |
| `defeito.trecho_mencao` | Na omissão parcial, o trecho literal da decisão que menciona o argumento sem enfrentá-lo | Regras do Anexo E | Âncora |
| `defeito.descricao` | O defeito em uma frase, para o cartão | — | Cartão |
| `defeito.efeito_modificativo` | Se a peça pede que a correção mude o resultado | Sim ou não | Pedidos |
| `momento_processual.prazo` | 5 dias úteis da intimação (art. 1.023 do CPC) | A matriz não sorteia partes com prazo em dobro (Fazenda, Ministério Público, Defensoria), e por isso o prazo é sempre de 5 dias úteis | Prazo |
| Naturezas de pedido | `acolhimento_embargos`, `suprir_omissao`, `eliminar_contradicao`, `esclarecer_obscuridade`, `corrigir_erro_material`, `efeito_modificativo`, `intimacao_parte_contraria` (art. 1.023, § 2º) | Lista fechada | Comparação, pedidos |

### A.4 Manifestação sobre Aviso de Recebimento Negativo

| Campo | O que é | Regra | Serve para |
|---|---|---|---|
| `processo.rito` | `juizado_especial_civel` ou `procedimento_comum` | Metade de cada | Trava |
| `peticionante` | Id da parte que se manifesta | Sempre o autor | Legitimidade |
| `citando` | Id do réu a citar | — | Coerência |
| `endereco_tentado` | Endereço onde a carta foi enviada | Dados de 5.2 | Comparação |
| `aviso_recebimento` | `data_juntada` e `motivo_devolucao`: `mudou_se`, `desconhecido`, `endereco_insuficiente`, `numero_inexistente`, `ausente` ou `nao_procurado` | Lista fechada. Recusa e falecimento ficam fora, porque pedem raciocínio de risco médio | Peças anteriores, trava |
| `determinacao_judicial` | `data_intimacao` e `prazo_dias_uteis` para a manifestação | Se o juiz não fixou prazo, 5 dias úteis (art. 218, § 3º, do CPC) | Prazo |
| `pedido_ar` | `informar_novo_endereco`, `renovar_mesmo_endereco` ou `ciencia_e_prazo` | Lista fechada; nunca citação por edital nem pesquisa de endereço em sistemas | Trava, pedidos |
| `novo_endereco` | Endereço novo, quando o pedido é informá-lo | Dados de 5.2 | Trava, comparação |
| `meio_nova_diligencia` | `correio` ou `oficial_de_justica` (art. 249 do CPC; no juizado, art. 18, III, da Lei 9.099/1995) | Só quando há nova diligência | Pedidos |
| `prazo_pedido_dias` | Prazo pedido, quando o pedido é ciência e prazo | De 10 a 30 dias | Comparação |
| Naturezas de pedido | `nova_citacao_novo_endereco`, `renovacao_mesmo_endereco`, `ciencia`, `concessao_prazo` | Lista fechada | Comparação, pedidos |

### A.5 Travas do MVP

**Visão das travas.** As travas não leem a ficha diretamente. `matriz.py`, na combinação sorteada, e `fichas.py`, na ficha pronta, montam uma visão plana com os campos abaixo, todos tirados da ficha; campo que não se aplica ao tipo fica vazio:
- `tipo`, `processo.rito`, `materia`;
- `autor.categoria`, `autor.capaz`, `autor.preso`, `reu.categoria`, `reu.capaz`, `reu.preso` (no MVP há exatamente um autor e um réu);
- `valor_causa_centavos` e `alcada_centavos` (40 vezes `salario_minimo_referencia`);
- `defeito.tipo`, `defeito.ancora.argumento_id`, `defeito.trecho_mencao`;
- `pedido_ar`, `aviso_recebimento.motivo_devolucao`, `novo_endereco`, `meio_nova_diligencia` e `nova_diligencia` (sim quando `pedido_ar` é `informar_novo_endereco` ou `renovar_mesmo_endereco`).

As travas abaixo que falam de "parte" viram uma trava para o autor e outra para o réu.

| Trava | Efeito | Base legal |
|---|---|---|
| Juizado especial cível com autor fora de pessoa física capaz, MEI, microempresa ou empresa de pequeno porte | Proíbe | Art. 8º, § 1º, da Lei 9.099/1995 (OSCIP e sociedade de crédito ao microempreendedor, também admitidas, ficam fora da matriz por simplicidade) |
| Juizado especial cível com pessoa jurídica de direito público, empresa pública da União, massa falida, incapaz ou preso como parte | Proíbe | Art. 8º, caput, da Lei 9.099/1995 |
| Juizado especial cível com matéria excluída | Proíbe | Art. 3º, § 2º, da Lei 9.099/1995 |
| Juizado especial cível com valor da causa acima de 40 salários mínimos | Proíbe | Art. 3º, I, da Lei 9.099/1995 |
| Embargos de Declaração com rito de juizado | Proíbe | Rótulo próprio na lista consolidada ("Embargos de Declaração em Juizado Especial") |
| Embargos com defeito de omissão (total ou parcial) | Exige `defeito.ancora.argumento_id` | Art. 1.022, II, e parágrafo único, do CPC |
| Embargos com omissão parcial | Exige `defeito.trecho_mencao` | Art. 489, § 1º, IV, do CPC |
| Manifestação com pedido de informar novo endereço | Exige `novo_endereco` | Art. 319, II, do CPC, quanto ao endereço do réu |
| Manifestação com motivo `mudou_se`, `desconhecido`, `numero_inexistente` ou `endereco_insuficiente` e pedido de renovar no mesmo endereço | Proíbe | Coerência: a carta não chegará ao mesmo endereço |
| Manifestação com nova diligência e sem `meio_nova_diligencia` | Exige `meio_nova_diligencia` | Art. 249 do CPC; art. 18 da Lei 9.099/1995 |

### A.6 Eixos da matriz

| Eixo | Valores | Distribuição em cada tipo de 10 peças |
|---|---|---|
| Matéria | As 5 matérias de A.2, nos 3 tipos. Nos embargos e na manifestação, é a matéria do processo de origem | No máximo 2 por matéria; na inicial, por isso, exatamente 2 de cada |
| Tese principal | Lista curta por matéria, proposta pela IA e aprovada pelo responsável na preparação | Sorteio uniforme |
| Polo de quem peticiona | Inicial e manifestação: autor. Embargos: autor ou réu | Embargos: 5 e 5 |
| Tipo de parte | As categorias de A.1 que as travas admitem para o rito | Sorteio uniforme |
| Complexidade | `simples` ou `media` | 5 e 5 |
| Momento processual | Fixo por tipo: inicial, antes da citação; embargos, depois da decisão embargada; manifestação, depois da juntada do aviso | — |
| Estilo | `conciso` ou `detalhado` | 5 e 5 |
| Campos próprios do tipo | Defeito e tipo da decisão nos embargos; rito, motivo da devolução e pedido na manifestação | Defeitos 2, 3, 2, 2 e 1 (2.2); 7 sentenças e 3 decisões interlocutórias; rito 5 e 5; motivo e pedido por sorteio uniforme entre os permitidos pelas travas |

Os eixos com número fixo são cruzados pelo sorteio, que usa a semente da rodada. Se o sorteio não achar combinação que respeite as travas e o teto por matéria em 1.000 tentativas, a matriz volta para a preparação.

---

## Anexo B — Lista de conferência

Adotada da seção 6.2 do plano para os itens do conferente, e da seção 6.1 para os itens de programa. Todos os itens, menos o estilo, são eliminatórios: um "não passa" reprova a peça.

### B.1 Itens de programa

| Item | Quem confere | Regra | Tipos |
|---|---|---|---|
| `estrutura` | `regras.py` | Blocos obrigatórios da família, do perfil e do tipo presentes e na ordem | Todos |
| `citacao_fora_da_tabela` | `citacoes.py` | Toda citação resolvida está na tabela. Citação não resolvida vira alerta e pergunta ao checklist, não reprova sozinha | Todos |
| `termos_inequivocos` | `regras.py` | Nenhum termo da lista de termos inequívocos | Todos |
| `coerencia_ficha` | `regras.py` | Extração igual à ficha, com as tolerâncias do Anexo D | Todos |
| `alcada` | `regras.py` | Valor da causa até 40 salários mínimos de 2026 | Inicial em Juizado Especial Cível |
| `prazo` | `regras.py` | Data da peça até o termo final do prazo da ficha, em dias úteis, sem sábados, domingos e feriados nacionais | Embargos; manifestação |
| `dado_real` | `dados_reais.py` | Detecção de 5.2 | Todos |
| `marca` | `regras.py` | "DOCUMENTO SINTÉTICO — FICTÍCIO" presente | Todos |
| `semelhanca` | `semelhanca.py` | Abaixo do limite registrado. Reprovação marcada na categoria "semelhança", em separado | Todos (desligado no teste) |

### B.2 Itens do conferente

| Item | Pergunta | Quem responde | Inicial JEC (médio) | Embargos (alto) | Manifestação AR (baixo) |
|---|---|---|---|---|---|
| `cabimento` | A peça é o instrumento certo para a situação da ficha? | Haiku | Sim | Sim | Sim |
| `competencia_enderecamento` | O juízo está certo, inclusive pela alçada? | Haiku | Sim | Sim | Sim |
| `prazo_e_momento` | A peça é compatível com a fase e o prazo da ficha? | Haiku | Sim | Sim | Sim |
| `legitimidade` | Quem pede pode pedir? | Haiku | Sim | Sim | Sim |
| `pedidos` | Os pedidos são compatíveis com o tipo, o rito e os fatos? | Haiku | Sim | Sim | Sim |
| `fundamento` | Cada dispositivo citado sustenta a afirmação feita, comparado com o texto da tabela? | Haiku | Sim | Sim | Sim |
| `coerencia` | Fatos, fundamentos e pedidos não se contradizem? | Haiku e modelo local | Sim | Sim | Sim |
| `pecas_anteriores` | A peça responde ao que a peça ou decisão anterior da ficha disse? | Haiku e modelo local | Não se aplica (não há peça anterior) | Sim | Sim |
| `argumentacao_suficiente` | Cada pedido tem fundamento de fato e de direito próprio, ligado aos fatos do caso? | Haiku | Sim | Sim | Não se aplica (só médio e alto) |
| `texto_generico` | A peça usa os fatos concretos da ficha, ou caberia em qualquer caso? | Haiku e modelo local | Sim | Sim | Não se aplica (só médio e alto) |
| Estilo (não eliminatório) | Notas de 1 a 5 para clareza, concisão e linguagem técnica | Haiku | Registrado | Registrado | Registrado |

"Não se aplica" é decidido pelo catálogo do tipo, e não pelo conferente: o item nem é perguntado. O Opus responde todos os itens nas peças de risco alto. Nas peças de risco baixo sem conferência local (8 das 10), os itens do modelo local ficam só com o Haiku.

### B.3 Como cada item chega à resposta final

- **Itens de programa:** a resposta do programa é a final.
- **Itens só do Haiku, no risco baixo e médio:** a resposta do Haiku é a final.
- **Itens do Haiku e do modelo local, no risco baixo e médio:** se os dois concordam, essa é a resposta; se discordam, o Opus decide.
- **Risco alto:** a resposta final de cada item é a do Opus, salvo quando o Haiku e o modelo local concordam em "não passa", caso em que o item reprova mesmo que o Opus diga "passa". Motivo: no risco alto o Opus soma uma barreira; ele não pode desfazer sozinho uma reprovação em que os outros dois conferentes concordam.
- **Risco médio sem conferente local por mais de 72 horas:** o Opus responde os itens do conferente local, e a resposta dele é a final nesses itens.

---

## Anexo C — Catálogo de erros plantados e gabarito

Cada tipo de erro tem um **item principal** (o que deveria reprovar) e **itens aceitos** (qualquer um deles reprovado conta como erro pego). Os itens aceitos existem porque um erro real costuma ferir mais de um item: um valor acima da alçada também diverge da ficha.

Nos erros por programa, o programa acha o trecho a trocar pelo texto que a extração da original devolveu ("o texto como aparece na peça", 2.3).

### C.1 Erros por programa — de regra (conferência de sanidade; precisam ser 100% pegos pelos programas)

| Erro | O que o programa muda | Tipos | Item principal | Itens aceitos |
|---|---|---|---|---|
| `valor_trocado` | Um valor de pedido ou o valor da causa, em algarismos e, se houver, por extenso, para um valor que não está em `valores[]`, não é soma de valores da ficha, não é valor de referência legal (Anexo D) e difere de cada um deles em mais de 1% | Inicial JEC; embargos com valor na decisão | `coerencia_ficha` | `coerencia_ficha` |
| `data_trocada` | A data de um fato, para uma data de outro mês que não está na ficha | Todos | `coerencia_ficha` | `coerencia_ficha` |
| `fora_do_prazo` | A data da peça, para depois do termo final do prazo | Embargos; manifestação | `prazo` | `prazo`, `coerencia_ficha` |
| `acima_da_alcada` | O valor da causa, para acima de 40 salários mínimos | Inicial JEC | `alcada` | `alcada`, `coerencia_ficha` |
| `citacao_fora_da_tabela` | O número de um artigo citado, para um que não está na tabela | Todos | `citacao_fora_da_tabela` | `citacao_fora_da_tabela` |
| `juizo_trocado` | O endereçamento, para um juízo incompetente (por exemplo, vara da Fazenda Pública na inicial do juizado; tribunal nos embargos de primeiro grau; outro juizado na manifestação) | Todos | `coerencia_ficha` | `coerencia_ficha`, `competencia_enderecamento` |
| `termo_inequivoco` | Insere uma frase pronta com um termo da lista de termos inequívocos | Todos | `termos_inequivocos` | `termos_inequivocos` |
| `pedido_incompativel_com_rito` | Insere um pedido pronto, de uma lista aprovada por tipo, incompatível com o rito: na inicial do juizado, citação por edital (art. 18, § 2º, da Lei 9.099/1995) ou condenação em honorários no primeiro grau (art. 55); nos embargos, reforma da decisão por simples discordância; na manifestação no juizado, citação por edital. A extração o classifica como `outro`, e a comparação com a ficha o reprova | Inicial JEC; embargos; manifestação no juizado | `coerencia_ficha` | `coerencia_ficha`, `pedidos`, `cabimento` |

### C.2 Erro por programa — de julgamento (diagnóstico e controle do viés do Opus; não entra no critério central)

| Erro | O que o programa muda | Tipos | Item principal | Itens aceitos |
|---|---|---|---|---|
| `funcao_trocada` | Um dispositivo citado, por outro do mesmo diploma e do mesmo assunto, com função diferente na tabela (por exemplo, um dispositivo de prazo citado como se fixasse competência). O dispositivo novo sai do trecho da tabela do tipo, e por isso `citacoes.py` não o reprova. As peças com algum dispositivo com par têm prioridade no sorteio; a peça sem par recebe um erro de regra (5.1) | Todos | `fundamento` | `fundamento` |

### C.3 Erros feitos pelo Opus (critério central)

| Erro | O que o Opus faz | Tipos | Item principal | Itens aceitos |
|---|---|---|---|---|
| `cabimento` | Torna a peça o instrumento errado para a situação (por exemplo, embargos que só rediscutem o mérito, sem defeito na decisão) | Todos | `cabimento` | `cabimento`, `pedidos` |
| `competencia` | Endereça a peça a juízo incompetente com justificativa plausível no texto | Todos | `competencia_enderecamento` | `competencia_enderecamento`, `coerencia_ficha` |
| `prazo_e_momento` | Torna a peça incompatível com a fase ou o prazo (por exemplo, afirma prazo errado ou pede algo já feito) | Todos | `prazo_e_momento` | `prazo_e_momento`, `prazo` |
| `legitimidade` | Faz a peça ser pedida por quem não pode pedir | Todos | `legitimidade` | `legitimidade` |
| `pedido_incompativel` | Troca ou acrescenta um pedido incompatível com o tipo, o rito ou os fatos | Todos | `pedidos` | `pedidos`, `cabimento`, `coerencia_ficha` (o pedido trocado ou acrescentado também diverge da ficha) |
| `fundamento_nao_sustenta` | Usa um dispositivo verdadeiro da tabela que não sustenta a afirmação feita | Todos | `fundamento` | `fundamento` |
| `fato_contraditorio` | Introduz um fato que contradiz outro fato, o fundamento ou o pedido | Todos | `coerencia` | `coerencia`, `coerencia_ficha` |
| `peca_anterior_distorcida` | Faz a peça atribuir à decisão ou ao aviso de recebimento algo que eles não dizem | Embargos; manifestação | `pecas_anteriores` | `pecas_anteriores`, `coerencia` |
| `argumentacao_generica` | Troca a fundamentação de um pedido por afirmação genérica, sem ligação com os fatos | Inicial JEC; embargos | `argumentacao_suficiente` | `argumentacao_suficiente`, `texto_generico` |
| `texto_generico` | Troca um trecho com fatos concretos por texto que caberia em qualquer caso | Inicial JEC; embargos | `texto_generico` | `texto_generico`, `argumentacao_suficiente` |

São 10 tipos de erro do Opus para cerca de 100 cópias: cerca de 10 por tipo, distribuídos pelo sorteio entre os que se aplicam a cada tipo de peça. Metade das cópias do Opus é pedida como sutil (o texto continua bem escrito e convincente), como no plano.

### C.4 Gabarito

Para cada cópia, `gabarito.json` guarda: `copia`, `original`, `origem` (`programa_regra`, `programa_julgamento` ou `opus`), `tipo_erro`, `sutil`, `item_principal`, `itens_aceitos`, `criador`, `verificador`, `item_apontado_pelo_verificador`, `amostra` (vazio, aceita ou rejeitada pelo responsável).

As cópias descartadas não entram no gabarito. Ficam em `saida/erros/descartadas.json`, com `copia`, `original`, `tipo_erro`, `sutil`, `criador`, `conferencia_que_falhou` (`programa` ou `verificador`), `item_apontado_pelo_verificador` (ou vazio, quando ele não viu erro), `outro_problema`, `motivo` (`outro_problema`, `outro_item` ou `nao_viu_erro`, vazio quando a falha foi na conferência de programa) e `amostra` (vazio, erro existe ou erro não existe, pelo responsável; só preenchido no motivo `nao_viu_erro`).

---

## Anexo D — Regras de tolerância na comparação entre extração e ficha

A comparação reprova `coerencia_ficha` só por **diferença de conteúdo**, nunca por diferença de forma. Cada regra abaixo tem exemplos que passam e que reprovam em `testes/dados/comparacao_exemplos.json`.

| O que se compara | Normalização | Passa | Reprova |
|---|---|---|---|
| **Valor em algarismos** | Para centavos, como número inteiro: "R$ 1.500,00", "R$ 1500", "1.500 reais" viram 150000 | Igual a um valor de `valores[]` | Qualquer diferença, mesmo de 1 centavo, nos pedidos e no valor da causa |
| **Valor por extenso** | O Haiku devolve o texto e o valor em centavos; o programa confere os dois quando a peça traz algarismos e extenso juntos, como em "R$ 1.500,00 (mil e quinhentos reais)" | Algarismos e extenso iguais entre si e iguais à ficha | Algarismos e extenso diferentes entre si: é erro da peça, mesmo que um deles bata com a ficha |
| **Valor de referência legal** | Como o valor em algarismos | O salário mínimo de 2026 e a alçada do juizado (R$ 1.621,00 e R$ 64.840,00, tirados de `salario_minimo_referencia`), quando o lugar do valor na extração (2.3) é `fatos` ou `outro`. É regra de programa: não há juízo sobre o papel do número no texto | Os mesmos valores no lugar `pedido` ou `valor_causa` seguem as outras linhas e reprovam se não estiverem na ficha |
| **Soma** | — | Valor que não está na ficha só passa se for igual à soma de alguns valores dos pedidos ou ao valor da causa. Dobros e outros cálculos precisam estar em `valores[]` (`ficha.md` manda registrá-los) | Qualquer outro valor novo |
| **Arredondamento** | — | Só no lugar `fatos`, com marca de aproximação ("cerca de", "aproximadamente", "mais de") e diferença de até 1% para o valor da ficha | Arredondamento sem marca, ou em pedido e valor da causa |
| **Data por extenso** | Para ano-mês-dia: "15 de março de 2026", "15/03/2026", "15.3.2026" viram 2026-03-15. Dia da semana é ignorado | Igual a uma data da ficha. Data parcial ("março de 2026") passa se o mês e o ano baterem com uma data da ficha | Data diferente. Datas relativas ("há três meses") não são comparadas |
| **CEP** | Só os 8 dígitos: "13010-111", "13.010-111", "13010111" | Iguais | Dígitos diferentes |
| **CPF, CNPJ, número do processo, protocolo** | Só os dígitos e letras, sem pontuação | Iguais | Diferentes |
| **Nome de parte e de advogado, e OAB** | Minúsculas, sem acento | O marcador do papel certo, como está na ficha, com tratamento antes ("Sr.", "Dr.") ou não | Marcador de outro papel ou categoria (por exemplo, o da parte ré onde a ficha põe a autora), ou qualquer outro nome |
| **Designação da parte** | — | "o autor", "a ré", "a requerida" e semelhantes não são nomes e não são comparados | — |
| **Comarca e juízo** | Minúsculas, sem acento, sem "da Comarca de" e sem artigos; "JEC" igual a "Juizado Especial Cível" | Mesma comarca e mesmo juízo | Comarca ou juízo diferente |
| **Pedidos** | Cada pedido extraído classificado na lista de naturezas do tipo (Anexo A), ou como `outro` | Todo pedido da ficha aparece; pedido a mais só passa se estiver entre os pedidos acessórios padrão do perfil, listados no perfil pelos nomes das naturezas (por exemplo, `citacao_reu` e `producao_provas`) | Pedido da ficha faltando, pedido a mais fora da lista padrão, ou qualquer pedido `outro` |

**Quando o problema é a extração, e não a peça:** se o Haiku extrair errado, a peça boa é reprovada por engano. Isso aparece na leitura do responsável (ele aprova a peça) e no relatório, que lista cada reprovação por `coerencia_ficha` com o valor extraído e o da ficha, para separar erro da peça de erro da extração.

---

## Anexo E — Âncora do defeito nos embargos e "termos principais"

### E.1 Regras por tipo de defeito

| Defeito | Âncora | O que o programa confere |
|---|---|---|
| Contradição, obscuridade ou erro material | Trecho literal da decisão fictícia | O trecho está, letra por letra depois da normalização de espaços, na fundamentação ou no dispositivo da decisão |
| Omissão total (a decisão ignora o argumento) | Trecho literal de um argumento de `argumentos_das_partes[]` | O trecho está no argumento indicado; a ficha tem pelo menos 3 termos principais desse trecho; e, na fundamentação e no dispositivo da decisão, aparecem no máximo 20% deles, arredondado para baixo (com 5 termos, no máximo 1) |
| Omissão parcial (a decisão menciona o argumento e não o enfrenta) | Trecho literal de um argumento e `trecho_mencao`, trecho literal da decisão | O trecho do argumento está no argumento indicado; o `trecho_mencao` está na decisão e tem no máximo 40 palavras; pelo menos metade dos termos principais, arredondada para cima, aparece no `trecho_mencao`; e, fora dele, na fundamentação e no dispositivo, aparecem no máximo 20% dos termos principais, arredondado para baixo |

A regra da omissão parcial confere só a forma: a decisão menciona o argumento num trecho curto e não volta a ele. Se essa menção equivale ou não a enfrentar o argumento é juízo jurídico, e fica com o responsável no cartão, onde o trecho da menção aparece destacado (limite declarado no PLANO, seção 2). Sem essa regra, a omissão parcial, que é o caso mais comum, seria descartada pela regra da omissão total, porque os termos do argumento aparecem na decisão.

### E.2 Como se tiram os termos principais

1. **Normalização:** tudo em minúsculas, sem acentos e sem pontuação. Números ficam como estão, sem pontos e vírgulas internos.
2. **Palavras ignoradas:** saem as palavras de `dados/conferencia/palavras_ignoradas.json`, em duas listas que o responsável aprova:
   - palavras comuns do português: artigos, preposições, conjunções, pronomes e as formas dos verbos ser, estar, ter e haver;
   - palavras jurídicas que aparecem em qualquer decisão: autor, autora, réu, ré, parte, partes, pedido, pedidos, processo, juízo, decisão, sentença, artigo, art, lei, código, alega, alegou, requer, requereu, nos termos, conforme, ainda, assim, e semelhantes.
3. **Tamanho mínimo:** saem as palavras com menos de 4 letras, exceto números.
4. **Radical:** cada palavra que sobra é cortada nas 6 primeiras letras (palavras menores ficam inteiras). Assim "prescrição", "prescrita" e "prescrever" contam como o mesmo termo. O corte simples erra nos dois sentidos:
   - às vezes junta palavras diferentes (como "contrato" e "contrário"). Isso faz o termo parecer presente na decisão, e o efeito é só descartar a ficha;
   - às vezes separa formas da mesma palavra que mudam antes da sexta letra (como "omissão" e "omitido", ou "nulidade" e "nulo"). Isso faz o termo parecer ausente, e pode deixar passar uma omissão que a decisão, na verdade, enfrentou com outra forma da palavra. O programa não pega esse caso: ele fica com a conferência da ficha pelo responsável, no cartão, onde a âncora aparece destacada. Uma ficha assim reprovada pelo responsável sai das medidas de conferência (5.12.7) e não contamina o critério central.

   Um radicalizador do português pronto (como o RSLP) não resolve o segundo caso, que é de derivação, e acrescentaria uma biblioteca. Por isso o MVP fica com o corte simples. `test_ancora.py` tem exemplos dos dois sentidos.
5. **Contexto comum:** saem os radicais que também aparecem nos fatos da ficha ou em qualquer outro argumento. Eles são o assunto do caso, não o argumento omitido, e apareceriam na decisão de qualquer jeito.
6. **O que sobra** são os termos principais, sem repetição. Se sobrarem menos de 3, a âncora é fraca demais, e a ficha volta para o Haiku.

Essas regras ficam em `normalizacao.py`, usadas por `fichas.py`, e são testadas em `test_ancora.py`.
