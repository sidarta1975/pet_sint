# Brief 020 — Revisão em duas etapas e publicação

- Fase: 10 — Revisão e publicação (PLANO §4)
- Objetivo: escrever `fabrica/revisao.py`, com todos os tipos de cartão (revisão, ensaio, amostra de 10 cópias, amostra das descartadas e leitura de publicação), o comando `revisar` e `revisar --resumo`, e `fabrica/publicacao.py`, com o comando `publicar`, com `testes/test_publicacao.py` e `testes/test_revisao.py`.
- Seções a ler: AGENTS §3 (segurança do produto), §7 e §8; PLANO §1, §2 e §4 (Fase 10); ARQUITETURA §1.3 (revisão e publicação), §1.4, §2.4 (`test_publicacao.py`), §3 (`Cartao`, `RespostasCartao`, `Metadados`), §4, §5.2 (leitura do responsável), §5.7 (amostras), §5.9, §5.10, §5.12.3, §5.12.7, §8; registro de decisão 001 (itens 13, 16 e 17); armadilhas do PLAN: "Ordem de construção".
- Arquivos que pode criar:
  - `fabrica/revisao.py`, `fabrica/publicacao.py`;
  - `testes/test_publicacao.py`, `testes/test_revisao.py`;
  - `docs/briefs/brief_020_revisao_publicacao_2026-11-21.md` (este brief);
  - `docs/docs/doc_020_revisao_publicacao_2026-11-21.md` (o relatório).
- Arquivos que pode alterar:
  - `fabrica/comum/formatos.py` — só para acrescentar o modelo `Amostras` (rodada, cópias sorteadas para a amostra de 10, descartadas sorteadas, data do sorteio), que o brief 021 grava e este brief lê; mudança de formato declarada por este brief;
  - `fabrica/__main__.py` — os comandos `revisar`, `revisar --resumo` e `publicar`;
  - `docs/ARQUITETURA.md` — seção 8, a linha de `python -m fabrica publicar --rodada <rodada>` e "construído no brief 020" nas de `revisar` (`test_revisao.py` vai para o relatório e é consolidado pelo brief 023);
  - `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `dados/`; `config/`; os demais módulos (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `scripts/`; `AGENTS.md`; `docs/PLANO.md`.
- Teste de aceite (escrito antes do código):
  - `testes/test_revisao.py`, com fichas, rascunhos, extrações, conferências e um arquivo de amostras de exemplo, e as respostas digitadas trocadas por uma função falsa:
    1. o cartão de revisão da primeira etapa mostra a peça (primeira versão), a ficha completa (nos embargos, a decisão fictícia com o trecho da âncora destacado), os fatos e valores da extração como auxílio, o texto dos dispositivos citados e a lista das citações resolvidas, e as três perguntas (ficha, peça pelo critério "a peça pode virar modelo como está, na forma e no conteúdo", e "há algum nome, número ou dado que pareça real?"); não mostra o veredito da fábrica;
    2. antes de confirmar, qualquer resposta pode ser corrigida; depois de confirmada, `saida/cartoes/<id>_respostas.json` é gravado e nunca muda (uma segunda tentativa é recusada);
    3. a segunda etapa (`<id>_etapa2.md`), com o veredito da fábrica sobre a mesma primeira versão, a categoria do motivo e os alertas com a origem de cada um, só é gerada depois das respostas confirmadas (o teste confere que ela não existe antes);
    4. a concordância é registrada nos dois sentidos, só nas peças cuja ficha foi aprovada; o destino de cada peça segue a tabela da ARQUITETURA §5.12.7;
    5. o cartão do ensaio mostra as duas etapas juntas, não às cegas, e pergunta se tudo saiu no formato certo (sim ou não, e o que saiu errado) e a pergunta fixa de dado real;
    6. o cartão da amostra de 10 cópias pergunta, para cada cópia, se o erro existe e se é o do gabarito; o da amostra das descartadas pergunta se o erro pedido existe na cópia, sem mostrar o que o Sonnet respondeu;
    7. o cartão da leitura de publicação, para versão refeita aprovada pela fábrica, não é às cegas e repete a pergunta de dado real;
    8. `revisar --resumo` lista os cartões respondidos, com as respostas e a data, sem mudar nada;
  - `testes/test_publicacao.py`: só a peça publicável entra no pacote (ficha e versão aprovada pela fábrica lidas e aprovadas pelo responsável; v2 ou v3 só depois da leitura de publicação); o pacote tem `.md`, `.json` com os metadados da ARQUITETURA §3, `.docx` e o índice; nenhum arquivo sai sem a marca "DOCUMENTO SINTÉTICO — FICTÍCIO" (no texto, no `.json`, no rodapé e nas propriedades do `.docx`, conferido abrindo o `.docx` gerado); peça sem a marca no rascunho faz o pacote recusar, em vez de acrescentá-la escondido; no ensaio, o pacote das três peças vai para `saida/pacotes/ensaio_<rodada>/<tipo>/`.
- Critério de conclusão: `test_publicacao.py` passa no gate (nenhum arquivo sem a marca) e o cartão de exemplo mostra que a segunda etapa só é gerada depois das respostas confirmadas (critério da Fase 10 no PLANO).
- Fora do escopo: sortear as amostras (021); fechar o banco e o teste dos conferentes (022); o relatório (023). As fases seguintes não alteram `revisao.py`.
- Depende de: 018.

**Regras deste brief**

- `revisar` é a única entrada das respostas do responsável (ARQUITETURA §8). Lê o que ele digita pela função `ler_linha` que recebe de `executar` (brief 008); nos testes, essa função é a falsa. Mostra o próximo cartão pendente, na ordem: ensaio, revisão, amostra de 10 cópias, amostra das descartadas, leitura de publicação; faz as perguntas; mostra as respostas juntas e pede confirmação. A leitura do teclado é recebida por parâmetro, para os testes.
- O cartão de revisão da primeira versão só é gerado depois que a conferência dessa versão terminou (porque mostra a extração e as citações); o veredito fica escondido até a confirmação.
- O cartão é gravado em `saida/cartoes/<rodada>_<tipo>_<n>_etapa1.md` (e `_etapa2.md`), como na ARQUITETURA §1.3. Os cartões de amostra e de leitura de publicação seguem o mesmo padrão de nome, com o tipo de cartão no nome.
- Publicação: `.docx` gerado com a biblioteca fixada no `pyproject.toml`, com a marca no rodapé de todas as páginas e nas propriedades do arquivo (título, assunto e comentários); `.json` com o modelo `Metadados` e `marca_sintetico` preenchida; índice em Markdown com uma linha por peça e a marca no topo.
- `revisao.py` é deste brief só (PLANO, Fase 10): por isso ele já traz os cartões das amostras e o do ensaio, que os briefs 021 a 024 só usam.
