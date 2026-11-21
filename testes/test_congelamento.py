"""Teste de aceite do brief 005: `fabrica/comum/congelamento.py`."""

import datetime
import shutil
import subprocess
from pathlib import Path

import pytest

from fabrica.comum.arquivos import Arquivos
from fabrica.comum.congelamento import Congelamento, ErroCongelamento
from fabrica.comum.formatos import Rodadas
from fabrica.comum.registro import Registro

RAIZ = Path(__file__).resolve().parent.parent
MOMENTO = datetime.datetime(2026, 11, 21, 10, 0, tzinfo=datetime.UTC)


def git(raiz: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=raiz, check=True, capture_output=True)


def commit(raiz: Path, *caminhos: str, mensagem: str = "x") -> None:
    git(raiz, "add", *caminhos)
    git(raiz, "commit", "-q", "-m", mensagem)


@pytest.fixture
def raiz(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "teste@ficticio.example")
    git(tmp_path, "config", "user.name", "Teste")
    for pasta in ("dados", "instrucoes", "config", "fabrica", "docs", "dados/sub"):
        (tmp_path / pasta).mkdir()
    (tmp_path / "dados/tipos.json").write_text('{"tipos": []}\n')
    (tmp_path / "dados/sub/matriz.json").write_text('{"m": 1}\n')
    (tmp_path / "instrucoes/ficha.md").write_text("Instrução de exemplo.\n")
    for nome in ("config.toml", "gasto.toml"):
        shutil.copy(RAIZ / "config" / nome, tmp_path / "config" / nome)
    (tmp_path / "fabrica/__init__.py").write_text("")
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    (tmp_path / "docs/nota.md").write_text("nota\n")
    (tmp_path / ".gitignore").write_text("saida/\n")
    commit(tmp_path, ".")
    return tmp_path


class Relogio:
    """Relógio que anda um segundo a cada leitura, como o de verdade anda."""

    def __init__(self) -> None:
        self.agora = MOMENTO

    def __call__(self) -> datetime.datetime:
        self.agora += datetime.timedelta(seconds=1)
        return self.agora


def montar(raiz: Path) -> tuple[Congelamento, Registro, Arquivos]:
    relogio = Relogio()
    arquivos = Arquivos(raiz, relogio=relogio)
    registro = Registro(arquivos)
    return Congelamento(arquivos, registro, relogio=relogio), registro, arquivos


def test_abrir_rodada_grava_as_impressoes(raiz: Path) -> None:
    congelamento, _, arquivos = montar(raiz)
    rodada = congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)
    gravadas = arquivos.ler_json("saida/rodadas.json", Rodadas)
    assert gravadas.rodadas == [rodada]
    assert rodada.estado == "aberta"
    assert rodada.semente == 7
    assert set(rodada.impressoes) == {
        "dados/tipos.json",
        "dados/sub/matriz.json",
        "instrucoes/ficha.md",
        "config/config.toml",
        "config/gasto.toml",
        "codigo:fabrica",
        "codigo:pyproject.toml",
    }


def test_nada_mudou_segue(raiz: Path) -> None:
    congelamento, registro, _ = montar(raiz)
    congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)
    resultado = congelamento.conferir("e01")
    assert not resultado.parar
    assert resultado.mudancas == []
    assert registro.ocorrencias() == []


@pytest.mark.parametrize(
    "arquivo",
    ["dados/tipos.json", "dados/sub/matriz.json", "config/gasto.toml", "instrucoes/ficha.md"],
)
def test_mudar_uma_letra_para(raiz: Path, arquivo: str) -> None:
    congelamento, registro, _ = montar(raiz)
    congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)
    caminho = raiz / arquivo
    texto = caminho.read_text()
    caminho.write_text(texto.replace("a", "e", 1) if "a" in texto else texto + "x")
    commit(raiz, arquivo)  # mesmo commitada, a mudança para a rodada
    resultado = congelamento.conferir("e01", peca="e01_peticao_inicial_jec_001")
    assert resultado.parar
    assert arquivo in resultado.mudancas
    ocorrencias = registro.ocorrencias()
    assert len(ocorrencias) == 1
    assert ocorrencias[0].tipo == "parada"
    assert ocorrencias[0].causa == "congelamento"
    assert arquivo in ocorrencias[0].detalhe
    assert ocorrencias[0].peca == "e01_peticao_inicial_jec_001"


def test_mudanca_sem_commit_tambem_para(raiz: Path) -> None:
    congelamento, _, _ = montar(raiz)
    congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)
    (raiz / "dados/tipos.json").write_text('{"tipos": [1]}\n')
    resultado = congelamento.conferir("e01")
    assert resultado.parar
    assert "dados/tipos.json" in resultado.mudancas


@pytest.mark.parametrize("pasta", ["dados", "instrucoes"])
def test_arquivo_novo_para(raiz: Path, pasta: str) -> None:
    congelamento, _, _ = montar(raiz)
    congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)
    (raiz / pasta / "novo.md").write_text("novo\n")
    commit(raiz, f"{pasta}/novo.md")
    resultado = congelamento.conferir("e01")
    assert resultado.parar
    assert f"{pasta}/novo.md" in resultado.mudancas


@pytest.mark.parametrize("arquivo", ["dados/tipos.json", "instrucoes/ficha.md"])
def test_arquivo_apagado_para(raiz: Path, arquivo: str) -> None:
    congelamento, _, _ = montar(raiz)
    congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)
    git(raiz, "rm", "-q", arquivo)
    git(raiz, "commit", "-q", "-m", "apaga")
    resultado = congelamento.conferir("e01")
    assert resultado.parar
    assert arquivo in resultado.mudancas


def test_mudanca_no_codigo_commitada_para(raiz: Path) -> None:
    congelamento, _, _ = montar(raiz)
    congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)
    (raiz / "fabrica/__init__.py").write_text("x = 1\n")
    commit(raiz, "fabrica/__init__.py")
    resultado = congelamento.conferir("e01")
    assert resultado.parar
    assert "codigo:fabrica" in resultado.mudancas


def test_mudanca_pendente_em_fabrica_impede_abrir(raiz: Path) -> None:
    congelamento, _, arquivos = montar(raiz)
    (raiz / "fabrica/__init__.py").write_text("x = 1\n")
    with pytest.raises(ErroCongelamento, match="mudança pendente"):
        congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)
    assert not arquivos.existe("saida/rodadas.json")


def test_commit_so_em_docs_nao_muda_impressao(raiz: Path) -> None:
    congelamento, _, _ = montar(raiz)
    antes = congelamento.impressoes()
    (raiz / "docs/nota.md").write_text("outra nota\n")
    commit(raiz, "docs/nota.md")
    assert congelamento.impressoes() == antes
    congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)
    (raiz / "docs/nota.md").write_text("mais uma\n")
    commit(raiz, "docs/nota.md")
    assert not congelamento.conferir("e01").parar


def test_comparar_com_ensaio_aprovado(raiz: Path) -> None:
    congelamento, _, _ = montar(raiz)
    ensaio = congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)
    rodada = congelamento.abrir_rodada("r01", semente=8, ensaio_aprovado_origem="e01")
    assert congelamento.comparar(rodada, ensaio) == []
    (raiz / "instrucoes/ficha.md").write_text("Outra instrução.\n")
    commit(raiz, "instrucoes/ficha.md")
    nova = congelamento.abrir_rodada("r02", semente=9, ensaio_aprovado_origem="e01")
    assert congelamento.comparar(nova, ensaio) == ["instrucoes/ficha.md"]


def test_segunda_rodada_preserva_a_primeira(raiz: Path) -> None:
    congelamento, _, arquivos = montar(raiz)
    congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)
    congelamento.abrir_rodada("e02", semente=8, ensaio_aprovado_origem=None)
    gravadas = arquivos.ler_json("saida/rodadas.json", Rodadas)
    assert [r.id for r in gravadas.rodadas] == ["e01", "e02"]
    with pytest.raises(ErroCongelamento, match="já existe"):
        congelamento.abrir_rodada("e01", semente=7, ensaio_aprovado_origem=None)


def test_rodada_desconhecida_recusada(raiz: Path) -> None:
    congelamento, _, _ = montar(raiz)
    with pytest.raises(ErroCongelamento):
        congelamento.conferir("e09")
