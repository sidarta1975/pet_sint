"""Bloqueio de rede de todos os testes (brief 006).

Durante a sessão de testes, abrir conexão de rede (AF_INET e AF_INET6, inclusive
127.0.0.1) falha com "teste tentou usar a rede". Canais locais entre processos
(AF_UNIX, socketpair) continuam livres. Um teste que esqueça o cliente falso e
tente falar com a API ou com o Ollama quebra o gate, em vez de gastar.
"""

from __future__ import annotations

import socket
from collections.abc import Iterator
from typing import Any

import pytest

MENSAGEM = "teste tentou usar a rede"
FAMILIAS_DE_REDE = (socket.AF_INET, socket.AF_INET6)


class RedeBloqueada(RuntimeError):
    """Conexão de rede tentada dentro de um teste."""


_connect_original = socket.socket.connect
_connect_ex_original = socket.socket.connect_ex


def _connect(self: socket.socket, endereco: Any) -> None:
    if self.family in FAMILIAS_DE_REDE:
        raise RedeBloqueada(f"{MENSAGEM}: {endereco!r}")
    _connect_original(self, endereco)


def _connect_ex(self: socket.socket, endereco: Any) -> int:
    if self.family in FAMILIAS_DE_REDE:
        raise RedeBloqueada(f"{MENSAGEM}: {endereco!r}")
    return _connect_ex_original(self, endereco)


def _create_connection(endereco: Any, *args: Any, **kwargs: Any) -> socket.socket:
    raise RedeBloqueada(f"{MENSAGEM}: {endereco!r}")


@pytest.fixture(autouse=True, scope="session")
def bloquear_rede() -> Iterator[None]:
    trocas = pytest.MonkeyPatch()
    trocas.setattr(socket.socket, "connect", _connect)
    trocas.setattr(socket.socket, "connect_ex", _connect_ex)
    trocas.setattr(socket, "create_connection", _create_connection)
    yield
    trocas.undo()
