# Brief 021 — Erros plantados pelo Opus e verificação do Sonnet

- Fase: 11 — Resto dos erros plantados, teste dos conferentes e relatório (PLANO §4)
- Objetivo: acrescentar a `fabrica/erros_plantados.py` as cópias com erro feitas pelo Opus, as três conferências de cada cópia (programa, verificador e gabarito), o descarte com motivo e o sorteio das duas amostras, com `instrucoes/plantar_erro.md` e `testes/test_erros_opus.py`, sem alterar `revisao.py`.
- Seções a ler: AGENTS §3, §4 e §8; PLANO §1 (custo), §3.1 e §4 (Fase 11); ARQUITETURA §2.3 (`plantar_erro.md`), §5.1, §5.7, §5.12.6, §5.12.8, Anexos B, C.3 e C.4; registro de decisão 001 (itens 16 e 17); armadilhas do PLAN: "erros_plantados.py", "estatistica.py, plano B", "instrucoes/".
- Arquivos que pode criar:
  - `instrucoes/plantar_erro.md`;
  - `testes/test_erros_opus.py`;
  - `docs/briefs/brief_021_erros_opus_2026-11-21.md` (este brief);
  - `docs/docs/doc_021_erros_opus_2026-11-21.md` (o relatório).
- Arquivos que pode alterar:
  - `fabrica/erros_plantados.py` — acréscimo da parte com modelos, sem mudar a parte por programa já testada;
  - `fabrica/__main__.py` — só a parte do comando `erros` que chama as cópias do Opus e o sorteio das amostras;
  - `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `docs/ARQUITETURA.md` (`test_erros_opus.py` vai para o relatório e é consolidado pelo brief 023); `fabrica/revisao.py` (é do 020 só); `dados/`; `config/`; os demais módulos (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `scripts/`; `AGENTS.md`; `docs/PLANO.md`.
- Teste de aceite (escrito antes do código): `testes/test_erros_opus.py`, com o Opus, o Sonnet e o Haiku falsos:
  1. cada peça boa recebe 4 vagas de cópia do Opus, de tipos diferentes entre si, sorteados entre os do Anexo C.3 que se aplicam ao tipo, metade sutis; com 14 a 19 peças boas, 6 vagas; com 20 ou mais, 4; com menos de 14, nenhuma cópia é pedida e o critério central é marcado inconclusivo (plano B); no ensaio, 1 vaga por peça; o sorteio equilibra os tipos de erro no conjunto e é igual com a mesma semente;
  2. o Opus devolve trecho original e trecho novo, e o programa faz a troca; o programa descarta a cópia quando o trecho original não aparece exatamente uma vez, quando a troca muda mais de uma região, quando a região passa de um quarto do texto, quando o resto não ficou idêntico, ou quando os itens de programa do Anexo B.1 (menos `semelhanca`), rodados na cópia, reprovam algum item fora dos itens aceitos;
  3. o Sonnet recebe a original e a cópia, sem saber o erro pedido, e só os itens do Anexo B que se aplicam ao tipo, menos `semelhanca` e `marca`; a cópia passa só se o item apontado estiver entre os aceitos e não houver outro problema;
  4. motivo do descarte, decidido por programa: sem item apontado, é sempre `nao_viu_erro`, mesmo que o Sonnet descreva outro problema; com outro problema, `outro_problema`; com item fora dos aceitos, `outro_item`; falha na conferência de programa, motivo vazio;
  5. a cópia descartada é refeita uma vez; falhando de novo, sorteia-se outro tipo de erro para a vaga, e o relatório conta a vaga que trocou de tipo; o custo das descartadas fica marcado à parte no registro;
  6. o sorteio das amostras grava `saida/erros/<rodada>_amostras.json`, no modelo `Amostras`: na rodada, 10 cópias feitas por IA que passaram nas três conferências e até 5 descartadas por `nao_viu_erro` (todas, se forem menos de 5); no ensaio, todas as cópias do Opus aceitas (até 3) e até 1 descartada por `nao_viu_erro`, se houver; o sorteio só acontece depois que todas as vagas foram resolvidas;
  7. nenhum pedido é enviado de verdade, e o texto de `plantar_erro.md` não aparece no código.
- Critério de conclusão: `test_erros_opus.py` passa no gate. O critério da Fase 11 no PLANO fecha no brief 023.
- Fora do escopo: os cartões das amostras (já no 020); fechar o banco e consolidar o gabarito (022); responder as amostras (só o responsável, no 024 e no 025).
- Depende de: 019 e 020.

**Regras deste brief**

- **`instrucoes/plantar_erro.md`** tem os dois textos da ARQUITETURA §2.3, separados por títulos: o do Opus (criar uma cópia com um erro do tipo pedido, sutil ou direto, devolvendo só o trecho original copiado literalmente e o trecho novo, em JSON; tarefa `copia_com_erro`) e o do Sonnet (com a original e a cópia, dizer que item da lista recebida o erro viola, descrever o erro e dizer se a troca criou algum outro problema, em JSON; tarefa `verificacao_copia`). O código lê cada texto pelo título; nenhum trecho fica no programa.
- **Itens de programa na cópia**: precisam da extração da cópia, que é pedida ao Haiku com a mesma instrução e a mesma tarefa da extração (017), como parte da criação do banco. Essa extração não é reaproveitada no teste dos conferentes, que confere tudo de novo, às cegas.
- **Nomes**: vagas 2 em diante (`<peça>_erro<k>_<tentativa>.md`), com `<cópia>_gabarito.json` para a aceita e `<cópia>_descartada.json` para cada descarte (registro de decisão 001, item 16). `gabarito.json` e `descartadas.json` consolidados são do 022.
- **Quem cria e quem verifica**: o Opus cria; o Sonnet verifica 100% das cópias do Opus; o Sonnet nunca cria cópia nem é conferente avaliado (ARQUITETURA §5.1).
- O comando `erros --rodada <rodada>` passa a fazer, em sequência e de forma retomável: cópias por programa (019), pedidos das cópias do Opus, e, quando `avancar` tiver coletado as respostas e todas as vagas estiverem resolvidas, o sorteio das amostras. Os pedidos ao Opus, ao Haiku e ao Sonnet seguem o caminho de dois passos, com a coleta pelo `avancar`, pela interface do registro de decisão 002.
