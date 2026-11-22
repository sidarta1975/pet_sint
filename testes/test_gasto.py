"""Teste de aceite do brief 005: `fabrica/comum/gasto.py`."""

import datetime
import shutil
from pathlib import Path

import pytest

from fabrica.comum import config
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.formatos import Chamada, Tokens
from fabrica.comum.gasto import ControleGasto, ErroGasto, Previsto
from fabrica.comum.registro import Registro

RAIZ = Path(__file__).resolve().parent.parent
MOMENTO = datetime.datetime(2026, 11, 21, 10, 0, tzinfo=datetime.UTC)
MILHAO = 1_000_000  # milionésimos de centavo por centavo


@pytest.fixture
def raiz(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    for nome in ("config.toml", "gasto.toml"):
        shutil.copy(RAIZ / "config" / nome, tmp_path / "config" / nome)
    return tmp_path


def montar(raiz: Path) -> tuple[ControleGasto, Registro]:
    arquivos = Arquivos(raiz)
    registro = Registro(arquivos)
    return ControleGasto(config.carregar(arquivos), registro, relogio=lambda: MOMENTO), registro


def chamada(
    custo: int,
    rodada: str = "r01",
    peca: str = "r01_peticao_inicial_jec_001",
    tarefa: str = "extracao",
) -> Chamada:
    return Chamada(
        rodada=rodada,
        peca=peca,
        pedido=f"{peca}_v1_{tarefa}_t1",
        tarefa=tarefa,  # type: ignore[arg-type]
        modelo="claude-haiku-5-5",
        tokens_entrada=1,
        tokens_cache=0,
        tokens_raciocinio=0,
        tokens_saida=1,
        custo_milionesimos=custo,
        duracao_segundos=1.0,
        momento=MOMENTO,
    )


def test_custo_previsto_e_inteiro_em_milionesimos(raiz: Path) -> None:
    gasto, _ = montar(raiz)
    # Sonnet: 200 e 1000 centavos por milhão; redação de risco médio tem teto 16000.
    previsto = gasto.previsto("redacao_risco_medio", tokens_entrada=12_345)
    assert previsto == Previsto(
        modelo="claude-sonnet-5-5", tokens_entrada=12_345, teto_saida=16_000
    )
    custo = gasto.custo_previsto(previsto)
    assert isinstance(custo, int)
    assert custo == 12_345 * 200 + 16_000 * 1000


def test_haiku_ate_100_mil_tokens_preco_normal(raiz: Path) -> None:
    gasto, _ = montar(raiz)
    custo = gasto.custo_previsto(Previsto("claude-haiku-5-5", 100_000, 8_000))
    assert custo == 100_000 * 10 + 8_000 * 50


def test_haiku_acima_de_100_mil_tokens_preco_alto(raiz: Path) -> None:
    gasto, _ = montar(raiz)
    custo = gasto.custo_previsto(Previsto("claude-haiku-5-5", 100_001, 8_000))
    assert custo == 100_001 * 50 + 8_000 * 250
    real = gasto.custo_real(
        "claude-haiku-5-5", Tokens(entrada=100_001, cache=0, raciocinio=0, saida=10)
    )
    assert real == 100_001 * 50 + 10 * 250
    # O limite conta todos os tokens de entrada do pedido, inclusive os de cache.
    real = gasto.custo_real(
        "claude-haiku-5-5", Tokens(entrada=60_000, cache=40_001, raciocinio=0, saida=10)
    )
    assert real == 100_001 * 50 + 10 * 250


def test_custo_real_pelos_tokens(raiz: Path) -> None:
    gasto, _ = montar(raiz)
    # Opus: 400 e 2000. Raciocínio já vem dentro da saída.
    real = gasto.custo_real(
        "claude-opus-5-5", Tokens(entrada=1000, cache=500, raciocinio=300, saida=700)
    )
    assert real == 1500 * 400 + 700 * 2000


def test_modelo_desconhecido_recusado(raiz: Path) -> None:
    gasto, _ = montar(raiz)
    with pytest.raises(ErroGasto):
        gasto.custo_previsto(Previsto("claude-qualquer", 1, 1))


def test_previsao_soma_registrado_pendentes_e_novo(raiz: Path) -> None:
    gasto, registro = montar(raiz)
    registro.chamada(chamada(1_000 * MILHAO))
    pendentes = [Previsto("claude-sonnet-5-5", 10_000, 16_000)]
    novo = Previsto("claude-haiku-5-5", 5_000, 8_000)
    esperado = 1_000 * MILHAO + (10_000 * 200 + 16_000 * 1000) + (5_000 * 10 + 8_000 * 50)
    assert gasto.previsao_pessimista(novo, pendentes) == esperado


def test_pedido_que_passaria_do_corte_nao_e_autorizado(raiz: Path) -> None:
    gasto, registro = montar(raiz)
    novo = Previsto("claude-haiku-5-5", 1_000, 1_000)
    custo_novo = 1_000 * 10 + 1_000 * 50
    registro.chamada(chamada(10_000 * MILHAO - custo_novo + 1))
    decisao = gasto.autorizar(novo, [], rodada="r01", peca="r01_peticao_inicial_jec_001")
    assert not decisao.autorizado
    ocorrencias = registro.ocorrencias()
    assert len(ocorrencias) == 1
    assert ocorrencias[0].tipo == "parada"
    assert ocorrencias[0].causa == "corte_de_gasto"
    assert ocorrencias[0].peca == "r01_peticao_inicial_jec_001"


def test_pedido_que_deixa_exatamente_no_corte_e_autorizado(raiz: Path) -> None:
    gasto, registro = montar(raiz)
    novo = Previsto("claude-haiku-5-5", 1_000, 1_000)
    custo_novo = 1_000 * 10 + 1_000 * 50
    registro.chamada(chamada(10_000 * MILHAO - custo_novo))
    decisao = gasto.autorizar(novo, [], rodada="r01", peca=None)
    assert decisao.autorizado
    assert registro.ocorrencias() == []


def test_pendentes_contam_para_o_corte(raiz: Path) -> None:
    gasto, registro = montar(raiz)
    registro.chamada(chamada(9_990 * MILHAO))
    novo = Previsto("claude-haiku-5-5", 1_000, 1_000)  # 0,06 centavo
    pendentes = [Previsto("claude-opus-5-5", 10_000, 8_000)]  # 20 centavos
    assert gasto.autorizar(novo, [], rodada="r01", peca=None).autorizado
    assert not gasto.autorizar(novo, pendentes, rodada="r01", peca=None).autorizado


def test_alerta_dispara_uma_vez_e_nao_para(raiz: Path) -> None:
    gasto, registro = montar(raiz)
    novo = Previsto("claude-haiku-5-5", 1_000, 1_000)
    registro.chamada(chamada(2_999 * MILHAO))
    primeira = gasto.autorizar(novo, [], rodada="r01", peca=None)
    assert primeira.autorizado and not primeira.alerta
    registro.chamada(chamada(2 * MILHAO))
    segunda = gasto.autorizar(novo, [], rodada="r01", peca=None)
    assert segunda.autorizado and segunda.alerta
    registro.chamada(chamada(5 * MILHAO))
    terceira = gasto.autorizar(novo, [], rodada="r01", peca=None)
    assert terceira.autorizado and not terceira.alerta
    assert registro.ocorrencias() == []


def test_alerta_ja_passado_ao_comecar_nao_repete(raiz: Path) -> None:
    arquivos = Arquivos(raiz)
    registro = Registro(arquivos)
    registro.chamada(chamada(3_500 * MILHAO))
    gasto = ControleGasto(config.carregar(arquivos), registro, relogio=lambda: MOMENTO)
    decisao = gasto.autorizar(Previsto("claude-haiku-5-5", 1, 1), [], rodada="r01", peca=None)
    assert decisao.autorizado and not decisao.alerta


def test_corte_nao_sobe(raiz: Path) -> None:
    gasto, _ = montar(raiz)
    assert gasto.corte_milionesimos == 10_000 * MILHAO
    with pytest.raises(AttributeError):
        gasto.corte_milionesimos = 20_000 * MILHAO  # type: ignore[misc]


def test_total_gasto(raiz: Path) -> None:
    gasto, registro = montar(raiz)
    registro.chamada(chamada(10))
    registro.chamada(chamada(32))
    assert gasto.total_gasto() == 42


def test_custo_marginal_exclui_ensaio_copias_e_teste(raiz: Path) -> None:
    gasto, registro = montar(raiz)
    registro.chamada(chamada(100, tarefa="ficha"))
    registro.chamada(chamada(200, tarefa="redacao_risco_medio"))
    registro.chamada(chamada(300, tarefa="extracao"))
    registro.chamada(chamada(400, tarefa="checklist", peca="r01_embargos_declaracao_002"))
    registro.chamada(chamada(500, tarefa="conferencia_opus"))
    # Fora: ensaio, cópias com erro (criação, verificação) e o teste dos conferentes.
    registro.chamada(chamada(10_000, rodada="e01", peca="e01_peticao_inicial_jec_001"))
    registro.chamada(chamada(20_000, tarefa="copia_com_erro"))
    registro.chamada(chamada(30_000, tarefa="verificacao_copia"))
    registro.chamada(
        chamada(40_000, tarefa="checklist", peca="r01_peticao_inicial_jec_001_erro1_1")
    )
    assert gasto.custo_marginal("r01", pecas_aprovadas=3) == 1500 // 3
    with pytest.raises(ErroGasto):
        gasto.custo_marginal("r01", pecas_aprovadas=0)
