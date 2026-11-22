"""Teste de aceite do brief 005: `fabrica/comum/estatistica.py`."""

import pytest

from fabrica.comum.estatistica import ErroEstatistica, criterio_central_passa, wilson


def pct(valor: float) -> float:
    return round(valor * 100, 1)


def test_80_em_100() -> None:
    intervalo = wilson(80, 100)
    assert intervalo.taxa == 0.8
    assert round(intervalo.inferior * 100) == 71
    assert round(intervalo.superior * 100) == 87


def test_32_em_40_limite_inferior() -> None:
    assert pct(wilson(32, 40).inferior) == 65.2


def test_28_em_35_limite_inferior() -> None:
    assert pct(wilson(28, 35).inferior) == 64.1


def test_5_em_5() -> None:
    intervalo = wilson(5, 5)
    assert round(intervalo.inferior * 100) == 57
    assert intervalo.superior == pytest.approx(1.0)


def test_2_em_25() -> None:
    intervalo = wilson(2, 25)
    assert round(intervalo.inferior * 100) == 2
    assert round(intervalo.superior * 100) == 25


def test_zero_em_zero_recusado() -> None:
    with pytest.raises(ErroEstatistica):
        wilson(0, 0)


@pytest.mark.parametrize(("sucessos", "total"), [(-1, 5), (6, 5), (1, -1)])
def test_contagem_impossivel_recusada(sucessos: int, total: int) -> None:
    with pytest.raises(ErroEstatistica):
        wilson(sucessos, total)


def test_criterio_central() -> None:
    assert criterio_central_passa(wilson(32, 40), taxa_minima=0.80, limite_inferior_minimo=0.65)
    assert not criterio_central_passa(wilson(28, 35), taxa_minima=0.80, limite_inferior_minimo=0.65)
    assert not criterio_central_passa(
        wilson(79, 100), taxa_minima=0.80, limite_inferior_minimo=0.65
    )
