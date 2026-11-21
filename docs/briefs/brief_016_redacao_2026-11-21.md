# Brief 016 — Redação

- Fase: 8 — Etapas com modelos (PLANO §4)
- Objetivo: escrever `fabrica/redacao.py` (pedido ao redator do tipo na ordem fixa, rascunho com metadados de origem e refação com o motivo) e `instrucoes/redacao.md`, com `testes/test_redacao.py`.
- Seções a ler: AGENTS §3 e §4; PLANO §3.1 e §4 (Fase 8); ARQUITETURA §1.3 (redação e refação), §2.3 (`redacao.md`), §3 (`Rascunho`), §4, §5.5, §5.12.8, §7.1 (ordem fixa do pedido); registros de decisão 001 (itens 9 e 13) e 002; armadilhas do PLAN: "instrucoes/".
- Arquivos que pode criar:
  - `fabrica/redacao.py`;
  - `instrucoes/redacao.md`;
  - `testes/test_redacao.py`;
  - `docs/briefs/brief_016_redacao_2026-11-21.md` (este brief);
  - `docs/docs/doc_016_redacao_2026-11-21.md` (o relatório).
- Arquivos que pode alterar:
  - `fabrica/__main__.py` — a etapa da redação na lista do condutor;
  - `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `dados/`; `config/`; os demais módulos (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `scripts/`; `AGENTS.md`; `docs/PLANO.md`; `docs/ARQUITETURA.md` (`test_redacao.py` vai para o relatório e é consolidado pelo brief 023).
- Teste de aceite (escrito antes do código): `testes/test_redacao.py`, com o cliente da API falso e uma ficha, uma estrutura montada e um trecho de exemplo em pasta temporária:
  1. o pedido sai para a tarefa de redação da classe do tipo (Haiku no baixo, Sonnet no médio e no alto, com o esforço e o teto da configuração) e com as partes na ordem fixa: instruções gerais (`redacao.md`), estrutura montada, trecho da tabela do tipo, ficha; na refação, o motivo da reprovação vai como quinta parte, depois da ficha, sem mudar a ordem das quatro primeiras;
  2. a redação não leva formato de saída estruturada;
  3. a resposta vira `saida/rascunhos/<peça>_v<k>.md` com a linha "DOCUMENTO SINTÉTICO — FICTÍCIO" no topo, seguida do texto como chegou, e os metadados de origem (ficha, estrutura, versão das instruções, que é a impressão digital de `redacao.md`, modelo e versão); a resposta crua continua em `saida/respostas/` sem mudança;
  4. a refação gera `_v2` e `_v3`, nunca sobrescreve a versão anterior e nunca passa de `_v3`;
  5. o texto de `redacao.md` não aparece no código (o teste procura uma frase do arquivo nos `.py` de `fabrica/`).
- Critério de conclusão: `test_redacao.py` passa no gate. O critério da Fase 8 no PLANO fecha no brief 018.
- Fora do escopo: a conferência do rascunho (017 e 018); a decisão de refazer (é de `decisao.py` e `estado.py`); o trecho da tabela (já em `estruturas.py`, 011); qualquer chamada de verdade.
- Depende de: 015.

**Regras deste brief**

- A redação segue a interface fixa das etapas (registro de decisão 002): `pedir` grava o pedido; `receber` grava o rascunho; nunca espera resposta.
- A estrutura vem de `saida/preparacao/<tipo>_estrutura.json`, aprovada no 014; o trecho, de `estruturas.trecho_da_tabela`; a tarefa de redação, do catálogo do tipo.
- **`instrucoes/redacao.md`** manda, como na ARQUITETURA §2.3: seguir os blocos na ordem, cada um com o seu título como título de segundo nível do Markdown (`## <título do bloco>`), que é o que `regras.py` confere; citar só o que está no trecho da tabela; não inventar fatos fora da ficha; não calcular valores novos (usar só os de `valores[]`); não usar nome de pessoa ou de empresa além dos marcadores da ficha; não dar nome a juiz, servidor ou membro do Ministério Público; não escrever a linha da marca (o programa a põe). Na refação, corrigir o motivo recebido sem mudar o que não foi apontado.
- Resposta de redação da primeira versão que falha duas vezes no formato, ou é recusada ou cortada, segue a ARQUITETURA §5.12.8 pelo condutor (a casa recebe uma ficha nova); na refação, conta como uma das três versões.
