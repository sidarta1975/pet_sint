#!/usr/bin/env bash
# Trava de git (AGENTS §5; ARQUITETURA §2.1; brief 001).
# Chamada pelo gancho de .claude/settings.json antes de cada comando de terminal.
# Lê o pedido em JSON na entrada padrão (campo tool_input.command), divide o
# comando nos separadores de terminal e bloqueia, com saída 2, todo trecho que
# seja git de escrita digitado direto. O resto passa com saída 0.
set -uo pipefail

exec python3 -c '
import json
import os
import re
import shlex
import sys

ESCRITA = {
    "add", "commit", "push", "rm", "mv", "reset", "checkout", "switch",
    "restore", "rebase", "merge", "tag", "stash",
}
BRANCH_PROIBIDAS = {
    "-d", "-D", "-m", "-M", "-c", "-C",
    "--delete", "--move", "--copy", "-f", "--force",
}
# Opções globais do git que consomem o argumento seguinte.
COM_ARGUMENTO = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
SEPARADORES = re.compile(r"&&|\|\||;|\||\n")
ATRIBUICAO = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def palavras(trecho: str) -> list[str]:
    try:
        return shlex.split(trecho)
    except ValueError:
        return trecho.split()


def escrita(trecho: str) -> bool:
    partes = palavras(trecho)
    while partes and ATRIBUICAO.match(partes[0]):
        partes = partes[1:]
    if not partes or os.path.basename(partes[0]) != "git":
        return False
    i = 1
    while i < len(partes) and partes[i].startswith("-"):
        i += 2 if partes[i] in COM_ARGUMENTO else 1
    if i >= len(partes):
        return False
    sub = partes[i]
    if sub in ESCRITA:
        return True
    if sub == "branch":
        return any(p in BRANCH_PROIBIDAS for p in partes[i + 1 :])
    return False


try:
    pedido = json.loads(sys.stdin.read() or "{}")
    comando = pedido.get("tool_input", {}).get("command", "")
except (ValueError, AttributeError):
    sys.exit(0)
if not isinstance(comando, str):
    sys.exit(0)

for trecho in SEPARADORES.split(comando):
    if escrita(trecho):
        print(
            "Bloqueado pela trava de git: git de escrita não é digitado direto. "
            "Use scripts/entregar.sh <NNN> (AGENTS, seção 5). Trecho: " + trecho.strip(),
            file=sys.stderr,
        )
        sys.exit(2)
sys.exit(0)
'
