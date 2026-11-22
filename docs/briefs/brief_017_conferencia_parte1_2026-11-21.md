# Brief 017 — Conferência, parte 1: extração, checklist e conferente local

- Fase: 8 — Etapas com modelos (PLANO §4)
- Objetivo: escrever as etapas `extracao.py`, `checklist.py` e `local.py` de `fabrica/conferencia/`, a etapa dos itens de programa (regras, citações e dado real sobre o rascunho) e as instruções `extracao.md`, `checklist.md` e `conferente_local.md`, com `testes/test_conferencia_etapas.py`.
- Seções a ler: AGENTS §3 e §4; PLANO §3.1 e §4 (Fase 8); ARQUITETURA §1.2 (conferência), §2.3 (`extracao.md`, `checklist.md`, `conferente_local.md`), §5.2, §5.6, §5.12.4, §5.12.8, §7.2, Anexos B e D; registros de decisão 001 (itens 10, 12 e 14) e 002; armadilhas do PLAN: "extracao.md, regras.py", "modelo_local.py", "modelo_local.py, estado.py", "instrucoes/".
- Arquivos que pode criar:
  - `fabrica/conferencia/extracao.py`, `fabrica/conferencia/checklist.py`, `fabrica/conferencia/local.py`;
  - `instrucoes/extracao.md`, `instrucoes/checklist.md`, `instrucoes/conferente_local.md`;
  - `testes/test_conferencia_etapas.py`;
  - `docs/briefs/brief_017_conferencia_parte1_2026-11-21.md` (este brief);
  - `docs/docs/doc_017_conferencia_parte1_2026-11-21.md` (o relatório).
- Arquivos que pode alterar:
  - `fabrica/conferencia/regras.py` — só para acrescentar o objeto de etapa "programas", que aplica `regras.py`, `citacoes.py` e `dados_reais.py` ao rascunho e grava `saida/conferencias/<peça>_v<k>_programas.json`, sem mudar as regras já testadas;
  - `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `docs/ARQUITETURA.md` (`test_conferencia_etapas.py` vai para o relatório e é consolidado pelo brief 023); `fabrica/__main__.py` (a ordem das etapas da conferência é montada no 018); `dados/`; `config/`; os demais módulos (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `scripts/`; `AGENTS.md`; `docs/PLANO.md`.
- Teste de aceite (escrito antes do código): `testes/test_conferencia_etapas.py`, com os clientes falsos e ficha, rascunho e estrutura de exemplo em pasta temporária:
  1. extração: o pedido vai para a tarefa `extracao`, com o esquema de `Extracao`; a resposta válida vira `<peça>_v<k>_extracao.json`; resposta fora do esquema volta "fora do formato", sem conserto;
  2. programas: sobre um rascunho e uma extração de exemplo, a etapa grava o resultado de `estrutura`, `citacao_fora_da_tabela`, `termos_inequivocos`, `coerencia_ficha`, `alcada` (só na inicial), `prazo` (só nos embargos e na manifestação), `dado_real` e `marca`; as citações não resolvidas viram alertas e entram no pedido do checklist como pergunta;
  3. checklist: o pedido leva só os itens do Anexo B.2 que se aplicam ao tipo, pelo catálogo, com os eliminatórios marcados, e as citações não resolvidas; a resposta traz cada item com o trecho e as três notas de estilo de 1 a 5;
  4. conferente local: `aplica` vale para todas as peças de risco médio e alto e para 2 das 10 de risco baixo, sorteadas pela semente da rodada (sempre as mesmas com a mesma semente); no teste dos conferentes, a cópia segue a sua original; o pedido leva só os itens `coerencia`, `pecas_anteriores` e `texto_generico` que se aplicam ao tipo, com o `num_ctx` da configuração; o resultado "indisponível", com a causa, é gravado como resultado, e quem decide o que fazer é `estado.py`;
  5. o texto das três instruções não aparece no código.
- Critério de conclusão: `test_conferencia_etapas.py` passa no gate. O critério da Fase 8 no PLANO fecha no brief 018.
- Fora do escopo: desempate, semelhança e decisão (018); a montagem da ordem das etapas em `__main__.py` (018); a regra do modelo local indisponível (já em `estado.py`); qualquer chamada de verdade.
- Depende de: 016.

**Regras deste brief**

- Cada etapa segue a interface do registro de decisão 002 e grava o seu arquivo intermediário em `saida/conferencias/<peça>_v<k>_<etapa>.json`.
- **`instrucoes/extracao.md`**, como na ARQUITETURA §2.3: extrair nomes com o papel; documentos e números; valores, cada um com o texto como aparece, os centavos e o lugar (`fatos`, `pedido` com o pedido a que pertence, `valor_causa` só no bloco formal do valor da causa, `outro` para o resto, inclusive a fundamentação da competência); só quantias em dinheiro (prazos, quantidades e limites em salários mínimos não entram); quando a peça traz algarismos e extenso juntos, `texto` com os dois e `centavos` com o valor por extenso (registro de decisão 001, item 14); datas com o texto e a data completa ou parcial; comarca e juízo com o texto; pedidos classificados na lista de naturezas do tipo ou como `outro`, com o texto; peças anteriores mencionadas; data da peça. Resposta só em JSON.
- **`instrucoes/checklist.md`**: responder cada item recebido com `passa` ou `nao_passa` e o trecho que justifica; responder as perguntas sobre citações não resolvidas; dar as notas de estilo (clareza, concisão, linguagem técnica), que só são registradas. Resposta só em JSON.
- **`instrucoes/conferente_local.md`**: texto curto, com os itens recebidos e resposta em JSON curto (item, resposta, trecho).
- O sorteio das 2 manifestações com conferente local usa a semente da rodada e o nome curto do tipo; o resultado é sempre o mesmo para a mesma rodada.
- Nenhuma das três instruções passa pela aprovação do 014: a primeira conferência delas é o ensaio (024).
