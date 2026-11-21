"""Leitura única e validada de config/config.toml e config/gasto.toml (ARQUITETURA §2.1).

Nenhum valor tem padrão no código: chave faltando, tipo trocado ou chave
desconhecida param a fábrica, com a chave na mensagem, antes de qualquer
outra coisa.
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from fabrica.comum.arquivos import Arquivos
from fabrica.comum.formatos import Configuracao, Gasto

CONFIG = "config/config.toml"
GASTO = "config/gasto.toml"


class ErroConfiguracao(Exception):
    """Configuração recusada; a mensagem diz o arquivo e a chave."""


@dataclass(frozen=True)
class Config:
    geral: Configuracao
    gasto: Gasto


def _validar(arquivo: str, dados: dict[str, Any], modelo: type[BaseModel]) -> Any:
    try:
        # Pelo JSON, para que datas e horários sejam lidos do texto ano-mês-dia.
        return modelo.model_validate_json(json.dumps(dados))
    except ValidationError as erro:
        problemas = []
        for item in erro.errors():
            chave = ".".join(str(parte) for parte in item["loc"])
            problemas.append(f"{arquivo}: chave {chave}: {item['msg']}")
        raise ErroConfiguracao("\n".join(problemas)) from erro


def validar(geral: dict[str, Any], gasto: dict[str, Any]) -> Config:
    return Config(
        geral=_validar(CONFIG, geral, Configuracao),
        gasto=_validar(GASTO, gasto, Gasto),
    )


def _ler_toml(arquivos: Arquivos, relativo: str) -> dict[str, Any]:
    try:
        return tomllib.loads(arquivos.ler_texto(relativo))
    except tomllib.TOMLDecodeError as erro:
        raise ErroConfiguracao(f"{relativo}: não é TOML válido: {erro}") from erro


def carregar(arquivos: Arquivos) -> Config:
    """Lê e valida os dois arquivos uma vez; o objeto vai para os demais módulos."""
    return validar(_ler_toml(arquivos, CONFIG), _ler_toml(arquivos, GASTO))
