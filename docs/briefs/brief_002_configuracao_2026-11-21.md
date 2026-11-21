# Brief 002 — Configuração do MVP travada

- Fase: 2 — Configuração do MVP travada (PLANO §4)
- Objetivo: escrever `config/config.toml` e `config/gasto.toml` com todos os valores da ARQUITETURA §2.1 e os limites declarados, e parar para o responsável conferir cada um.
- Seções a ler: AGENTS §3 e §4 (regras do domínio, limites numéricos); PLANO §3, §3.1, §4 (Fase 2) e §5; ARQUITETURA §2.1 (`config.toml` e `gasto.toml`), §5.1, §5.2 (DDDs), §5.6 (semelhança), §5.7 (amostras), §5.12.4, §5.12.5, §5.12.6, §6, §7.1, §7.2, Anexos A.6 e E; armadilhas do PLAN: "api_claude.py" (esforço explícito), "modelo_local.py" (contexto), "estatistica.py, plano B".
- Arquivos que pode criar:
  - `config/config.toml`;
  - `config/gasto.toml`;
  - `docs/briefs/brief_002_configuracao_2026-11-21.md` (este brief);
  - `docs/docs/doc_002_configuracao_2026-11-21.md` (o relatório).
- Arquivos que pode alterar: `docs/PLAN.md` (Resumo, Doing, Backlog, Done e Pendências de Sidarta Borges).
- Arquivos que não pode tocar: todo o resto, inclusive `fabrica/`, `testes/`, `AGENTS.md`, `docs/ARQUITETURA.md` e `docs/PLANO.md`.
- Teste de aceite (escrito antes do código): não há código neste brief. O aceite é a conferência do responsável, registrada no relatório. O gate continua verde (o brief não pode quebrá-lo). O brief 004 é que cria `test_config.py`, que lê estes arquivos.
- Critério de conclusão: o da Fase 2 no PLANO — os dois arquivos existem com todos os valores abaixo e o responsável os conferiu, com o registro no relatório.
- Fora do escopo: qualquer código, inclusive o leitor da configuração (`config.py`, brief 004); `dados/`; `instrucoes/`; qualquer chamada à API ou ao modelo local; mudar um valor declarado nos canônicos.
- Depende de: 001.

**Regras deste brief**

- Todo valor abaixo vem dos canônicos e é usado como está. O executor não muda nenhum. Valor que os canônicos não dão fica marcado no arquivo com um comentário `# PENDENTE: <o que falta>` e entra nas pendências do relatório; nunca é inventado. A única exceção são os dois preços do Haiku acima de 100 mil tokens de entrada (50 e 250 centavos por milhão): os canônicos não os dão, mas eles foram conferidos na página oficial de preços da Anthropic em 2026-11-21 (análise da rodada 4) e vão no arquivo com a fonte no comentário, para o responsável confirmar na parada.
- Cada valor tem, ao lado, um comentário curto com a seção da ARQUITETURA ou do PLANO de onde veio.
- Unidades (fixadas aqui, porque os canônicos não as fixam): preços em centavos de dólar por milhão de tokens, inteiros; alerta e corte em centavos de dólar, inteiros; frações como número decimal (0,85 vira `0.85`); horas, dias e minutos em chaves com a unidade no nome (`_horas`, `_dias`, `_minutos`, `_segundos`).
- Nomes das tarefas (fixados aqui e usados por todos os briefs seguintes): `ficha`, `redacao_risco_baixo`, `redacao_risco_medio`, `redacao_risco_alto`, `extracao`, `checklist`, `conferencia_opus` (risco alto e desempate), `copia_com_erro`, `verificacao_copia`.

**Conteúdo de `config/config.toml`** (as chaves são estas; o executor pode só acrescentar o comentário de origem):

```toml
[modelos]
data_conferencia = "2026-11-21"          # ARQUITETURA §7.1

[modelos.opus]
id = "claude-opus-5-5"
preco_entrada_centavos_por_milhao = 400
preco_saida_centavos_por_milhao = 2000

[modelos.sonnet]
id = "claude-sonnet-5-5"
preco_entrada_centavos_por_milhao = 200
preco_saida_centavos_por_milhao = 1000

[modelos.haiku]
id = "claude-haiku-5-5"
preco_entrada_centavos_por_milhao = 10   # vale até 100 mil tokens de entrada
preco_saida_centavos_por_milhao = 50
limite_entrada_tokens_do_preco = 100000
preco_entrada_acima_do_limite_centavos_por_milhao = 50    # página oficial de preços da Anthropic, conferida em 2026-11-21
preco_saida_acima_do_limite_centavos_por_milhao = 250     # idem; o responsável confirma na parada deste brief

[tarefas.ficha]
modelo = "haiku"
esforco = "low"
teto_saida_tokens = 8000
[tarefas.redacao_risco_baixo]
modelo = "haiku"
esforco = "low"
teto_saida_tokens = 8000
[tarefas.extracao]
modelo = "haiku"
esforco = "low"
teto_saida_tokens = 8000
[tarefas.checklist]
modelo = "haiku"
esforco = "low"
teto_saida_tokens = 8000
[tarefas.redacao_risco_medio]
modelo = "sonnet"
esforco = "low"
teto_saida_tokens = 16000
[tarefas.redacao_risco_alto]
modelo = "sonnet"
esforco = "medium"
teto_saida_tokens = 16000
[tarefas.conferencia_opus]
modelo = "opus"
esforco = "low"
teto_saida_tokens = 8000
[tarefas.copia_com_erro]
modelo = "opus"
esforco = "medium"
teto_saida_tokens = 8000
[tarefas.verificacao_copia]
modelo = "sonnet"
esforco = "medium"
teto_saida_tokens = 8000

[api]
modo_chamada = "uma_a_uma"               # ARQUITETURA §2.1
esperas_novas_tentativas_segundos = [30, 120, 480]   # §7.1: 30 s, 2 min, 8 min

[volume]
pecas_por_tipo = 10
copias_opus_por_peca_boa = 4
copias_programa_por_peca_boa = 1
fracao_copias_opus_sutis = 0.5
versoes_maximas = 3

[plano_b]                                # ARQUITETURA §5.12.6
normal_a_partir_de_pecas_boas = 20
faixa_media_de = 14
faixa_media_ate = 19
copias_opus_por_peca_boa_faixa_media = 6
inconclusivo_abaixo_de = 14

[semelhanca]
limite = 0.85
palavras_por_trecho = 5

[modelo_local]
nome = "gemma3:27b"
etiqueta_completa = ""   # PENDENTE: o responsável informa (máquina de produção)
digest = ""              # PENDENTE: o responsável informa (máquina de produção)
porta = 11434
num_ctx = 16384
num_ctx_alternativo = 32768
fracao_limite_contexto_ensaio = 0.75
divisor_caracteres_por_token = 3
porteiro_intervalo_segundos = 60
porteiro_espera_maxima_minutos = 15
fracao_pecas_risco_baixo = 0.2           # 2 das 10 manifestações

[janela_local]
inicio = "22:00"   # PENDENTE: provisório ("a noite", PLAN); o responsável define
fim = "06:00"      # PENDENTE: provisório; a janela tem de ter 24 horas ou menos

[valvula]
espera_risco_medio_horas = 72
espera_risco_alto_dias = 7
fracao_sem_local_para_ressalva = 0.20

[referencias_legais]
ano_das_fichas = 2026
salario_minimo_centavos = 162100
salario_minimo_norma = "Decreto nº 12.797, de 23/12/2025"
salario_minimo_data_conferencia = "2026-11-21"
alcada_em_salarios_minimos = 40          # alçada de R$ 64.840,00

[ddds]
inexistentes = [20, 23, 25, 26, 29, 36, 39, 52, 56, 57, 58, 59, 72, 76, 78]
data_conferencia = "2026-11-21"   # PENDENTE: confirmar a data da conferência da lista

[criterios]                              # ARQUITETURA §5.1, §5.7, §6
taxa_minima = 0.80
limite_inferior_minimo = 0.65
confianca = 0.95
pontos_dependencia_opus = 15
minimo_copias_julgamento = 5
fracao_maxima_pecas_boas_reprovadas = 0.10
custo_marginal_maximo_centavos = 15
piso_pecas_por_tipo = 8
fracao_fichas_reprovadas_por_tipo = 0.20
rejeitadas_para_banco_nao_confiavel = 2
existentes_para_banco_filtrado = 2

[amostras]
copias_aceitas = 10
descartadas_nao_viu_erro = 5
ensaio_copias_aceitas_maximo = 3
ensaio_descartadas_maximo = 1

[matriz]
tentativas_maximas = 1000
fracao_maxima_por_materia = 0.25
dias_uteis_de_folga = 1
anos_maximos_dos_fatos = 2

[fichas]
retornos_ao_haiku = 1
fichas_novas_por_casa = 2

[trecho]
teto_tokens = 8000

[ancora]                                 # ARQUITETURA, Anexo E
termos_minimos = 3
letras_do_radical = 6
letras_minimas = 4
fracao_maxima_fora_da_mencao = 0.20
palavras_maximas_mencao = 40

[erros]                                  # ARQUITETURA §5.7 e Anexo C.1
fracao_maxima_regiao = 0.25
diferenca_minima_valor_trocado = 0.01

[comparacao]                             # ARQUITETURA, Anexo D
diferenca_maxima_arredondamento = 0.01
```

**Conteúdo de `config/gasto.toml`:**

```toml
alerta_centavos = 3000    # US$ 30, só avisa (ARQUITETURA §5.12.5)
corte_centavos = 10000    # US$ 100, o orçamento do mês; não sobe
```

**Onde o brief para.** Depois do gate verde, o executor entrega pelo `scripts/entregar.sh 002`, abre o pedido de integração do ramo para `main` e escreve na resposta final só a pendência: "No computador, fazer a conferência da máquina (abaixo, copiada no relatório) e informar o resultado; conferir os valores de `config/config.toml` e `config/gasto.toml`, inclusive os preços do Haiku acima de 100 mil tokens; e informar a janela da conferência local e a etiqueta completa e o digest do `gemma3:27b`". O relatório fica com a seção "## Conferência do responsável: pendente". Quando o responsável responder, uma sessão seguinte do mesmo brief:
- troca os valores que ele corrigir e tira o `# PENDENTE` dos que ele informar (etiqueta e digest podem continuar vazios se a máquina não tiver o Ollama: vale a válvula de escape, ARQUITETURA §5.12.4);
- se a conferência da máquina mostrar que o `gemma3:27b` não roda nela, registra em `docs/PLAN.md`, nas Pendências de Sidarta Borges, a decisão que ele precisa tomar antes do ensaio: outra máquina que rode o modelo, ou mudar a regra do risco alto na ARQUITETURA §5.12.4 (sem o modelo local, as peças de risco alto ficam em pausa e nem o ensaio nem a rodada fecham);
- acrescenta ao relatório a seção "## Conferência do responsável", com a data e a lista do que ele conferiu, corrigiu ou deixou pendente;
- atualiza o manifesto do relatório e entrega de novo.

**Conferência da máquina (pelo responsável, no computador, cerca de 15 minutos, sem gastar API).** O executor está na nuvem, sem o Ollama e sem a máquina do responsável: ele não roda nenhum destes comandos e não registra a ausência do Ollama na nuvem como defeito. Ele copia os passos no relatório, na seção de conferência do responsável; o responsável os roda no computador dele e devolve o resultado de cada um, a etiqueta e o digest:
1. `python3.12 --version` responde 3.12;
2. `ollama list` mostra `gemma3:27b` (se não mostrar: `ollama pull gemma3:27b`, cerca de 17,5 GB);
3. `ollama show gemma3:27b` e anotar a etiqueta completa e o digest, que vão para o `config.toml`;
4. `curl -s http://localhost:11434/api/generate -d '{"model":"gemma3:27b","prompt":"Responda só: ok","stream":false,"options":{"num_ctx":16384}}'` responde, e `ollama ps` mostra o modelo carregado; anotar quanto tempo levou (o modelo pede memória folgada, na prática 32 GB);
5. `porteiro cabe gemma3:27b --porta 11434 --json` responde, se ele usar o `porteiro`.

O brief só é marcado como concluído no `docs/PLAN.md` depois dessa seção. Como o ensaio aprovado congela os dois arquivos, a conferência daqui vale para a rodada inteira (PLAN, Backlog).

**Decisão em aberto que este brief respeita:** 10 peças por tipo (PLAN, Decisões em aberto). Se o responsável escolher 20 antes da conferência, muda só `pecas_por_tipo`; as contagens dos eixos da matriz dobram no brief 014.
