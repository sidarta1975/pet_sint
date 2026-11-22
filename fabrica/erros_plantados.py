"""Erros plantados por programa (ARQUITETURA §5.1, §5.7 e Anexos C.1, C.2 e C.4;
brief 019).

Para cada peça boa da rodada (no ensaio, as três peças), uma cópia por programa,
feita sobre a primeira versão: um erro de regra (Anexo C.1) ou, em metade das peças
boas do tipo, arredondada para baixo e escolhidas entre as que citam dispositivo com
par, a função trocada (Anexo C.2). O trecho a trocar é achado pelo texto que a extração
da original devolveu. Cada cópia muda uma só região; a marca fica no topo. A cópia vai
para `saida/erros/<peça>_erro1_1.md` e o gabarito para `..._erro1_1_gabarito.json`.
As vagas 2 em diante são do Opus (brief 021). Não chama modelo.
"""

from __future__ import annotations

import datetime
import difflib
import itertools
import json
import random
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Literal

from pydantic import ValidationError

from fabrica import estado, estruturas, matriz
from fabrica.comum import normalizacao as norm
from fabrica.comum.api_claude import nome_do_pedido
from fabrica.comum.congelamento import Congelamento
from fabrica.comum.formatos import (
    Amostras,
    CatalogoErros,
    CatalogoTipos,
    ConfigAmostras,
    Configuracao,
    CopiaComErro,
    DataExtraida,
    Descartada,
    Dispositivo,
    EstruturaMontada,
    Extracao,
    FeriadosNacionais,
    Ficha,
    FichaInicial,
    FichaQualquer,
    Gabarito,
    ListaConferencia,
    ListasFicticias,
    Ocorrencia,
    Pedido,
    Perfil,
    Resposta,
    RespostaCopiaOpus,
    RespostasCartao,
    RespostaVerificacao,
    ResultadoProgramas,
    TabelaNormas,
    TermosInequivocos,
    TipoCatalogo,
    TipoErroCatalogo,
)
from fabrica.conferencia import citacoes, regras
from fabrica.conferencia import extracao as extracao_mod
from fabrica.conferencia.regras import MARCA
from fabrica.estado import RefPeca, Servicos
from fabrica.estruturas import Trecho

PASTA = "saida/erros"
CARTOES = "saida/cartoes"
CATALOGO = "dados/catalogo/tipos.json"
ERROS = "dados/erros/catalogo_erros.json"
FUNCAO_TROCADA = "funcao_trocada"
MESES = (
    "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro"
).split()
TENTATIVAS = 200


class ErroErros(Exception):
    """Rodada sem peças, ou arquivo da peça que falta."""


@dataclass(frozen=True)
class Material:
    """O que o programa lê para fazer a cópia de uma peça."""

    peca: str
    tipo: str
    rascunho: str
    extracao: Extracao
    ficha: FichaQualquer
    montada: EstruturaMontada
    tabela: TabelaNormas
    trecho: Trecho
    termos: TermosInequivocos
    listas: ListasFicticias
    config: Configuracao
    catalogo: TipoCatalogo
    erros: CatalogoErros
    feriados: list[datetime.date]
    perfis: dict[str, Perfil]


@dataclass(frozen=True)
class Copia:
    """A cópia com erro: o texto inteiro e a região trocada no original."""

    tipo_erro: str
    texto: str
    inicio: int
    fim: int
    trecho_original: str
    trecho_novo: str
    valor_novo: int | None = None
    data_nova: datetime.date | None = None


def perfil(m: Material) -> Perfil:
    return m.perfis[m.catalogo.perfil]


# ---------------------------------------------------------------------------
# Números e datas por escrito
# ---------------------------------------------------------------------------

_UNIDADES = (
    "zero um dois três quatro cinco seis sete oito nove dez onze doze treze quatorze "
    "quinze dezesseis dezessete dezoito dezenove"
).split()
_DEZENAS = "_ _ vinte trinta quarenta cinquenta sessenta setenta oitenta noventa".split()
_CENTENAS = (
    "_ cento duzentos trezentos quatrocentos quinhentos seiscentos setecentos oitocentos novecentos"
).split()


def _ate_mil(n: int) -> str:
    if n == 100:
        return "cem"
    partes = []
    if n >= 100:
        partes.append(_CENTENAS[n // 100])
    resto = n % 100
    if resto:
        if resto < 20:
            partes.append(_UNIDADES[resto])
        else:
            dezena = _DEZENAS[resto // 10]
            partes.append(dezena if resto % 10 == 0 else f"{dezena} e {_UNIDADES[resto % 10]}")
    return " e ".join(partes)


def _inteiro(n: int) -> str:
    if n == 0:
        return "zero"
    grupos = [(n // 1_000_000, "milhao"), ((n // 1000) % 1000, "mil"), (n % 1000, "")]
    textos: list[tuple[int, str]] = []
    for valor, escala in grupos:
        if not valor:
            continue
        if escala == "milhao":
            texto = "um milhão" if valor == 1 else f"{_ate_mil(valor)} milhões"
        elif escala == "mil":
            texto = "mil" if valor == 1 else f"{_ate_mil(valor)} mil"
        else:
            texto = _ate_mil(valor)
        textos.append((valor, texto))
    saida = textos[0][1]
    for valor, texto in textos[1:]:
        ligacao = " e " if valor < 100 or valor % 100 == 0 else ", "
        saida += ligacao + texto
    return saida


def por_extenso(centavos: int) -> str:
    """O valor em reais por extenso, em português ("mil e quinhentos reais")."""
    reais, cents = divmod(centavos, 100)
    partes = []
    if reais:
        moeda = "real" if reais == 1 else "reais"
        de = " de" if reais % 1_000_000 == 0 else ""
        partes.append(f"{_inteiro(reais)}{de} {moeda}")
    if cents:
        partes.append(f"{_inteiro(cents)} {'centavo' if cents == 1 else 'centavos'}")
    return " e ".join(partes) if partes else "zero real"


def formatar_reais(centavos: int) -> str:
    reais, cents = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{cents:02d}"


def _escrever_data(data: datetime.date, como: str) -> str:
    """A data no mesmo estilo do texto original."""
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", como.strip()):
        return data.strftime("%d/%m/%Y")
    return f"{data.day} de {MESES[data.month - 1]} de {data.year}"


def datas_da_ficha(ficha: FichaQualquer) -> set[datetime.date]:
    achadas: set[datetime.date] = set()

    def andar(valor: Any) -> None:
        if isinstance(valor, dict):
            for item in valor.values():
                andar(item)
        elif isinstance(valor, list):
            for item in valor:
                andar(item)
        elif isinstance(valor, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
            achadas.add(datetime.date.fromisoformat(valor))

    andar(ficha.model_dump(mode="json"))
    return achadas


# ---------------------------------------------------------------------------
# Região única
# ---------------------------------------------------------------------------


def _uma_vez(texto: str, trecho: str) -> int | None:
    """A posição do trecho, se ele aparece uma só vez fora da linha da marca."""
    if not trecho or texto.count(trecho) != 1:
        return None
    posicao = texto.index(trecho)
    return posicao if posicao > len(MARCA) else None


def _copia(m: Material, tipo_erro: str, inicio: int, fim: int, novo: str, **extra: Any) -> Copia:
    original = m.rascunho
    return Copia(
        tipo_erro=tipo_erro,
        texto=original[:inicio] + novo + original[fim:],
        inicio=inicio,
        fim=fim,
        trecho_original=original[inicio:fim],
        trecho_novo=novo,
        **extra,
    )


def _bloco(m: Material, nomes: Sequence[str]) -> tuple[int, int] | None:
    """Início e fim do texto do primeiro bloco presente entre os nomes pedidos."""
    titulos = {b.nome: b.titulo for b in m.montada.blocos}
    for nome in nomes:
        titulo = titulos.get(nome)
        if titulo is None:
            continue
        cabeca = re.search(rf"^##\s+{re.escape(titulo)}\s*$", m.rascunho, re.MULTILINE)
        if cabeca is None:
            continue
        seguinte = re.search(r"^##\s", m.rascunho[cabeca.end() :], re.MULTILINE)
        fim = cabeca.end() + seguinte.start() if seguinte else len(m.rascunho)
        fim = len(m.rascunho[:fim].rstrip())
        return cabeca.end(), fim
    return None


# ---------------------------------------------------------------------------
# Erros de regra (Anexo C.1)
# ---------------------------------------------------------------------------


def _somas(valores: Sequence[int]) -> set[int]:
    return {sum(c) for n in range(1, len(valores) + 1) for c in itertools.combinations(valores, n)}


def _proibidos(m: Material) -> set[int]:
    valores = [v.centavos for v in m.ficha.valores]
    referencias = m.config.referencias_legais
    salario = referencias.salario_minimo_centavos
    legais = {salario, referencias.alcada_em_salarios_minimos * salario}
    if isinstance(m.ficha, FichaInicial):
        legais |= {
            m.ficha.salario_minimo_referencia,
            referencias.alcada_em_salarios_minimos * m.ficha.salario_minimo_referencia,
        }
    return set(valores) | _somas(valores) | legais


def _regiao_do_valor(m: Material, texto: str) -> tuple[int, int, str] | None:
    """A região do valor (algarismos e, se houver, o extenso entre parênteses)."""
    inicio = _uma_vez(m.rascunho, texto)
    if inicio is None:
        return None
    fim = inicio + len(texto)
    if "(" in texto:
        return inicio, fim, " "
    seguinte = re.match(r"(\s*)\(([^()]*)\)", m.rascunho[fim:])
    if seguinte and norm.tem_extenso(texto + seguinte.group()):
        return inicio, fim + seguinte.end(), seguinte.group(1)
    return inicio, fim, ""


def _novo_valor(
    m: Material,
    tipo_erro: str,
    centavos: int,
    inicio: int,
    fim: int,
    espaco: str,
    candidato: int,
) -> Copia:
    escrito = formatar_reais(candidato)
    if espaco:
        escrito += f"{espaco}({por_extenso(candidato)})"
    return _copia(m, tipo_erro, inicio, fim, escrito, valor_novo=candidato)


def _valor_trocado(m: Material, rng: random.Random) -> Copia | None:
    candidatos = [v for v in m.extracao.valores if v.lugar in ("pedido", "valor_causa")]
    if m.tipo == "embargos_declaracao":
        candidatos = list(m.extracao.valores)  # o valor da decisão
    ficha = {v.centavos for v in m.ficha.valores}
    regioes = [
        (v, r)
        for v in candidatos
        if v.centavos in ficha and (r := _regiao_do_valor(m, v.texto)) is not None
    ]
    if not regioes:
        return None
    valor, (inicio, fim, espaco) = rng.choice(regioes)
    proibidos = _proibidos(m)
    diferenca = m.config.erros.diferenca_minima_valor_trocado
    for _ in range(TENTATIVAS):
        fator = rng.choice((rng.uniform(0.3, 0.8), rng.uniform(1.25, 2.5)))
        candidato = max(100, round(valor.centavos * fator / 100) * 100)
        if all(abs(candidato - p) > diferenca * p for p in proibidos):
            return _novo_valor(m, "valor_trocado", valor.centavos, inicio, fim, espaco, candidato)
    return None


def _acima_da_alcada(m: Material, rng: random.Random) -> Copia | None:
    if not isinstance(m.ficha, FichaInicial):
        return None
    causa = [v for v in m.extracao.valores if v.lugar == "valor_causa"]
    regioes = [r for v in causa if (r := _regiao_do_valor(m, v.texto)) is not None]
    if not regioes:
        return None
    inicio, fim, espaco = regioes[0]
    referencias = m.config.referencias_legais
    alcada = referencias.alcada_em_salarios_minimos * m.ficha.salario_minimo_referencia
    candidato = round(alcada * rng.uniform(1.1, 2.0) / 100) * 100
    return _novo_valor(m, "acima_da_alcada", causa[0].centavos, inicio, fim, espaco, candidato)


def _data_nova(
    m: Material, rng: random.Random, original: datetime.date, depois_de: datetime.date | None
) -> datetime.date | None:
    proibidas = datas_da_ficha(m.ficha)
    for _ in range(TENTATIVAS):
        if depois_de is not None:
            nova = depois_de + datetime.timedelta(days=rng.randint(3, 30))
        else:
            meses = rng.choice((-3, -2, -1, 1, 2, 3))
            ano, mes = divmod(original.year * 12 + original.month - 1 + meses, 12)
            nova = datetime.date(ano, mes + 1, min(original.day, 28))
            if (nova.year, nova.month) == (original.year, original.month):
                continue
        if nova not in proibidas:
            return nova
    return None


def _trocar_data(
    m: Material, tipo_erro: str, data: DataExtraida, nova: datetime.date | None
) -> Copia | None:
    inicio = _uma_vez(m.rascunho, data.texto)
    if inicio is None or nova is None:
        return None
    escrita = _escrever_data(nova, data.texto)
    return _copia(m, tipo_erro, inicio, inicio + len(data.texto), escrita, data_nova=nova)


def _data_trocada(m: Material, rng: random.Random) -> Copia | None:
    dos_fatos = {f.data for f in m.ficha.fatos}
    candidatas = [
        d
        for d in m.extracao.datas
        if d.data is not None
        and len(d.data) == 10
        and datetime.date.fromisoformat(d.data) in dos_fatos
        and _uma_vez(m.rascunho, d.texto) is not None
    ]
    if not candidatas:
        return None
    escolhida = rng.choice(candidatas)
    assert escolhida.data is not None
    original = datetime.date.fromisoformat(escolhida.data)
    return _trocar_data(m, "data_trocada", escolhida, _data_nova(m, rng, original, None))


def _fora_do_prazo(m: Material, rng: random.Random) -> Copia | None:
    prazo = m.ficha.momento_processual.prazo
    data_peca = m.extracao.data_peca
    if prazo is None or data_peca is None or len(data_peca) != 10:
        return None
    escolhida = next(
        (d for d in m.extracao.datas if d.data == data_peca and _uma_vez(m.rascunho, d.texto)),
        None,
    )
    if escolhida is None:
        return None
    termo = matriz.termo_final(prazo.inicio, prazo.dias_uteis, m.feriados)
    original = datetime.date.fromisoformat(data_peca)
    return _trocar_data(m, "fora_do_prazo", escolhida, _data_nova(m, rng, original, termo))


def _citacao_fora_da_tabela(m: Material, rng: random.Random) -> Copia | None:
    resolvidas = list(citacoes.ler(m.rascunho, m.tabela).resolvidas)
    rng.shuffle(resolvidas)
    for citacao in resolvidas:
        numero = re.search(r"\d{1,3}(?:\.\d{3})*", citacao.trecho)
        if numero is None:
            continue
        artigos = {
            citacoes.chave(d)[1] for d in m.tabela.dispositivos if d.diploma == citacao.diploma
        }
        inicio = citacao.posicao + numero.start()
        fim = citacao.posicao + numero.end()
        if m.rascunho[inicio:fim] != numero.group():
            continue
        for _ in range(20):
            novo = str(rng.randint(200, 999))
            if novo in artigos:
                continue
            copia = _copia(m, "citacao_fora_da_tabela", inicio, fim, novo)
            if citacoes.conferir(copia.texto, m.tabela).item.resposta == "nao_passa":
                return copia
    return None


def _juizo_trocado(m: Material, rng: random.Random) -> Copia | None:
    juizo = m.extracao.juizo
    inicio = _uma_vez(m.rascunho, juizo) if juizo else None
    if juizo is None or inicio is None:
        return None
    processo = m.ficha.processo
    if m.tipo == "peticao_inicial_jec":
        novo = f"Vara da Fazenda Pública da Comarca de {processo.comarca}"
    elif m.tipo == "embargos_declaracao":
        novo = f"Tribunal de Justiça do Estado de {processo.uf}"
    else:
        outras = sorted(c.nome for c in m.listas.cidades if c.nome != processo.comarca)
        novo = f"Juizado Especial Cível da Comarca de {rng.choice(outras)}"
    return _copia(m, "juizo_trocado", inicio, inicio + len(juizo), novo)


# O "bloco de fundamentos" de cada tipo: o primeiro destes que a peça tiver.
BLOCOS_DE_FUNDAMENTOS = ("fundamentos", "razoes", "novo_endereco", "exposicao")


def _termo_inequivoco(m: Material, rng: random.Random) -> Copia | None:
    bloco = _bloco(m, BLOCOS_DE_FUNDAMENTOS)
    if bloco is None or not m.termos.termos:
        return None
    termo = rng.choice(m.termos.termos).termo
    _, fim = bloco
    return _copia(m, "termo_inequivoco", fim, fim, f" Ressalte-se, por fim, {termo}.")


def _pedido_incompativel(m: Material, rng: random.Random) -> Copia | None:
    rito = m.ficha.processo.rito
    prontos = [
        p.texto
        for p in m.listas.pedidos_incompativeis
        if p.tipo == m.tipo and (p.rito is None or p.rito == rito)
    ]
    bloco = _bloco(m, ("pedidos",))
    if not prontos or bloco is None:
        return None
    _, fim = bloco
    return _copia(m, "pedido_incompativel_com_rito", fim, fim, f"\n\n{rng.choice(prontos)}")


# ---------------------------------------------------------------------------
# Erro de julgamento (Anexo C.2)
# ---------------------------------------------------------------------------


def _pares(m: Material) -> dict[tuple[str, str, str], list[Dispositivo]]:
    """Para cada dispositivo do trecho, os do mesmo diploma e assunto com outra função."""
    dispositivos = m.trecho.dispositivos
    return {
        citacoes.chave(d): [
            o
            for o in dispositivos
            if o.diploma == d.diploma and o.assunto == d.assunto and o.funcao != d.funcao
        ]
        for d in dispositivos
    }


def _citadas_com_par(m: Material) -> list[tuple[Any, list[Dispositivo]]]:
    pares = _pares(m)
    achadas = []
    for c in citacoes.ler(m.rascunho, m.tabela).resolvidas:
        chave = (c.diploma, citacoes._artigo(c.artigo), citacoes._paragrafo(c.paragrafo))
        if pares.get(chave):
            achadas.append((c, pares[chave]))
    return achadas


def tem_par(m: Material) -> bool:
    return bool(_citadas_com_par(m))


def _funcao_trocada(m: Material, rng: random.Random) -> Copia | None:
    citadas = _citadas_com_par(m)
    rng.shuffle(citadas)
    for citacao, pares in citadas:
        resto = re.search(r"\s+(d[oa]s?\s+\S.*)$", citacao.trecho)
        if resto is None:
            continue
        for par in rng.sample(pares, len(pares)):
            parte = "" if par.paragrafo == "caput" else f", {par.paragrafo},"
            novo = f"art. {par.artigo}{parte} {resto.group(1)}"
            inicio = citacao.posicao
            copia = _copia(m, FUNCAO_TROCADA, inicio, inicio + len(citacao.trecho), novo)
            lidas = citacoes.ler(copia.texto, m.tabela).resolvidas
            chaves = {
                (c.diploma, citacoes._artigo(c.artigo), citacoes._paragrafo(c.paragrafo))
                for c in lidas
            }
            passa = citacoes.conferir(copia.texto, m.tabela).item.resposta == "passa"
            if citacoes.chave(par) in chaves and passa:
                return copia
    return None


GERADORES = {
    "valor_trocado": _valor_trocado,
    "data_trocada": _data_trocada,
    "fora_do_prazo": _fora_do_prazo,
    "acima_da_alcada": _acima_da_alcada,
    "citacao_fora_da_tabela": _citacao_fora_da_tabela,
    "juizo_trocado": _juizo_trocado,
    "termo_inequivoco": _termo_inequivoco,
    "pedido_incompativel_com_rito": _pedido_incompativel,
    FUNCAO_TROCADA: _funcao_trocada,
}


def gerar(tipo_erro: str, m: Material, rng: random.Random) -> Copia | None:
    """A cópia com o erro pedido, ou None se o erro não cabe nesta peça."""
    entrada = next((e for e in m.erros.erros if e.tipo_erro == tipo_erro), None)
    if entrada is None or m.tipo not in entrada.tipos:
        return None
    return GERADORES[tipo_erro](m, rng)


# ---------------------------------------------------------------------------
# Sorteio
# ---------------------------------------------------------------------------


def sortear(
    tipo: str,
    semente: int,
    pecas: Sequence[str],
    com_par: set[str],
    viaveis: dict[str, list[str]],
    regras: Sequence[str],
) -> dict[str, str]:
    """O tipo de erro de cada peça boa do tipo. A função trocada vai para metade das
    peças, arredondada para baixo, escolhidas entre as que citam dispositivo com par;
    as outras recebem um erro de regra viável, equilibrado entre os do tipo."""
    rng = random.Random(f"{semente}:{tipo}:erros_programa")
    ordenadas = sorted(pecas)
    candidatas = [p for p in ordenadas if p in com_par]
    julgamento = set(rng.sample(candidatas, min(len(ordenadas) // 2, len(candidatas))))
    ordem = {e: i for i, e in enumerate(rng.sample(list(regras), len(regras)))}
    contagem: Counter[str] = Counter()
    plano: dict[str, str] = {}
    for peca in ordenadas:
        if peca in julgamento:
            plano[peca] = FUNCAO_TROCADA
            continue
        opcoes = [e for e in regras if e in viaveis.get(peca, [])]
        if not opcoes:
            continue
        escolhido = min(opcoes, key=lambda e: (contagem[e], ordem[e]))
        contagem[escolhido] += 1
        plano[peca] = escolhido
    return plano


# ---------------------------------------------------------------------------
# Leitura das peças e gravação das cópias
# ---------------------------------------------------------------------------


def _ref(rodada: str, peca: str) -> RefPeca:
    tipo, _, numero = peca[len(rodada) + 1 :].rpartition("_")
    return RefPeca(rodada=rodada, tipo=tipo, numero=int(numero))


def _boa(peca: str, servicos: Servicos) -> bool:
    caminho = f"{CARTOES}/{peca}_respostas.json"
    if not servicos.arquivos.existe(caminho):
        return False
    respostas = servicos.arquivos.ler_json(caminho, RespostasCartao)
    return respostas.veredito_ficha == "aprovada" and respostas.veredito_peca == "aprovada"


def pecas_base(rodada: str, servicos: Servicos) -> list[RefPeca]:
    """As peças que recebem cópia: as boas na rodada rNN; no ensaio, as três."""
    Congelamento(servicos.arquivos, servicos.registro, servicos.relogio).rodada(rodada)
    lidas = servicos.arquivos.listar("saida/rascunhos", f"{rodada}_*_v1.md")
    ids = sorted(c.removeprefix("saida/rascunhos/").removesuffix("_v1.md") for c in lidas)
    if not rodada.startswith("e"):
        ids = [p for p in ids if _boa(p, servicos)]
    return [_ref(rodada, p) for p in ids]


def material(ref: RefPeca, servicos: Servicos) -> Material:
    arquivos = servicos.arquivos
    config: Configuracao = servicos.config.geral
    tabela = arquivos.ler_json("dados/normas/tabela_normas.json", TabelaNormas)
    catalogo = next(
        t for t in arquivos.ler_json(CATALOGO, CatalogoTipos).tipos if t.nome_curto == ref.tipo
    )
    feriados = arquivos.ler_json("dados/conferencia/feriados_nacionais.json", FeriadosNacionais)
    peca = ref.com_versao(1)
    return Material(
        peca=ref.id,
        tipo=ref.tipo,
        rascunho=arquivos.ler_texto(f"saida/rascunhos/{peca.nome_versao}.md"),
        extracao=arquivos.ler_json(
            f"saida/conferencias/{peca.nome_versao}_extracao.json", Extracao
        ),
        ficha=arquivos.ler_json(f"saida/fichas/{ref.id}.json", Ficha).root,
        montada=arquivos.ler_json(
            f"{estruturas.PASTA}/{ref.tipo}_estrutura.json", EstruturaMontada
        ),
        tabela=tabela,
        trecho=estruturas.trecho_da_tabela(tabela, ref.tipo, config.trecho.teto_tokens),  # type: ignore[arg-type]
        termos=arquivos.ler_json("dados/conferencia/termos_inequivocos.json", TermosInequivocos),
        listas=arquivos.ler_json("dados/ficticios/listas_ficticias.json", ListasFicticias),
        config=config,
        catalogo=catalogo,
        erros=arquivos.ler_json(ERROS, CatalogoErros),
        feriados=[f.data for f in feriados.feriados],
        perfis={
            catalogo.perfil: arquivos.ler_json(
                f"dados/estruturas/perfis/{catalogo.perfil}.json", Perfil
            )
        },
    )


def nome_da_copia(peca: str, vaga: int = 1, tentativa: int = 1) -> str:
    return f"{peca}_erro{vaga}_{tentativa}"


def gravar_copias(rodada: str, servicos: Servicos) -> list[str]:
    """Grava as cópias por programa que ainda não existem; não refaz as que existem."""
    arquivos = servicos.arquivos
    semente = Congelamento(arquivos, servicos.registro, servicos.relogio).rodada(rodada).semente
    pecas = pecas_base(rodada, servicos)
    gravadas: list[str] = []
    for tipo in sorted({p.tipo for p in pecas}):
        materiais = {p.id: material(p, servicos) for p in pecas if p.tipo == tipo}
        erros = next(iter(materiais.values())).erros.erros
        regras: list[str] = [
            e.tipo_erro for e in erros if e.origem == "programa_regra" and tipo in e.tipos
        ]
        viaveis = {
            p: [e for e in regras if gerar(e, m, random.Random(0)) is not None]
            for p, m in materiais.items()
        }
        com_par = {p for p, m in materiais.items() if tem_par(m)}
        plano = sortear(tipo, semente, list(materiais), com_par, viaveis, regras)
        for peca, tipo_erro in plano.items():
            nome = nome_da_copia(peca)
            if arquivos.existe(f"{PASTA}/{nome}.md"):
                continue
            m = materiais[peca]
            copia = gerar(tipo_erro, m, random.Random(f"{semente}:{peca}:{tipo_erro}"))
            if copia is None:
                raise ErroErros(f"{peca}: o erro {tipo_erro} sorteado não coube na peça")
            entrada = next(e for e in erros if e.tipo_erro == tipo_erro)
            arquivos.gravar_texto(f"{PASTA}/{nome}.md", copia.texto)
            arquivos.gravar_json(
                f"{PASTA}/{nome}_gabarito.json",
                Gabarito(
                    copia=nome,
                    original=f"{peca}_v1",
                    origem=entrada.origem,
                    tipo_erro=entrada.tipo_erro,
                    sutil=False,
                    item_principal=entrada.item_principal,
                    itens_aceitos=list(entrada.itens_aceitos),
                    criador="programa",
                    verificador=None,
                    item_apontado_pelo_verificador=None,
                    amostra=None,
                ),
            )
            gravadas.append(nome)
    return gravadas


# ---------------------------------------------------------------------------
# Cópias do Opus e verificação do Sonnet (brief 021)
# ---------------------------------------------------------------------------
#
# Vagas 2 em diante de cada peça base, pelo plano B (ARQUITETURA §5.12.6): 4 por peça
# boa com 20 ou mais, 6 de 14 a 19, nenhuma abaixo de 14 (critério central
# inconclusivo); no ensaio, 1 por peça. Cada tentativa de uma vaga é uma cópia
# `<peça>_erro<k>_<t>`, levada pelo condutor (registro de decisão 002) por quatro
# etapas: o pedido ao Opus e a troca, a extração da cópia pelo Haiku, os itens de
# programa e o Sonnet. O condutor conhece a cópia pela referência `<cópia>_banco`,
# para que os arquivos do banco não se misturem com os do teste dos conferentes (022).
# O comando `erros` grava os pedidos e o sorteio; o `avancar` coleta as respostas.

INSTRUCAO_PLANTAR = "instrucoes/plantar_erro.md"
TITULO_OPUS = "Cópia com erro"
TITULO_SONNET = "Verificação da cópia"
LISTA = "dados/conferencia/lista_conferencia.json"
FORA_DO_VERIFICADOR = ("semelhanca", "marca")
ITENS_DE_PROGRAMA = (*regras.ITENS_DE_REGRAS, "citacao_fora_da_tabela", "dado_real")
SUFIXO_BANCO = "_banco"
TENTATIVAS_POR_TIPO = 2
TIPOS_POR_VAGA = 2  # o tipo sorteado e um tipo de troca (provisório; relatório do 021)
INCONCLUSIVO = "criterio_central_inconclusivo"
FAIXA_MEDIA = "plano_b_faixa_media"
CUSTO_DESCARTADA = "custo_copia_descartada"
SituacaoPlano = Literal["ensaio", "normal", "faixa_media", "inconclusivo"]
SituacaoVaga = Literal["pendente", "aceita", "perdida"]
_COPIA = re.compile(
    r"^(?P<peca>(?P<rodada>[er]\d{2})_(?P<tipo>.+)_(?P<n>\d{3}))_erro(?P<k>\d+)_(?P<t>\d+)$"
)


def secao(texto: str, titulo: str) -> str:
    """O texto de `plantar_erro.md` sob o título `# <titulo>`, até o título seguinte."""
    partes = re.split(r"(?m)^(?=# )", texto)
    for parte in partes:
        if parte.startswith(f"# {titulo}\n"):
            return parte.strip() + "\n"
    raise ErroErros(f"{INSTRUCAO_PLANTAR}: falta o título '# {titulo}'")


def ref_da_peca(rodada: str, peca: str) -> RefPeca:
    return _ref(rodada, peca)


@dataclass(frozen=True, order=True)
class Vaga:
    rodada: str
    peca: str
    tipo: str
    k: int
    tipo_erro: str
    sutil: bool


@dataclass(frozen=True)
class Plano:
    situacao: SituacaoPlano
    pecas_boas: int
    vagas: tuple[Vaga, ...]


def vagas_por_peca(rodada: str, boas: int, config: Configuracao) -> tuple[SituacaoPlano, int]:
    if rodada.startswith("e"):
        return "ensaio", 1
    plano_b = config.plano_b
    if boas >= plano_b.normal_a_partir_de_pecas_boas:
        return "normal", config.volume.copias_opus_por_peca_boa
    if boas < plano_b.inconclusivo_abaixo_de:
        return "inconclusivo", 0
    return "faixa_media", plano_b.copias_opus_por_peca_boa_faixa_media


def _ordem(semente: int, rodada: str, nomes: Sequence[str]) -> dict[str, int]:
    lista = sorted(set(nomes))
    random.Random(f"{semente}:{rodada}:erros_opus").shuffle(lista)
    return {nome: i for i, nome in enumerate(lista)}


def planejar(
    rodada: str,
    semente: int,
    pecas: Sequence[tuple[str, str]],
    aplicaveis: Mapping[str, Sequence[str]],
    config: Configuracao,
) -> Plano:
    """As vagas do Opus: tipos diferentes na mesma peça, equilibrados no conjunto
    (o menos usado primeiro; o empate pela ordem sorteada com a semente), e metade
    sutis, também equilibradas por tipo de erro."""
    situacao, n = vagas_por_peca(rodada, len(pecas), config)
    ordem = _ordem(semente, rodada, [e for lista in aplicaveis.values() for e in lista])
    fracao = Fraction(str(config.volume.fracao_copias_opus_sutis))
    usos: Counter[str] = Counter()
    sutis: Counter[str] = Counter()
    vagas: list[Vaga] = []
    total = 0
    # O menos usado no conjunto vem primeiro, e as peças vão alternadas por tipo de peça,
    # para que os erros que cabem em poucos tipos não fiquem para o fim.
    por_tipo: dict[str, list[tuple[str, str]]] = {}
    for peca, tipo in sorted(pecas):
        por_tipo.setdefault(tipo, []).append((peca, tipo))
    grupos = itertools.zip_longest(*(por_tipo[t] for t in sorted(por_tipo)))
    alternadas = [par for grupo in grupos for par in grupo if par is not None]
    for peca, tipo in alternadas:
        escolhidos: list[str] = []
        for _ in range(n):
            opcoes = [e for e in aplicaveis[tipo] if e not in escolhidos]
            if not opcoes:
                break
            escolhido = min(opcoes, key=lambda e: (usos[e], ordem[e]))
            usos[escolhido] += 1
            escolhidos.append(escolhido)
        antes = int(total * fracao)
        total += len(escolhidos)
        quantos = int(total * fracao) - antes
        saldo = {e: 2 * sutis[e] - (usos[e] - 1) for e in escolhidos}
        marcados = set(sorted(escolhidos, key=lambda e: (saldo[e], ordem[e]))[:quantos])
        for k, escolhido in enumerate(escolhidos, start=2):
            sutil = escolhido in marcados
            sutis[escolhido] += sutil
            vagas.append(Vaga(rodada, peca, tipo, k, escolhido, sutil))
    return Plano(situacao, len(pecas), tuple(vagas))


def aplicaveis_do_opus(servicos: Servicos) -> dict[str, list[str]]:
    erros = servicos.arquivos.ler_json(ERROS, CatalogoErros).erros
    tipos = {t for e in erros for t in e.tipos}
    return {t: [e.tipo_erro for e in erros if e.origem == "opus" and t in e.tipos] for t in tipos}


def plano_da_rodada(rodada: str, servicos: Servicos) -> Plano:
    semente = (
        Congelamento(servicos.arquivos, servicos.registro, servicos.relogio).rodada(rodada).semente
    )
    pecas = [(p.id, p.tipo) for p in pecas_base(rodada, servicos)]
    return planejar(rodada, semente, pecas, aplicaveis_do_opus(servicos), servicos.config.geral)


# --- a troca feita pelo programa ------------------------------------------------


@dataclass(frozen=True)
class Troca:
    texto: str | None
    falha: str | None


def trocar(original: str, trecho_original: str, trecho_novo: str, fracao_maxima: float) -> Troca:
    """Conferência de programa da troca (ARQUITETURA §5.7, item 1)."""
    if not trecho_original or original.count(trecho_original) != 1:
        return Troca(None, "o trecho original não aparece exatamente uma vez na peça")
    if trecho_original == trecho_novo:
        return Troca(None, "o trecho novo é igual ao original")
    inicio = original.index(trecho_original)
    fim = inicio + len(trecho_original)
    texto = original[:inicio] + trecho_novo + original[fim:]
    if texto[:inicio] != original[:inicio] or texto[inicio + len(trecho_novo) :] != original[fim:]:
        return Troca(None, "o resto da peça não ficou idêntico")
    linhas = difflib.SequenceMatcher(
        None, original.splitlines(), texto.splitlines(), autojunk=False
    ).get_opcodes()
    if sum(op != "equal" for op, *_ in linhas) > 1:
        return Troca(None, "a troca muda mais de uma região")
    comeco = 0
    while comeco < min(len(original), len(texto)) and original[comeco] == texto[comeco]:
        comeco += 1
    final = 0
    while (
        final < min(len(original), len(texto)) - comeco
        and original[len(original) - 1 - final] == texto[len(texto) - 1 - final]
    ):
        final += 1
    regiao = max(len(original) - comeco - final, len(texto) - comeco - final)
    if Fraction(regiao, len(original)) > Fraction(str(fracao_maxima)):
        return Troca(None, "a região trocada passa do limite do texto")
    return Troca(texto, None)


# --- nomes e arquivos do banco ------------------------------------------------


def caminho_copia(nome: str) -> str:
    return f"{PASTA}/{nome}.md"


def caminho_gabarito(nome: str) -> str:
    return f"{PASTA}/{nome}_gabarito.json"


def caminho_descartada(nome: str) -> str:
    return f"{PASTA}/{nome}_descartada.json"


def caminho_troca_de_tipo(vaga: Vaga) -> str:
    return f"{PASTA}/{vaga.peca}_erro{vaga.k}_troca_de_tipo.txt"


def caminho_amostras(rodada: str) -> str:
    return f"{PASTA}/{rodada}_amostras.json"


def ref_banco(nome: str) -> RefPeca:
    achado = _COPIA.match(nome)
    if achado is None:
        raise ErroErros(f"nome de cópia fora do padrão: {nome}")
    return RefPeca(
        rodada=achado["rodada"],
        tipo=achado["tipo"],
        numero=int(achado["n"]),
        versao=1,
        copia=f"{nome}{SUFIXO_BANCO}",
    )


def nome_do_ref(ref: RefPeca) -> str:
    if ref.copia is None or not ref.copia.endswith(SUFIXO_BANCO):
        raise ErroErros(f"{ref.id} não é cópia do banco")
    return ref.copia.removesuffix(SUFIXO_BANCO)


def _original(nome: str) -> str:
    achado = _COPIA.match(nome)
    assert achado is not None
    return achado["peca"]


def _entrada(tipo_erro: str, servicos: Servicos) -> TipoErroCatalogo:
    for entrada in servicos.arquivos.ler_json(ERROS, CatalogoErros).erros:
        if entrada.tipo_erro == tipo_erro:
            return entrada
    raise ErroErros(f"tipo de erro fora do catálogo: {tipo_erro}")


def _pedido_do_erro(nome: str, servicos: Servicos) -> dict[str, Any]:
    """O erro pedido ao Opus, lido do próprio pedido (`estrutura`)."""
    caminho = (
        f"{estado.PEDIDOS}/{nome_do_pedido(f'{nome}{SUFIXO_BANCO}', 1, 'copia_com_erro', 1)}.json"
    )
    pedido = servicos.arquivos.ler_json(caminho, Pedido)
    dados: dict[str, Any] = json.loads(
        next(p.texto for p in pedido.partes if p.nome == "estrutura")
    )
    return dados


def _custo(ref: RefPeca, servicos: Servicos) -> tuple[int, int]:
    chamadas = [c for c in servicos.registro.chamadas() if c.peca == ref.id]
    return sum(c.custo_milionesimos for c in chamadas), len(chamadas)


def descartar(
    nome: str,
    conferencia: Literal["programa", "verificador"],
    servicos: Servicos,
    motivo: Literal["outro_problema", "outro_item", "nao_viu_erro"] | None = None,
    item: str | None = None,
    outro_problema: bool = False,
) -> None:
    """Grava `<cópia>_descartada.json` e marca à parte, no registro, o custo da cópia."""
    erro = _pedido_do_erro(nome, servicos)
    entrada = _entrada(erro["tipo_erro"], servicos)
    servicos.arquivos.gravar_json(
        caminho_descartada(nome),
        Descartada.model_validate_json(
            json.dumps(
                {
                    "copia": nome,
                    "original": f"{_original(nome)}_v1",
                    "tipo_erro": entrada.tipo_erro,
                    "sutil": bool(erro["sutil"]),
                    "criador": "opus",
                    "conferencia_que_falhou": conferencia,
                    "item_apontado_pelo_verificador": item,
                    "outro_problema": outro_problema,
                    "motivo": motivo,
                    "amostra": None,
                }
            )
        ),
    )
    ref = ref_banco(nome)
    custo, quantas = _custo(ref, servicos)
    servicos.registro.ocorrencia(
        Ocorrencia(
            tipo="contexto",
            causa=CUSTO_DESCARTADA,
            inicio=servicos.relogio(),
            fim=None,
            peca=nome,
            rodada=ref.rodada,
            detalhe=f"{custo} milionésimos de centavo de dólar em {quantas} chamada(s); "
            f"conferência {conferencia}, motivo {motivo or 'vazio'}",
        )
    )


def itens_do_verificador(tipo: str, servicos: Servicos) -> list[dict[str, str]]:
    catalogo = next(
        t for t in servicos.arquivos.ler_json(CATALOGO, CatalogoTipos).tipos if t.nome_curto == tipo
    )
    perguntas = {
        i.item: i.pergunta for i in servicos.arquivos.ler_json(LISTA, ListaConferencia).itens
    }
    return [
        {"item": i, "pergunta": perguntas.get(i, "")}
        for i in catalogo.itens_conferencia
        if i not in FORA_DO_VERIFICADOR
    ]


def itens_de_programa_da_copia(
    m: Material, texto: str, extracao: Extracao, servicos: Servicos
) -> ResultadoProgramas:
    """Os itens de programa do Anexo B.1 (menos `semelhanca`) rodados na cópia."""
    pedidos = [i for i in m.catalogo.itens_conferencia if i in regras.ITENS_DE_REGRAS]
    de_regras = regras.conferir(
        texto, extracao, m.ficha, m.montada, perfil(m), m.termos, m.feriados, m.config, pedidos
    )
    por_item = {r.item: r for r in de_regras}
    cit = citacoes.conferir(texto, m.tabela)
    por_item["citacao_fora_da_tabela"] = cit.item
    if "dado_real" in m.catalogo.itens_conferencia:
        por_item["dado_real"] = regras.dado_real(
            texto, m.ficha, m.montada, servicos.arquivos, m.config
        )
    return ResultadoProgramas(
        itens=[por_item[i] for i in m.catalogo.itens_conferencia if i in por_item],
        alertas=list(cit.alertas),
        citacoes_resolvidas=list(cit.resolvidas),
        citacoes_nao_resolvidas=list(cit.nao_resolvidas),
    )


def motivo_do_descarte(
    resposta: RespostaVerificacao, aceitos: Sequence[str]
) -> Literal["outro_problema", "outro_item", "nao_viu_erro"] | None:
    """ARQUITETURA §5.7: sem item apontado, sempre `nao_viu_erro`; None = a cópia passa."""
    if resposta.item_apontado is None:
        return "nao_viu_erro"
    if resposta.outro_problema:
        return "outro_problema"
    if resposta.item_apontado not in aceitos:
        return "outro_item"
    return None


# --- as quatro etapas do banco (interface do registro de decisão 002) -----------


def _api(servicos: Servicos) -> Any:
    if servicos.api_claude is None:
        raise estado.ErroServicos(
            "a variável de ambiente ANTHROPIC_API_KEY não está definida: "
            "o passo precisa da API da Claude. Defina a variável e rode de novo."
        )
    return servicos.api_claude


class _EtapaDoBanco:
    nome = ""

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        if peca.copia is None or not peca.copia.endswith(SUFIXO_BANCO):
            return False
        nome = nome_do_ref(peca)
        return not servicos.arquivos.existe(caminho_descartada(nome)) and self._antes(
            nome, servicos
        )

    def _antes(self, nome: str, servicos: Servicos) -> bool:
        return True


class EtapaCopiaOpus(_EtapaDoBanco):
    """O pedido ao Opus e a troca feita pelo programa."""

    nome = "copia_opus"

    def __init__(self, erros: Mapping[str, tuple[str, bool]] | None = None) -> None:
        self.erros = dict(erros or {})  # cópia -> (tipo de erro, sutil), dado pelo comando

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return caminho_copia(nome_do_ref(peca))

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        nome = nome_do_ref(peca)
        if nome not in self.erros:
            raise ErroErros(f"{nome}: o pedido ao Opus é gravado pelo comando erros")
        tipo_erro, sutil = self.erros[nome]
        entrada = _entrada(tipo_erro, servicos)
        arquivos = servicos.arquivos
        erro = {"tipo_erro": tipo_erro, "descricao": entrada.descricao, "sutil": sutil}
        caminho: str = _api(servicos).gravar_pedido(
            rodada=peca.rodada,
            peca=peca.id,
            versao=peca.versao,
            tarefa="copia_com_erro",
            partes={
                "instrucoes": secao(arquivos.ler_texto(INSTRUCAO_PLANTAR), TITULO_OPUS),
                "estrutura": json.dumps(erro, ensure_ascii=False),
                "conteudo": arquivos.ler_texto(f"saida/rascunhos/{_original(nome)}_v1.md"),
            },
            modelo_resposta=RespostaCopiaOpus,
        )
        return caminho

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        if not isinstance(resposta, Resposta):
            raise ErroErros(f"{peca.id}: resposta do Opus fora do esperado")
        try:
            lida = RespostaCopiaOpus.model_validate_json(resposta.conteudo)
        except ValidationError:
            return estado.FORA_DO_FORMATO
        nome = nome_do_ref(peca)
        arquivos = servicos.arquivos
        original = arquivos.ler_texto(f"saida/rascunhos/{_original(nome)}_v1.md")
        fracao = servicos.config.geral.erros.fracao_maxima_regiao
        troca = trocar(original, lida.trecho_original, lida.trecho_novo, fracao)
        if troca.texto is None:
            descartar(nome, "programa", servicos)
            return None
        erro = _pedido_do_erro(nome, servicos)
        arquivos.gravar_json(
            f"{PASTA}/{nome}_troca.json",
            CopiaComErro.model_validate_json(
                json.dumps(
                    {
                        "copia": nome,
                        "original": f"{_original(nome)}_v1",
                        "trecho_original": lida.trecho_original,
                        "trecho_novo": lida.trecho_novo,
                        "tipo_erro": erro["tipo_erro"],
                        "sutil": bool(erro["sutil"]),
                        "criador": "opus",
                    }
                )
            ),
        )
        arquivos.gravar_texto(caminho_copia(nome), troca.texto)
        return None


class EtapaExtracaoDaCopia(_EtapaDoBanco):
    """A extração da cópia pelo Haiku, com a instrução e a tarefa da extração (017)."""

    nome = "extracao_banco"

    def _antes(self, nome: str, servicos: Servicos) -> bool:
        return servicos.arquivos.existe(caminho_copia(nome))

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return f"{PASTA}/{nome_do_ref(peca)}_extracao.json"

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        arquivos = servicos.arquivos
        naturezas = ", ".join(extracao_mod.NATUREZAS[peca.tipo])
        caminho: str = _api(servicos).gravar_pedido(
            rodada=peca.rodada,
            peca=peca.id,
            versao=peca.versao,
            tarefa="extracao",
            partes={
                "instrucoes": arquivos.ler_texto(extracao_mod.INSTRUCAO),
                "estrutura": f"Naturezas de pedido do tipo: {naturezas}.",
                "conteudo": arquivos.ler_texto(caminho_copia(nome_do_ref(peca))),
            },
            modelo_resposta=Extracao,
        )
        return caminho

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        if not isinstance(resposta, Resposta):
            raise ErroErros(f"{peca.id}: resposta da extração fora do esperado")
        try:
            lida = Extracao.model_validate_json(resposta.conteudo)
        except ValidationError:
            return estado.FORA_DO_FORMATO
        servicos.arquivos.gravar_json(self.arquivo_resultado(peca), lida)
        return None


class EtapaProgramasDaCopia(_EtapaDoBanco):
    """Os itens de programa na cópia: reprovar item fora dos aceitos descarta."""

    nome = "programas_banco"

    def _antes(self, nome: str, servicos: Servicos) -> bool:
        return servicos.arquivos.existe(f"{PASTA}/{nome}_extracao.json")

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return f"{PASTA}/{nome_do_ref(peca)}_programas.json"

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        nome = nome_do_ref(peca)
        arquivos = servicos.arquivos
        m = material(_ref(peca.rodada, _original(nome)), servicos)
        lida = arquivos.ler_json(f"{PASTA}/{nome}_extracao.json", Extracao)
        resultado = itens_de_programa_da_copia(
            m, arquivos.ler_texto(caminho_copia(nome)), lida, servicos
        )
        arquivos.gravar_json(self.arquivo_resultado(peca), resultado)
        aceitos = _entrada(_pedido_do_erro(nome, servicos)["tipo_erro"], servicos).itens_aceitos
        if any(r.resposta == "nao_passa" and r.item not in aceitos for r in resultado.itens):
            descartar(nome, "programa", servicos, outro_problema=True)
        return None

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        raise ErroErros("a conferência de programa da cópia não faz pedido")


class EtapaVerificacao(_EtapaDoBanco):
    """O Sonnet, sem saber o erro pedido, aponta o item; o programa decide."""

    nome = "verificacao"

    def _antes(self, nome: str, servicos: Servicos) -> bool:
        return servicos.arquivos.existe(f"{PASTA}/{nome}_programas.json")

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return caminho_gabarito(nome_do_ref(peca))

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        nome = nome_do_ref(peca)
        arquivos = servicos.arquivos
        textos = {
            "original": arquivos.ler_texto(f"saida/rascunhos/{_original(nome)}_v1.md"),
            "copia": arquivos.ler_texto(caminho_copia(nome)),
        }
        caminho: str = _api(servicos).gravar_pedido(
            rodada=peca.rodada,
            peca=peca.id,
            versao=peca.versao,
            tarefa="verificacao_copia",
            partes={
                "instrucoes": secao(arquivos.ler_texto(INSTRUCAO_PLANTAR), TITULO_SONNET),
                "estrutura": json.dumps(
                    {"itens": itens_do_verificador(peca.tipo, servicos)}, ensure_ascii=False
                ),
                "conteudo": json.dumps(textos, ensure_ascii=False),
            },
            modelo_resposta=RespostaVerificacao,
        )
        return caminho

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        if not isinstance(resposta, Resposta):
            raise ErroErros(f"{peca.id}: resposta do Sonnet fora do esperado")
        try:
            lida = RespostaVerificacao.model_validate_json(resposta.conteudo)
        except ValidationError:
            return estado.FORA_DO_FORMATO
        nome = nome_do_ref(peca)
        erro = _pedido_do_erro(nome, servicos)
        entrada = _entrada(erro["tipo_erro"], servicos)
        motivo = motivo_do_descarte(lida, entrada.itens_aceitos)
        if motivo is not None:
            descartar(
                nome, "verificador", servicos, motivo, lida.item_apontado, lida.outro_problema
            )
            return None
        servicos.arquivos.gravar_json(
            caminho_gabarito(nome),
            Gabarito(
                copia=nome,
                original=f"{_original(nome)}_v1",
                origem=entrada.origem,
                tipo_erro=entrada.tipo_erro,
                sutil=bool(erro["sutil"]),
                item_principal=entrada.item_principal,
                itens_aceitos=list(entrada.itens_aceitos),
                criador="opus",
                verificador=resposta.modelo,
                item_apontado_pelo_verificador=lida.item_apontado,
                amostra=None,
            ),
        )
        return None


def etapas_do_banco(erros: Mapping[str, tuple[str, bool]] | None = None) -> list[Any]:
    return [
        EtapaCopiaOpus(erros),
        EtapaExtracaoDaCopia(),
        EtapaProgramasDaCopia(),
        EtapaVerificacao(),
    ]


# --- vagas, comando e coleta ------------------------------------------------------


@dataclass(frozen=True)
class EstadoVaga:
    vaga: Vaga
    situacao: SituacaoVaga
    tentativa: int
    tipo_erro: str | None
    trocou_de_tipo: bool


def _tipo_de_troca(vaga: Vaga, plano: Plano, servicos: Servicos) -> str | None:
    """Outro tipo de erro para a vaga: fora dos da peça, o menos usado no conjunto."""
    arquivos = servicos.arquivos
    caminho = caminho_troca_de_tipo(vaga)
    if arquivos.existe(caminho):
        return arquivos.ler_texto(caminho).strip() or None
    da_peca = [v for v in plano.vagas if v.peca == vaga.peca]
    usados = {v.tipo_erro for v in da_peca}
    usos = Counter(v.tipo_erro for v in plano.vagas)
    for outra in da_peca:
        if arquivos.existe(caminho_troca_de_tipo(outra)):
            trocado = arquivos.ler_texto(caminho_troca_de_tipo(outra)).strip()
            if trocado:
                usados.add(trocado)
                usos[trocado] += 1
    aplicaveis = aplicaveis_do_opus(servicos)[vaga.tipo]
    semente = (
        Congelamento(arquivos, servicos.registro, servicos.relogio).rodada(vaga.rodada).semente
    )
    ordem = _ordem(semente, vaga.rodada, aplicaveis)
    opcoes = [e for e in aplicaveis if e not in usados]
    escolhido = min(opcoes, key=lambda e: (usos[e], ordem[e])) if opcoes else ""
    arquivos.gravar_texto(caminho, escolhido + "\n")
    return escolhido or None


def estado_da_vaga(vaga: Vaga, plano: Plano, servicos: Servicos) -> EstadoVaga:
    """O ponto da vaga, pelos arquivos. A cópia que o condutor encerrou por formato
    (duas respostas fora do formato) é descartada aqui, com o motivo vazio."""
    arquivos = servicos.arquivos
    tipo_erro: str | None = vaga.tipo_erro
    for t in range(1, TENTATIVAS_POR_TIPO * TIPOS_POR_VAGA + 1):
        trocou = t > TENTATIVAS_POR_TIPO
        if trocou and t == TENTATIVAS_POR_TIPO + 1:
            tipo_erro = _tipo_de_troca(vaga, plano, servicos)
            if tipo_erro is None:
                return EstadoVaga(vaga, "perdida", t, None, True)
        nome = nome_da_copia(vaga.peca, vaga.k, t)
        if arquivos.existe(caminho_gabarito(nome)):
            return EstadoVaga(vaga, "aceita", t, tipo_erro, trocou)
        if arquivos.existe(caminho_descartada(nome)):
            continue
        if estado.destino(ref_banco(nome), arquivos) is not None:
            conferencia: Literal["programa", "verificador"] = (
                "verificador" if arquivos.existe(f"{PASTA}/{nome}_programas.json") else "programa"
            )
            descartar(nome, conferencia, servicos)
            continue
        return EstadoVaga(vaga, "pendente", t, tipo_erro, trocou)
    return EstadoVaga(vaga, "perdida", TENTATIVAS_POR_TIPO * TIPOS_POR_VAGA, tipo_erro, True)


@dataclass
class ResumoBanco:
    situacao: SituacaoPlano
    pecas_boas: int
    vagas: int = 0
    aceitas: int = 0
    perdidas: int = 0
    pendentes: int = 0
    trocaram_de_tipo: int = 0
    descartadas: int = 0
    pedidos_gravados: int = 0
    parada: str | None = None
    amostras: str | None = None


def _estados(plano: Plano, servicos: Servicos) -> list[EstadoVaga]:
    return [estado_da_vaga(v, plano, servicos) for v in plano.vagas]


def resumo_do_banco(rodada: str, servicos: Servicos) -> ResumoBanco:
    plano = plano_da_rodada(rodada, servicos)
    estados = _estados(plano, servicos)
    descartadas = [
        c
        for v in plano.vagas
        for c in servicos.arquivos.listar(PASTA, f"{v.peca}_erro{v.k}_*_descartada.json")
    ]
    return ResumoBanco(
        situacao=plano.situacao,
        pecas_boas=plano.pecas_boas,
        vagas=len(plano.vagas),
        aceitas=sum(e.situacao == "aceita" for e in estados),
        perdidas=sum(e.situacao == "perdida" for e in estados),
        pendentes=sum(e.situacao == "pendente" for e in estados),
        trocaram_de_tipo=sum(e.trocou_de_tipo for e in estados),
        descartadas=len(descartadas),
        amostras=caminho_amostras(rodada)
        if servicos.arquivos.existe(caminho_amostras(rodada))
        else None,
    )


def _marcar_plano_b(plano: Plano, rodada: str, servicos: Servicos) -> None:
    causa = {"inconclusivo": INCONCLUSIVO, "faixa_media": FAIXA_MEDIA}.get(plano.situacao)
    if causa is None:
        return
    if any(o.causa == causa and o.rodada == rodada for o in servicos.registro.ocorrencias()):
        return
    detalhe = (
        f"{plano.pecas_boas} peça(s) boa(s): critério central inconclusivo, nenhuma cópia do Opus"
        if causa == INCONCLUSIVO
        else f"{plano.pecas_boas} peça(s) boa(s): 6 cópias do Opus por peça boa; cópias da "
        "mesma original não são independentes entre si"
    )
    servicos.registro.ocorrencia(
        Ocorrencia(
            tipo="contexto",
            causa=causa,
            inicio=servicos.relogio(),
            fim=None,
            peca=None,
            rodada=rodada,
            detalhe=detalhe,
        )
    )


def gravar_banco(rodada: str, servicos: Servicos) -> ResumoBanco:
    """Grava os pedidos ao Opus das vagas que esperam uma cópia nova e, com todas as
    vagas resolvidas, o sorteio das amostras. Não envia nada: a coleta é do `avancar`."""
    plano = plano_da_rodada(rodada, servicos)
    _marcar_plano_b(plano, rodada, servicos)
    congelamento = Congelamento(servicos.arquivos, servicos.registro, servicos.relogio)
    if congelamento.conferir(rodada).parar:
        resumo = resumo_do_banco(rodada, servicos)
        resumo.parada = "congelamento"
        return resumo
    gravados = 0
    for situacao in _estados(plano, servicos):
        if situacao.situacao != "pendente" or situacao.tipo_erro is None:
            continue
        nome = nome_da_copia(situacao.vaga.peca, situacao.vaga.k, situacao.tentativa)
        ref = ref_banco(nome)
        etapas = etapas_do_banco({nome: (situacao.tipo_erro, situacao.vaga.sutil)})
        atual = estado.ponto(ref, etapas, servicos)
        if atual.acao == "pedir" and atual.etapa == EtapaCopiaOpus.nome:
            caminho = etapas[0].pedir(ref, servicos)
            estado.registrar_pedido(ref, EtapaCopiaOpus.nome, caminho, servicos.arquivos)
            gravados += 1
    gravar_amostras(rodada, servicos)
    resumo = resumo_do_banco(rodada, servicos)
    resumo.pedidos_gravados = gravados
    return resumo


def refs_do_banco(servicos: Servicos) -> list[RefPeca]:
    """As cópias do banco cujo pedido ao Opus foi gravado pelo comando `erros`."""
    marcadores = servicos.arquivos.listar(
        estado.CONDUCAO, f"*{SUFIXO_BANCO}_v1_{EtapaCopiaOpus.nome}_t1.txt"
    )
    nomes = [
        m.removeprefix(f"{estado.CONDUCAO}/").removesuffix(
            f"{SUFIXO_BANCO}_v1_{EtapaCopiaOpus.nome}_t1.txt"
        )
        for m in marcadores
    ]
    return sorted(ref_banco(n) for n in nomes)


def coletar_banco(servicos: Servicos) -> estado.ResumoAvanco:
    """A parte do `avancar` que leva as cópias do banco pelas quatro etapas."""
    refs = refs_do_banco(servicos)
    if not refs:
        return estado.ResumoAvanco()
    return estado.avancar(etapas_do_banco(), servicos, refs)


# --- as amostras ------------------------------------------------------------------


def sortear_amostras(
    rodada: str,
    semente: int,
    aceitas: Sequence[str],
    nao_viu: Sequence[str],
    config: ConfigAmostras,
) -> tuple[list[str], list[str]]:
    """Na rodada, 10 cópias aceitas e até 5 descartadas por `nao_viu_erro`; no ensaio,
    as aceitas até 3 e até 1 descartada. Igual com a mesma semente."""
    rng = random.Random(f"{semente}:{rodada}:amostras")
    if rodada.startswith("e"):
        limite_copias, limite_descartadas = (
            config.ensaio_copias_aceitas_maximo,
            config.ensaio_descartadas_maximo,
        )
    else:
        limite_copias, limite_descartadas = config.copias_aceitas, config.descartadas_nao_viu_erro
    copias = sorted(aceitas)
    if len(copias) > limite_copias:
        copias = sorted(rng.sample(copias, limite_copias))
    descartadas = sorted(nao_viu)
    if len(descartadas) > limite_descartadas:
        descartadas = sorted(rng.sample(descartadas, limite_descartadas))
    return copias, descartadas


def gravar_amostras(rodada: str, servicos: Servicos) -> str | None:
    """Grava `saida/erros/<rodada>_amostras.json` uma vez, só com todas as vagas
    resolvidas. Devolve o caminho gravado, ou None."""
    arquivos = servicos.arquivos
    destino = caminho_amostras(rodada)
    if arquivos.existe(destino):
        return None
    plano = plano_da_rodada(rodada, servicos)
    if plano.situacao == "inconclusivo" or not plano.vagas:
        return None
    if any(e.situacao == "pendente" for e in _estados(plano, servicos)):
        return None
    aceitas, nao_viu = [], []
    for vaga in plano.vagas:
        for t in range(1, TENTATIVAS_POR_TIPO * TIPOS_POR_VAGA + 1):
            nome = nome_da_copia(vaga.peca, vaga.k, t)
            if arquivos.existe(caminho_gabarito(nome)):
                aceitas.append(nome)
            elif arquivos.existe(caminho_descartada(nome)):
                if arquivos.ler_json(caminho_descartada(nome), Descartada).motivo == "nao_viu_erro":
                    nao_viu.append(nome)
    semente = Congelamento(arquivos, servicos.registro, servicos.relogio).rodada(rodada).semente
    copias, descartadas = sortear_amostras(
        rodada, semente, aceitas, nao_viu, servicos.config.geral.amostras
    )
    arquivos.gravar_json(
        destino,
        Amostras(
            rodada=rodada, copias=copias, descartadas=descartadas, sorteado_em=servicos.relogio()
        ),
    )
    return destino
