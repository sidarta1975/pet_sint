# Relatório do brief 019 — Erros por programa

- Data: 2026-11-21
- Brief: `docs/briefs/brief_019_erros_programa_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.** `test_erros_programa.py` passa no gate (critério da Fase 9).

## RELATÓRIO FINAL

- Brief executado: 019 — Erros por programa (Fase 9).

- Arquivos criados:
  - `docs/briefs/brief_019_erros_programa_2026-11-21.md` — o brief, literal;
  - `testes/test_erros_programa.py` — os 7 pontos do aceite (14 testes), com peças, extrações e fichas de exemplo das três peças do ensaio;
  - `fabrica/erros_plantados.py` — `Material`, `Copia`, `gerar` (os 8 erros de regra e a função trocada), `sortear`, `pecas_base`, `material`, `gravar_copias`, `por_extenso`, `formatar_reais`, `datas_da_ficha`, `tem_par`;
  - `docs/docs/doc_019_erros_programa_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `fabrica/__main__.py` — o comando `erros --rodada <rodada>`;
  - `docs/ARQUITETURA.md` — seção 8, a linha do comando `python -m fabrica erros --rodada <rodada>`;
  - `docs/docs/pendencias_para_o_computador.md` — quatro linhas do 019;
  - `docs/PLAN.md` — Resumo; 019 do Backlog para o Done; hash do 018 no Done.

- Arquivos preservados literalmente na área afetada: `dados/`, `config/`, os demais módulos, `scripts/`, `AGENTS.md`, `docs/PLANO.md`.

- Testes rodados e resultado (com a saída colada):

  Primeiro o teste, sem o código (vermelho):

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_erros_programa.py'.
  E   ImportError: cannot import name 'erros_plantados' from 'fabrica' (/home/user/pet_sint/fabrica/__init__.py)
  ```

  Gate (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  108 files already formatted
  == mypy fabrica
  Success: no issues found in 30 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 1102 items

  testes/test_ancora.py ..........................                         [  2%]
  testes/test_api_claude.py ...............................                [  5%]
  testes/test_arquivos.py ..................                               [  6%]
  testes/test_citacoes.py ................................................ [ 11%]
  ............                                                             [ 12%]
  testes/test_comparacao.py .............................................. [ 16%]
  ..............................................                           [ 20%]
  testes/test_conferencia_etapas.py ..............                         [ 21%]
  testes/test_config.py .................................................. [ 26%]
  ........................................................................ [ 32%]
  ........................................................................ [ 39%]
  ...............................................................          [ 45%]
  testes/test_congelamento.py .................                            [ 46%]
  testes/test_dados_reais.py ..........................................    [ 50%]
  testes/test_decisao.py .................                                 [ 52%]
  testes/test_entrega.py .................................                 [ 55%]
  testes/test_erros_programa.py ..............                             [ 56%]
  testes/test_estado.py ........................................           [ 59%]
  testes/test_estatistica.py ..........                                    [ 60%]
  testes/test_fichas.py .............                                      [ 62%]
  testes/test_ficticios.py ..........................                      [ 64%]
  testes/test_formatos.py ................................................ [ 68%]
  ........................................................................ [ 75%]
  ........................................................................ [ 81%]
  ......................................................................   [ 88%]
  testes/test_gasto.py ..............                                      [ 89%]
  testes/test_integracao.py ....                                           [ 89%]
  testes/test_modelo_local.py ..........................                   [ 92%]
  testes/test_redacao.py ......                                            [ 92%]
  testes/test_registro.py ...                                              [ 93%]
  testes/test_regras.py .......................                            [ 95%]
  testes/test_travas.py .................................................. [ 99%]
  ....                                                                     [100%]

  ============================ 1102 passed in 25.99s =============================
  saída=0
  ```

- Comandos executados: `pytest testes/test_erros_programa.py` (vermelho e depois verde); `ruff format`; `ruff check --fix`; `scripts/verificar.sh`; `scripts/entregar.sh 019`. Nenhuma chamada a modelo.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_019_erros_programa_2026-11-21.md
testes/test_erros_programa.py
fabrica/erros_plantados.py
fabrica/__main__.py
docs/ARQUITETURA.md
docs/docs/pendencias_para_o_computador.md
docs/docs/doc_019_erros_programa_2026-11-21.md
docs/PLAN.md

Brief 019: erros por programa

Uma cópia por programa para cada peça boa (no ensaio, as três), sobre a
primeira versão: os oito erros de regra do Anexo C.1 e a função trocada
do Anexo C.2, cada um numa só região achada pelo texto da extração da
original, com o gabarito tirado do catálogo. Comando erros --rodada.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Peça boa:** `saida/cartoes/<peça>_respostas.json` com `veredito_ficha` e `veredito_peca` iguais a "aprovada" (o id do cartão é o id da peça, como em `saida/cartoes/<rodada>_<tipo>_<n>_etapa1.md` da ARQUITETURA §1.3; o 020 constrói o cartão). As candidatas são as peças com `saida/rascunhos/<peça>_v1.md`. No ensaio, todas as que têm a primeira versão.
  2. **Achar o trecho:** o texto que a extração da original devolveu precisa aparecer uma só vez na peça, fora da linha da marca; se aparecer mais de uma vez, a troca não acontece ali. Quando o valor em algarismos vem seguido do extenso entre parênteses, a região inclui o extenso, e os dois mudam juntos.
  3. **Valor novo:** fator sorteado entre 0,3 e 0,8 ou entre 1,25 e 2,5 do valor original, em reais inteiros, até cair a mais de 1% (`diferenca_minima_valor_trocado`) de cada valor da ficha, de cada soma de valores da ficha, do valor da causa e dos valores de referência legal (salário mínimo e alçada, do `config.toml` e da ficha). A soma proibida considera todos os valores de `valores[]`, o que cobre a soma dos pedidos.
  4. **Data nova:** 1 a 3 meses antes ou depois, com o dia até 28, fora das datas da ficha. Fora do prazo: de 3 a 30 dias depois do termo final recalculado com os feriados. A data é escrita no estilo da original (dd/mm/aaaa ou "d de mês de aaaa").
  5. **Acima da alçada:** de 1,1 a 2 vezes a alçada da ficha (40 salários mínimos de `salario_minimo_referencia`).
  6. **Citação fora da tabela:** troca o número do artigo por um de 200 a 999 que o diploma não tem na tabela, e confere que `citacoes.py` reprova.
  7. **Textos fixos do brief:** `juizo_trocado` usa a comarca da ficha, a sigla da UF (os dados não trazem o nome do estado por extenso; linha nas pendências) e outra cidade de `listas_ficticias.json`; a frase do `termo_inequivoco` vai no fim do primeiro bloco presente entre `fundamentos`, `razoes`, `novo_endereco` e `exposicao`; o pedido incompatível é um da lista do tipo com o rito da ficha, num parágrafo novo no fim do bloco de pedidos.
  8. **Função trocada:** a citação é trocada por `art. <artigo do par>[, <parágrafo>,] <resto da citação original>`; a cópia só vale se `citacoes.py` resolver o dispositivo novo e não reprovar.
  9. **Sorteio:** `random.Random("<semente>:<tipo>:erros_programa")`. Cada peça só recebe erros que cabem nela (a viabilidade é testada antes); o erro de regra é o de menor contagem até ali, com desempate pela ordem sorteada. A peça em que nenhum erro cabe fica sem cópia por programa, e o sorteado que não couber na geração para o comando com erro.
  10. **Gabarito:** `original` é `<peça>_v1`; `sutil` é falso nas cópias por programa; `verificador` e `item_apontado_pelo_verificador` ficam vazios.
