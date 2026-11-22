# Brief 009 — Dados fictícios e nomes reservados do teste

- Fase: 5 — Dados fictícios e detector (PLANO §4)
- Objetivo: escrever `fabrica/ficticios.py`, que cria por programa todos os dados que nunca podem ser reais (ARQUITETURA §5.2), com `testes/test_ficticios.py` e listas de exemplo dentro do teste, e criar `testes/dados/reais_reservados.json`, à parte e antes do detector.
- Seções a ler: AGENTS §1 (nunca dado real) e §3 (segurança do produto); PLANO §2 e §4 (Fase 5); ARQUITETURA §2.2 (`listas_ficticias.json`, `reais_proibidos.json`), §2.4 (`test_ficticios.py`), §5.2, §5.4 e Anexo A.1; registro de decisão 001; armadilhas do PLAN: todas as de "ficticios.py" e as duas de "dados_reais.py, test_dados_reais.py".
- Arquivos que pode criar:
  - `fabrica/ficticios.py`;
  - `testes/test_ficticios.py`;
  - `testes/dados/reais_reservados.json`;
  - `docs/briefs/brief_009_ficticios_2026-11-21.md` (este brief);
  - `docs/docs/doc_009_ficticios_2026-11-21.md` (o relatório).
- Arquivos que pode alterar: `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `fabrica/comum/` (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `dados/` (nasce só no 014); `config/`; `scripts/`; `AGENTS.md`; `docs/PLANO.md`; `docs/ARQUITETURA.md`.
- Teste de aceite (escrito antes do código): `testes/test_ficticios.py`, com uma lista de exemplo de ruas, bairros, cidades (com estado e faixa de CEP) e profissões escrita dentro do teste, e uma semente fixa:
  1. gera 5.000 CPFs e 5.000 CNPJs: nenhum tem dígito verificador válido (o teste tem o seu próprio cálculo do dígito, inclusive o do CNPJ com letras, cada caractere valendo o código ASCII menos 48, com os mesmos pesos e o mesmo resto da divisão por 11);
  2. gera 5.000 números de processo no padrão do CNJ para juízos de exemplo: o ramo é o da Justiça Estadual (8), o tribunal é o do estado do juízo, e o dígito verificador é sempre inválido (o teste calcula o oficial, pelo resto da divisão por 97);
  3. gera 5.000 telefones: todo DDD está na lista dos 15 DDDs inexistentes da configuração e nenhum está entre os 67 em uso (o teste traz a lista dos 67, copiada da ARQUITETURA §5.2);
  4. todo e-mail termina em `.example`;
  5. todo nome de parte e de advogado é exatamente o marcador do papel e da categoria, e toda OAB é exatamente "OAB/UF nº 000.000";
  6. todo endereço tem rua e bairro da lista de exemplo, cidade real da lista e CEP dentro da faixa da cidade;
  7. todo número de contrato ou de protocolo começa com `SINT-`;
  8. todo código de banco gerado está fora de uma lista oficial de exemplo, não vazia, escrita no teste e recebida pela função (o teste não passa por lista vazia);
  9. a mesma semente gera os mesmos dados, e sementes diferentes geram dados diferentes.
- Critério de conclusão: `test_ficticios.py` passa no gate (metade do critério da Fase 5 no PLANO) e `testes/dados/reais_reservados.json` existe com o conteúdo pedido abaixo.
- Fora do escopo: o detector de dado real (010); `dados/ficticios/` (nasce no 014); juntar os dados numa ficha (015); qualquer chamada a modelo.
- Depende de: 003.

**Regras deste brief**

- Os marcadores são fixos e exatos: "Nome e Sobrenome da Parte Autora" e "Nome e Sobrenome da Parte Ré" para pessoa física; "Razão Social da Parte Autora" e "Razão Social da Parte Ré" para todas as outras categorias; "Nome e Sobrenome do Advogado"; "OAB/UF nº 000.000". Nunca se sorteia nome.
- Número do processo: `NNNNNNN-DD.AAAA.J.TR.OOOO`, com `J` = 8 (Justiça Estadual, que julga os três tipos do MVP), `TR` = código do tribunal do estado do juízo, recebido de uma tabela por parâmetro (no 014, a tabela fica em `listas_ficticias.json`), `OOOO` = unidade sorteada de quatro dígitos, e `DD` sempre diferente do dígito oficial. O ano é o da data de ajuizamento da ficha.
- Identificadores do caso: `SINT-<ano>-<seis dígitos>`.
- Telefone: `(<DDD>) 9<quatro dígitos>-<quatro dígitos>`, com o DDD da lista da configuração.
- E-mail: partes e escritório com domínio terminado em `.example`; a parte antes da arroba é sempre genérica (por exemplo, `parte.autora`, `parte.re`, `escritorio`), nunca tirada de nome.
- Código de banco: a função recebe a lista oficial de códigos por parâmetro e sorteia um código fora dela. Os canônicos não põem essa lista em `dados/`, e nenhum dos 3 tipos do MVP usa dados bancários (ARQUITETURA §5.2): a lista real fica como pendência do relatório, sem bloquear o brief.
- Tudo é gerado a partir de um gerador aleatório criado com a semente recebida por parâmetro; nenhum sorteio usa o gerador global.
- `ficticios.py` não lê arquivo: recebe as listas por parâmetro.

**Conteúdo de `testes/dados/reais_reservados.json`**

- Validado pelo modelo `ReaisReservados` de `formatos.py` (nome e forma como aparece numa peça).
- Pelo menos 20 nomes de empresas reais, de setores que costumam aparecer em processos de consumo (bancos, companhias aéreas, operadoras de telefonia e internet, varejistas e outras). Preferir empresas conhecidas que não sejam as maiores de cada setor, para que as maiores possam ficar em `reais_proibidos.json`, que o brief 014 propõe e que nunca pode conter um nome reservado.
- A forma de cada nome é a que um redator escreveria na peça: razão social com a forma societária ("... S.A.", "... Ltda.") ou nome com duas ou mais palavras de inicial maiúscula. É a forma que a regra de "nome que não é marcador" cobre (ARQUITETURA §5.2). Nomes de uma palavra só, sem forma societária, ficam de fora, e o relatório registra isso como limite conhecido da regra, não do teste.
- Nenhum desses nomes pode aparecer em `fabrica/` nem em `dados/`. O próprio executor deste brief não os escreve em nenhum outro arquivo, nem no relatório (o relatório diz só quantos nomes há e de que setores).
