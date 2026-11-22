# Brief 005 — Gasto, estatística e congelamento

- Fase: 3 — Base (PLANO §4)
- Objetivo: escrever `gasto.py` (previsão pessimista, alerta e corte), `estatistica.py` (intervalo de Wilson de 95%) e `congelamento.py` (impressões digitais da rodada e conferência antes de cada passo), com `test_gasto.py`, `test_estatistica.py` e `test_congelamento.py`.
- Seções a ler: AGENTS §3, §4 e §7; PLANO §3 e §4 (Fase 3); ARQUITETURA §2.4 (`test_congelamento.py`, `test_estatistica.py`, `test_gasto.py`), §4 (congelamento), §5.1, §5.12.1, §5.12.2, §5.12.5, §5.12.6, §7.4; registro de decisão 001 (itens 3, 4 e 6); armadilhas do PLAN: "estatistica.py, plano B", "congelamento.py".
- Arquivos que pode criar:
  - `fabrica/comum/gasto.py`, `fabrica/comum/estatistica.py`, `fabrica/comum/congelamento.py`;
  - `testes/test_gasto.py`, `testes/test_estatistica.py`, `testes/test_congelamento.py`;
  - `docs/briefs/brief_005_gasto_estatistica_congelamento_2026-11-21.md` (este brief);
  - `docs/docs/doc_005_gasto_estatistica_congelamento_2026-11-21.md` (o relatório).
- Arquivos que pode alterar: `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `formatos.py`, `arquivos.py`, `config.py` e `registro.py` (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `config/`; `scripts/`; `AGENTS.md`; `docs/PLANO.md`; `docs/ARQUITETURA.md`.
- Teste de aceite (escrito antes do código):
  - `test_estatistica.py`: o intervalo de Wilson de 95% bate com os números da ARQUITETURA §2.4, arredondados a um décimo de ponto percentual: 80 em 100 dá de 71% a 87%; 32 em 40 dá limite inferior de 65,2%; 28 em 35 dá 64,1%; 5 em 5 dá de 57% a 100%; 2 em 25 dá de 2% a 25%. Também: zero em zero é recusado com erro, e não vira divisão por zero;
  - `test_gasto.py`: a previsão pessimista soma o gasto registrado em `chamadas.jsonl`, o custo previsto dos pedidos enviados e não coletados e o do pedido novo (tokens de entrada contados mais o teto de saída da tarefa, ao preço do modelo); o pedido que faria o total passar do corte não é autorizado e a parada é registrada em `ocorrencias.jsonl`; o pedido que deixa o total exatamente no corte é autorizado; o alerta dispara uma vez ao passar de 3000 centavos e não para nada; o custo é inteiro, em milionésimos de centavo de dólar; o custo marginal por peça aprovada exclui ensaio, cópias com erro e teste (ARQUITETURA §6);
  - `test_congelamento.py`: num repositório git temporário com `dados/`, `instrucoes/` e `config/` de exemplo, a rodada aberta grava as impressões; mudar uma letra num arquivo de `dados/` faz a conferência dizer "parar" antes do passo seguinte, com o arquivo que mudou; o mesmo com `config/gasto.toml`, com um arquivo de `instrucoes/` e com arquivo novo ou apagado numa dessas pastas; mudança pendente em `fabrica/` impede abrir a rodada; um commit só em `docs/` não muda a impressão do código; a comparação com o ensaio aprovado diz "iguais" ou lista o que mudou.
- Critério de conclusão: os três testes passam no gate. Com os briefs 003 e 004, fecha o critério da Fase 3 no PLANO.
- Fora do escopo: o envio de pedidos (006); a contagem de tokens (006, que entrega o número a `gasto.py`); abrir rodada pelo comando `fichas` ou `ensaio` (015) e registrar ensaio aprovado (023); qualquer comando.
- Depende de: 004.

**Regras deste brief**

- `gasto.py` recebe a configuração, o registro e a lista de pedidos enviados e não coletados por parâmetro; não abre arquivo. Funções mínimas: custo previsto de um pedido; autorizar ou recusar um pedido novo (com a ocorrência de parada no corte); custo real de uma resposta a partir dos tokens; total gasto; custo marginal por peça aprovada. O corte não sobe por nenhum caminho do programa (PLANO §2).
- **Haiku acima de 100 mil tokens.** Um pedido ao Haiku com mais de `limite_entrada_tokens_do_preco` tokens de entrada custa, nos tokens de entrada e de saída desse pedido, os preços `preco_entrada_acima_do_limite_centavos_por_milhao` e `preco_saida_acima_do_limite_centavos_por_milhao` do `config.toml` (50 e 250), e não os normais. Cada pedido é cobrado por si, e o limite conta todos os tokens de entrada do pedido (página oficial de preços, conferida em 2026-11-21). A previsão pessimista usa a mesma regra, com os tokens contados. Em `test_gasto.py`: um pedido ao Haiku com exatamente 100.000 tokens de entrada usa 10 e 50; com 100.001, usa 50 e 250, na entrada e na saída.
- `estatistica.py` tem uma função de Wilson de 95% (z = 1,96) que devolve a taxa e os limites inferior e superior, e uma função que diz se o critério central passa (taxa de pelo menos 0,80 e limite inferior de pelo menos 0,65), com os dois valores lidos da configuração.
- `congelamento.py` calcula as impressões digitais de cada arquivo de `dados/` e de `instrucoes/`, de `config/config.toml`, de `config/gasto.toml` e do código (registro de decisão 001, item 6), pelos serviços de `arquivos.py`; abre a rodada em `saida/rodadas.json` com identificador, semente, impressões e o ensaio aprovado de origem; confere, antes de cada passo, se algo mudou e, se mudou, devolve "parar" com a lista e grava a ocorrência; compara as impressões de uma rodada com as de um ensaio aprovado. Não decide nada além disso: quem para o passo é `estado.py` (008) e quem recusa a rodada é o comando `fichas` (015).
- Nenhum teste toca em `saida/` do repositório.
