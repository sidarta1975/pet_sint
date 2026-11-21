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

from fabrica import estado, estruturas, fichas, redacao
from fabrica.comum import config
from fabrica.comum.api_claude import ApiClaude
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.congelamento import ErroCongelamento
from fabrica.comum.gasto import ControleGasto
from fabrica.comum.modelo_local import ModeloLocal
from fabrica.comum.registro import Registro
from fabrica.estado import Servicos

RAIZ = Path(__file__).resolve().parent.parent
VARIAVEL_DA_CHAVE = "ANTHROPIC_API_KEY"

LerLinha = Callable[[str], str]
Comando = Callable[[Sequence[str], Servicos, LerLinha], int]

# A ordem das etapas do fluxo das peças (registro de decisão 002, item 5).
ETAPAS: list[Any] = [fichas.EtapaFicha(), fichas.EtapaRetorno(), redacao.EtapaRedacao()]


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
        fichas.repor_falhas_de_formato(servicos)
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


def comando_preparar(argumentos: Sequence[str], servicos: Servicos, ler_linha: LerLinha) -> int:
    """Valida `dados/` e grava a preparação, sem gastar API (brief 011)."""
    semente = estruturas.SEMENTE_DE_PROVA
    if argumentos:
        if len(argumentos) != 2 or argumentos[0] != "--semente" or not argumentos[1].isdigit():
            print("uso: python -m fabrica preparar [--semente N]", file=sys.stderr)
            return 2
        semente = int(argumentos[1])
    prep = estruturas.preparar(servicos.arquivos, servicos.config, semente)
    for linha in prep.linhas:
        if linha.startswith("- "):
            print(linha[2:])
    for problema in prep.problemas:
        print(f"falhou: {problema}", file=sys.stderr)
    print(f"resumo em {estruturas.PASTA}/resumo.md")
    return 0 if prep.passou else 1


def _opcoes(argumentos: Sequence[str], aceitas: Sequence[str]) -> dict[str, str] | None:
    """Pares `--nome valor`; None se algo não estiver nesse formato."""
    if len(argumentos) % 2:
        return None
    lidas = dict(zip(argumentos[::2], argumentos[1::2], strict=True))
    if any(nome not in aceitas for nome in lidas) or len(lidas) * 2 != len(argumentos):
        return None
    return lidas


def _semente(opcoes: dict[str, str]) -> int | None | bool:
    texto = opcoes.get("--semente")
    if texto is None:
        return None
    return int(texto) if texto.isdigit() else False


def comando_ensaio(argumentos: Sequence[str], servicos: Servicos, ler_linha: LerLinha) -> int:
    """Abre a rodada de ensaio seguinte e grava uma ficha por tipo (brief 015)."""
    opcoes = _opcoes(argumentos, ["--semente"])
    semente = _semente(opcoes) if opcoes is not None else False
    if opcoes is None or semente is False:
        print("uso: python -m fabrica ensaio [--semente N]", file=sys.stderr)
        return 2
    try:
        rodada, pecas = fichas.abrir_ensaio(servicos, semente)
    except (fichas.ErroFichas, ErroCongelamento) as erro:
        print(f"ensaio não abriu: {erro}", file=sys.stderr)
        return 1
    print(f"ensaio {rodada}: {len(pecas)} pedido(s) de ficha gravado(s): {', '.join(pecas)}")
    return 0


def comando_fichas(argumentos: Sequence[str], servicos: Servicos, ler_linha: LerLinha) -> int:
    """Sorteia as combinações e grava os pedidos de ficha do tipo (brief 015)."""
    opcoes = _opcoes(argumentos, ["--tipo", "--semente"])
    semente = _semente(opcoes) if opcoes is not None else False
    if opcoes is None or semente is False or "--tipo" not in opcoes:
        print("uso: python -m fabrica fichas --tipo <tipo> [--semente N]", file=sys.stderr)
        return 2
    try:
        rodada, pecas = fichas.abrir_fichas(servicos, opcoes["--tipo"], semente)
    except (fichas.ErroFichas, ErroCongelamento) as erro:
        print(f"fichas recusado: {erro}", file=sys.stderr)
        return 1
    print(f"rodada {rodada}: {len(pecas)} pedido(s) de ficha gravado(s).")
    return 0


COMANDOS: dict[str, Comando] = {
    "avancar": comando_avancar,
    "ensaio": comando_ensaio,
    "fichas": comando_fichas,
    "preparar": comando_preparar,
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
