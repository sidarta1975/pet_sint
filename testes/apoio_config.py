"""Configuração de teste montada a partir do config.toml real (brief 026).

Os testes não dependem dos valores que o responsável põe no config.toml real
(etiqueta e digest do modelo local, janela da conferência local): cada teste
escreve, na cópia que usa, os valores de que precisa. A troca é da linha inteira
da chave, qualquer que seja o valor atual.
"""

from __future__ import annotations

import re

# Valores provisórios com que os testes foram escritos (brief 002).
PROVISORIOS = {
    "etiqueta_completa": "",
    "digest": "",
    "inicio": "22:00",
    "fim": "06:00",
}


def trocar(texto: str, **valores: str) -> str:
    """Troca a linha `chave = ...` de cada chave pelo valor pedido, entre aspas."""
    for chave, valor in valores.items():
        padrao = re.compile(rf"^{re.escape(chave)} = .*$", re.MULTILINE)
        texto, trocas = padrao.subn(f'{chave} = "{valor}"', texto)
        if trocas != 1:
            raise AssertionError(f"config.toml de teste: chave {chave} achada {trocas} vezes")
    return texto


def provisorio(texto: str, **valores: str) -> str:
    """O config.toml com os valores provisórios, mais as trocas pedidas pelo teste."""
    return trocar(texto, **{**PROVISORIOS, **valores})
