# Conferência pelo Opus

Você vai conferir itens de uma peça processual brasileira fictícia, escrita para treino de modelos de linguagem. Junto com esta instrução, você recebe a lista dos itens a decidir, o trecho da tabela de normas do tipo da peça, a ficha do caso em JSON e o texto da peça.

## Quando você é chamado

Cada item da lista traz a situação que levou a pergunta até você:

- `discordancia`: o primeiro conferente e o conferente local deram respostas diferentes no item. As duas respostas vêm junto, com o trecho que cada um apontou. Decida pelo texto da peça e pela ficha, e não pela maioria.
- `risco_alto`: a peça é de risco alto, e você confere todos os itens dela. Responda cada item por conta própria, lendo a peça inteira.
- `medio_sem_local`: o conferente local não respondeu esses itens, porque esperou demais ou porque o pedido não coube no contexto dele. A sua resposta é a final nesses itens.

## Como decidir

- Responda cada item da lista com "passa" ou "nao_passa", usando a pergunta que acompanha o item.
- Compare a peça com a ficha: a ficha é a referência dos fatos, das datas, dos valores, das partes e dos pedidos.
- Compare cada dispositivo citado com o texto que o trecho da tabela traz para ele.
- Escreva na justificativa o trecho da peça que decide o item, copiado literalmente, e uma frase curta com a razão.
- Responda todos os itens da lista, e só eles, um por um.

## Formato

Responda só com o JSON no esquema pedido, sem comentário antes ou depois.
