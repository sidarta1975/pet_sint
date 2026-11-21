"""Estrutura montada de cada tipo, trecho da tabela e a preparação.

ARQUITETURA §2.2 e §5.5. A estrutura junta a família, o perfil e o acréscimo do
tipo; nenhum deles retira bloco obrigatório. O trecho da tabela é o mesmo para
todas as peças do tipo. `preparar` não gasta API: valida `dados/`, grava as
estruturas e o resumo em `saida/preparacao/` e diz o que precisa voltar.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from fabrica import matriz
from fabrica.comum.arquivos import Arquivos, ErroArquivo
from fabrica.comum.config import Config
from fabrica.comum.formatos import (
    Acrescimo,
    Bloco,
    CatalogoErros,
    CatalogoTipos,
    Dispositivo,
    EstruturaMontada,
    Familia,
    FeriadosNacionais,
    ListaConferencia,
    ListasFicticias,
    Matriz,
    NomeCurto,
    PalavrasIgnoradas,
    Perfil,
    ReaisPermitidos,
    ReaisProibidos,
    ReaisReservados,
    TabelaNormas,
    TermosInequivocos,
    TipoCatalogo,
    Travas,
)

__all__ = [
    "EstruturaMontada",
    "ErroEstrutura",
    "Trecho",
    "em_markdown",
    "faltando",
    "montar",
    "preparar",
    "trecho_da_tabela",
]

PASTA = "saida/preparacao"
RESERVADOS = "testes/dados/reais_reservados.json"
SEMENTE_DE_PROVA = 2026
TETO_TOKENS = 8000
DIVISOR = 3


class ErroEstrutura(Exception):
    """Estrutura recusada; `faltando` lista os blocos obrigatórios que sumiram."""

    def __init__(self, mensagem: str, faltando: Sequence[str] = ()) -> None:
        super().__init__(mensagem)
        self.faltando = list(faltando)


# ---------------------------------------------------------------------------
# Estrutura montada
# ---------------------------------------------------------------------------


def _obrigatorios(*niveis: Sequence[Bloco]) -> list[str]:
    nomes: list[str] = []
    for blocos in niveis:
        for b in blocos:
            if b.obrigatorio and b.nome not in nomes:
                nomes.append(b.nome)
    return nomes


def faltando(
    estrutura: EstruturaMontada, familia: Familia, perfil: Perfil, acrescimo: Acrescimo | None
) -> list[str]:
    """Blocos obrigatórios da família, do perfil e do tipo que não estão na estrutura."""
    niveis = [familia.blocos, perfil.blocos, perfil.ajustar]
    if acrescimo is not None:
        niveis += [acrescimo.blocos, acrescimo.ajustar]
    presentes = {b.nome for b in estrutura.blocos if b.obrigatorio}
    return [nome for nome in _obrigatorios(*niveis) if nome not in presentes]


def _aplicar(
    blocos: dict[str, Bloco],
    origem: str,
    acrescentar: Sequence[Bloco],
    retirar: Sequence[str],
    ajustar: Sequence[Bloco],
) -> list[str]:
    """Aplica um nível sobre os blocos; devolve os obrigatórios que ele tentou tirar."""
    tirados: list[str] = []
    for nome in retirar:
        if nome not in blocos:
            raise ErroEstrutura(f"{origem}: retira o bloco inexistente {nome}")
        if blocos[nome].obrigatorio:
            tirados.append(nome)
        del blocos[nome]
    for b in ajustar:
        if b.nome not in blocos:
            raise ErroEstrutura(f"{origem}: ajusta o bloco inexistente {b.nome}")
        if blocos[b.nome].obrigatorio and not b.obrigatorio:
            tirados.append(b.nome)
        blocos[b.nome] = b
    for b in acrescentar:
        if b.nome in blocos:
            raise ErroEstrutura(f"{origem}: acrescenta o bloco {b.nome}, que já existe")
        blocos[b.nome] = b
    return tirados


def montar(
    tipo: NomeCurto, familia: Familia, perfil: Perfil, acrescimo: Acrescimo | None
) -> EstruturaMontada:
    """Família, depois perfil, depois acréscimo do tipo, em ordem; recusa o que falta."""
    if perfil.familia != familia.id:
        raise ErroEstrutura(f"perfil {perfil.id} é da família {perfil.familia}, não {familia.id}")
    if acrescimo is not None and acrescimo.tipo != tipo:
        raise ErroEstrutura(f"acréscimo do tipo {acrescimo.tipo} usado no tipo {tipo}")
    blocos: dict[str, Bloco] = {}
    for b in familia.blocos:
        if b.nome in blocos:
            raise ErroEstrutura(f"família {familia.id}: bloco {b.nome} repetido")
        blocos[b.nome] = b
    tirados = _aplicar(blocos, f"perfil {perfil.id}", perfil.blocos, perfil.retirar, perfil.ajustar)
    if acrescimo is not None:
        tirados += _aplicar(
            blocos,
            f"acréscimo {acrescimo.tipo}",
            acrescimo.blocos,
            acrescimo.retirar,
            acrescimo.ajustar,
        )
    if tirados:
        raise ErroEstrutura(f"{tipo}: bloco obrigatório retirado: {', '.join(tirados)}", tirados)
    ordens = [b.ordem for b in blocos.values()]
    if len(set(ordens)) != len(ordens):
        raise ErroEstrutura(f"{tipo}: dois blocos com a mesma ordem")
    estrutura = EstruturaMontada(
        tipo=tipo,
        familia=familia.id,
        perfil=perfil.id,
        blocos=sorted(blocos.values(), key=lambda b: b.ordem),
        pedidos_acessorios_padrao=list(perfil.pedidos_acessorios_padrao),
    )
    falta = faltando(estrutura, familia, perfil, acrescimo)
    if falta:
        raise ErroEstrutura(f"{tipo}: faltou bloco obrigatório: {', '.join(falta)}", falta)
    return estrutura


def em_markdown(estrutura: EstruturaMontada) -> str:
    """Cópia legível da estrutura, para o responsável aprovar."""
    linhas = [
        f"# Estrutura montada: {matriz.ROTULO_DO_TIPO[estrutura.tipo]}",
        "",
        f"- Família: `{estrutura.familia}`; perfil: `{estrutura.perfil}`.",
        "- Pedidos acessórios padrão: "
        + (", ".join(f"`{p}`" for p in estrutura.pedidos_acessorios_padrao) or "nenhum")
        + ".",
        "",
        "| Ordem | Bloco | Título | Obrigatório | Descrição |",
        "|---|---|---|---|---|",
    ]
    for b in estrutura.blocos:
        obrigatorio = "obrigatório" if b.obrigatorio else "opcional"
        linhas.append(f"| {b.ordem} | `{b.nome}` | {b.titulo} | {obrigatorio} | {b.descricao} |")
    return "\n".join(linhas) + "\n"


# ---------------------------------------------------------------------------
# Trecho da tabela
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Trecho:
    tipo: NomeCurto
    dispositivos: tuple[Dispositivo, ...]
    texto: str
    tokens_estimados: int
    pares: int
    situacao: matriz.Situacao


def _artigo(artigo: str) -> tuple[int, str]:
    achado = re.match(r"\s*(\d[\d.]*)\s*[º°o]?\s*-?\s*([A-Za-z]*)", artigo)
    if achado is None:
        return (10**9, artigo)
    return (int(achado.group(1).replace(".", "")), achado.group(2).upper())


def _paragrafo(paragrafo: str) -> tuple[int, int, str]:
    texto = paragrafo.strip().casefold()
    if texto in ("", "caput"):
        return (0, 0, "")
    if "nico" in texto:  # parágrafo único
        return (1, 0, "")
    numero = re.search(r"\d+", texto)
    if numero is not None:
        return (2, int(numero.group()), "")
    return (3, 0, texto)


def _ordem(tabela: TabelaNormas) -> Any:
    posicao = {d.id: i for i, d in enumerate(tabela.diplomas)}

    def chave(d: Dispositivo) -> tuple[Any, ...]:
        return (
            posicao.get(d.diploma, len(posicao)),
            d.diploma,
            _artigo(d.artigo),
            _paragrafo(d.paragrafo),
            d.id,
        )

    return chave


def _contar_pares(dispositivos: Sequence[Dispositivo]) -> int:
    return sum(
        1
        for d in dispositivos
        if any(
            o.diploma == d.diploma and o.assunto == d.assunto and o.funcao != d.funcao
            for o in dispositivos
        )
    )


def trecho_da_tabela(
    tabela: TabelaNormas,
    tipo: NomeCurto,
    teto_tokens: int = TETO_TOKENS,
    divisor: int = DIVISOR,
) -> Trecho:
    """Os dispositivos do tipo, em ordem fixa (diploma, artigo, parágrafo)."""
    nomes = {d.id: d.nome for d in tabela.diplomas}
    escolhidos = tuple(
        sorted((d for d in tabela.dispositivos if tipo in d.tipos), key=_ordem(tabela))
    )
    linhas = [
        f"[{d.id}] {nomes.get(d.diploma, d.diploma)}, art. {d.artigo}, {d.paragrafo} "
        f"(função: {d.funcao}; assunto: {d.assunto}): {d.texto_vigente}"
        for d in escolhidos
    ]
    texto = "\n".join(linhas)
    tokens = math.ceil(len(texto) / divisor)
    situacao: matriz.Situacao = "ok" if tokens <= teto_tokens else matriz.VOLTA
    return Trecho(tipo, escolhidos, texto, tokens, _contar_pares(escolhidos), situacao)


# ---------------------------------------------------------------------------
# Preparação (comando `preparar`)
# ---------------------------------------------------------------------------

ARQUIVOS_FIXOS: dict[str, type[BaseModel]] = {
    "dados/catalogo/tipos.json": CatalogoTipos,
    "dados/normas/tabela_normas.json": TabelaNormas,
    "dados/travas/travas.json": Travas,
    "dados/conferencia/lista_conferencia.json": ListaConferencia,
    "dados/conferencia/termos_inequivocos.json": TermosInequivocos,
    "dados/conferencia/palavras_ignoradas.json": PalavrasIgnoradas,
    "dados/conferencia/feriados_nacionais.json": FeriadosNacionais,
    "dados/erros/catalogo_erros.json": CatalogoErros,
    "dados/ficticios/listas_ficticias.json": ListasFicticias,
    "dados/ficticios/reais_permitidos.json": ReaisPermitidos,
    "dados/ficticios/reais_proibidos.json": ReaisProibidos,
}


@dataclass
class Preparacao:
    linhas: list[str] = field(default_factory=list)
    problemas: list[str] = field(default_factory=list)

    @property
    def passou(self) -> bool:
        return not self.problemas


def _normal(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFD", texto.casefold())
    return " ".join("".join(c for c in sem_acento if unicodedata.category(c) != "Mn").split())


def _ler(arquivos: Arquivos, relativo: str, modelo: type[Any], prep: Preparacao) -> Any:
    try:
        return arquivos.ler_json(relativo, modelo)
    except ErroArquivo as erro:
        prep.problemas.append(str(erro).split("\n")[0])
        return None


def _reservados(raiz: Path, prep: Preparacao) -> ReaisReservados | None:
    # Fora das pastas de leitura de `arquivos.py`: lido direto e só contado.
    caminho = raiz / RESERVADOS
    try:
        return ReaisReservados.model_validate_json(caminho.read_text(encoding="utf-8"))
    except FileNotFoundError:
        prep.problemas.append(f"{RESERVADOS}: arquivo não existe")
    except ValidationError:
        prep.problemas.append(f"{RESERVADOS}: fora do formato ReaisReservados")
    return None


def preparar(arquivos: Arquivos, config: Config, semente: int = SEMENTE_DE_PROVA) -> Preparacao:
    """Valida `dados/`, grava as estruturas e o resumo; nenhuma chamada a modelo."""
    prep = Preparacao()
    lidos: dict[str, Any] = {}
    for relativo, modelo in ARQUIVOS_FIXOS.items():
        lidos[relativo] = _ler(arquivos, relativo, modelo, prep)
    catalogo: CatalogoTipos | None = lidos["dados/catalogo/tipos.json"]
    tabela: TabelaNormas | None = lidos["dados/normas/tabela_normas.json"]
    travas: Travas | None = lidos["dados/travas/travas.json"]
    feriados = lidos["dados/conferencia/feriados_nacionais.json"]
    proibidos: ReaisProibidos | None = lidos["dados/ficticios/reais_proibidos.json"]
    prep.linhas.append(
        f"- Arquivos fixos de `dados/` lidos no formato: "
        f"{sum(v is not None for v in lidos.values())} de {len(ARQUIVOS_FIXOS)}."
    )

    if tabela is not None:
        _conferir_tabela(tabela, prep)
    if travas is not None:
        _conferir_travas(travas, tabela, prep)
    if feriados is not None:
        fora = [f.data.isoformat() for f in feriados.feriados if f.data.year != matriz.ANO_DO_MVP]
        if fora:
            prep.problemas.append(f"feriados fora de {matriz.ANO_DO_MVP}: {', '.join(fora)}")
    reservados = _reservados(arquivos.raiz, prep)
    if proibidos is not None and reservados is not None:
        formas = {_normal(n.nome) for n in reservados.nomes} | {
            _normal(n.forma) for n in reservados.nomes
        }
        achados = sum(1 for n in proibidos.nomes if _normal(n.nome) in formas)
        prep.linhas.append(f"- nomes reservados em reais_proibidos.json: {achados}")
        if achados:
            prep.problemas.append(
                f"{achados} nome(s) reservado(s) do teste em reais_proibidos.json"
            )

    if catalogo is not None:
        for tipo in catalogo.tipos:
            prep.linhas.append("")
            prep.linhas.append(f"## {tipo.rotulo} (`{tipo.nome_curto}`)")
            prep.linhas.append("")
            if matriz.ROTULO_DO_TIPO[tipo.nome_curto] != tipo.rotulo:
                prep.problemas.append(f"{tipo.nome_curto}: rótulo diferente do catálogo")
            _preparar_tipo(arquivos, config, tipo, tabela, travas, semente, prep)

    situacao = "passou" if prep.passou else "falhou"
    cabecalho = [
        "# Resumo da preparação",
        "",
        f"- Situação: {situacao}.",
        f"- Semente de prova do sorteio: {semente}.",
    ]
    if prep.problemas:
        cabecalho += ["", "## O que falhou", ""] + [f"- {p}" for p in prep.problemas]
    cabecalho += ["", "## Conferências", ""]
    arquivos.gravar_texto(f"{PASTA}/resumo.md", "\n".join(cabecalho + prep.linhas) + "\n")
    return prep


def _conferir_tabela(tabela: TabelaNormas, prep: Preparacao) -> None:
    diplomas = {d.id for d in tabela.diplomas}
    ids = [d.id for d in tabela.dispositivos]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        prep.problemas.append(f"tabela_normas.json: id repetido: {', '.join(repetidos)}")
    sem = sorted({d.diploma for d in tabela.dispositivos if d.diploma not in diplomas})
    if sem:
        prep.problemas.append(f"tabela_normas.json: diploma sem cadastro: {', '.join(sem)}")


def _conferir_travas(travas: Travas, tabela: TabelaNormas | None, prep: Preparacao) -> None:
    for numero, trava in enumerate(travas.travas, start=1):
        for problema in matriz.conferir_trava(trava):
            prep.problemas.append(f"travas.json, trava {numero}: {problema}")
    if tabela is None:
        return
    ids = {d.id for d in tabela.dispositivos}
    citados = sorted({d for t in travas.travas for d in t.dispositivos} - ids)
    if citados:
        prep.problemas.append(f"travas.json cita dispositivo fora da tabela: {', '.join(citados)}")
    else:
        prep.linhas.append("- Todo dispositivo citado em travas.json está na tabela.")


def _preparar_tipo(
    arquivos: Arquivos,
    config: Config,
    tipo: TipoCatalogo,
    tabela: TabelaNormas | None,
    travas: Travas | None,
    semente: int,
    prep: Preparacao,
) -> None:
    nome = tipo.nome_curto
    familia = _ler(arquivos, f"dados/estruturas/familias/{tipo.familia}.json", Familia, prep)
    perfil = _ler(arquivos, f"dados/estruturas/perfis/{tipo.perfil}.json", Perfil, prep)
    rel_acrescimo = f"dados/estruturas/acrescimos/{nome}.json"
    acrescimo = (
        _ler(arquivos, rel_acrescimo, Acrescimo, prep) if arquivos.existe(rel_acrescimo) else None
    )
    if familia is not None and perfil is not None:
        try:
            estrutura = montar(nome, familia, perfil, acrescimo)
        except ErroEstrutura as erro:
            prep.problemas.append(str(erro))
        else:
            arquivos.gravar_json(f"{PASTA}/{nome}_estrutura.json", estrutura)
            arquivos.gravar_texto(f"{PASTA}/{nome}_estrutura.md", em_markdown(estrutura))
            prep.linhas.append(
                f"- Estrutura: {len(estrutura.blocos)} blocos, gravada em "
                f"`{PASTA}/{nome}_estrutura.json` e `.md`."
            )

    m = _ler(arquivos, f"dados/matrizes/{nome}.json", Matriz, prep)
    if m is not None and travas is not None:
        problemas = matriz.conferir_matriz(m, config.geral.matriz)
        if m.tipo != nome:
            problemas.append(f"matriz de {nome} diz tipo {m.tipo}")
        if m.quantidade != tipo.quantidade:
            problemas.append(f"{nome}: matriz com {m.quantidade}, catálogo com {tipo.quantidade}")
        prep.problemas += problemas
        if not problemas:
            _sorteio(m, travas, config, semente, prep)

    if tabela is not None:
        trecho = trecho_da_tabela(
            tabela,
            nome,
            config.geral.trecho.teto_tokens,
            config.geral.modelo_local.divisor_caracteres_por_token,
        )
        prep.linhas.append(
            f"- Trecho da tabela: {len(trecho.dispositivos)} dispositivos, cerca de "
            f"{trecho.tokens_estimados} tokens; {trecho.pares} dispositivo(s) com par "
            f"(mesmo diploma, mesmo assunto, função diferente)."
        )
        if not trecho.dispositivos:
            prep.problemas.append(f"{nome}: trecho da tabela vazio")
        if trecho.situacao != "ok":
            prep.problemas.append(
                f"{nome}: trecho da tabela com {trecho.tokens_estimados} tokens: {matriz.VOLTA}"
            )


def _sorteio(m: Matriz, travas: Travas, config: Config, semente: int, prep: Preparacao) -> None:
    cfg = config.geral.matriz
    try:
        sorteio = matriz.sortear(m, travas, semente, cfg)
        ensaio = matriz.combinacao_do_ensaio(m, travas, semente, cfg)
    except matriz.ErroMatriz as erro:
        prep.problemas.append(str(erro))
        return
    if sorteio.situacao == "ok":
        prep.linhas.append(
            f"- Sorteio de prova: {len(sorteio.combinacoes)} combinações em "
            f"{sorteio.tentativas} tentativa(s)."
        )
    else:
        prep.problemas.append(
            f"{m.tipo}: nenhuma combinação em {sorteio.tentativas} tentativas: {matriz.VOLTA}"
        )
    if ensaio.situacao == "ok":
        (c,) = ensaio.combinacoes
        prep.linhas.append(
            f"- Combinação do ensaio: {json.dumps(c.casa().model_dump(), ensure_ascii=False)}."
        )
    else:
        prep.problemas.append(f"{m.tipo}: combinação do ensaio não cabe: {matriz.VOLTA}")
