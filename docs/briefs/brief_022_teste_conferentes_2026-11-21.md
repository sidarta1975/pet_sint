# Brief 022 — Teste dos conferentes

- Fase: 11 — Resto dos erros plantados, teste dos conferentes e relatório (PLANO §4)
- Objetivo: escrever `fabrica/teste_conferentes.py` e o comando `testar`, que recusa começar sem as duas amostras respondidas, fecha o banco, passa as cópias e as peças boas pela conferência em modo de teste e calcula as cinco taxas com a margem de Wilson, com `testes/test_teste_conferentes.py`.
- Seções a ler: AGENTS §4 e §8; PLANO §4 (Fase 11); ARQUITETURA §1.3 (teste dos conferentes), §5.1, §5.6 (`local.py` e `semelhanca.py` no teste), §5.7 (amostras e banco), §5.8, §5.12.8, §6 e Anexo C.4; registros de decisão 001 (item 16) e 002; armadilhas do PLAN: "teste_conferentes.py", "semelhanca.py, teste_conferentes.py", "estatistica.py, plano B".
- Arquivos que pode criar:
  - `fabrica/teste_conferentes.py`;
  - `testes/test_teste_conferentes.py`;
  - `docs/briefs/brief_022_teste_conferentes_2026-11-21.md` (este brief);
  - `docs/docs/doc_022_teste_conferentes_2026-11-21.md` (o relatório).
- Arquivos que pode alterar:
  - `fabrica/comum/formatos.py` — só para acrescentar o modelo `ResultadoTeste` de `saida/relatorios/teste_conferentes.json`, mudança de formato declarada por este brief;
  - `fabrica/__main__.py` — o comando `testar`;
  - `docs/ARQUITETURA.md` — seção 8, a linha de `python -m fabrica testar --rodada <rodada>` (`test_teste_conferentes.py` vai para o relatório e é consolidado pelo brief 023);
  - `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `fabrica/revisao.py`; `fabrica/estado.py` e os módulos de `conferencia/` (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `dados/`; `config/`; `scripts/`; `AGENTS.md`; `docs/PLANO.md`.
- Teste de aceite (escrito antes do código): `testes/test_teste_conferentes.py`, com banco, respostas das amostras e conferências falsas:
  1. sem as respostas confirmadas da amostra de 10 cópias e da amostra das descartadas, `testar` recusa começar e diz o que falta;
  2. no fechamento do banco: a cópia rejeitada na amostra sai do banco; com 2 ou mais rejeitadas, o banco é marcado não confiável (o critério central é calculado, mas não decide); com o erro pedido existindo em 2 ou mais descartadas, o banco é marcado filtrado pelo verificador; `gabarito.json` e `descartadas.json` são gravados uma vez, com o campo `amostra` preenchido; as descartadas não voltam ao banco; no ensaio, as marcas de banco não confiável e filtrado não se aplicam;
  3. a conferência roda em modo de teste: a semelhança fica desligada sem mexer no `config.toml`, não há refação, e cada cópia segue a sua original no conferente local;
  4. um erro só conta como pego quando a cópia é reprovada, um item aceito é reprovado na cópia e esse mesmo item passou na original, conferida de novo no mesmo teste; reprovar a cópia por outro item não conta; cópia terminada na categoria formato conta como não pega e é listada;
  5. as cinco taxas, cada uma com a margem de Wilson: a das cópias feitas por IA (critério central); a sem o Opus (mesmo denominador; no numerador só os pegos em que programa, Haiku ou modelo local também marcou "não passa" num item aceito que passou na original; nunca maior que a completa); a dos erros de julgamento por programa, com a contagem ao lado e inconclusiva com menos de 5; a dos erros de regra por programa (sanidade, precisa ser 100%); e a taxa de reprovação das peças boas no teste, que só descreve;
  6. os números separados por conferente, por tipo de erro e por origem, como diagnóstico;
  7. a marca "dependente do Opus" quando a taxa sem o Opus fica mais de 15 pontos abaixo da completa;
  8. `testar` é retomável: a primeira chamada fecha o banco e registra as peças do teste para o `avancar`; chamada antes de todas as conferências do teste terminarem diz quantas faltam; a chamada final grava `saida/relatorios/teste_conferentes.json`.
- Critério de conclusão: `test_teste_conferentes.py` passa no gate, com dados falsos calculando as cinco taxas com a margem de Wilson. O critério da Fase 11 no PLANO fecha no brief 023.
- Fora do escopo: escrever o relatório do MVP (023); qualquer chamada de verdade.
- Depende de: 021.

**Regras deste brief**

- A conferência do teste usa a mesma lista de etapas da conferência montada no 018, pelo condutor, em modo de teste (registro de decisão 002, item 2). Os arquivos do teste levam o prefixo `teste_` (`saida/conferencias/teste_<cópia ou peça>_<etapa>.json`), para não se misturarem com as conferências da rodada.
- O teste é uma passagem só, às cegas: a conferência não sabe o que é cópia e o que é original.
- Resposta fora do formato de extração, checklist ou desempate de uma cópia, no teste, conta como não pega e é listada (ARQUITETURA §5.12.8).
- A estatística vem de `estatistica.py` (005); nenhum cálculo de Wilson fica neste módulo.
