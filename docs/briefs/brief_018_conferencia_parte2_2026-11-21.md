# Brief 018 — Conferência, parte 2: desempate, semelhança e decisão

- Fase: 8 — Etapas com modelos (PLANO §4)
- Objetivo: escrever `desempate.py`, `semelhanca.py` e `decisao.py` de `fabrica/conferencia/` e `instrucoes/opus_desempate.md`, montar em `fabrica/__main__.py` a ordem completa das etapas da conferência, com `testes/test_decisao.py` e o primeiro teste de integração, `testes/test_integracao.py`.
- Seções a ler: AGENTS §3, §4 e §8; PLANO §2 (estilo, semelhança) e §4 (Fase 8); ARQUITETURA §2.3 (`opus_desempate.md`), §2.4 (`test_decisao.py`), §5.6, §5.12.4, §5.12.8, §6, Anexos B.3; registros de decisão 001 e 002; armadilhas do PLAN: "semelhanca.py, teste_conferentes.py", "instrucoes/".
- Arquivos que pode criar:
  - `fabrica/conferencia/desempate.py`, `fabrica/conferencia/semelhanca.py`, `fabrica/conferencia/decisao.py`;
  - `instrucoes/opus_desempate.md`;
  - `testes/test_decisao.py`;
  - `testes/test_integracao.py` — o primeiro teste de integração (abaixo);
  - `docs/briefs/brief_018_conferencia_parte2_2026-11-21.md` (este brief);
  - `docs/docs/doc_018_conferencia_parte2_2026-11-21.md` (o relatório).
- Arquivos que pode alterar:
  - `fabrica/__main__.py` — a ordem das etapas da conferência na lista do condutor: extração, programas, checklist, conferente local, desempate, semelhança, decisão;
  - `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `dados/`; `config/`; os demais módulos (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `scripts/`; `AGENTS.md`; `docs/PLANO.md`; `docs/ARQUITETURA.md` (`test_integracao.py` vai para o relatório e é consolidado pelo brief 023).
- Teste de aceite (escrito antes do código): `testes/test_decisao.py`, com resultados de conferência de exemplo escritos no teste:
  1. as regras do Anexo B.3, item por item: itens de programa (a resposta do programa é a final); itens só do Haiku no baixo e no médio; itens do Haiku e do modelo local que concordam; que discordam (o Opus decide); risco alto (vale o Opus, salvo quando Haiku e modelo local concordam em "não passa", caso em que o item reprova mesmo com o Opus dizendo "passa"); risco médio sem conferente local por mais de 72 horas e pedido que não cabe no contexto (o Opus responde os itens do local e a resposta dele é a final);
  2. "não passa" em qualquer item eliminatório reprova; as quatro categorias do motivo: `conteudo` (eliminatório que não é semelhança), `semelhanca`, `ambos` e `formato` (extração, checklist ou desempate que falhou duas vezes no formato: reprovada sem refação);
  3. as notas de estilo ficam gravadas e não mudam o veredito, nem com média abaixo de 3;
  4. o caminho de cada item até a resposta final fica gravado no veredito;
  5. desempate: numa mesma peça, todas as perguntas ao Opus vão num pedido só; o pedido existe só nas três situações de `opus_desempate.md`;
  6. semelhança: duas peças iguais dão 1,0 e reprovam; peças diferentes ficam abaixo de 0,85; a marca, os títulos dos blocos e os marcadores de nome e de OAB não contam; o cálculo de Jaccard sobre trechos de cinco palavras é exato; em modo de teste a etapa não roda e grava "desligada em modo de teste", sem ninguém mexer no `config.toml`;
  7. a peça aprovada vai para `saida/aprovadas/<peça>_v<k>.md`, cópia do rascunho, e é a base de comparação da semelhança das peças seguintes do mesmo tipo;
  8. uma frase de `instrucoes/opus_desempate.md` não aparece em nenhum `.py` de `fabrica/` (o código lê o arquivo).
  E `testes/test_integracao.py`, o primeiro teste de integração: os módulos de verdade, ligados pela lista de etapas de `__main__.py`, com o cliente falso da API (006) e o modelo local falso (007), em pasta temporária com cópias de `fabrica/`, `pyproject.toml`, `dados/`, `instrucoes/` e `config/`, transformada num repositório git local com um commit (como no `test_congelamento.py`, sem remoto e sem rede), para que as impressões digitais do congelamento possam ser calculadas:
  9. os comandos `preparar` e `ensaio`, chamados por `executar` (brief 008) com os serviços falsos, seguidos de `avancar` até não haver mais o que fazer, levam as três peças do ensaio de ficha até veredito, passando por redação e por todas as etapas da conferência, sem erro e sem nenhuma etapa pulada;
  10. as respostas falsas são preparadas para que uma peça seja aprovada de primeira, uma passe por uma refação e a de risco alto tenha um item em que o Haiku e o modelo local discordam, decidido pelo Opus; o teste confere o veredito, a versão aprovada em `saida/aprovadas/` e o caminho do item no veredito;
  11. todo pedido falso tem o formato que o registro de decisão 002 fixa e passa pelo controle de gasto: o gasto registrado é a soma dos custos das respostas falsas;
  12. nenhum arquivo é gravado fora de `saida/` da pasta temporária, e o bloqueio de rede de `conftest.py` não é acionado;
  13. noutro cenário, com respostas falsas preparadas para isso: uma ficha que falha na conferência volta ao Haiku uma vez (`retornos_ao_haiku`), falha de novo e é trocada por ficha nova na mesma casa, com o próximo número livre do tipo; esgotadas as fichas novas da casa (`fichas_novas_por_casa`), a casa fica vazia, com a causa registrada; uma peça reprovada nas três versões é descartada, com o motivo gravado, e não aparece em `saida/aprovadas/`;
  14. noutro cenário, com o modelo local falso indisponível e o relógio falso dos serviços: a peça de risco médio, passadas 72 horas, tem os itens do conferente local respondidos pelo Opus, com a substituição registrada; a de risco alto, passados 7 dias, fica em pausa registrada; antes de cada prazo, um `avancar` não move nenhuma das duas; o modelo voltar e cair de novo antes de responder não zera a contagem; com o modelo de volta, o `avancar` seguinte leva a peça de risco alto ao veredito;
  15. a etapa de semelhança roda em todas as peças e grava o valor no veredito; noutro cenário, pelo comando `fichas --tipo manifestacao_ar_negativo` (que exige ensaio aprovado: o teste grava um em `saida/rodadas.json` da pasta temporária, no modelo de `formatos.py`, com as impressões calculadas por `congelamento.py`), com a redação falsa devolvendo o mesmo texto para duas peças, a primeira é aprovada e a segunda reprova com o motivo `semelhanca` e não vai para `saida/aprovadas/`.
  Cada cenário é uma função de teste própria, com nome que diz o cenário e pasta temporária própria, e não depende de outro cenário, para que uma falha aponte o cenário que quebrou.
- Critério de conclusão: `test_ancora.py`, `test_decisao.py` e `test_integracao.py` passam no gate, com respostas de modelo falsas, e a semelhança se desliga sozinha em modo de teste (critério da Fase 8 no PLANO).
- Fora do escopo: calibrar o limite de semelhança (PLANO §2); a regra de estilo que reprova (piloto); a refação (é de `estado.py`); qualquer chamada de verdade.
- Depende de: 017.

**Regras deste brief**

- **`instrucoes/opus_desempate.md`**, nas três situações da ARQUITETURA §2.3: discordância entre o Haiku e o modelo local num item; todos os itens das peças de risco alto; os itens do conferente local numa peça de risco médio que esperou mais de 72 horas ou cujo pedido não coube no contexto. Pede decisão por item, com justificativa, em JSON. Usa a tarefa `conferencia_opus` da configuração.
- **Semelhança**: compara a peça com as já aprovadas do mesmo tipo e da mesma rodada; proporção de trechos de cinco palavras seguidas em comum (Jaccard), depois de tirar a marca, os títulos dos blocos e os marcadores e de passar o texto a minúsculas sem acento; reprova a partir do limite do `config.toml` (0,85); a reprovação tem marca própria. O limite não é calibrado.
- **Decisão**: regra única ("não passa" em eliminatório reprova); veredito `aprovada`, `refazer` ou `descartada` (na terceira versão reprovada, ou na categoria formato); motivo em uma das quatro categorias; notas de estilo só registradas.
- A ordem das etapas montada em `__main__.py` é a única ordem da conferência; o teste dos conferentes (022) usa a mesma lista, em modo de teste.
- **Teste de integração.** Até aqui cada módulo foi testado sozinho. `test_integracao.py` liga os módulos de verdade, sem gastar nada, para que um defeito de interface entre a ficha, a redação e a conferência apareça agora, e não no ensaio. As respostas falsas são escritas no teste, uma por tarefa, válidas pelos modelos de `formatos.py`; não imitam a qualidade de um modelo de verdade, só o formato. Se o teste mostrar que a interface do registro de decisão 002 não basta, o executor para e registra; não muda a interface por conta própria. O brief 023 estende este teste até o fechamento do ensaio. O plano B (6 cópias por peça boa) não entra aqui: é testado no 021 com contagens falsas, e repeti-lo aqui pediria simular a rodada inteira até o banco, o que custa mais do que acrescenta.
- **Dono do teste.** `test_integracao.py` é criado aqui e só o 023 o estende. Os briefs 019 a 022 não mudam a interface do registro de decisão 002; se um deles fizer este teste falhar, isso é o aviso que o teste existe para dar, e vale a regra do defeito comprovado (registro de decisão 001, item 19).
