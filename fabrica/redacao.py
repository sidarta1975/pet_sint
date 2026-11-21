"""Redação (ARQUITETURA §5.5 e §7.1; brief 016).

`EtapaRedacao` segue a interface fixa das etapas (registro de decisão 002): `pedir`
grava o pedido ao redator da classe do tipo, com as partes na ordem fixa
(instruções, estrutura montada, trecho da tabela, ficha e, na refação, o motivo);
`receber` grava o rascunho com a marca no topo e os metadados de origem. Nunca
espera resposta. O texto enviado ao redator é lido de `instrucoes/redacao.md`.
"""

from __future__ import annotations

from typing import Any

from fabrica import estado, estruturas
from fabrica.comum.formatos import CatalogoTipos, Rascunho, Resposta, TabelaNormas
from fabrica.conferencia.regras import MARCA
from fabrica.estado import RefPeca, Servicos

INSTRUCAO = "instrucoes/redacao.md"
FICHAS = "saida/fichas"
RASCUNHOS = "saida/rascunhos"
RESPOSTAS = "saida/respostas"
CATALOGO = "dados/catalogo/tipos.json"
TABELA = "dados/normas/tabela_normas.json"


class ErroRedacao(Exception):
    """Versão fora do limite ou tipo fora do catálogo."""


def caminho_ficha(peca: RefPeca) -> str:
    return f"{FICHAS}/{peca.id}.json"


def caminho_estrutura(peca: RefPeca) -> str:
    return f"{estruturas.PASTA}/{peca.tipo}_estrutura.json"


def caminho_rascunho(peca: RefPeca) -> str:
    return f"{RASCUNHOS}/{peca.nome_versao}.md"


def caminho_metadados(peca: RefPeca) -> str:
    return f"{RASCUNHOS}/{peca.nome_versao}.json"


def tarefa_do_tipo(tipo: str, servicos: Servicos) -> str:
    catalogo = servicos.arquivos.ler_json(CATALOGO, CatalogoTipos)
    for item in catalogo.tipos:
        if item.nome_curto == tipo:
            return item.tarefa_redacao
    raise ErroRedacao(f"tipo {tipo} fora do catálogo {CATALOGO}")


def _conferir_versao(peca: RefPeca, servicos: Servicos) -> None:
    maxima = servicos.config.geral.volume.versoes_maximas
    if not 1 <= peca.versao <= maxima:
        raise ErroRedacao(f"{peca.nome_versao}: a versão vai de 1 a {maxima}")


class EtapaRedacao:
    nome = "redacao"

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        return peca.copia is None and servicos.arquivos.existe(caminho_ficha(peca))

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return caminho_rascunho(peca)

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        _conferir_versao(peca, servicos)
        arquivos = servicos.arquivos
        tabela = arquivos.ler_json(TABELA, TabelaNormas)
        teto = servicos.config.geral.trecho.teto_tokens
        trecho = estruturas.trecho_da_tabela(tabela, peca.tipo, teto)  # type: ignore[arg-type]
        partes = {
            "instrucoes": arquivos.ler_texto(INSTRUCAO),
            "estrutura": arquivos.ler_texto(caminho_estrutura(peca)),
            "trecho": trecho.texto,
            "ficha": arquivos.ler_texto(caminho_ficha(peca)),
        }
        motivo = estado.motivo_da_refacao(peca, arquivos)
        if motivo is not None:
            partes["motivo"] = motivo
        if servicos.api_claude is None:
            raise estado.ErroServicos(
                "a variável de ambiente ANTHROPIC_API_KEY não está definida: "
                "o passo precisa da API da Claude. Defina a variável e rode de novo."
            )
        return servicos.api_claude.gravar_pedido(
            rodada=peca.rodada,
            peca=peca.id,
            versao=peca.versao,
            tarefa=tarefa_do_tipo(peca.tipo, servicos),
            partes=partes,
            modelo_resposta=None,
        )

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        _conferir_versao(peca, servicos)
        if not isinstance(resposta, Resposta):
            raise ErroRedacao(f"{peca.nome_versao}: resposta da redação fora do esperado")
        arquivos = servicos.arquivos
        arquivos.gravar_texto(caminho_rascunho(peca), f"{MARCA}\n\n{resposta.conteudo}")
        arquivos.gravar_json(
            caminho_metadados(peca),
            Rascunho(
                peca=peca.id,
                versao=peca.versao,
                ficha=caminho_ficha(peca),
                estrutura=caminho_estrutura(peca),
                versao_instrucoes=arquivos.impressao(INSTRUCAO),
                modelo=resposta.modelo,
                tarefa=tarefa_do_tipo(peca.tipo, servicos),  # type: ignore[arg-type]
                resposta=f"{RESPOSTAS}/{resposta.pedido}.json",
                motivo_refacao=estado.motivo_da_refacao(peca, arquivos),
            ),
        )
        return None
