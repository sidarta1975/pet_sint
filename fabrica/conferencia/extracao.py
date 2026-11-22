"""Extração da peça pelo Haiku (ARQUITETURA §2.3 e §5.6; brief 017).

`EtapaExtracao` grava o pedido com a instrução de `instrucoes/extracao.md`, o
rascunho e a lista de naturezas de pedido do tipo, com o esquema de `Extracao`.
A resposta válida vira `saida/conferencias/<peça>_v<k>_extracao.json`; a resposta
fora do esquema volta "fora do formato", sem conserto. A extração não recebe a ficha.
"""

from __future__ import annotations

from typing import Any, get_args

from pydantic import ValidationError

from fabrica.comum.formatos import (
    CatalogoTipos,
    Extracao,
    NaturezaEmbargos,
    NaturezaInicial,
    NaturezaManifestacao,
    Resposta,
    TipoCatalogo,
)
from fabrica.estado import FORA_DO_FORMATO, ErroServicos, RefPeca, Servicos

INSTRUCAO = "instrucoes/extracao.md"
CONFERENCIAS = "saida/conferencias"
RASCUNHOS = "saida/rascunhos"
FICHAS = "saida/fichas"
CATALOGO = "dados/catalogo/tipos.json"
NATUREZAS: dict[str, tuple[str, ...]] = {
    "peticao_inicial_jec": get_args(NaturezaInicial),
    "embargos_declaracao": get_args(NaturezaEmbargos),
    "manifestacao_ar_negativo": get_args(NaturezaManifestacao),
}


class ErroConferencia(Exception):
    """Arquivo da conferência que falta ou tipo fora do catálogo."""


def caminho_rascunho(peca: RefPeca) -> str:
    return f"{RASCUNHOS}/{peca.nome_versao}.md"


def caminho_ficha(peca: RefPeca) -> str:
    """A ficha da peça; a cópia do teste dos conferentes usa a da sua original."""
    return f"{FICHAS}/{peca.rodada}_{peca.tipo}_{peca.numero:03d}.json"


def caminho_etapa(peca: RefPeca, etapa: str) -> str:
    return f"{CONFERENCIAS}/{peca.nome_versao}_{etapa}.json"


def tipo_do_catalogo(tipo: str, servicos: Servicos) -> TipoCatalogo:
    for item in servicos.arquivos.ler_json(CATALOGO, CatalogoTipos).tipos:
        if item.nome_curto == tipo:
            return item
    raise ErroConferencia(f"tipo {tipo} fora do catálogo {CATALOGO}")


def api(servicos: Servicos) -> Any:
    if servicos.api_claude is None:
        raise ErroServicos(
            "a variável de ambiente ANTHROPIC_API_KEY não está definida: "
            "o passo precisa da API da Claude. Defina a variável e rode de novo."
        )
    return servicos.api_claude


class EtapaExtracao:
    nome = "extracao"

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        return servicos.arquivos.existe(caminho_rascunho(peca))

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return caminho_etapa(peca, self.nome)

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        arquivos = servicos.arquivos
        naturezas = ", ".join(NATUREZAS[peca.tipo])
        caminho: str = api(servicos).gravar_pedido(
            rodada=peca.rodada,
            peca=peca.id,
            versao=peca.versao,
            tarefa="extracao",
            partes={
                "instrucoes": arquivos.ler_texto(INSTRUCAO),
                "estrutura": f"Naturezas de pedido do tipo: {naturezas}.",
                "conteudo": arquivos.ler_texto(caminho_rascunho(peca)),
            },
            modelo_resposta=Extracao,
        )
        return caminho

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        if not isinstance(resposta, Resposta):
            raise ErroConferencia(f"{peca.nome_versao}: resposta da extração fora do esperado")
        try:
            extraida = Extracao.model_validate_json(resposta.conteudo)
        except ValidationError:
            return FORA_DO_FORMATO
        servicos.arquivos.gravar_json(caminho_etapa(peca, self.nome), extraida)
        return None
