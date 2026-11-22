# AGENTS.md — Petições Sintéticas

> Arquivo na raiz do repositório. O Claude Code o carrega sozinho no início da sessão.
> Não criar `CLAUDE.md` nem `CLAUDE.local.md` no repositório: com eles, este arquivo deixa de ser lido.

---

## 1. Papel do executor

Você implementa briefs. Não tem latitude criativa. Se o brief não cobre algo, pare e registre no relatório como pendência — não invente.

Antes de alterar qualquer coisa, leia:
1. `docs/PLAN.md`, até o fim de `## Dívidas conhecidas`;
2. as seções do PLANO, da ARQUITETURA e das armadilhas citadas em "Seções a ler" no cabeçalho do brief;
3. o brief;
4. o código existente da área afetada.

O histórico (`docs/historico/`) é consultado por busca, nunca lido inteiro. As versões antigas da arquitetura e o plano v15 não são lidos: o que vale deles já está em `docs/PLANO.md` e `docs/ARQUITETURA.md`.

O projeto gera petições fictícias. Nunca recebe nem escreve dado real de pessoa, empresa privada, documento, endereço ou processo.

## 2. Estrutura do repositório

Repositório: `sidarta1975/pet_sint`, no GitHub. Estrutura: `docs/ARQUITETURA.md` §2. O nome do pacote e da pasta é sempre `fabrica`; os testes ficam em `testes/`; o ponto de entrada é `fabrica/__main__.py` e não existe `fabrica.py` na raiz. Desvio de nomenclatura é corrigido imediatamente.

## 3. Stack — só o que é regra

A descrição da stack fica na ARQUITETURA.

- Python 3.12. Bibliotecas só as do `pyproject.toml`, com versão fixa; biblioteca nova só se o brief pedir.
- Não há banco de dados. O estado são os arquivos JSON e Markdown de `saida/`. Todo arquivo é gravado primeiro num temporário e depois renomeado. Nada em `saida/` é sobrescrito nem apagado: refação gera arquivo novo.
- Contratos de dados: Pydantic 2, todos em `fabrica/comum/formatos.py`, com `extra="forbid"` e modo estrito. Todo arquivo é validado ao gravar e ao ler. Valores em dinheiro em centavos, inteiros; datas ano-mês-dia.
- Só três arquivos falam com o mundo de fora: `fabrica/comum/api_claude.py` (API da Claude), `fabrica/comum/modelo_local.py` (Ollama) e `fabrica/comum/arquivos.py` (disco). Os três são montados em `fabrica/__main__.py` e entregues aos módulos por parâmetro; nenhum outro módulo instancia cliente externo nem abre arquivo de `saida/` diretamente.
- Chamada à API da Claude: sempre em dois passos (gravar o pedido, coletar a resposta); saída estruturada só por `output_config.format`; nível de esforço e teto de saída da tabela do `config.toml` em toda chamada. Proibido: teto de tokens de raciocínio, uso forçado de ferramenta, parâmetros de amostragem, resposta pré-escrita do assistente e troca automática de modelo. Ver as armadilhas de `api_claude.py` em `docs/PLAN.md`.
- Ollama: o executor e a fábrica nunca iniciam, param, reiniciam nem descarregam o Ollama nem um modelo dele. Antes de cada uso, `porteiro cabe <modelo> --porta 11434 --json`. `num_ctx` sempre explícito.
- Rede: a fábrica não abre nenhuma porta. Só faz conexões de saída para a API da Claude e para `127.0.0.1:11434`.
- Agendamento: não existe. Toda execução da fábrica é disparada pelo responsável.
- Modelos, preços, esforço, tetos, quantidades e limites ficam em `config/config.toml`; alerta e corte de gasto, em `config/gasto.toml`. Nenhum desses valores fica no código.
- A chave da API vem de variável de ambiente. Nunca é escrita em arquivo do repositório, em relatório ou em log.
- Segurança do produto:
  - nome de parte e de advogado é sempre o marcador fixo; OAB é sempre "OAB/UF nº 000.000";
  - e-mail sempre em `.example` (nunca `exemplo.com`);
  - CPF, CNPJ (inclusive com letras) e número de processo sempre com dígito verificador inválido; telefone só com os DDDs da lista; contratos e protocolos com `SINT-`;
  - todo arquivo publicado leva "DOCUMENTO SINTÉTICO — FICTÍCIO";
  - nenhum arquivo sem a marca sai da fábrica.

## 4. Regras de alteração

- Mudança cirúrgica: só o que o brief pede.
- Código funcionando não se altera sem evidência de defeito.
- Sem variantes de depuração e sem arquivos paralelos de módulos existentes.
- Sem caminho fixo no código: resolução a partir da raiz do repositório.
- Texto enviado a modelo fica só no arquivo de `instrucoes/` da tarefa; o código lê o arquivo e nunca embute instrução em texto do programa. O brief que constrói o módulo cria a instrução que ele usa.
- Resposta de modelo é guardada como chegou, em `saida/respostas/`. Nunca se conserta resposta com expressão regular: resposta fora do formato gera novo pedido. A normalização (Anexos D e E) roda sobre cópias, na comparação, nunca sobre o texto guardado.
- Restrições são estruturais, não procedurais: o que não deve ser visto adiante é bloqueado na origem. Exemplos já na arquitetura: a segunda etapa do cartão só é gerada depois das respostas confirmadas; o modo de teste desliga a semelhança sozinho; o comando `fichas` recusa a rodada sem ensaio aprovado; `gasto.py` não envia pedido acima do corte.
- Antes de diagnosticar erro, perguntar "isso funcionava antes?" e responder antes de tocar em código.
- Não há banco nem migração. Mudança de formato de arquivo só em `formatos.py`, por brief que a declare, e nunca reescrevendo arquivos já gravados em `saida/`.
- Regras do domínio:
  - quem aprova dados, lê as peças e decide se escala é o responsável, que é advogado; o programa nunca aprova por ele;
  - todo limite numérico da ARQUITETURA (80% e 65%, 10%, 8 de 10, US$ 0,15, 15 pontos, 20%, 75%, 72 horas, 7 dias, 0,85, US$ 30 e US$ 100) é escolha declarada antes de rodar; o executor não o muda;
  - rótulo de tipo de peça é sempre o exato da lista consolidada;
  - peça só cita dispositivo da tabela de normas.
- Divergência com o plano v15 não reabre o plano: vira uma linha em "divergencias com o plano v15 2026-11-21 b.md", registrada como pendência no relatório.

## 5. Git

- Proibido `git add -A` e `git add .`. Adição arquivo por arquivo, com lista explícita.
- `git status` antes de qualquer `add`; arquivo inesperado interrompe a operação.
- Trunk-based em `main`. Sem branches de longa duração.
- Sessão na nuvem que só pode enviar a um ramo próprio: `entregar.sh` envia o ramo atual, e o executor abre o pedido de integração desse ramo para `main`, que o responsável aceita. O ramo dura um brief.
- **(A) Executor autônomo** — escolha padrão; o responsável troca esta linha pela opção (B) se quiser rodar o git ele mesmo: o executor commita e faz push ao fim de cada brief, exclusivamente por `scripts/entregar.sh <NNN>`, que só commita com o gate verde e só os arquivos do manifesto do relatório. Git de escrita digitado direto fica bloqueado pela trava de `.claude/settings.json` (`scripts/trava_git.sh`).
  - (B), se escolhida no lugar de (A): o executor nunca roda git de escrita. Prepara a lista de arquivos e o texto do commit no relatório; Sidarta Borges autoriza e roda.
- Remoção de arquivo rastreado: entra no manifesto como `remover: <caminho>`, com o critério escrito no relatório; `entregar.sh` faz o `git rm`. Nunca se removem `__init__.py`, `.gitkeep` e afins.
- Todo `.md` de `docs/` é versionado. `saida/` nunca entra no git.

## 6. Testes e gate

- O gate completo é `scripts/verificar.sh`: `ruff check`, `ruff format --check`, `mypy fabrica`, `pytest testes`.
- O executor roda o gate dentro do script de entrega; pode rodá-lo antes, à vontade.
- Havendo teste de aceite no brief, o teste é escrito antes do código.
- Sem saída de comando colada no relatório, não se escreve que algo passou.
- Nenhum teste chama a API da Claude ou o Ollama de verdade: os três clientes externos são trocados por falsos. Testes de disco usam pasta temporária, nunca `saida/`.
- O executor nunca roda comando da fábrica que gaste API ou use o modelo local (`fichas`, `avancar`, ensaio, erros plantados, teste dos conferentes) nem toca em `saida/` de uma rodada. Ensaio e rodada são rodados pelo responsável; o brief da fase prepara o roteiro e lê o resultado.

## 7. Tarefas não assistidas

Podem rodar sem supervisão do executor: o gate (`scripts/verificar.sh`) e a entrega (`scripts/entregar.sh`). Na fábrica, `python -m fabrica avancar` pode ser deixado rodando pelo responsável: é retomável pelos arquivos, registra tudo em `saida/registro/`, para sozinho no corte de gasto e no congelamento, e interrompê-lo é seguro (não é intervenção).
Requisitos de tudo que roda sozinho: idempotência e retomada pelos arquivos; registro em arquivo (`chamadas.jsonl` e `ocorrencias.jsonl`); parada por interrupção do comando, sem arquivo sentinela, porque o estado está todo em disco.
Nunca rodam sozinhos: os vereditos e as amostras do comando `revisar` (só o responsável); a aprovação dos dados da preparação; qualquer mudança em `dados/`, `instrucoes/`, `config/` ou no código durante uma rodada; edição de arquivo de `saida/`; subir o corte de gasto; qualquer ação sobre o Ollama.

## 8. Comportamento do software

Regras de produto que o executor não pode mudar:
- Processamento de ponta a ponta sem intervenção manual; o que é intervenção está na ARQUITETURA 5.12.3.
- Revisão humana às cegas da primeira versão das 30 peças, com a ficha sempre ao lado; as respostas do responsável só entram pelo comando `revisar` e não mudam depois de confirmadas.
- Todas as regras de operação da rodada (ensaio, congelamento, válvula do modelo local, corte, plano B, destino das peças, resposta fora do formato) ficam escritas antes de rodar e são aplicadas por programa, sem decisão depois de ver o resultado.
- Critério "zero" de dado real; qualquer achado do detector reprova.
- A conferência não troca de modelo sozinha; o verificador das cópias (Sonnet) nunca é conferente avaliado; o criador das cópias (Opus) e o viés que isso cria são medidos, não escondidos.
- Erro só conta como pego se o item aceito reprovou na cópia e passou na original.
- O sistema entrega o relatório com os critérios e as ressalvas; quem decide se escala é o responsável.

## 9. Relatório final obrigatório

O bloco abaixo é escrito no relatório do brief, `docs/docs/doc_<NNN>_<slug>_<AAAA-MM-DD>.md`, e não na resposta da conversa. Sem ele, a sessão é considerada incompleta. Na opção (A) de git, o bloco "Lista de arquivos para `git add` e texto do commit" é o manifesto que `scripts/entregar.sh` lê: uma linha por arquivo, `remover: <caminho>` nas remoções, e o texto do commit depois de uma linha em branco.

```
## RELATÓRIO FINAL
- Brief executado:
- Arquivos criados:
- Arquivos alterados (com resumo da mudança em uma linha cada):
- Arquivos preservados literalmente na área afetada:
- Testes rodados e resultado (com a saída colada):
- Comandos executados:
- Lista de arquivos para `git add` e texto do commit:
- Pendências e decisões que ficaram abertas:
- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim/não
```

A resposta final da sessão tem três linhas: o caminho do relatório; o que foi feito (com o hash do commit, se houver); e "Nada para você." ou só a pendência que exige Sidarta Borges (aprovação de dados, ensaio, leitura de peças, decisão de produto).

## 10. Briefs e numeração

- Briefs e relatórios seguem uma única sequência numérica. O próximo número é o maior encontrado em `docs/briefs/` e `docs/docs/`, mais um.
- Todo brief escrito fora do repositório é gravado em `docs/briefs/` antes de ser executado. O executor não executa brief que não esteja no disco.
- O cabeçalho do brief segue `docs/briefs/_modelo.md`. O brief 001 cria esse arquivo com este conteúdo:

```
# Brief NNN — <título curto>

- Fase: <número e nome, do PLANO §4>
- Objetivo: <uma frase>
- Seções a ler: <PLANO §…; ARQUITETURA §…; armadilhas do PLAN: <áreas>>
- Arquivos que pode criar:
- Arquivos que pode alterar:
- Arquivos que não pode tocar:
- Teste de aceite (escrito antes do código):
- Critério de conclusão: <o da fase no PLANO, ou parte dele>
- Fora do escopo:
- Depende de: <briefs anteriores>
```

- Não editar este arquivo, regra ou skill numa sessão de execução, salvo quando o brief tiver esse arquivo como alvo.

## 11. Certificação

Uma tarefa só está certificada quando: testes verdes, escopo respeitado (nada além do brief), relatório final completo e Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados. Ao fim de cada fase de implementação, aplica-se auditoria independente, com validação cruzada em outro modelo, que não o que executou a fase.
