"""Intervalo de Wilson de 95% e o critério central (ARQUITETURA §2.4 e §6)."""

from __future__ import annotations

import math
from dataclasses import dataclass

Z_95 = 1.96


class ErroEstatistica(Exception):
    """Contagem impossível (zero em zero, negativa ou acertos acima do total)."""


@dataclass(frozen=True)
class Intervalo:
    sucessos: int
    total: int
    taxa: float
    inferior: float
    superior: float


def wilson(sucessos: int, total: int, z: float = Z_95) -> Intervalo:
    if total <= 0:
        raise ErroEstatistica(f"intervalo sem nenhum caso ({sucessos} em {total})")
    if sucessos < 0 or sucessos > total:
        raise ErroEstatistica(f"contagem impossível: {sucessos} em {total}")
    taxa = sucessos / total
    z2 = z * z
    centro = (taxa + z2 / (2 * total)) / (1 + z2 / total)
    margem = (z / (1 + z2 / total)) * math.sqrt(
        taxa * (1 - taxa) / total + z2 / (4 * total * total)
    )
    return Intervalo(
        sucessos=sucessos,
        total=total,
        taxa=taxa,
        inferior=max(0.0, centro - margem),
        superior=min(1.0, centro + margem),
    )


def criterio_central_passa(
    intervalo: Intervalo, taxa_minima: float, limite_inferior_minimo: float
) -> bool:
    """Taxa de pelo menos `taxa_minima` e limite inferior de pelo menos o mínimo (config)."""
    return intervalo.taxa >= taxa_minima and intervalo.inferior >= limite_inferior_minimo
