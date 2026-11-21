"""Teste de aceite do brief 004: `fabrica/comum/arquivos.py`."""

import datetime
import json
import subprocess
from pathlib import Path

import pytest

from fabrica.comum import arquivos as modulo
from fabrica.comum.arquivos import Arquivos, ErroArquivo
from fabrica.comum.formatos import Rodada, Rodadas, Tokens

UTC = datetime.UTC


def relogio_fixo() -> datetime.datetime:
    return datetime.datetime(2026, 11, 21, 10, 0, 0, 123456, tzinfo=UTC)


@pytest.fixture
def arq(tmp_path: Path) -> Arquivos:
    return Arquivos(tmp_path, relogio=relogio_fixo)


def tokens(n: int = 1) -> Tokens:
    return Tokens(entrada=n, cache=0, raciocinio=0, saida=n)


def rodada(estado: str = "aberta") -> Rodada:
    return Rodada.model_validate_json(
        json.dumps(
            {
                "id": "e01",
                "semente": 7,
                "impressoes": {},
                "ensaio_aprovado_origem": None,
                "estado": estado,
                "aberta_em": "2026-11-21T10:00:00+00:00",
                "ensaio_aprovado": False,
                "aprovado_em": None,
            }
        )
    )


def test_grava_e_le_json_validado(arq: Arquivos, tmp_path: Path) -> None:
    arq.gravar_json("saida/x/a.json", tokens(3))
    assert (tmp_path / "saida/x/a.json").exists()
    assert arq.ler_json("saida/x/a.json", Tokens) == tokens(3)


def test_gravar_arquivo_que_ja_existe_e_recusado(arq: Arquivos) -> None:
    arq.gravar_json("saida/a.json", tokens())
    with pytest.raises(ErroArquivo, match="já existe"):
        arq.gravar_json("saida/a.json", tokens(2))
    assert arq.ler_json("saida/a.json", Tokens) == tokens()
    arq.gravar_texto("saida/a.md", "um")
    with pytest.raises(ErroArquivo, match="já existe"):
        arq.gravar_texto("saida/a.md", "dois")


def test_arquivo_final_so_aparece_completo(
    arq: Arquivos, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def renomear_falha(origem: Path, destino: Path) -> None:
        raise OSError("interrompido no meio")

    monkeypatch.setattr(modulo, "_renomear", renomear_falha)
    with pytest.raises(OSError):
        arq.gravar_texto("saida/peca.md", "texto completo")
    restos = sorted(p.name for p in (tmp_path / "saida").iterdir())
    assert len(restos) == 1
    assert restos[0].startswith("peca.md.tmp-")
    assert not (tmp_path / "saida/peca.md").exists()


def test_temporario_ignorado_na_leitura_e_na_listagem(arq: Arquivos, tmp_path: Path) -> None:
    arq.gravar_texto("saida/p/a.md", "a")
    (tmp_path / "saida/p/b.md.tmp-abc123").write_text("meio", encoding="utf-8")
    assert arq.listar("saida/p", "*.md") == ["saida/p/a.md"]
    assert arq.listar("saida/p", "*") == ["saida/p/a.md"]
    assert not arq.existe("saida/p/b.md")
    with pytest.raises(ErroArquivo):
        arq.ler_texto("saida/p/b.md.tmp-abc123")


def test_arquivo_fora_do_formato_e_recusado(arq: Arquivos, tmp_path: Path) -> None:
    destino = tmp_path / "saida/ruim.json"
    destino.parent.mkdir(parents=True)
    destino.write_text('{"entrada": 1, "cache": 0, "raciocinio": 0}', encoding="utf-8")
    with pytest.raises(ErroArquivo, match="fora do formato"):
        arq.ler_json("saida/ruim.json", Tokens)
    destino.write_text("não é json", encoding="utf-8")
    with pytest.raises(ErroArquivo, match="fora do formato"):
        arq.ler_json("saida/ruim.json", Tokens)


def test_rodadas_regravado_com_copia_anterior(arq: Arquivos, tmp_path: Path) -> None:
    arq.regravar_rodadas(Rodadas(rodadas=[rodada()]))
    assert not (tmp_path / "saida/registro/rodadas_anteriores").exists()
    arq.regravar_rodadas(Rodadas(rodadas=[rodada("encerrada")]))
    atual = arq.ler_json("saida/rodadas.json", Rodadas)
    assert atual.rodadas[0].estado == "encerrada"
    copias = arq.listar("saida/registro/rodadas_anteriores", "rodadas_*.json")
    assert len(copias) == 1
    anterior = arq.ler_json(copias[0], Rodadas)
    assert anterior.rodadas[0].estado == "aberta"


def test_rodadas_so_pelo_caminho_proprio(arq: Arquivos) -> None:
    arq.regravar_rodadas(Rodadas(rodadas=[rodada()]))
    with pytest.raises(ErroArquivo, match="já existe"):
        arq.gravar_json("saida/rodadas.json", Rodadas(rodadas=[]))


@pytest.mark.parametrize(
    "caminho",
    ["../fora.json", "/tmp/fora.json", "config/novo.json", "dados/novo.json", "saida/../x.json"],
)
def test_gravar_fora_da_pasta_de_saida_e_recusado(arq: Arquivos, caminho: str) -> None:
    with pytest.raises(ErroArquivo, match="fora da pasta"):
        arq.gravar_json(caminho, tokens())


def test_ler_fora_das_pastas_permitidas_e_recusado(arq: Arquivos) -> None:
    with pytest.raises(ErroArquivo, match="fora da pasta"):
        arq.ler_texto("../segredo.txt")
    with pytest.raises(ErroArquivo, match="fora da pasta"):
        arq.ler_texto("docs/PLAN.md")


def test_le_de_config_dados_e_instrucoes(arq: Arquivos, tmp_path: Path) -> None:
    for pasta in ("config", "dados", "instrucoes"):
        (tmp_path / pasta).mkdir()
        (tmp_path / pasta / "a.txt").write_text(pasta, encoding="utf-8")
        assert arq.ler_texto(f"{pasta}/a.txt") == pasta


def test_jsonl_acrescenta_e_ignora_ultima_linha_incompleta(arq: Arquivos, tmp_path: Path) -> None:
    arq.acrescentar_linha("saida/registro/x.jsonl", tokens(1))
    arq.acrescentar_linha("saida/registro/x.jsonl", tokens(2))
    with (tmp_path / "saida/registro/x.jsonl").open("a", encoding="utf-8") as saida:
        saida.write('{"entrada": 3, "cach')
    assert arq.ler_linhas("saida/registro/x.jsonl", Tokens) == [tokens(1), tokens(2)]
    assert arq.ler_linhas("saida/registro/nada.jsonl", Tokens) == []


def test_jsonl_linha_quebrada_no_meio_e_recusada(arq: Arquivos, tmp_path: Path) -> None:
    destino = tmp_path / "saida/registro/x.jsonl"
    destino.parent.mkdir(parents=True)
    destino.write_text('{"quebrada"\n{"entrada": 1, "cache": 0, "raciocinio": 0, "saida": 1}\n')
    with pytest.raises(ErroArquivo, match="fora do formato"):
        arq.ler_linhas("saida/registro/x.jsonl", Tokens)


def test_impressao_digital_do_conteudo(arq: Arquivos) -> None:
    arq.gravar_texto("saida/a.md", "abc")
    assert arq.impressao("saida/a.md") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def _git(raiz: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=raiz, check=True, capture_output=True)


def test_impressao_do_codigo_pelo_git(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "teste@ficticio.example")
    _git(tmp_path, "config", "user.name", "Teste")
    (tmp_path / "fabrica").mkdir()
    (tmp_path / "fabrica/a.py").write_text("x = 1\n")
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    _git(tmp_path, "add", "fabrica/a.py", "pyproject.toml")
    _git(tmp_path, "commit", "-q", "-m", "um")
    arq = Arquivos(tmp_path, relogio=relogio_fixo)
    primeira = arq.impressao_codigo()
    assert len(primeira) == 2 and all(len(parte) == 40 for parte in primeira)
    assert not arq.mudanca_pendente()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/nota.md").write_text("não conta\n")
    (tmp_path / "saida").mkdir()
    (tmp_path / "saida/x.json").write_text("{}\n")
    assert not arq.mudanca_pendente()
    (tmp_path / "fabrica/a.py").write_text("x = 2\n")
    assert arq.mudanca_pendente()
    _git(tmp_path, "add", "fabrica/a.py")
    _git(tmp_path, "commit", "-q", "-m", "dois")
    assert arq.impressao_codigo()[0] != primeira[0]
    assert arq.impressao_codigo()[1] == primeira[1]
    (tmp_path / "config").mkdir()
    (tmp_path / "config/novo.toml").write_text("")
    assert arq.mudanca_pendente()
