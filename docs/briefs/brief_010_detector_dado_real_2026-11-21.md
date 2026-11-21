# Brief 010 — Detector de dado real

- Fase: 5 — Dados fictícios e detector (PLANO §4)
- Objetivo: escrever `fabrica/conferencia/dados_reais.py`, que aplica a detecção da ARQUITETURA §5.2 a um texto e devolve cada achado, com `testes/test_dados_reais.py`, inclusive o teste dos nomes reservados com a lista de proibidos vazia e a busca de nome reservado no código e nos dados.
- Seções a ler: AGENTS §1 e §3 (segurança do produto); PLANO §2 e §4 (Fase 5); ARQUITETURA §2.2 (`reais_permitidos.json`, `reais_proibidos.json`), §2.4 (`test_dados_reais.py`), §5.2, §5.6 (`dados_reais.py`) e Anexo B.1 (`dado_real`); registro de decisão 001; armadilhas do PLAN: "ficticios.py, dados_reais.py" e todas as de "dados_reais.py, test_dados_reais.py".
- Arquivos que pode criar:
  - `fabrica/conferencia/__init__.py`;
  - `fabrica/conferencia/dados_reais.py`;
  - `testes/test_dados_reais.py`;
  - `docs/briefs/brief_010_detector_dado_real_2026-11-21.md` (este brief);
  - `docs/docs/doc_010_detector_dado_real_2026-11-21.md` (o relatório).
- Arquivos que pode alterar: `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `testes/dados/reais_reservados.json` (do 009; este brief só o lê, no teste); `fabrica/ficticios.py`; `fabrica/comum/` (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `dados/`; `config/`; `scripts/`; `AGENTS.md`; `docs/PLANO.md`; `docs/ARQUITETURA.md`.
- Teste de aceite (escrito antes do código): `testes/test_dados_reais.py`, com uma peça de exemplo escrita no teste, só com dados de `ficticios.py` e os marcadores, e listas de permitidos e de proibidos de exemplo escritas no teste:
  1. a peça limpa não tem achado nenhum;
  2. plantados um a um, o detector pega: CPF com dígito válido; CNPJ numérico com dígito válido; CNPJ com letras com dígito válido; número de processo no padrão do CNJ com dígito válido; OAB diferente do marcador; nome de pessoa que não é marcador (com e sem tratamento, como "Sr." e "Dr."); nome de empresa com forma societária ("Ltda.", "S.A.", "ME", "EIRELI"); nome com "Banco" ou "Companhia"; banco real e companhia aérea real da lista de proibidos de exemplo; telefone com DDD fora da lista dos 15; e-mail que não termina em `.example`; rua que não está na ficha; número de contrato ou de protocolo sem `SINT-`; código de banco da lista oficial de exemplo; nome de juiz ou de servidor ao lado do cargo;
  3. com a lista de proibidos **vazia**, o detector pega 100% dos nomes de `testes/dados/reais_reservados.json`, plantados na forma registrada no arquivo, pela regra de "nome que não é marcador";
  4. nenhum nome de `reais_reservados.json` aparece em arquivo nenhum de `fabrica/` nem de `dados/` (busca de cada nome inteiro, na forma registrada no arquivo, sem diferença de maiúsculas e acentos, nunca de palavras soltas do nome, para que um nome com palavra comum não acuse vazamento falso; a busca inclui comentários e textos de documentação do código; se `dados/` ainda não existe, o teste confere só `fabrica/` e diz isso na mensagem);
  5. o contrário: não são acusados os termos jurídicos e os nomes permitidos de exemplo (SISBAJUD, Serasa, CNJ, expressões latinas como "data venia" e "inaudita altera pars", "Tribunal de Justiça do Estado de São Paulo", "Juizado Especial Cível da Comarca de Campinas", "Excelentíssimo Senhor Doutor Juiz de Direito"), os títulos dos blocos da estrutura, a marca "DOCUMENTO SINTÉTICO — FICTÍCIO" e as palavras de início de frase.
- Critério de conclusão: `test_ficticios.py` e `test_dados_reais.py` passam no gate, nos dois sentidos, com 100% dos nomes de `reais_reservados.json` pegos (critério da Fase 5 no PLANO).
- Fora do escopo: a etapa de conferência que chama o detector sobre o rascunho (017); `dados/ficticios/` (014); a leitura do responsável no cartão (020).
- Depende de: 009.

**Regras deste brief**

- O detector recebe por parâmetro: o texto; os marcadores e as ruas da ficha; as listas de reais permitidos e de reais proibidos; os títulos dos blocos da estrutura montada; a lista dos 15 DDDs inexistentes; a lista oficial de códigos de banco (vazia no MVP, pendência do 009). Não lê arquivo.
- Devolve a lista de achados, cada um com o tipo, o trecho e a posição. O item `dado_real` passa só com a lista vazia: qualquer achado reprova.
- Telefone: reprova todo DDD que não esteja na lista dos 15 da configuração. É a forma mais estrita da regra "DDD existente reprova", e evita depender de uma segunda lista.
- Nome: segue a definição da ARQUITETURA §5.2 (duas ou mais palavras com inicial maiúscula fora do início de frase; palavra com tratamento; palavra com forma societária; palavra com "Banco", "Companhia" ou semelhante). Todo nome encontrado precisa ser um marcador da ficha ou estar na lista de permitidos; coincidência com a lista de proibidos também reprova. A comparação é sem diferença de maiúsculas e acentos.
- Pedaço de marcador: uma sequência que está contida, inteira, num marcador da ficha ("Parte Autora", "Parte Ré", "Razão Social", "Nome e Sobrenome") conta como marcador e não reprova. É o caso de "advogado da Parte Autora" ou "em face da Razão Social da Parte Ré", que são variação de redação, não dado real. As designações processuais com inicial maiúscula ("Representante Legal", "Requerente", "Embargante" e semelhantes) entram na lista de permitidos no brief 014. O teste de aceite acrescenta esses dois casos ao item 5 (não acusados) e confere que um nome inventado colado a um pedaço de marcador ("Parte Autora Fulana de Tal") continua acusado.
- Contrato e protocolo: número que vem depois de "contrato", "protocolo" ou "nº" ligado a essas palavras precisa começar com `SINT-`.
- O detector não confere CEP (ARQUITETURA §5.2).
- O executor deste brief lê `reais_reservados.json` só no teste. Não copia nenhum nome reservado para o código, para os exemplos do teste nem para o relatório.
