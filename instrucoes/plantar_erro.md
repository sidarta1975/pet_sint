# Cópia com erro

Você vai criar uma cópia de uma peça processual brasileira fictícia, escrita para treino de modelos de linguagem, com um erro plantado de propósito. A cópia serve para testar se os conferentes da fábrica acham o erro. Junto com esta instrução, você recebe, em JSON, o erro pedido (o tipo, o que ele é e se deve ser sutil ou direto) e o texto inteiro da peça original.

## O que fazer

- Plante na peça um único erro, do tipo pedido, e só ele. Não corrija nem melhore nada do resto.
- Quando o pedido disser sutil (`"sutil": true`), o texto com o erro continua bem escrito e convincente, no mesmo tom da peça, e o erro só aparece para quem confere com atenção.
- Quando o pedido disser direto (`"sutil": false`), o erro pode ser visível numa leitura atenta, mas o texto continua sendo uma peça plausível.
- Mude um só trecho contínuo da peça, o menor que basta para o erro, e nunca mais de um quarto do texto.
- Não toque na primeira linha da peça, nos títulos dos blocos nem nos marcadores de nome e de OAB.
- Não use nome, documento, endereço ou número de processo reais. Os dados da peça são fictícios e continuam fictícios.

## O que devolver

- Não devolva a peça inteira. Devolva só o trecho original e o trecho novo que o substitui.
- O trecho original é copiado literalmente da peça, letra por letra, com a mesma pontuação e os mesmos espaços, e precisa aparecer uma única vez no texto. Escolha um trecho longo o bastante para não se repetir.
- O trecho novo é o texto que entra no lugar do trecho original, já com o erro.

## Formato

Responda só com o JSON no esquema pedido, sem comentário antes ou depois.

# Verificação da cópia

Você vai comparar uma peça processual brasileira fictícia com uma cópia dela em que um trecho foi trocado. Junto com esta instrução, você recebe, em JSON, a lista dos itens de conferência que valem para o tipo da peça, cada um com a sua pergunta, e os dois textos: a original e a cópia.

## O que fazer

- Ache o que mudou da original para a cópia e diga se a mudança criou um erro na peça.
- Se criou, escolha na lista recebida o item que o erro viola e descreva o erro numa frase curta, citando o trecho da cópia.
- Escolha só entre os itens da lista. Se a mudança não criou erro nenhum, não aponte item.
- Diga também se a troca criou algum outro problema além desse erro, como um texto truncado, uma frase sem sentido, um erro de português ou um segundo erro jurídico, e descreva esse problema.
- Julgue pela peça e pela lista. Não suponha o que a pessoa que fez a cópia quis fazer.

## Formato

Responda só com o JSON no esquema pedido, sem comentário antes ou depois. Sem item apontado, o campo do item fica nulo.
