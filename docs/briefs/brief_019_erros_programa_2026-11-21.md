# Brief 019 — Erros por programa

- Fase: 9 — Erros por programa (PLANO §4)
- Objetivo: escrever a parte de `fabrica/erros_plantados.py` que não usa modelo (uma cópia por programa para cada peça boa, com erro de regra ou de julgamento, e o seu gabarito) e o comando `erros`, com `testes/test_erros_programa.py`.
- Seções a ler: AGENTS §4 e §8; PLANO §4 (Fase 9); ARQUITETURA §1.3 (erros plantados), §2.4 (`test_erros_programa.py`), §5.1, §5.7, §5.12.7, Anexos C.1, C.2, C.4 e D; registro de decisão 001 (itens 16 e 17); armadilhas do PLAN: "teste_conferentes.py".
- Arquivos que pode criar:
  - `fabrica/erros_plantados.py`;
  - `testes/test_erros_programa.py`;
  - `docs/briefs/brief_019_erros_programa_2026-11-21.md` (este brief);
  - `docs/docs/doc_019_erros_programa_2026-11-21.md` (o relatório).
- Arquivos que pode alterar:
  - `fabrica/__main__.py` — o comando `erros`;
  - `docs/ARQUITETURA.md` — seção 8, a linha do comando `python -m fabrica erros --rodada <rodada>`;
  - `docs/PLAN.md` (Resumo, Doing, Backlog e Done).
- Arquivos que não pode tocar: `dados/`; `config/`; os demais módulos (a não ser por defeito comprovado (registro de decisão 001, item 19), registrado no relatório); `scripts/`; `AGENTS.md`; `docs/PLANO.md`.
- Teste de aceite (escrito antes do código): `testes/test_erros_programa.py`, com peças, extrações, fichas e tabela de exemplo em pasta temporária:
  1. cada erro de regra do Anexo C.1 é gerado em peças de exemplo dos tipos a que se aplica, e os programas de regra o pegam no item principal (o teste monta a extração da cópia aplicando à extração da original a mesma troca, que é o que um extrator correto devolveria);
  2. em 1.000 sementes, o valor trocado nunca é igual a um valor, a uma soma de valores dos pedidos, ao valor da causa ou a um valor de referência legal, e difere de cada um em mais de 1%; a data trocada nunca é uma data da ficha e cai em outro mês; o valor trocado também muda o extenso, quando a peça o traz;
  3. a função trocada troca um dispositivo citado por outro do mesmo diploma e do mesmo assunto, com função diferente, de dentro do trecho do tipo, e `citacoes.py` não a reprova;
  4. o sorteio dá a função trocada a metade das peças boas, arredondada para baixo, escolhidas primeiro entre as que citam dispositivo com par; se menos da metade tem par, todas as que têm recebem; o tipo sem nenhuma peça com par fica com zero cópias de julgamento; as outras recebem um erro de regra que se aplica ao tipo; tudo igual com a mesma semente;
  5. cada cópia muda uma só região e o resto fica idêntico à primeira versão da peça boa; a marca continua no topo;
  6. o gabarito de cada cópia tem origem, tipo de erro, item principal e itens aceitos tirados do catálogo, criador `programa` e amostra vazia;
  7. só peças boas (ficha e peça aprovadas pelo responsável) recebem cópia na rodada `rNN`; no ensaio `eNN`, as três peças recebem, qualquer que seja o veredito.
- Critério de conclusão: `test_erros_programa.py` passa no gate (critério da Fase 9 no PLANO).
- Fora do escopo: as cópias do Opus, a verificação do Sonnet e as amostras (021); o teste dos conferentes (022); o cartão de revisão (020).
- Depende de: 018.

**Regras deste brief**

- **Peça boa** (ARQUITETURA §5.12.7): ficha aprovada e peça aprovada nas respostas confirmadas do cartão (`saida/cartoes/<id>_respostas.json`, formato de `formatos.py`). Este brief lê as respostas pelo formato; o cartão é construído no 020. No ensaio, a base são as três peças (registro de decisão 001, item 17).
- **Base de cada cópia**: a primeira versão da peça boa. O trecho a trocar é achado pelo texto que a extração da original devolveu.
- **Erros de regra** (Anexo C.1), com estes textos fixos onde o anexo pede texto pronto:
  - `juizo_trocado`: na inicial, "Vara da Fazenda Pública da Comarca de <comarca da ficha>"; nos embargos, "Tribunal de Justiça do Estado de <estado da ficha>"; na manifestação, "Juizado Especial Cível da Comarca de <outra comarca da lista>";
  - `termo_inequivoco`: insere, no fim do bloco de fundamentos, a frase "Ressalte-se, por fim, <termo>." com um termo de `termos_inequivocos.json`;
  - `pedido_incompativel_com_rito`: insere no bloco de pedidos um pedido pronto da lista do tipo em `listas_ficticias.json`;
  - `valor_trocado` e `acima_da_alcada`: trocam algarismos e, se houver, o extenso, escrito por uma função de número por extenso em português do próprio módulo;
  - `data_trocada`, `fora_do_prazo` e `citacao_fora_da_tabela`, como no anexo.
- **Nomes dos arquivos**: a cópia por programa é `saida/erros/<peça>_erro1_1.md` (vaga 1, tentativa 1), com o gabarito em `saida/erros/<peça>_erro1_1_gabarito.json`. As vagas 2 em diante são do Opus (021).
- **Comando `erros --rodada <rodada>`**: grava as cópias por programa das peças boas que ainda não as têm; é retomável e não refaz o que já existe. O brief 021 acrescenta as cópias do Opus ao mesmo comando.
