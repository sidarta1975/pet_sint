# Relatório do brief 023 — Relatório do MVP e fechamento do ensaio

- Data: 2026-11-21
- Brief: `docs/briefs/brief_023_relatorio_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.** O relatório traz cada item da ARQUITETURA §5.11 com dados falsos, `ensaio --fechar` aplica a regra de §5.12.1, o ensaio inteiro passa pelos comandos com clientes falsos em `test_integracao.py` e o gate passa (critério da Fase 11). Com este brief, todo o código e todas as instruções estão prontos para o ensaio (brief 024, que espera o computador do responsável).

## RELATÓRIO FINAL

- Brief executado: 023 — Relatório do MVP e fechamento do ensaio (Fase 11).

- Arquivos criados:
  - `docs/briefs/brief_023_relatorio_2026-11-21.md` — o brief, literal;
  - `testes/test_relatorios.py` — o aceite (27 testes), com registro, ocorrências, conferências, cartões e resultado do teste falsos;
  - `fabrica/relatorios.py` — leitura da rodada (`ler`), os critérios da seção 6, as ressalvas, as seções 2 a 14 de §5.11, `montar`, `gerar` (o comando `relatorio`) e o fechamento do ensaio (`conferir_ensaio`, `fechar_ensaio`);
  - `docs/docs/doc_023_relatorio_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `fabrica/__main__.py` — o comando `relatorio --rodada <rodada>` e `ensaio --fechar <rodada>` (dentro de `comando_ensaio`, com a lista `ETAPAS`);
  - `testes/test_integracao.py` — o `ApiFalsa` responde às duas seções de `plantar_erro.md` (Opus e Sonnet) e reconhece as cópias por programa; três cenários novos: o ensaio inteiro pelos comandos e aprovado (sem a chave falsa em nenhum arquivo de `saida/`), o Opus fora do formato (reprovado) e o pedido local acima de 75% do `num_ctx` (reprovado, com 16.384 e 32.768 na mensagem);
  - `fabrica/erros_plantados.py` — **defeito comprovado** (ADR 001, item 19): a ocorrência do custo da descartada dizia "milionésimos de dólar"; o custo é em milionésimos de centavo de dólar (ADR 001, item 3). Só o texto mudou;
  - `docs/ARQUITETURA.md` — seção 8, as linhas de `relatorio` e `ensaio --fechar`; a consolidação dos acréscimos do método dos briefs 004 a 023 (ADR 001, item 20): na árvore da seção 2, os 11 arquivos de teste novos, `saida/preparacao/`, `saida/registro/rodadas_anteriores/` e os dois ADR; na seção 2.4, uma linha por arquivo de teste novo. Tudo marcado como acréscimo do método. Conferi, arquivo por arquivo, que cada item consolidado existe no repositório (`docs/roteiros/` fica para o 024);
  - `docs/docs/pendencias_para_o_computador.md` — as linhas do 023;
  - `docs/PLAN.md` — Resumo; 023 do Backlog para o Done; hash do 022 no Done.

- Arquivos preservados literalmente na área afetada: `fabrica/estado.py`, `fabrica/revisao.py`, `fabrica/teste_conferentes.py`, `fabrica/publicacao.py`, os módulos de `conferencia/` e `comum/`, `dados/`, `config/`, `instrucoes/`, `scripts/`, `AGENTS.md` e `docs/PLANO.md`.

- Como funciona:
  1. **`relatorio --rodada <rodada>`** grava `saida/relatorios/relatorio_mvp.md` (no ensaio, `relatorio_<rodada>.md`) e não regrava um relatório que já existe. Recusa rodada que não está em `saida/rodadas.json`.
  2. **Ordem de §5.11.** Primeiro os critérios da seção 6, cada um com o resultado, a exigência, a margem de Wilson e o papel (decide ou indicador), o critério central em primeiro, com a taxa sem o Opus e a dos erros de julgamento por programa ao lado. Depois as ressalvas e as seções 2 a 14. A última linha diz que a decisão de escalar é do responsável: o relatório só descreve e marca.
  3. **Critério central.** Não decide com o banco não confiável; é inconclusivo com menos de 14 peças boas, ou quando o teste não foi feito depois de um corte de gasto.
  4. **Peças boas reprovadas na primeira versão:** o limite é a proporção do brief com arredondamento para baixo (2 de 20 a 29 boas, 1 de 14 a 19). A reprovação só por semelhança fica numa linha própria, como indicador, para ser revista antes do piloto.
  5. **Custo marginal por peça aprovada** exclui o ensaio, as cópias do banco (`_banco`) e o teste (`teste_`); acima de 15 centavos, marca "rever antes de escalar". O gasto total soma tudo.
  6. **Ressalvas**, cada uma pelo seu gatilho: banco não confiável, filtrado pelo verificador, dependente do Opus e sem conferente local estável (mais de 20% das peças de risco médio e alto sem a resposta do modelo local, `valvula.fracao_sem_local_para_ressalva`).
  7. **Outras marcas:** "Os números vieram de uma rodada com intervenção." quando há ocorrência de intervenção; "fechou X de N" por tipo; as casas vazias com a causa da última peça descartada; o aviso para rever `ficha.md` e `fichas.py` do tipo com mais de 20% de fichas reprovadas pelo responsável. No ensaio, o aviso "ensaio: sem valor de medida" no alto e em cada critério.
  8. **`ensaio --fechar <rodada>`** só lê e confere: três peças, uma de cada tipo, no ponto final do condutor; ficha válida, conferência da primeira versão, cartão do ensaio com o formato certo confirmado e pacote; uma cópia com erro por peça, o sorteio das amostras e as respostas delas, o resultado do teste e o relatório do ensaio; nenhum pedido `_t2` (resposta fora do formato); nenhuma mudança nos arquivos congelados. Pedido ao modelo local que não coube ou passou de 75% do `num_ctx`: com `num_ctx` abaixo do alternativo, reprova e manda subir para 32.768 e fazer um ensaio novo; com o alternativo, só avisa e lista os pedidos. Se tudo passa, grava `ensaio_aprovado` e `aprovado_em` em `saida/rodadas.json` pela única regravação permitida (ADR 001, item 4), com a cópia anterior em `saida/registro/rodadas_anteriores/`. Se não passa, mostra cada motivo e não grava nada.

- Testes rodados e resultado (com a saída colada):

  Ordem: `relatorios.py` foi esboçado antes do teste. Para manter "teste antes do código", o teste foi escrito em seguida e rodado com `relatorios.py` tirado da árvore (vermelho), e só então o módulo voltou e foi ajustado até o verde (o mesmo procedimento do 018).

  ```text
    ImportError while importing test module '/home/user/pet_sint/testes/test_relatorios.py'.
  E   ImportError: cannot import name 'relatorios' from 'fabrica' (/home/user/pet_sint/fabrica/__init__.py)
  ```

  Gate (`scripts/verificar.sh`):

  ```text
    == ruff check
  All checks passed!
  == ruff format --check
  127 files already formatted
  == mypy fabrica
  Success: no issues found in 34 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 1180 items

  testes/test_ancora.py ..........................                         [  2%]
  testes/test_api_claude.py ...............................                [  4%]
  testes/test_arquivos.py ..................                               [  6%]
  testes/test_citacoes.py ................................................ [ 10%]
  ............                                                             [ 11%]
  testes/test_comparacao.py .............................................. [ 15%]
  ..............................................                           [ 19%]
  testes/test_conferencia_etapas.py ..............                         [ 20%]
  testes/test_config.py .................................................. [ 24%]
  ........................................................................ [ 30%]
  ........................................................................ [ 36%]
  ...............................................................          [ 42%]
  testes/test_congelamento.py .................                            [ 43%]
  testes/test_dados_reais.py ..........................................    [ 47%]
  testes/test_decisao.py .................                                 [ 48%]
  testes/test_entrega.py .................................                 [ 51%]
  testes/test_erros_opus.py .....................                          [ 53%]
  testes/test_erros_programa.py ..............                             [ 54%]
  testes/test_estado.py ........................................           [ 57%]
  testes/test_estatistica.py ..........                                    [ 58%]
  testes/test_fichas.py .............                                      [ 59%]
  testes/test_ficticios.py ..........................                      [ 61%]
  testes/test_formatos.py ................................................ [ 66%]
  ........................................................................ [ 72%]
  ........................................................................ [ 78%]
  ......................................................................   [ 84%]
  testes/test_gasto.py ..............                                      [ 85%]
  testes/test_integracao.py .......                                        [ 85%]
  testes/test_modelo_local.py ..........................                   [ 88%]
  testes/test_publicacao.py ........                                       [ 88%]
  testes/test_redacao.py ......                                            [ 89%]
  testes/test_registro.py ...                                              [ 89%]
  testes/test_regras.py .......................                            [ 91%]
  testes/test_relatorios.py ...........................                    [ 93%]
  testes/test_revisao.py .........                                         [ 94%]
  testes/test_teste_conferentes.py ..........                              [ 95%]
  testes/test_travas.py .................................................. [ 99%]
  ....                                                                     [100%]

  ============================ 1180 passed in 51.39s =============================
  saída=0
  ```

- Comandos executados: `pytest testes/test_relatorios.py` (vermelho e depois verde); `pytest testes/test_integracao.py`; `ruff format`; `ruff check --fix`; `mypy fabrica`; `scripts/verificar.sh`; `scripts/entregar.sh 023`. Nenhuma chamada a modelo.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_023_relatorio_2026-11-21.md
testes/test_relatorios.py
fabrica/relatorios.py
fabrica/__main__.py
fabrica/erros_plantados.py
testes/test_integracao.py
docs/ARQUITETURA.md
docs/docs/pendencias_para_o_computador.md
docs/docs/doc_023_relatorio_2026-11-21.md
docs/PLAN.md

Brief 023: relatório do MVP e fechamento do ensaio

Comando relatorio: cada item de 5.11 na ordem, os critérios da seção 6
com exigência, margem de Wilson e papel, as ressalvas e as marcas, sem
decidir. ensaio --fechar aplica 5.12.1 e só então grava o ensaio
aprovado. Ensaio inteiro pelos comandos no teste de integração.
Consolidação dos acréscimos do método na ARQUITETURA. Texto do custo da
descartada corrigido para milionésimos de centavo.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Peça boa:** a que tem ficha e peça aprovadas pelo responsável no cartão de revisão.
  2. **Limite das boas reprovadas:** proporção com arredondamento para baixo (2 de 20 a 29, 1 de 14 a 19).
  3. **"Sem conferente local estável":** conta sobre as peças de risco médio e alto com rascunho; falta de arquivo do conferente local conta como sem resposta.
  4. **Custo marginal:** só chamadas da rodada fora do banco e do teste, divididas pelas peças aprovadas pela fábrica.
  5. **Fechamento do ensaio:** mudança pendente nos arquivos de código (`git status`) conta como mudança nos congelados; qualquer pedido `_t2` da rodada conta como resposta fora do formato.
  6. **Fechar um ensaio já aprovado** não regrava; mostra que já está aprovado.
  7. **Os modelos das listas do banco fechado** continuam em `teste_conferentes.py` (pendência 3 do 022); o brief 023 não pediu a mudança.
  8. **Defeito comprovado fora da lista:** o texto do custo da descartada em `erros_plantados.py` (só o texto).
  9. **Auditoria do AGENTS §11:** com todo o código pronto, lembrar de rodar a auditoria prevista antes do ensaio (brief 024).
  10. **Para o ensaio (024), no computador:** os cinco comandos de conferência da máquina, `ANTHROPIC_API_KEY` em variável de ambiente, a janela do modelo local, a etiqueta e o digest do modelo local no `config.toml`, a conferência na fonte dos textos de lei marcados "a conferir na fonte", e então `preparar`, `ensaio`, `avancar`, `revisar`, `publicar`, `erros`, `testar`, `relatorio` e `ensaio --fechar`.
