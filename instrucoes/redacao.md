# Redação da peça

Você vai escrever uma peça processual brasileira fictícia, para treino de modelos de linguagem. Junto com esta instrução, você recebe a estrutura montada do tipo da peça, o trecho da tabela de normas do tipo e a ficha do caso, em JSON.

## Como escrever

- Siga os blocos da estrutura na ordem em que aparecem. Comece cada bloco com o seu título como título de segundo nível do Markdown, exatamente assim: `## <título do bloco>`. Os blocos opcionais só entram quando a ficha pede o que eles tratam.
- Cite só dispositivos que estão no trecho da tabela, com o texto que a tabela traz. Nunca cite artigo, súmula ou lei fora do trecho recebido.
- Não invente fato fora da ficha. Use as datas, os documentos, os identificadores SINT- e as peças anteriores como estão na ficha.
- Não calcule valor novo. Escreva só os valores de `valores[]` da ficha, em algarismos e, se quiser, também por extenso.
- Não use nome de pessoa ou de empresa além dos marcadores da ficha, como "Nome e Sobrenome da Parte Autora", "Razão Social da Parte Ré", "Nome e Sobrenome do Advogado" e "OAB/UF nº 000.000".
- Não dê nome a juiz, a servidor ou a membro do Ministério Público: escreva só o cargo.
- Não escreva a linha de marca de documento sintético, porque o programa a põe no topo.
- Siga o estilo da casa da matriz: no estilo conciso, frases curtas e só o necessário; no estilo detalhado, a argumentação completa, sempre ligada aos fatos do caso.

## Refação

Quando houver um motivo de reprovação depois da ficha, corrija o que o motivo aponta e não mude o que não foi apontado. Escreva a peça inteira de novo, com a mesma estrutura.

## Formato

Responda só com o texto da peça, em Markdown, sem comentário antes ou depois.
