# Registro de decisão 002 — Interface fixa das etapas

- Data: 2026-11-21
- Situação: aceita
- Contexto: o PLANO (Fase 4) manda que `estado.py` chame cada etapa por uma interface fixa, escrita no brief do condutor, sem importar os módulos de etapa.

## Decisão

1. Cada peça é identificada por uma referência: rodada, tipo (nome curto), número e versão, mais o identificador da cópia quando a peça é uma cópia com erro no teste dos conferentes.
2. Os serviços entregues a toda etapa são um objeto só, com: o cliente da API (`api_claude`), o cliente do modelo local (`modelo_local`), o disco (`arquivos`), a configuração, o registro, o gasto, o relógio e o modo de teste (sim ou não).
3. Cada módulo de etapa expõe um objeto com:
   - `nome`: o nome da etapa, igual ao usado no nome do arquivo que ela grava;
   - `aplica(peca, servicos)`: se a etapa vale para a peça, pelo catálogo do tipo (por exemplo, o conferente local só em parte das peças de risco baixo);
   - `pedir(peca, servicos)`: grava o pedido (pela API ou pelo modelo local) ou, nas etapas só de programa, grava o resultado. Nunca espera resposta;
   - `receber(peca, resposta, servicos)`: recebe a resposta coletada por `estado.py` e grava o resultado. Se a resposta não serve ao formato, devolve "fora do formato", sem consertar nada;
   - `arquivo_resultado(peca)`: o caminho do arquivo que prova que a etapa terminou para aquela peça.
4. `estado.py` percorre as etapas na ordem recebida; a primeira cujo resultado falta e que se aplica é o próximo passo. Antes de cada passo, confere o congelamento e, nas etapas com modelo, a autorização do gasto.
5. A ordem das etapas de cada fluxo é montada em `fabrica/__main__.py` pelos briefs que constroem as etapas: fichas (015), redação (016), conferência (017 e 018).
6. A regra do modelo local indisponível (ARQUITETURA 5.12.4) e o destino das respostas fora do formato (5.12.8) ficam só em `estado.py`.

## Consequência

Uma etapa nova não muda `estado.py`: só acrescenta um objeto à lista. Mudança desta interface só por brief que a declare, com novo registro de decisão.
