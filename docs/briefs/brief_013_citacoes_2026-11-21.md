# Brief 013 — Citações de lei

- Fase: 6 — Preparação, travas e regras (PLANO §4)
- Objetivo: escrever `fabrica/conferencia/citacoes.py`, que encontra cada citação de lei no texto, inclusive as compostas, resolve cada uma em diploma, artigo e parágrafo (guardando inciso e alínea) e confere se está na tabela, com `testes/dados/citacoes_50.json` (conteúdo abaixo) e `testes/test_citacoes.py`.
- Seções a ler: AGENTS §4 ("peça só cita dispositivo da tabela de normas"); PLANO §4 (Fase 6); ARQUITETURA §2.2 (`tabela_normas.json`), §2.4 (`test_citacoes.py`), §5.6 (`citacoes.py`), §5.9 (citações no cartão), Anexo B.1 (`citacao_fora_da_tabela`) e Anexo C.1; registro de decisão 001 (item 12).
- Arquivos que pode criar:
  - `fabrica/conferencia/citacoes.py`;
  - `testes/dados/citacoes_50.json` (cópia literal do bloco abaixo);
  - `testes/test_citacoes.py`;
  - `docs/briefs/brief_013_citacoes_2026-11-21.md` (este brief);
  - `docs/docs/doc_013_citacoes_2026-11-21.md` (o relatório).
- Arquivos que pode alterar: `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `fabrica/comum/` (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `fabrica/conferencia/regras.py`; `dados/`; `config/`; `scripts/`; `AGENTS.md`; `docs/PLANO.md`; `docs/ARQUITETURA.md`.
- Teste de aceite (escrito antes do código):
  - `testes/dados/citacoes_50.json`, copiado literalmente deste brief antes de qualquer código;
  - `testes/test_citacoes.py`: as 50 formas do arquivo são resolvidas em 100%, cada uma exatamente na lista esperada, na ordem; e, com uma tabela de exemplo escrita no teste: citação resolvida que está na tabela passa; citação resolvida fora da tabela reprova `citacao_fora_da_tabela`; artigo sem diploma e sem expressão elíptica vira citação não resolvida, que gera alerta e pergunta ao checklist e não reprova sozinha; citação elíptica sem citação anterior no texto também vira não resolvida; a lista de todas as citações resolvidas sai para o cartão (020).
- Critério de conclusão: `test_citacoes.py` passa no gate, com as 50 formas resolvidas em 100% (critério da Fase 6 no PLANO, exigência da Fase 0 do plano). Com 011 e 012, fecha a Fase 6.
- Fora do escopo: a conferência do sentido do dispositivo (é o item `fundamento`, do conferente); a tabela de verdade (014); a etapa de conferência que chama `citacoes.py` (017); acórdãos (PLANO §2).
- Depende de: 012.

**Regras deste brief**

- `citacoes.py` recebe o texto e a tabela (com `diplomas[]` e as formas de escrita de cada diploma) por parâmetro. Não lê arquivo.
- Uma citação resolvida tem `diploma` (identificador da tabela), `artigo` (só os algarismos, sem ponto de milhar nem "º": "1.022" vira "1022", "8º" vira "8"), `paragrafo` (`caput`, `unico` ou o número em texto), `inciso` (algarismo romano ou vazio) e `alinea` (letra ou vazio), mais o trecho do texto e a posição. A conferência contra a tabela é no nível de artigo e parágrafo: inciso e alínea são guardados, para o cartão, e não mudam o resultado.
- Formas cobertas (ARQUITETURA §5.6): simples; com parte do artigo (parágrafo, inciso, "caput", "parágrafo único", inclusive com o parágrafo ou o inciso antes do artigo); múltipla ("arts. 186 e 927", "caput e § 3º", "§§ 1º e 2º", "VI e VIII", e artigos de diplomas diferentes na mesma frase); por intervalo ("arts. 319 a 321", "I a III"), que vira um item por artigo ou inciso do intervalo; e elíptica.
- Elíptica: as expressões "do mesmo diploma", "o mesmo diploma", "do mesmo código", "da mesma lei", "do referido código", "do referido diploma", "da referida lei", "daquele código", "daquele diploma" e "daquela lei" valem o diploma da última citação resolvida antes no texto; "do mesmo artigo" e "do mesmo dispositivo" valem o último artigo resolvido. "ambos do <diploma>" dá o diploma a todos os artigos do grupo.
- Artigo citado sem diploma e sem expressão elíptica não é adivinhado: vira citação não resolvida.
- Nos números por extenso de artigo ("artigo quinto"), a citação também vira não resolvida; o conjunto de 50 não os usa.

**Conteúdo literal de `testes/dados/citacoes_50.json`:**

```json
{
  "versao": "2026-11-21-v2",
  "descricao": "Cinquenta formas de citação de lei, com a resolução esperada de cada uma. A resolução é no nível de artigo e parágrafo, com inciso e alínea guardados.",
  "diplomas": [
    {"id": "cpc", "nome": "Código de Processo Civil", "formas": ["CPC", "CPC/2015", "NCPC", "Novo Código de Processo Civil", "Código de Processo Civil", "Lei 13.105/2015", "Lei nº 13.105/2015", "Lei n. 13.105/2015", "Lei nº 13.105, de 16 de março de 2015"]},
    {"id": "cdc", "nome": "Código de Defesa do Consumidor", "formas": ["CDC", "Código de Defesa do Consumidor", "Lei 8.078/1990", "Lei nº 8.078/1990", "Lei nº 8.078/90", "Lei 8078/90"]},
    {"id": "cc", "nome": "Código Civil", "formas": ["CC", "CC/2002", "Código Civil", "Lei 10.406/2002", "Lei nº 10.406/2002"]},
    {"id": "lei_9099_1995", "nome": "Lei dos Juizados Especiais Cíveis e Criminais", "formas": ["Lei 9.099/1995", "Lei nº 9.099/1995", "Lei nº 9.099/95", "Lei 9.099/95", "Lei 9099/95", "Lei dos Juizados Especiais", "Lei nº 9.099, de 26 de setembro de 1995"]},
    {"id": "cf", "nome": "Constituição Federal", "formas": ["CF", "CF/88", "CF/1988", "Constituição Federal", "Constituição da República"]}
  ],
  "casos": [
    {"id": 1, "forma": "simples", "texto": "nos termos do art. 319 do CPC", "esperado": [{"diploma": "cpc", "artigo": "319", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 2, "forma": "simples", "texto": "conforme o artigo 6º do Código de Defesa do Consumidor", "esperado": [{"diploma": "cdc", "artigo": "6", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 3, "forma": "simples", "texto": "na forma do art. 186 do Código Civil", "esperado": [{"diploma": "cc", "artigo": "186", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 4, "forma": "simples", "texto": "como prevê o art. 3º da Lei 9.099/1995", "esperado": [{"diploma": "lei_9099_1995", "artigo": "3", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 5, "forma": "simples", "texto": "garantia do art. 5º da Constituição Federal", "esperado": [{"diploma": "cf", "artigo": "5", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 6, "forma": "simples", "texto": "o art. 1.022 do Código de Processo Civil", "esperado": [{"diploma": "cpc", "artigo": "1022", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 7, "forma": "simples", "texto": "com base no art. 1022 do CPC", "esperado": [{"diploma": "cpc", "artigo": "1022", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 8, "forma": "simples", "texto": "responde nos termos do artigo 14 do CDC", "esperado": [{"diploma": "cdc", "artigo": "14", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 9, "forma": "simples", "texto": "dever de indenizar do art. 927 do CC/2002", "esperado": [{"diploma": "cc", "artigo": "927", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 10, "forma": "simples", "texto": "na forma do art. 18 da Lei nº 9.099/95", "esperado": [{"diploma": "lei_9099_1995", "artigo": "18", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 11, "forma": "simples", "texto": "contagem do prazo (CPC, art. 224)", "esperado": [{"diploma": "cpc", "artigo": "224", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 12, "forma": "simples", "texto": "legitimidade ativa (Lei 9099/95, art. 8º)", "esperado": [{"diploma": "lei_9099_1995", "artigo": "8", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 13, "forma": "simples", "texto": "citação pelo correio, art. 249 da Lei nº 13.105/2015", "esperado": [{"diploma": "cpc", "artigo": "249", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 14, "forma": "simples", "texto": "repetição do indébito do art. 42 da Lei nº 8.078/90", "esperado": [{"diploma": "cdc", "artigo": "42", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 15, "forma": "parte_do_artigo", "texto": "valor da causa do art. 292, VI, do CPC", "esperado": [{"diploma": "cpc", "artigo": "292", "paragrafo": "caput", "inciso": "VI", "alinea": null}]},
    {"id": 16, "forma": "parte_do_artigo", "texto": "na ação indenizatória, art. 292, inciso V, do CPC", "esperado": [{"diploma": "cpc", "artigo": "292", "paragrafo": "caput", "inciso": "V", "alinea": null}]},
    {"id": 17, "forma": "parte_do_artigo", "texto": "violação do art. 489, § 1º, IV, do CPC", "esperado": [{"diploma": "cpc", "artigo": "489", "paragrafo": "1", "inciso": "IV", "alinea": null}]},
    {"id": 18, "forma": "parte_do_artigo", "texto": "omissão do art. 1.022, parágrafo único, II, do CPC", "esperado": [{"diploma": "cpc", "artigo": "1022", "paragrafo": "unico", "inciso": "II", "alinea": null}]},
    {"id": 19, "forma": "parte_do_artigo", "texto": "matérias excluídas pelo art. 3º, § 2º, da Lei 9.099/95", "esperado": [{"diploma": "lei_9099_1995", "artigo": "3", "paragrafo": "2", "inciso": null, "alinea": null}]},
    {"id": 20, "forma": "parte_do_artigo", "texto": "não podem ser partes, art. 8º, caput, da Lei 9.099/1995", "esperado": [{"diploma": "lei_9099_1995", "artigo": "8", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 21, "forma": "parte_do_artigo", "texto": "inversão do ônus da prova, art. 6º, VIII, do CDC", "esperado": [{"diploma": "cdc", "artigo": "6", "paragrafo": "caput", "inciso": "VIII", "alinea": null}]},
    {"id": 22, "forma": "parte_do_artigo", "texto": "em dobro, art. 42, parágrafo único, do Código de Defesa do Consumidor", "esperado": [{"diploma": "cdc", "artigo": "42", "paragrafo": "unico", "inciso": null, "alinea": null}]},
    {"id": 23, "forma": "parte_do_artigo", "texto": "prazo supletivo do § 3º do art. 218 do CPC", "esperado": [{"diploma": "cpc", "artigo": "218", "paragrafo": "3", "inciso": null, "alinea": null}]},
    {"id": 24, "forma": "parte_do_artigo", "texto": "nos termos do parágrafo único do art. 1.022 do CPC", "esperado": [{"diploma": "cpc", "artigo": "1022", "paragrafo": "unico", "inciso": null, "alinea": null}]},
    {"id": 25, "forma": "parte_do_artigo", "texto": "o inciso VIII do art. 6º do CDC", "esperado": [{"diploma": "cdc", "artigo": "6", "paragrafo": "caput", "inciso": "VIII", "alinea": null}]},
    {"id": 26, "forma": "parte_do_artigo", "texto": "acesso à justiça, art. 5º, inciso XXXV, da Constituição Federal", "esperado": [{"diploma": "cf", "artigo": "5", "paragrafo": "caput", "inciso": "XXXV", "alinea": null}]},
    {"id": 27, "forma": "parte_do_artigo", "texto": "intimação do embargado, art. 1.023, § 2º, do CPC", "esperado": [{"diploma": "cpc", "artigo": "1023", "paragrafo": "2", "inciso": null, "alinea": null}]},
    {"id": 28, "forma": "parte_do_artigo", "texto": "qualificação das partes, art. 319, II, do Novo Código de Processo Civil", "esperado": [{"diploma": "cpc", "artigo": "319", "paragrafo": "caput", "inciso": "II", "alinea": null}]},
    {"id": 29, "forma": "parte_do_artigo", "texto": "excludente do art. 14, § 3º, I, do CDC", "esperado": [{"diploma": "cdc", "artigo": "14", "paragrafo": "3", "inciso": "I", "alinea": null}]},
    {"id": 30, "forma": "multipla", "texto": "responsabilidade dos arts. 186 e 927 do Código Civil", "esperado": [{"diploma": "cc", "artigo": "186", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cc", "artigo": "927", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 31, "forma": "multipla", "texto": "arts. 186, 187 e 927 do CC", "esperado": [{"diploma": "cc", "artigo": "186", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cc", "artigo": "187", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cc", "artigo": "927", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 32, "forma": "multipla", "texto": "art. 14, caput e § 3º, do CDC", "esperado": [{"diploma": "cdc", "artigo": "14", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cdc", "artigo": "14", "paragrafo": "3", "inciso": null, "alinea": null}]},
    {"id": 33, "forma": "multipla", "texto": "art. 18, §§ 1º e 2º, da Lei 9.099/1995", "esperado": [{"diploma": "lei_9099_1995", "artigo": "18", "paragrafo": "1", "inciso": null, "alinea": null}, {"diploma": "lei_9099_1995", "artigo": "18", "paragrafo": "2", "inciso": null, "alinea": null}]},
    {"id": 34, "forma": "multipla", "texto": "arts. 3º, I, e 8º, § 1º, da Lei 9.099/1995", "esperado": [{"diploma": "lei_9099_1995", "artigo": "3", "paragrafo": "caput", "inciso": "I", "alinea": null}, {"diploma": "lei_9099_1995", "artigo": "8", "paragrafo": "1", "inciso": null, "alinea": null}]},
    {"id": 35, "forma": "multipla", "texto": "direitos básicos do art. 6º, VI e VIII, do CDC", "esperado": [{"diploma": "cdc", "artigo": "6", "paragrafo": "caput", "inciso": "VI", "alinea": null}, {"diploma": "cdc", "artigo": "6", "paragrafo": "caput", "inciso": "VIII", "alinea": null}]},
    {"id": 36, "forma": "multipla", "texto": "conforme o art. 14 do CDC e o art. 186 do Código Civil", "esperado": [{"diploma": "cdc", "artigo": "14", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cc", "artigo": "186", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 37, "forma": "multipla", "texto": "cabimento e prazo, arts. 1.022 e 1.023 do CPC", "esperado": [{"diploma": "cpc", "artigo": "1022", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cpc", "artigo": "1023", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 38, "forma": "multipla", "texto": "art. 1.022, II, e art. 1.023, § 2º, ambos do CPC", "esperado": [{"diploma": "cpc", "artigo": "1022", "paragrafo": "caput", "inciso": "II", "alinea": null}, {"diploma": "cpc", "artigo": "1023", "paragrafo": "2", "inciso": null, "alinea": null}]},
    {"id": 39, "forma": "intervalo", "texto": "requisitos dos arts. 319 a 321 do CPC", "esperado": [{"diploma": "cpc", "artigo": "319", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cpc", "artigo": "320", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cpc", "artigo": "321", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 40, "forma": "intervalo", "texto": "disciplina dos arts. 1.022 a 1.026 do CPC", "esperado": [{"diploma": "cpc", "artigo": "1022", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cpc", "artigo": "1023", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cpc", "artigo": "1024", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cpc", "artigo": "1025", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cpc", "artigo": "1026", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 41, "forma": "intervalo", "texto": "hipóteses do art. 1.022, I a III, do CPC", "esperado": [{"diploma": "cpc", "artigo": "1022", "paragrafo": "caput", "inciso": "I", "alinea": null}, {"diploma": "cpc", "artigo": "1022", "paragrafo": "caput", "inciso": "II", "alinea": null}, {"diploma": "cpc", "artigo": "1022", "paragrafo": "caput", "inciso": "III", "alinea": null}]},
    {"id": 42, "forma": "intervalo", "texto": "atos ilícitos, arts. 186 a 188 do Código Civil", "esperado": [{"diploma": "cc", "artigo": "186", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cc", "artigo": "187", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cc", "artigo": "188", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 43, "forma": "intervalo", "texto": "meios de citação do art. 18, I a III, da Lei 9.099/95", "esperado": [{"diploma": "lei_9099_1995", "artigo": "18", "paragrafo": "caput", "inciso": "I", "alinea": null}, {"diploma": "lei_9099_1995", "artigo": "18", "paragrafo": "caput", "inciso": "II", "alinea": null}, {"diploma": "lei_9099_1995", "artigo": "18", "paragrafo": "caput", "inciso": "III", "alinea": null}]},
    {"id": 44, "forma": "eliptica", "texto": "cabem embargos pelo art. 1.022 do CPC. O mesmo diploma, no art. 1.023, fixa o prazo de cinco dias.", "esperado": [{"diploma": "cpc", "artigo": "1022", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cpc", "artigo": "1023", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 45, "forma": "eliptica", "texto": "art. 6º, VIII, do CDC e art. 14 do mesmo código", "esperado": [{"diploma": "cdc", "artigo": "6", "paragrafo": "caput", "inciso": "VIII", "alinea": null}, {"diploma": "cdc", "artigo": "14", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 46, "forma": "eliptica", "texto": "art. 3º da Lei 9.099/95 e art. 8º da mesma lei; o art. 9º daquela lei trata da assistência", "esperado": [{"diploma": "lei_9099_1995", "artigo": "3", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "lei_9099_1995", "artigo": "8", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "lei_9099_1995", "artigo": "9", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 47, "forma": "eliptica", "texto": "a inicial atende ao art. 319 do CPC; o art. 320 do referido código exige os documentos indispensáveis, e o art. 321 do referido diploma manda emendar", "esperado": [{"diploma": "cpc", "artigo": "319", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cpc", "artigo": "320", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cpc", "artigo": "321", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 48, "forma": "eliptica", "texto": "art. 18 da Lei 9.099/1995 e art. 19 da referida lei", "esperado": [{"diploma": "lei_9099_1995", "artigo": "18", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "lei_9099_1995", "artigo": "19", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 49, "forma": "eliptica", "texto": "art. 186 do Código Civil e art. 927 do mesmo diploma, além do art. 188 daquele código e do art. 187 daquele diploma", "esperado": [{"diploma": "cc", "artigo": "186", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cc", "artigo": "927", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cc", "artigo": "188", "paragrafo": "caput", "inciso": null, "alinea": null}, {"diploma": "cc", "artigo": "187", "paragrafo": "caput", "inciso": null, "alinea": null}]},
    {"id": 50, "forma": "eliptica", "texto": "art. 489, § 1º, IV, do CPC e § 3º do mesmo artigo; o § 2º do mesmo dispositivo trata da colisão de normas", "esperado": [{"diploma": "cpc", "artigo": "489", "paragrafo": "1", "inciso": "IV", "alinea": null}, {"diploma": "cpc", "artigo": "489", "paragrafo": "3", "inciso": null, "alinea": null}, {"diploma": "cpc", "artigo": "489", "paragrafo": "2", "inciso": null, "alinea": null}]}
  ]
}
```

- As 50 formas se dividem em 14 simples, 15 com parte do artigo, 9 múltiplas, 5 por intervalo e 7 elípticas. O teste confere também essa contagem, para que nenhum caso seja apagado sem aviso.
- Versão 2: os casos elípticos 46, 47, 49 e 50 passaram a cobrir também "daquela lei", "do referido diploma", "daquele código", "daquele diploma" e "do mesmo dispositivo", e o caso 28 cobre "Novo Código de Processo Civil", sem mudar o total de 50. Quando duas formas de diploma se sobrepõem ("Novo Código de Processo Civil" contém "Código de Processo Civil"), vale a mais longa.
- O Código de Processo Civil de 1973 ("CPC/73") está revogado e não entra na tabela: uma citação a ele fica não resolvida, vira alerta e pergunta ao checklist, que é o comportamento certo.
