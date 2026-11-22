"""Decisão (ARQUITETURA §5.6, §5.12.8 e Anexo B.3; brief 018).

`decidir` junta as conferências de uma versão e decide, por uma regra só: "não passa"
em item eliminatório reprova. Cada item chega à resposta final pelo Anexo B.3, e o
caminho fica gravado no veredito. O motivo cai numa das quatro categorias (conteúdo,
semelhança, ambos, formato). As notas de estilo são só registradas.

`EtapaDecisao` grava o veredito em `saida/conferencias/<peça>_v<k>.json` e, quando a
peça é aprovada fora do modo de teste, a cópia do rascunho em
`saida/aprovadas/<peça>_v<k>.md`, que é a base da semelhança das peças seguintes.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from fabrica.comum.formatos import (
    Alerta,
    CaminhoItem,
    CategoriaMotivo,
    Conferencia,
    Extracao,
    ListaConferencia,
    RespostaChecklist,
    RespostaDesempate,
    RespostaItem,
    ResultadoConferenteLocal,
    ResultadoItem,
    ResultadoProgramas,
    ResultadoSemelhanca,
    Veredito,
)
from fabrica.conferencia import semelhanca as sem
from fabrica.conferencia.checklist import LISTA, itens_do_tipo
from fabrica.conferencia.desempate import ITENS_LOCAIS, respostas_locais
from fabrica.conferencia.extracao import (
    ErroConferencia,
    caminho_etapa,
    caminho_rascunho,
    tipo_do_catalogo,
)
from fabrica.conferencia.local import EtapaLocal
from fabrica.estado import CONFERENCIAS, RefPeca, Servicos

NAO: RespostaItem = "nao_passa"
PASSA: RespostaItem = "passa"


@dataclass(frozen=True)
class Entradas:
    """Tudo o que a decisão lê de uma versão. `local` é None quando o conferente local
    não se aplica à peça; `formato` é a etapa cuja resposta saiu fora do formato duas
    vezes (extração, checklist ou desempate)."""

    peca: str
    versao: int
    classe: str
    versoes_maximas: int
    itens_conferente: Sequence[str]
    eliminatorios: frozenset[str]
    programas: ResultadoProgramas | None
    checklist: RespostaChecklist | None
    local: ResultadoConferenteLocal | None
    desempate: RespostaDesempate | None
    semelhanca: ResultadoSemelhanca | None
    extracao: Extracao | None = None
    formato: str | None = None
    modo_teste: bool = False


def _item(item: str, resposta: RespostaItem, quem: str, trecho: str) -> ResultadoItem:
    return ResultadoItem.model_validate(
        {"item": item, "resposta": resposta, "quem": quem, "trecho": trecho, "divergencias": []}
    )


def _caminho(
    item: str, respostas: list[ResultadoItem], regra: str, final: ResultadoItem
) -> CaminhoItem:
    return CaminhoItem.model_validate(
        {
            "item": item,
            "respostas": [r.model_dump() for r in respostas],
            "regra": regra,
            "resposta_final": final.resposta,
            "quem_final": final.quem,
        }
    )


def _caminhos_de_programa(e: Entradas) -> list[CaminhoItem]:
    caminhos: list[CaminhoItem] = []
    assert e.programas is not None and e.checklist is not None
    citacoes = [
        _item("citacao_fora_da_tabela", c.resposta, "haiku", f"{c.citacao}: {c.trecho}")
        for c in e.checklist.citacoes
    ]
    for r in e.programas.itens:
        if r.item == "citacao_fora_da_tabela" and citacoes:
            # A citação não resolvida foi perguntada ao checklist: nunca passa sem conferência.
            todas = [r, *citacoes]
            final = next((x for x in todas if x.resposta == NAO), r)
            caminhos.append(_caminho(r.item, todas, "programa e pergunta ao checklist", final))
            continue
        caminhos.append(_caminho(r.item, [r], "programa", r))
    s = e.semelhanca
    if s is not None and not s.desligada:
        trecho = (
            f"{s.valor:.4f} com {s.comparada_com} (limite {s.limite})"
            if s.valor is not None
            else "nenhuma aprovada do tipo para comparar"
        )
        r = _item("semelhanca", NAO if s.reprova else PASSA, "programa", trecho)
        caminhos.append(_caminho("semelhanca", [r], "programa", r))
    return caminhos


def _opus(e: Entradas, item: str) -> ResultadoItem:
    achado = next((i for i in (e.desempate.itens if e.desempate else []) if i.item == item), None)
    if achado is None:
        raise ErroConferencia(f"{e.peca}_v{e.versao}: falta a resposta do Opus no item {item}")
    return _item(item, achado.resposta, "opus", achado.justificativa)


def _caminho_do_conferente(e: Entradas, item: str) -> CaminhoItem:
    assert e.checklist is not None
    h_lido = next((i for i in e.checklist.itens if i.item == item), None)
    if h_lido is None:
        raise ErroConferencia(f"{e.peca}_v{e.versao}: o checklist não respondeu {item}")
    h = _item(item, h_lido.resposta, "haiku", h_lido.trecho)
    do_local = respostas_locais(e.local)
    lo: ResultadoItem | None = None
    if item in ITENS_LOCAIS and item in do_local:
        trecho = next(i.trecho for i in e.local.respostas.itens if i.item == item)  # type: ignore[union-attr]
        lo = _item(item, do_local[item], "local", trecho)
    vistos = [h] + ([lo] if lo is not None else [])
    if e.classe == "alto":
        o = _opus(e, item)
        if lo is not None and h.resposta == NAO and lo.resposta == NAO:
            return _caminho(item, [*vistos, o], "alto: Haiku e local concordam em não passa", h)
        return _caminho(item, [*vistos, o], "alto: vale o Opus", o)
    if item not in ITENS_LOCAIS:
        return _caminho(item, vistos, "só do Haiku", h)
    if lo is not None:
        if lo.resposta == h.resposta:
            return _caminho(item, vistos, "Haiku e local concordam", h)
        o = _opus(e, item)
        return _caminho(item, [*vistos, o], "discordância: o Opus decide", o)
    if e.classe == "medio" and e.local is not None:
        o = _opus(e, item)
        return _caminho(item, [*vistos, o], "médio sem conferente local: vale o Opus", o)
    return _caminho(item, vistos, "sem conferente local: vale o Haiku", h)


def _alertas(e: Entradas) -> list[Alerta]:
    alertas = list(e.programas.alertas) if e.programas is not None else []
    if e.local is not None and e.local.resultado == "indisponivel":
        alertas.append(
            Alerta(
                item=None, origem="local", texto=f"conferente local indisponível ({e.local.causa})"
            )
        )
    if e.semelhanca is not None and e.semelhanca.desligada:
        alertas.append(Alerta(item="semelhanca", origem="semelhanca", texto=sem.DESLIGADA))
    return alertas


def decidir(e: Entradas) -> Conferencia:
    comum: dict[str, Any] = {
        "peca": e.peca,
        "versao": e.versao,
        "extracao": e.extracao,
        "notas_estilo": e.checklist.notas if e.checklist is not None else None,
        "semelhanca": e.semelhanca.valor if e.semelhanca is not None else None,
        "conferencia_local": e.local.resultado if e.local is not None else None,
        "modo_teste": e.modo_teste,
    }
    if e.formato is not None:
        return Conferencia(
            **comum,
            itens=[],
            caminho=[],
            alertas=_alertas(e),
            veredito="descartada",
            categoria_motivo="formato",
            motivo=f"[formato] a resposta da etapa {e.formato} saiu fora do formato duas vezes",
        )
    if e.programas is None or e.checklist is None:
        raise ErroConferencia(f"{e.peca}_v{e.versao}: faltam os programas ou o checklist")
    caminhos = _caminhos_de_programa(e)
    caminhos += [_caminho_do_conferente(e, item) for item in e.itens_conferente]
    finais = [_item(c.item, c.resposta_final, c.quem_final, _trecho_final(c)) for c in caminhos]
    reprovados = [r for r in finais if r.resposta == NAO and r.item in e.eliminatorios]
    por_semelhanca = any(r.item == "semelhanca" for r in reprovados)
    por_conteudo = any(r.item != "semelhanca" for r in reprovados)
    veredito: Veredito
    categoria: CategoriaMotivo | None
    if not reprovados:
        veredito, categoria, motivo = "aprovada", None, ""
    else:
        veredito = "descartada" if e.versao >= e.versoes_maximas else "refazer"
        categoria = (
            "ambos"
            if por_semelhanca and por_conteudo
            else "semelhanca"
            if por_semelhanca
            else "conteudo"
        )
        marca = "[semelhança] " if por_semelhanca else ""
        motivo = marca + "; ".join(f"{r.item}: {r.trecho}" for r in reprovados)
    return Conferencia(
        **comum,
        itens=finais,
        caminho=caminhos,
        alertas=_alertas(e),
        veredito=veredito,
        categoria_motivo=categoria,
        motivo=motivo,
    )


def _trecho_final(caminho: CaminhoItem) -> str:
    final = next(
        r
        for r in caminho.respostas
        if r.quem == caminho.quem_final and r.resposta == caminho.resposta_final
    )
    return final.trecho


# ---------------------------------------------------------------------------
# Etapa
# ---------------------------------------------------------------------------


def caminho_veredito(peca: RefPeca) -> str:
    return f"{CONFERENCIAS}/{peca.nome_versao}.json"


def eliminatorios(servicos: Servicos) -> frozenset[str]:
    lista = servicos.arquivos.ler_json(LISTA, ListaConferencia)
    return frozenset(i.item for i in lista.itens if i.eliminatorio)


def entradas(peca: RefPeca, servicos: Servicos, formato: str | None = None) -> Entradas:
    arquivos = servicos.arquivos

    def ler(etapa: str, modelo: Any) -> Any:
        caminho = caminho_etapa(peca, etapa)
        return arquivos.ler_json(caminho, modelo) if arquivos.existe(caminho) else None

    local = None
    if EtapaLocal().se_aplica(peca, servicos):
        local = ler("local", ResultadoConferenteLocal)
    return Entradas(
        peca=peca.id,
        versao=peca.versao,
        classe=tipo_do_catalogo(peca.tipo, servicos).classe_risco,
        versoes_maximas=servicos.config.geral.volume.versoes_maximas,
        itens_conferente=[i["item"] for i in itens_do_tipo(peca, servicos)],
        eliminatorios=eliminatorios(servicos),
        programas=ler("programas", ResultadoProgramas),
        checklist=ler("checklist", RespostaChecklist),
        local=local,
        desempate=ler("desempate", RespostaDesempate),
        semelhanca=ler("semelhanca", ResultadoSemelhanca),
        extracao=ler("extracao", Extracao),
        formato=formato,
        modo_teste=servicos.modo_teste,
    )


def veredito_de_formato(peca: RefPeca, servicos: Servicos, etapa: str) -> Conferencia:
    """O veredito da categoria formato (§5.12.8), para quem lê o destino gravado pelo
    condutor: a peça é reprovada sem refação."""
    return decidir(entradas(peca, servicos, formato=etapa))


class EtapaDecisao:
    nome = "decisao"

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        return bool(servicos.arquivos.existe(caminho_etapa(peca, "checklist")))

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return caminho_veredito(peca)

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        conferencia = decidir(entradas(peca, servicos))
        arquivos = servicos.arquivos
        arquivos.gravar_json(caminho_veredito(peca), conferencia)
        if conferencia.veredito == "aprovada" and not servicos.modo_teste:
            arquivos.gravar_texto(
                sem.caminho_aprovada(peca), arquivos.ler_texto(caminho_rascunho(peca))
            )
        return None

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        raise ErroConferencia("a etapa decisao não faz pedido e não recebe resposta")
