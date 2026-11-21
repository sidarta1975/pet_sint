"""Citações de lei: achar, resolver e conferir contra a tabela (ARQUITETURA §5.6).

`ler(texto, tabela)` acha cada citação, inclusive as compostas (com parte do
artigo, múltipla, por intervalo e elíptica), e a resolve em diploma, artigo e
parágrafo, guardando inciso e alínea para o cartão. Artigo sem diploma nem
expressão elíptica não é adivinhado: vira citação não resolvida. `conferir`
compara com a tabela no nível de artigo e parágrafo. Não lê arquivo.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final

from fabrica.comum.formatos import (
    Alerta,
    CitacaoNaoResolvida,
    CitacaoResolvida,
    Diploma,
    Dispositivo,
    Divergencia,
    ResultadoItem,
    TabelaNormas,
)

ITEM: Final = "citacao_fora_da_tabela"
EXTENSO = frozenset(
    """
    primeiro segundo terceiro quarto quinto sexto setimo oitavo nono decimo
    um dois tres quatro cinco seis sete oito nove dez onze doze treze quatorze quinze
    vinte trinta quarenta cinquenta cem cento mil
    """.split()
)
ANTES_DO_ARTIGO = frozenset({"no", "na", "nos", "nas", "pelo", "pela", "conforme", "segundo"})
_ROMANO = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")

# Ordem das alternativas importa: elípticas e diplomas antes das palavras soltas.
_FIXOS: list[tuple[str, str]] = [
    ("ELIP_ARTIGO", r"(?i:\b(?:do|no|o)\s+mesmo\s+(?:artigo|dispositivo)\b)"),
    (
        "ELIP_DIPLOMA",
        r"(?i:\b(?:(?:do|da|o|a|no|na)\s+)?(?:mesm[oa]|referid[oa])\s+(?:diploma|codigo|lei)\b"
        r"|\bdaquel[ea]\s+(?:diploma|codigo|lei)\b)",
    ),
    ("AMBOS", r"(?i:\bamb[oa]s\s+d[oa]s?\b)"),
]
_DEPOIS: list[tuple[str, str]] = [
    ("ART", r"(?i:\barts?\.|\bartigos?\b)"),
    ("UNICO", r"(?i:\bparagrafo\s+unico\b)"),
    ("PARS", r"(?i:§§|\bparagrafos\b)"),
    ("PAR", r"(?i:§|\bparagrafo\b)"),
    ("CAPUT", r"(?i:\bcaput\b)"),
    ("INCISO", r"(?i:\bincisos?\b)"),
    ("ALINEA", r"(?i:\balineas?\s+[\"“']?(?P<letra>[a-z])\b[\"”']?)"),
    ("NUM", r"\b(?P<num>\d{1,3}(?:\.\d{3})+|\d+)(?:\s?[º°o](?!\w))?(?:-(?P<suf>[A-Z])\b)?"),
    ("ROMANO", r"\b[IVXLCDM]+\b"),
    ("E", r"(?i:\be\b)"),
    ("A", r"\ba\b"),
    ("DO", r"(?i:\bd[oa]s?\b)"),
    ("VIRGULA", r","),
    ("PALAVRA", r"\w+"),
    ("SINAL", r"[^\w\s]"),
]


def dobrar(texto: str) -> str:
    """Tira o acento de cada letra sem mudar o tamanho do texto (posições iguais)."""
    return "".join(unicodedata.normalize("NFD", c)[0] for c in texto)


@dataclass(frozen=True)
class _Token:
    tipo: str
    texto: str
    inicio: int
    fim: int
    valor: str = ""


@dataclass
class _Entrada:
    paragrafo: str = "caput"
    inciso: str | None = None
    alinea: str | None = None


@dataclass
class _Spec:
    artigo: str
    entradas: list[_Entrada]
    inicio: int
    fim: int
    diploma: str | None = None
    sem_diploma: bool = False  # elíptica sem citação anterior


@dataclass(frozen=True)
class Leitura:
    resolvidas: tuple[CitacaoResolvida, ...]
    nao_resolvidas: tuple[CitacaoNaoResolvida, ...]


@dataclass(frozen=True)
class Conferencia:
    item: ResultadoItem
    resolvidas: tuple[CitacaoResolvida, ...]
    nao_resolvidas: tuple[CitacaoNaoResolvida, ...]
    alertas: list[Alerta] = field(default_factory=list)
    perguntas: list[str] = field(default_factory=list)


def _forma(forma: str) -> str:
    partes = [re.escape(p) for p in dobrar(forma).split()]
    corpo = r"\s+".join(partes)
    sensivel = forma.isupper() or not any(c.islower() for c in forma)
    padrao = rf"(?<![\w/]){corpo}(?!\w)(?!/\d)"
    return padrao if sensivel else f"(?i:{padrao})"


def _padrao(diplomas: Sequence[Diploma]) -> tuple[re.Pattern[str], dict[str, str]]:
    formas = sorted(
        ((f, d.id) for d in diplomas for f in [*d.formas, d.nome]),
        key=lambda x: len(x[0]),
        reverse=True,
    )
    grupos: list[str] = []
    ids: dict[str, str] = {}
    for tipo, regex in _FIXOS:
        grupos.append(f"(?P<{tipo}>{regex})")
    for i, (forma, id_) in enumerate(formas):
        nome = f"DIP{i}"
        ids[nome] = id_
        grupos.append(f"(?P<{nome}>{_forma(forma)})")
    for tipo, regex in _DEPOIS:
        grupos.append(f"(?P<{tipo}>{regex})")
    return re.compile("|".join(grupos)), ids


def _tokens(texto: str, diplomas: Sequence[Diploma]) -> list[_Token]:
    padrao, ids = _padrao(diplomas)
    tokens: list[_Token] = []
    for m in padrao.finditer(dobrar(texto)):
        tipo = m.lastgroup or "SINAL"
        valor = ""
        if tipo in ids:
            valor, tipo = ids[tipo], "DIPLOMA"
        elif tipo == "NUM":
            valor = m.group("num").replace(".", "") + (
                f"-{m.group('suf')}" if m.group("suf") else ""
            )
        elif tipo == "ALINEA":
            valor = m.group("letra")
        elif tipo == "ROMANO" and not _ROMANO.match(m.group()):
            tipo = "PALAVRA"
        tokens.append(_Token(tipo, texto[m.start() : m.end()], m.start(), m.end(), valor))
    tokens.append(_Token("FIM", "", len(texto), len(texto)))
    return tokens


def _int_romano(r: str) -> int:
    valores = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for i, c in enumerate(r):
        v = valores[c]
        total += -v if i + 1 < len(r) and valores[r[i + 1]] > v else v
    return total


def _romano(n: int) -> str:
    pares = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    saida = ""
    for valor, letras in pares:
        while n >= valor:
            saida += letras
            n -= valor
    return saida


class _Leitor:
    def __init__(self, texto: str, diplomas: Sequence[Diploma]) -> None:
        self.texto = texto
        self.t = _tokens(texto, diplomas)
        self.usados: set[int] = set()
        self.ultimo_diploma: str | None = None
        self.ultimo_artigo: tuple[str, str] | None = None
        self.resolvidas: list[CitacaoResolvida] = []
        self.nao_resolvidas: list[CitacaoNaoResolvida] = []

    def tipo(self, i: int) -> str:
        return self.t[i].tipo if i < len(self.t) else "FIM"

    # --- partes do artigo -----------------------------------------------------

    def _romanos(self, j: int) -> tuple[list[str], int]:
        romanos = [self.t[j].texto]
        j += 1
        while True:
            if self.tipo(j) == "E" and self.tipo(j + 1) == "ROMANO":
                romanos.append(self.t[j + 1].texto)
                j += 2
            elif self.tipo(j) == "A" and self.tipo(j + 1) == "ROMANO":
                fim = _int_romano(self.t[j + 1].texto)
                romanos += [_romano(n) for n in range(_int_romano(romanos[-1]) + 1, fim + 1)]
                j += 2
            else:
                return romanos, j

    def _paragrafos(self, j: int, plural: bool) -> tuple[list[str], int]:
        numeros = [self.t[j].valor]
        j += 1
        while plural:
            if self.tipo(j) == "E" and self.tipo(j + 1) == "NUM":
                numeros.append(self.t[j + 1].valor)
                j += 2
            elif self.tipo(j) == "A" and self.tipo(j + 1) == "NUM":
                fim = int(self.t[j + 1].valor)
                numeros += [str(n) for n in range(int(numeros[-1]) + 1, fim + 1)]
                j += 2
            else:
                break
        return numeros, j

    def partes(self, j: int) -> tuple[list[_Entrada], int]:
        """Lê caput, parágrafos, incisos e alíneas; devolve as entradas e onde parou."""
        entradas: list[_Entrada] = []
        inicio_partes = {"CAPUT", "UNICO", "PAR", "PARS", "INCISO", "ROMANO", "ALINEA"}
        while True:
            k = j
            if self.tipo(k) == "VIRGULA":
                k += 1
            if self.tipo(k) == "E" and self.tipo(k + 1) in inicio_partes - {"ROMANO"}:
                k += 1
            tipo = self.tipo(k)
            if tipo == "CAPUT":
                entradas.append(_Entrada("caput"))
                j = k + 1
            elif tipo == "UNICO":
                entradas.append(_Entrada("unico"))
                j = k + 1
            elif tipo in ("PAR", "PARS") and self.tipo(k + 1) == "NUM":
                numeros, j = self._paragrafos(k + 1, tipo == "PARS")
                entradas += [_Entrada(n) for n in numeros]
            elif tipo == "ROMANO" or (tipo == "INCISO" and self.tipo(k + 1) == "ROMANO"):
                romanos, j = self._romanos(k + 1 if tipo == "INCISO" else k)
                if entradas and entradas[-1].inciso is None:
                    entradas[-1].inciso = romanos.pop(0)
                paragrafo = entradas[-1].paragrafo if entradas else "caput"
                entradas += [_Entrada(paragrafo, r) for r in romanos]
            elif tipo == "ALINEA":
                if not entradas:
                    entradas.append(_Entrada())
                entradas[-1].alinea = self.t[k].valor
                j = k + 1
            else:
                return entradas, j

    # --- diploma depois e antes -----------------------------------------------

    def diploma_depois(self, j: int) -> tuple[str | None, bool, bool, int]:
        """(diploma, é elíptica sem anterior, vale para o grupo todo, onde parou)."""
        k = j + 1 if self.tipo(j) == "VIRGULA" else j
        if self.tipo(k) == "DO" and self.tipo(k + 1) == "DIPLOMA":
            self.usados.add(k + 1)
            return self.t[k + 1].valor, False, False, k + 2
        if self.tipo(k) == "AMBOS" and self.tipo(k + 1) == "DIPLOMA":
            self.usados.add(k + 1)
            return self.t[k + 1].valor, False, True, k + 2
        if self.tipo(k) == "ELIP_DIPLOMA":
            self.usados.add(k)
            return self.ultimo_diploma, self.ultimo_diploma is None, False, k + 1
        return None, False, False, j

    def diploma_antes(self, i: int) -> tuple[str | None, bool]:
        k = i - 1
        while k >= 0 and (
            self.t[k].tipo in ("VIRGULA",)
            or self.t[k].texto == "("
            or (
                self.t[k].tipo in ("PALAVRA", "DO")
                and dobrar(self.t[k].texto).lower() in ANTES_DO_ARTIGO
            )
        ):
            k -= 1
        if k < 0 or k in self.usados:
            return None, False
        if self.t[k].tipo == "DIPLOMA":
            self.usados.add(k)
            return self.t[k].valor, False
        if self.t[k].tipo == "ELIP_DIPLOMA":
            self.usados.add(k)
            return self.ultimo_diploma, self.ultimo_diploma is None
        return None, False

    # --- emitir ---------------------------------------------------------------

    def emitir(self, specs: list[_Spec], inicio: int, fim: int) -> None:
        trecho = self.texto[inicio:fim]
        for s in specs:
            if s.diploma is None:
                self.nao_resolvidas.append(
                    CitacaoNaoResolvida(trecho=self.texto[s.inicio : s.fim], posicao=s.inicio)
                )
                continue
            for e in s.entradas or [_Entrada()]:
                self.resolvidas.append(
                    CitacaoResolvida(
                        diploma=s.diploma,
                        artigo=s.artigo,
                        paragrafo=e.paragrafo,
                        inciso=e.inciso,
                        alinea=e.alinea,
                        trecho=trecho,
                        posicao=inicio,
                    )
                )
            self.ultimo_diploma = s.diploma
            self.ultimo_artigo = (s.artigo, s.diploma)

    def _atribuir(self, specs: list[_Spec], diploma: str | None, falhou: bool) -> None:
        for s in specs:
            if s.diploma is None and not s.sem_diploma:
                s.diploma = diploma
                s.sem_diploma = falhou
        if diploma is not None:
            self.ultimo_diploma = diploma

    # --- grupos ---------------------------------------------------------------

    def grupo(self, i: int) -> int:
        """Lê um grupo que começa em "art."; devolve o índice seguinte."""
        if self.tipo(i + 1) != "NUM":
            palavra = dobrar(self.t[i + 1].texto).lower() if i + 1 < len(self.t) else ""
            if palavra in EXTENSO:
                fim = self.t[i + 1].fim
                self.nao_resolvidas.append(
                    CitacaoNaoResolvida(
                        trecho=self.texto[self.t[i].inicio : fim], posicao=self.t[i].inicio
                    )
                )
                return i + 2
            return i + 1
        specs: list[_Spec] = []
        j = i + 1
        fim = self.t[i].fim
        while True:
            num = self.t[j]
            if self.tipo(j + 1) == "A" and self.tipo(j + 2) == "NUM":
                ultimo = self.t[j + 2]
                for n in range(int(num.valor), int(ultimo.valor) + 1):
                    specs.append(_Spec(str(n), [], num.inicio, ultimo.fim))
                j += 3
            else:
                entradas, j = self.partes(j + 1)
                specs.append(_Spec(num.valor, entradas, self.t[i].inicio, self.t[j - 1].fim))
            fim = self.t[j - 1].fim
            diploma, falhou, _, depois = self.diploma_depois(j)
            if depois != j:
                self._atribuir(specs, diploma, falhou)
                j = depois
                fim = self.t[j - 1].fim
            pulos = (
                (("VIRGULA", "NUM"), 1),
                (("E", "NUM"), 1),
                (("VIRGULA", "E", "NUM"), 2),
                (("E", "ART", "NUM"), 2),
                (("VIRGULA", "E", "ART", "NUM"), 3),
            )
            for padrao, salto in pulos:
                if all(self.tipo(j + n) == p for n, p in enumerate(padrao)):
                    j += salto
                    break
            else:
                break
        pendentes = [s for s in specs if s.diploma is None and not s.sem_diploma]
        if pendentes:
            diploma, falhou = self.diploma_antes(i)
            self._atribuir(pendentes, diploma, falhou)
        self.emitir(specs, self.t[i].inicio, fim)
        return j

    def prefixo(self, i: int) -> int:
        """ "§ 3º do art. 218", "o inciso VIII do art. 6º", "§ 2º do mesmo artigo"."""
        entradas, j = self.partes(i - 1 if self.tipo(i - 1) == "VIRGULA" else i)
        if not entradas:
            return i + 1
        inicio = self.t[i].inicio
        if self.tipo(j) == "ELIP_ARTIGO":
            fim = self.t[j].fim
            if self.ultimo_artigo is None:
                self.nao_resolvidas.append(
                    CitacaoNaoResolvida(trecho=self.texto[inicio:fim], posicao=inicio)
                )
                return j + 1
            artigo, anterior = self.ultimo_artigo
            self.emitir([_Spec(artigo, entradas, inicio, fim, anterior)], inicio, fim)
            return j + 1
        if self.tipo(j) == "DO" and self.tipo(j + 1) == "ART" and self.tipo(j + 2) == "NUM":
            num = self.t[j + 2]
            spec = _Spec(num.valor, entradas, inicio, num.fim)
            fim = num.fim
            diploma, falhou, _, depois = self.diploma_depois(j + 3)
            if depois != j + 3:
                self._atribuir([spec], diploma, falhou)
                fim = self.t[depois - 1].fim
            else:
                diploma, falhou = self.diploma_antes(i)
                self._atribuir([spec], diploma, falhou)
            self.emitir([spec], inicio, fim)
            return max(depois, j + 3)
        return i + 1

    def ler(self) -> Leitura:
        i = 0
        while i < len(self.t):
            tipo = self.t[i].tipo
            if tipo == "ART":
                i = self.grupo(i)
            elif tipo in ("PAR", "PARS", "UNICO", "INCISO", "CAPUT"):
                i = self.prefixo(i)
            else:
                i += 1
        return Leitura(tuple(self.resolvidas), tuple(self.nao_resolvidas))


def ler(texto: str, tabela: TabelaNormas | Sequence[Diploma]) -> Leitura:
    """Todas as citações do texto, na ordem, resolvidas ou não."""
    diplomas = tabela.diplomas if isinstance(tabela, TabelaNormas) else list(tabela)
    return _Leitor(texto, diplomas).ler()


# ---------------------------------------------------------------------------
# Conferência contra a tabela
# ---------------------------------------------------------------------------


def _artigo(artigo: str) -> str:
    m = re.match(r"\s*(\d[\d.]*)\s*[º°o]?\s*(?:-\s*([A-Za-z]))?", artigo)
    if m is None:
        return artigo.strip()
    return m.group(1).replace(".", "") + (f"-{m.group(2).upper()}" if m.group(2) else "")


def _paragrafo(paragrafo: str) -> str:
    texto = dobrar(paragrafo).strip().lower()
    if texto in ("", "caput"):
        return "caput"
    if "unico" in texto:
        return "unico"
    numero = re.search(r"\d+", texto)
    return numero.group() if numero else texto


def chave(dispositivo: Dispositivo) -> tuple[str, str, str]:
    """Diploma, artigo e parágrafo do dispositivo, na forma da citação resolvida."""
    return (dispositivo.diploma, _artigo(dispositivo.artigo), _paragrafo(dispositivo.paragrafo))


def pergunta(citacao: CitacaoNaoResolvida) -> str:
    return (
        f'A peça cita "{citacao.trecho}" (posição {citacao.posicao}) sem que o programa '
        "reconheça o diploma. A que dispositivo se refere, e ele está no trecho da tabela "
        "do tipo?"
    )


def conferir(texto: str, tabela: TabelaNormas) -> Conferencia:
    """`citacao_fora_da_tabela`: reprova citação resolvida fora da tabela; a não resolvida
    vira alerta e pergunta ao checklist e não reprova sozinha."""
    leitura = ler(texto, tabela)
    na_tabela = {chave(d) for d in tabela.dispositivos}
    divergencias: list[Divergencia] = []
    vistos: set[tuple[int, str, str, str]] = set()
    for c in leitura.resolvidas:
        if (c.diploma, c.artigo, c.paragrafo) in na_tabela:
            continue
        # Uma divergência por dispositivo; o inciso não muda o resultado.
        marca = (c.posicao, c.diploma, c.artigo, c.paragrafo)
        if marca in vistos:
            continue
        vistos.add(marca)
        divergencias.append(
            Divergencia(
                regra="citação fora da tabela",
                extraido=c.trecho,
                ficha=f"{c.diploma}, art. {c.artigo}, {c.paragrafo}: não está na tabela "
                f"{tabela.versao}",
            )
        )
    if divergencias:
        trecho = "; ".join(d.extraido for d in divergencias)
        item = ResultadoItem(
            item=ITEM,
            resposta="nao_passa",
            quem="programa",
            trecho=trecho,
            divergencias=divergencias,
        )
    else:
        item = ResultadoItem(
            item=ITEM,
            resposta="passa",
            quem="programa",
            trecho="toda citação resolvida está na tabela",
            divergencias=[],
        )
    alertas = [
        Alerta(item=ITEM, origem="citacoes.py", texto=f"citação não reconhecida: {n.trecho}")
        for n in leitura.nao_resolvidas
    ]
    return Conferencia(
        item=item,
        resolvidas=leitura.resolvidas,
        nao_resolvidas=leitura.nao_resolvidas,
        alertas=alertas,
        perguntas=[pergunta(n) for n in leitura.nao_resolvidas],
    )
