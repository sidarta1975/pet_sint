"""Itens de programa sobre o rascunho (ARQUITETURA §5.6, Anexos B.1 e D).

`estrutura`, `coerencia_ficha`, `alcada`, `prazo`, `termos_inequivocos` e `marca`.
Tudo chega por parâmetro e cada item devolve um `ResultadoItem` respondido pelo
programa. Não lê arquivo nem chama modelo. A normalização roda sobre cópias.
"""

from __future__ import annotations

import datetime
import itertools
import re
from collections.abc import Callable, Collection, Iterator, Sequence
from typing import Any

from pydantic import BaseModel

from fabrica import ficticios, matriz
from fabrica.comum import normalizacao as norm
from fabrica.comum.formatos import (
    Configuracao,
    Divergencia,
    Endereco,
    EstruturaMontada,
    Extracao,
    FeriadosNacionais,
    Ficha,
    FichaEmbargos,
    FichaInicial,
    FichaManifestacao,
    FichaQualquer,
    ItemPrograma,
    Perfil,
    ReaisPermitidos,
    ReaisProibidos,
    ResultadoItem,
    ResultadoProgramas,
    TabelaNormas,
    TermosInequivocos,
    ValorExtraido,
)
from fabrica.conferencia import citacoes
from fabrica.conferencia.dados_reais import Detector
from fabrica.conferencia.extracao import (
    caminho_etapa,
    caminho_ficha,
    caminho_rascunho,
    tipo_do_catalogo,
)

MARCA = "DOCUMENTO SINTÉTICO — FICTÍCIO"
LUGARES_DE_REFERENCIA = ("fatos", "outro")
_TITULO = re.compile(r"^##(?!#)\s*(.*?)\s*#*\s*$")


class ErroRegras(Exception):
    """Chamada que não faz sentido: item que não é de programa ou ficha sem o dado."""


def _resultado(item: ItemPrograma, divergencias: list[Divergencia], ok: str) -> ResultadoItem:
    if divergencias:
        trecho = "; ".join(f"{d.regra}: {d.extraido} (ficha: {d.ficha})" for d in divergencias)
        return ResultadoItem(
            item=item,
            resposta="nao_passa",
            quem="programa",
            trecho=trecho,
            divergencias=divergencias,
        )
    return ResultadoItem(item=item, resposta="passa", quem="programa", trecho=ok, divergencias=[])


def _div(regra: str, extraido: object, ficha: object) -> Divergencia:
    return Divergencia(regra=regra, extraido=str(extraido), ficha=str(ficha))


# ---------------------------------------------------------------------------
# Estrutura
# ---------------------------------------------------------------------------


def titulos(rascunho: str) -> list[str]:
    """Os títulos de segundo nível do Markdown, na ordem em que aparecem."""
    achados: list[str] = []
    for linha in rascunho.splitlines():
        m = _TITULO.match(linha.strip())
        if m is not None:
            achados.append(m.group(1))
    return achados


def estrutura(rascunho: str, montada: EstruturaMontada) -> ResultadoItem:
    """Blocos obrigatórios presentes e todos os blocos achados na ordem da estrutura."""
    posicoes: dict[str, int] = {}
    for i, titulo in enumerate(titulos(rascunho)):
        posicoes.setdefault(norm.comparavel(titulo), i)
    divergencias: list[Divergencia] = []
    for b in montada.blocos:
        if b.obrigatorio and norm.comparavel(b.titulo) not in posicoes:
            divergencias.append(_div("bloco ausente", "ausente", f"## {b.titulo}"))
    achados = [b for b in montada.blocos if norm.comparavel(b.titulo) in posicoes]
    ordem_na_peca = sorted(achados, key=lambda b: posicoes[norm.comparavel(b.titulo)])
    if ordem_na_peca != achados:
        divergencias.append(
            _div(
                "bloco fora de ordem",
                " > ".join(b.titulo for b in ordem_na_peca),
                " > ".join(b.titulo for b in achados),
            )
        )
    return _resultado("estrutura", divergencias, "blocos presentes e na ordem")


# ---------------------------------------------------------------------------
# Coerência com a ficha (Anexo D)
# ---------------------------------------------------------------------------


def _percorrer(objeto: Any) -> Iterator[Any]:
    yield objeto
    if isinstance(objeto, BaseModel):
        for nome in type(objeto).model_fields:
            yield from _percorrer(getattr(objeto, nome))
    elif isinstance(objeto, list | tuple):
        for item in objeto:
            yield from _percorrer(item)


def datas_da_ficha(ficha: FichaQualquer) -> set[datetime.date]:
    return {x for x in _percorrer(ficha) if isinstance(x, datetime.date)}


def ceps_da_ficha(ficha: FichaQualquer) -> set[str]:
    return {norm.cep(x.cep) for x in _percorrer(ficha) if isinstance(x, Endereco)}


def _identificadores(ficha: FichaQualquer) -> dict[str, set[str]]:
    protocolos = {p.identificador for p in ficha.provas} | {ficha.processo.identificador_ficticio}
    tentativa = getattr(ficha, "tentativa_previa", None)
    if tentativa is not None:
        protocolos.add(tentativa.protocolo)
    documentos = {p.documento for p in ficha.partes}
    processo = {ficha.processo.numero_cnj} if ficha.processo.numero_cnj else set()
    brutos = {
        "cpf": documentos,
        "cnpj": documentos,
        "numero_processo": processo,
        "protocolo": protocolos,
        "contrato": protocolos,
    }
    return {tipo: {norm.so_digitos_e_letras(x) for x in v} for tipo, v in brutos.items()}


def _referencias_legais(ficha: FichaQualquer, config: Configuracao) -> set[int]:
    # Só a inicial carrega o salário mínimo de referência (Anexo A.2).
    if not isinstance(ficha, FichaInicial):
        return set()
    salario = ficha.salario_minimo_referencia
    return {salario, config.referencias_legais.alcada_em_salarios_minimos * salario}


def _somas(ficha: FichaQualquer) -> set[int]:
    centavos = {v.id: v.centavos for v in ficha.valores}
    dos_pedidos = sorted({p.valor for p in ficha.pedidos if p.valor is not None})
    somas = {
        sum(centavos[i] for i in combinacao)
        for k in range(2, len(dos_pedidos) + 1)
        for combinacao in itertools.combinations(dos_pedidos, k)
    }
    if ficha.valor_causa is not None:
        somas.add(centavos[ficha.valor_causa])
    return somas


def _valor(v: ValorExtraido, ficha: FichaQualquer, config: Configuracao) -> Divergencia | None:
    extraido = f"{v.texto} ({v.centavos} centavos, lugar {v.lugar})"
    algarismos = norm.centavos_em_algarismos(v.texto)
    if algarismos is not None and norm.tem_extenso(v.texto) and algarismos != v.centavos:
        return _div("valor por extenso", extraido, f"algarismos {algarismos}, extenso {v.centavos}")
    valores = {x.centavos for x in ficha.valores}
    centavos = {x.id: x.centavos for x in ficha.valores}
    if v.lugar == "valor_causa":
        causa = centavos.get(ficha.valor_causa) if ficha.valor_causa else None
        if causa is None:
            return _div("valor da causa", extraido, "a ficha não tem valor da causa")
        return None if v.centavos == causa else _div("valor da causa", extraido, causa)
    if v.centavos in valores:
        return None
    if v.lugar == "pedido":
        return _div("valor", extraido, f"valores da ficha: {sorted(valores)}")
    if v.centavos in _referencias_legais(ficha, config):
        return None
    if v.centavos in _somas(ficha):
        return None
    if v.lugar == "fatos" and norm.tem_marca_de_aproximacao(v.texto):
        limite = config.comparacao.diferenca_maxima_arredondamento
        if any(x and abs(v.centavos - x) / x <= limite for x in valores):
            return None
    return _div("valor", extraido, f"valores da ficha: {sorted(valores)}")


def _datas(extracao: Extracao, ficha: FichaQualquer) -> list[Divergencia]:
    datas = datas_da_ficha(ficha)
    meses = {d.isoformat()[:7] for d in datas}
    divergencias: list[Divergencia] = []
    for d in extracao.datas:
        if d.data is None:  # data relativa: não comparada
            continue
        bate = d.data in meses if len(d.data) == 7 else d.data in {x.isoformat() for x in datas}
        if not bate:
            divergencias.append(
                _div(
                    "data",
                    f"{d.texto} ({d.data})",
                    f"datas da ficha: {', '.join(sorted(x.isoformat() for x in datas))}",
                )
            )
    return divergencias


def _documentos(extracao: Extracao, ficha: FichaQualquer) -> list[Divergencia]:
    ceps = ceps_da_ficha(ficha)
    ids = _identificadores(ficha)
    oab = norm.nome(ficha.advogado.oab)
    por_regra: dict[str, list[Divergencia]] = {"cep": [], "documento": [], "oab": []}
    for d in extracao.documentos:
        if d.tipo == "cep":
            if norm.cep(d.texto) not in ceps:
                por_regra["cep"].append(_div("cep", d.texto, f"CEPs da ficha: {sorted(ceps)}"))
        elif d.tipo == "oab":
            if norm.nome(d.texto) != oab:
                por_regra["oab"].append(_div("oab", d.texto, ficha.advogado.oab))
        elif norm.so_digitos_e_letras(d.texto) not in ids[d.tipo]:
            ficha_txt = ", ".join(sorted(ids[d.tipo])) or "nenhum na ficha"
            por_regra["documento"].append(_div(d.tipo, d.texto, ficha_txt))
    return por_regra["cep"] + por_regra["documento"] + por_regra["oab"]


def _nomes(extracao: Extracao, ficha: FichaQualquer) -> list[Divergencia]:
    marcadores: dict[str, str] = {p.papel: p.nome for p in ficha.partes}
    marcadores["advogado"] = ficha.advogado.nome
    todos = {norm.nome(x) for x in marcadores.values()}
    divergencias: list[Divergencia] = []
    for n in extracao.nomes:
        if norm.eh_designacao(n.texto):  # "o autor", "a ré": não é nome
            continue
        if n.papel == "outro":
            if norm.nome(n.texto) not in todos:
                divergencias.append(_div("nome", f"{n.texto} (outro)", "nenhum nome da ficha"))
            continue
        certo = marcadores[n.papel]
        if norm.nome(n.texto) != norm.nome(certo):
            divergencias.append(_div("nome", f"{n.texto} ({n.papel})", certo))
    return divergencias


def _comarca_juizo(extracao: Extracao, ficha: FichaQualquer) -> list[Divergencia]:
    divergencias: list[Divergencia] = []
    if extracao.comarca is not None and norm.comarca(extracao.comarca) != norm.comarca(
        ficha.processo.comarca
    ):
        divergencias.append(_div("comarca", extracao.comarca, ficha.processo.comarca))
    if extracao.juizo is not None and norm.juizo(extracao.juizo) != norm.juizo(
        ficha.processo.juizo
    ):
        divergencias.append(_div("juizo", extracao.juizo, ficha.processo.juizo))
    return divergencias


def _pedidos(extracao: Extracao, ficha: FichaQualquer, perfil: Perfil) -> list[Divergencia]:
    da_ficha = [p.natureza for p in ficha.pedidos]
    extraidos = [p.natureza for p in extracao.pedidos]
    divergencias: list[Divergencia] = []
    for natureza in da_ficha:
        if natureza not in extraidos:
            divergencias.append(_div("pedido faltando", "ausente", natureza))
    padrao = set(perfil.pedidos_acessorios_padrao)
    for p in extracao.pedidos:
        if p.natureza == "outro":
            divergencias.append(_div("pedido outro", p.texto, "nenhum pedido outro na ficha"))
        elif p.natureza not in da_ficha and p.natureza not in padrao:
            divergencias.append(
                _div(
                    "pedido a mais",
                    p.natureza,
                    f"ficha: {', '.join(da_ficha)}; padrão do "
                    f"perfil: {', '.join(sorted(padrao)) or 'nenhum'}",
                )
            )
    return divergencias


def coerencia_ficha(
    extracao: Extracao, ficha: FichaQualquer, perfil: Perfil, config: Configuracao
) -> ResultadoItem:
    """Todas as linhas do Anexo D, na ordem do brief; cada reprovação guarda os dois lados."""
    divergencias = [d for v in extracao.valores if (d := _valor(v, ficha, config)) is not None]
    divergencias += _datas(extracao, ficha)
    divergencias += _documentos(extracao, ficha)
    divergencias += _nomes(extracao, ficha)
    divergencias += _comarca_juizo(extracao, ficha)
    divergencias += _pedidos(extracao, ficha, perfil)
    return _resultado("coerencia_ficha", divergencias, "extração igual à ficha")


# ---------------------------------------------------------------------------
# Alçada e prazo
# ---------------------------------------------------------------------------


def alcada(extracao: Extracao, ficha: FichaQualquer, config: Configuracao) -> ResultadoItem:
    """Valor da causa até 40 salários mínimos de `salario_minimo_referencia` da ficha."""
    if not isinstance(ficha, FichaInicial):
        raise ErroRegras("alçada só se confere na petição inicial do juizado")
    limite = config.referencias_legais.alcada_em_salarios_minimos * ficha.salario_minimo_referencia
    causas = [v for v in extracao.valores if v.lugar == "valor_causa"]
    if not causas:
        return _resultado("alcada", [_div("alçada", "sem valor da causa na peça", limite)], "")
    acima = [_div("alçada", v.centavos, limite) for v in causas if v.centavos > limite]
    return _resultado("alcada", acima, f"valor da causa até {limite} centavos")


def prazo(
    extracao: Extracao, ficha: FichaQualquer, feriados: Collection[datetime.date]
) -> ResultadoItem:
    """Data da peça até o termo final, recalculado em dias úteis com os feriados recebidos."""
    p = ficha.momento_processual.prazo
    if p is None:
        raise ErroRegras(f"{ficha.id}: a ficha não tem prazo")
    termo = matriz.termo_final(p.inicio, p.dias_uteis, feriados)
    data = extracao.data_peca
    if data is None or len(data) != 10:
        return _resultado("prazo", [_div("prazo", data or "sem data da peça", termo)], "")
    if datetime.date.fromisoformat(data) > termo:
        return _resultado("prazo", [_div("prazo", data, termo.isoformat())], "")
    return _resultado("prazo", [], f"data da peça {data} até o termo final {termo.isoformat()}")


# ---------------------------------------------------------------------------
# Termos inequívocos e marca
# ---------------------------------------------------------------------------


def termos_inequivocos(rascunho: str, termos: TermosInequivocos) -> ResultadoItem:
    achados = [
        _div("termo inequívoco", t.termo, f"{t.motivo} ({t.norma})")
        for t in termos.termos
        if norm.contem_termo(rascunho, t.termo)
    ]
    return _resultado("termos_inequivocos", achados, "nenhum termo inequívoco")


def marca(rascunho: str) -> ResultadoItem:
    presente = any(linha.strip() == MARCA for linha in rascunho.splitlines())
    falta = [] if presente else [_div("marca", "linha ausente", MARCA)]
    return _resultado("marca", falta, MARCA)


# ---------------------------------------------------------------------------
# Todos os itens pedidos
# ---------------------------------------------------------------------------


def conferir(
    rascunho: str,
    extracao: Extracao,
    ficha: FichaQualquer,
    montada: EstruturaMontada,
    perfil: Perfil,
    termos: TermosInequivocos,
    feriados: Collection[datetime.date],
    config: Configuracao,
    itens: Sequence[str],
) -> list[ResultadoItem]:
    """Os itens de programa pedidos, na ordem pedida."""
    funcoes: dict[str, Callable[[], ResultadoItem]] = {
        "estrutura": lambda: estrutura(rascunho, montada),
        "coerencia_ficha": lambda: coerencia_ficha(extracao, ficha, perfil, config),
        "alcada": lambda: alcada(extracao, ficha, config),
        "prazo": lambda: prazo(extracao, ficha, feriados),
        "termos_inequivocos": lambda: termos_inequivocos(rascunho, termos),
        "marca": lambda: marca(rascunho),
    }
    desconhecidos = [i for i in itens if i not in funcoes]
    if desconhecidos:
        raise ErroRegras(f"não é item de regras.py: {', '.join(desconhecidos)}")
    return [funcoes[i]() for i in itens]


# ---------------------------------------------------------------------------
# Etapa "programas" (brief 017): regras, citações e dado real sobre o rascunho
# ---------------------------------------------------------------------------

ITENS_DE_REGRAS = ("estrutura", "coerencia_ficha", "alcada", "prazo", "termos_inequivocos", "marca")


def _textos_da_ficha(ficha: FichaQualquer) -> tuple[list[str], list[str]]:
    """Ruas e outros textos de endereço e de processo da ficha (para o detector)."""
    enderecos = [p.endereco for p in ficha.partes] + [ficha.advogado.endereco_escritorio]
    if isinstance(ficha, FichaManifestacao):
        enderecos.append(ficha.endereco_tentado)
        if ficha.novo_endereco is not None:
            enderecos.append(ficha.novo_endereco)
    ruas = sorted({e.rua for e in enderecos})
    termos = {e.bairro for e in enderecos} | {e.cidade for e in enderecos}
    termos |= {ficha.processo.comarca, ficha.processo.juizo, ficha.local_peca}
    if isinstance(ficha, FichaEmbargos):
        termos.add(ficha.decisao_embargada.juizo)
    return ruas, sorted(termos)


def dado_real(
    rascunho: str,
    ficha: FichaQualquer,
    montada: EstruturaMontada,
    arquivos: Any,
    config: Configuracao,
) -> ResultadoItem:
    """O item `dado_real`: qualquer achado do detector de 5.2 reprova."""
    permitidos = arquivos.ler_json("dados/ficticios/reais_permitidos.json", ReaisPermitidos)
    proibidos = arquivos.ler_json("dados/ficticios/reais_proibidos.json", ReaisProibidos)
    ruas, termos = _textos_da_ficha(ficha)
    detector = Detector(
        marcadores=sorted(ficticios.MARCADORES),
        ruas=ruas,
        termos_da_ficha=termos,
        permitidos=[n.nome for n in permitidos.nomes],
        proibidos=[n.nome for n in proibidos.nomes],
        titulos=[b.titulo for b in montada.blocos],
        ddds=config.ddds.inexistentes,
        codigos_banco=[],  # lista oficial vazia no MVP (pendência do brief 009)
    )
    achados = detector.detectar(rascunho)
    divergencias = [_div("dado real", f"{a.tipo}: {a.trecho}", "nenhum dado real") for a in achados]
    return _resultado("dado_real", divergencias, "nenhum dado real")


class EtapaProgramas:
    """Aplica `regras.py`, `citacoes.py` e `dados_reais.py` ao rascunho e grava
    `saida/conferencias/<peça>_v<k>_programas.json`. Não chama modelo."""

    nome = "programas"

    def aplica(self, peca: Any, servicos: Any) -> bool:
        return bool(servicos.arquivos.existe(caminho_etapa(peca, "extracao")))

    def arquivo_resultado(self, peca: Any) -> str:
        return caminho_etapa(peca, self.nome)

    def pedir(self, peca: Any, servicos: Any) -> str | None:
        arquivos = servicos.arquivos
        config: Configuracao = servicos.config.geral
        catalogo = tipo_do_catalogo(peca.tipo, servicos)
        rascunho = arquivos.ler_texto(caminho_rascunho(peca))
        extracao = arquivos.ler_json(caminho_etapa(peca, "extracao"), Extracao)
        ficha = arquivos.ler_json(caminho_ficha(peca), Ficha).root
        montada = arquivos.ler_json(
            f"saida/preparacao/{peca.tipo}_estrutura.json", EstruturaMontada
        )
        perfil = arquivos.ler_json(f"dados/estruturas/perfis/{catalogo.perfil}.json", Perfil)
        termos = arquivos.ler_json("dados/conferencia/termos_inequivocos.json", TermosInequivocos)
        feriados = arquivos.ler_json("dados/conferencia/feriados_nacionais.json", FeriadosNacionais)
        tabela = arquivos.ler_json("dados/normas/tabela_normas.json", TabelaNormas)
        pedidos = [i for i in catalogo.itens_conferencia if i in ITENS_DE_REGRAS]
        de_regras = conferir(
            rascunho,
            extracao,
            ficha,
            montada,
            perfil,
            termos,
            [f.data for f in feriados.feriados],
            config,
            pedidos,
        )
        por_item = {r.item: r for r in de_regras}
        cit = citacoes.conferir(rascunho, tabela)
        por_item["citacao_fora_da_tabela"] = cit.item
        if "dado_real" in catalogo.itens_conferencia:
            por_item["dado_real"] = dado_real(rascunho, ficha, montada, arquivos, config)
        itens = [por_item[i] for i in catalogo.itens_conferencia if i in por_item]
        resultado = ResultadoProgramas(
            itens=itens,
            alertas=list(cit.alertas),
            citacoes_resolvidas=list(cit.resolvidas),
            citacoes_nao_resolvidas=list(cit.nao_resolvidas),
        )
        arquivos.gravar_json(caminho_etapa(peca, self.nome), resultado)
        return None

    def receber(self, peca: Any, resposta: Any, servicos: Any) -> str | None:
        raise ErroRegras("a etapa programas não faz pedido e não recebe resposta")
