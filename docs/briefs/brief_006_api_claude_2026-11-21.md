# Brief 006 — API da Claude em dois passos

- Fase: 4 — Clientes externos e condutor (PLANO §4)
- Objetivo: escrever `fabrica/comum/api_claude.py`, o único arquivo que fala com a API da Claude, em dois passos (gravar o pedido; coletar a resposta), com `testes/test_api_claude.py`, todo com cliente falso.
- Seções a ler: AGENTS §3 (chamada à API) e §6; PLANO §3 e §3.1; ARQUITETURA §2.4 (`test_api_claude.py`), §4 (resposta guardada como chegou), §5.12.5, §5.12.8, §7 e §7.1; registro de decisão 001 (itens 3, 7 e 9); armadilhas do PLAN: todas as de "api_claude.py".
- Arquivos que pode criar:
  - `fabrica/comum/api_claude.py`;
  - `testes/test_api_claude.py`;
  - `testes/conftest.py` — o bloqueio de rede de todos os testes (abaixo);
  - `docs/briefs/brief_006_api_claude_2026-11-21.md` (este brief);
  - `docs/docs/doc_006_api_claude_2026-11-21.md` (o relatório).
- Arquivos que pode alterar: `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: os módulos de `fabrica/comum/` já prontos (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `config/`; `scripts/`; `AGENTS.md`; `docs/PLANO.md`; `docs/ARQUITETURA.md`.
- Teste de aceite (escrito antes do código): `testes/test_api_claude.py`, com um cliente falso no lugar do pacote `anthropic`, que guarda cada pedido recebido e devolve respostas preparadas:
  1. todo pedido leva o nível de esforço (`output_config.effort`) e o teto de saída (`max_tokens`) da tarefa, lidos da configuração; as tarefas com resposta JSON levam o formato de saída estruturada (`output_config.format`) com o esquema de `formatos.esquema_resposta`; a redação não leva formato;
  2. nenhum pedido leva teto de tokens de raciocínio, uso forçado de ferramenta (nem ferramentas), temperatura ou outro parâmetro de amostragem, mensagem pré-escrita do assistente nem troca automática de modelo; o teste confere a lista exata de chaves enviadas;
  3. o pedido é gravado em `saida/pedidos/` antes de ser enviado (o falso confere que o arquivo existe quando é chamado);
  4. erro de rede, limite de uso e serviço sobrecarregado geram até 3 novas tentativas, com esperas de 30, 120 e 480 segundos (o relógio é falso: o teste não espera de verdade); depois da terceira, a coleta devolve "pausa" e grava a ocorrência;
  5. resposta com motivo de parada "recusa" ou cortada pelo teto de saída é gravada como chegou e marcada como fora do formato; resposta JSON que não passa no esquema também;
  6. a resposta é gravada em `saida/respostas/` sem mudança nenhuma, e a chamada vai para o registro com os tokens e o custo inteiro;
  7. o pedido que `gasto.py` não autoriza não é enviado, e a coleta devolve "corte";
  8. as partes do pedido saem na ordem fixa: instruções gerais, estrutura, trecho da tabela de normas, ficha (as partes que a tarefa não usa ficam de fora, sem mudar a ordem das outras);
  9. a chave da API não aparece em nenhum arquivo gravado nem em mensagem de erro;
  10. `contar_tokens` segue as mesmas novas tentativas de rede e de limite de uso (30, 120 e 480 segundos) e, esgotadas, a coleta devolve "pausa", sem enviar o pedido;
  11. com o bloqueio de `testes/conftest.py`, uma tentativa de abrir conexão de rede (para qualquer endereço, inclusive `127.0.0.1`) dentro de um teste falha com erro claro; o teste confere isso de propósito.
- Critério de conclusão: `test_api_claude.py` passa no gate (parte do critério da Fase 4 no PLANO).
- Fora do escopo: modo lote e cache (PLANO §2); a decisão do que acontece com a peça depois de resposta fora do formato (é de `estado.py`, 008, pela ARQUITETURA §5.12.8); qualquer instrução aos modelos; montar o cliente em `__main__.py` (008); qualquer chamada de verdade.
- Depende de: 005.

**Regras deste brief**

- O cliente do pacote `anthropic` (versão fixada no `pyproject.toml`) é recebido por parâmetro, já montado; `api_claude.py` não lê a chave nem a variável de ambiente (isso é de `__main__.py`, 008). Nos testes, o cliente é falso.
- Funções mínimas:
  - `gravar_pedido(...)`: recebe rodada, peça, versão, tarefa, as partes do pedido e, quando a resposta é JSON, o modelo de resposta; monta o `Pedido` de `formatos.py` com modelo, esforço e teto da tarefa (do `config.toml`) e grava `saida/pedidos/<peça>_v<k>_<tarefa>_t<n>.json`. Não envia nada. É o que os módulos de etapa chamam.
  - `contar_tokens(pedido)`: usa o contador de tokens da API, que não cobra, e devolve o número de tokens de entrada para `gasto.py`.
  - `coletar(caminho_do_pedido)`: chamada só por `estado.py`. No modo `uma_a_uma`, pede autorização a `gasto.py`, envia, faz as novas tentativas de rede, grava a `Resposta` como chegou, registra a chamada e devolve a situação (`ok`, `fora_do_formato`, `recusa`, `cortada`, `pausa` ou `corte`).
  - `gravar_pedido_igual(caminho_do_pedido)`: grava o pedido `t2`, idêntico ao `t1`, para o caso de resposta fora do formato. Não existe `t3`.
- Nunca se conserta resposta com expressão regular. A validação contra o esquema só lê; não altera o texto.
- **Bloqueio de rede (`testes/conftest.py`).** Vale para todos os testes, deste brief em diante: troca, durante a sessão de testes, a abertura de conexão de rede da biblioteca padrão (`socket.socket.connect` e `socket.create_connection`, para as famílias de endereço de rede `AF_INET` e `AF_INET6`, inclusive `127.0.0.1`) por uma função que falha com a mensagem "teste tentou usar a rede". Não troca `socket.socket` inteiro nem bloqueia `AF_UNIX` ou `socket.socketpair`, que o Python usa para canais locais entre processos. Assim, um teste que esqueça o cliente falso e tente falar com a API ou com o Ollama quebra o gate, em vez de gastar. Comandos locais (como o git dos testes de entrega e de congelamento) não usam rede e não são afetados. O executor confere que o gate inteiro continua verde com o bloqueio.
- Os arquivos de teste novos entram no relatório como acréscimo do método; a ARQUITETURA não é alterada aqui (consolidação no brief 023).
- Os nomes dos campos da API seguem a documentação da versão fixada do pacote. Se um nome dos canônicos (`output_config.effort`, `output_config.format`, `max_tokens`) não existir na versão fixada, o executor para e registra a pendência; não troca por outro parâmetro.
