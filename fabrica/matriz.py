"""Travas, sorteio das combinações e das datas, combinação do ensaio e dias úteis.

ARQUITETURA §2.2 (travas), §5.4 (sorteio), §1.4 (ensaio) e Anexos A.5 e A.6.
As travas são listas de condições simples avaliadas por uma função curta: nada
de texto executado como código nem linguagem própria. A contagem de dias úteis
(`termo_final`) existe só aqui; `regras.py` (brief 012) a usa daqui.
"""

from __future__ import annotations

import datetime
import random
from collections import Counter
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Final, Literal

from fabrica.comum.formatos import (
    CasaMatriz,
    Categoria,
    Complexidade,
    Condicao,
    ConfigMatriz,
    Estilo,
    FichaEmbargos,
    FichaInicial,
    FichaManifestacao,
    FichaQualquer,
    Matriz,
    MotivoDevolucao,
    NomeCurto,
    Papel,
    PedidoAR,
    Rito,
    RotuloTipo,
    TipoDecisao,
    TipoDefeito,
    Trava,
    Travas,
    VisaoTravas,
)

VOLTA: Final = "volta para a preparação"
Situacao = Literal["ok", "volta para a preparação"]

ROTULO_DO_TIPO: dict[NomeCurto, RotuloTipo] = {
    "peticao_inicial_jec": "Petição Inicial em Juizado Especial Cível",
    "embargos_declaracao": "Embargos de Declaração",
    "manifestacao_ar_negativo": "Manifestação sobre Aviso de Recebimento Negativo",
}
RITO_FIXO: dict[NomeCurto, Rito] = {
    "peticao_inicial_jec": "juizado_especial_civel",
    "embargos_declaracao": "procedimento_comum",
}
# Parte com prazo em dobro (art. 183 do CPC): a matriz nunca a sorteia (Anexo A.3).
PRAZO_EM_DOBRO: frozenset[str] = frozenset({"pessoa_juridica_direito_publico"})
# Campos da visão que só a ficha pronta preenche: na combinação ficam pendentes,
# e as travas que os exigem são conferidas por `fichas.py` sobre a ficha.
CAMPOS_DA_FICHA: frozenset[str] = frozenset(
    {
        "valor_causa_centavos",
        "alcada_centavos",
        "defeito.ancora.argumento_id",
        "defeito.trecho_mencao",
        "novo_endereco",
        "meio_nova_diligencia",
    }
)
CAMPOS_DA_VISAO: frozenset[str] = frozenset(
    (campo.alias or nome) for nome, campo in VisaoTravas.model_fields.items()
)
PRAZO_EMBARGOS = 5  # art. 1.023 do CPC
PRAZO_SEM_FIXACAO = 5  # art. 218, § 3º, do CPC
ALCADA_EM_SALARIOS = 40  # art. 3º, I, da Lei 9.099/1995
ANO_DO_MVP = 2026
EIXOS_OBRIGATORIOS = ("complexidade", "estilo")


class ErroMatriz(Exception):
    """Dado de matriz ou de trava fora do formato, ou campo desconhecido."""


# ---------------------------------------------------------------------------
# Travas
# ---------------------------------------------------------------------------


def _campos(visao: VisaoTravas) -> dict[str, Any]:
    return visao.model_dump(by_alias=True)


def _ler(campos: Mapping[str, Any], campo: str) -> Any:
    if campo not in campos:
        raise ErroMatriz(f"campo desconhecido na visão das travas: {campo}")
    return campos[campo]


def _vazio(valor: Any) -> bool:
    return valor is None or valor == "" or valor == []


def _igual(a: Any, b: Any) -> bool:
    # Booleano não é número: True não é igual a 1.
    return type(a) is type(b) and bool(a == b)


def _numero(valor: Any) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def _vale(condicao: Condicao, campos: Mapping[str, Any]) -> bool:
    atual = _ler(campos, condicao.campo)
    op = condicao.op
    if op == "vazio":
        return _vazio(atual)
    if op == "preenchido":
        return not _vazio(atual)
    # Campo vazio não se compara: só `vazio` e `preenchido` valem sobre ele.
    if _vazio(atual):
        return False
    if condicao.outro_campo is not None:
        alvo = _ler(campos, condicao.outro_campo)
        if _vazio(alvo):
            return False
    else:
        alvo = condicao.valor
    if op == "igual":
        return _igual(atual, alvo)
    if op == "diferente":
        return not _igual(atual, alvo)
    if op in ("na_lista", "fora_da_lista"):
        if not isinstance(alvo, list):
            raise ErroMatriz(f"{condicao.campo}: {op} pede uma lista de valores")
        dentro = any(_igual(atual, item) for item in alvo)
        return dentro if op == "na_lista" else not dentro
    if not (_numero(atual) and _numero(alvo)):
        raise ErroMatriz(f"{condicao.campo}: {op} compara só números")
    return bool(atual > alvo) if op == "maior" else bool(atual < alvo)


def condicao_vale(condicao: Condicao, visao: VisaoTravas) -> bool:
    """Avalia uma condição simples sobre a visão das travas."""
    return _vale(condicao, _campos(visao))


def _dispara(trava: Trava, campos: Mapping[str, Any]) -> bool:
    return all(_vale(condicao, campos) for condicao in trava.condicoes)


def _violadas(
    travas: Iterable[Trava], campos: Mapping[str, Any], pendentes: Collection[str]
) -> list[Trava]:
    violadas: list[Trava] = []
    for trava in travas:
        if trava.efeito == "exige" and trava.campo_exigido in pendentes:
            continue
        if not _dispara(trava, campos):
            continue
        if trava.efeito == "proibe":
            violadas.append(trava)
        elif _vazio(_ler(campos, trava.campo_exigido or "")):
            violadas.append(trava)
    return violadas


def violacoes(
    travas: Iterable[Trava], visao: VisaoTravas, pendentes: Collection[str] = frozenset()
) -> list[Trava]:
    """As travas que a visão viola. `pendentes`: campos que a ficha ainda vai preencher."""
    return _violadas(travas, _campos(visao), pendentes)


def conferir_trava(trava: Trava) -> list[str]:
    """Problemas de escrita de uma trava (vazio quando está certa)."""
    problemas: list[str] = []
    if not trava.condicoes:
        problemas.append("trava sem condição")
    for c in trava.condicoes:
        if c.campo not in CAMPOS_DA_VISAO:
            problemas.append(f"campo desconhecido: {c.campo}")
        if c.outro_campo is not None and c.outro_campo not in CAMPOS_DA_VISAO:
            problemas.append(f"campo desconhecido: {c.outro_campo}")
        if c.op in ("vazio", "preenchido"):
            if c.valor is not None or c.outro_campo is not None:
                problemas.append(f"{c.campo}: {c.op} não leva valor")
            continue
        if c.outro_campo is not None and c.valor is not None:
            problemas.append(f"{c.campo}: valor e outro campo ao mesmo tempo")
            continue
        if c.outro_campo is None and c.valor is None:
            problemas.append(f"{c.campo}: {c.op} pede valor ou outro campo")
            continue
        if c.op in ("na_lista", "fora_da_lista"):
            if not isinstance(c.valor, list):
                problemas.append(f"{c.campo}: {c.op} pede uma lista de valores")
        elif c.op in ("maior", "menor"):
            if c.outro_campo is None and not _numero(c.valor):
                problemas.append(f"{c.campo}: {c.op} compara só números")
        elif isinstance(c.valor, list):
            problemas.append(f"{c.campo}: {c.op} não leva lista")
    if trava.efeito == "exige":
        if trava.campo_exigido is None:
            problemas.append("trava que exige sem campo exigido")
        elif trava.campo_exigido not in CAMPOS_DA_VISAO:
            problemas.append(f"campo exigido desconhecido: {trava.campo_exigido}")
    elif trava.campo_exigido is not None:
        problemas.append("trava que proíbe não tem campo exigido")
    return problemas


# ---------------------------------------------------------------------------
# Visão das travas
# ---------------------------------------------------------------------------


def _visao(**campos: Any) -> VisaoTravas:
    base: dict[str, Any] = dict.fromkeys(VisaoTravas.model_fields)
    base.update(campos)
    return VisaoTravas(**base)


def _texto_endereco(ficha: FichaManifestacao) -> str | None:
    e = ficha.novo_endereco
    if e is None:
        return None
    return f"{e.rua}, {e.numero}, {e.bairro}, {e.cidade}/{e.estado}, CEP {e.cep}"


def visao_da_ficha(ficha: FichaQualquer) -> VisaoTravas:
    """Visão plana do Anexo A.5, tirada da ficha pronta; o que não se aplica fica vazio."""
    autor = next(p for p in ficha.partes if p.papel == "autor")
    reu = next(p for p in ficha.partes if p.papel == "reu")
    valores = {v.id: v.centavos for v in ficha.valores}
    campos: dict[str, Any] = {
        "tipo": ficha.tipo,
        "processo_rito": ficha.processo.rito,
        "materia": ficha.casa_matriz.materia,
        "autor_categoria": autor.categoria,
        "autor_capaz": autor.capaz,
        "autor_preso": autor.preso,
        "reu_categoria": reu.categoria,
        "reu_capaz": reu.capaz,
        "reu_preso": reu.preso,
        "valor_causa_centavos": valores.get(ficha.valor_causa) if ficha.valor_causa else None,
    }
    if isinstance(ficha, FichaInicial):
        campos["materia"] = ficha.materia
        campos["alcada_centavos"] = ALCADA_EM_SALARIOS * ficha.salario_minimo_referencia
    elif isinstance(ficha, FichaEmbargos):
        campos["defeito_tipo"] = ficha.defeito.tipo
        campos["defeito_ancora_argumento_id"] = ficha.defeito.ancora.argumento_id
        campos["defeito_trecho_mencao"] = ficha.defeito.trecho_mencao
    elif isinstance(ficha, FichaManifestacao):
        campos["pedido_ar"] = ficha.pedido_ar
        campos["aviso_recebimento_motivo_devolucao"] = ficha.aviso_recebimento.motivo_devolucao
        campos["novo_endereco"] = _texto_endereco(ficha)
        campos["meio_nova_diligencia"] = ficha.meio_nova_diligencia
        campos["nova_diligencia"] = _nova_diligencia(ficha.pedido_ar)
    return _visao(**campos)


def _nova_diligencia(pedido: PedidoAR | None) -> bool | None:
    if pedido is None:
        return None
    return pedido in ("informar_novo_endereco", "renovar_mesmo_endereco")


@dataclass(frozen=True)
class Combinacao:
    """Uma casa sorteada da matriz, com os campos próprios do tipo."""

    tipo: NomeCurto
    materia: str
    tese: str
    polo: Papel
    complexidade: Complexidade
    estilo: Estilo
    momento: str
    rito: Rito
    categoria_autor: Categoria | None = None
    categoria_reu: Categoria | None = None
    defeito: TipoDefeito | None = None
    tipo_decisao: TipoDecisao | None = None
    motivo_devolucao: MotivoDevolucao | None = None
    pedido_ar: PedidoAR | None = None

    @property
    def rotulo(self) -> RotuloTipo:
        return ROTULO_DO_TIPO[self.tipo]

    def casa(self) -> CasaMatriz:
        return CasaMatriz(
            materia=self.materia,
            tese=self.tese,
            polo=self.polo,
            complexidade=self.complexidade,
            momento=self.momento,
            estilo=self.estilo,
        )


def _capaz_preso(categoria: Categoria | None) -> tuple[bool | None, bool | None]:
    # A matriz só gera pessoa física capaz e solta (Anexo A.1).
    return (True, False) if categoria == "pessoa_fisica" else (None, None)


def visao_da_combinacao(c: Combinacao) -> VisaoTravas:
    """Visão das travas da combinação sorteada; os campos da ficha ficam vazios."""
    autor_capaz, autor_preso = _capaz_preso(c.categoria_autor)
    reu_capaz, reu_preso = _capaz_preso(c.categoria_reu)
    return _visao(
        tipo=c.rotulo,
        processo_rito=c.rito,
        materia=c.materia,
        autor_categoria=c.categoria_autor,
        autor_capaz=autor_capaz,
        autor_preso=autor_preso,
        reu_categoria=c.categoria_reu,
        reu_capaz=reu_capaz,
        reu_preso=reu_preso,
        defeito_tipo=c.defeito,
        pedido_ar=c.pedido_ar,
        aviso_recebimento_motivo_devolucao=c.motivo_devolucao,
        nova_diligencia=_nova_diligencia(c.pedido_ar),
    )


# ---------------------------------------------------------------------------
# Sorteio
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Sorteio:
    situacao: Situacao
    combinacoes: tuple[Combinacao, ...]
    tentativas: int


def gerador(semente: int, tipo: str, uso: str = "matriz") -> random.Random:
    """Gerador próprio e repetível por semente da rodada, tipo e uso."""
    return random.Random(f"{semente}:{tipo}:{uso}")


def _fixos(m: Matriz) -> dict[str, list[str]]:
    fixos: dict[str, list[str]] = {}
    for e in m.eixos_fixos:
        if e.eixo in fixos:
            raise ErroMatriz(f"{m.tipo}: eixo {e.eixo} repetido")
        valores = [c.valor for c in e.contagens for _ in range(c.quantidade)]
        if len(valores) != m.quantidade:
            raise ErroMatriz(
                f"{m.tipo}: eixo {e.eixo} soma {len(valores)}, e a matriz tem {m.quantidade}"
            )
        fixos[e.eixo] = valores
    for eixo in EIXOS_OBRIGATORIOS:
        if eixo not in fixos:
            raise ErroMatriz(f"{m.tipo}: falta o eixo {eixo}")
    if m.tipo not in RITO_FIXO and "rito" not in fixos:
        raise ErroMatriz(f"{m.tipo}: falta o eixo rito")
    if m.tipo == "embargos_declaracao":
        for eixo in ("polo", "defeito", "tipo_decisao"):
            if eixo not in fixos:
                raise ErroMatriz(f"{m.tipo}: falta o eixo {eixo}")
    return fixos


def conferir_matriz(m: Matriz, config: ConfigMatriz) -> list[str]:
    """Problemas da matriz que o sorteio não aceita (vazio quando está certa)."""
    problemas: list[str] = []
    try:
        _fixos(m)
    except ErroMatriz as erro:
        problemas.append(str(erro))
    teto = int(config.fracao_maxima_por_materia * m.quantidade)
    if m.teto_por_materia > teto:
        problemas.append(f"{m.tipo}: teto por matéria {m.teto_por_materia} passa de {teto}")
    if not m.materias:
        problemas.append(f"{m.tipo}: matriz sem matéria")
    for materia in m.materias:
        if not materia.teses:
            problemas.append(f"{m.tipo}: matéria {materia.materia} sem tese")
        if materia.quantidade is not None and materia.quantidade > m.teto_por_materia:
            problemas.append(f"{m.tipo}: matéria {materia.materia} passa do teto")
    return problemas


def _materias(m: Matriz, rng: random.Random) -> list[str] | None:
    lista = [x.materia for x in m.materias for _ in range(x.quantidade or 0)]
    livres = [x.materia for x in m.materias if x.quantidade is None]
    contagem = Counter(lista)
    while len(lista) < m.quantidade:
        cabem = [x for x in livres if contagem[x] < m.teto_por_materia]
        if not cabem:
            return None
        escolhida = rng.choice(cabem)
        contagem[escolhida] += 1
        lista.append(escolhida)
    if len(lista) != m.quantidade:
        return None
    rng.shuffle(lista)
    return lista


def _permitidos(
    base: Combinacao, campo: str, opcoes: Sequence[Any], travas: Sequence[Trava]
) -> list[Any]:
    cabem: list[Any] = []
    for opcao in opcoes:
        candidata = replace(base, **{campo: opcao})
        if not _violadas(travas, _campos(visao_da_combinacao(candidata)), CAMPOS_DA_FICHA):
            cabem.append(opcao)
    return cabem


def _completar(
    base: Combinacao, m: Matriz, travas: Sequence[Trava], rng: random.Random
) -> Combinacao | None:
    """Sorteia os eixos uniformes entre os valores que as travas admitem."""
    autores = [c for c in m.categorias_autor if c not in PRAZO_EM_DOBRO]
    reus = [c for c in m.categorias_reu if c not in PRAZO_EM_DOBRO]
    etapas: list[tuple[str, Sequence[Any]]] = [
        ("categoria_autor", autores),
        ("categoria_reu", reus),
    ]
    if m.tipo == "manifestacao_ar_negativo":
        etapas += [("motivo_devolucao", m.motivos_devolucao), ("pedido_ar", m.pedidos_ar)]
    atual = base
    for campo, opcoes in etapas:
        cabem = _permitidos(atual, campo, opcoes, travas)
        if not cabem:
            return None
        atual = replace(atual, **{campo: rng.choice(cabem)})
    if _violadas(travas, _campos(visao_da_combinacao(atual)), CAMPOS_DA_FICHA):
        return None
    return atual


def _tese(m: Matriz, materia: str, rng: random.Random) -> str:
    return rng.choice(next(x.teses for x in m.materias if x.materia == materia))


def _base(m: Matriz, i: int, fixos: Mapping[str, Sequence[str]], materia: str, tese: str) -> Any:
    def valor(eixo: str, padrao: str | None) -> Any:
        return fixos[eixo][i] if eixo in fixos else padrao

    return Combinacao(
        tipo=m.tipo,
        materia=materia,
        tese=tese,
        polo=valor("polo", "autor"),
        complexidade=valor("complexidade", None),
        estilo=valor("estilo", None),
        momento=m.momento,
        rito=valor("rito", RITO_FIXO.get(m.tipo)),
        defeito=valor("defeito", None),
        tipo_decisao=valor("tipo_decisao", None),
    )


def sortear(m: Matriz, travas: Travas, semente: int, config: ConfigMatriz) -> Sorteio:
    """Sorteia as combinações do tipo; em `tentativas_maximas` sem achar, volta."""
    fixos = _fixos(m)
    rng = gerador(semente, m.tipo)
    lista = travas.travas
    for tentativa in range(1, config.tentativas_maximas + 1):
        materias = _materias(m, rng)
        if materias is None:
            continue
        embaralhados = {eixo: rng.sample(valores, len(valores)) for eixo, valores in fixos.items()}
        combinacoes: list[Combinacao] = []
        for i, materia in enumerate(materias):
            base = _base(m, i, embaralhados, materia, _tese(m, materia, rng))
            completa = _completar(base, m, lista, rng)
            if completa is None:
                break
            combinacoes.append(completa)
        else:
            return Sorteio("ok", tuple(combinacoes), tentativa)
    return Sorteio(VOLTA, (), config.tentativas_maximas)


def combinacao_do_ensaio(m: Matriz, travas: Travas, semente: int, config: ConfigMatriz) -> Sorteio:
    """A combinação da peça mais longa do tipo (ARQUITETURA §1.4); o resto pela semente."""
    fixos = _fixos(m)
    rng = gerador(semente, m.tipo, "ensaio")
    escolhas = {
        "complexidade": "media",
        "estilo": "detalhado",
    }
    if m.tipo == "embargos_declaracao":
        escolhas |= {"tipo_decisao": "sentenca", "defeito": "omissao_parcial"}
    for tentativa in range(1, config.tentativas_maximas + 1):
        unico = {
            eixo: [escolhas.get(eixo) or rng.choice(sorted(set(valores)))]
            for eixo, valores in fixos.items()
        }
        materia = rng.choice([x.materia for x in m.materias])
        base = _base(m, 0, unico, materia, _tese(m, materia, rng))
        completa = _completar(base, m, travas.travas, rng)
        if completa is not None:
            return Sorteio("ok", (completa,), tentativa)
    return Sorteio(VOLTA, (), config.tentativas_maximas)


# ---------------------------------------------------------------------------
# Datas e dias úteis
# ---------------------------------------------------------------------------

UM_DIA = datetime.timedelta(days=1)


def eh_dia_util(data: datetime.date, feriados: Collection[datetime.date]) -> bool:
    return data.weekday() < 5 and data not in feriados


def termo_final(
    inicio: datetime.date, dias_uteis: int, feriados: Collection[datetime.date]
) -> datetime.date:
    """Último dia do prazo em dias úteis, sem o dia do início (art. 224 do CPC)."""
    if dias_uteis < 1:
        raise ErroMatriz("o prazo tem pelo menos um dia útil")
    dia = inicio
    contados = 0
    while contados < dias_uteis:
        dia += UM_DIA
        if eh_dia_util(dia, feriados):
            contados += 1
    return dia


def prazo_da_manifestacao(prazo_fixado: int | None) -> int:
    """O prazo da determinação, ou 5 dias úteis se o juiz não fixou (art. 218, § 3º)."""
    return prazo_fixado if prazo_fixado is not None else PRAZO_SEM_FIXACAO


@dataclass(frozen=True)
class Datas:
    ajuizamento: datetime.date
    limite_fatos: datetime.date
    fato_inicial: datetime.date
    data_peca: datetime.date
    decisao: datetime.date | None = None
    intimacao: datetime.date | None = None
    juntada_aviso: datetime.date | None = None
    prazo_inicio: datetime.date | None = None
    prazo_dias: int | None = None
    termo_final: datetime.date | None = None


def _util_em_ou_apos(data: datetime.date, feriados: Collection[datetime.date]) -> datetime.date:
    while not eh_dia_util(data, feriados):
        data += UM_DIA
    return data


def _anos_antes(data: datetime.date, anos: int) -> datetime.date:
    try:
        return data.replace(year=data.year - anos)
    except ValueError:  # 29 de fevereiro
        return data.replace(year=data.year - anos, day=28)


def _dia(rng: random.Random, inicio: datetime.date, fim: datetime.date) -> datetime.date:
    return inicio + datetime.timedelta(days=rng.randint(0, (fim - inicio).days))


def sortear_datas(
    rng: random.Random,
    tipo: NomeCurto,
    feriados: Collection[datetime.date],
    config: ConfigMatriz,
    prazo_fixado: int | None = None,
) -> Datas:
    """Datas do MVP em 2026, fatos até 2 anos antes e folga antes do termo final."""
    feriados = frozenset(feriados)
    for _ in range(config.tentativas_maximas):
        ajuizamento = _util_em_ou_apos(
            _dia(rng, datetime.date(ANO_DO_MVP, 1, 2), datetime.date(ANO_DO_MVP, 8, 31)),
            feriados,
        )
        limite = _anos_antes(ajuizamento, config.anos_maximos_dos_fatos)
        fato = _dia(rng, limite, ajuizamento - UM_DIA)
        if tipo == "peticao_inicial_jec":
            return Datas(ajuizamento, limite, fato, data_peca=ajuizamento)
        if tipo == "embargos_declaracao":
            decisao = _util_em_ou_apos(
                ajuizamento + datetime.timedelta(days=rng.randint(30, 150)), feriados
            )
            intimacao = _util_em_ou_apos(
                decisao + datetime.timedelta(days=rng.randint(0, 10)), feriados
            )
            juntada = None
            dias = PRAZO_EMBARGOS
        else:
            decisao = None
            juntada = _util_em_ou_apos(
                ajuizamento + datetime.timedelta(days=rng.randint(20, 120)), feriados
            )
            intimacao = _util_em_ou_apos(
                juntada + datetime.timedelta(days=rng.randint(0, 15)), feriados
            )
            dias = prazo_da_manifestacao(prazo_fixado)
        termo = termo_final(intimacao, dias, feriados)
        if termo.year != ANO_DO_MVP:
            continue
        # Dias úteis depois da intimação que deixam a folga antes do termo final.
        candidatos: list[datetime.date] = []
        dia = intimacao
        while True:
            dia = termo_final(dia, 1, feriados)
            if termo_final(dia, config.dias_uteis_de_folga, feriados) > termo:
                break
            candidatos.append(dia)
        if not candidatos:
            continue
        return Datas(
            ajuizamento,
            limite,
            fato,
            data_peca=rng.choice(candidatos),
            decisao=decisao,
            intimacao=intimacao,
            juntada_aviso=juntada,
            prazo_inicio=intimacao,
            prazo_dias=dias,
            termo_final=termo,
        )
    raise ErroMatriz(f"{tipo}: nenhuma data coube em {ANO_DO_MVP}")
