"""Dados que nunca podem ser reais, criados por programa (ARQUITETURA §5.2).

Não lê arquivo: recebe as listas por parâmetro. Todo sorteio usa um gerador
criado com a semente recebida; nenhum usa o gerador global. Nunca se sorteia
nome: os nomes são os marcadores fixos.
"""

from __future__ import annotations

import random
import string
from collections.abc import Sequence

from fabrica.comum.formatos import Categoria, Cidade, Endereco, Tribunal

MARCADORES_PESSOA = {
    "autor": "Nome e Sobrenome da Parte Autora",
    "reu": "Nome e Sobrenome da Parte Ré",
}
MARCADORES_EMPRESA = {
    "autor": "Razão Social da Parte Autora",
    "reu": "Razão Social da Parte Ré",
}
MARCADOR_ADVOGADO = "Nome e Sobrenome do Advogado"
MARCADOR_OAB = "OAB/UF nº 000.000"
MARCADORES = frozenset(
    {*MARCADORES_PESSOA.values(), *MARCADORES_EMPRESA.values(), MARCADOR_ADVOGADO}
)
PREFIXO = "SINT-"
RAMO_ESTADUAL = "8"
DOMINIO = "ficticio.example"
EMAILS = {
    "autor": "parte.autora",
    "reu": "parte.re",
    "advogado": "advogado",
    "escritorio": "escritorio",
}
# Os 67 DDDs em uso no país (ARQUITETURA §5.2).
DDDS_EM_USO = frozenset(
    [*range(11, 20), 21, 22, 24, 27, 28, *range(31, 36), 37, 38, *range(41, 50), 51]
    + [*range(53, 56), *range(61, 70), 71, *range(73, 76), 77, 79, *range(81, 90)]
    + [*range(91, 100)]
)
PESOS_CPF_1 = list(range(10, 1, -1))
PESOS_CPF_2 = list(range(11, 1, -1))
PESOS_CNPJ_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
PESOS_CNPJ_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
ALFANUMERICOS = string.digits + string.ascii_uppercase


class ErroFicticio(Exception):
    """Lista recebida que não permite gerar dado fictício."""


def _valor(caractere: str) -> int:
    """Cada caractere vale o código ASCII menos 48 (vale também para o CNPJ com letras)."""
    return ord(caractere) - 48


def digito_mod11(base: str, pesos: Sequence[int]) -> str:
    resto = sum(_valor(c) * p for c, p in zip(base, pesos, strict=True)) % 11
    return "0" if resto < 2 else str(11 - resto)


def digitos_cpf(base: str) -> str:
    d1 = digito_mod11(base, PESOS_CPF_1)
    return d1 + digito_mod11(base + d1, PESOS_CPF_2)


def digitos_cnpj(base: str) -> str:
    d1 = digito_mod11(base, PESOS_CNPJ_1)
    return d1 + digito_mod11(base + d1, PESOS_CNPJ_2)


def digito_cnj(sequencial: str, ano: str, ramo: str, tribunal: str, unidade: str) -> str:
    """Dígito oficial do número do CNJ: 98 menos o resto da divisão por 97."""
    resto = int(sequencial + ano + ramo + tribunal + unidade + "00") % 97
    return f"{98 - resto:02d}"


class Ficticios:
    def __init__(
        self,
        semente: int,
        ddds: Sequence[int],
        ruas: Sequence[str],
        bairros: Sequence[str],
        cidades: Sequence[Cidade],
        tribunais: Sequence[Tribunal],
        profissoes: Sequence[str],
    ) -> None:
        em_uso = sorted(set(ddds) & DDDS_EM_USO)
        if not ddds or em_uso:
            raise ErroFicticio(f"a lista de DDDs inexistentes tem DDD em uso: {em_uso}")
        for nome, lista in (("ruas", ruas), ("bairros", bairros), ("cidades", cidades)):
            if not lista:
                raise ErroFicticio(f"lista de {nome} vazia")
        self._rng = random.Random(semente)
        self._ddds = list(ddds)
        self._ruas = list(ruas)
        self._bairros = list(bairros)
        self._cidades = list(cidades)
        self._tribunais = {tribunal.uf: tribunal.codigo for tribunal in tribunais}
        self._profissoes = list(profissoes)

    # --- marcadores -----------------------------------------------------------

    @staticmethod
    def nome(papel: str, categoria: Categoria) -> str:
        marcadores = MARCADORES_PESSOA if categoria == "pessoa_fisica" else MARCADORES_EMPRESA
        return marcadores[papel]

    @staticmethod
    def nome_advogado() -> str:
        return MARCADOR_ADVOGADO

    @staticmethod
    def oab() -> str:
        return MARCADOR_OAB

    # --- documentos com dígito propositalmente inválido -----------------------

    def _digitos(self, n: int) -> str:
        return "".join(self._rng.choice(string.digits) for _ in range(n))

    def _errado(self, certo: str) -> str:
        while True:
            errado = self._digitos(len(certo))
            if errado != certo:
                return errado

    def cpf(self) -> str:
        base = self._digitos(9)
        dv = self._errado(digitos_cpf(base))
        return f"{base[:3]}.{base[3:6]}.{base[6:9]}-{dv}"

    def cnpj(self) -> str:
        """Metade com letras (formato emitido pela Receita desde 31/07/2026)."""
        if self._rng.random() < 0.5:
            base = "".join(self._rng.choice(ALFANUMERICOS) for _ in range(12))
        else:
            base = self._digitos(12)
        dv = self._errado(digitos_cnpj(base))
        return f"{base[:2]}.{base[2:5]}.{base[5:8]}/{base[8:12]}-{dv}"

    def numero_processo(self, uf: str, ano: int) -> str:
        """`NNNNNNN-DD.AAAA.8.TR.OOOO`, com o tribunal do estado e o dígito inválido."""
        tribunal = self._tribunais.get(uf)
        if tribunal is None:
            raise ErroFicticio(f"sem código de tribunal para o estado {uf}")
        sequencial = self._digitos(7)
        unidade = self._digitos(4)
        texto_ano = f"{ano:04d}"
        certo = digito_cnj(sequencial, texto_ano, RAMO_ESTADUAL, tribunal, unidade)
        dv = self._errado(certo)
        return f"{sequencial}-{dv}.{texto_ano}.{RAMO_ESTADUAL}.{tribunal}.{unidade}"

    # --- contato, endereço e números do caso ---------------------------------

    def telefone(self) -> str:
        ddd = self._rng.choice(self._ddds)
        return f"({ddd:02d}) 9{self._digitos(4)}-{self._digitos(4)}"

    @staticmethod
    def email(papel: str) -> str:
        return f"{EMAILS[papel]}@{DOMINIO}"

    def endereco(self, cidade: str | None = None) -> Endereco:
        if cidade is None:
            escolhida = self._rng.choice(self._cidades)
        else:
            achadas = [c for c in self._cidades if c.nome == cidade]
            if not achadas:
                raise ErroFicticio(f"cidade fora da lista: {cidade}")
            escolhida = achadas[0]
        inicio = int(escolhida.cep_inicio.replace("-", ""))
        fim = int(escolhida.cep_fim.replace("-", ""))
        cep = f"{self._rng.randint(inicio, fim):08d}"
        return Endereco(
            rua=self._rng.choice(self._ruas),
            numero=str(self._rng.randint(1, 9999)),
            complemento=None,
            bairro=self._rng.choice(self._bairros),
            cidade=escolhida.nome,
            estado=escolhida.uf,
            cep=f"{cep[:5]}-{cep[5:]}",
        )

    def identificador(self, ano: int) -> str:
        return f"{PREFIXO}{ano:04d}-{self._digitos(6)}"

    def profissao(self) -> str:
        if not self._profissoes:
            raise ErroFicticio("lista de profissões vazia")
        return self._rng.choice(self._profissoes)

    def codigo_banco(self, oficiais: Sequence[str]) -> str:
        """Código de banco fora da lista oficial recebida (nunca vazia)."""
        if not oficiais:
            raise ErroFicticio("a lista oficial de códigos de banco está vazia")
        livres = sorted(set(f"{n:03d}" for n in range(1000)) - set(oficiais))
        if not livres:
            raise ErroFicticio("nenhum código de banco fora da lista oficial")
        return self._rng.choice(livres)
