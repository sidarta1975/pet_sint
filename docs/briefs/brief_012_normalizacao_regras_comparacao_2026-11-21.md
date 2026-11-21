# Brief 012 — Normalização, regras e comparação com a ficha

- Fase: 6 — Preparação, travas e regras (PLANO §4)
- Objetivo: escrever `fabrica/comum/normalizacao.py` (normalizações do Anexo D) e `fabrica/conferencia/regras.py` (itens de programa `estrutura`, `coerencia_ficha`, `alcada`, `prazo`, `termos_inequivocos` e `marca`), com `testes/dados/comparacao_exemplos.json` (conteúdo abaixo), `testes/test_regras.py` e `testes/test_comparacao.py`.
- Seções a ler: AGENTS §3 e §4; PLANO §2 e §4 (Fase 6); ARQUITETURA §2.2 (perfis, termos inequívocos, feriados), §2.3 (`extracao.md`), §2.4 (`test_regras.py`, `test_comparacao.py`), §4, §5.6 (`regras.py`), Anexos A, B.1 e D; registro de decisão 001 (itens 13 e 14); armadilhas do PLAN: "extracao.md, regras.py", "fichas.py, regras.py", "normalizacao.py, fichas.py (âncora)".
- Arquivos que pode criar:
  - `fabrica/comum/normalizacao.py`;
  - `fabrica/conferencia/regras.py`;
  - `testes/dados/comparacao_exemplos.json` (cópia literal do bloco abaixo);
  - `testes/test_regras.py`, `testes/test_comparacao.py`;
  - `docs/briefs/brief_012_normalizacao_regras_comparacao_2026-11-21.md` (este brief);
  - `docs/docs/doc_012_normalizacao_regras_comparacao_2026-11-21.md` (o relatório).
- Arquivos que pode alterar: `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `fabrica/matriz.py` (este brief só usa a contagem de dias úteis de lá); `fabrica/comum/` já pronto (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `dados/`; `config/`; `scripts/`; `AGENTS.md`; `docs/PLANO.md`; `docs/ARQUITETURA.md`.
- Teste de aceite (escrito antes do código):
  - `testes/dados/comparacao_exemplos.json`, copiado literalmente deste brief antes de qualquer código;
  - `testes/test_comparacao.py`: cada caso do arquivo com `"verificado_por": "regras"` dá o resultado esperado (cada forma aceita passa, cada diferença real reprova), contra a ficha de base do arquivo; os casos com `"verificado_por": "fichas"` são ignorados aqui e testados no brief 015;
  - `testes/test_regras.py`, com peças, extrações e fichas de exemplo escritas no teste: `estrutura` reprova bloco obrigatório faltando e bloco fora de ordem, e aprova a peça completa; `alcada` reprova valor da causa de R$ 64.840,01 e aprova R$ 64.840,00; `prazo` reprova data da peça um dia útil depois do termo final e aprova no termo final, com um feriado de exemplo no meio do prazo; `termos_inequivocos` reprova cada termo de uma lista de exemplo (com e sem acento, em maiúsculas) e aprova a peça sem eles; `marca` reprova o rascunho sem a linha da marca.
- Critério de conclusão: `test_regras.py` e `test_comparacao.py` passam no gate (parte do critério da Fase 6 no PLANO).
- Fora do escopo: as regras da âncora e dos termos principais do Anexo E (015, que as acrescenta a `normalizacao.py`); citações (013); detector de dado real (010); a recusa de ficha com valor igual ao salário mínimo ou à alçada (015); a etapa de conferência que chama `regras.py` (017).
- Depende de: 011.

**Regras deste brief**

- `regras.py` recebe tudo por parâmetro (rascunho, extração, ficha, estrutura montada, perfil, termos inequívocos, feriados, configuração) e devolve, para cada item, um `ResultadoItem` (`passa` ou `nao_passa`, quem respondeu = `programa`, e o trecho). Não lê arquivo nem chama modelo.
- **Estrutura.** Cada bloco da estrutura montada aparece no rascunho como um título de segundo nível do Markdown (`## <título do bloco>`), na ordem da estrutura. É a forma que `redacao.md` manda usar (016). O item reprova bloco obrigatório ausente ou fora de ordem.
- **Coerência com a ficha.** Aplica todas as linhas do Anexo D, nesta ordem: valores (algarismos, extenso, referência legal, soma, arredondamento), datas, CEP, documentos e protocolos, nomes e OAB, designação da parte, comarca e juízo, pedidos. Cada reprovação guarda o valor extraído e o da ficha, para o relatório separar erro da peça de erro da extração.
- **Valor por extenso** (registro de decisão 001, item 14): quando o `texto` de um valor extraído traz algarismos e extenso juntos, o programa lê os algarismos do `texto` e os compara com `centavos`, que a extração devolve como o valor por extenso. Diferentes entre si: reprova, mesmo que um deles bata com a ficha.
- **Soma** (Anexo D, linha "Soma"): um valor que não está em `valores[]` só passa se for igual ao valor da causa ou à soma de dois ou mais valores **distintos** dos pedidos da ficha (cada valor de pedido entra no máximo uma vez). Valor citado só nos fatos, que não é de pedido, não entra em soma. Dobro e qualquer outro cálculo precisam estar em `valores[]`. Com poucos pedidos, a conta de todas as combinações é exata e barata; o código não usa aproximação.
- **Arredondamento** (Anexo D, linha "Arredondamento"): só no lugar `fatos`, só com marca de aproximação ("cerca de", "aproximadamente", "mais de"), e só com diferença de até 1% para um valor da ficha, lida da chave `comparacao.diferenca_maxima_arredondamento` do `config.toml` (0,01). O Anexo D não manda conferir o sentido da marca (se "mais de" é mesmo mais), e por isso o programa não confere.
- **Referência legal.** O salário mínimo e a alçada vêm de `salario_minimo_referencia` da ficha (e a alçada é 40 vezes ele); nunca de número escrito no código.
- **Alçada.** Valor da causa (lugar `valor_causa`) até 40 salários mínimos de 2026. **Prazo.** Data da peça extraída até o termo final calculado por `matriz.termo_final` a partir do início e dos dias úteis do prazo da ficha, com os feriados recebidos.
- **Termos inequívocos e marca.** Comparação sem diferença de maiúsculas e acentos. A marca é a linha exata "DOCUMENTO SINTÉTICO — FICTÍCIO".
- A normalização roda sobre cópias; nunca altera o texto guardado (AGENTS §4).

**Conteúdo literal de `testes/dados/comparacao_exemplos.json`:**

```json
{
  "versao": "2026-11-21-v2",
  "descricao": "Exemplos das regras de tolerância do Anexo D. A ficha de base é uma Petição Inicial em Juizado Especial Cível fictícia. Cada caso diz a regra, a entrada extraída, o resultado esperado e quem verifica. Versão 2: casos soma_05 e soma_06 acrescentados (88 casos).",
  "ficha_base": {
    "salario_minimo_referencia_centavos": 162100,
    "valores": [
      {"id": "v1", "descricao": "danos materiais", "centavos": 150000},
      {"id": "v2", "descricao": "danos morais", "centavos": 500000},
      {"id": "v3", "descricao": "restituição de tarifa cobrada indevidamente", "centavos": 30000},
      {"id": "v4", "descricao": "valor da causa, soma dos pedidos", "centavos": 680000},
      {"id": "v5", "descricao": "total pago no contrato, citado nos fatos", "centavos": 281500}
    ],
    "pedidos": [
      {"id": "p1", "natureza": "danos_materiais", "valor": "v1"},
      {"id": "p2", "natureza": "danos_morais", "valor": "v2"},
      {"id": "p3", "natureza": "restituicao_simples", "valor": "v3"},
      {"id": "p4", "natureza": "exclusao_cadastro", "valor": null}
    ],
    "valor_causa": "v4",
    "datas": ["2026-03-15", "2026-04-10", "2026-06-04"],
    "partes": [
      {"papel": "autor", "categoria": "pessoa_fisica", "nome": "Nome e Sobrenome da Parte Autora", "documento": "123.456.789-00", "cep": "13010-111"},
      {"papel": "reu", "categoria": "pessoa_juridica_privada", "nome": "Razão Social da Parte Ré", "documento": "11.222.333/0001-80", "cep": "13015-904"}
    ],
    "advogado": {"nome": "Nome e Sobrenome do Advogado", "oab": "OAB/UF nº 000.000"},
    "numero_processo": "0001234-04.2026.8.26.0100",
    "protocolo": "SINT-2026-000123",
    "comarca": "Campinas",
    "juizo": "Juizado Especial Cível da Comarca de Campinas",
    "pedidos_acessorios_padrao": ["citacao_reu", "producao_provas"]
  },
  "casos": [
    {"id": "valor_01", "regra": "valor", "entrada": {"texto": "R$ 1.500,00", "centavos": 150000, "lugar": "pedido", "pedido": "p1"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "valor_02", "regra": "valor", "entrada": {"texto": "R$ 1500", "centavos": 150000, "lugar": "pedido", "pedido": "p1"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "valor_03", "regra": "valor", "entrada": {"texto": "1.500 reais", "centavos": 150000, "lugar": "pedido", "pedido": "p1"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "valor_04", "regra": "valor", "entrada": {"texto": "R$ 1.500,01", "centavos": 150001, "lugar": "pedido", "pedido": "p1"}, "esperado": "reprova", "verificado_por": "regras", "nota": "diferença de 1 centavo no pedido"},
    {"id": "valor_05", "regra": "valor", "entrada": {"texto": "R$ 6.800,00", "centavos": 680000, "lugar": "valor_causa", "pedido": null}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "valor_06", "regra": "valor", "entrada": {"texto": "R$ 6.799,99", "centavos": 679999, "lugar": "valor_causa", "pedido": null}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "valor_07", "regra": "valor", "entrada": {"texto": "R$ 300,00", "centavos": 30000, "lugar": "pedido", "pedido": "p3"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "valor_08", "regra": "valor", "entrada": {"texto": "R$ 3.000,00", "centavos": 300000, "lugar": "pedido", "pedido": "p1"}, "esperado": "reprova", "verificado_por": "regras", "nota": "valor que não está na ficha"},
    {"id": "extenso_01", "regra": "valor", "entrada": {"texto": "R$ 1.500,00 (mil e quinhentos reais)", "centavos": 150000, "lugar": "pedido", "pedido": "p1"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "extenso_02", "regra": "valor", "entrada": {"texto": "R$ 1.500,00 (mil e cinquenta reais)", "centavos": 105000, "lugar": "pedido", "pedido": "p1"}, "esperado": "reprova", "verificado_por": "regras", "nota": "algarismos batem com a ficha, extenso não"},
    {"id": "extenso_03", "regra": "valor", "entrada": {"texto": "R$ 1.050,00 (mil e quinhentos reais)", "centavos": 150000, "lugar": "pedido", "pedido": "p1"}, "esperado": "reprova", "verificado_por": "regras", "nota": "extenso bate com a ficha, algarismos não"},
    {"id": "extenso_04", "regra": "valor", "entrada": {"texto": "R$ 6.800,00 (seis mil e oitocentos reais)", "centavos": 680000, "lugar": "valor_causa", "pedido": null}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "legal_01", "regra": "valor", "entrada": {"texto": "R$ 1.621,00", "centavos": 162100, "lugar": "fatos", "pedido": null}, "esperado": "passa", "verificado_por": "regras", "nota": "salário mínimo como referência legal"},
    {"id": "legal_02", "regra": "valor", "entrada": {"texto": "R$ 1.621,00", "centavos": 162100, "lugar": "outro", "pedido": null}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "legal_03", "regra": "valor", "entrada": {"texto": "R$ 1.621,00", "centavos": 162100, "lugar": "pedido", "pedido": "p1"}, "esperado": "reprova", "verificado_por": "regras", "nota": "no pedido segue a regra comum"},
    {"id": "legal_04", "regra": "valor", "entrada": {"texto": "R$ 64.840,00", "centavos": 6484000, "lugar": "outro", "pedido": null}, "esperado": "passa", "verificado_por": "regras", "nota": "alçada citada na fundamentação da competência"},
    {"id": "legal_05", "regra": "valor", "entrada": {"texto": "R$ 64.840,00", "centavos": 6484000, "lugar": "valor_causa", "pedido": null}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "legal_06", "regra": "valor", "entrada": {"texto": "R$ 64.840,00 (sessenta e quatro mil, oitocentos e quarenta reais)", "centavos": 6484000, "lugar": "fatos", "pedido": null}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "soma_01", "regra": "valor", "entrada": {"texto": "R$ 1.800,00", "centavos": 180000, "lugar": "fatos", "pedido": null}, "esperado": "passa", "verificado_por": "regras", "nota": "soma de v1 e v3"},
    {"id": "soma_02", "regra": "valor", "entrada": {"texto": "R$ 5.300,00", "centavos": 530000, "lugar": "outro", "pedido": null}, "esperado": "passa", "verificado_por": "regras", "nota": "soma de v2 e v3"},
    {"id": "soma_03", "regra": "valor", "entrada": {"texto": "R$ 3.000,00", "centavos": 300000, "lugar": "fatos", "pedido": null}, "esperado": "reprova", "verificado_por": "regras", "nota": "dobro de v1 não registrado na ficha"},
    {"id": "soma_04", "regra": "valor", "entrada": {"texto": "R$ 2.000,00", "centavos": 200000, "lugar": "fatos", "pedido": null}, "esperado": "reprova", "verificado_por": "regras", "nota": "não é valor nem soma da ficha"},
    {"id": "soma_05", "regra": "valor", "entrada": {"texto": "R$ 6.500,00", "centavos": 650000, "lugar": "outro", "pedido": null}, "esperado": "passa", "verificado_por": "regras", "nota": "soma de v1 e v2, dois valores de pedidos"},
    {"id": "soma_06", "regra": "valor", "entrada": {"texto": "R$ 4.315,00", "centavos": 431500, "lugar": "fatos", "pedido": null}, "esperado": "reprova", "verificado_por": "regras", "nota": "v1 mais v5: v5 está nos fatos e não é valor de pedido"},
    {"id": "arred_01", "regra": "valor", "entrada": {"texto": "cerca de R$ 2.800,00", "centavos": 280000, "lugar": "fatos", "pedido": null}, "esperado": "passa", "verificado_por": "regras", "nota": "0,53% de v5, com marca"},
    {"id": "arred_02", "regra": "valor", "entrada": {"texto": "aproximadamente R$ 2.800,00", "centavos": 280000, "lugar": "fatos", "pedido": null}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "arred_03", "regra": "valor", "entrada": {"texto": "mais de R$ 2.800,00", "centavos": 280000, "lugar": "fatos", "pedido": null}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "arred_04", "regra": "valor", "entrada": {"texto": "R$ 2.800,00", "centavos": 280000, "lugar": "fatos", "pedido": null}, "esperado": "reprova", "verificado_por": "regras", "nota": "arredondamento sem marca"},
    {"id": "arred_05", "regra": "valor", "entrada": {"texto": "aproximadamente R$ 2.780,00", "centavos": 278000, "lugar": "fatos", "pedido": null}, "esperado": "reprova", "verificado_por": "regras", "nota": "diferença de 1,24%"},
    {"id": "arred_06", "regra": "valor", "entrada": {"texto": "cerca de R$ 6.790,00", "centavos": 679000, "lugar": "valor_causa", "pedido": null}, "esperado": "reprova", "verificado_por": "regras", "nota": "arredondamento no valor da causa"},
    {"id": "arred_07", "regra": "valor", "entrada": {"texto": "R$ 2.815,00", "centavos": 281500, "lugar": "fatos", "pedido": null}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "data_01", "regra": "data", "entrada": {"texto": "15 de março de 2026", "data": "2026-03-15"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "data_02", "regra": "data", "entrada": {"texto": "15/03/2026", "data": "2026-03-15"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "data_03", "regra": "data", "entrada": {"texto": "15.3.2026", "data": "2026-03-15"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "data_04", "regra": "data", "entrada": {"texto": "domingo, 15 de março de 2026", "data": "2026-03-15"}, "esperado": "passa", "verificado_por": "regras", "nota": "dia da semana ignorado"},
    {"id": "data_05", "regra": "data", "entrada": {"texto": "março de 2026", "data": "2026-03"}, "esperado": "passa", "verificado_por": "regras", "nota": "data parcial com mês e ano da ficha"},
    {"id": "data_06", "regra": "data", "entrada": {"texto": "16 de março de 2026", "data": "2026-03-16"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "data_07", "regra": "data", "entrada": {"texto": "maio de 2026", "data": "2026-05"}, "esperado": "reprova", "verificado_por": "regras", "nota": "nenhuma data da ficha em maio"},
    {"id": "data_08", "regra": "data", "entrada": {"texto": "há três meses", "data": null}, "esperado": "passa", "verificado_por": "regras", "nota": "data relativa não é comparada"},
    {"id": "data_09", "regra": "data", "entrada": {"texto": "04/06/2026", "data": "2026-06-04"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "data_10", "regra": "data", "entrada": {"texto": "10/04/2025", "data": "2025-04-10"}, "esperado": "reprova", "verificado_por": "regras", "nota": "ano diferente"},
    {"id": "cep_01", "regra": "cep", "entrada": {"papel": "autor", "texto": "13010-111"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "cep_02", "regra": "cep", "entrada": {"papel": "autor", "texto": "13.010-111"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "cep_03", "regra": "cep", "entrada": {"papel": "autor", "texto": "13010111"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "cep_04", "regra": "cep", "entrada": {"papel": "autor", "texto": "13010-112"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "doc_01", "regra": "documento", "entrada": {"campo": "documento_autor", "texto": "12345678900"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "doc_02", "regra": "documento", "entrada": {"campo": "documento_autor", "texto": "123.456.789-00"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "doc_03", "regra": "documento", "entrada": {"campo": "documento_autor", "texto": "123.456.789-01"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "doc_04", "regra": "documento", "entrada": {"campo": "documento_reu", "texto": "11222333000180"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "doc_05", "regra": "documento", "entrada": {"campo": "documento_reu", "texto": "11.222.333/0001-80"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "doc_06", "regra": "documento", "entrada": {"campo": "documento_reu", "texto": "11.222.333/0001-90"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "doc_07", "regra": "documento", "entrada": {"campo": "numero_processo", "texto": "0001234-04.2026.8.26.0100"}, "esperado": "passa", "verificado_por": "regras", "nota": "a regra é a mesma em qualquer tipo; a inicial real não tem número"},
    {"id": "doc_08", "regra": "documento", "entrada": {"campo": "numero_processo", "texto": "00012340420268260100"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "doc_09", "regra": "documento", "entrada": {"campo": "numero_processo", "texto": "0001234-05.2026.8.26.0100"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "doc_10", "regra": "documento", "entrada": {"campo": "protocolo", "texto": "SINT-2026-000123"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "doc_11", "regra": "documento", "entrada": {"campo": "protocolo", "texto": "SINT 2026 000123"}, "esperado": "passa", "verificado_por": "regras", "nota": "sem pontuação os dois ficam SINT2026000123"},
    {"id": "doc_12", "regra": "documento", "entrada": {"campo": "protocolo", "texto": "SINT-2026-000124"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "nome_01", "regra": "nome", "entrada": {"papel": "autor", "texto": "Nome e Sobrenome da Parte Autora"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "nome_02", "regra": "nome", "entrada": {"papel": "autor", "texto": "Sr. Nome e Sobrenome da Parte Autora"}, "esperado": "passa", "verificado_por": "regras", "nota": "tratamento antes do marcador"},
    {"id": "nome_03", "regra": "nome", "entrada": {"papel": "autor", "texto": "NOME E SOBRENOME DA PARTE AUTORA"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "nome_04", "regra": "nome", "entrada": {"papel": "autor", "texto": "Nome e Sobrenome da Parte Ré"}, "esperado": "reprova", "verificado_por": "regras", "nota": "marcador de outro papel"},
    {"id": "nome_05", "regra": "nome", "entrada": {"papel": "reu", "texto": "Razão Social da Parte Ré"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "nome_06", "regra": "nome", "entrada": {"papel": "reu", "texto": "Razao Social da Parte Re"}, "esperado": "passa", "verificado_por": "regras", "nota": "sem acento"},
    {"id": "nome_07", "regra": "nome", "entrada": {"papel": "reu", "texto": "Razão Social da Parte Autora"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "nome_08", "regra": "nome", "entrada": {"papel": "reu", "texto": "Nome e Sobrenome da Parte Ré"}, "esperado": "reprova", "verificado_por": "regras", "nota": "marcador de outra categoria: a ré é empresa"},
    {"id": "nome_09", "regra": "nome", "entrada": {"papel": "advogado", "texto": "Dr. Nome e Sobrenome do Advogado"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "nome_10", "regra": "nome", "entrada": {"papel": "advogado", "texto": "Nome Diferente do Marcador"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "oab_01", "regra": "oab", "entrada": {"texto": "OAB/UF nº 000.000"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "oab_02", "regra": "oab", "entrada": {"texto": "oab/uf nº 000.000"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "oab_03", "regra": "oab", "entrada": {"texto": "OAB/SP nº 123.456"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "design_01", "regra": "designacao", "entrada": {"texto": "o autor"}, "esperado": "passa", "verificado_por": "regras", "nota": "designação não é nome e não é comparada"},
    {"id": "design_02", "regra": "designacao", "entrada": {"texto": "a requerida"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "juizo_01", "regra": "juizo", "entrada": {"comarca": "Campinas", "juizo": "Juizado Especial Cível da Comarca de Campinas"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "juizo_02", "regra": "juizo", "entrada": {"comarca": "Campinas", "juizo": "JEC de Campinas"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "juizo_03", "regra": "juizo", "entrada": {"comarca": "campinas", "juizo": "juizado especial civel da comarca de campinas"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "juizo_04", "regra": "juizo", "entrada": {"comarca": "Campinas", "juizo": "Juizado Especial Cível de Campinas"}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "juizo_05", "regra": "juizo", "entrada": {"comarca": "Jundiaí", "juizo": "Juizado Especial Cível da Comarca de Jundiaí"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "juizo_06", "regra": "juizo", "entrada": {"comarca": "Campinas", "juizo": "2ª Vara Cível da Comarca de Campinas"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "juizo_07", "regra": "juizo", "entrada": {"comarca": "Campinas", "juizo": "Vara da Fazenda Pública da Comarca de Campinas"}, "esperado": "reprova", "verificado_por": "regras"},
    {"id": "pedidos_01", "regra": "pedidos", "entrada": {"naturezas": ["danos_materiais", "danos_morais", "restituicao_simples", "exclusao_cadastro"], "outros": []}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "pedidos_02", "regra": "pedidos", "entrada": {"naturezas": ["citacao_reu", "danos_materiais", "danos_morais", "restituicao_simples", "exclusao_cadastro"], "outros": []}, "esperado": "passa", "verificado_por": "regras", "nota": "pedido acessório padrão do perfil"},
    {"id": "pedidos_03", "regra": "pedidos", "entrada": {"naturezas": ["citacao_reu", "producao_provas", "danos_materiais", "danos_morais", "restituicao_simples", "exclusao_cadastro"], "outros": []}, "esperado": "passa", "verificado_por": "regras"},
    {"id": "pedidos_04", "regra": "pedidos", "entrada": {"naturezas": ["danos_materiais", "danos_morais", "restituicao_simples"], "outros": []}, "esperado": "reprova", "verificado_por": "regras", "nota": "falta exclusao_cadastro"},
    {"id": "pedidos_05", "regra": "pedidos", "entrada": {"naturezas": ["danos_materiais", "danos_morais", "restituicao_simples", "exclusao_cadastro", "restituicao_em_dobro"], "outros": []}, "esperado": "reprova", "verificado_por": "regras", "nota": "pedido a mais fora da lista padrão"},
    {"id": "pedidos_06", "regra": "pedidos", "entrada": {"naturezas": ["danos_materiais", "danos_morais", "restituicao_simples", "exclusao_cadastro"], "outros": ["condenação da ré ao pagamento de honorários advocatícios"]}, "esperado": "reprova", "verificado_por": "regras", "nota": "qualquer pedido outro reprova"},
    {"id": "pedidos_07", "regra": "pedidos", "entrada": {"naturezas": ["danos_materiais", "danos_morais", "restituicao_simples", "exclusao_cadastro", "inversao_onus"], "outros": []}, "esperado": "reprova", "verificado_por": "regras", "nota": "inversão não está na ficha nem na lista padrão"},
    {"id": "ficha_01", "regra": "ficha_valor_legal", "entrada": {"centavos": 162100}, "esperado": "recusa_ficha", "verificado_por": "fichas", "nota": "valor da ficha igual ao salário mínimo"},
    {"id": "ficha_02", "regra": "ficha_valor_legal", "entrada": {"centavos": 6484000}, "esperado": "recusa_ficha", "verificado_por": "fichas", "nota": "valor da ficha igual à alçada"}
  ]
}
```

- Os números de documento e de processo da ficha de base têm dígito verificador inválido, de propósito: o CPF válido seria `-09`, o CNPJ válido seria `-81` e o número de processo válido teria `-03`. O executor não os troca.
- **Campos de que este brief depende**, já exigidos de `Extracao` no brief 003: `valores[]` com `texto`, `centavos`, `lugar` e `pedido`; `datas[]` com `texto` e `data` completa, parcial ou vazia; `documentos[]` com `tipo` (inclusive `cep`) e `texto`; `nomes[]` com `texto` e `papel`; `comarca`; `juizo`; `pedidos[]` com `natureza` e `texto`. O teste converte cada `entrada` do arquivo para esses campos. Se algum faltar em `formatos.py`, o brief 012 não começa: é defeito do brief 003, corrigido lá (por defeito comprovado, registro de decisão 001, item 19), e não pendência deste.
