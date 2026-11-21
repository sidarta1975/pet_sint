"""Congelamento da rodada (ARQUITETURA §4 e §5.12.2; ADR 001, itens 4 e 6).

Grava as impressões digitais de cada arquivo de `dados/` e de `instrucoes/`, de
`config/config.toml`, de `config/gasto.toml` e do código; confere antes de cada
passo; compara uma rodada com o ensaio aprovado. Não decide além disso: quem
para o passo é `estado.py` e quem recusa a rodada é o comando `fichas`.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from dataclasses import dataclass, field

from fabrica.comum.arquivos import RODADAS, Arquivos
from fabrica.comum.formatos import Ocorrencia, Rodada, Rodadas
from fabrica.comum.registro import Registro

PASTAS_CONGELADAS = ("dados", "instrucoes")
ARQUIVOS_CONGELADOS = ("config/config.toml", "config/gasto.toml")
CODIGO_FABRICA = "codigo:fabrica"
CODIGO_PYPROJECT = "codigo:pyproject.toml"
MUDANCA_PENDENTE = "codigo:mudança pendente"


class ErroCongelamento(Exception):
    """Rodada que não pode abrir ou que não existe."""


@dataclass(frozen=True)
class Resultado:
    parar: bool
    mudancas: list[str] = field(default_factory=list)


def _agora() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def diferencas(antes: dict[str, str], agora: dict[str, str]) -> list[str]:
    """Arquivos que mudaram, apareceram ou sumiram, em ordem."""
    return sorted(nome for nome in set(antes) | set(agora) if antes.get(nome) != agora.get(nome))


class Congelamento:
    def __init__(
        self,
        arquivos: Arquivos,
        registro: Registro,
        relogio: Callable[[], datetime.datetime] = _agora,
    ) -> None:
        self._arquivos = arquivos
        self._registro = registro
        self._relogio = relogio

    def impressoes(self) -> dict[str, str]:
        impressoes: dict[str, str] = {}
        for pasta in PASTAS_CONGELADAS:
            for relativo in self._arquivos.listar(pasta, "**/*"):
                impressoes[relativo] = self._arquivos.impressao(relativo)
        for relativo in ARQUIVOS_CONGELADOS:
            if self._arquivos.existe(relativo):
                impressoes[relativo] = self._arquivos.impressao(relativo)
        fabrica, pyproject = self._arquivos.impressao_codigo()
        impressoes[CODIGO_FABRICA] = fabrica
        impressoes[CODIGO_PYPROJECT] = pyproject
        return impressoes

    def _rodadas(self) -> Rodadas:
        if self._arquivos.existe(RODADAS):
            return self._arquivos.ler_json(RODADAS, Rodadas)
        return Rodadas(rodadas=[])

    def rodada(self, identificador: str) -> Rodada:
        for rodada in self._rodadas().rodadas:
            if rodada.id == identificador:
                return rodada
        raise ErroCongelamento(f"rodada {identificador} não existe em {RODADAS}")

    def abrir_rodada(
        self, identificador: str, semente: int, ensaio_aprovado_origem: str | None
    ) -> Rodada:
        if self._arquivos.mudanca_pendente():
            raise ErroCongelamento(
                "há mudança pendente em fabrica/, dados/, instrucoes/, config/ ou "
                "pyproject.toml: a rodada não abre"
            )
        rodadas = self._rodadas()
        if any(rodada.id == identificador for rodada in rodadas.rodadas):
            raise ErroCongelamento(f"rodada {identificador} já existe")
        rodada = Rodada(
            id=identificador,
            semente=semente,
            impressoes=self.impressoes(),
            ensaio_aprovado_origem=ensaio_aprovado_origem,
            estado="aberta",
            aberta_em=self._relogio(),
            ensaio_aprovado=False,
            aprovado_em=None,
        )
        self._arquivos.regravar_rodadas(Rodadas(rodadas=[*rodadas.rodadas, rodada]))
        return rodada

    def conferir(self, identificador: str, peca: str | None = None) -> Resultado:
        """Antes de cada passo: se algo mudou, 'parar', com a lista e a ocorrência."""
        rodada = self.rodada(identificador)
        mudancas = diferencas(rodada.impressoes, self.impressoes())
        if self._arquivos.mudanca_pendente():
            mudancas.append(MUDANCA_PENDENTE)
        if not mudancas:
            return Resultado(parar=False)
        self._registro.ocorrencia(
            Ocorrencia(
                tipo="parada",
                causa="congelamento",
                inicio=self._relogio(),
                fim=None,
                peca=peca,
                rodada=identificador,
                detalhe="mudou: " + ", ".join(mudancas),
            )
        )
        return Resultado(parar=True, mudancas=mudancas)

    def comparar(self, rodada: Rodada, ensaio: Rodada) -> list[str]:
        """Vazio quando iguais; senão, o que mudou desde o ensaio aprovado."""
        return diferencas(ensaio.impressoes, rodada.impressoes)
