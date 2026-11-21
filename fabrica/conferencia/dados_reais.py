"""Detector de dado real (ARQUITETURA §5.2 e §5.6; item `dado_real` do Anexo B.1).

Recebe tudo por parâmetro e não lê arquivo. Devolve cada achado com o tipo, o
trecho e a posição; o item passa só com a lista vazia.

Nome, pela definição da §5.2: duas ou mais palavras com inicial maiúscula fora do
início de frase; palavra com tratamento (Sr., Sra., Dr., Dra.); palavra com forma
societária (Ltda., S.A., ME, EIRELI); palavra com "Banco", "Companhia" ou
semelhante. Todo nome precisa ser marcador da ficha (ou pedaço dele) ou estar
na lista de permitidos; coincidência com a de proibidos também reprova. As
comparações ignoram maiúsculas e acentos.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

MARCA = "DOCUMENTO SINTÉTICO — FICTÍCIO"
MARCADOR_OAB = "OAB/UF nº 000.000"
PREFIXO = "SINT-"
DOMINIO_DE_EXEMPLO = ".example"

MAIUSCULA = "A-ZÀ-ÖØ-Ý"
LETRA = "A-Za-zÀ-ÖØ-öø-ÿ"
PALAVRA = rf"[{MAIUSCULA}][{LETRA}'’\-]*"
CONECTOR = r"(?:de|da|do|das|dos|e|d')"
SEQUENCIA = re.compile(rf"{PALAVRA}(?:\s+(?:{CONECTOR}\s+)?{PALAVRA})*")
TRATAMENTOS = ("Sr", "Sra", "Srta", "Dr", "Dra")
TRATAMENTO = re.compile(
    rf"\b(?:{'|'.join(TRATAMENTOS)})\.\s+{PALAVRA}(?:\s+(?:{CONECTOR}\s+)?{PALAVRA})*"
)
SOCIETARIAS = frozenset({"ltda", "s", "sa", "me", "eireli", "epp", "cia"})
EMPRESA = frozenset(
    {
        "banco",
        "companhia",
        "cia",
        "empresa",
        "grupo",
        "cooperativa",
        "seguradora",
        "operadora",
        "construtora",
        "instituicao",
        "lojas",
        "loja",
    }
)
ABREVIACOES = frozenset(
    {"sr", "sra", "srta", "dr", "dra", "nº", "n", "art", "arts", "fls", "fl", "inc", "p", "cf"}
    | {"s.a", "ltda", "av", "ex", "pag", "pág", "sec", "cia"}
)
CARGOS = (
    "juiz",
    "juíza",
    "desembargador",
    "desembargadora",
    "magistrado",
    "magistrada",
    "escrivão",
    "escrivã",
    "servidor",
    "servidora",
    "promotor",
    "promotora",
    "promotor de justiça",
    "promotora de justiça",
    "oficial de justiça",
    "analista judiciário",
    "analista judiciária",
    "técnico judiciário",
    "técnica judiciária",
    "diretor de secretaria",
    "diretora de secretaria",
    "chefe de cartório",
    "conciliador",
    "conciliadora",
)
CARGO = re.compile(
    rf"(?i:\b(?:{'|'.join(sorted(CARGOS, key=len, reverse=True))})(?:\s+de\s+direito)?)"
    rf"\s*,?\s+(?:(?:Dr|Dra)\.\s+)?(?P<nome>{PALAVRA}(?:\s+(?:{CONECTOR}\s+)?{PALAVRA})*)"
)
CPF = re.compile(r"(?<![\d.])\d{3}\.\d{3}\.\d{3}-\d{2}(?!\d)")
CNPJ = re.compile(r"(?<![0-9A-Z.])[0-9A-Z]{2}\.[0-9A-Z]{3}\.[0-9A-Z]{3}/[0-9A-Z]{4}-\d{2}(?!\d)")
PROCESSO = re.compile(r"(?<!\d)(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})(?!\d)")
OAB = re.compile(r"\bOAB\b[^\n]{0,25}?\d[\d.\-]*")
TELEFONES = (
    re.compile(r"\((\d{2})\)\s?\d{4,5}-?\d{4}(?!\d)"),
    re.compile(r"\+55\s?\(?(\d{2})\)?\s?\d{4,5}-?\d{4}(?!\d)"),
)
EMAIL = re.compile(r"[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+")
RUA = re.compile(
    r"\b(?:Rua|Avenida|Av\.|Travessa|Alameda|Praça|Estrada|Rodovia|Largo|Viela)\s+[^,;\n\d]*"
)
CONTRATO = re.compile(
    r"(?i:\b(?:contrato|protocolo)s?\b)\s*(?:(?i:n\.?\s*[º°o]\.?|número)\s*)?"
    r"(?P<numero>[A-Za-z0-9][\w./\-]*\d[\w./\-]*)"
)
BANCO = re.compile(
    r"(?i:c[óo]digo\s+(?:do\s+)?banco|\bbanco)\s*(?:(?i:n\.?\s*[º°])\s*)?(?P<codigo>\d{3})(?!\d)"
)


@dataclass(frozen=True)
class Achado:
    tipo: str
    trecho: str
    posicao: int


def _normal_letra(letra: str) -> str:
    base = unicodedata.normalize("NFD", letra)[0]
    minuscula = base.lower()
    return minuscula if len(minuscula) == 1 else base


def normalizar(texto: str) -> str:
    """Minúsculas e sem acento, com o mesmo tamanho do texto (posições iguais)."""
    return "".join(_normal_letra(letra) for letra in texto)


def _mod11(base: str, pesos: Sequence[int]) -> str:
    resto = sum((ord(c) - 48) * p for c, p in zip(base, pesos, strict=True)) % 11
    return "0" if resto < 2 else str(11 - resto)


def cpf_valido(cpf: str) -> bool:
    numeros = re.sub(r"\D", "", cpf)
    d1 = _mod11(numeros[:9], range(10, 1, -1))
    d2 = _mod11(numeros[:9] + d1, range(11, 1, -1))
    return numeros[9:] == d1 + d2


def cnpj_valido(cnpj: str) -> bool:
    caracteres = re.sub(r"[./\-]", "", cnpj)
    d1 = _mod11(caracteres[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = _mod11(caracteres[:12] + d1, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return caracteres[12:] == d1 + d2


def processo_valido(numero: re.Match[str]) -> bool:
    sequencial, dv, ano, ramo, tribunal, unidade = numero.groups()
    resto = int(sequencial + ano + ramo + tribunal + unidade + "00") % 97
    return dv == f"{98 - resto:02d}"


def _ocorrencias(normal: str, frase: str) -> Iterable[tuple[int, int]]:
    alvo = normalizar(frase).strip()
    if not alvo:
        return
    padrao = re.compile(r"(?<!\w)" + re.escape(alvo) + r"(?!\w)")
    for achado in padrao.finditer(normal):
        yield achado.start(), achado.end()


def _sigla(palavra: str) -> bool:
    letras = palavra.replace("-", "")
    return len(letras) >= 2 and letras.isupper()


class Detector:
    def __init__(
        self,
        marcadores: Sequence[str],
        ruas: Sequence[str],
        termos_da_ficha: Sequence[str],
        permitidos: Sequence[str],
        proibidos: Sequence[str],
        titulos: Sequence[str],
        ddds: Sequence[int],
        codigos_banco: Sequence[str],
    ) -> None:
        self._marcadores = [normalizar(m) for m in marcadores]
        self._ruas = [normalizar(r).strip() for r in ruas]
        self._mascarar = [*marcadores, *ruas, *termos_da_ficha, *permitidos, *titulos, MARCA]
        self._aceitos = [normalizar(t) for t in (*permitidos, *termos_da_ficha, *ruas)]
        self._proibidos = list(proibidos)
        self._ddds = frozenset(ddds)
        self._codigos = frozenset(codigos_banco)

    # --- números e contatos ----------------------------------------------------

    def _numeros(self, texto: str) -> list[Achado]:
        achados: list[Achado] = []
        for m in CPF.finditer(texto):
            if cpf_valido(m.group()):
                achados.append(Achado("cpf", m.group(), m.start()))
        for m in CNPJ.finditer(texto):
            if cnpj_valido(m.group()):
                achados.append(Achado("cnpj", m.group(), m.start()))
        for m in PROCESSO.finditer(texto):
            if processo_valido(m):
                achados.append(Achado("numero_processo", m.group(), m.start()))
        for m in OAB.finditer(texto):
            if not texto.startswith(MARCADOR_OAB, m.start()):
                achados.append(Achado("oab", m.group(), m.start()))
        for padrao in TELEFONES:
            for m in padrao.finditer(texto):
                if int(m.group(1)) not in self._ddds:
                    achados.append(Achado("telefone", m.group(), m.start()))
        for m in EMAIL.finditer(texto):
            if not m.group().lower().endswith(DOMINIO_DE_EXEMPLO):
                achados.append(Achado("email", m.group(), m.start()))
        for m in RUA.finditer(texto):
            trecho = re.split(r"\s+n[º°.]", m.group())[0].rstrip(" -—")
            nome = normalizar(trecho)
            if not any(nome == rua or nome.startswith(rua) for rua in self._ruas):
                achados.append(Achado("rua", trecho, m.start()))
        for m in CONTRATO.finditer(texto):
            numero = m.group("numero").rstrip(".,;:")
            if not numero.startswith(PREFIXO):
                achados.append(Achado("contrato_protocolo", numero, m.start("numero")))
        for m in BANCO.finditer(texto):
            if m.group("codigo") in self._codigos:
                achados.append(Achado("codigo_banco", m.group("codigo"), m.start("codigo")))
        return achados

    # --- nomes -----------------------------------------------------------------

    def _proibidos_no(self, texto: str, normal: str) -> list[Achado]:
        return [
            Achado("nome_proibido", texto[inicio:fim], inicio)
            for nome in self._proibidos
            for inicio, fim in _ocorrencias(normal, nome)
        ]

    def _mascarado(self, texto: str, normal: str) -> str:
        letras = list(texto)
        trechos = [(m.start(), m.end()) for m in EMAIL.finditer(texto)]
        for frase in self._mascarar:
            trechos.extend(_ocorrencias(normal, frase))
        for inicio, fim in trechos:
            for i in range(inicio, fim):
                if not letras[i].isspace():
                    letras[i] = "x"
        return "".join(letras)

    @staticmethod
    def _inicio_de_frase(texto: str, posicao: int) -> bool:
        i = posicao - 1
        while i >= 0 and texto[i] in " \t\"'“”‘’()[]*#•-—–":
            i -= 1
        if i < 0 or texto[i] in "\n!?:":
            return True
        if texto[i] != ".":
            return False
        j = i
        while j > 0 and not texto[j - 1].isspace():
            j -= 1
        anterior = normalizar(texto[j:i]).strip("(")
        return anterior not in ABREVIACOES

    def _aceito(self, candidato: str) -> bool:
        nome = normalizar(candidato)
        if any(nome in marcador for marcador in self._marcadores):
            return True  # o marcador ou um pedaço dele
        return any(nome in aceito for aceito in self._aceitos)

    def _nomes(self, texto: str, mascarado: str) -> list[Achado]:
        achados: list[Achado] = []
        for m in TRATAMENTO.finditer(mascarado):
            achados.append(Achado("nome", texto[m.start() : m.end()], m.start()))
        for m in SEQUENCIA.finditer(mascarado):
            palavras = [(p.start() + m.start(), p.group()) for p in re.finditer(PALAVRA, m.group())]
            chaves = [normalizar(p).rstrip(".") for _, p in palavras]
            societaria = any(c in SOCIETARIAS for c in chaves)
            empresa = any(c in EMPRESA for c in chaves)
            if (
                self._inicio_de_frase(mascarado, m.start())
                and not societaria
                and chaves[0] not in EMPRESA
            ):
                palavras = palavras[1:]
            if len(palavras) < 2:
                continue
            if all(_sigla(p) for _, p in palavras) and not (societaria or empresa):
                continue  # siglas juntas ("CPF e CNPJ") não são nome
            inicio = palavras[0][0]
            fim = palavras[-1][0] + len(palavras[-1][1])
            candidato = texto[inicio:fim]
            if self._aceito(candidato):
                continue
            achados.append(Achado("nome", candidato, inicio))
        for m in CARGO.finditer(mascarado):
            inicio, fim = m.start("nome"), m.end("nome")
            if not self._aceito(texto[inicio:fim]):
                achados.append(Achado("nome_ao_lado_do_cargo", texto[inicio:fim], inicio))
        return achados

    # --- entrada -----------------------------------------------------------------

    def detectar(self, texto: str) -> list[Achado]:
        normal = normalizar(texto)
        mascarado = self._mascarado(texto, normal)
        achados = self._numeros(texto) + self._proibidos_no(texto, normal)
        achados += self._nomes(texto, mascarado)
        unicos = {(a.posicao, a.tipo, a.trecho): a for a in achados}
        return [unicos[chave] for chave in sorted(unicos)]
