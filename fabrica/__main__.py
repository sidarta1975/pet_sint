"""Ponto de entrada único: `python -m fabrica <comando>` (ARQUITETURA §8).

Não tem lógica de etapa. Lê o comando e chama a função registrada para ele.
Nenhum comando está registrado ainda: cada brief que cria um comando
acrescenta a sua linha em `COMANDOS` (PLANO §4, regras para todas as fases).
"""

import sys
from collections.abc import Callable, Sequence

COMANDOS: dict[str, Callable[[Sequence[str]], int]] = {}


def principal(argumentos: Sequence[str]) -> int:
    """Executa o comando pedido; recusa comando ausente ou desconhecido."""
    if not argumentos:
        print("uso: python -m fabrica <comando>", file=sys.stderr)
        return 2
    comando = argumentos[0]
    funcao = COMANDOS.get(comando)
    if funcao is None:
        print(f"comando desconhecido: {comando}", file=sys.stderr)
        return 2
    return funcao(argumentos[1:])


if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))
