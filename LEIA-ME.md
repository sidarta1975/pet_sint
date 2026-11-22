# LEIA-ME — Petições Sintéticas

Este arquivo é a versão inicial (brief 001). O detalhe de cada ponto está nos documentos de `docs/`, citados em cada seção.

## O que é a fábrica

Um programa que gera petições fictícias do direito brasileiro, típicas de advogados autônomos, para servir de modelo e de dado de treino de inteligência artificial. A fábrica **só gera peças fictícias** e **nunca recebe dados reais** de pessoa, empresa privada, documento, endereço ou processo. Ela não atende caso real. Detalhe: `docs/PLANO.md`, seções 1 e 2.

## O que pode e o que não pode ser real

**Pode ser real**, porque é público ou necessário: tribunais, varas, juizados e comarcas; cidades e estados, inclusive o CEP da cidade; entes públicos (União, estados, municípios, INSS e outros); sistemas e cadastros do processo (SISBAJUD, RENAJUD, Serasa e outros); órgãos e siglas institucionais (CNJ, OAB, Ministério Público, Defensoria); leis, códigos, artigos e expressões latinas de uso jurídico; cargos e formas de tratamento forense; o salário mínimo.

**Nunca é real**, e é criado pelo programa:

- nomes das partes e do advogado: sempre marcadores fixos, como "Nome e Sobrenome da Parte Autora" ou "Razão Social da Parte Ré";
- OAB: sempre "OAB/UF nº 000.000";
- CPF, CNPJ e número de processo: formato certo, com o dígito verificador propositalmente errado;
- telefone: só com DDD que não existe no país;
- e-mail: sempre terminado em `.example`;
- endereço: rua inventada em cidade real;
- contratos e protocolos: sempre começando por `SINT-`.

Um detector confere cada peça, e qualquer dado que pareça real reprova a peça. Detalhe: `docs/ARQUITETURA.md`, seção 5.2.

## Como rodar

Precisa de Python 3.12. Para instalar as bibliotecas, nas versões fixas do `pyproject.toml`:

```
python3.12 -m venv .venv
. .venv/bin/activate
pip install anthropic==2.12.0 pydantic==2.14.4 python-docx==1.2.0 pytest==9.2.0 ruff==0.17.6 mypy==2.4.1
```

- **Conferir o código (o gate):** `scripts/verificar.sh`. Não gasta nada: nenhum teste chama a API da Claude nem o modelo local.
- **Comandos da fábrica:** `python -m fabrica <comando>`. Nesta versão inicial nenhum comando existe ainda: o programa recusa qualquer comando. Os comandos previstos (preparação, fichas, avançar, revisar, ensaio, erros plantados, teste dos conferentes, publicação e relatório) entram um a um, nos briefs que os constroem, e cada um é registrado em `docs/ARQUITETURA.md`, seção 8, e neste arquivo.
- A chave da API da Claude fica numa variável de ambiente da máquina, nunca num arquivo do repositório.

## Convivência com o Ollama (modelo local)

O modelo local roda no Ollama, que pode ser compartilhado com outros projetos. A regra, copiada do plano:

- antes de usar o modelo local, a fábrica consulta o `porteiro` (`porteiro cabe <modelo> --porta 11434 --json`);
- segue a resposta dele; se ele disser que não cabe, ou se faltar, vale a válvula de escape (`docs/ARQUITETURA.md`, seção 5.12.4);
- a fábrica **nunca** inicia, para, reinicia ou descarrega o Ollama nem um modelo dele.

O Ollama e o `porteiro` são desejáveis, não obrigatórios.

## A semente não refaz o texto

A semente da rodada refaz o sorteio das combinações e os dados fictícios, mas **não** refaz o texto escrito pelos modelos. Por isso o conjunto publicado não pode ser refeito idêntico. Detalhe: `docs/ARQUITETURA.md`, seções 2.1 e 4.

## Quem aprova e lê

Quem aprova os dados, lê as peças e decide se o projeto escala é o responsável, e precisa ser **advogado**. O programa nunca aprova por ele.

## O que é operação normal e o que é intervenção manual numa rodada

**Operação normal** (não afeta a rodada): rodar os comandos previstos, inclusive `avancar` de novo depois de uma interrupção, falta de energia ou reinício da máquina; dar os vereditos e conferir as amostras pelo comando `revisar`; aprovar os dados na preparação, antes da rodada; as novas tentativas automáticas e as esperas do `porteiro`; abrir um arquivo de `saida/` só para ler.

**Pausa ou parada** (registrada, não invalida): peça parada porque a API ou o modelo local ficou indisponível; corte de gasto atingido; peça de risco alto esperando o modelo local por mais de 7 dias.

**Intervenção manual** (invalida o critério de ponta a ponta da rodada): editar à mão qualquer arquivo de `saida/`; mudar um arquivo congelado, mesmo para corrigir defeito; forçar uma peça a mudar de etapa, pular etapa, reenviar pedido à mão, escolher quais peças entram ou descartar peça fora das regras.

A tabela completa está em `docs/ARQUITETURA.md`, seção 5.12.3.

## Onde ficam as regras

- `AGENTS.md`: regras de quem constrói o código.
- `docs/PLANO.md`: o que o software é, as decisões e as fases.
- `docs/ARQUITETURA.md`: como ele funciona.
- `docs/PLAN.md`: o estado da construção, atualizado a cada brief.
