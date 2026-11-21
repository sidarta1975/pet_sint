# Registro de decisão 001 — Convenções da construção

- Data: 2026-11-21
- Situação: aceita
- Contexto: os canônicos deixam para os briefs alguns detalhes que o executor precisa para não inventar. Este registro junta as decisões, para que todos os briefs usem as mesmas.

## Decisões

1. Nomes curtos dos tipos: `peticao_inicial_jec`, `embargos_declaracao`, `manifestacao_ar_negativo`. O rótulo exato da lista consolidada fica no catálogo e nos metadados.
2. Identificadores: rodada `e01`, `e02`... no ensaio e `r01`, `r02`... na rodada; peça `<rodada>_<tipo>_<nnn>`, com três dígitos; versão `_v1` a `_v3`; cópia com erro `_erro<k>`.
3. Dinheiro da API: preço em centavos de dólar por milhão de tokens, inteiro; custo de cada chamada em milionésimos de centavo de dólar, inteiro; alerta e corte em centavos de dólar.
4. `saida/rodadas.json` é o único arquivo de `saida/` regravado, sempre por gravação atômica, e só para acrescentar rodada, mudar o estado de uma rodada ou registrar ensaio aprovado. Antes de cada regravação, a versão anterior vai para `saida/registro/rodadas_anteriores/rodadas_<carimbo>.json`.
5. Arquivos `.jsonl` são acrescentados linha a linha; uma última linha incompleta é ignorada na leitura.
6. Impressão digital do código: o identificador que o git dá ao conteúdo de `fabrica/` e de `pyproject.toml` na versão atual, sem mudança pendente em `fabrica/`, `dados/`, `instrucoes/`, `config/` e `pyproject.toml`. A leitura do git é feita por `arquivos.py`.
7. Contagem de tokens antes de enviar: pelo contador de tokens da API, que não cobra, só em `api_claude.py`.
8. Chave da API na variável de ambiente `ANTHROPIC_API_KEY`.
9. Pedidos e respostas: `saida/pedidos/<peça>_v<k>_<tarefa>_t<n>.json` e `saida/respostas/<peça>_v<k>_<tarefa>_t<n>.json`. Na ficha, que não tem versão, o nome não leva `_v<k>`.
10. Arquivos intermediários da conferência: `saida/conferencias/<peça>_v<k>_<etapa>.json`; o veredito final é `saida/conferencias/<peça>_v<k>.json`.
11. Estrutura montada: `saida/preparacao/<tipo>_estrutura.json` e `.md`.
12. Tabela de normas: objeto com `versao`, `diplomas[]` e `dispositivos[]`; citação conferida no nível de artigo e parágrafo, com inciso e alínea guardados para o cartão.
13. O rascunho leva a linha "DOCUMENTO SINTÉTICO — FICTÍCIO" no topo, posta por `redacao.py`, seguida do texto do redator como chegou.
14. Valor por extenso: quando a peça traz algarismos e extenso juntos, a extração devolve em `centavos` o valor por extenso, e o programa lê os algarismos do `texto`.
15. Comandos: `preparar`, `ensaio`, `fichas`, `avancar`, `revisar`, `erros`, `testar`, `publicar`, `relatorio`.
16. Gabarito e descartes: um arquivo por cópia (`<cópia>_gabarito.json` ou `<cópia>_descartada.json`); `gabarito.json` e `descartadas.json` são gravados uma vez, no fechamento do banco, já com o resultado das amostras.
17. No ensaio, os erros em miniatura e o pacote partem das três peças, qualquer que seja o veredito; o pacote do ensaio vai para `saida/pacotes/ensaio_<rodada>/<tipo>/`.
18. O ensaio aprovado é registrado pelo comando `ensaio --fechar <rodada>`, que aplica a regra da ARQUITETURA 5.12.1.
19. Defeito comprovado, que permite tocar num módulo já pronto, só existe com as três condições juntas: um teste (do brief atual ou do gate) falha por causa do módulo anterior, com a saída colada no relatório; a mudança é a mínima para o teste passar, sem refatoração; e não muda interface, formato de arquivo nem valor declarado. Fora disso, o executor para e registra a pendência.
20. Durante a construção, os briefs só alteram a ARQUITETURA na seção 8 (nome de cada comando, como o PLANO e a própria seção 8 mandam). Arquivos de teste e pastas novos são listados no relatório de cada brief e consolidados na árvore (seção 2) e na seção 2.4 pelo brief 023, antes do ensaio.

## Consequência

Nenhuma destas decisões muda o que o MVP mede nem um valor declarado. Mudança numa delas é feita por brief que a declare, com novo registro de decisão.
