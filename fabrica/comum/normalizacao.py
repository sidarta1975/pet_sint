"""Normalizações da comparação entre extração e ficha (ARQUITETURA, Anexo D).

Todas as funções recebem texto e devolvem uma cópia normalizada: nenhuma altera
o texto guardado (AGENTS §4). As regras da âncora e dos termos principais do
Anexo E entram aqui no brief 015.
"""

from __future__ import annotations

import re
import unicodedata

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
