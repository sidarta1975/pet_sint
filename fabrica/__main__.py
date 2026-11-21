"""Ponto de entrada único: `python -m fabrica <comando>` (ARQUITETURA §8).

Não tem lógica de etapa. `montar_servicos(raiz)` monta os serviços de verdade
(registro de decisão 002, item 2); `executar(argumentos, servicos, ler_linha)`
roda um comando com os serviços recebidos; `main()` só chama as duas.
Cada brief que cria um comando acrescenta a sua linha em `COMANDOS`, e cada
brief que constrói uma etapa a acrescenta em `ETAPAS`, na ordem do fluxo.
"""

from __future__ import annotations

import datetime
import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import anthropic

from fabrica import estado
from fabrica.comum import config
from fabrica.comum.api_claude import ApiClaude
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.gasto import ControleGasto
from fabrica.comum.modelo_local import ModeloLocal
from fabrica.comum.registro import Registro
from fabrica.estado import Servicos

RAIZ = Path(__file__).resolve().parent.parent
VARIAVEL_DA_CHAVE = "ANTHROPIC_API_KEY"

LerLinha = Callable[[str], str]
Comando = Callable[[Sequence[str], Servicos, LerLinha], int]

# A ordem das etapas do fluxo das peças (registro de decisão 002, item 5).
ETAPAS: list[Any] = []


def _agora() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def montar_servicos(raiz: Path) -> Servicos:
    """Monta os três clientes e os demais serviços. A chave só passa pela memória."""
    arquivos = Arquivos(raiz, relogio=_agora)
    lida = config.carregar(arquivos)
    registro = Registro(arquivos)
    gasto = ControleGasto(lida, registro, relogio=_agora)
    chave = os.environ.get(VARIAVEL_DA_CHAVE)
    api: ApiClaude | None = None
    if chave:
        # As novas tentativas são só as de api_claude.py (30, 120 e 480 segundos).
        cliente = anthropic.Anthropic(api_key=chave, max_retries=0)
        api = ApiClaude(cliente, lida, arquivos, registro, gasto, relogio=_agora)
    return Servicos(
        api_claude=api,
        modelo_local=ModeloLocal(lida, arquivos, registro, relogio=_agora),
        arquivos=arquivos,
        config=lida,
        registro=registro,
        gasto=gasto,
        relogio=_agora,
        modo_teste=False,
    )


def comando_avancar(argumentos: Sequence[str], servicos: Servicos, ler_linha: LerLinha) -> int:
    """Leva cada peça à próxima etapa possível (ARQUITETURA §8)."""
    try:
        resumo = estado.avancar(ETAPAS, servicos)
    except estado.ErroServicos as erro:
        print(f"avancar parou: {erro}", file=sys.stderr)
        return 2
    print(f"avancar: {resumo.passos} passo(s).")
    if resumo.alerta_de_gasto:
        print("aviso: o gasto passou do alerta do gasto.toml (a rodada continua).")
    if resumo.esperando:
        print(f"esperando: {', '.join(resumo.esperando)}")
    if resumo.parada == "congelamento":
        print("parado: um arquivo congelado mudou (ver ocorrencias.jsonl).", file=sys.stderr)
        return 1
    if resumo.parada == "corte":
        print("parado: o próximo pedido passaria do corte de gasto.", file=sys.stderr)
        return 1
    return 0


COMANDOS: dict[str, Comando] = {
    "avancar": comando_avancar,
}


def executar(argumentos: Sequence[str], servicos: Servicos, ler_linha: LerLinha = input) -> int:
    """Executa o comando pedido; recusa comando ausente ou desconhecido."""
    if not argumentos:
        print("uso: python -m fabrica <comando>", file=sys.stderr)
        return 2
    comando = argumentos[0]
    funcao = COMANDOS.get(comando)
    if funcao is None:
        print(f"comando desconhecido: {comando}", file=sys.stderr)
        return 2
    return funcao(argumentos[1:], servicos, ler_linha)


def main() -> int:
    return executar(sys.argv[1:], montar_servicos(RAIZ))


if __name__ == "__main__":
    sys.exit(main())
