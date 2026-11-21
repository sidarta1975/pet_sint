"""Semelhança textual (ARQUITETURA §5.6 e Anexo B.1; brief 018).

Compara a peça com as já aprovadas do mesmo tipo e da mesma rodada, em
`saida/aprovadas/`: a proporção de trechos de cinco palavras seguidas em comum
(índice de Jaccard, calculado exatamente com frações), depois de tirar a marca, os
títulos dos blocos e os marcadores de nome e de OAB e de passar o texto a minúsculas
sem acento. Reprova a partir do limite do `config.toml` (0,85, não calibrado). Em modo
de teste a etapa não compara: grava "desligada em modo de teste".
"""

from __future__ import annotations

from collections.abc import Iterable
from fractions import Fraction
from typing import Any

from fabrica import ficticios
from fabrica.comum import normalizacao as norm
from fabrica.comum.formatos import EstruturaMontada, ResultadoSemelhanca
from fabrica.conferencia.extracao import ErroConferencia, caminho_etapa, caminho_rascunho
from fabrica.conferencia.regras import MARCA
from fabrica.estado import RefPeca, Servicos

APROVADAS = "saida/aprovadas"
DESLIGADA = "desligada em modo de teste"
MARCADORES = (*sorted(ficticios.MARCADORES, key=len, reverse=True), ficticios.MARCADOR_OAB)


def limpar(texto: str, titulos: Iterable[str] = ()) -> list[str]:
    """As palavras que contam: sem a marca, os títulos dos blocos e os marcadores."""
    titulos_normais = {norm.comparavel(t) for t in titulos}
    linhas = []
    for linha in texto.splitlines():
        crua = linha.strip()
        if crua == MARCA or crua.startswith("#"):
            continue
        if norm.comparavel(crua) in titulos_normais:
            continue
        linhas.append(crua)
    limpo = "\n".join(linhas)
    for marcador in MARCADORES:
        limpo = limpo.replace(marcador, " ")
    return norm.palavras(limpo)


def trechos(palavras: list[str], tamanho: int) -> frozenset[tuple[str, ...]]:
    if not palavras:
        return frozenset()
    if len(palavras) < tamanho:
        return frozenset({tuple(palavras)})
    return frozenset(tuple(palavras[i : i + tamanho]) for i in range(len(palavras) - tamanho + 1))


def jaccard(a: frozenset[tuple[str, ...]], b: frozenset[tuple[str, ...]]) -> Fraction:
    uniao = a | b
    if not uniao:
        return Fraction(0)
    return Fraction(len(a & b), len(uniao))


def indice(texto_a: str, texto_b: str, tamanho: int, titulos: Iterable[str] = ()) -> Fraction:
    lista = list(titulos)
    return jaccard(
        trechos(limpar(texto_a, lista), tamanho), trechos(limpar(texto_b, lista), tamanho)
    )


def caminho_aprovada(peca: RefPeca) -> str:
    return f"{APROVADAS}/{peca.nome_versao}.md"


def aprovadas_do_tipo(peca: RefPeca, servicos: Servicos) -> list[str]:
    """As aprovadas do mesmo tipo e da mesma rodada, menos as da própria peça."""
    lidas = servicos.arquivos.listar(APROVADAS, f"{peca.rodada}_{peca.tipo}_*_v*.md")
    proprio = f"{APROVADAS}/{peca.id}_v"
    return sorted(c for c in lidas if not c.startswith(proprio))


class EtapaSemelhanca:
    nome = "semelhanca"

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        return bool(servicos.arquivos.existe(caminho_etapa(peca, "checklist")))

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return caminho_etapa(peca, self.nome)

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        config = servicos.config.geral.semelhanca
        arquivos = servicos.arquivos
        if servicos.modo_teste:
            resultado = ResultadoSemelhanca(
                valor=None, comparada_com=None, limite=config.limite, reprova=False, desligada=True
            )
            arquivos.gravar_json(self.arquivo_resultado(peca), resultado)
            return None
        montada = arquivos.ler_json(
            f"saida/preparacao/{peca.tipo}_estrutura.json", EstruturaMontada
        )
        titulos = [b.titulo for b in montada.blocos]
        texto = arquivos.ler_texto(caminho_rascunho(peca))
        maior: Fraction | None = None
        comparada: str | None = None
        for caminho in aprovadas_do_tipo(peca, servicos):
            valor = indice(texto, arquivos.ler_texto(caminho), config.palavras_por_trecho, titulos)
            if maior is None or valor > maior:
                maior, comparada = valor, caminho
        resultado = ResultadoSemelhanca(
            valor=float(maior) if maior is not None else None,
            comparada_com=comparada,
            limite=config.limite,
            reprova=maior is not None and maior >= Fraction(str(config.limite)),
            desligada=False,
        )
        arquivos.gravar_json(self.arquivo_resultado(peca), resultado)
        return None

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        raise ErroConferencia("a etapa semelhanca não faz pedido e não recebe resposta")
