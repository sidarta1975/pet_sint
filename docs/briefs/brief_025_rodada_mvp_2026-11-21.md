# Brief 025 — Rodada do MVP

- Fase: 13 — Rodada do MVP (PLANO §4)
- Objetivo: preparar o roteiro da rodada `r01` para o responsável e, depois que ele rodar, ler `saida/relatorios/relatorio_mvp.md`, resumir o resultado de cada critério com as ressalvas e registrar a decisão do responsável de escalar ou não.
- Seções a ler: AGENTS §6, §7 e §8; PLANO §1, §2, §4 (Fase 13) e §4.1; ARQUITETURA §1.4, §5.1, §5.7, §5.9, §5.11, §5.12 (toda), §6, §8 e §9; armadilhas do PLAN: "congelamento.py", "estatistica.py, plano B".
- Arquivos que pode criar:
  - `docs/roteiros/roteiro_rodada_2026-11-21.md`;
  - `docs/briefs/brief_025_rodada_mvp_2026-11-21.md` (este brief);
  - `docs/docs/doc_025_rodada_mvp_2026-11-21.md` (o relatório).
- Arquivos que pode alterar: `docs/PLAN.md` (Resumo, Doing, Backlog, Done e Pendências de Sidarta Borges).
- Arquivos que não pode tocar: `fabrica/`, `instrucoes/`, `dados/`, `config/` e `testes/` (qualquer mudança neles invalida a rodada pelo congelamento); `saida/`; `scripts/`; `AGENTS.md`; `docs/PLANO.md`; `docs/ARQUITETURA.md`.
- Teste de aceite (escrito antes do código): não há código neste brief. O gate continua verde. O aceite é `saida/relatorios/relatorio_mvp.md` de uma rodada válida, com todos os critérios da ARQUITETURA §6, e a decisão do responsável registrada.
- Critério de conclusão: o da Fase 13 no PLANO — `saida/relatorios/relatorio_mvp.md` existe com todos os critérios da ARQUITETURA §6, de uma rodada válida, e o responsável registrou a decisão de escalar ou não.
- Fora do escopo: rodar qualquer comando que gaste API (só o responsável); decidir se escala (só o responsável; o executor só descreve); corrigir qualquer arquivo durante a rodada; começar o piloto.
- Depende de: 024, com o ensaio aprovado registrado em `saida/rodadas.json`.

**Regras deste brief**

- **Primeira sessão: o roteiro.** O executor escreve `docs/roteiros/roteiro_rodada_2026-11-21.md`, em português simples, com:
  1. o que precisa estar igual ao ensaio aprovado: nenhum arquivo de código, `dados/`, `instrucoes/` ou `config/` mudado desde então (o comando `fichas` recusa a rodada se algo mudou, e diz o quê);
  2. a sequência: `python -m fabrica fichas --tipo peticao_inicial_jec`, `--tipo embargos_declaracao` e `--tipo manifestacao_ar_negativo` (a primeira abre a rodada `r01` com a semente gravada); `python -m fabrica avancar`, repetido quantas vezes for preciso, inclusive dentro da janela da conferência local; `python -m fabrica revisar` para as 30 primeiras versões (às cegas, com a ficha ao lado; a segunda etapa de cada cartão só aparece depois de confirmar as respostas); `python -m fabrica erros --rodada r01` e `avancar` até o fim do banco; `revisar` para a amostra de 10 cópias e a das descartadas; `python -m fabrica testar --rodada r01`, `avancar` e `testar --rodada r01` de novo; `revisar` para as leituras de publicação, se houver (opcional, não entra em nenhuma medida); `python -m fabrica publicar --rodada r01`; `python -m fabrica relatorio --rodada r01`;
  3. o plano B, que o programa aplica sozinho pela contagem de peças boas, sem decisão nova (ARQUITETURA §5.12.6);
  4. o que é operação normal, pausa, parada e intervenção (ARQUITETURA §5.12.3), e que interromper um comando é seguro;
  5. o custo esperado (US$ 19 a 25, PLANO §1), o alerta em US$ 30 e o corte em US$ 100, que não sobe;
  6. o que enviar ao projeto ao terminar: `saida/relatorios/`, `saida/registro/` e `saida/rodadas.json`, compactados num arquivo só.
  O executor entrega pelo `scripts/entregar.sh 025` e escreve na resposta final só a pendência: "Rodar a rodada do MVP pelo roteiro `docs/roteiros/roteiro_rodada_2026-11-21.md` e enviar ao projeto os arquivos pedidos no fim dele".
- **Segunda sessão: a leitura.** Com os arquivos enviados, o executor acrescenta ao relatório a seção "## Resultado da rodada": de qual rodada são os números; cada critério da ARQUITETURA §6 com o resultado, a exigência e a margem; as ressalvas marcadas; e, quando um critério não for atingido, o módulo que a tabela de erros não pegos aponta. O executor não recomenda escalar nem não escalar.
- **Terceira sessão: a decisão.** Quando o responsável disser a decisão, o executor acrescenta a seção "## Decisão do responsável", com a data, a decisão (escalar para o piloto ou não) e as ressalvas que ele registrar, e atualiza o `docs/PLAN.md`. Só então o brief é concluído.
- Se a rodada for invalidada por intervenção ou terminar no corte, o relatório diz isso; uma rodada nova (`r02`) exige corrigir a causa, um ensaio novo e um brief novo, com o número seguinte da sequência.
