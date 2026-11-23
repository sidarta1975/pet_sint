"""Teste de aceite do brief 004: `fabrica/comum/config.py`."""

import copy
import datetime
import shutil
import tomllib
from pathlib import Path
from typing import Any

import pytest

from fabrica.comum import config
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.config import ErroConfiguracao
from testes import apoio_config

RAIZ = Path(__file__).resolve().parent.parent


def originais() -> tuple[dict[str, Any], dict[str, Any]]:
    with (RAIZ / "config/config.toml").open("rb") as entrada:
        geral = tomllib.load(entrada)
    with (RAIZ / "config/gasto.toml").open("rb") as entrada:
        gasto = tomllib.load(entrada)
    return geral, gasto


def folhas(dados: dict[str, Any], prefixo: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    caminhos: list[tuple[str, ...]] = []
    for chave, valor in dados.items():
        caminho = (*prefixo, chave)
        caminhos.append(caminho)
        if isinstance(valor, dict):
            caminhos.extend(folhas(valor, caminho))
    return caminhos


def pai(dados: dict[str, Any], caminho: tuple[str, ...]) -> dict[str, Any]:
    for chave in caminho[:-1]:
        dados = dados[chave]
    return dados


class ClienteFalso:
    def __init__(self) -> None:
        self.chamadas = 0

    def enviar(self) -> None:
        self.chamadas += 1


def carregar_e_chamar(arquivos: Arquivos, cliente: ClienteFalso) -> None:
    """O que a fábrica faz: primeiro a configuração, só depois qualquer cliente."""
    config.carregar(arquivos)
    cliente.enviar()


@pytest.fixture
def raiz(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    for nome in ("config.toml", "gasto.toml"):
        shutil.copy(RAIZ / "config" / nome, tmp_path / "config" / nome)
    return tmp_path


def test_leitura_entrega_todos_os_valores(raiz: Path) -> None:
    lida = config.carregar(Arquivos(raiz))
    geral, gasto = originais()
    assert lida.geral.model_dump(mode="json") == _como_json(geral)
    assert lida.gasto.model_dump(mode="json") == gasto
    assert lida.geral.modelos.haiku.id == "claude-haiku-5-5"
    assert lida.geral.modelos.data_conferencia == datetime.date(2026, 11, 21)
    assert lida.geral.tarefas.redacao_risco_alto.esforco == "medium"
    assert lida.geral.janela_local.inicio == datetime.time.fromisoformat(
        geral["janela_local"]["inicio"]
    )
    assert lida.gasto.corte_centavos == 10000


def _como_json(geral: dict[str, Any]) -> dict[str, Any]:
    esperado = copy.deepcopy(geral)
    local = esperado["modelo_local"]
    for chave in ("etiqueta_completa", "digest"):
        if local[chave] == "":
            local[chave] = None
    esperado["janela_local"] = {
        chave: valor + ":00" for chave, valor in esperado["janela_local"].items()
    }
    return esperado


def test_pendente_vazio_lido_como_ausente(raiz: Path) -> None:
    caminho = raiz / "config/config.toml"
    caminho.write_text(apoio_config.provisorio(caminho.read_text("utf-8")), "utf-8")
    lida = config.carregar(Arquivos(raiz))
    assert lida.geral.modelo_local.etiqueta_completa is None
    assert lida.geral.modelo_local.digest is None


@pytest.mark.parametrize("caminho", folhas(originais()[0]), ids=".".join)
def test_chave_faltando_para_com_o_nome(caminho: tuple[str, ...]) -> None:
    geral, gasto = originais()
    del pai(geral, caminho)[caminho[-1]]
    with pytest.raises(ErroConfiguracao) as erro:
        config.validar(geral, gasto)
    assert ".".join(caminho) in str(erro.value)
    assert "config.toml" in str(erro.value)


@pytest.mark.parametrize("chave", ["alerta_centavos", "corte_centavos"])
def test_chave_do_gasto_faltando_para(chave: str) -> None:
    geral, gasto = originais()
    del gasto[chave]
    with pytest.raises(ErroConfiguracao, match=f"gasto.toml.*{chave}"):
        config.validar(geral, gasto)


def _trocado(valor: Any) -> Any:
    if isinstance(valor, bool):
        return "sim"
    if isinstance(valor, int | float):
        return "texto"
    if isinstance(valor, str):
        return 7
    if isinstance(valor, list):
        return "lista"
    return None


@pytest.mark.parametrize(
    "caminho",
    [c for c in folhas(originais()[0]) if not isinstance(pai(originais()[0], c)[c[-1]], dict)],
    ids=".".join,
)
def test_tipo_trocado_para_com_o_nome(caminho: tuple[str, ...]) -> None:
    geral, gasto = originais()
    alvo = pai(geral, caminho)
    alvo[caminho[-1]] = _trocado(alvo[caminho[-1]])
    with pytest.raises(ErroConfiguracao) as erro:
        config.validar(geral, gasto)
    assert ".".join(caminho) in str(erro.value)


def test_tipo_trocado_no_gasto_para() -> None:
    geral, gasto = originais()
    gasto["corte_centavos"] = 100.5
    with pytest.raises(ErroConfiguracao, match="corte_centavos"):
        config.validar(geral, gasto)


@pytest.mark.parametrize("onde", [(), ("modelos",), ("modelos", "haiku"), ("tarefas", "ficha")])
def test_chave_desconhecida_para_com_o_nome(onde: tuple[str, ...]) -> None:
    geral, gasto = originais()
    alvo = geral
    for chave in onde:
        alvo = alvo[chave]
    alvo["chave_inventada"] = 1
    with pytest.raises(ErroConfiguracao) as erro:
        config.validar(geral, gasto)
    assert ".".join((*onde, "chave_inventada")) in str(erro.value)


def test_chave_desconhecida_no_gasto_para() -> None:
    geral, gasto = originais()
    gasto["teto_extra"] = 1
    with pytest.raises(ErroConfiguracao, match="teto_extra"):
        config.validar(geral, gasto)


def test_erro_para_antes_de_qualquer_cliente(raiz: Path) -> None:
    texto = (raiz / "config/config.toml").read_text(encoding="utf-8")
    (raiz / "config/config.toml").write_text(
        texto.replace("pecas_por_tipo = 10", 'pecas_por_tipo = "dez"'), encoding="utf-8"
    )
    cliente = ClienteFalso()
    with pytest.raises(ErroConfiguracao, match="volume.pecas_por_tipo"):
        carregar_e_chamar(Arquivos(raiz), cliente)
    assert cliente.chamadas == 0


def test_arquivo_que_nao_e_toml_para(raiz: Path) -> None:
    (raiz / "config/gasto.toml").write_text("alerta_centavos = = 3\n", encoding="utf-8")
    cliente = ClienteFalso()
    with pytest.raises(ErroConfiguracao, match="gasto.toml"):
        carregar_e_chamar(Arquivos(raiz), cliente)
    assert cliente.chamadas == 0
