# Brief 007 — Modelo local

- Fase: 4 — Clientes externos e condutor (PLANO §4)
- Objetivo: escrever `fabrica/comum/modelo_local.py`, o único arquivo que fala com o Ollama e com o `porteiro`, que só informa o resultado (rodou, esperou e rodou, indisponível) e nunca decide o destino da peça, com `testes/test_modelo_local.py`.
- Seções a ler: AGENTS §3 (Ollama) e §6; PLANO §2 (não inicia, não para, não descarrega o Ollama), §3 e §5; ARQUITETURA §2.4 (`test_modelo_local.py`), §5.12.4, §7.2 e §9; armadilhas do PLAN: todas as de "modelo_local.py".
- Arquivos que pode criar:
  - `fabrica/comum/modelo_local.py`;
  - `testes/test_modelo_local.py`;
  - `docs/briefs/brief_007_modelo_local_2026-11-21.md` (este brief);
  - `docs/docs/doc_007_modelo_local_2026-11-21.md` (o relatório).
- Arquivos que pode alterar: `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: os módulos de `fabrica/comum/` já prontos (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `config/`; `scripts/`; `AGENTS.md`; `docs/PLANO.md`; `docs/ARQUITETURA.md`.
- Teste de aceite (escrito antes do código): `testes/test_modelo_local.py`, com o `porteiro` e o Ollama trocados por falsos (nenhuma conexão de verdade e nenhum processo de verdade):
  1. tradução das respostas do `porteiro`: saída 0 vira "rodou"; saída 1 tenta de novo a cada 60 segundos por até 15 minutos (relógio falso) e vira "esperou e rodou" se couber, ou "indisponível" se não couber; saídas 2 e 3, falha do comando e comando ausente viram "indisponível" com a causa `porteiro`;
  2. o pedido maior que o `num_ctx` pela estimativa pessimista (caracteres divididos por 3, mais o teto de saída) não é enviado, e o resultado é "indisponível" com a causa `contexto`; o teste também confere a fração do `num_ctx` usada, que `estado.py` usa no ensaio (75%);
  3. o `num_ctx` vai sempre explícito no pedido ao Ollama, com o valor da configuração, e o esquema JSON vai no parâmetro de formato do Ollama;
  4. resposta que o Ollama encerra por tamanho e resposta que não passa no esquema viram fora do formato;
  5. etiqueta ou digest vazios na configuração (máquina sem Ollama) dão "indisponível" sem chamar nada;
  6. o módulo nunca chama comando que inicie, pare ou descarregue o Ollama ou um modelo: o teste confere a lista de comandos e endereços usados (só `porteiro cabe <modelo> --porta 11434 --json` e o pedido de conversa em `127.0.0.1:11434`).
- Critério de conclusão: `test_modelo_local.py` passa no gate (parte do critério da Fase 4 no PLANO).
- Fora do escopo: a regra do que acontece com a peça quando o modelo está indisponível, a janela e os prazos de 72 horas e 7 dias (todos de `estado.py`, 008); o conferente local (`local.py`, 017); a instrução `conferente_local.md` (017); qualquer chamada de verdade.
- Depende de: 005.

**Regras deste brief**

- O acesso ao Ollama é por HTTP na porta 11434 de `127.0.0.1`, com a biblioteca padrão do Python (nenhuma biblioteca nova). O `porteiro` é chamado como processo, com a linha exata da ARQUITETURA §7.2. Os dois acessos são recebidos por parâmetro, para que os testes os troquem por falsos.
- Funções mínimas: `consultar_porteiro(modelo)`; `estimar_tokens(texto, teto_saida)`; `conferir(pedido, esquema)`, que consulta o porteiro, estima o tamanho, envia e devolve o resultado (com a resposta guardada como chegou e a duração, para o relatório). A resposta é gravada em `saida/respostas/` por `arquivos.py`, como na API.
- O módulo só informa. Não sabe a classe de risco da peça nem a janela.
