# Relatório do brief 010 — Detector de dado real

- Data: 2026-11-21
- Brief: `docs/briefs/brief_010_detector_dado_real_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.** Com o 009, fecha o critério da Fase 5: 100% dos nomes reservados pegos, com a lista de proibidos vazia.

## RELATÓRIO FINAL

- Brief executado: 010 — Detector de dado real (Fase 5).

- Arquivos criados:
  - `docs/briefs/brief_010_detector_dado_real_2026-11-21.md` — o brief, literal;
  - `fabrica/conferencia/__init__.py` — o pacote da conferência;
  - `fabrica/conferencia/dados_reais.py` — `Detector`, que recebe tudo por parâmetro e devolve os achados (tipo, trecho, posição): CPF, CNPJ (inclusive com letras) e número do CNJ com dígito válido; OAB diferente do marcador; telefone com DDD fora dos 15; e-mail fora de `.example`; rua que não está na ficha; contrato ou protocolo sem `SINT-`; código de banco da lista oficial; nome que não é marcador nem permitido (sequência de maiúsculas fora do início de frase, tratamento, forma societária, "Banco", "Companhia" e semelhantes); nome da lista de proibidos; nome ao lado de cargo de juiz ou de servidor;
  - `testes/test_dados_reais.py` — o teste de aceite (os 5 pontos do brief), escrito antes do código; os nomes reservados são lidos do arquivo do 009, nunca copiados;
  - `docs/docs/doc_010_detector_dado_real_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `docs/PLAN.md` — Resumo; 010 do Backlog para o Done; hash do 009 no Done; fase atual.

- Arquivos preservados literalmente na área afetada: `testes/dados/reais_reservados.json` (só lido no teste), `fabrica/ficticios.py`, `fabrica/comum/`, `config/`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`. Nenhum defeito comprovado.

- Testes rodados e resultado (com a saída colada):

  Primeiro o teste, sem o código (vermelho):

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_dados_reais.py'.
  E   ModuleNotFoundError: No module named 'fabrica.conferencia'
  ```

  Com o código, os 41 casos passaram na primeira rodada; depois, duas condições do detector foram simplificadas sem mudar o comportamento, e o item 5 ganhou um caso de siglas juntas ("CPF e CNPJ"). Gate final (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  58 files already formatted
  == mypy fabrica
  Success: no issues found in 16 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 779 items

  testes/test_api_claude.py ...............................                [  3%]
  testes/test_arquivos.py ..................                               [  6%]
  testes/test_config.py .................................................. [ 12%]
  ........................................................................ [ 21%]
  ........................................................................ [ 31%]
  ...............................................................          [ 39%]
  testes/test_congelamento.py .................                            [ 41%]
  testes/test_dados_reais.py ..........................................    [ 46%]
  testes/test_entrega.py .................................                 [ 51%]
  testes/test_estado.py ........................................           [ 56%]
  testes/test_estatistica.py ..........                                    [ 57%]
  testes/test_ficticios.py ..........................                      [ 60%]
  testes/test_formatos.py ................................................ [ 67%]
  ........................................................................ [ 76%]
  ........................................................................ [ 85%]
  ......................................................................   [ 94%]
  testes/test_gasto.py ..............                                      [ 96%]
  testes/test_modelo_local.py ..........................                   [ 99%]
  testes/test_registro.py ...                                              [100%]

  ============================= 779 passed in 14.50s =============================
  ```

- Comandos executados: `pytest testes/test_dados_reais.py` (vermelho e depois verde); `ruff format`; `scripts/verificar.sh`; `scripts/entregar.sh 010`. Nenhuma chamada a modelo.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_010_detector_dado_real_2026-11-21.md
fabrica/conferencia/__init__.py
fabrica/conferencia/dados_reais.py
testes/test_dados_reais.py
docs/docs/doc_010_detector_dado_real_2026-11-21.md
docs/PLAN.md

Brief 010: detector de dado real

dados_reais.py aplica a detecção da ARQUITETURA 5.2 e devolve cada achado.
O teste pega 100% dos nomes reservados com a lista de proibidos vazia,
confere que nenhum deles aparece em fabrica/ (dados/ ainda não existe) e
que termos jurídicos, permitidos, títulos e a marca não são acusados.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Parâmetro a mais, `termos_da_ficha`:** além das ruas, o detector recebe os outros textos do endereço e do processo que a ficha traz (bairro, cidade, comarca, juízo). Sem isso, um bairro fictício de duas palavras ("Jardim ...") seria acusado como nome. Quem chama o detector na conferência (brief 017) passa esses textos tirados da ficha.
  2. **Para o brief 014 (`reais_permitidos.json`):** precisam estar na lista, para não serem acusados, as leis e códigos com nome de duas ou mais palavras ("Código de Defesa do Consumidor", "Código Civil", "Constituição Federal", "Código de Processo Civil"), as designações processuais com maiúscula ("Representante Legal", "Requerente", "Requerido", "Embargante", "Embargado"), os cargos com complemento ("Juiz de Direito Substituto"), os juízos, as varas e os tribunais, e os sistemas e órgãos.
  3. **Siglas:** palavras todas em maiúsculas (CPF, CNPJ, INSS, CNJ) não formam nome entre si; só contam junto de uma palavra comum com maiúscula ou de forma societária ou "Banco".
  4. **Início de frase:** depois de ponto, de dois-pontos, de interrogação, de exclamação ou de quebra de linha, a primeira palavra não conta, salvo se for "Banco", "Companhia" ou semelhante, ou se a sequência tiver forma societária. Ponto de abreviação (Sr., Dr., nº, art., S.A., Ltda.) não abre frase.
  5. **OAB:** qualquer "OAB" seguida, em até 25 caracteres, de número que não seja o marcador reprova. Uma menção à OAB seguida de número de artigo pode, em tese, ser acusada; o caso não aparece nos exemplos e fica como limite conhecido.
  6. **Contrato e protocolo:** reprova o número logo depois de "contrato" ou "protocolo" (com "nº" ou "número" no meio ou não) que não começa com `SINT-`. Número separado da palavra por outras palavras ("contrato de prestação de serviços nº ...") não é conferido.
  7. **CPF** só no formato com pontos e traço; **telefone** só com o DDD entre parênteses ou com "+55". Formatos sem separador não são conferidos.
  8. **Lista oficial dos códigos de banco:** vazia no MVP (pendência do 009); com a lista vazia, nenhum código é acusado.
  9. **Busca dos reservados no código:** feita sobre `fabrica/`, porque `dados/` ainda não existe; o teste diz isso na mensagem e passa a incluir `dados/` sozinho quando a pasta existir (brief 014).
  10. **Ramo único**, como nos briefs anteriores (pedido de integração #2).

- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim.
