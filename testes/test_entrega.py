"""Teste de aceite do brief 001: script de entrega e trava de git.

Roda num repositório git temporário, com um `scripts/verificar.sh` falso
(verde ou vermelho) e os `entregar.sh` e `trava_git.sh` verdadeiros copiados
para ele. Não usa rede.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
ENTREGAR = RAIZ / "scripts" / "entregar.sh"
TRAVA = RAIZ / "scripts" / "trava_git.sh"

GATE_VERDE = "#!/usr/bin/env bash\nexit 0\n"
GATE_VERMELHO = "#!/usr/bin/env bash\necho 'gate falso vermelho' >&2\nexit 1\n"


def _git(repo: Path, *args: str) -> str:
    resultado = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return resultado.stdout


def _relatorio(manifesto: str) -> str:
    return (
        "# Relatório 001\n\n"
        "## RELATÓRIO FINAL\n"
        "- Brief executado: 001\n"
        "- Lista de arquivos para `git add` e texto do commit:\n\n"
        "```\n"
        f"{manifesto}"
        "```\n\n"
        "- Pendências e decisões que ficaram abertas: nenhuma\n"
    )


def _montar_repo(tmp_path: Path, gate: str) -> Path:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "docs" / "docs").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Teste")
    _git(repo, "config", "user.email", "teste@teste.example")
    _git(repo, "config", "commit.gpgsign", "false")
    shutil.copy(ENTREGAR, repo / "scripts" / "entregar.sh")
    shutil.copy(TRAVA, repo / "scripts" / "trava_git.sh")
    verificar = repo / "scripts" / "verificar.sh"
    verificar.write_text(gate, encoding="utf-8")
    for script in ("entregar.sh", "trava_git.sh", "verificar.sh"):
        (repo / "scripts" / script).chmod(0o755)
    (repo / "antigo.txt").write_text("arquivo a remover\n", encoding="utf-8")
    (repo / "fica.txt").write_text("arquivo que fica\n", encoding="utf-8")
    _git(
        repo,
        "add",
        "scripts/entregar.sh",
        "scripts/trava_git.sh",
        "scripts/verificar.sh",
        "antigo.txt",
        "fica.txt",
    )
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def _entregar(repo: Path, numero: str = "001") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/entregar.sh", numero],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def _numero_de_commits(repo: Path) -> int:
    return int(_git(repo, "rev-list", "--count", "HEAD").strip())


def _preparar_entrega(repo: Path, manifesto: str) -> None:
    (repo / "novo.txt").write_text("conteúdo novo\n", encoding="utf-8")
    (repo / "docs" / "docs" / "doc_001_teste_2026-11-21.md").write_text(
        _relatorio(manifesto), encoding="utf-8"
    )


MANIFESTO_COMPLETO = (
    "novo.txt\n"
    "docs/docs/doc_001_teste_2026-11-21.md\n"
    "remover: antigo.txt\n"
    "\n"
    "Brief 001: entrega de teste\n"
    "\n"
    "Segunda linha do texto do commit.\n"
)


def test_recusa_commit_com_gate_vermelho(tmp_path: Path) -> None:
    repo = _montar_repo(tmp_path, GATE_VERMELHO)
    _preparar_entrega(repo, MANIFESTO_COMPLETO)
    antes = _numero_de_commits(repo)

    resultado = _entregar(repo)

    assert resultado.returncode != 0
    assert "gate" in resultado.stderr.lower()
    assert _numero_de_commits(repo) == antes
    assert _git(repo, "diff", "--cached", "--name-only") == ""


def test_recusa_arquivo_fora_do_manifesto(tmp_path: Path) -> None:
    repo = _montar_repo(tmp_path, GATE_VERDE)
    _preparar_entrega(repo, MANIFESTO_COMPLETO)
    (repo / "intruso.txt").write_text("fora do manifesto\n", encoding="utf-8")
    antes = _numero_de_commits(repo)

    resultado = _entregar(repo)

    assert resultado.returncode != 0
    assert "intruso.txt" in resultado.stderr
    assert _numero_de_commits(repo) == antes


def test_recusa_arquivo_alterado_fora_do_manifesto(tmp_path: Path) -> None:
    repo = _montar_repo(tmp_path, GATE_VERDE)
    _preparar_entrega(repo, MANIFESTO_COMPLETO)
    (repo / "fica.txt").write_text("alterado sem estar no manifesto\n", encoding="utf-8")
    antes = _numero_de_commits(repo)

    resultado = _entregar(repo)

    assert resultado.returncode != 0
    assert "fica.txt" in resultado.stderr
    assert _numero_de_commits(repo) == antes


def test_commita_so_o_manifesto_e_remove(tmp_path: Path) -> None:
    repo = _montar_repo(tmp_path, GATE_VERDE)
    _preparar_entrega(repo, MANIFESTO_COMPLETO)
    antes = _numero_de_commits(repo)

    resultado = _entregar(repo)

    assert resultado.returncode == 0, resultado.stderr
    assert _numero_de_commits(repo) == antes + 1
    mensagem = _git(repo, "log", "-1", "--format=%B").strip()
    assert mensagem == "Brief 001: entrega de teste\n\nSegunda linha do texto do commit."
    alterados = _git(repo, "show", "--name-status", "--format=", "HEAD").split("\n")
    assert sorted(linha for linha in alterados if linha) == [
        "A\tdocs/docs/doc_001_teste_2026-11-21.md",
        "A\tnovo.txt",
        "D\tantigo.txt",
    ]
    assert not (repo / "antigo.txt").exists()
    assert _git(repo, "status", "--porcelain") == ""


@pytest.mark.parametrize(
    "manifesto",
    [
        "",
        "novo.txt\ndocs/docs/doc_001_teste_2026-11-21.md\n",
        "\nTexto do commit sem arquivos\n",
        "novo.txt\ndocs/docs/doc_001_teste_2026-11-21.md\nfica.txt\n\nTexto\n",
    ],
    ids=["vazio", "sem_texto_de_commit", "sem_arquivos", "caminho_sem_mudanca"],
)
def test_recusa_manifesto_invalido(tmp_path: Path, manifesto: str) -> None:
    repo = _montar_repo(tmp_path, GATE_VERDE)
    _preparar_entrega(repo, manifesto)
    antes = _numero_de_commits(repo)

    resultado = _entregar(repo)

    assert resultado.returncode != 0
    assert _numero_de_commits(repo) == antes


def test_recusa_numero_sem_tres_digitos(tmp_path: Path) -> None:
    repo = _montar_repo(tmp_path, GATE_VERDE)
    _preparar_entrega(repo, MANIFESTO_COMPLETO)

    resultado = _entregar(repo, "1")

    assert resultado.returncode != 0
    assert _numero_de_commits(repo) == 1


def test_recusa_sem_relatorio_unico(tmp_path: Path) -> None:
    repo = _montar_repo(tmp_path, GATE_VERDE)
    _preparar_entrega(repo, MANIFESTO_COMPLETO)
    (repo / "docs" / "docs" / "doc_001_outro_2026-11-21.md").write_text(
        _relatorio(MANIFESTO_COMPLETO), encoding="utf-8"
    )

    resultado = _entregar(repo)

    assert resultado.returncode != 0
    assert _numero_de_commits(repo) == 1


def _trava(repo: Path, comando: str) -> subprocess.CompletedProcess[str]:
    pedido = {"tool_name": "Bash", "tool_input": {"command": comando}}
    return subprocess.run(
        ["bash", "scripts/trava_git.sh"],
        cwd=repo,
        input=json.dumps(pedido),
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "comando",
    [
        "git add arquivo.txt",
        "git commit -m 'texto'",
        "git push origin main",
        "git -C pasta commit -m x",
        "git status && git commit -m x",
        "ls; git push",
        "git log | git add -A",
        "git status\ngit add .",
        "false || git reset --hard",
        "git rm arquivo.txt",
        "git checkout main",
        "git branch -D velho",
        "git branch --delete velho",
        "git stash",
    ],
)
def test_trava_bloqueia_git_de_escrita(tmp_path: Path, comando: str) -> None:
    repo = _montar_repo(tmp_path, GATE_VERDE)

    resultado = _trava(repo, comando)

    assert resultado.returncode == 2
    assert "scripts/entregar.sh" in resultado.stderr


@pytest.mark.parametrize(
    "comando",
    [
        "git status",
        "git log --oneline -5",
        "git diff",
        "git show HEAD",
        "git branch",
        "git branch -a",
        "scripts/entregar.sh 001",
        "bash scripts/entregar.sh 001",
        "ls -la",
    ],
)
def test_trava_deixa_passar_leitura_e_entrega(tmp_path: Path, comando: str) -> None:
    repo = _montar_repo(tmp_path, GATE_VERDE)

    resultado = _trava(repo, comando)

    assert resultado.returncode == 0, resultado.stderr
