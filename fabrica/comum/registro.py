"""Registro das chamadas e das ocorrências (ARQUITETURA §7.3 e §7.4).

`saida/registro/chamadas.jsonl` e `saida/registro/ocorrencias.jsonl`, uma linha
por evento, sempre por `arquivos.py`.
"""

from __future__ import annotations

from fabrica.comum.arquivos import Arquivos
from fabrica.comum.formatos import Chamada, Ocorrencia

CHAMADAS = "saida/registro/chamadas.jsonl"
OCORRENCIAS = "saida/registro/ocorrencias.jsonl"


class Registro:
    def __init__(self, arquivos: Arquivos) -> None:
        self.arquivos = arquivos

    def chamada(self, chamada: Chamada) -> None:
        self.arquivos.acrescentar_linha(CHAMADAS, chamada)

    def ocorrencia(self, ocorrencia: Ocorrencia) -> None:
        self.arquivos.acrescentar_linha(OCORRENCIAS, ocorrencia)

    def chamadas(self) -> list[Chamada]:
        return self.arquivos.ler_linhas(CHAMADAS, Chamada)

    def ocorrencias(self) -> list[Ocorrencia]:
        return self.arquivos.ler_linhas(OCORRENCIAS, Ocorrencia)

    def custo_total_milionesimos(self) -> int:
        return sum(chamada.custo_milionesimos for chamada in self.chamadas())
