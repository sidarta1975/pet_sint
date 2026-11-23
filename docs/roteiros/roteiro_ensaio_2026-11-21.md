# Roteiro do ensaio de três peças

- Para: Sidarta Borges, no MacBook Pro M5.
- Brief: 024 (ensaio de três peças). Escrito em 2026-11-23; o nome do arquivo segue o do brief, de 2026-11-21.
- Custo esperado: cerca de US$ 1 a 2 na API da Claude. Tempo: uma a duas horas, a maior parte esperando os comandos.

## Para que serve o ensaio

Uma peça de cada tipo (petição inicial, embargos de declaração e manifestação) percorre a fábrica inteira, da ficha ao pacote publicado. Sobre as três peças corre também o caminho dos erros plantados em miniatura: cópias com erro, a verificação, as amostras, o teste dos conferentes e o relatório.

**É o primeiro teste de integração de verdade.** Até aqui, cada parte foi testada sozinha, com respostas falsas. No ensaio, as partes rodam juntas pela primeira vez, e as instruções da pasta `instrucoes/` vão pela primeira vez a um modelo de verdade. Um defeito de instrução só aparece aqui, e é para isso que o ensaio existe.

O ensaio **não mede nada**. O que importa é que tudo chegue ao fim no formato certo. A qualidade das peças não conta.

Se o ensaio falhar, nada se perde: o defeito vira um brief de correção e depois se faz um ensaio novo (`e02`).

---

## 1. Antes de começar

Confira cada item. Se algum faltar, não comece.

| Item | Como conferir | Situação em 2026-11-23 |
|---|---|---|
| Código integrado ao ramo principal | No GitHub, o pedido de integração #2 aparece como "Merged" | A fazer |
| Repositório atualizado no Mac, no ramo principal | Passo 1.1 abaixo | A fazer depois da integração |
| Python 3.12 e as bibliotecas | O ambiente `.venv` da pasta `repositorio` | Pronto |
| Bash 5 do Homebrew | `bash --version` mostra "5." | Pronto (5.3.20) |
| Verificação completa verde no Mac | `scripts/verificar.sh` termina com "1180 passed" | Pronto; rodar de novo depois do passo 1.1 |
| Chave da API | `echo ${ANTHROPIC_API_KEY:0:7}` mostra "sk-ant-" | A fazer |
| Identificação do modelo local e janela de 24 horas no `config.toml` | Já gravadas no repositório (brief 026) | Pronto |
| Textos de lei e faixas de CEP conferidos na fonte | Pendência do brief 014 | A fazer; recomendado antes do ensaio, porque mudar `dados/` depois dele obriga a um ensaio novo |

### 1.1 Atualizar o repositório

Abra o Terminal e rode, um de cada vez:

```
cd ~/github/pet_sint/repositorio
source .venv/bin/activate
git checkout main
git pull
git status
```

O que cada um faz:
- `cd` entra na pasta do repositório.
- `source .venv/bin/activate` liga o Python 3.12 do projeto; o começo da linha passa a mostrar `(.venv)`.
- `git checkout main` passa para o ramo principal.
- `git pull` baixa o que estiver novo no GitHub.
- `git status` precisa dizer "nothing to commit, working tree clean". **Se mostrar qualquer arquivo alterado, pare:** a fábrica recusa rodar com mudança pendente no código.

Depois rode a verificação completa:

```
scripts/verificar.sh
```

O resultado deve ser "1180 passed" ou mais, e nenhuma falha.

### 1.2 Conferir o modelo local, antes de qualquer comando que gaste

```
ollama list
porteiro cabe gemma3:27b --porta 11434 --json; echo "resposta: $?"
```

- `ollama list` precisa mostrar `gemma3:27b`.
- O porteiro precisa terminar com "resposta: 0".

**Se o modelo não aparecer ou o porteiro não responder, não comece o ensaio.** Sem o modelo local, os embargos (a peça de risco alto) ficam esperando e o ensaio não fecha. Leve o caso para a conversa do projeto.

---

## 2. Os comandos, na ordem

Rode **um comando por vez, num Terminal só**. Dois comandos da fábrica ao mesmo tempo podem pedir o mesmo passo duas vezes.

Todo comando pode ser interrompido com Control+C, e isso é seguro: o estado está todo nos arquivos, e o mesmo comando, rodado de novo, continua de onde parou.

| # | Comando | O que faz | O que esperar |
|---|---|---|---|
| 1 | `python -m fabrica preparar` | Confere todos os dados e monta a estrutura de cada tipo. Não gasta nada | Termina sem erro e grava `saida/preparacao/`. Se precisar rodá-lo de novo, apague antes a pasta com `rm -rf saida/preparacao`, porque ele não sobrescreve (defeito conhecido) |
| 2 | `python -m fabrica ensaio` | Abre o ensaio `e01` e grava a impressão digital do código e dos dados | Mostra a rodada `e01` aberta e os três pedidos de ficha |
| 3 | `python -m fabrica avancar` | Leva cada peça ao próximo passo: ficha, redação, conferência e refação | Começa a gastar API. Termina com a linha `avancar: N passo(s).` **Repita até aparecer `avancar: 0 passo(s).`** |
| 4 | `python -m fabrica revisar` | Mostra os três cartões do ensaio | Veja a seção 3 abaixo |
| 5 | `python -m fabrica erros --rodada e01` | Cria as cópias com erro das três peças | Grava a cópia por programa e os pedidos das cópias do Opus |
| 6 | `python -m fabrica avancar`, e depois `python -m fabrica erros --rodada e01` de novo | Coleta as cópias e a verificação, e sorteia as amostras | Repita os dois, nessa ordem, até o `erros` mostrar a linha `erros: amostras sorteadas em ...` |
| 7 | `python -m fabrica revisar` | Mostra as amostras reduzidas de cópias | Veja a seção 3 abaixo |
| 8 | `python -m fabrica testar --rodada e01` | Fecha o banco de cópias e registra o teste dos conferentes | Diz quantas conferências faltam |
| 9 | `python -m fabrica avancar` | Leva as cópias e as peças pela conferência, às cegas | Repita até aparecer `avancar: 0 passo(s).` |
| 10 | `python -m fabrica testar --rodada e01` | Calcula o resultado do teste | Grava o resultado em `saida/relatorios/` |
| 11 | `python -m fabrica publicar --rodada e01` | Monta o pacote das três peças | Grava `.md`, `.json` e `.docx` em `saida/pacotes/ensaio_e01/` |
| 12 | `python -m fabrica relatorio --rodada e01` | Escreve o relatório do ensaio | Grava `saida/relatorios/relatorio_e01.md`, com o aviso "ensaio: sem valor de medida" |
| 13 | `python -m fabrica ensaio --fechar e01` | Aplica a regra de passa ou para | Diz "aprovado" ou lista cada motivo da reprovação |

Se o `avancar` mostrar uma linha `esperando: ...`, alguma peça espera uma resposta sua num cartão ou o modelo local: siga para o passo seguinte do roteiro.

Se um comando disser o que falta (por exemplo, `testar` antes das amostras respondidas), faça o que falta e rode o comando de novo.

## 3. Os cartões (`revisar`)

O comando mostra um cartão por vez, faz as perguntas e, no fim, mostra as suas respostas juntas e pede confirmação. **Antes de confirmar, dá para corrigir qualquer resposta; depois, ela não muda.**

- **Cartões do ensaio (passo 4), um por peça.** Mostram a peça e o veredito da fábrica juntos, porque o ensaio não é às cegas. Perguntas:
  - **tudo saiu no formato certo?** Responda "não" se faltar um bloco, se um campo vier vazio ou trocado, se houver texto cortado ou estranho, e diga o que saiu errado;
  - **há algum nome, número ou dado que pareça real?**

  A pergunta é sobre o formato, não sobre a qualidade jurídica.
- **Amostras reduzidas (passo 7).** Para cada cópia com erro aceita, diga se o erro existe e se é o que o gabarito diz. Na cópia descartada, se houver, diga se o erro pedido existe nela.

## 4. O que nunca fazer durante o ensaio

- Editar qualquer arquivo da pasta `saida/`; abrir para ler pode.
- Mudar qualquer arquivo de `dados/`, `instrucoes/`, `config/` ou do código.
- Reenviar um pedido à mão.
- Iniciar, parar ou descarregar o Ollama ou um modelo dele.

Qualquer uma dessas coisas invalida o ensaio.

### 4.1 Se o modelo local cair no meio

1. Não mexa no Ollama com um comando da fábrica rodando.
2. Interrompa o comando com Control+C; isso é seguro. A peça fica em pausa registrada, o que não invalida o ensaio.
3. Reinicie o computador, que é operação normal.
4. Confira com `ollama list` que o modelo voltou.
5. Ative o ambiente de novo (`cd ~/github/pet_sint/repositorio` e `source .venv/bin/activate`) e rode `python -m fabrica avancar`. A peça continua de onde parou.

O reinício não zera a contagem dos 7 dias de espera, que corre desde a primeira queda naquela peça. Se o modelo não voltar, pare e leve o caso para a conversa do projeto.

## 5. Custo e limites

- **Esperado:** o ensaio mais menos de US$ 1 do caminho dos erros em miniatura, dentro de US$ 1 a 2.
- **Alerta em US$ 30:** só avisa.
- **Corte em US$ 100:** a fábrica não envia nenhum pedido que passe do corte; as peças param onde estão, sem perder nada. No ensaio, chegar perto disso indica defeito: pare e leve o caso para a conversa do projeto.

A conta conta só o que a fábrica gastou, registrado em `saida/registro/chamadas.jsonl`.

## 6. Ao terminar: o que enviar

Na pasta do repositório, rode:

```
zip -r ../ensaio_e01.zip saida/rodadas.json saida/registro saida/relatorios saida/cartoes
```

Esse comando junta num arquivo só, `ensaio_e01.zip`, o registro do ensaio, os relatórios e os cartões respondidos. O arquivo fica em `~/github/pet_sint`, a pasta ligada à conversa, um nível acima do repositório. Nada mais da pasta `saida/` é necessário.

Depois, avise na conversa do projeto. A leitura do resultado diz:
- se o ensaio passou;
- o tamanho de contexto do modelo local decidido (16.384 ou 32.768);
- os tokens reais de cada tarefa;
- o custo;
- o que os cartões apontaram.

**Se reprovar só por contexto do modelo local**, o valor sobe para 32.768 no `config.toml` e se faz um ensaio novo (`e02`) por este mesmo roteiro. **Se reprovar por defeito de código, instrução ou dado**, o conserto vira um brief novo, e depois vem o ensaio novo.
