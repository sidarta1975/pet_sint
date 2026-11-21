# Extração da peça

Você recebe o texto de uma peça processual fictícia. Extraia dela, sem julgar nada, o que o formato de resposta pede. Copie cada texto como aparece na peça.

- `nomes`: cada nome de pessoa ou de empresa, com o papel (autor, réu, advogado ou outro).
- `documentos`: CPF, CNPJ, OAB, número do processo, protocolos, contratos e CEP, com o tipo e o texto.
- `valores`: só quantias em dinheiro. Prazos em dias, quantidades e limites escritos em salários mínimos não entram. Cada valor leva o texto como aparece, os centavos e o lugar: `fatos` (a narrativa), `pedido` (o bloco dos pedidos, com o id do pedido a que pertence), `valor_causa` (só o bloco formal do valor da causa) ou `outro` (o resto, inclusive a fundamentação da competência). Quando a peça escreve o mesmo valor em algarismos e por extenso, ponha os dois no `texto` e, em `centavos`, o valor escrito por extenso.
- `datas`: cada data com o texto e a data completa (ano-mês-dia) ou parcial (ano-mês).
- `comarca` e `juizo`: como aparecem no endereçamento.
- `pedidos`: cada pedido classificado numa natureza da lista do tipo, que vem junto com a peça, ou como `outro` quando não cabe em nenhuma, com o texto do pedido.
- `pecas_anteriores`: as peças e decisões anteriores que a peça menciona.
- `data_peca`: a data da assinatura.

Responda só com o JSON no formato pedido.
