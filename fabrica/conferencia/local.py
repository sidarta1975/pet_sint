"""Conferente local (ARQUITETURA §5.6, §5.12.4 e §7.2; brief 017).

`EtapaLocal` vale para todas as peças de risco médio e alto e para uma fração das de
risco baixo (`fracao_pecas_risco_baixo`, 2 das 10 manifestações), sorteada pela
semente da rodada e pelo nome curto do tipo. No teste dos conferentes, a cópia segue
a sua original. O pedido leva a instrução de `instrucoes/conferente_local.md`, a
ficha, o rascunho e só os itens do conferente local que se aplicam ao tipo. O
resultado, inclusive "indisponível" com a causa, vira
`saida/conferencias/<peça>_v<k>_local.json`; quem decide o que fazer é `estado.py`.
"""

from __future__ import annotations

import json
import random
from typing import Any, get_args

from fabrica.comum.congelamento import Congelamento
from fabrica.comum.formatos import (
    BaseFicha,
    ItemLocal,
    ParteDoPedido,
    Pedido,
    RespostaLocal,
    ResultadoConferenteLocal,
    esquema_resposta,
)
from fabrica.comum.modelo_local import Resultado
from fabrica.conferencia.checklist import itens_do_tipo
from fabrica.conferencia.extracao import (
    ErroConferencia,
    caminho_etapa,
    caminho_ficha,
    caminho_rascunho,
    tipo_do_catalogo,
)
from fabrica.estado import PEDIDOS, RefPeca, Servicos

INSTRUCAO = "instrucoes/conferente_local.md"
ITENS_LOCAIS = frozenset(get_args(ItemLocal))
# Provisório, registrado no relatório do brief 017: a configuração não tem teto de
# saída para o conferente local.
TETO_SAIDA = 2000


def sorteadas(tipo: str, semente: int, quantidade: int, fracao: float) -> frozenset[int]:
    """As casas de risco baixo que passam pelo conferente local (sempre as mesmas)."""
    k = round(fracao * quantidade)
    rng = random.Random(f"{semente}:{tipo}:conferente_local")
    return frozenset(rng.sample(range(1, quantidade + 1), k))


def _casa(peca: RefPeca, servicos: Servicos) -> int:
    """A casa da matriz da peça original; a ficha nova da casa herda a casa."""
    base = f"saida/fichas/{peca.rodada}_{peca.tipo}_{peca.numero:03d}_base.json"
    if servicos.arquivos.existe(base):
        return servicos.arquivos.ler_json(base, BaseFicha).casa
    return peca.numero


class EtapaLocal:
    nome = "local"

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        # Defeito corrigido no brief 018: sem esperar o checklist, a peça cuja ficha foi
        # descartada (sem rascunho) caía no pedido do conferente local.
        existe = servicos.arquivos.existe(caminho_etapa(peca, "checklist"))
        return bool(existe) and self.se_aplica(peca, servicos)

    def se_aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        """A regra do sorteio: a peça passa pelo conferente local?"""
        catalogo = tipo_do_catalogo(peca.tipo, servicos)
        if catalogo.classe_risco in ("medio", "alto"):
            return True
        rodada = Congelamento(servicos.arquivos, servicos.registro, servicos.relogio).rodada(
            peca.rodada
        )
        fracao = servicos.config.geral.modelo_local.fracao_pecas_risco_baixo
        escolhidas = sorteadas(peca.tipo, rodada.semente, catalogo.quantidade, fracao)
        return _casa(peca, servicos) in escolhidas

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return caminho_etapa(peca, self.nome)

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        arquivos = servicos.arquivos
        itens = [i for i in itens_do_tipo(peca, servicos) if i["item"] in ITENS_LOCAIS]
        lista = json.dumps(
            {"itens": [{"item": i["item"], "pergunta": i["pergunta"]} for i in itens]},
            ensure_ascii=False,
            indent=2,
        )
        nome = f"{peca.nome_versao}_conferente_local_t1"
        pedido = Pedido(
            nome=nome,
            servico="local",
            rodada=peca.rodada,
            peca=peca.id,
            versao=peca.versao,
            tarefa="conferente_local",
            tentativa=1,
            modelo=servicos.config.geral.modelo_local.nome,
            esforco=None,
            teto_saida=TETO_SAIDA,
            partes=[
                ParteDoPedido(nome="instrucoes", texto=arquivos.ler_texto(INSTRUCAO)),
                ParteDoPedido(nome="estrutura", texto=lista),
                ParteDoPedido(nome="ficha", texto=arquivos.ler_texto(caminho_ficha(peca))),
                ParteDoPedido(nome="conteudo", texto=arquivos.ler_texto(caminho_rascunho(peca))),
            ],
            formato="RespostaLocal",
            esquema=esquema_resposta(RespostaLocal),
            criado_em=servicos.relogio(),
        )
        caminho = f"{PEDIDOS}/{nome}.json"
        arquivos.gravar_json(caminho, pedido)
        return caminho

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        if not isinstance(resposta, Resultado):
            raise ErroConferencia(f"{peca.nome_versao}: resultado do local fora do esperado")
        servicos.arquivos.gravar_json(
            caminho_etapa(peca, self.nome),
            ResultadoConferenteLocal(
                resultado=resposta.resultado,
                causa=resposta.causa,
                respostas=resposta.respostas,
                fracao_contexto=resposta.fracao_contexto,
                duracao_segundos=resposta.duracao_segundos,
            ),
        )
        return None
