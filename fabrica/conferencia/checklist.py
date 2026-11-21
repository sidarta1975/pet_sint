"""Checklist do Haiku (ARQUITETURA §2.3, §5.6 e Anexo B.2; brief 017).

`EtapaChecklist` grava o pedido com a instrução de `instrucoes/checklist.md`, o
trecho da tabela, a ficha, o rascunho e a lista dos itens do conferente que se
aplicam ao tipo (pelo catálogo), com os eliminatórios marcados e as perguntas sobre
as citações não resolvidas. A resposta, item por item com o trecho e as notas de
estilo, vira `saida/conferencias/<peça>_v<k>_checklist.json`.
"""

from __future__ import annotations

import json
from typing import Any, get_args

from pydantic import ValidationError

from fabrica import estruturas
from fabrica.comum.formatos import (
    ItemConferente,
    ListaConferencia,
    Resposta,
    RespostaChecklist,
    ResultadoProgramas,
    TabelaNormas,
)
from fabrica.conferencia import citacoes
from fabrica.conferencia.extracao import (
    ErroConferencia,
    api,
    caminho_etapa,
    caminho_ficha,
    caminho_rascunho,
    tipo_do_catalogo,
)
from fabrica.estado import FORA_DO_FORMATO, RefPeca, Servicos

INSTRUCAO = "instrucoes/checklist.md"
LISTA = "dados/conferencia/lista_conferencia.json"
TABELA = "dados/normas/tabela_normas.json"
ITENS_DO_CONFERENTE = frozenset(get_args(ItemConferente))


def itens_do_tipo(peca: RefPeca, servicos: Servicos) -> list[dict[str, Any]]:
    """Os itens do Anexo B.2 do catálogo do tipo, na ordem do catálogo."""
    catalogo = tipo_do_catalogo(peca.tipo, servicos)
    lista = {i.item: i for i in servicos.arquivos.ler_json(LISTA, ListaConferencia).itens}
    itens = []
    for nome in catalogo.itens_conferencia:
        if nome not in ITENS_DO_CONFERENTE:
            continue
        item = lista.get(nome)
        if item is None:
            raise ErroConferencia(f"item {nome} do catálogo fora de {LISTA}")
        itens.append({"item": nome, "pergunta": item.pergunta, "eliminatorio": item.eliminatorio})
    return itens


class EtapaChecklist:
    nome = "checklist"

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        return servicos.arquivos.existe(caminho_etapa(peca, "programas"))

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return caminho_etapa(peca, self.nome)

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        arquivos = servicos.arquivos
        programas = arquivos.ler_json(caminho_etapa(peca, "programas"), ResultadoProgramas)
        lista = {
            "itens": itens_do_tipo(peca, servicos),
            "citacoes_nao_resolvidas": [
                citacoes.pergunta(n) for n in programas.citacoes_nao_resolvidas
            ],
        }
        tabela = arquivos.ler_json(TABELA, TabelaNormas)
        teto = servicos.config.geral.trecho.teto_tokens
        trecho = estruturas.trecho_da_tabela(tabela, peca.tipo, teto)  # type: ignore[arg-type]
        caminho: str = api(servicos).gravar_pedido(
            rodada=peca.rodada,
            peca=peca.id,
            versao=peca.versao,
            tarefa="checklist",
            partes={
                "instrucoes": arquivos.ler_texto(INSTRUCAO),
                "estrutura": json.dumps(lista, ensure_ascii=False, indent=2),
                "trecho": trecho.texto,
                "ficha": arquivos.ler_texto(caminho_ficha(peca)),
                "conteudo": arquivos.ler_texto(caminho_rascunho(peca)),
            },
            modelo_resposta=RespostaChecklist,
        )
        return caminho

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        if not isinstance(resposta, Resposta):
            raise ErroConferencia(f"{peca.nome_versao}: resposta do checklist fora do esperado")
        try:
            lida = RespostaChecklist.model_validate_json(resposta.conteudo)
        except ValidationError:
            return FORA_DO_FORMATO
        pedidos = [i["item"] for i in itens_do_tipo(peca, servicos)]
        if sorted(i.item for i in lida.itens) != sorted(pedidos):
            return FORA_DO_FORMATO  # faltou item pedido, ou veio item a mais
        servicos.arquivos.gravar_json(caminho_etapa(peca, self.nome), lida)
        return None
