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
import itertools
import random
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from fabrica import estruturas, matriz
from fabrica.comum import normalizacao as norm
from fabrica.comum.congelamento import Congelamento
from fabrica.comum.formatos import (
    CatalogoErros,
    CatalogoTipos,
    Configuracao,
    DataExtraida,
    Dispositivo,
    EstruturaMontada,
    Extracao,
    FeriadosNacionais,
    Ficha,
    FichaInicial,
    FichaQualquer,
    Gabarito,
    ListasFicticias,
    Perfil,
    RespostasCartao,
    TabelaNormas,
    TermosInequivocos,
    TipoCatalogo,
)
from fabrica.conferencia import citacoes
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
