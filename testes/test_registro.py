"""Teste de aceite do brief 004: `fabrica/comum/registro.py`."""

import datetime
from pathlib import Path

from fabrica.comum.arquivos import Arquivos
from fabrica.comum.formatos import Chamada, Ocorrencia
from fabrica.comum.registro import Registro

UTC = datetime.UTC
MOMENTO = datetime.datetime(2026, 11, 21, 10, 0, tzinfo=UTC)


def chamada(custo: int) -> Chamada:
    return Chamada(
        rodada="e01",
        peca="e01_peticao_inicial_jec_001",
        pedido="e01_peticao_inicial_jec_001_v1_extracao_t1",
        tarefa="extracao",
        modelo="claude-haiku-5-5",
        tokens_entrada=100,
        tokens_cache=10,
        tokens_raciocinio=0,
        tokens_saida=50,
        custo_milionesimos=custo,
        duracao_segundos=1.5,
        momento=MOMENTO,
    )


def ocorrencia() -> Ocorrencia:
    return Ocorrencia(
        tipo="pausa",
        causa="api",
        inicio=MOMENTO,
        fim=None,
        peca=None,
        rodada="e01",
        detalhe="",
    )


def test_cada_chamada_e_ocorrencia_vira_uma_linha(tmp_path: Path) -> None:
    registro = Registro(Arquivos(tmp_path))
    registro.chamada(chamada(10))
    registro.chamada(chamada(20))
    registro.ocorrencia(ocorrencia())
    linhas = (tmp_path / "saida/registro/chamadas.jsonl").read_text().splitlines()
    assert len(linhas) == 2
    assert all(Chamada.model_validate_json(linha) for linha in linhas)
    linhas = (tmp_path / "saida/registro/ocorrencias.jsonl").read_text().splitlines()
    assert [Ocorrencia.model_validate_json(linha) for linha in linhas] == [ocorrencia()]
    assert registro.chamadas() == [chamada(10), chamada(20)]
    assert registro.ocorrencias() == [ocorrencia()]


def test_ultima_linha_incompleta_ignorada(tmp_path: Path) -> None:
    registro = Registro(Arquivos(tmp_path))
    registro.chamada(chamada(10))
    with (tmp_path / "saida/registro/chamadas.jsonl").open("a") as saida:
        saida.write('{"rodada": "e01", "pec')
    assert registro.chamadas() == [chamada(10)]


def test_soma_do_custo_bate(tmp_path: Path) -> None:
    registro = Registro(Arquivos(tmp_path))
    custos = [3500, 0, 125, 999_999, 7]
    for custo in custos:
        registro.chamada(chamada(custo))
    assert Registro(Arquivos(tmp_path)).custo_total_milionesimos() == sum(custos)
    assert Registro(Arquivos(tmp_path / "vazio")).custo_total_milionesimos() == 0
