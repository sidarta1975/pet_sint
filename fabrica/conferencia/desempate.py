"""Desempate e conferência pelo Opus (ARQUITETURA §2.3, §5.6, §5.12.4 e Anexo B.3;
brief 018).

`EtapaDesempate` só grava pedido nas três situações de `instrucoes/opus_desempate.md`:
discordância entre o Haiku e o modelo local num item (risco baixo e médio); todos os
itens do conferente nas peças de risco alto; os itens do conferente local numa peça de
risco médio que ficou sem a resposta dele (mais de 72 horas de espera, ou pedido que não
coube no contexto). Numa mesma peça, todas as perguntas vão num pedido só, com a tarefa
`conferencia_opus`. A resposta vira `saida/conferencias/<peça>_v<k>_desempate.json`.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, get_args

from pydantic import ValidationError

from fabrica import estruturas
from fabrica.comum.formatos import (
    ItemLocal,
    Resposta,
    RespostaChecklist,
    RespostaDesempate,
    RespostaItem,
    ResultadoConferenteLocal,
    TabelaNormas,
)
from fabrica.conferencia.checklist import itens_do_tipo
from fabrica.conferencia.extracao import (
    ErroConferencia,
    api,
    caminho_etapa,
    caminho_ficha,
    caminho_rascunho,
    tipo_do_catalogo,
)
from fabrica.conferencia.local import EtapaLocal
from fabrica.estado import FORA_DO_FORMATO, RefPeca, Servicos

INSTRUCAO = "instrucoes/opus_desempate.md"
TABELA = "dados/normas/tabela_normas.json"
ITENS_LOCAIS = frozenset(get_args(ItemLocal))

Situacao = Literal["discordancia", "risco_alto", "medio_sem_local"]


@dataclass(frozen=True)
class Pergunta:
    item: str
    situacao: Situacao


def respostas_locais(local: ResultadoConferenteLocal | None) -> dict[str, RespostaItem]:
    """As respostas do modelo local por item; vazio quando ele não respondeu."""
    if local is None or local.resultado == "indisponivel" or local.respostas is None:
        return {}
    return {i.item: i.resposta for i in local.respostas.itens}


def perguntas(
    classe: str,
    itens_conferente: Sequence[str],
    checklist: RespostaChecklist,
    local: ResultadoConferenteLocal | None,
) -> list[Pergunta]:
    """O que vai ao Opus, na ordem dos itens do tipo; lista vazia: não há pedido."""
    if classe == "alto":
        return [Pergunta(item, "risco_alto") for item in itens_conferente]
    haiku: dict[str, RespostaItem] = {i.item: i.resposta for i in checklist.itens}
    do_local = respostas_locais(local)
    lista: list[Pergunta] = []
    for item in itens_conferente:
        if item not in ITENS_LOCAIS:
            continue
        if item in do_local:
            if do_local[item] != haiku.get(item):
                lista.append(Pergunta(item, "discordancia"))
        elif classe == "medio" and local is not None:
            lista.append(Pergunta(item, "medio_sem_local"))
    return lista


def _entradas(peca: RefPeca, servicos: Servicos) -> list[Pergunta] | None:
    """As perguntas da peça, ou None se ainda falta a conferência que vem antes."""
    arquivos = servicos.arquivos
    if not arquivos.existe(caminho_etapa(peca, "checklist")):
        return None
    local: ResultadoConferenteLocal | None = None
    if EtapaLocal().se_aplica(peca, servicos):
        if not arquivos.existe(caminho_etapa(peca, "local")):
            return None
        local = arquivos.ler_json(caminho_etapa(peca, "local"), ResultadoConferenteLocal)
    checklist = arquivos.ler_json(caminho_etapa(peca, "checklist"), RespostaChecklist)
    classe = tipo_do_catalogo(peca.tipo, servicos).classe_risco
    itens = [i["item"] for i in itens_do_tipo(peca, servicos)]
    return perguntas(classe, itens, checklist, local)


class EtapaDesempate:
    nome = "desempate"

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        return bool(_entradas(peca, servicos))

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return caminho_etapa(peca, self.nome)

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        arquivos = servicos.arquivos
        lista = _entradas(peca, servicos)
        if not lista:
            raise ErroConferencia(f"{peca.nome_versao}: nada a perguntar ao Opus")
        checklist = arquivos.ler_json(caminho_etapa(peca, "checklist"), RespostaChecklist)
        haiku: dict[str, Any] = {i.item: i for i in checklist.itens}
        local = None
        if arquivos.existe(caminho_etapa(peca, "local")):
            local = arquivos.ler_json(caminho_etapa(peca, "local"), ResultadoConferenteLocal)
        do_local: dict[str, Any] = {}
        if local is not None and local.respostas is not None:
            do_local = {i.item: i for i in local.respostas.itens}
        texto_das = {i["item"]: i["pergunta"] for i in itens_do_tipo(peca, servicos)}
        itens: list[dict[str, Any]] = []
        for p in lista:
            linha: dict[str, Any] = {
                "item": p.item,
                "pergunta": texto_das[p.item],
                "situacao": p.situacao,
            }
            if p.situacao == "discordancia":
                h, lo = haiku[p.item], do_local[p.item]
                linha["primeiro_conferente"] = {"resposta": h.resposta, "trecho": h.trecho}
                linha["conferente_local"] = {"resposta": lo.resposta, "trecho": lo.trecho}
            itens.append(linha)
        tabela = arquivos.ler_json(TABELA, TabelaNormas)
        teto = servicos.config.geral.trecho.teto_tokens
        trecho = estruturas.trecho_da_tabela(tabela, peca.tipo, teto)  # type: ignore[arg-type]
        caminho: str = api(servicos).gravar_pedido(
            rodada=peca.rodada,
            peca=peca.id,
            versao=peca.versao,
            tarefa="conferencia_opus",
            partes={
                "instrucoes": arquivos.ler_texto(INSTRUCAO),
                "estrutura": json.dumps({"itens": itens}, ensure_ascii=False, indent=2),
                "trecho": trecho.texto,
                "ficha": arquivos.ler_texto(caminho_ficha(peca)),
                "conteudo": arquivos.ler_texto(caminho_rascunho(peca)),
            },
            modelo_resposta=RespostaDesempate,
        )
        return caminho

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        if not isinstance(resposta, Resposta):
            raise ErroConferencia(f"{peca.nome_versao}: resposta do desempate fora do esperado")
        try:
            lida = RespostaDesempate.model_validate_json(resposta.conteudo)
        except ValidationError:
            return FORA_DO_FORMATO
        pedidas = [p.item for p in _entradas(peca, servicos) or []]
        if sorted(i.item for i in lida.itens) != sorted(pedidas):
            return FORA_DO_FORMATO  # faltou item pedido, ou veio item a mais
        servicos.arquivos.gravar_json(caminho_etapa(peca, self.nome), lida)
        return None
