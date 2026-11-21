"""Único acesso ao disco da fábrica (ARQUITETURA §2.5 e §4; ADR 001, itens 3 a 6).

Lê de `saida/`, `dados/`, `instrucoes/` e `config/`; grava só em `saida/`.
Gravação atômica (temporário, escrita forçada no disco e troca de nome) e nunca
sobrescreve. A única exceção é `saida/rodadas.json`, regravado por
`regravar_rodadas`, com a cópia anterior guardada (ADR 001, item 4).
"""

from __future__ import annotations

import datetime
import hashlib
import os
import secrets
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from fabrica.comum.formatos import Rodadas

M = TypeVar("M", bound=BaseModel)

PASTAS_DE_LEITURA = ("saida", "dados", "instrucoes", "config")
PASTA_DE_GRAVACAO = "saida"
RODADAS = "saida/rodadas.json"
RODADAS_ANTERIORES = "saida/registro/rodadas_anteriores"
MARCA_TEMPORARIO = ".tmp-"
CAMINHOS_DO_CODIGO = ("fabrica", "dados", "instrucoes", "config", "pyproject.toml")

# Separado para que o teste possa interromper a gravação no meio.
_renomear: Callable[[Path, Path], None] = os.replace


class ErroArquivo(Exception):
    """Arquivo recusado: fora da pasta, já existente, ausente ou fora do formato."""


def _agora() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class Arquivos:
    def __init__(self, raiz: Path, relogio: Callable[[], datetime.datetime] = _agora) -> None:
        self.raiz = raiz.resolve()
        self.relogio = relogio

    # --- caminhos -----------------------------------------------------------

    def _caminho(self, relativo: str, pastas: tuple[str, ...]) -> Path:
        caminho = (self.raiz / relativo).resolve()
        for pasta in pastas:
            base = self.raiz / pasta
            if caminho == base or base in caminho.parents:
                return caminho
        raise ErroArquivo(f"{relativo}: caminho fora da pasta permitida ({', '.join(pastas)})")

    def _leitura(self, relativo: str) -> Path:
        caminho = self._caminho(relativo, PASTAS_DE_LEITURA)
        if MARCA_TEMPORARIO in caminho.name:
            raise ErroArquivo(f"{relativo}: arquivo temporário não é lido")
        return caminho

    def _relativo(self, caminho: Path) -> str:
        return caminho.relative_to(self.raiz).as_posix()

    # --- gravação -----------------------------------------------------------

    def _gravar(self, caminho: Path, conteudo: bytes, sobrescrever: bool = False) -> None:
        if caminho.exists() and not sobrescrever:
            raise ErroArquivo(f"{self._relativo(caminho)}: já existe; nunca se sobrescreve")
        caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = caminho.with_name(f"{caminho.name}{MARCA_TEMPORARIO}{secrets.token_hex(6)}")
        with temporario.open("xb") as saida:
            saida.write(conteudo)
            saida.flush()
            os.fsync(saida.fileno())
        _renomear(temporario, caminho)

    def gravar_json(self, relativo: str, objeto: BaseModel) -> None:
        caminho = self._caminho(relativo, (PASTA_DE_GRAVACAO,))
        texto = objeto.model_dump_json(indent=2, by_alias=True) + "\n"
        self._gravar(caminho, texto.encode("utf-8"))

    def gravar_texto(self, relativo: str, texto: str) -> None:
        caminho = self._caminho(relativo, (PASTA_DE_GRAVACAO,))
        self._gravar(caminho, texto.encode("utf-8"))

    def gravar_bytes(self, relativo: str, conteudo: bytes) -> None:
        """Arquivo binário (o `.docx` do pacote, brief 020), com as mesmas regras."""
        caminho = self._caminho(relativo, (PASTA_DE_GRAVACAO,))
        self._gravar(caminho, conteudo)

    def regravar_rodadas(self, rodadas: Rodadas) -> None:
        """Único arquivo regravado; a versão anterior vai para rodadas_anteriores/."""
        caminho = self._caminho(RODADAS, (PASTA_DE_GRAVACAO,))
        if caminho.exists():
            carimbo = self.relogio().strftime("%Y%m%dT%H%M%S%fZ")
            copia = self._caminho(
                f"{RODADAS_ANTERIORES}/rodadas_{carimbo}.json", (PASTA_DE_GRAVACAO,)
            )
            self._gravar(copia, caminho.read_bytes())
        texto = rodadas.model_dump_json(indent=2) + "\n"
        self._gravar(caminho, texto.encode("utf-8"), sobrescrever=True)

    def acrescentar_linha(self, relativo: str, objeto: BaseModel) -> None:
        caminho = self._caminho(relativo, (PASTA_DE_GRAVACAO,))
        if caminho.suffix != ".jsonl":
            raise ErroArquivo(f"{relativo}: só se acrescenta linha a arquivo .jsonl")
        caminho.parent.mkdir(parents=True, exist_ok=True)
        linha = objeto.model_dump_json() + "\n"
        with caminho.open("a", encoding="utf-8") as saida:
            saida.write(linha)
            saida.flush()
            os.fsync(saida.fileno())

    # --- leitura ------------------------------------------------------------

    def ler_texto(self, relativo: str) -> str:
        caminho = self._leitura(relativo)
        if not caminho.is_file():
            raise ErroArquivo(f"{relativo}: arquivo não existe")
        return caminho.read_text(encoding="utf-8")

    def ler_json(self, relativo: str, modelo: type[M]) -> M:
        texto = self.ler_texto(relativo)
        try:
            return modelo.model_validate_json(texto)
        except ValidationError as erro:
            raise ErroArquivo(f"{relativo}: fora do formato {modelo.__name__}: {erro}") from erro

    def ler_linhas(self, relativo: str, modelo: type[M]) -> list[M]:
        caminho = self._leitura(relativo)
        if not caminho.is_file():
            return []
        texto = caminho.read_text(encoding="utf-8")
        linhas = texto.split("\n")
        # A última linha sem quebra no fim está incompleta (gravação interrompida).
        completas = linhas[:-1]
        lidas: list[M] = []
        for numero, linha in enumerate(completas, start=1):
            if not linha.strip():
                continue
            try:
                lidas.append(modelo.model_validate_json(linha))
            except ValidationError as erro:
                raise ErroArquivo(
                    f"{relativo}, linha {numero}: fora do formato {modelo.__name__}: {erro}"
                ) from erro
        return lidas

    def existe(self, relativo: str) -> bool:
        try:
            return self._leitura(relativo).is_file()
        except ErroArquivo:
            return False

    def listar(self, pasta: str, padrao: str) -> list[str]:
        base = self._leitura(pasta)
        if not base.is_dir():
            return []
        return sorted(
            self._relativo(caminho)
            for caminho in base.glob(padrao)
            if caminho.is_file() and MARCA_TEMPORARIO not in caminho.name
        )

    def impressao(self, relativo: str) -> str:
        """Impressão digital do conteúdo (SHA-256)."""
        caminho = self._leitura(relativo)
        if not caminho.is_file():
            raise ErroArquivo(f"{relativo}: arquivo não existe")
        return hashlib.sha256(caminho.read_bytes()).hexdigest()

    # --- controle de versão (só leitura do git; ADR 001, item 6) -------------

    def _git(self, *argumentos: str) -> str:
        resultado = subprocess.run(
            ["git", *argumentos],
            cwd=self.raiz,
            capture_output=True,
            text=True,
            check=False,
        )
        if resultado.returncode != 0:
            raise ErroArquivo(f"git {' '.join(argumentos)}: {resultado.stderr.strip()}")
        return resultado.stdout

    def impressao_codigo(self) -> tuple[str, str]:
        """Identificador que o git dá a fabrica/ e a pyproject.toml na versão atual."""
        return (
            self._git("rev-parse", "HEAD:fabrica").strip(),
            self._git("rev-parse", "HEAD:pyproject.toml").strip(),
        )

    def mudanca_pendente(self) -> bool:
        """Há mudança pendente em fabrica/, dados/, instrucoes/, config/ ou pyproject.toml."""
        saida = self._git("status", "--porcelain", "--", *CAMINHOS_DO_CODIGO)
        return bool(saida.strip())
