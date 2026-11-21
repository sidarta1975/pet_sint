# Pendências para definir no computador

Lista única dos pontos que pedem uma decisão ou um comando do responsável. Enquanto ele trabalha pelo celular, cada brief segue com o valor provisório que o próprio brief declara (decisão tomada por falta de resposta). Pedido do responsável em 2026-11-21: "Coloque resoluções provisórias e registre esses pontos para serem definidos quando eu estiver no computador".

Cada linha: o ponto, o valor provisório em uso e o brief onde ele aparece. Nada aqui é regra nova: quando o responsável definir, uma sessão troca o valor no arquivo indicado e risca a linha.

## Comandos na máquina do responsável

| Ponto | Provisório em uso | Brief |
|---|---|---|
| Rodar o gate (`scripts/verificar.sh`) na máquina dele | O gate roda só na nuvem | 001 |
| Os 5 comandos da conferência da máquina (Python, Ollama, porteiro, memória, disco) | Nenhum rodou; o modelo local é tratado como indisponível | 002 |
| Chave da API em `ANTHROPIC_API_KEY` | Sem chave: `ensaio` e `fichas` só gravam pedidos; `avancar` para pedindo a chave | 002, 015 |
| `python -m fabrica preparar` na máquina, para ver `saida/preparacao/<tipo>_estrutura.md` | Rodou só na nuvem (sai sem erro) | 014 |

## Valores do `config/config.toml`

| Ponto | Provisório em uso | Brief |
|---|---|---|
| `modelo_local.etiqueta_completa` e `modelo_local.digest` do `gemma3:27b` | Vazios: modelo local indisponível, vale a válvula de escape | 002 |
| Janela da conferência local (`janela_local.inicio` e `fim`) | 22:00 às 06:00 | 002 |
| Data da conferência da lista de DDDs inexistentes | 2026-11-21 | 002 |
| Quantidade de peças por tipo | 10 | 002 |

## Dados de `dados/`

| Ponto | Provisório em uso | Brief |
|---|---|---|
| Conferir os 56 textos de lei da tabela de normas na fonte oficial (o Planalto não abriu da nuvem) | Textos de memória, marcados "a conferir na fonte" | 014 |
| Aprovar cada arquivo de `dados/` pelo roteiro do relatório do 014 | Aprovação antecipada ("Aprovo pode seguir até o fim de todos os briefs sem mais aprovação futuras") | 014 |
| Faixas de CEP das 12 cidades | De memória, a conferir | 014 |
| Carnaval, Sexta-feira da Paixão e Corpus Christi como feriado | Fora da lista (não são feriado nacional por lei federal) | 014 |
| Dias de eleição (4 e 25 de outubro de 2026) como feriado | Dentro da lista | 014 |
| Recesso do art. 220 do CPC (20/12 a 20/01) | A contagem de prazo não o trata; as datas do MVP ficam até agosto para o ajuizamento | 014 |
| Itens de conferência por tipo em `tipos.json` | Os que o relatório do 014 lista (item 3 das pendências) | 014 |

## Regras do programa

| Ponto | Provisório em uso | Brief |
|---|---|---|
| `preparar` não roda duas vezes seguidas (não sobrescreve `saida/preparacao/`) | Apagar `saida/preparacao/` antes de rodar de novo | 014 |
| Prazo da determinação judicial na manifestação | Sorteado entre "não fixado" (5 dias úteis), 10 e 15 dias úteis | 015 |
| Prazo pedido na ciência e prazo | Sorteado entre 10, 15, 20 e 30 dias | 015 |
| Resposta da ficha fora do formato duas vezes | Descarte e ficha nova na casa, sem o retorno com motivo | 015 |
| Número da ficha nova da casa | O seguinte do tipo na rodada (011, 012...; no ensaio, 002, 003) | 015 |
| Rodar `preparar` antes do `ensaio`: a redação lê a estrutura de `saida/preparacao/<tipo>_estrutura.json` | Sem a estrutura, `avancar` para na redação com o arquivo que falta | 016 |

## Briefs que esperam o computador

| Ponto | Provisório em uso | Brief |
|---|---|---|
| Ensaio de três peças (gasta API e usa o modelo local) | Não executado | 024 |
| Rodada do MVP | Não executada | 025 |
