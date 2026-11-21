# Relatório do brief 014 — Dados dos três tipos

- Data: 2026-11-21
- Brief: `docs/briefs/brief_014_dados_dos_tres_tipos_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21, com a aprovação antecipada do responsável** (ver "## Aprovação do responsável"). Os textos de lei propostos ficam marcados "a conferir na fonte" e são pendência antes do ensaio (brief 024).

## RELATÓRIO FINAL

- Brief executado: 014 — Dados dos três tipos (Fase 7).

- Arquivos criados (todos propostos; nenhum código):
  - `docs/briefs/brief_014_dados_dos_tres_tipos_2026-11-21.md` — o brief, literal;
  - `dados/catalogo/tipos.json` — os 3 tipos do MVP;
  - `dados/estruturas/familias/peticao_inicial.json`, `recurso.json`, `peticao_intermediaria.json` — as 3 famílias;
  - `dados/estruturas/perfis/inicial_juizado_especial_civel.json`, `recurso_primeiro_grau.json`, `intermediaria_processo_em_curso.json` — os 3 perfis;
  - `dados/estruturas/acrescimos/peticao_inicial_jec.json`, `embargos_declaracao.json`, `manifestacao_ar_negativo.json` — os acréscimos de cada tipo;
  - `dados/matrizes/peticao_inicial_jec.json`, `embargos_declaracao.json`, `manifestacao_ar_negativo.json` — as matrizes, com 5 matérias e 2 ou 3 teses cada;
  - `dados/normas/tabela_normas.json` — 56 dispositivos (CPC 26, Lei 9.099/1995 13, CDC 11, CC 6) e 5 diplomas com as formas de escrita;
  - `dados/travas/travas.json` — 15 travas do Anexo A.5;
  - `dados/conferencia/lista_conferencia.json`, `termos_inequivocos.json`, `palavras_ignoradas.json`, `feriados_nacionais.json`;
  - `dados/erros/catalogo_erros.json` — os 19 tipos de erro do Anexo C;
  - `dados/ficticios/listas_ficticias.json`, `reais_permitidos.json` (259 nomes), `reais_proibidos.json` (129 nomes);
  - `docs/docs/doc_014_dados_dos_tres_tipos_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `docs/PLAN.md` — Resumo; 014 do Backlog para o Done; hash do 013 no Done.

- Arquivos preservados literalmente na área afetada: `fabrica/`, `testes/`, `config/`, `instrucoes/`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`.

- Testes rodados e resultado (com a saída colada):

  Este brief não tem código; o aceite é `preparar` sem erro e o gate verde. Saída de `python -m fabrica preparar` (sem chave de API, sem chamada a modelo):

  ```text
  Arquivos fixos de `dados/` lidos no formato: 11 de 11.
  Todo dispositivo citado em travas.json está na tabela.
  nomes reservados em reais_proibidos.json: 0
  Estrutura: 11 blocos, gravada em `saida/preparacao/peticao_inicial_jec_estrutura.json` e `.md`.
  Sorteio de prova: 10 combinações em 1 tentativa(s).
  Combinação do ensaio: {"materia": "negativacao_indevida", "tese": "inscrição em cadastro de inadimplentes por dívida inexistente", "polo": "autor", "complexidade": "media", "momento": "antes_da_citacao", "estilo": "detalhado"}.
  Trecho da tabela: 33 dispositivos, cerca de 3850 tokens; 27 dispositivo(s) com par (mesmo diploma, mesmo assunto, função diferente).
  Estrutura: 9 blocos, gravada em `saida/preparacao/embargos_declaracao_estrutura.json` e `.md`.
  Sorteio de prova: 10 combinações em 1 tentativa(s).
  Combinação do ensaio: {"materia": "vicio_produto", "tese": "vício do produto não sanado no prazo de trinta dias", "polo": "reu", "complexidade": "media", "momento": "depois_da_decisao_embargada", "estilo": "detalhado"}.
  Trecho da tabela: 28 dispositivos, cerca de 3151 tokens; 23 dispositivo(s) com par (mesmo diploma, mesmo assunto, função diferente).
  Estrutura: 6 blocos, gravada em `saida/preparacao/manifestacao_ar_negativo_estrutura.json` e `.md`.
  Sorteio de prova: 10 combinações em 1 tentativa(s).
  Combinação do ensaio: {"materia": "vicio_produto", "tese": "vício do produto não sanado no prazo de trinta dias", "polo": "autor", "complexidade": "media", "momento": "depois_da_juntada_do_aviso", "estilo": "detalhado"}.
  Trecho da tabela: 12 dispositivos, cerca de 1306 tokens; 11 dispositivo(s) com par (mesmo diploma, mesmo assunto, função diferente).
  resumo em saida/preparacao/resumo.md
  ```

  Gate (`scripts/verificar.sh`), que inclui `test_dados_reais.py` conferindo agora também `dados/`:

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  75 files already formatted
  == mypy fabrica
  Success: no issues found in 21 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 1005 items

  testes/test_api_claude.py ...............................                [  3%]
  testes/test_arquivos.py ..................                               [  4%]
  testes/test_citacoes.py ................................................ [  9%]
  ............                                                             [ 10%]
  testes/test_comparacao.py .............................................. [ 15%]
  ...........................................                              [ 19%]
  testes/test_config.py .................................................. [ 24%]
  ........................................................................ [ 31%]
  ........................................................................ [ 39%]
  ...............................................................          [ 45%]
  testes/test_congelamento.py .................                            [ 46%]
  testes/test_dados_reais.py ..........................................    [ 51%]
  testes/test_entrega.py .................................                 [ 54%]
  testes/test_estado.py ........................................           [ 58%]
  testes/test_estatistica.py ..........                                    [ 59%]
  testes/test_ficticios.py ..........................                      [ 61%]
  testes/test_formatos.py ................................................ [ 66%]
  ........................................................................ [ 73%]
  ........................................................................ [ 81%]
  ......................................................................   [ 88%]
  testes/test_gasto.py ..............                                      [ 89%]
  testes/test_modelo_local.py ..........................                   [ 92%]
  testes/test_registro.py ...                                              [ 92%]
  testes/test_regras.py .......................                            [ 94%]
  testes/test_travas.py .................................................. [ 99%]
  ....                                                                     [100%]

  ============================ 1005 passed in 13.99s =============================
  saída=0
  ```

- Comandos executados: um script de uma vez, fora do repositório, que escreveu os arquivos de `dados/` e conferiu, com a mesma normalização do teste, que nenhuma forma reservada aparece neles (resultado: 0; 6 candidatos a reais proibidos foram tirados por coincidirem com nomes reservados, e o relatório só dá a contagem); `python -m fabrica preparar`; `scripts/verificar.sh`; `scripts/entregar.sh 014`. Nenhuma chamada a modelo.

## Roteiro de aprovação

Na ordem do brief. Para cada arquivo: o que contém, o que conferir, e a caixa.

### 1. Tabela de normas e travas

- `dados/normas/tabela_normas.json` — os dispositivos de que os 3 tipos precisam, com texto, função, assunto, tipos e fonte.
  - Conferir: texto igual ao da fonte oficial; função de cada dispositivo; os 56 marcados "a conferir na fonte".
  - [ ] aprovado  [ ] devolver — motivo:
- `dados/travas/travas.json` — 15 travas (proíbe ou exige), cada uma com base legal e dispositivos da tabela.
  - Conferir: se cada uma proíbe o que a lei proíbe; se as listas de categorias e de matérias excluídas estão certas.
  - [ ] aprovado  [ ] devolver — motivo:

### 2. Catálogo, estruturas e estrutura montada

- `dados/catalogo/tipos.json` — rótulo, família, perfil, risco, quantidade (10) e itens de conferência de cada tipo.
  - Conferir: classe de risco (inicial médio, embargos alto, manifestação baixo) e itens que se aplicam a cada tipo.
  - [ ] aprovado  [ ] devolver — motivo:
- `dados/estruturas/` (famílias, perfis e acréscimos) e a estrutura montada de cada tipo, que `preparar` grava em `saida/preparacao/<tipo>_estrutura.md` na sua máquina (inicial 11 blocos, embargos 9, manifestação 6).
  - Conferir: blocos, títulos, ordem e quais são obrigatórios.
  - [ ] aprovado  [ ] devolver — motivo:

### 3. Matrizes e teses

- `dados/matrizes/*.json` — 5 matérias (negativação indevida, voo atrasado ou cancelado, vício do produto, cobrança indevida de telefonia ou internet, falha de serviço bancário), cada uma com 2 ou 3 teses; teto de 2 por matéria.
  - Conferir: se as teses são plausíveis; contagens do Anexo A.6 (embargos: polo 5/5, defeitos 2/3/2/2/1, sentença 7 e interlocutória 3; manifestação: rito 5/5; complexidade e estilo 5/5 em todos).
  - [ ] aprovado  [ ] devolver — motivo:

### 4. Conferência

- `dados/conferencia/lista_conferencia.json` — os itens do Anexo B (programa e modelos), com pergunta, quem confere, se é eliminatório e tipos.
- `dados/conferencia/termos_inequivocos.json` — os 3 termos do plano, com motivo e norma de hoje (arts. 183, 64 e 330, § 1º, do CPC). Nenhum outro termo entrou.
- `dados/conferencia/palavras_ignoradas.json` — as duas listas do Anexo E.2.
- `dados/conferencia/feriados_nacionais.json` — 11 dias de 2026, cada um com a lei (ver as perguntas abaixo).
  - Conferir: perguntas da lista; os termos; os feriados.
  - [ ] aprovado  [ ] devolver — motivo:

### 5. Catálogo de erros

- `dados/erros/catalogo_erros.json` — os 19 tipos do Anexo C (8 do programa por regra, 1 do programa por julgamento, 10 do Opus), com item principal e itens aceitos.
  - Conferir: se cada erro bate com o item que deve pegá-lo.
  - [ ] aprovado  [ ] devolver — motivo:

### 6. Listas fictícias e reais

- `dados/ficticios/listas_ficticias.json` — ruas e bairros com "Fictícia", "Inventada" ou "Imaginário" no nome; 12 cidades reais com faixa de CEP, juizado e varas; profissões; estados civis; os 27 códigos de tribunal estadual do número CNJ; pedidos incompatíveis por tipo e rito.
  - Conferir: faixas de CEP (propostas de memória, a conferir); códigos de tribunal.
  - [ ] aprovado  [ ] devolver — motivo:
- `dados/ficticios/reais_permitidos.json` — tribunais, juizados, varas, comarcas, estados, entes públicos, sistemas, órgãos e siglas, leis, cargos, tratamentos, latim e designações processuais.
- `dados/ficticios/reais_proibidos.json` — bancos, companhias aéreas, telefonia e internet, varejo, seguros e saúde, pagamento e crédito, e outras empresas reais.
  - Conferir: se falta algum nome que costuma aparecer em processos; se algum permitido deveria ser proibido.
  - [ ] aprovado  [ ] devolver — motivo:

## Textos "a conferir na fonte"

A sessão não conseguiu abrir o portal do Planalto (a conexão volta vazia deste ambiente). Por isso, todos os 56 textos foram propostos de memória e cada um tem em `fonte` o endereço da página mais "(a conferir na fonte)". Nenhum é dado como conferido. Dispositivos, um por um:

- `cpc_art291` (cpc, art. 291, caput; requisito; peticao_inicial_jec)
- `cpc_art292` (cpc, art. 292, caput; definicao; peticao_inicial_jec)
- `cpc_art300` (cpc, art. 300, caput; requisito; peticao_inicial_jec)
- `cpc_art319` (cpc, art. 319, caput; requisito; peticao_inicial_jec, manifestacao_ar_negativo)
- `cpc_art320` (cpc, art. 320, caput; requisito; peticao_inicial_jec)
- `cpc_art321` (cpc, art. 321, caput; consequencia; peticao_inicial_jec)
- `cpc_art330_p1` (cpc, art. 330, § 1º; definicao; nenhum tipo (só citado em termos inequívocos ou travas))
- `cpc_art64` (cpc, art. 64, caput; requisito; nenhum tipo (só citado em termos inequívocos ou travas))
- `cpc_art183` (cpc, art. 183, caput; prazo; nenhum tipo (só citado em termos inequívocos ou travas))
- `cpc_art218_p3` (cpc, art. 218, § 3º; prazo; manifestacao_ar_negativo)
- `cpc_art219` (cpc, art. 219, caput; definicao; embargos_declaracao, manifestacao_ar_negativo)
- `cpc_art224` (cpc, art. 224, caput; definicao; embargos_declaracao, manifestacao_ar_negativo)
- `cpc_art231` (cpc, art. 231, caput; prazo; manifestacao_ar_negativo)
- `cpc_art246` (cpc, art. 246, caput; definicao; manifestacao_ar_negativo)
- `cpc_art247` (cpc, art. 247, caput; requisito; manifestacao_ar_negativo)
- `cpc_art248` (cpc, art. 248, caput; requisito; manifestacao_ar_negativo)
- `cpc_art249` (cpc, art. 249, caput; excecao; manifestacao_ar_negativo)
- `cpc_art489` (cpc, art. 489, caput; requisito; embargos_declaracao)
- `cpc_art489_p1` (cpc, art. 489, § 1º; definicao; embargos_declaracao)
- `cpc_art494` (cpc, art. 494, caput; excecao; embargos_declaracao)
- `cpc_art1022` (cpc, art. 1.022, caput; requisito; embargos_declaracao)
- `cpc_art1022_pu` (cpc, art. 1.022, parágrafo único; definicao; embargos_declaracao)
- `cpc_art1023` (cpc, art. 1.023, caput; prazo; embargos_declaracao)
- `cpc_art1023_p2` (cpc, art. 1.023, § 2º; consequencia; embargos_declaracao)
- `cpc_art1024` (cpc, art. 1.024, caput; prazo; embargos_declaracao)
- `cpc_art1026` (cpc, art. 1.026, caput; consequencia; embargos_declaracao)
- `cdc_art2` (cdc, art. 2º, caput; definicao; peticao_inicial_jec, embargos_declaracao)
- `cdc_art3` (cdc, art. 3º, caput; definicao; peticao_inicial_jec, embargos_declaracao)
- `cdc_art6` (cdc, art. 6º, caput; requisito; peticao_inicial_jec, embargos_declaracao)
- `cdc_art14` (cdc, art. 14, caput; consequencia; peticao_inicial_jec, embargos_declaracao)
- `cdc_art14_p3` (cdc, art. 14, § 3º; excecao; peticao_inicial_jec, embargos_declaracao)
- `cdc_art18` (cdc, art. 18, caput; consequencia; peticao_inicial_jec, embargos_declaracao)
- `cdc_art18_p1` (cdc, art. 18, § 1º; prazo; peticao_inicial_jec, embargos_declaracao)
- `cdc_art42` (cdc, art. 42, caput; requisito; peticao_inicial_jec, embargos_declaracao)
- `cdc_art42_pu` (cdc, art. 42, parágrafo único; consequencia; peticao_inicial_jec, embargos_declaracao)
- `cdc_art43` (cdc, art. 43, caput; definicao; peticao_inicial_jec, embargos_declaracao)
- `cdc_art43_p2` (cdc, art. 43, § 2º; requisito; peticao_inicial_jec, embargos_declaracao)
- `cc_art186` (cc, art. 186, caput; definicao; peticao_inicial_jec, embargos_declaracao)
- `cc_art187` (cc, art. 187, caput; definicao; peticao_inicial_jec, embargos_declaracao)
- `cc_art927` (cc, art. 927, caput; consequencia; peticao_inicial_jec, embargos_declaracao)
- `cc_art944` (cc, art. 944, caput; consequencia; peticao_inicial_jec, embargos_declaracao)
- `cc_art734` (cc, art. 734, caput; consequencia; peticao_inicial_jec, embargos_declaracao)
- `cc_art737` (cc, art. 737, caput; requisito; peticao_inicial_jec, embargos_declaracao)
- `lei_9099_1995_art3` (lei_9099_1995, art. 3º, caput; competencia; peticao_inicial_jec)
- `lei_9099_1995_art3_p2` (lei_9099_1995, art. 3º, § 2º; excecao; peticao_inicial_jec)
- `lei_9099_1995_art3_p3` (lei_9099_1995, art. 3º, § 3º; consequencia; peticao_inicial_jec)
- `lei_9099_1995_art8` (lei_9099_1995, art. 8º, caput; excecao; peticao_inicial_jec)
- `lei_9099_1995_art8_p1` (lei_9099_1995, art. 8º, § 1º; requisito; peticao_inicial_jec)
- `lei_9099_1995_art9` (lei_9099_1995, art. 9º, caput; requisito; peticao_inicial_jec)
- `lei_9099_1995_art14` (lei_9099_1995, art. 14, caput; definicao; peticao_inicial_jec)
- `lei_9099_1995_art14_p1` (lei_9099_1995, art. 14, § 1º; requisito; peticao_inicial_jec)
- `lei_9099_1995_art18` (lei_9099_1995, art. 18, caput; requisito; manifestacao_ar_negativo)
- `lei_9099_1995_art18_p2` (lei_9099_1995, art. 18, § 2º; excecao; peticao_inicial_jec, manifestacao_ar_negativo)
- `lei_9099_1995_art19` (lei_9099_1995, art. 19, caput; definicao; manifestacao_ar_negativo)
- `lei_9099_1995_art48` (lei_9099_1995, art. 48, caput; requisito; nenhum tipo (só citado em termos inequívocos ou travas))
- `lei_9099_1995_art55` (lei_9099_1995, art. 55, caput; consequencia; peticao_inicial_jec)

Dispositivos com par (mesmo diploma, mesmo assunto, função diferente), pela saída de `preparar`: inicial 27 de 33; embargos 23 de 28; manifestação 11 de 12.

## Perguntas ao responsável

1. **Carnaval, Sexta-feira da Paixão e Corpus Christi** não são feriado nacional por lei federal e ficaram fora da lista. Algum deve contar?
2. **Dias de eleição** (4 e 25 de outubro de 2026, art. 380 do Código Eleitoral) entraram como feriado. Ficam?
3. **Recesso do art. 220 do CPC** (prazos suspensos de 20 de dezembro a 20 de janeiro): a contagem de prazo de hoje não o trata. As datas sorteadas devem evitar esse período?

## Aprovação do responsável

- 2026-11-21: o responsável escreveu, antes da execução: "Aprovo pode seguir até o fim de todos os briefs sem mais aprovação futuras". Com isso, os arquivos de `dados/` propostos aqui ficam aprovados para seguir aos briefs 015 a 023 (decisão tomada por falta de resposta arquivo por arquivo).
- Continuam pendentes antes do ensaio (024): a conferência dos 56 textos de lei na fonte oficial, as faixas de CEP e as 3 perguntas acima. O roteiro acima fica para essa conferência.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_014_dados_dos_tres_tipos_2026-11-21.md
dados/catalogo/tipos.json
dados/estruturas/familias/peticao_inicial.json
dados/estruturas/familias/recurso.json
dados/estruturas/familias/peticao_intermediaria.json
dados/estruturas/perfis/inicial_juizado_especial_civel.json
dados/estruturas/perfis/recurso_primeiro_grau.json
dados/estruturas/perfis/intermediaria_processo_em_curso.json
dados/estruturas/acrescimos/peticao_inicial_jec.json
dados/estruturas/acrescimos/embargos_declaracao.json
dados/estruturas/acrescimos/manifestacao_ar_negativo.json
dados/matrizes/peticao_inicial_jec.json
dados/matrizes/embargos_declaracao.json
dados/matrizes/manifestacao_ar_negativo.json
dados/normas/tabela_normas.json
dados/travas/travas.json
dados/conferencia/lista_conferencia.json
dados/conferencia/termos_inequivocos.json
dados/conferencia/palavras_ignoradas.json
dados/conferencia/feriados_nacionais.json
dados/erros/catalogo_erros.json
dados/ficticios/listas_ficticias.json
dados/ficticios/reais_permitidos.json
dados/ficticios/reais_proibidos.json
docs/docs/doc_014_dados_dos_tres_tipos_2026-11-21.md
docs/PLAN.md

Brief 014: dados dos três tipos

Proposta de todos os arquivos de dados/ dos três tipos do MVP: catálogo,
estruturas, matrizes, tabela de normas, travas, conferência, erros e listas.
preparar sai sem erro e o gate fica verde. Os textos de lei ficam marcados
"a conferir na fonte"; aprovação antecipada do responsável registrada.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **`preparar` não roda duas vezes seguidas:** na segunda vez, para com "saida/preparacao/...: já existe; nunca se sobrescreve" (regra de `arquivos.py`). Este brief não pode mexer em `fabrica/`. Até a correção (sugestão: gravar a preparação numa pasta com data e hora, como manda "cada versão tem caminho próprio"), apague `saida/preparacao/` antes de rodar de novo. Fica para o brief 023 ou para uma correção do 011.
  2. **Textos de lei de memória**, todos "a conferir na fonte" (acima).
  3. **Itens de conferência por tipo:** todos os itens do programa e os comuns entram nos 3 tipos; `alcada` só na inicial; `prazo` e `pecas_anteriores` só em embargos e manifestação; `argumentacao_suficiente` e `texto_generico` na inicial e nos embargos; `estilo` em todos, não eliminatório. Decisão tomada por falta de resposta.
  4. **Travas divididas por papel:** onde o Anexo A.5 fala em "parte", há uma trava para o autor e outra para o réu. OSCIP e sociedade de crédito ao microempreendedor ficam fora das categorias do autor, por simplicidade.
  5. **Faixas de CEP** propostas de memória, a conferir.
  6. **Reais proibidos:** 6 candidatos tirados por coincidirem com nomes reservados (só a contagem).
  7. **Recesso do art. 220 do CPC** não tratado pela contagem de prazo (pergunta 3).
