# Ficha do caso fictício

Você vai criar o caso fictício de uma peça processual brasileira, para treino de modelos de linguagem. Tudo é inventado: nenhum fato, nome, número ou documento pode ser de um caso real.

## O que você recebe

Junto com esta instrução, você recebe a base da ficha, em JSON, montada pelo programa. Ela traz o tipo da peça, a casa da matriz (matéria, tese principal, polo, complexidade, momento e estilo), o processo, as partes, o advogado, as datas, os identificadores SINT- e, conforme o tipo, o defeito da decisão, o motivo da devolução do aviso e o pedido. Recebe também o trecho da tabela de normas do tipo, com o identificador de cada dispositivo entre colchetes.

Não mude nada da base. Use só os marcadores de nome, os identificadores SINT- e as datas que ela traz.

## O que você escreve

Escreva só os campos do formato de resposta pedido, e nada mais:

- `fatos`: os fatos do caso, em ordem de data, cada um com a data, uma descrição curta e os ids dos valores que ele usa. Nenhum fato pode ser anterior ao campo `limite_fatos` da base nem posterior à data de ajuizamento.
- `valores`: todo valor em dinheiro que a peça vá usar, em centavos, inclusive somas, dobros e totais. A peça não poderá escrever valor que não esteja nesta lista.
- `provas`: os documentos do caso, cada um com um dos identificadores SINT- recebidos.
- `pedidos`: cada pedido com uma natureza da lista fechada do tipo e, quando tiver valor, o id do valor.
- `valor_causa`: na petição inicial, o id do valor igual à soma dos valores dos pedidos (art. 292, VI, do CPC); no dano moral, o valor pretendido entra nessa soma (art. 292, V). Nos embargos e na manifestação, deixe vazio.
- `fundamentos`: os identificadores dos dispositivos do trecho da tabela que sustentam o caso. Nunca use dispositivo fora do trecho recebido.
- `momento_processual.ultima_decisao`: um resumo curto da última decisão do processo, ou "nenhuma" na petição inicial.
- `pecas_anteriores`: as peças anteriores que importam, com tipo, data e resumo.

## Valores proibidos

Nenhum valor da ficha pode ser igual a R$ 1.621,00 (o salário mínimo de 2026) nem a R$ 64.840,00 (a alçada do juizado). Na petição inicial, o valor da causa não pode passar de R$ 64.840,00.

## Embargos de Declaração

Escreva a decisão fictícia que os embargos vão atacar, com o tipo de decisão e a data da base, o juízo do processo, o relatório só na sentença, a fundamentação e o dispositivo. Escreva pelo menos 3 argumentos das partes, apresentados antes da decisão, cada um com id, parte, peça de origem e texto.

A decisão precisa ter o defeito pedido na base, e a âncora do defeito segue estas regras:

- contradição, obscuridade ou erro material: a âncora tem origem "decisao" e o trecho literal, copiado letra por letra, da fundamentação ou do dispositivo;
- omissão total: a âncora tem origem "argumento", o id do argumento e um trecho literal dele; a decisão ignora esse argumento, e as palavras próprias do trecho quase não aparecem na fundamentação nem no dispositivo;
- omissão parcial: como na omissão total, e mais o `trecho_mencao`, trecho literal da decisão, de no máximo 40 palavras, que menciona o argumento sem enfrentá-lo; fora dessa menção, a decisão não volta ao argumento.

O trecho da âncora precisa ter palavras próprias do argumento, que não sejam o assunto geral do caso nem apareçam nos fatos ou nos outros argumentos. Descreva o defeito em uma frase e diga se a correção mudaria o resultado.

## Proibições

É proibido usar dado real de qualquer tipo, nome de pessoa ou de empresa além dos marcadores recebidos, e nome de juiz, de servidor ou de membro do Ministério Público: use só o cargo.

## Formato

Responda só com o JSON no formato pedido, sem texto antes ou depois.
