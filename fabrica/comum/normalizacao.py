"""Normalizações da comparação entre extração e ficha (ARQUITETURA, Anexo D).

Todas as funções recebem texto e devolvem uma cópia normalizada: nenhuma altera
o texto guardado (AGENTS §4). As regras da âncora e dos termos principais do
Anexo E (brief 015) ficam no fim do arquivo.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

MARCAS_DE_APROXIMACAO = ("cerca de", "aproximadamente", "mais de")
NUMEROS_POR_EXTENSO = frozenset(
    """
    um uma dois duas tres quatro cinco seis sete oito nove dez onze doze treze quatorze
    catorze quinze dezesseis dezessete dezoito dezenove vinte trinta quarenta cinquenta
    sessenta setenta oitenta noventa cem cento duzentos duzentas trezentos trezentas
    quatrocentos quatrocentas quinhentos quinhentas seiscentos seiscentas setecentos
    setecentas oitocentos oitocentas novecentos novecentas mil milhao milhoes bilhao bilhoes
    """.split()
)
TRATAMENTOS = ("sr", "sra", "srta", "dr", "dra", "exmo", "exma", "ilmo", "ilma")
DESIGNACOES = frozenset(
    """
    autor autora autores autoras reu re reus res requerente requerentes requerido requerida
    requeridos requeridas embargante embargantes embargado embargada embargados embargadas
    demandante demandado demandada promovente promovido promovida suplicante suplicado
    suplicada peticionante peticionario peticionaria citando citanda exequente executado
    executada
    """.split()
)
ARTIGOS = frozenset({"o", "a", "os", "as", "da", "do", "das", "dos", "de"})
_ALGARISMOS = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:,\d{1,2})?")
_TRATAMENTO = re.compile(r"^(?:(?:" + "|".join(TRATAMENTOS) + r")\.?\s+)+")


def sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def compactar_espacos(texto: str) -> str:
    return " ".join(texto.split())


def comparavel(texto: str) -> str:
    """Minúsculas, sem acento e com os espaços compactados."""
    return compactar_espacos(sem_acento(texto.casefold()))


def palavras(texto: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", comparavel(texto))


# --- valores -------------------------------------------------------------------


def centavos_em_algarismos(texto: str) -> int | None:
    """O primeiro valor em algarismos do texto, em centavos ("R$ 1.500,00" é 150000)."""
    achado = _ALGARISMOS.search(texto)
    if achado is None:
        return None
    inteiro, _, fracao = achado.group().partition(",")
    return int(inteiro.replace(".", "")) * 100 + (int(fracao.ljust(2, "0")) if fracao else 0)


def tem_extenso(texto: str) -> bool:
    """Se o texto traz, depois dos algarismos, o valor escrito por extenso."""
    achado = _ALGARISMOS.search(texto)
    if achado is None:
        return False
    return any(p in NUMEROS_POR_EXTENSO for p in palavras(texto[achado.end() :]))


def tem_marca_de_aproximacao(texto: str) -> bool:
    normal = comparavel(texto)
    return any(re.search(rf"(?<!\w){m}(?!\w)", normal) for m in MARCAS_DE_APROXIMACAO)


# --- documentos ----------------------------------------------------------------


def so_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def so_digitos_e_letras(texto: str) -> str:
    """CPF, CNPJ, número do processo e protocolo: sem pontuação nem espaço."""
    return re.sub(r"[^0-9A-Z]", "", sem_acento(texto).upper())


def cep(texto: str) -> str:
    return so_digitos(texto)


# --- nomes, designação, comarca e juízo ----------------------------------------


def nome(texto: str) -> str:
    """Minúsculas, sem acento, sem tratamento antes ("Sr.", "Dr.")."""
    return _TRATAMENTO.sub("", comparavel(texto)).strip()


def eh_designacao(texto: str) -> bool:
    """ "o autor", "a ré", "a requerida": designação, não nome."""
    resto = [p for p in palavras(texto) if p not in ARTIGOS and p != "parte"]
    return len(resto) == 1 and resto[0] in DESIGNACOES


def comarca(texto: str) -> str:
    return " ".join(p for p in palavras(texto) if p not in ARTIGOS)


def juizo(texto: str) -> str:
    """Sem "da Comarca de" e sem artigos; "JEC" igual a "Juizado Especial Cível"."""
    normal = comparavel(texto)
    normal = re.sub(r"(?<!\w)(?:da |de |na )?comarca de(?!\w)", " ", normal)
    normal = re.sub(r"(?<!\w)jec(?!\w)", "juizado especial civel", normal)
    return " ".join(p for p in re.findall(r"[a-z0-9ªº]+", normal) if p not in ARTIGOS)


# --- termos --------------------------------------------------------------------


def contem_termo(texto: str, termo: str) -> bool:
    """O termo aparece como palavra inteira, sem diferença de maiúsculas e acentos."""
    alvo = comparavel(termo)
    if not alvo:
        return False
    return re.search(rf"(?<!\w){re.escape(alvo)}(?!\w)", comparavel(texto)) is not None


# ---------------------------------------------------------------------------
# Âncora e termos principais (ARQUITETURA, Anexo E.2; brief 015)
# ---------------------------------------------------------------------------

_SEPARADOR_DE_NUMERO = re.compile(r"(?<=\d)[.,](?=\d)")
_NAO_PALAVRA = re.compile(r"[^0-9a-z]+")
LETRAS_DO_RADICAL = 6
LETRAS_MINIMAS = 4


def normalizar_termos(texto: str) -> str:
    """Minúsculas, sem acentos e sem pontuação; números sem pontos e vírgulas internos."""
    t = sem_acento(texto).casefold()
    t = _SEPARADOR_DE_NUMERO.sub("", t)
    return _NAO_PALAVRA.sub(" ", t).strip()


def palavras_normalizadas(texto: str) -> list[str]:
    return normalizar_termos(texto).split()


def radical(palavra: str, letras: int = LETRAS_DO_RADICAL) -> str:
    """Corte simples nas primeiras letras; palavras menores ficam inteiras."""
    return palavra[:letras]


def radicais(texto: str, letras: int = LETRAS_DO_RADICAL) -> frozenset[str]:
    """Os radicais de todas as palavras do texto, sem tirar nenhuma."""
    return frozenset(radical(p, letras) for p in palavras_normalizadas(texto))


def _sem_ignoradas(texto: str, ignoradas: Iterable[str]) -> list[str]:
    normalizadas = [normalizar_termos(i) for i in ignoradas]
    simples = {i for i in normalizadas if i and " " not in i}
    compostas = sorted((i for i in normalizadas if " " in i), key=len, reverse=True)
    t = f" {normalizar_termos(texto)} "
    for composta in compostas:
        t = t.replace(f" {composta} ", "  ")
    return [p for p in t.split() if p not in simples]


def termos_principais(
    trecho: str,
    contexto: Iterable[str],
    ignoradas: Iterable[str],
    letras_minimas: int = LETRAS_MINIMAS,
    letras_do_radical: int = LETRAS_DO_RADICAL,
) -> list[str]:
    """Os termos principais do trecho, sem repetição e na ordem em que aparecem.

    Saem as palavras ignoradas, as com menos de `letras_minimas` letras (menos os
    números) e os radicais que também aparecem no contexto (os fatos da ficha e os
    outros argumentos).
    """
    comuns: set[str] = set()
    for texto in contexto:
        comuns |= radicais(texto, letras_do_radical)
    termos: list[str] = []
    for palavra in _sem_ignoradas(trecho, ignoradas):
        if len(palavra) < letras_minimas and not palavra.isdigit():
            continue
        r = radical(palavra, letras_do_radical)
        if r not in comuns and r not in termos:
            termos.append(r)
    return termos


def presentes(termos: Iterable[str], texto: str, letras_do_radical: int = LETRAS_DO_RADICAL) -> int:
    """Quantos termos aparecem no texto, pelo mesmo corte."""
    achados = radicais(texto, letras_do_radical)
    return sum(1 for t in termos if t in achados)


def contem_trecho(texto: str, trecho: str) -> bool:
    """O trecho está no texto, letra por letra, depois da normalização de espaços."""
    alvo = compactar_espacos(trecho)
    return bool(alvo) and alvo in compactar_espacos(texto)


def sem_trecho(texto: str, trecho: str) -> str:
    """O texto sem a primeira ocorrência do trecho (espaços normalizados)."""
    return compactar_espacos(texto).replace(compactar_espacos(trecho), " ", 1)
