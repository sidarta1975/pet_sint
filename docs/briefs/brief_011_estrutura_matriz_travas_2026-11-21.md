# Brief 011 — Montagem da estrutura, matriz e travas

- Fase: 6 — Preparação, travas e regras (PLANO §4)
- Objetivo: escrever `fabrica/estruturas.py` (montagem da estrutura em três níveis e trecho da tabela), `fabrica/matriz.py` (visão das travas, avaliação das travas, sorteio das combinações e das datas, combinação do ensaio e contagem de dias úteis) e o comando `preparar`, com `testes/test_travas.py`, usando exemplos dentro do teste.
- Seções a ler: AGENTS §3 e §4; PLANO §2 (prazo e datas), §4 (Fase 6, Fase 7 e regras para todas as fases); ARQUITETURA §1.2, §1.3 e §1.4 (preparação e ensaio), §2.2 (estruturas, matrizes, tabela, travas), §2.4 (`test_travas.py`), §5.4, §5.5, §8 e Anexos A.1, A.5 e A.6; registro de decisão 001; armadilhas do PLAN: "matriz.py, travas.json", "travas.json".
- Arquivos que pode criar:
  - `fabrica/estruturas.py`, `fabrica/matriz.py`;
  - `testes/test_travas.py`;
  - `docs/briefs/brief_011_estrutura_matriz_travas_2026-11-21.md` (este brief);
  - `docs/docs/doc_011_estrutura_matriz_travas_2026-11-21.md` (o relatório).
- Arquivos que pode alterar:
  - `fabrica/__main__.py` — o comando `preparar`;
  - `docs/ARQUITETURA.md` — só a seção 8, a linha do comando `python -m fabrica preparar` (a pasta `saida/preparacao/` vai para o relatório e é consolidada na árvore pelo brief 023);
  - `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `fabrica/comum/` (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `fabrica/ficticios.py`; `fabrica/conferencia/`; `dados/` (nasce no 014); `config/`; `scripts/`; `AGENTS.md`; `docs/PLANO.md`.
- Teste de aceite (escrito antes do código): `testes/test_travas.py`, com famílias, perfis, acréscimos, matrizes, travas, tabela e feriados de exemplo escritos dentro do teste, em pasta temporária:
  1. cada operação (`igual`, `diferente`, `maior`, `menor`, `na_lista`, `fora_da_lista`, `vazio`, `preenchido`) dá o resultado certo, inclusive a comparação com outro campo;
  2. as travas do Anexo A.5 que cruzam campos proíbem e permitem as combinações certas, nos dois efeitos: a de juizado com autor fora das categorias admitidas proíbe; a de juizado com pessoa jurídica de direito público como parte proíbe; a dos embargos com rito de juizado proíbe; a da manifestação com pedido de informar novo endereço exige `novo_endereco`, e passa com ele preenchido;
  3. a visão das travas é montada certa a partir de fichas de exemplo dos três tipos, com o campo que não se aplica vazio e `nova_diligencia` calculado;
  4. o sorteio de 10 combinações de uma matriz de exemplo respeita as travas, o teto por matéria e as contagens fixas dos eixos (5 e 5, 2-3-2-2-1 nos defeitos, 7 e 3 nas decisões), repete-se igual com a mesma semente e devolve "volta para a preparação" quando nenhuma combinação cabe em 1.000 tentativas;
  5. as datas sorteadas ficam em 2026, com os fatos até 2 anos antes do ajuizamento, e a data da peça fica dentro do prazo com pelo menos um dia útil de folga; o termo final em dias úteis exclui o dia do início, sábados, domingos e os feriados de exemplo, e nunca cai em 2027;
  6. a combinação do ensaio de cada tipo tem complexidade `media`, estilo `detalhado` e, nos embargos, sentença com omissão parcial, e respeita as travas;
  7. estruturas: família, perfil e acréscimo de exemplo montam a estrutura na ordem certa; um perfil que tenta retirar um bloco obrigatório, ou uma montagem em que um bloco obrigatório some, é recusada com a lista do que faltou;
  8. o trecho da tabela de um tipo traz só os dispositivos cujo campo `tipos` inclui o tipo, em ordem de diploma, artigo e parágrafo (caput, parágrafo único e parágrafos numerados, nessa ordem), e é o mesmo para todas as peças do tipo; os pares (mesmo diploma, mesmo assunto, função diferente) são contados;
  9. `python -m fabrica preparar`, sobre dados de exemplo em pasta temporária, grava `saida/preparacao/<tipo>_estrutura.json` e `.md` de cada tipo e o resumo da preparação, e recusa dados fora do formato.
- Critério de conclusão: `test_travas.py` passa no gate, inclusive a recusa da montagem sem bloco obrigatório (parte do critério da Fase 6 no PLANO).
- Fora do escopo: os dados de verdade (014); as fichas (015); regras, comparação e citações (012 e 013); qualquer chamada a modelo.
- Depende de: 003 e 004.

**Regras deste brief**

- **Travas.** A condição é uma lista de condições simples que valem juntas; "ou" vira duas travas. Uma função curta avalia cada lista; nada de texto executado como código nem linguagem própria (ARQUITETURA §2.2). A visão das travas tem exatamente os campos do Anexo A.5, e as travas que falam de "parte" viram uma para o autor e outra para o réu.
- **Sorteio.** Usa um gerador criado com a semente da rodada e o nome curto do tipo, para que cada tipo tenha um sorteio próprio e repetível. Eixos com número fixo são cruzados pelo sorteio; os de sorteio uniforme (tese, tipo de parte, motivo e pedido da manifestação) sorteiam entre os valores que as travas admitem. A matriz nunca sorteia categoria proibida para o rito nem parte com prazo em dobro.
- **Datas.** Ajuizamento, decisão, intimação, juntada do aviso, termo final do prazo e data da peça em 2026; fatos até 2 anos antes do ajuizamento. Nos embargos, prazo de 5 dias úteis da intimação (art. 1.023 do CPC); na manifestação, o prazo da determinação, ou 5 dias úteis se o juiz não fixou (art. 218, § 3º, do CPC). A data da peça fica com pelo menos um dia útil de folga antes do termo final. A contagem de dias úteis (`termo_final(inicio, dias_uteis, feriados)`) fica em `matriz.py`, e o brief 012 a usa em `regras.py`; nenhuma outra cópia dela existe.
- **Combinação do ensaio** (ARQUITETURA §1.4): complexidade `media`, estilo `detalhado` e, nos embargos, sentença com omissão parcial; os demais eixos são sorteados pela semente, dentro das travas.
- **Estrutura montada.** Junta os blocos da família, aplica os acréscimos, retiradas e ajustes do perfil e acrescenta os blocos do tipo. Perfil e acréscimo não podem retirar bloco obrigatório. Grava `saida/preparacao/<tipo>_estrutura.json` (validado por `formatos.py`) e uma cópia `.md` legível para o responsável aprovar. É o que a redação usa (016) e o que `regras.py` confere no item `estrutura` (012).
- **Trecho da tabela.** `trecho_da_tabela(tabela, tipo)` fica em `estruturas.py`. O tamanho é estimado sem chamar a API, pela mesma estimativa pessimista do modelo local (caracteres divididos por 3); passar de 8 mil tokens devolve "volta para a preparação".
- **Comando `preparar`.** Não gasta API. Valida todos os arquivos de `dados/` pelos modelos de `formatos.py`; monta e grava a estrutura de cada tipo; sorteia, só para conferir, as 10 combinações de cada tipo com uma semente de prova e diz em quantas tentativas coube; mede o trecho de cada tipo; mostra quantos dispositivos de cada tipo têm par; confere que todo dispositivo citado em `travas.json` está na tabela e que nenhum nome de `testes/dados/reais_reservados.json` está em `reais_proibidos.json` (sem mostrar os nomes reservados na tela nem no resumo: só a contagem). Grava `saida/preparacao/resumo.md`. Sai com erro se alguma conferência falhar.
