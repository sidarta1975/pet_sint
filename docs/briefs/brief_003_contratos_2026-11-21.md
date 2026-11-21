# Brief 003 — Contratos de dados

- Fase: 3 — Base (PLANO §4)
- Objetivo: escrever `fabrica/comum/formatos.py` com todos os contratos da ARQUITETURA §3 e os campos do Anexo A, o gerador do esquema JSON das respostas estruturadas e `testes/test_formatos.py`, e gravar o registro de decisão com as convenções da construção.
- Seções a ler: AGENTS §3 (contratos de dados) e §4; PLANO §3; ARQUITETURA §2 (árvore), §2.2, §2.3, §3, §4, §5.2, §5.6, §5.7, §5.9, Anexos A, B, C, D e E; armadilhas do PLAN: "extracao.md, regras.py", "fichas.py, regras.py".
- Arquivos que pode criar:
  - `fabrica/comum/__init__.py`;
  - `fabrica/comum/formatos.py`;
  - `testes/test_formatos.py`;
  - `docs/adr/adr_001_convencoes_da_construcao_2026-11-21.md` (conteúdo abaixo, literal);
  - `docs/briefs/brief_003_contratos_2026-11-21.md` (este brief);
  - `docs/docs/doc_003_contratos_2026-11-21.md` (o relatório).
- Arquivos que pode alterar: `docs/PLAN.md` (Resumo, Doing, Backlog e Done); `pyproject.toml`, só para acrescentar a seção `[tool.pytest.ini_options]` com `pythonpath = ["."]` e `testpaths = ["testes"]`.
- Arquivos que não pode tocar: `config/`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`, `fabrica/__main__.py`.
- Teste de aceite (escrito antes do código): `testes/test_formatos.py` — para cada contrato, um exemplo válido passa; o mesmo exemplo com um campo faltando, com um campo a mais e com um tipo errado (texto onde se espera inteiro, inteiro onde se espera texto, data fora do formato ano-mês-dia) é recusado. E ainda: valor em dinheiro com casas decimais é recusado; `categoria`, `natureza`, `lugar`, `origem`, `motivo` e os demais campos de lista fechada recusam valor fora da lista; a ficha da Petição Inicial em Juizado Especial Cível recusa `processo.rito` diferente de `juizado_especial_civel` e a dos embargos recusa `juizado_especial_civel`; o esquema JSON gerado para cada resposta estruturada proíbe campo a mais.
- Critério de conclusão: `test_formatos.py` passa no gate (parte do critério da Fase 3 no PLANO).
- Fora do escopo: o modelo da configuração (é do brief 004, que lê o `config.toml`); gravar e ler arquivos (brief 004); qualquer regra de negócio além da validação de formato e de lista fechada (as regras de coerência são de `fichas.py`, `regras.py` e `matriz.py`); `dados/` (nasce no 014); `instrucoes/`.
- Depende de: 001.

**Regras deste brief**

- **`pytest` e o pacote.** Este é o primeiro teste que importa `fabrica`. Sem `pythonpath = ["."]` no `pyproject.toml`, o comando `pytest testes` do gate não acha o pacote (conferido em 2026-11-21 com as versões fixadas, em Python 3.12). O 001, como está no repositório, não tem essa seção, porque foi escrito antes deste achado: este brief sempre a acrescenta, e o relatório registra que o `pyproject.toml` entregue pelo 001 estava incompleto nesse ponto. Nenhuma outra linha do `pyproject.toml` muda, e nenhuma versão.
- Todos os modelos herdam de uma base com `model_config = ConfigDict(extra="forbid", strict=True, frozen=True)`. Dinheiro é `int` em centavos; datas são `datetime.date` lidas do texto ano-mês-dia; horários são `datetime.datetime` com fuso.
- Lista fechada é `Literal[...]` com os valores exatos dos canônicos. Os valores das listas fechadas são estes, sem acréscimo:
  - tipos (rótulo exato): "Petição Inicial em Juizado Especial Cível", "Embargos de Declaração", "Manifestação sobre Aviso de Recebimento Negativo"; nomes curtos: `peticao_inicial_jec`, `embargos_declaracao`, `manifestacao_ar_negativo`;
  - classe de risco: `baixo`, `medio`, `alto`;
  - rito: `juizado_especial_civel`, `procedimento_comum`;
  - categoria da parte: as 8 do Anexo A.1;
  - papel: `autor`, `reu`;
  - complexidade: `simples`, `media`; estilo: `conciso`, `detalhado`;
  - naturezas de pedido: as listas fechadas de A.2, A.3 e A.4, cada uma presa ao seu tipo, mais `outro` só na extração;
  - defeito: `omissao_total`, `omissao_parcial`, `contradicao`, `obscuridade`, `erro_material`; origem da âncora: `decisao`, `argumento`; tipo de decisão: `sentenca`, `decisao_interlocutoria`; peça de origem do argumento: `inicial`, `contestacao`, `replica`, `manifestacao`;
  - motivo de devolução do aviso: os 6 de A.4; pedido da manifestação: `informar_novo_endereco`, `renovar_mesmo_endereco`, `ciencia_e_prazo`; meio da nova diligência: `correio`, `oficial_de_justica`;
  - lugar do valor: `fatos`, `pedido`, `valor_causa`, `outro`;
  - função do dispositivo: `requisito`, `prazo`, `competencia`, `excecao`, `consequencia`, `definicao`;
  - operação da trava: as 8 da ARQUITETURA §2.2; efeito: `proibe`, `exige`;
  - itens da lista de conferência: os 9 de B.1 e os 10 de B.2, mais `estilo`;
  - veredito: `aprovada`, `refazer`, `descartada`; categoria do motivo: `conteudo`, `semelhanca`, `ambos`, `formato`;
  - origem do erro: `programa_regra`, `programa_julgamento`, `opus`; tipos de erro: os 8 de C.1, o de C.2 e os 10 de C.3;
  - motivo do descarte: `outro_problema`, `outro_item`, `nao_viu_erro`; conferência que falhou: `programa`, `verificador`;
  - amostra do gabarito: vazio, `aceita`, `rejeitada`; amostra da descartada: vazio, `erro_existe`, `erro_nao_existe`;
  - tipo de cartão: `revisao`, `ensaio`, `amostra_copias`, `amostra_descartadas`, `leitura_publicacao`;
  - estado da rodada: `aberta`, `parada`, `encerrada`, `invalida`;
  - tipo de ocorrência: `pausa`, `parada`, `intervencao`, `contexto`;
  - resultado do modelo local: `rodou`, `esperou_e_rodou`, `indisponivel`; causa da indisponibilidade: `porteiro`, `contexto`, `janela`, `falha`.
- **Contratos que o brief cria** (um modelo por linha; os campos são os da ARQUITETURA §3 e dos anexos citados):
  - **Ficha**, com os campos comuns (A.1) e um bloco próprio por tipo (A.2, A.3 e A.4), escolhido pelo campo `tipo` (união discriminada). No MVP, `partes` tem exatamente um autor e um réu.
  - **RespostaFicha**: o que o Haiku devolve para a ficha, que é só a parte do caso que o programa não sorteia: `fatos[]`, `valores[]`, `provas[]`, `pedidos[]`, `valor_causa`, `fundamentos[]`, `momento_processual.ultima_decisao`, `pecas_anteriores[]` e, por tipo: na inicial, `relacao_consumo`, `inversao_onus_pedida`, `tutela_urgencia` e `tentativa_previa`; nos embargos, `decisao_embargada` (menos `data_intimacao`, que é sorteada), `argumentos_das_partes[]`, `defeito` (menos `tipo`, que vem da matriz) e `efeito_modificativo`; na manifestação, nenhum campo além dos comuns acima. Partes, advogado, processo, números, endereços, datas sorteadas pela matriz e identificadores `SINT-` são do programa (brief 015).
  - **VisaoTravas**, **Trava** e **Condicao**, como na ARQUITETURA §3 e no Anexo A.5.
  - **Dispositivo** e **TabelaNormas** (`versao`, `diplomas[]` com `id`, `nome` e `formas[]`, e `dispositivos[]`). `paragrafo` é `caput`, `unico` ou o número do parágrafo em texto (`"1"`, `"2"`).
  - **Formatos de `dados/`**: `CatalogoTipos` (cada tipo com rótulo exato, nome curto, família, perfil, classe de risco, tarefa de redação do `config.toml`, quantidade, se depende de peça anterior e os itens de conferência que se aplicam); `Familia`, `Perfil` (com `pedidos_acessorios_padrao[]`) e `Acrescimo` (blocos com nome, ordem, obrigatório e descrição; perfil e acréscimo também com blocos a retirar ou ajustar); `Matriz` (eixos e distribuição do Anexo A.6, teses por matéria, teto por matéria e distribuição dos defeitos); `ListaConferencia` (item, pergunta, quem confere, eliminatório, tipos); `TermosInequivocos` (termo, motivo, norma de hoje); `PalavrasIgnoradas` (as duas listas do Anexo E.2); `FeriadosNacionais` (data e nome); `CatalogoErros` (tipo de erro, origem, tipos de peça, item principal, itens aceitos); `ListasFicticias` (ruas, bairros, cidades com estado e faixa de CEP, profissões, e as listas prontas de pedidos incompatíveis com o rito por tipo, Anexo C.1); `ReaisPermitidos` e `ReaisProibidos` (nome e categoria); `ReaisReservados` (nome e forma como aparece numa peça).
  - **Pedido** e **Resposta** (ARQUITETURA §3 e §7.1; a resposta com `situacao`: `ok`, `fora_do_formato`, `recusa`, `cortada`).
  - **Rascunho** (metadados de origem; o texto fica no `.md`), **Extracao** (campos exigidos abaixo), **ResultadoItem** (resposta `passa` ou `nao_passa`, quem respondeu, trecho), **Conferencia** (ARQUITETURA §3, com o caminho de cada item do Anexo B.3).
  - **Respostas dos conferentes**: `RespostaChecklist` (item, resposta, trecho, mais as três notas de estilo de 1 a 5), `RespostaLocal` (item, resposta, trecho), `RespostaDesempate` (item, resposta, justificativa).
  - **CopiaComErro**, **Gabarito**, **Descartada**, `RespostaCopiaOpus` (trecho original e trecho novo) e `RespostaVerificacao` (item apontado ou vazio, descrição do erro, outro problema sim ou não, com a descrição).
  - **Cartao**, **RespostasCartao**, **Rodada** (com o `ensaio_aprovado` de origem e as impressões digitais por arquivo), **Chamada**, **Ocorrencia** e **Metadados** do pacote.
- **Campos exigidos em `Extracao`**, porque os briefs 012 e 017 dependem deles: `nomes[]` com `texto` e `papel` (`autor`, `reu`, `advogado`, `outro`); `documentos[]` com `tipo` (`cpf`, `cnpj`, `oab`, `numero_processo`, `protocolo`, `contrato`, `cep`) e `texto`, porque o Anexo D compara o CEP e a ARQUITETURA §2.3 fala em "documentos e números"; `valores[]` com `texto`, `centavos`, `lugar` e `pedido` (id do pedido da ficha ou vazio); `datas[]` com `texto` e `data` (completa, só ano e mês, ou vazia nas datas relativas); `comarca` e `juizo`, com o texto; `pedidos[]` com `natureza` (da lista do tipo ou `outro`) e `texto`; `pecas_anteriores[]`; `data_peca`. Se algum desses não couber no que a ARQUITETURA §3 diz, o executor para e registra; não o retira.
- O esquema JSON enviado como formato de resposta sai de uma função única, `esquema_resposta(modelo)`, que devolve o esquema do Pydantic com campo a mais proibido em todos os níveis.
- Campo que o executor não encontrar descrito nos canônicos não é inventado: vai para as pendências do relatório, com a seção onde faltou.
- O executor lê a ARQUITETURA, Anexo A, ao pé da letra: os nomes dos campos são os de lá.

**Conteúdo literal de `docs/adr/adr_001_convencoes_da_construcao_2026-11-21.md`:**

```
# Registro de decisão 001 — Convenções da construção

- Data: 2026-11-21
- Situação: aceita
- Contexto: os canônicos deixam para os briefs alguns detalhes que o executor precisa para não inventar. Este registro junta as decisões, para que todos os briefs usem as mesmas.

## Decisões

1. Nomes curtos dos tipos: `peticao_inicial_jec`, `embargos_declaracao`, `manifestacao_ar_negativo`. O rótulo exato da lista consolidada fica no catálogo e nos metadados.
2. Identificadores: rodada `e01`, `e02`... no ensaio e `r01`, `r02`... na rodada; peça `<rodada>_<tipo>_<nnn>`, com três dígitos; versão `_v1` a `_v3`; cópia com erro `_erro<k>`.
3. Dinheiro da API: preço em centavos de dólar por milhão de tokens, inteiro; custo de cada chamada em milionésimos de centavo de dólar, inteiro; alerta e corte em centavos de dólar.
4. `saida/rodadas.json` é o único arquivo de `saida/` regravado, sempre por gravação atômica, e só para acrescentar rodada, mudar o estado de uma rodada ou registrar ensaio aprovado. Antes de cada regravação, a versão anterior vai para `saida/registro/rodadas_anteriores/rodadas_<carimbo>.json`.
5. Arquivos `.jsonl` são acrescentados linha a linha; uma última linha incompleta é ignorada na leitura.
6. Impressão digital do código: o identificador que o git dá ao conteúdo de `fabrica/` e de `pyproject.toml` na versão atual, sem mudança pendente em `fabrica/`, `dados/`, `instrucoes/`, `config/` e `pyproject.toml`. A leitura do git é feita por `arquivos.py`.
7. Contagem de tokens antes de enviar: pelo contador de tokens da API, que não cobra, só em `api_claude.py`.
8. Chave da API na variável de ambiente `ANTHROPIC_API_KEY`.
9. Pedidos e respostas: `saida/pedidos/<peça>_v<k>_<tarefa>_t<n>.json` e `saida/respostas/<peça>_v<k>_<tarefa>_t<n>.json`. Na ficha, que não tem versão, o nome não leva `_v<k>`.
10. Arquivos intermediários da conferência: `saida/conferencias/<peça>_v<k>_<etapa>.json`; o veredito final é `saida/conferencias/<peça>_v<k>.json`.
11. Estrutura montada: `saida/preparacao/<tipo>_estrutura.json` e `.md`.
12. Tabela de normas: objeto com `versao`, `diplomas[]` e `dispositivos[]`; citação conferida no nível de artigo e parágrafo, com inciso e alínea guardados para o cartão.
13. O rascunho leva a linha "DOCUMENTO SINTÉTICO — FICTÍCIO" no topo, posta por `redacao.py`, seguida do texto do redator como chegou.
14. Valor por extenso: quando a peça traz algarismos e extenso juntos, a extração devolve em `centavos` o valor por extenso, e o programa lê os algarismos do `texto`.
15. Comandos: `preparar`, `ensaio`, `fichas`, `avancar`, `revisar`, `erros`, `testar`, `publicar`, `relatorio`.
16. Gabarito e descartes: um arquivo por cópia (`<cópia>_gabarito.json` ou `<cópia>_descartada.json`); `gabarito.json` e `descartadas.json` são gravados uma vez, no fechamento do banco, já com o resultado das amostras.
17. No ensaio, os erros em miniatura e o pacote partem das três peças, qualquer que seja o veredito; o pacote do ensaio vai para `saida/pacotes/ensaio_<rodada>/<tipo>/`.
18. O ensaio aprovado é registrado pelo comando `ensaio --fechar <rodada>`, que aplica a regra da ARQUITETURA 5.12.1.
19. Defeito comprovado, que permite tocar num módulo já pronto, só existe com as três condições juntas: um teste (do brief atual ou do gate) falha por causa do módulo anterior, com a saída colada no relatório; a mudança é a mínima para o teste passar, sem refatoração; e não muda interface, formato de arquivo nem valor declarado. Fora disso, o executor para e registra a pendência.
20. Durante a construção, os briefs só alteram a ARQUITETURA na seção 8 (nome de cada comando, como o PLANO e a própria seção 8 mandam). Arquivos de teste e pastas novos são listados no relatório de cada brief e consolidados na árvore (seção 2) e na seção 2.4 pelo brief 023, antes do ensaio.

## Consequência

Nenhuma destas decisões muda o que o MVP mede nem um valor declarado. Mudança numa delas é feita por brief que a declare, com novo registro de decisão.
```
