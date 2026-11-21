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
| Teto de saída do conferente local (a configuração não tem `[tarefas.conferente_local]`) | 2000 tokens, constante em `fabrica/conferencia/local.py` | 017 |
| Lista oficial dos códigos de banco para o detector | Vazia: nenhum código é acusado | 009, 017 |
| Manifestação do ensaio passa pelo conferente local só se a casa 1 for uma das 2 sorteadas | Sem exceção para o ensaio | 017 |
| Veredito da categoria formato: o condutor grava só o destino `reprovada_formato` e encerra a versão antes da etapa de decisão | O destino é a fonte; `decisao.veredito_de_formato` monta o veredito para quem lê o destino (relatório do 023) | 018 |
| O Opus, no risco alto, recebe as respostas do Haiku e do modelo local? | Não: só na discordância ele as recebe; no risco alto e no médio sem local responde sozinho | 018 |
| Citação não resolvida que o checklist responde "não passa" | Reprova pelo item `citacao_fora_da_tabela` | 018 |
| Peça aprovada em modo de teste vai para `saida/aprovadas/`? | Não (só fora do modo de teste) | 018 |
| Semelhança com mais de uma aprovada do tipo | Vale o maior índice; texto com menos de 5 palavras vira um trecho só | 018 |
| `juizo_trocado` nos embargos: "Tribunal de Justiça do Estado de <estado da ficha>" | O estado vai pela sigla da UF da ficha (os dados não têm o nome por extenso dos estados) | 019 |
| "Bloco de fundamentos" onde entra a frase do `termo_inequivoco` | O primeiro presente entre `fundamentos`, `razoes`, `novo_endereco` e `exposicao` (os embargos e a manifestação não têm bloco `fundamentos`) | 019 |
| `valor_trocado` nos embargos "com valor na decisão" | Só quando a extração da original traz algum valor da ficha; sem valor, os embargos recebem outro erro de regra | 019 |
| Erro de regra sorteado que não cabe na peça (por exemplo, sem citação para trocar) | O sorteio só oferece a cada peça os erros que cabem nela; a peça em que nenhum cabe fica sem cópia por programa | 019 |
| Nomes dos cartões de amostra e de leitura | `saida/cartoes/<rodada>_amostra_copias.md`, `<rodada>_amostra_descartadas.md` e `<peça>_v<k>_leitura_publicacao.md`; o do ensaio, `<peça>_ensaio.md`; as amostras sorteadas em `saida/erros/<rodada>_amostras.json` | 020 |
| Peça com "sim" na pergunta de dado real (no cartão ou na leitura) | Não é publicada | 020 |
| Versão publicada no ensaio | A aprovada pela fábrica; sem versão aprovada, a primeira | 020 |
| `publicar` rodado de novo | Não regrava o que já existe (nem o índice) | 020 |
| Respostas das amostras: `dado_real` | Gravado como "não", porque a pergunta não é feita nesses cartões | 020 |
| `avancar` também coleta as cópias do banco (fora da parte de `__main__.py` que o brief libera) | `avancar` chama `erros_plantados.coletar_banco`; o `erros` só grava pedidos e sorteia | 021 |
| Quantas vezes a vaga do Opus troca de tipo | Uma troca, com duas tentativas no tipo novo; depois a vaga fica perdida | 021 |
| "Troca muda mais de uma região" | Medido por linhas; a fração da região é a maior entre a parte tirada e a posta | 021 |
| Cópia com resposta fora do formato duas vezes | Descartada com motivo vazio (`programa` antes do Sonnet; `verificador` no Sonnet), fora da amostra | 021 |
| Item `estilo` na lista do Sonnet | Fica (o brief só tira `semelhanca` e `marca`) | 021 |
| O Opus recebe a ficha? | Não: recebe o tipo do erro, a descrição, se é sutil e a primeira versão da original | 021 |
| Marca do critério central inconclusivo e da faixa média do plano B | Ocorrência no registro (`criterio_central_inconclusivo`, `plano_b_faixa_media`) | 021 |
| Custo das descartadas à parte | Ocorrência `custo_copia_descartada` por descarte; as chamadas do banco têm `peca` `<cópia>_banco` | 021 |

## Briefs que esperam o computador

| Ponto | Provisório em uso | Brief |
|---|---|---|
| Ensaio de três peças (gasta API e usa o modelo local) | Não executado | 024 |
| Rodada do MVP | Não executada | 025 |
