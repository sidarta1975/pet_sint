# Relatório do brief 009 — Dados fictícios e nomes reservados do teste

- Data: 2026-11-21
- Brief: `docs/briefs/brief_009_ficticios_2026-11-21.md` (texto da versão 5, gravado antes da execução).
- Executor: sessão do Claude Code na nuvem, ramo `claude/project-thread-t7c3zg`.
- **Estado: concluído em 2026-11-21.**

## RELATÓRIO FINAL

- Brief executado: 009 — Dados fictícios e nomes reservados do teste (Fase 5).

- Arquivos criados:
  - `docs/briefs/brief_009_ficticios_2026-11-21.md` — o brief, literal;
  - `fabrica/ficticios.py` — `Ficticios`, com gerador próprio criado pela semente: marcadores fixos de nome e de OAB; CPF e CNPJ (metade com letras) com dígito propositalmente inválido; número do processo do CNJ com ramo 8, tribunal do estado e dígito inválido; telefone com DDD da lista recebida (recusa lista com DDD em uso); e-mail genérico em `ficticio.example`; endereço de lista com CEP da faixa da cidade; identificador `SINT-<ano>-<seis dígitos>`; profissão; código de banco fora da lista oficial recebida (recusa lista vazia). Não lê arquivo;
  - `testes/test_ficticios.py` — o teste de aceite, com as listas de exemplo dentro dele e cálculos próprios dos dígitos (os 9 pontos do brief), escrito antes do código; acrescenta a conferência do arquivo de reservados (validado pelo modelo, pelo menos 20 nomes, cada um com forma societária ou duas palavras de inicial maiúscula);
  - `testes/dados/reais_reservados.json` — 22 nomes de empresas reais com a forma em que apareceriam numa peça: 7 bancos, 1 companhia aérea, 6 operadoras de telefonia, internet e televisão, 5 varejistas, 2 seguradoras e 1 empresa de meios de pagamento. Os nomes não estão escritos em nenhum outro arquivo;
  - `docs/docs/doc_009_ficticios_2026-11-21.md` — este relatório.

- Arquivos alterados:
  - `docs/PLAN.md` — Resumo; 009 do Backlog para o Done; hash do 008 no Done.

- Arquivos preservados literalmente na área afetada: `fabrica/comum/`, `config/`, `scripts/`, `AGENTS.md`, `docs/PLANO.md`, `docs/ARQUITETURA.md`. `dados/` não existe ainda. Nenhum defeito comprovado.

- Testes rodados e resultado (com a saída colada):

  Primeiro o teste, sem o código (vermelho):

  ```text
  ImportError while importing test module '/home/user/pet_sint/testes/test_ficticios.py'.
  E   ModuleNotFoundError: No module named 'fabrica.ficticios'
  ```

  Gate final (`scripts/verificar.sh`):

  ```text
  == ruff check
  All checks passed!
  == ruff format --check
  53 files already formatted
  == mypy fabrica
  Success: no issues found in 14 source files
  == pytest testes
  ============================= test session starts ==============================
  platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
  rootdir: /home/user/pet_sint
  configfile: pyproject.toml
  plugins: anyio-4.16.0
  collected 737 items

  testes/test_api_claude.py ...............................                [  4%]
  testes/test_arquivos.py ..................                               [  6%]
  testes/test_config.py .................................................. [ 13%]
  ........................................................................ [ 23%]
  ........................................................................ [ 32%]
  ...............................................................          [ 41%]
  testes/test_congelamento.py .................                            [ 43%]
  testes/test_entrega.py .................................                 [ 48%]
  testes/test_estado.py ........................................           [ 53%]
  testes/test_estatistica.py ..........                                    [ 55%]
  testes/test_ficticios.py ..........................                      [ 58%]
  testes/test_formatos.py ................................................ [ 65%]
  ........................................................................ [ 74%]
  ........................................................................ [ 84%]
  ......................................................................   [ 94%]
  testes/test_gasto.py ..............                                      [ 96%]
  testes/test_modelo_local.py ..........................                   [ 99%]
  testes/test_registro.py ...                                              [100%]

  ============================= 737 passed in 12.45s =============================
  ```

- Comandos executados: `pytest testes/test_ficticios.py` (vermelho e depois verde); `ruff format`; `ruff check --fix`; validação do arquivo de reservados pelo modelo `ReaisReservados`; `scripts/verificar.sh`; `scripts/entregar.sh 009`. Nenhuma chamada a modelo.

- Lista de arquivos para `git add` e texto do commit:

```
docs/briefs/brief_009_ficticios_2026-11-21.md
fabrica/ficticios.py
testes/test_ficticios.py
testes/dados/reais_reservados.json
docs/docs/doc_009_ficticios_2026-11-21.md
docs/PLAN.md

Brief 009: dados fictícios e nomes reservados do teste

ficticios.py cria por programa tudo o que nunca pode ser real: marcadores
de nome e de OAB, CPF, CNPJ e número do CNJ com dígito inválido, DDD
inexistente, e-mail .example, endereço de lista com CEP da cidade,
identificadores SINT- e código de banco fora da lista oficial.
testes/dados/reais_reservados.json guarda os nomes do teste do detector.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BMQiEMLLbLrr2Sfg3kBJBL
```

- Pendências e decisões que ficaram abertas:
  1. **Lista oficial dos códigos de banco:** os canônicos não a põem em `dados/`, e nenhum dos 3 tipos do MVP usa dados bancários. A função está pronta e recebe a lista por parâmetro; a lista real (participantes do sistema de pagamentos, publicada pelo Banco Central) fica para quando um tipo precisar dela.
  2. **Limite conhecido da regra de "nome que não é marcador"** (ARQUITETURA §5.2): nome de empresa de uma palavra só, sem forma societária e sem "Banco" ou "Companhia" ao lado, não tem aparência de nome para o detector. Por isso o arquivo de reservados só tem formas que a regra cobre. É limite da regra, não do teste.
  3. **E-mail:** a parte antes da arroba é fixa por papel (`parte.autora`, `parte.re`, `advogado`, `escritorio`) e o domínio é sempre `ficticio.example`; não há sorteio, porque nada no canônico pede variação.
  4. **CNPJ com letras:** metade dos CNPJs sai no formato com letras, para que o detector (brief 010) seja exercitado nos dois formatos.
  5. **DDDs em uso:** `ficticios.py` traz a lista dos 67 DDDs em uso copiada da ARQUITETURA §5.2, para recusar uma configuração que ponha DDD em uso na lista dos inexistentes. O detector (010) pode usar a mesma lista.
  6. Pasta nova para o 023 consolidar: `testes/dados/`.
  7. **Ramo único**, como nos briefs anteriores (pedido de integração #2).

- Resumo, Doing, Backlog e Done do `docs/PLAN.md` atualizados: sim.
