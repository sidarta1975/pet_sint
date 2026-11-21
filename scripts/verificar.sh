#!/usr/bin/env bash
# O gate (AGENTS §6; ARQUITETURA §2.1): para na primeira falha.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "== ruff check"
ruff check
echo "== ruff format --check"
ruff format --check
echo "== mypy fabrica"
mypy fabrica
echo "== pytest testes"
pytest testes
