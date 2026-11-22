"""Revisão humana (ARQUITETURA §1.3, §4, §5.7, §5.9, §5.12.7 e §8; brief 020).

`revisar` é a única entrada das respostas do responsável. Mostra o próximo cartão
pendente, na ordem: ensaio, revisão, amostra de 10 cópias, amostra das descartadas e
leitura de publicação; faz as perguntas; mostra as respostas juntas e pede
confirmação. Antes de confirmar, qualquer resposta pode ser corrigida; depois, as
respostas são gravadas em `saida/cartoes/<id>_respostas.json` e nunca mudam. A segunda
etapa do cartão de revisão, com o veredito da fábrica, só é gerada depois disso. A
leitura do teclado vem por parâmetro (`ler_linha`), para os testes.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from fabrica.comum.formatos import (
    Amostras,
    CatalogoErros,
    CatalogoTipos,
    Conferencia,
    Descartada,
    Extracao,
    Ficha,
    FichaEmbargos,
    Gabarito,
    RespostaAmostra,
    RespostasCartao,
    ResultadoProgramas,
    TabelaNormas,
    TipoCartao,
)
from fabrica.conferencia import citacoes
from fabrica.estado import RefPeca, Servicos

CARTOES = "saida/cartoes"
ERROS = "saida/erros"
CONFERENCIAS = "saida/conferencias"
RASCUNHOS = "saida/rascunhos"
PERGUNTA_FICHA = (
    "A ficha: o caso fictício faz sentido e, nos embargos, o defeito existe na decisão? "
    "(aprovada ou reprovada)"
)
PERGUNTA_PECA = (
    "A peça: a peça pode virar modelo como está, na forma e no conteúdo? Peça com bloco "
    "obrigatório faltando é reprovada mesmo que o conteúdo seja bom. (aprovada ou reprovada)"
)
PERGUNTA_DADO = "Dado real: há algum nome, número ou dado que pareça real? (sim ou não)"
PERGUNTA_TRECHO = "Qual o trecho que parece real?"
PERGUNTA_CITACOES = (
    "Alguma citação do texto ficou fora da lista das resolvidas pelo programa? "
    "Escreva as citações separadas por ponto e vírgula, ou deixe vazio."
)
PERGUNTA_FORMATO = "Ensaio: tudo saiu no formato certo? (sim ou não)"
PERGUNTA_ERRADO = "O que saiu errado?"
PERGUNTA_PUBLICAR = "Leitura de publicação: esta versão pode ser publicada? (aprovada ou reprovada)"
_PECA = re.compile(r"^(?P<rodada>[er]\d{2})_(?P<tipo>.+)_(?P<numero>\d{3})_v1\.json$")

LerLinha = Callable[[str], str]
Escrever = Callable[[str], None]


class ErroRevisao(Exception):
    """Cartão sem o que mostrar."""


def caminho_amostras(rodada: str) -> str:
    return f"{ERROS}/{rodada}_amostras.json"


def caminho_respostas(identificador: str) -> str:
    return f"{CARTOES}/{identificador}_respostas.json"


# ---------------------------------------------------------------------------
# Leitura dos arquivos
# ---------------------------------------------------------------------------


def _respostas(identificador: str, servicos: Servicos) -> RespostasCartao | None:
    caminho = caminho_respostas(identificador)
    if not servicos.arquivos.existe(caminho):
        return None
    return servicos.arquivos.ler_json(caminho, RespostasCartao)


def _veredito(ref: RefPeca, servicos: Servicos) -> Conferencia | None:
    caminho = f"{CONFERENCIAS}/{ref.nome_versao}.json"
    if not servicos.arquivos.existe(caminho):
        return None
    return servicos.arquivos.ler_json(caminho, Conferencia)


def pecas_conferidas(servicos: Servicos, prefixo: str) -> list[RefPeca]:
    """As peças cuja primeira versão já tem veredito, das rodadas com o prefixo."""
    refs = []
    for caminho in servicos.arquivos.listar(CONFERENCIAS, f"{prefixo}*_v1.json"):
        achado = _PECA.match(caminho.rsplit("/", 1)[-1])
        if achado:
            refs.append(RefPeca(achado["rodada"], achado["tipo"], int(achado["numero"])))
    return sorted(refs)


def versao_aprovada(ref: RefPeca, servicos: Servicos) -> int | None:
    maxima = servicos.config.geral.volume.versoes_maximas
    for versao in range(1, maxima + 1):
        conferencia = _veredito(ref.com_versao(versao), servicos)
        if conferencia is not None and conferencia.veredito == "aprovada":
            return versao
    return None


def _destino_final(ref: RefPeca, servicos: Servicos) -> str | None:
    maxima = servicos.config.geral.volume.versoes_maximas
    for versao in range(1, maxima + 1):
        conferencia = _veredito(ref.com_versao(versao), servicos)
        if conferencia is not None and conferencia.veredito in ("aprovada", "descartada"):
            return conferencia.veredito
    return None


# ---------------------------------------------------------------------------
# Conteúdo dos cartões
# ---------------------------------------------------------------------------


def _destacar(texto: str, trecho: str | None) -> str:
    if trecho and trecho in texto:
        return texto.replace(trecho, f"**[[{trecho}]]**")
    return texto


def _secao_ficha(ficha: Any) -> list[str]:
    linhas = ["## A ficha", "", "```json", ficha.model_dump_json(indent=2), "```", ""]
    if isinstance(ficha, FichaEmbargos):
        decisao = ficha.decisao_embargada
        ancora = ficha.defeito.ancora
        na_decisao = ancora.trecho_literal if ancora.origem == "decisao" else None
        linhas += ["### Decisão fictícia (trecho da âncora destacado)", ""]
        for parte in (decisao.relatorio, decisao.fundamentacao, decisao.dispositivo):
            if parte:
                texto = _destacar(parte, na_decisao)
                linhas += [_destacar(texto, ficha.defeito.trecho_mencao), ""]
        linhas += ["### Argumentos das partes", ""]
        for argumento in ficha.argumentos_das_partes:
            texto = argumento.texto
            if ancora.origem == "argumento" and argumento.id == ancora.argumento_id:
                texto = _destacar(texto, ancora.trecho_literal)
            linhas += [f"- {argumento.id} ({argumento.parte}): {texto}"]
        linhas += [""]
    return linhas


def _secao_extracao(extracao: Extracao | None) -> list[str]:
    linhas = ["## Fatos e valores da extração (auxílio; a referência é a ficha)", ""]
    if extracao is None:
        return [*linhas, "Sem extração.", ""]
    linhas += [f"- valor: {v.texto} ({v.centavos} centavos; {v.lugar})" for v in extracao.valores]
    linhas += [f"- data: {d.texto} ({d.data})" for d in extracao.datas]
    linhas += [f"- pedido: {p.texto} ({p.natureza})" for p in extracao.pedidos]
    return [*linhas, ""]


def _secao_citacoes(ref: RefPeca, servicos: Servicos) -> list[str]:
    arquivos = servicos.arquivos
    caminho = f"{CONFERENCIAS}/{ref.nome_versao}_programas.json"
    programas = arquivos.ler_json(caminho, ResultadoProgramas) if arquivos.existe(caminho) else None
    tabela = arquivos.ler_json("dados/normas/tabela_normas.json", TabelaNormas)
    por_chave = {citacoes.chave(d): d for d in tabela.dispositivos}
    resolvidas = programas.citacoes_resolvidas if programas else []
    linhas = ["## Dispositivos citados", ""]
    vistos = set()
    for c in resolvidas:
        chave = (c.diploma, citacoes._artigo(c.artigo), citacoes._paragrafo(c.paragrafo))
        d = por_chave.get(chave)
        if d is not None and d.id not in vistos:
            vistos.add(d.id)
            linhas.append(f"- {d.id} (art. {d.artigo}, {d.paragrafo}): {d.texto_vigente}")
    if not vistos:
        linhas.append("Nenhum dispositivo da tabela citado.")
    linhas += ["", "## Citações resolvidas pelo programa", ""]
    linhas += [f"- {c.trecho}" for c in resolvidas] or ["Nenhuma."]
    return [*linhas, ""]


def _corpo(ref: RefPeca, servicos: Servicos, titulo_peca: str) -> list[str]:
    arquivos = servicos.arquivos
    ficha = arquivos.ler_json(f"saida/fichas/{ref.id}.json", Ficha).root
    caminho = f"{CONFERENCIAS}/{ref.nome_versao}_extracao.json"
    extracao = arquivos.ler_json(caminho, Extracao) if arquivos.existe(caminho) else None
    return [
        f"## {titulo_peca}",
        "",
        arquivos.ler_texto(f"{RASCUNHOS}/{ref.nome_versao}.md"),
        "",
        *_secao_ficha(ficha),
        *_secao_extracao(extracao),
        *_secao_citacoes(ref, servicos),
    ]


def _origem(item: str, quem: str) -> str:
    if quem == "programa":
        programa = {
            "citacao_fora_da_tabela": "citações",
            "dado_real": "dados reais",
            "semelhanca": "semelhança",
        }.get(item, "programa de regras")
        return f"programa ({programa})"
    return {"haiku": "haiku (checklist)", "local": "local (conferente local)"}.get(quem, quem)


def segunda_etapa(ref: RefPeca, servicos: Servicos) -> list[str]:
    conferencia = _veredito(ref, servicos)
    if conferencia is None:
        raise ErroRevisao(f"{ref.nome_versao}: a conferência não terminou")
    linhas = [
        "## Veredito da fábrica sobre a primeira versão",
        "",
        f"- Veredito: {conferencia.veredito}",
        f"- Categoria do motivo: {conferencia.categoria_motivo or '—'}",
        f"- Motivo: {conferencia.motivo or '—'}",
        "",
        "## Alertas (o que algum conferente reprovou, com a origem)",
        "",
    ]
    for caminho in conferencia.caminho:
        for r in caminho.respostas:
            if r.resposta == "nao_passa":
                linhas.append(
                    f"- {caminho.item}: não passa (origem: {_origem(r.item, r.quem)}): {r.trecho}"
                )
    linhas += [
        f"- {a.item or 'geral'}: {a.texto} (origem: {a.origem})" for a in conferencia.alertas
    ]
    return [*linhas, ""]


def cartao_revisao(ref: RefPeca, servicos: Servicos) -> str:
    """A primeira etapa: tudo para julgar a peça, sem o veredito da fábrica."""
    linhas = [
        f"# Cartão de revisão — {ref.id} (primeira etapa)",
        "",
        *_corpo(ref, servicos, "A peça (primeira versão)"),
        "## Perguntas",
        "",
        f"1. {PERGUNTA_FICHA}",
        f"2. {PERGUNTA_PECA}",
        f"3. {PERGUNTA_DADO}",
        f"4. {PERGUNTA_CITACOES}",
    ]
    return "\n".join(linhas) + "\n"


def cartao_segunda_etapa(ref: RefPeca, servicos: Servicos) -> str:
    linhas = [f"# Cartão de revisão — {ref.id} (segunda etapa)", "", *segunda_etapa(ref, servicos)]
    return "\n".join(linhas) + "\n"


def cartao_ensaio(ref: RefPeca, servicos: Servicos) -> str:
    """O ensaio não é às cegas: as duas etapas juntas."""
    linhas = [
        f"# Cartão do ensaio — {ref.id}",
        "",
        *_corpo(ref, servicos, "A peça (primeira versão)"),
        *segunda_etapa(ref, servicos),
        "## Perguntas",
        "",
        f"1. {PERGUNTA_FORMATO}",
        f"2. {PERGUNTA_DADO}",
    ]
    return "\n".join(linhas) + "\n"


def _catalogo_erros(servicos: Servicos) -> dict[str, str]:
    lido = servicos.arquivos.ler_json("dados/erros/catalogo_erros.json", CatalogoErros)
    return {e.tipo_erro: e.descricao for e in lido.erros}


def _original(copia: str, servicos: Servicos, original: str) -> str:
    return servicos.arquivos.ler_texto(f"{RASCUNHOS}/{original}.md")


def cartao_amostra_copias(amostras: Amostras, servicos: Servicos) -> str:
    descricoes = _catalogo_erros(servicos)
    linhas = [f"# Amostra de {len(amostras.copias)} cópias — {amostras.rodada}", ""]
    for n, copia in enumerate(amostras.copias, start=1):
        g = servicos.arquivos.ler_json(f"{ERROS}/{copia}_gabarito.json", Gabarito)
        linhas += [
            f"## {n}. {copia}",
            "",
            f"Erro do gabarito: {g.tipo_erro} — {descricoes.get(g.tipo_erro, '')}",
            f"Item principal: {g.item_principal}; itens aceitos: {', '.join(g.itens_aceitos)}",
            "",
            "### A cópia",
            "",
            servicos.arquivos.ler_texto(f"{ERROS}/{copia}.md"),
            "",
            "### A original",
            "",
            _original(copia, servicos, g.original),
            "",
        ]
    linhas += ["## Perguntas, para cada cópia", "", "1. O erro existe? 2. É o erro do gabarito?"]
    return "\n".join(linhas) + "\n"


def cartao_amostra_descartadas(amostras: Amostras, servicos: Servicos) -> str:
    """Sem mostrar o que o verificador respondeu."""
    descricoes = _catalogo_erros(servicos)
    linhas = [f"# Amostra de {len(amostras.descartadas)} descartadas — {amostras.rodada}", ""]
    for n, copia in enumerate(amostras.descartadas, start=1):
        d = servicos.arquivos.ler_json(f"{ERROS}/{copia}_descartada.json", Descartada)
        linhas += [
            f"## {n}. {copia}",
            "",
            f"Erro pedido: {d.tipo_erro} — {descricoes.get(d.tipo_erro, '')}",
            "",
            "### A cópia",
            "",
            servicos.arquivos.ler_texto(f"{ERROS}/{copia}.md"),
            "",
            "### A original",
            "",
            _original(copia, servicos, d.original),
            "",
        ]
    linhas += ["## Pergunta, para cada cópia", "", "O erro pedido existe na cópia?"]
    return "\n".join(linhas) + "\n"


def cartao_leitura(ref: RefPeca, servicos: Servicos) -> str:
    """A leitura de publicação da versão refeita aprovada: não é às cegas."""
    linhas = [
        f"# Leitura de publicação — {ref.nome_versao}",
        "",
        *_corpo(ref, servicos, f"A versão aprovada pela fábrica (v{ref.versao})"),
        *segunda_etapa(ref, servicos),
        "## Perguntas",
        "",
        f"1. {PERGUNTA_PUBLICAR}",
        f"2. {PERGUNTA_DADO}",
    ]
    return "\n".join(linhas) + "\n"


# ---------------------------------------------------------------------------
# Perguntas e confirmação
# ---------------------------------------------------------------------------

TipoPergunta = Literal["veredito", "sim_nao", "texto"]


@dataclass(frozen=True)
class Pergunta:
    chave: str
    texto: str
    tipo: TipoPergunta
    se: tuple[str, Any] | None = None  # só é feita quando a resposta da chave tem o valor


def _ler(pergunta: Pergunta, ler: LerLinha, escrever: Escrever) -> Any:
    while True:
        bruto = ler(f"{pergunta.texto} ").strip()
        lido = bruto.lower()
        if pergunta.tipo == "texto":
            return bruto
        if pergunta.tipo == "veredito" and lido in ("aprovada", "a", "reprovada", "r"):
            return "aprovada" if lido.startswith("a") else "reprovada"
        if pergunta.tipo == "sim_nao" and lido in ("s", "sim", "n", "nao", "não"):
            return lido.startswith("s")
        escrever(f"resposta inválida: {bruto!r}")


def perguntar(perguntas: list[Pergunta], ler: LerLinha, escrever: Escrever) -> dict[str, Any]:
    """Faz as perguntas, mostra as respostas juntas e só devolve depois da confirmação."""
    respostas: dict[str, Any] = {}

    def completar() -> None:
        for p in perguntas:
            ativa = p.se is None or respostas.get(p.se[0]) == p.se[1]
            if not ativa:
                respostas.pop(p.chave, None)
            elif p.chave not in respostas:
                respostas[p.chave] = _ler(p, ler, escrever)

    completar()
    while True:
        escrever("Respostas:")
        ativas = [(n, p) for n, p in enumerate(perguntas, start=1) if p.chave in respostas]
        for n, p in ativas:
            escrever(f"  {n}. {p.texto} -> {respostas[p.chave]}")
        escolha = ler("Confirmar (s) ou corrigir (número da pergunta)? ").strip().lower()
        if escolha in ("s", "sim"):
            return respostas
        if escolha.isdigit() and any(n == int(escolha) for n, _ in ativas):
            alvo = perguntas[int(escolha) - 1]
            respostas[alvo.chave] = _ler(alvo, ler, escrever)
            completar()
            continue
        escrever(f"escolha inválida: {escolha!r}")


# ---------------------------------------------------------------------------
# Pendentes, respostas e concordância
# ---------------------------------------------------------------------------


def _amostras(servicos: Servicos) -> list[Amostras]:
    lidas = servicos.arquivos.listar(ERROS, "*_amostras.json")
    return [servicos.arquivos.ler_json(c, Amostras) for c in sorted(lidas)]


def pendente(servicos: Servicos) -> tuple[TipoCartao, str] | None:
    """O próximo cartão sem resposta, na ordem fixa."""
    for ref in pecas_conferidas(servicos, "e"):
        if _respostas(ref.id, servicos) is None:
            return "ensaio", ref.id
    rodada = pecas_conferidas(servicos, "r")
    for ref in rodada:
        if _respostas(ref.id, servicos) is None:
            return "revisao", ref.id
    for amostras in _amostras(servicos):
        if amostras.copias and _respostas(f"{amostras.rodada}_amostra_copias", servicos) is None:
            return "amostra_copias", f"{amostras.rodada}_amostra_copias"
    for amostras in _amostras(servicos):
        identificador = f"{amostras.rodada}_amostra_descartadas"
        if amostras.descartadas and _respostas(identificador, servicos) is None:
            return "amostra_descartadas", identificador
    for ref in rodada:
        respostas = _respostas(ref.id, servicos)
        versao = versao_aprovada(ref, servicos)
        if respostas is None or respostas.veredito_ficha != "aprovada" or not versao:
            continue
        identificador = f"{ref.com_versao(versao).nome_versao}_leitura_publicacao"
        if versao >= 2 and _respostas(identificador, servicos) is None:
            return "leitura_publicacao", identificador
    return None


def gravar_respostas(respostas: RespostasCartao, servicos: Servicos) -> None:
    """Grava uma vez só: uma segunda gravação é recusada (o arquivo já existe)."""
    servicos.arquivos.gravar_json(caminho_respostas(respostas.id_cartao), respostas)


def destino_das_respostas(ficha: str | None, peca: str | None) -> str:
    """ARQUITETURA §5.12.7."""
    if ficha != "aprovada":
        return "fora_das_medidas"
    return "peca_boa" if peca == "aprovada" else "peca_ruim"


def concordancia(peca: str, servicos: Servicos) -> dict[str, Any]:
    """A concordância sobre a primeira versão, nos dois sentidos, só com ficha aprovada."""
    respostas = _respostas(peca, servicos)
    if respostas is None:
        raise ErroRevisao(f"{peca}: o cartão de revisão não foi respondido")
    rodada, _, resto = peca.partition("_")
    tipo, _, numero = resto.rpartition("_")
    ref = RefPeca(rodada, tipo, int(numero))
    v1 = _veredito(ref, servicos)
    fabrica = v1.veredito if v1 is not None else None
    sentido = None
    if respostas.veredito_ficha == "aprovada":
        aprovou_a_fabrica = fabrica == "aprovada"
        aprovou_o_responsavel = respostas.veredito_peca == "aprovada"
        if aprovou_a_fabrica == aprovou_o_responsavel:
            sentido = "concordam"
        elif aprovou_a_fabrica:
            sentido = "so_a_fabrica_aprovou"
        else:
            sentido = "so_o_responsavel_aprovou"
    return {
        "peca": peca,
        "veredito_ficha": respostas.veredito_ficha,
        "veredito_peca": respostas.veredito_peca,
        "veredito_da_fabrica_v1": fabrica,
        "sentido": sentido,
        "destino": destino_das_respostas(respostas.veredito_ficha, respostas.veredito_peca),
        "versao_final_da_fabrica": versao_aprovada(ref, servicos),
        "destino_final_da_fabrica": _destino_final(ref, servicos),
    }


def _respostas_cartao(
    identificador: str, tipo: TipoCartao, servicos: Servicos, **campos: Any
) -> RespostasCartao:
    dados: dict[str, Any] = {
        "id_cartao": identificador,
        "tipo_cartao": tipo,
        "veredito_ficha": None,
        "veredito_peca": None,
        "dado_real": False,
        "dado_real_trecho": None,
        "citacoes_nao_resolvidas": [],
        "formato_certo": None,
        "formato_errado": None,
        "amostra": [],
        "data_confirmacao": servicos.relogio(),
    }
    dados.update(campos)
    return RespostasCartao(**dados)


def _dado_real() -> list[Pergunta]:
    return [
        Pergunta("dado_real", PERGUNTA_DADO, "sim_nao"),
        Pergunta("trecho", PERGUNTA_TRECHO, "texto", ("dado_real", True)),
    ]


def _ref_de(identificador: str) -> RefPeca:
    achado = re.match(r"^([er]\d{2})_(.+)_(\d{3})(?:_v(\d))?", identificador)
    if achado is None:
        raise ErroRevisao(f"{identificador}: não é id de peça")
    versao = int(achado[4]) if achado[4] else 1
    return RefPeca(achado[1], achado[2], int(achado[3]), versao)


def _mostrar(caminho: str, texto: str, servicos: Servicos, escrever: Escrever) -> None:
    if not servicos.arquivos.existe(caminho):
        servicos.arquivos.gravar_texto(caminho, texto)
    escrever(servicos.arquivos.ler_texto(caminho))


def revisar(servicos: Servicos, ler: LerLinha, escrever: Escrever = print) -> str | None:
    """Mostra e responde o próximo cartão pendente; devolve o id respondido."""
    proximo = pendente(servicos)
    if proximo is None:
        escrever("Nenhum cartão pendente.")
        return None
    tipo, identificador = proximo
    if tipo == "revisao":
        ref = _ref_de(identificador)
        _mostrar(
            f"{CARTOES}/{identificador}_etapa1.md",
            cartao_revisao(ref, servicos),
            servicos,
            escrever,
        )
        lidas = perguntar(
            [
                Pergunta("ficha", PERGUNTA_FICHA, "veredito"),
                Pergunta("peca", PERGUNTA_PECA, "veredito"),
                *_dado_real(),
                Pergunta("citacoes", PERGUNTA_CITACOES, "texto"),
            ],
            ler,
            escrever,
        )
        citadas = [c.strip() for c in lidas["citacoes"].split(";") if c.strip()]
        respostas = _respostas_cartao(
            identificador,
            tipo,
            servicos,
            veredito_ficha=lidas["ficha"],
            veredito_peca=lidas["peca"],
            dado_real=lidas["dado_real"],
            dado_real_trecho=lidas.get("trecho"),
            citacoes_nao_resolvidas=citadas,
        )
        gravar_respostas(respostas, servicos)
        segunda = f"{CARTOES}/{identificador}_etapa2.md"
        _mostrar(segunda, cartao_segunda_etapa(ref, servicos), servicos, escrever)
        servicos.arquivos.gravar_texto(
            f"{CARTOES}/{identificador}_concordancia.json",
            json.dumps(concordancia(identificador, servicos), ensure_ascii=False, indent=2) + "\n",
        )
        return identificador
    if tipo == "ensaio":
        ref = _ref_de(identificador)
        _mostrar(
            f"{CARTOES}/{identificador}_ensaio.md", cartao_ensaio(ref, servicos), servicos, escrever
        )
        lidas = perguntar(
            [
                Pergunta("formato", PERGUNTA_FORMATO, "sim_nao"),
                Pergunta("errado", PERGUNTA_ERRADO, "texto", ("formato", False)),
                *_dado_real(),
            ],
            ler,
            escrever,
        )
        respostas = _respostas_cartao(
            identificador,
            tipo,
            servicos,
            formato_certo=lidas["formato"],
            formato_errado=lidas.get("errado"),
            dado_real=lidas["dado_real"],
            dado_real_trecho=lidas.get("trecho"),
        )
    elif tipo in ("amostra_copias", "amostra_descartadas"):
        rodada = identificador.partition("_")[0]
        amostras = servicos.arquivos.ler_json(caminho_amostras(rodada), Amostras)
        if tipo == "amostra_copias":
            texto, copias = cartao_amostra_copias(amostras, servicos), amostras.copias
            perguntas = [
                q
                for c in copias
                for q in (
                    Pergunta(f"{c}:existe", f"{c}: o erro existe? (sim ou não)", "sim_nao"),
                    Pergunta(
                        f"{c}:gabarito",
                        f"{c}: é o erro do gabarito? (sim ou não)",
                        "sim_nao",
                        (f"{c}:existe", True),
                    ),
                )
            ]
        else:
            texto, copias = cartao_amostra_descartadas(amostras, servicos), amostras.descartadas
            perguntas = [
                Pergunta(
                    f"{c}:existe", f"{c}: o erro pedido existe na cópia? (sim ou não)", "sim_nao"
                )
                for c in copias
            ]
        _mostrar(f"{CARTOES}/{identificador}.md", texto, servicos, escrever)
        lidas = perguntar(perguntas, ler, escrever)
        amostra = [
            RespostaAmostra(
                copia=c,
                erro_existe=lidas[f"{c}:existe"],
                erro_do_gabarito=lidas.get(f"{c}:gabarito") if tipo == "amostra_copias" else None,
            )
            for c in copias
        ]
        respostas = _respostas_cartao(identificador, tipo, servicos, amostra=amostra)
    else:
        ref = _ref_de(identificador)
        _mostrar(f"{CARTOES}/{identificador}.md", cartao_leitura(ref, servicos), servicos, escrever)
        lidas = perguntar(
            [Pergunta("publicar", PERGUNTA_PUBLICAR, "veredito"), *_dado_real()], ler, escrever
        )
        respostas = _respostas_cartao(
            identificador,
            tipo,
            servicos,
            veredito_peca=lidas["publicar"],
            dado_real=lidas["dado_real"],
            dado_real_trecho=lidas.get("trecho"),
        )
    gravar_respostas(respostas, servicos)
    return identificador


def resumo(servicos: Servicos, escrever: Escrever = print) -> int:
    """Lista os cartões respondidos, com as respostas e a data, sem mudar nada."""
    caminhos = sorted(servicos.arquivos.listar(CARTOES, "*_respostas.json"))
    if not caminhos:
        escrever("Nenhum cartão respondido.")
    for caminho in caminhos:
        r = servicos.arquivos.ler_json(caminho, RespostasCartao)
        campos = {
            "ficha": r.veredito_ficha,
            "peça": r.veredito_peca,
            "dado real": ("sim: " + (r.dado_real_trecho or "")) if r.dado_real else "não",
            "formato certo": r.formato_certo,
            "o que saiu errado": r.formato_errado,
            "citações fora da lista": "; ".join(r.citacoes_nao_resolvidas) or None,
        }
        texto = "; ".join(f"{k}: {v}" for k, v in campos.items() if v is not None)
        amostra = "; ".join(
            f"{a.copia}: existe={a.erro_existe}, gabarito={a.erro_do_gabarito}" for a in r.amostra
        )
        data = r.data_confirmacao.isoformat(timespec="minutes")
        escrever(
            f"{r.id_cartao} · {r.tipo_cartao} · confirmado em {data} · {texto} {amostra}".strip()
        )
    return len(caminhos)


def rotulo(tipo: str, servicos: Servicos) -> str:
    catalogo = servicos.arquivos.ler_json("dados/catalogo/tipos.json", CatalogoTipos)
    return next(t.rotulo for t in catalogo.tipos if t.nome_curto == tipo)
