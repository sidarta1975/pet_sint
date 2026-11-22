# Brief 008 — Condutor das peças

- Fase: 4 — Clientes externos e condutor (PLANO §4)
- Objetivo: escrever `fabrica/estado.py`, que descobre pelos arquivos o ponto de cada peça e a leva ao próximo passo pela interface fixa das etapas, com a coleta das respostas, a refação até a terceira versão, o congelamento antes de cada passo e a válvula do modelo local; o comando `avancar`; e a montagem dos três clientes em `fabrica/__main__.py`; com `testes/test_estado.py`.
- Seções a ler: AGENTS §3, §4, §6 e §7; PLANO §4 (Fase 4 e regras para todas as fases); ARQUITETURA §1.1, §2.4 (`test_estado.py`), §4, §5.3, §5.6 (ordem das conferências), §5.12.2, §5.12.3, §5.12.4, §5.12.5, §5.12.8, §7, §8 e §9; registro de decisão 001; armadilhas do PLAN: "estado.py", "modelo_local.py, estado.py".
- Arquivos que pode criar:
  - `fabrica/estado.py`;
  - `testes/test_estado.py`;
  - `docs/adr/adr_002_interface_das_etapas_2026-11-21.md` (com a interface abaixo, literal);
  - `docs/briefs/brief_008_condutor_2026-11-21.md` (este brief);
  - `docs/docs/doc_008_condutor_2026-11-21.md` (o relatório).
- Arquivos que pode alterar:
  - `fabrica/__main__.py` — montagem dos três clientes e o comando `avancar`;
  - `docs/ARQUITETURA.md` — só a seção 8, para registrar o nome `avancar` como já em uso (a linha já existe; acrescentar "construído no brief 008");
  - `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: os módulos de `fabrica/comum/` (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `config/`; `scripts/`; `AGENTS.md`; `docs/PLANO.md`.
- Teste de aceite (escrito antes do código): `testes/test_estado.py`, com clientes falsos e etapas falsas (nenhum módulo de etapa existe ainda), em pasta temporária:
  1. para peças em cada ponto (ficha pronta; pedido de redação gravado e sem resposta; rascunho pronto; cada etapa da conferência; esperando o modelo local; reprovada com refação pendente; aprovada; descartada), o condutor escolhe o próximo passo certo;
  2. peça interrompida no meio (pedido gravado e resposta ausente) é retomada pela coleta, sem pedido novo; arquivo temporário deixado pela metade é ignorado;
  3. a refação gera a versão seguinte com o motivo, e a peça que é reprovada na terceira versão é descartada, sem quarta versão;
  4. resposta fora do formato gera o pedido `t2`; a segunda falha segue o destino da ARQUITETURA §5.12.8 para cada tipo de pedido (ficha, redação da primeira versão, redação de refação, extração, checklist, desempate, conferente local);
  5. a válvula do modelo local, por classe: no risco baixo, segue sem ele e registra a ausência; no médio, espera a janela e, passadas 72 horas da primeira indisponibilidade, chama a etapa do Opus no lugar dele e registra a substituição; no alto, espera e, passados 7 dias, grava a pausa, que não invalida; o pedido que não cabe no contexto não espera a janela em nenhuma classe; tudo com relógio falso;
  6. no ensaio (rodada `eNN`), o pedido acima de 75% do `num_ctx` e o que não cabe ficam registrados como ocorrência de contexto, para o fechamento do ensaio (023); na rodada (`rNN`), só o que não cabe é bloqueado;
  7. arquivo congelado mudado faz o condutor parar antes do passo seguinte e gravar a ocorrência;
  8. corte de gasto: a peça fica parada no passo, nada se perde, e a parada fica registrada; o próximo `avancar` não envia nada acima do corte;
  9. em modo de teste, o condutor não faz refação (uma passagem só) e passa o modo às etapas;
  10. `python -m fabrica avancar` monta os clientes e chama o condutor; comando desconhecido continua recusado.
- Critério de conclusão: `test_api_claude.py`, `test_modelo_local.py` e `test_estado.py` passam no gate, com o que pede o critério da Fase 4 no PLANO.
- Fora do escopo: todo módulo de etapa (fichas, redação e conferência, briefs 015 a 018); a lista de etapas de cada fluxo, que cada brief de etapa acrescenta a `__main__.py`; os comandos `fichas`, `ensaio` e `revisar`.
- Depende de: 006 e 007.

**Regras deste brief**

- `estado.py` não importa nenhum módulo de etapa. Recebe a lista de etapas e os serviços por parâmetro.
- `estado.py` não guarda estado próprio: descobre o ponto de cada peça pelos arquivos de `saida/`, a cada `avancar`. Os prazos de 72 horas e de 7 dias são contados a partir dos horários gravados (ARQUITETURA §9), desde a primeira indisponibilidade do modelo local naquela etapa daquela peça. A contagem nunca zera: nem reinício do computador, nem nova tentativa, nem uma volta e uma nova queda do modelo antes de ele responder. A espera termina só quando o modelo local responde a etapa, ou pela regra do prazo. Cada queda fica registrada em `ocorrencias.jsonl`.
- A janela da conferência local é lida do `config.toml` a cada `avancar`; não é agendamento.
- A montagem em `fabrica/__main__.py`: resolve a raiz do repositório a partir do próprio arquivo; lê a configuração por `config.py`; lê a chave da variável de ambiente `ANTHROPIC_API_KEY` e monta o cliente do pacote `anthropic` (sem a variável, o comando que precisa da API para com mensagem clara, sem gravar a chave em lugar nenhum); monta `api_claude`, `modelo_local` e `arquivos` e os entrega ao condutor. Nenhuma lógica de etapa em `__main__.py`.
- **Montagem separada da execução.** `__main__.py` tem duas funções: `montar_servicos(raiz)`, que monta os serviços de verdade (registro de decisão 002, item 2); e `executar(argumentos, servicos, ler_linha=input)`, que roda um comando com os serviços recebidos e com a função que lê o que o responsável digita (com valor padrão, para que os comandos que não leem nada possam ser chamados só com os dois primeiros). `main()` só chama as duas. Os testes de integração (018 e 023) chamam `executar` com serviços falsos e uma `ler_linha` falsa; nenhum teste roda `python -m fabrica` como outro processo, porque nem os clientes falsos nem o bloqueio de rede de `conftest.py` chegam a outro processo. Em `test_estado.py`: `executar` com serviços falsos roda `avancar` sem montar nenhum cliente de verdade.

**Conteúdo literal de `docs/adr/adr_002_interface_das_etapas_2026-11-21.md`:**

```
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
```

- A interface acima é a que os briefs 015 a 022 seguem. Se ao escrever `estado.py` o executor achar que ela não basta para um caso do teste de aceite, para e registra a pendência; não muda a interface por conta própria.
