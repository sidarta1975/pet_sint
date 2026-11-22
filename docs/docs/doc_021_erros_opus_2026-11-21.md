# Relatório do brief 021 — Erros plantados pelo Opus e verificação do Sonnet

- Data: 2026-11-21
- Brief: `docs/briefs/brief_021_erros_opus_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.** `test_erros_opus.py` passa no gate, com o Opus, o Haiku e o Sonnet falsos. O critério da Fase 11 fecha no brief 023.

## RELATÓRIO FINAL

- Brief executado: 021 — Erros plantados pelo Opus e verificação do Sonnet (Fase 11).

- Arquivos criados:
  - `docs/briefs/brief_021_erros_opus_2026-11-21.md` — o brief, literal;
  - `instrucoes/plantar_erro.md` — os dois textos da ARQUITETURA §2.3, cada um sob o seu título (`# Cópia com erro`, para o Opus, e `# Verificação da cópia`, para o Sonnet). O código lê cada texto pelo título;
  - `testes/test_erros_opus.py` — os 7 pontos do aceite (21 testes), com um falso que responde pela instrução que abre o pedido;
  - `docs/docs/doc_021_erros_opus_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `fabrica/erros_plantados.py` — só acréscimos, depois da parte por programa (019), que não mudou:
    - o plano das vagas (`planejar` e `plano_da_rodada`);
    - a troca feita pelo programa (`trocar`);
    - as quatro etapas do banco, pela interface do registro de decisão 002: `EtapaCopiaOpus`, `EtapaExtracaoDaCopia`, `EtapaProgramasDaCopia` e `EtapaVerificacao`;
    - o motivo do descarte (`motivo_do_descarte`), o descarte com o custo à parte (`descartar`) e o ponto de cada vaga (`estado_da_vaga`);
    - o comando (`gravar_banco`), a coleta (`coletar_banco`), o resumo (`resumo_do_banco`) e as amostras (`sortear_amostras` e `gravar_amostras`);
  - `fabrica/__main__.py`:
    - o comando `erros` chama `gravar_banco` depois das cópias por programa e mostra o resumo das vagas;
    - **fora da parte que o brief libera:** o comando `avancar` também chama `coletar_banco`. Sem isso, o `avancar` não acha as cópias do banco, porque o condutor só descobre as peças pelos pedidos de ficha. Assim, a regra do brief ("a coleta pelo `avancar`") não teria como ser cumprida. A interface das etapas não mudou, e `estado.py` também não. Ver a pendência 1;
  - `docs/docs/pendencias_para_o_computador.md` — oito linhas do 021;
  - `docs/PLAN.md` — Resumo; 021 do Backlog para o Done; hash do 020 no Done.

- Arquivos preservados literalmente na área afetada: `docs/ARQUITETURA.md`, `fabrica/revisao.py`, `dados/`, `config/`, os demais módulos (inclusive `estado.py` e `conferencia/`), `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `testes/test_integracao.py` e `testes/test_erros_programa.py`.

- Como funciona:
  1. **Vagas.**
     - Pelo plano B (ARQUITETURA §5.12.6), com o número de peças boas da rodada (as do `pecas_base` do 019):
       - 20 ou mais: 4 vagas por peça (`volume.copias_opus_por_peca_boa`);
       - de 14 a 19: 6 vagas (`plano_b.copias_opus_por_peca_boa_faixa_media`);
       - menos de 14: nenhuma vaga.
     - No ensaio, 1 vaga por peça.
     - As vagas são numeradas de 2 em diante, porque a vaga 1 é a do programa.
     - A rodada inconclusiva e a da faixa média ficam marcadas uma vez no registro de ocorrências (`criterio_central_inconclusivo` e `plano_b_faixa_media`), para o relatório do 023.
  2. **Sorteio.**
     - Os tipos de uma peça são diferentes entre si e saem dos erros do Opus no catálogo que cabem no tipo da peça.
     - O tipo menos usado no conjunto vem primeiro. O empate é decidido por uma ordem sorteada com a semente da rodada, e as peças são percorridas alternando os tipos de peça.
     - Metade das vagas é sutil (`volume.fracao_copias_opus_sutis`, arredondada para baixo no acumulado). Ficam sutis os tipos de erro com menos sutis até ali.
     - Com a mesma semente, o sorteio é igual, qualquer que seja a ordem de entrada.
  3. **Cada tentativa de uma vaga** é a cópia `<peça>_erro<k>_<t>`, levada pelo condutor por quatro etapas:
     1. o pedido ao Opus (`copia_com_erro`), com o texto do Opus, o erro pedido em JSON (tipo, descrição do catálogo, sutil) e a original (`_v1`). A troca é feita pelo programa (`trocar`);
     2. a extração da cópia pelo Haiku, com a instrução e a tarefa da extração (017). Ela é gravada em `saida/erros/<cópia>_extracao.json` e não é reaproveitada no 022;
     3. os itens de programa do Anexo B.1 (menos `semelhanca`) na cópia, em `<cópia>_programas.json`;
     4. o Sonnet (`verificacao_copia`), que recebe só os itens do tipo, menos `semelhanca` e `marca`, e um JSON com a original e a cópia, sem o erro pedido.

     A cópia aceita grava `<cópia>_gabarito.json`. A descartada grava `<cópia>_descartada.json`, e o condutor a encerra ali.
  4. **Conferência de programa da troca.** A cópia é descartada quando:
     - o trecho original não aparece exatamente uma vez, ou está vazio;
     - o trecho novo é igual ao original;
     - o resto da peça não ficou idêntico;
     - a troca muda mais de uma região (comparação por linhas);
     - a região trocada passa de `erros.fracao_maxima_regiao` (0,25) do texto. A região é a maior entre a parte tirada e a parte posta, depois de descontar o começo e o fim iguais;
     - algum item de programa reprova fora dos itens aceitos do tipo de erro.

     O descarte de programa tem o motivo vazio.
  5. **Motivo do Sonnet, decidido por programa:**
     - sem item apontado, é sempre `nao_viu_erro`;
     - com outro problema, `outro_problema`;
     - com item fora dos aceitos, `outro_item`;
     - nos demais casos, a cópia passa.
  6. **Refação e troca de tipo.**
     - A tentativa 2 refaz o mesmo tipo.
     - Depois da segunda falha, a vaga troca de tipo. O novo tipo cabe na peça, não é nenhum dos tipos dela e é o menos usado no conjunto. Ele fica gravado em `saida/erros/<peça>_erro<k>_troca_de_tipo.txt` e mantém a sutileza da vaga.
     - O tipo novo também tem duas tentativas (3 e 4). Falhando as duas, a vaga fica perdida.
     - `resumo_do_banco` conta as vagas aceitas, pendentes, perdidas e as que trocaram de tipo, e o comando `erros` mostra a contagem.
  7. **Custo à parte.** Cada descarte grava no registro uma ocorrência `custo_copia_descartada`, com a soma dos custos das chamadas daquela cópia.
  8. **Resposta fora do formato duas vezes.** O condutor encerra a cópia (destino do §5.12.8). O comando `erros` grava a descartada: `programa` se a falha foi antes do Sonnet, `verificador` se foi no Sonnet. O motivo fica vazio, e a vaga segue para a próxima tentativa.
  9. **Amostras.**
     - Vão para `saida/erros/<rodada>_amostras.json` (modelo `Amostras`, lido pelo 020).
     - O sorteio só acontece quando nenhuma vaga está pendente, e uma vez só.
     - Na rodada: 10 cópias aceitas e até 5 descartadas por `nao_viu_erro`.
     - No ensaio: as aceitas até 3 e até 1 descartada.
     - A semente é a da rodada.
     - Na rodada inconclusiva não há sorteio.
  10. **Caminho de dois passos.**
      - O `erros` grava o pedido ao Opus de cada vaga que espera cópia, sem enviar.
      - O `avancar` envia, recebe e leva a cópia pelas etapas seguintes.
      - O `erros` seguinte grava as refações e as trocas e, com tudo resolvido, sorteia as amostras.
      - O condutor conhece a cópia pela referência `<cópia>_banco`. Assim, os seus arquivos (pedidos, marcadores e destino) não se misturam com os do teste dos conferentes (022), que conferirá a mesma cópia às cegas.

- Testes rodados e resultado (com a saída colada):

  Primeiro o teste, sem o código (vermelho):

  ```text
    E   AttributeError: module 'fabrica.erros_plantados' has no attribute 'secao'
  ERROR testes/test_erros_opus.py - AttributeError: module 'fabrica.erros_plant...
  ```

  Gate (`scripts/verificar.sh`):

  ```text
    == ruff check
  All checks passed!
  == ruff format --check
  118 files already formatted
  == mypy fabrica
  Success: no issues found in 32 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 1140 items

  testes/test_ancora.py ..........................                         [  2%]
  testes/test_api_claude.py ...............................                [  5%]
  testes/test_arquivos.py ..................                               [  6%]
  testes/test_citacoes.py ................................................ [ 10%]
  ............                                                             [ 11%]
  testes/test_comparacao.py .............................................. [ 15%]
  ..............................................                           [ 19%]
  testes/test_conferencia_etapas.py ..............                         [ 21%]
  testes/test_config.py .................................................. [ 25%]
  ........................................................................ [ 31%]
  ........................................................................ [ 38%]
  ...............................................................          [ 43%]
  testes/test_congelamento.py .................                            [ 45%]
  testes/test_dados_reais.py ..........................................    [ 48%]
  testes/test_decisao.py .................                                 [ 50%]
  testes/test_entrega.py .................................                 [ 53%]
  testes/test_erros_opus.py .....................                          [ 55%]
  testes/test_erros_programa.py ..............                             [ 56%]
  testes/test_estado.py ........................................           [ 59%]
  testes/test_estatistica.py ..........                                    [ 60%]
  testes/test_fichas.py .............                                      [ 61%]
  testes/test_ficticios.py ..........................                      [ 64%]
  testes/test_formatos.py ................................................ [ 68%]
  ........................................................................ [ 74%]
  ........................................................................ [ 80%]
  ......................................................................   [ 87%]
  testes/test_gasto.py ..............                                      [ 88%]
  testes/test_integracao.py ....                                           [ 88%]
  testes/test_modelo_local.py ..........................                   [ 90%]
  testes/test_publicacao.py ........                                       [ 91%]
  testes/test_redacao.py ......                                            [ 92%]
  testes/test_registro.py ...                                              [ 92%]
  testes/test_regras.py .......................                            [ 94%]
  testes/test_revisao.py .........                                         [ 95%]
  testes/test_travas.py .................................................. [ 99%]
  ....                                                                     [100%]

  ============================ 1140 passed in 43.21s =============================
  saída=0
  ```

- Comandos executados: `pytest testes/test_erros_opus.py` (vermelho e depois verde); `ruff format`; `ruff check --fix`; `scripts/verificar.sh`; `scripts/entregar.sh 021`. Nenhuma chamada a modelo: o cliente da API é falso.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_021_erros_opus_2026-11-21.md
instrucoes/plantar_erro.md
testes/test_erros_opus.py
fabrica/erros_plantados.py
fabrica/__main__.py
docs/docs/pendencias_para_o_computador.md
docs/docs/doc_021_erros_opus_2026-11-21.md
docs/PLAN.md

Brief 021: cópias do Opus e verificação do Sonnet

Vagas do Opus pelo plano B (4, 6 ou nenhuma; 1 no ensaio), com tipos
diferentes por peça, equilibrados no conjunto e metade sutis. Troca feita
pelo programa e conferida (trecho único, uma região, até um quarto, resto
idêntico, itens de programa na cópia); extração da cópia pelo Haiku;
Sonnet sem o erro pedido; motivo do descarte por programa; refação, troca
de tipo e custo das descartadas à parte; sorteio das duas amostras.
O erros grava os pedidos e o avancar coleta. Instruções em plantar_erro.md.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **O `avancar` coleta o banco.** O comando `avancar` ganhou a chamada a `coletar_banco`, fora da parte de `__main__.py` que o brief libera. É o único jeito de cumprir "a coleta pelo `avancar`" sem mudar o condutor. Se o responsável preferir, a coleta pode ficar no próprio `erros`; nesse caso, o `erros` passaria a enviar pedidos.
  2. **Quantas trocas de tipo.** O brief não diz quantas vezes a vaga troca de tipo. Provisório: uma troca, com duas tentativas no tipo novo. Depois disso, a vaga fica perdida e é contada no resumo.
  3. **"Mais de uma região"** é medido por linhas: a troca não pode mudar duas linhas separadas por uma linha igual. A fração da região é a maior entre a parte tirada e a parte posta.
  4. **Resposta fora do formato duas vezes:** descarte com motivo vazio, de `programa` antes do Sonnet e de `verificador` no Sonnet. Não entra na amostra das descartadas. A extração da cópia fora do formato recebe do condutor o destino `copia_nao_pega`, porque a tarefa `extracao` não é do banco. O destino só encerra a referência `<cópia>_banco`, e o `erros` grava o descarte.
  5. **Lista do Sonnet:** os itens do tipo no catálogo, menos `semelhanca` e `marca`, com a pergunta de `lista_conferencia.json`. O item `estilo`, que só dá notas, fica na lista, porque o brief só tira os dois.
  6. **O que vai ao Opus:** o tipo do erro, a descrição do catálogo, se é sutil e a original. A ficha não vai. A original é a primeira versão, como na cópia por programa (019).
  7. **Marca do critério inconclusivo e da faixa média:** uma ocorrência no registro (`criterio_central_inconclusivo` e `plano_b_faixa_media`), porque os modelos de `formatos.py` não têm um campo para isso. O 023 a lê para o relatório.
  8. **Custo à parte:** uma ocorrência `custo_copia_descartada` por descarte, porque `Chamada` não tem um campo para a marca. As chamadas do banco têm `peca` igual a `<cópia>_banco`.
  9. **Para o brief 023 consolidar:** `test_erros_opus.py` e `plantar_erro.md` na ARQUITETURA; a linha do `erros` na §8, que agora também grava os pedidos ao Opus e sorteia as amostras; a coleta do banco no `avancar`.
